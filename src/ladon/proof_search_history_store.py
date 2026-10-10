"""Storage primitives for immutable proof-search index history snapshots."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any


def _error(message: str, *, code="history-invalid", details=None) -> Exception:
    # Keep this module below proof_search_index in the import graph.
    from ladon.proof_search_index import ProofSearchIndexError

    return ProofSearchIndexError(message, exit_class="operational", code=code, details=details)


def history_directory(index: Path) -> Path:
    return Path(index).absolute().with_name(Path(index).name + ".history")


def _metadata(connection: sqlite3.Connection) -> dict[str, str]:
    try:
        return {str(key): str(value) for key, value in connection.execute("SELECT key,value FROM metadata")}
    except sqlite3.Error as exc:
        raise _error("index history requires a readable metadata table") from exc


def _inventory(connection: sqlite3.Connection) -> dict[str, int]:
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    result: dict[str, int] = {}
    for (name,) in tables:
        quoted = '"' + str(name).replace('"', '""') + '"'
        result[str(name)] = int(connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
    return result


def _hash(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def archive_base(
    old: sqlite3.Connection, destination: Path, max_history_bytes: int | None = None
) -> dict[str, Any]:
    """Back up a consistent database to a standalone digest-named file.

    ``destination`` is the adjacent history directory. The caller serializes
    publication against other writers before calling this function.
    """
    root = Path(destination).absolute()
    if root.is_symlink():
        raise _error("history directory must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    if root.resolve() != root:
        raise _error("history directory resolves outside its selected path")
    metadata = _metadata(old)
    inventory = _inventory(old)
    fd, temp_name = tempfile.mkstemp(prefix=".snapshot-", suffix=".tmp", dir=root)
    os.close(fd)
    temp = Path(temp_name)
    try:
        target = sqlite3.connect(temp)
        try:
            old.backup(target)
            target.execute("PRAGMA journal_mode=DELETE")
            target.commit()
            _validate_snapshot(target)
        finally:
            target.close()
        with temp.open("rb") as stream:
            os.fsync(stream.fileno())
        snapshot_id, size = _hash(temp)
        final = root / f"{snapshot_id}.sqlite"
        _publish_archive(temp, final, snapshot_id, size, max_history_bytes)
        return {
            "snapshotId": snapshot_id,
            "sha256": snapshot_id,
            "path": str(final),
            "bytes": size,
            "generationIdentity": metadata.get("generationIdentity", ""),
            "metadata": metadata,
            "evidenceInventory": inventory,
        }
    except sqlite3.Error as exc:
        raise _error(f"SQLite history archive failed: {exc}") from exc
    finally:
        if temp.exists():
            temp.unlink()


def create_history_catalog(connection: sqlite3.Connection, entries: list[dict[str, Any]]) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS index_history (snapshot_id TEXT PRIMARY KEY, entry_json TEXT NOT NULL)"
    )
    connection.execute("DELETE FROM index_history")
    for entry in entries:
        snapshot_id = entry.get("snapshotId")
        if not _snapshot_id(snapshot_id):
            raise _error("history catalog entry has an invalid snapshot identity")
        connection.execute(
            "INSERT INTO index_history(snapshot_id,entry_json) VALUES (?,?)",
            (snapshot_id, json.dumps(entry, sort_keys=True, separators=(",", ":"))),
        )


def read_history(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    try:
        rows = connection.execute("SELECT snapshot_id,entry_json FROM index_history ORDER BY snapshot_id").fetchall()
    except sqlite3.Error as exc:
        if "no such table" in str(exc).lower():
            if _metadata(connection).get("indexSchema") == "ladon-proof-search-index-v5":
                return []
            raise _error("current index is missing its history catalog") from exc
        raise _error(f"cannot read index history catalog: {exc}") from exc
    entries: list[dict[str, Any]] = []
    for snapshot_id, raw in rows:
        try:
            item = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise _error("index history catalog contains invalid JSON") from exc
        if not isinstance(item, dict):
            raise _error("index history catalog entry must be an object")
        _validate_entry(item, snapshot_id)
        entries.append(item)
    return entries


def _snapshot_id(value):
    return (isinstance(value, str) and len(value) == 64
            and all(character in "0123456789abcdef" for character in value))


def _validate_entry(entry, snapshot_id):
    if not _snapshot_id(snapshot_id) or entry.get("snapshotId") != snapshot_id:
        raise _error("history catalog contains an invalid snapshot identity")
    if entry.get("sha256") != snapshot_id or entry.get("path") != f"{snapshot_id}.sqlite":
        raise _error("history snapshot path or digest is invalid")
    size = entry.get("bytes")
    if type(size) is not int or size <= 0:
        raise _error("history snapshot size must be a positive integer")
    if not isinstance(entry.get("metadata"), dict) or not isinstance(entry.get("evidenceInventory"), dict):
        raise _error("history catalog is missing its original observation or inventory")


def validate_history(index: Path, entries: list[dict[str, Any]]) -> None:
    root = history_directory(index)
    if root.is_symlink():
        raise _error("history directory must not be a symlink")
    resolved_root = root.resolve(strict=False)
    for entry in entries:
        snapshot_id = entry.get("snapshotId")
        _validate_entry(entry, snapshot_id)
        candidate = root / entry["path"]
        if candidate.is_symlink() or not candidate.is_file():
            raise _error("registered history snapshot is missing or unsafe")
        if candidate.resolve().parent != resolved_root:
            raise _error("registered history snapshot resolves outside history directory")
        digest, size = _hash(candidate)
        if digest != snapshot_id or size != entry["bytes"]:
            raise _error("registered history snapshot failed digest or size validation")


def _validate_snapshot(connection):
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    if integrity != ("ok",) or connection.execute("PRAGMA foreign_key_check").fetchone():
        raise _error(f"history snapshot integrity check failed: {integrity}")


def _sync_directory(root):
    descriptor = os.open(root, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _history_budget(root, temporary, size, limit):
    if limit is None:
        return
    if limit < 0:
        raise _error("maximum history bytes must be nonnegative")
    existing = 0
    for item in root.rglob("*"):
        if item.is_symlink():
            raise _error("history storage contains a symlink")
        if item.is_file() and item != temporary:
            existing += item.stat().st_size
    if existing + size > limit:
        raise _error("maximum history size would be exceeded", code="history-storage-limit",
                     details={"maxHistoryBytes": limit, "requiredHistoryBytes": existing + size})


def _publish_archive(temporary, final, identity, size, limit):
    if final.exists() or final.is_symlink():
        if final.is_symlink() or not final.is_file():
            raise _error("history snapshot path is not a regular file")
        if _hash(final) != (identity, size):
            raise _error("conflicting history snapshot already exists")
        temporary.unlink()
    else:
        _history_budget(final.parent, temporary, size, limit)
        os.replace(temporary, final)
    # A retry of an earlier uncertain publication must also sync the directory.
    _sync_directory(final.parent)
    _sync_directory(final.parent.parent)


def has_history(index: Path) -> bool:
    """Conservatively protect registered, orphaned and partially moved history."""
    folder = history_directory(index)
    if folder.exists() or folder.is_symlink():
        return True
    if not index.is_file():
        return False
    try:
        with sqlite3.connect(f"{index.as_uri()}?mode=ro", uri=True) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            return "index_history" in tables and bool(read_history(connection))
    except (sqlite3.Error, ValueError):
        return True


def refuse_history_replacement(index: Path) -> None:
    if has_history(index):
        raise _error("cannot rebuild over retained or uncertain history; use index update or a new index path")


def enforce_history_budget(root, limit):
    if root.exists():
        _history_budget(root, None, 0, limit)
    elif limit is not None and limit < 0:
        raise _error("maximum history bytes must be nonnegative")
