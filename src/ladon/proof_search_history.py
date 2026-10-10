"""Bounded inventory and private verified reading of retained index snapshots."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from ladon.proof_search_history_store import history_directory, read_history, validate_history


def _entries(repo_root, index_path):
    from ladon.proof_search_index import (
        _metadata,
        _open_readonly,
        _require_query_schema,
        _resolved_index_path,
    )

    index = _resolved_index_path(repo_root, index_path)
    with _open_readonly(index) as connection:
        _require_query_schema(_metadata(connection))
        from ladon.proof_search_history_schema import require_supported_layout

        require_supported_layout(connection, verify_integrity=False)
        return index, read_history(connection)


def list_history(repo_root: Path, *, index_path=None, limit=100, offset=0):
    from ladon.proof_search_index import ProofSearchIndexError

    if not 1 <= limit <= 1000 or offset < 0:
        raise ProofSearchIndexError("history requires limit 1..1000 and nonnegative offset")
    index, entries = _entries(repo_root, index_path)
    selected = entries[offset:offset + limit]
    rows = []
    for entry in selected:
        try:
            validate_history(index, [entry])
            availability = "available"
            reason = None
        except (OSError, ValueError, ProofSearchIndexError) as error:
            availability = "unavailable"
            reason = str(error)
        rows.append({**entry, "availability": availability, "reason": reason})
    truncated = offset + len(rows) < len(entries)
    return {
        "schema": "ladon-proof-search-index-history-v1", "operation": "history",
        "status": "available", "indexPath": str(index), "directory": str(history_directory(index)),
        "total": len(entries), "returned": len(rows), "limit": limit, "offset": offset,
        "snapshots": rows, "truncated": truncated,
        "nextOffset": offset + len(rows) if truncated else None,
        "historyBytes": sum(entry["bytes"] for entry in entries),
        "totalBytesScope": "registered-snapshots",
        "currentAssociation": "not-established",
        "unregisteredFiles": unregistered_files(index, entries),
    }


def history_status(index: Path, entries):
    from ladon.proof_search_index import ProofSearchIndexError

    try:
        validate_history(index, entries)
        availability = "available" if entries else "empty"
    except (OSError, ValueError, ProofSearchIndexError):
        availability = "unavailable"
    return {"snapshots": len(entries), "bytes": sum(entry["bytes"] for entry in entries),
            "availability": availability, "currentAssociation": "not-established"}


@contextmanager
def open_history_snapshot(repo_root, index_path, snapshot_id):
    """Copy selected bytes to owned request storage before checking and opening."""
    from ladon.proof_search_index import ProofSearchIndexError, _metadata, _open_readonly

    index, entries = _entries(repo_root, index_path)
    selected = [entry for entry in entries if entry["snapshotId"] == snapshot_id]
    if len(selected) != 1:
        raise ProofSearchIndexError("history snapshot is not uniquely registered")
    entry = selected[0]
    validate_history(index, [entry])
    source = history_directory(index) / entry["path"]
    with tempfile.TemporaryDirectory(prefix="ladon-history-") as temporary:
        target = Path(temporary) / "snapshot.sqlite"
        _copy_verified(source, target, snapshot_id, entry["bytes"])
        connection = _open_readonly(target)
        try:
            from ladon.proof_search_history_schema import require_supported_layout

            require_supported_layout(connection)
            metadata = _metadata(connection)
            if metadata != entry["metadata"]:
                raise ProofSearchIndexError("history catalog observation differs from snapshot bytes")
            yield connection, entry, metadata
        finally:
            connection.close()


def _copy_verified(source, target, expected, size):
    from ladon.proof_search_index import ProofSearchIndexError

    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream, target.open("wb") as output:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ProofSearchIndexError("history snapshot is not a regular file")
        remaining = size
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            output.write(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            raise ProofSearchIndexError("history snapshot grew while preparing inspection")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected or target.stat().st_size != size:
        raise ProofSearchIndexError("history snapshot changed while preparing inspection")


def render_history(payload):
    lines = [f"proof-search index history: {payload['status']}",
             f"snapshots: {payload['total']}; registered bytes: {payload['historyBytes']}",
             "current compiled association: not established"]
    for row in payload["snapshots"]:
        lines.append(f"- {row['snapshotId']}: {row['availability']} "
                     f"generation={row['generationIdentity']} bytes={row['bytes']}")
        if row["reason"]:
            lines.append(f"  {row['reason']}")
    if payload["truncated"]:
        lines.append(f"More snapshots: use --offset {payload['nextOffset']}")
    return "\n".join(lines) + "\n"


def unregistered_files(index, entries, *, limit=100):
    """Bound retained rows while accounting for all unregistered directory entries."""
    import heapq

    root = history_directory(index)
    registered = {entry['path'] for entry in entries}
    total = 0
    size = 0

    def candidates():
        nonlocal total, size
        for item in root.iterdir():
            if item.name not in registered:
                total += 1
                observed = item.lstat()
                size += observed.st_size
                yield {'name': item.name, 'bytes': observed.st_size,
                       'classification': 'protected', 'reason': 'unregistered-or-uncertain-history'}

    rows = [] if not root.is_dir() or root.is_symlink() else heapq.nsmallest(
        limit, candidates(), key=lambda row: row['name']
    )
    return {'total': total, 'bytes': size, 'rows': rows, 'truncated': total > limit,
            'bytesScope': 'directory-entries-not-recursive'}
