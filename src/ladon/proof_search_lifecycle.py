"""Preview-first lifecycle for repository-local disposable proof-search indexes."""

from __future__ import annotations

import hashlib
import heapq
import json
import os
import sqlite3
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_retained import first_retained_evidence_table
from ladon.proof_search_schema import PROOF_SEARCH_INDEX_SCHEMA
from ladon.sqlite_publication import (
    PublicationLockBusy,
    acquire_publication_lock,
    publication_lock_status,
    release_publication_lock,
)

_LIFECYCLE_SCHEMA = "ladon-proof-search-index-lifecycle-v1"
_PREVIEW_LIMIT = 4 * 1024 * 1024


def _directory(repo_root: Path, directory: Path | None) -> Path:
    chosen = directory if directory is not None else repo_root / ".ladon/index"
    return chosen.expanduser().absolute()


def _identity(path: Path, stat: os.stat_result) -> str:
    content = f"{path.name}:{stat.st_dev}:{stat.st_ino}:{stat.st_size}:{stat.st_mtime_ns}"
    return hashlib.sha256(content.encode()).hexdigest()


def _sidecars(path: Path) -> list[str]:
    return [suffix for suffix in ("-journal", "-wal", "-shm") if Path(str(path) + suffix).exists()]


def _inspect(repo_root: Path, path: Path, *, owner_held: bool = False) -> dict[str, Any]:
    try:
        stat = path.lstat()
    except OSError as exc:
        return {"name": path.name, "path": str(path), "classification": "protected", "reason": f"unreadable: {exc}"}
    row: dict[str, Any] = {
        "name": path.name, "path": str(path), "bytes": stat.st_size,
        "mtimeEpoch": stat.st_mtime, "identity": _identity(path, stat),
        "classification": "protected", "reason": "unrecognized-file",
    }
    if path.is_symlink() or not path.is_file():
        row["reason"] = "symlink-or-nonregular"
        return row
    if path.name.endswith(".lock"):
        row["reason"] = "persistent-publication-lock"
        return row
    if path.name.endswith((".tmp", "-journal", "-wal", "-shm")):
        row["reason"] = "temporary-or-sidecar-ownership-unknown"
        return row
    if not (path.name.startswith("proof-search.") and path.name.endswith(".sqlite")):
        return row
    return _inspect_candidate(repo_root, path, row, owner_held=owner_held)


def _inspect_candidate(
    repo_root: Path, path: Path, row: dict[str, Any], *, owner_held: bool
) -> dict[str, Any]:
    row["publisher"] = "owned-by-cleanup" if owner_held else publication_lock_status(path)["status"]
    if path.name == "proof-search.sqlite":
        row["reason"] = "default-index"
        return row
    if row["publisher"] not in {"inactive", "absent", "owned-by-cleanup"}:
        row["reason"] = "active-publisher"
        return row
    if _sidecars(path):
        row["reason"] = "active-or-uncertain-sidecar"
        return row
    return _inspect_sqlite(repo_root, path, row)


def _inspect_sqlite(repo_root: Path, path: Path, row: dict[str, Any]) -> dict[str, Any]:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
            metadata = dict(connection.execute("SELECT key,value FROM metadata"))
            row["generationIdentity"] = metadata.get("generationIdentity")
            row["repository"] = metadata.get("repository")
            if metadata.get("indexSchema") != PROOF_SEARCH_INDEX_SCHEMA:
                row["reason"] = "incompatible-index-schema"
                return row
            if metadata.get("repository") != str(repo_root.resolve()):
                row["reason"] = "foreign-repository"
                return row
            retained = first_retained_evidence_table(connection)
            if retained is not None:
                row["reason"] = f"retained-evidence:{retained}"
                return row
    except (OSError, sqlite3.Error, ValueError) as exc:
        row["reason"] = f"unreadable-index:{exc}"
        return row
    row["classification"] = "disposable-private"
    row["reason"] = "lexical-private-index"
    return row


def list_indexes(
    repo_root: Path, *, directory: Path | None = None, limit: int = 1000
) -> dict[str, Any]:
    if not 1 <= limit <= 10000:
        raise ProofSearchIndexError("index list limit must be between 1 and 10000")
    folder = _directory(repo_root, directory)
    if not folder.is_dir() or folder.is_symlink():
        raise ProofSearchIndexError("index directory is missing or is a symlink")
    total = 0

    def entries():
        nonlocal total
        for path in folder.iterdir():
            total += 1
            yield path

    # Bound expensive SQLite inspection and retained output even when a
    # repository has accumulated a very large private-index directory.
    paths = heapq.nsmallest(limit + 1, entries(), key=lambda path: path.name)
    rows = [_inspect(repo_root, path) for path in paths[:limit]]
    return {
        "schema": _LIFECYCLE_SCHEMA, "operation": "list", "status": "available",
        "repository": str(repo_root.resolve()), "directory": str(folder),
        "total": total, "returned": len(rows),
        "truncated": total > limit,
        "totalBytes": sum(row.get("bytes", 0) for row in rows),
        "totalBytesScope": "returned-rows" if total > limit else "all-entries",
        "rows": rows,
        "nonclaim": "mtime is a filesystem age hint, not last use or proof of publisher inactivity",
    }


