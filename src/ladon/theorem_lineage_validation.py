"""Minimal live-index preflight without inventory or historical diagnostics."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ladon.proof_search_history_schema import require_supported_layout
from ladon.proof_search_index import (
    ProofSearchIndexError,
    _metadata,
    _require_query_schema,
)


@contextmanager
def open_lineage_index(index: Path, *, writable: bool):
    """Pin metadata and stored rows to one read transaction; never create an index."""
    if not index.is_file():
        raise ProofSearchIndexError("proof-search index unavailable: index_missing")
    connection = _connect(index, writable=writable)
    try:
        metadata = _preflight(connection)
        yield connection, metadata
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def _connect(index: Path, *, writable: bool):
    try:
        mode = "rw" if writable else "ro"
        connection = sqlite3.connect(f"{index.as_uri()}?mode={mode}", uri=True)
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as exc:
        raise ProofSearchIndexError(f"proof-search index unavailable: index_unreadable: {exc}") from exc


def _preflight(connection):
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")
        metadata = _metadata(connection)
        _require_query_schema(metadata)
        require_supported_layout(connection, verify_integrity=False)
        return metadata
    except sqlite3.Error as exc:
        raise ProofSearchIndexError(f"proof-search index unavailable: index_unreadable: {exc}") from exc


def has_stored_closure(connection, theorem: str) -> bool:
    """Lookup absence before any live repository scan."""
    return connection.execute(
        "SELECT 1 FROM lineage_closures WHERE theorem_name=? AND active=1 LIMIT 1",
        (theorem,),
    ).fetchone() is not None
