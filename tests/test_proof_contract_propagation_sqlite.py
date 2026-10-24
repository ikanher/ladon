"""Native propagation projection enforces exact ownership and rebuild boundaries."""

import sqlite3

import pytest
from test_proof_contract_propagation_native import artifact, inputs

from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database


def database():
    graph, contracts, request = inputs()
    result = artifact(graph, contracts, request)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [graph, *contracts, result])
    return connection, graph, contracts, result


@pytest.mark.parametrize("field,value", [
    ("derivation_owner", "sha256:" + "f" * 64),
    ("goal_local_id", "statement:foreign"),
    ("goal_kind", "contract"),
])
def test_projection_rejects_foreign_or_wrongly_typed_goals_and_rolls_back(field, value):
    connection, graph, _, _ = database()
    with pytest.raises(sqlite3.IntegrityError), connection:
        connection.execute(f"UPDATE proofir_v3_contract_analysis_derivations SET {field}=?", (value,))
    row = connection.execute(
        "SELECT derivation_owner,goal_kind,goal_local_id FROM proofir_v3_contract_analysis_derivations"
    ).fetchone()
    assert row == (graph["artifactId"], "statement", "statement:goal")
    validate_v3_database(connection)


def test_exact_goal_lookup_uses_named_covering_index():
    connection, graph, _, _ = database()
    plan = connection.execute(
        "EXPLAIN QUERY PLAN SELECT owner_artifact_id FROM proofir_v3_contract_analysis_derivations "
        "WHERE derivation_owner=? AND goal_kind=? AND goal_local_id=?",
        (graph["artifactId"], "statement", "statement:goal"),
    ).fetchall()
    assert "idx_v3_contract_analysis_derivation" in str(plan)


def test_complete_rebuild_removes_previous_analysis_and_exact_goal_rows():
    connection, graph, contracts, _ = database()
    project_envelopes(connection, [graph, *contracts])
    assert connection.execute("SELECT count(*) FROM proofir_v3_contract_analyses").fetchone() == (0,)
    assert connection.execute(
        "SELECT count(*) FROM proofir_v3_contract_analysis_derivations"
    ).fetchone() == (0,)
    validate_v3_database(connection)


def test_previous_disposable_schema_requires_explicit_rebuild():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA user_version=10")
    graph, contracts, request = inputs()
    result = artifact(graph, contracts, request)
    with pytest.raises(RuntimeError, match="rebuild"):
        project_envelopes(connection, [graph, *contracts, result])
    assert connection.execute("PRAGMA user_version").fetchone() == (10,)
