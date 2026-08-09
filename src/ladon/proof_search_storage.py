"""SQLite allocation accounting for proof-search databases."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Callable


def database_storage_accounting(path: Path, opener: Callable[[Path], sqlite3.Connection]) -> dict[str, Any]:
    """Return deterministic dbstat object and category byte totals."""
    try:
        with opener(path) as connection:
            rows = connection.execute("SELECT name, SUM(pgsize) FROM dbstat GROUP BY name ORDER BY name").fetchall()
    except (OSError, sqlite3.Error):
        return {"status": "unavailable", "objectBytes": {}, "accountedBytes": None}
    objects = {str(row[0]): int(row[1] or 0) for row in rows}
    groups = {name: 0 for name in ("base", "fts", "semantic", "lineage", "proofir", "sqlite-internal", "other")}
    for name, size in objects.items():
        groups[_storage_group(name)] += size
    return {"status": "complete", "objectBytes": objects, "groups": groups, "accountedBytes": sum(objects.values())}


def _storage_group(name: str) -> str:
    if name.startswith("sqlite_"):
        return "sqlite-internal"
    if name.startswith(("proofir_", "idx_proofir_")):
        return "proofir"
    if name.startswith(("lineage_", "idx_lineage_")):
        return "lineage"
    if name == "declaration_search" or name.startswith("declaration_search_"):
        return "fts"
    if name.startswith(("idx_", "declaration_", "binder", "structure", "module_semantic")):
        return "semantic"
    return "base"
