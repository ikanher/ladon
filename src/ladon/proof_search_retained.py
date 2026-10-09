"""Detect retained evidence that cannot be discarded by lexical maintenance."""

from __future__ import annotations

import sqlite3

_SEMANTIC_TABLES = frozenset({
    "binders", "declaration_dependencies", "declaration_shapes", "structure_fields", "aliases",
})
_REQUIRED_TABLES = frozenset({
    "proofir_generations", "proofir_artifacts", "proofir_v3_artifacts",
    "lineage_closures", "binders", "declarations", "modules", "metadata",
})


def first_retained_evidence_table(connection: sqlite3.Connection) -> str | None:
    """Return an evidence-bearing table, including future lineage/v3 tables."""

    tables = {
        str(row[0]) for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if not _REQUIRED_TABLES <= tables:
        raise sqlite3.DatabaseError("index lacks required evidence or lexical tables")
    for name in sorted(filter(_is_evidence_table, tables)):
        quoted = name.replace('"', '""')
        if connection.execute(f'SELECT 1 FROM "{quoted}" LIMIT 1').fetchone():
            return name
    if connection.execute(
        "SELECT 1 FROM proofir_generations WHERE artifact_count > 0 LIMIT 1"
    ).fetchone():
        return "proofir_generations"
    return None


def _is_evidence_table(name: str) -> bool:
    return (
        name in _SEMANTIC_TABLES or name.startswith("lineage_")
        or (name.startswith("proofir_") and name != "proofir_generations")
    )
