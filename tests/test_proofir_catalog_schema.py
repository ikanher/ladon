from __future__ import annotations

import sqlite3

from ladon.proof_search_schema import (
    EXPECTED_FOREIGN_KEYS,
    REQUIRED_LOOKUP_INDEX_COLUMNS,
    create_proof_search_schema,
    schema_foreign_keys,
    schema_index_columns,
    schema_lookup_indexes,
)


def test_proofir_catalog_schema_has_constraints_and_lookup_indexes() -> None:
    with sqlite3.connect(":memory:") as connection:
        create_proof_search_schema(connection)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table'"
            )
        }
        assert {
            "proofir_generations",
            "proofir_artifacts",
            "proofir_relations",
            "proofir_diagnostics",
        } <= tables
        assert REQUIRED_LOOKUP_INDEX_COLUMNS.keys() <= schema_lookup_indexes(connection)
        assert schema_index_columns(connection) == REQUIRED_LOOKUP_INDEX_COLUMNS
        assert EXPECTED_FOREIGN_KEYS <= schema_foreign_keys(connection)


def test_proofir_catalog_schema_rejects_orphan_relation() -> None:
    with sqlite3.connect(":memory:") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        create_proof_search_schema(connection)
        connection.execute(
            "INSERT INTO proofir_generations VALUES ('g', '{}', 0, 0, 1, 'configured')"
        )
        try:
            connection.execute(
                "INSERT INTO proofir_relations VALUES ('r', 'g', 'missing', 'missing2', 'checks', '{}')"
            )
        except sqlite3.IntegrityError as exc:
            assert "FOREIGN KEY constraint failed" in str(exc)
        else:
            raise AssertionError("orphan ProofIR relation was accepted")
