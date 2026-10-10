"""Compatibility and lexical isolation for evidence-bearing index generations."""

from __future__ import annotations

import sqlite3
from functools import lru_cache

from ladon.proof_search_schema import (
    LEGACY_INDEX_SCHEMA,
    LEGACY_SCHEMA_GENERATION,
    PROOF_SEARCH_INDEX_SCHEMA,
    PROOF_SEARCH_SCHEMA_GENERATION,
)


def supported_index_schema(metadata) -> bool:
    return (metadata.get("indexSchema"), metadata.get("schemaGeneration")) in {
        (PROOF_SEARCH_INDEX_SCHEMA, PROOF_SEARCH_SCHEMA_GENERATION),
        (LEGACY_INDEX_SCHEMA, LEGACY_SCHEMA_GENERATION),
    }


def _table_layout(connection):
    names = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )]
    return {
        name: tuple(tuple(row) for row in connection.execute(
            'PRAGMA table_info("' + name.replace('"', '""') + '")'
        )) for name in names
    }


@lru_cache(maxsize=1)
def _supported_layout():
    from ladon.proof_search_schema import create_proof_search_schema
    from ladon.proofir_sqlite_v3 import create_v3_schema

    with sqlite3.connect(":memory:") as reference:
        create_proof_search_schema(reference)
        create_v3_schema(reference, manage_user_version=False)
        return _table_layout(reference)


def require_supported_layout(connection, *, verify_integrity=True) -> None:
    from ladon.proof_search_index import ProofSearchIndexError, _metadata, _validate_database

    metadata = _metadata(connection)
    expected = dict(_supported_layout())
    if metadata.get("indexSchema") == LEGACY_INDEX_SCHEMA:
        expected.pop("index_history")
    expected_version = 5 if metadata.get("indexSchema") == LEGACY_INDEX_SCHEMA else 6
    if (metadata.get("schemaVersion") != str(expected_version)
            or connection.execute("PRAGMA user_version").fetchone()[0] != expected_version):
        raise ProofSearchIndexError("unsupported private index schema version", code="full-build-required")
    if _table_layout(connection) != expected or connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='trigger' LIMIT 1"
    ).fetchone():
        raise ProofSearchIndexError(
            "unsupported index table or column layout; preserve this index and build to a new path",
            exit_class="operational", code="full-build-required",
        )
    if verify_integrity:
        _validate_database(connection)


def semantic_modules(connection) -> set[str]:
    rows = connection.execute(
        "SELECT DISTINCT module FROM declarations WHERE authority != 'lexical_text' "
        "OR type_status = 'lean-rendered' OR semantic_status != 'unavailable' "
        "OR rendered_type != COALESCE(type_text,'') "
        "OR conclusion_text != COALESCE(type_text,'') OR fingerprint != '' "
        "OR head != '' OR arity != 0 OR is_proposition != 0 "
        "OR helper_identity != '' OR lean_identity != '' "
        "UNION SELECT module FROM module_semantic_state WHERE status != 'lexical' "
        "OR compiled_fingerprint != '' OR surface_fingerprint != '' "
        "UNION SELECT module FROM structures WHERE authority != 'lexical_text'"
    )
    return {str(row[0]) for row in rows}


def clear_retained_projection(connection) -> None:
    """Clear supported owners after their original database has been archived."""
    from ladon.proofir_sqlite_v3 import project_envelopes

    project_envelopes(connection, [], exact_inventory=False, manage_user_version=False)
    for table in (
        "lineage_closures", "binders", "declaration_dependencies",
        "declaration_shapes", "structure_fields", "aliases",
    ):
        connection.execute(f"DELETE FROM {table}")