def preview_prune(
    repo_root: Path, *, directory: Path | None = None,
    selected: tuple[str, ...] = (), older_than_days: float | None = None,
    keep: tuple[str, ...] = (),
) -> dict[str, Any]:
    _validate_preview_selection(selected, keep, older_than_days)
    listing = list_indexes(repo_root, directory=directory, limit=10000)
    if listing["truncated"]:
        raise ProofSearchIndexError("directory inventory exceeds the safe preview limit")
    known = {row["name"] for row in listing["rows"]}
    if set(selected) - known:
        raise ProofSearchIndexError("selected index is missing from directory")
    now = time.time()
    rows = _selected_preview_rows(listing["rows"], selected, keep, older_than_days, now)
    return {
        "schema": _LIFECYCLE_SCHEMA, "operation": "prune-preview", "status": "available",
        "repository": listing["repository"], "directory": listing["directory"],
        "rows": rows,
        "eligibleBytes": sum(row.get("bytes", 0) for row in rows if row["classification"] == "disposable-private"),
        "selected": list(selected), "keep": list(keep), "olderThanDays": older_than_days,
        "createdEpoch": now,
    }


def _validate_preview_selection(selected, keep, older_than_days) -> None:
    if not selected and older_than_days is None:
        raise ProofSearchIndexError("select at least one private index or an explicit age filter")
    if older_than_days is not None and older_than_days < 0:
        raise ProofSearchIndexError("age filter must be nonnegative")
    for name in (*selected, *keep):
        if Path(name).name != name or name in {".", ".."}:
            raise ProofSearchIndexError("selection and keep values must be basenames")


def _selected_preview_rows(rows, selected, keep, older_than_days, now):
    selected_rows = []
    for row in rows:
        chosen = row["name"] in selected or (
            older_than_days is not None and row.get("mtimeEpoch", now) <= now - older_than_days * 86400
        )
        if not chosen:
            continue
        item = dict(row)
        if item["name"] in keep:
            item["classification"] = "protected"
            item["reason"] = "explicit-keep"
        selected_rows.append(item)
    return selected_rows


def apply_prune(repo_root: Path, preview_file: Path) -> dict[str, Any]:
    preview = _read_preview(preview_file)
    folder = _preview_directory(repo_root, preview)
    outcomes = []
    for row in preview.get("rows", []):
        outcomes.append(_apply_one(repo_root, folder, row))
    status = "partial" if any(row["status"] == "failed" for row in outcomes) else "complete"
    return {
        "schema": _LIFECYCLE_SCHEMA, "operation": "prune-apply", "status": status,
        "repository": str(repo_root.resolve()), "directory": str(folder),
        "rows": outcomes, "reclaimedBytes": sum(row.get("bytes", 0) for row in outcomes if row["status"] == "deleted"),
    }


def _read_preview(preview_file: Path) -> Mapping[str, Any]:
    try:
        if preview_file.stat().st_size > _PREVIEW_LIMIT:
            raise ProofSearchIndexError("prune preview exceeds its input limit")
        preview = json.loads(preview_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProofSearchIndexError(f"unreadable prune preview: {exc}") from exc
    if not isinstance(preview, Mapping) or not isinstance(preview.get("rows"), list):
        raise ProofSearchIndexError("prune preview must contain a row list")
    return preview


def _preview_directory(repo_root: Path, preview: Mapping[str, Any]) -> Path:
    folder = Path(str(preview.get("directory", "")))
    if (
        preview.get("schema") != _LIFECYCLE_SCHEMA
        or preview.get("operation") != "prune-preview"
        or preview.get("repository") != str(repo_root.resolve())
        or not folder.is_dir() or folder.is_symlink()
    ):
        raise ProofSearchIndexError("prune preview does not match this repository and directory")
    return folder


def _apply_one(repo_root: Path, folder: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    name = row.get("name") if isinstance(row, Mapping) else None
    _require_safe_preview_name(name)
    if row.get("classification") != "disposable-private":
        return {"name": name, "status": "protected", "reason": row.get("reason")}
    path = folder / name
    if not path.exists():
        return {"name": name, "status": "skipped", "reason": "already-absent"}
    try:
        lock = acquire_publication_lock(path)
    except PublicationLockBusy:
        return {"name": name, "status": "protected", "reason": "active-publisher"}
    try:
        current = _inspect(repo_root, path, owner_held=True)
        if current.get("identity") != row.get("identity") or (
            current.get("classification") != "disposable-private"
        ):
            return {"name": name, "status": "protected", "reason": "identity-or-ownership-changed"}
        try:
            path.unlink()
        except OSError as exc:
            return {"name": name, "status": "failed", "reason": str(exc)}
        return {"name": name, "status": "deleted", "bytes": row["bytes"]}
    finally:
        release_publication_lock(lock)


def _require_safe_preview_name(name: Any) -> None:
    if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
        raise ProofSearchIndexError("prune preview contains an unsafe filename")
