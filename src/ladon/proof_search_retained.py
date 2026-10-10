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
        "SELECT 1 FROM declarations WHERE authority != 'lexical_text' "
        "OR type_status = 'lean-rendered' OR semantic_status != 'unavailable' "
        "OR rendered_type != COALESCE(type_text,'') "
        "OR conclusion_text != COALESCE(type_text,'') OR fingerprint != '' "
        "OR head != '' OR arity != 0 OR is_proposition != 0 "
        "OR helper_identity != '' OR lean_identity != '' LIMIT 1"
    ).fetchone():
        return "declarations"
    if connection.execute(
        "SELECT 1 FROM structures WHERE authority != 'lexical_text' LIMIT 1"
    ).fetchone():
        return "structures"
    if connection.execute(
        "SELECT 1 FROM module_semantic_state WHERE status != 'lexical' "
        "OR compiled_fingerprint != '' OR surface_fingerprint != '' LIMIT 1"
    ).fetchone():
        return "module_semantic_state"
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
