"""Exact comparison inputs survive the disposable normalized projection."""

import json
import sqlite3

from support.proof_contract_native import contract_artifact

from ladon.proof_contract_artifacts import comparison_artifact
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import detached_content_id


def test_normalized_comparison_retains_both_exact_ordered_inputs_and_result():
    left, right = contract_artifact(), contract_artifact()
    right["payload"]["record"]["features"]["regularity"]["offset"] = 5
    right["artifactId"] = detached_content_id(right)
    analysis = comparison_artifact(left, right, analysis_id="analysis:stored")
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [left, right, analysis])
    validate_v3_database(connection)
    row = connection.execute(
        "SELECT stage,result_json FROM proofir_v3_contract_analyses WHERE owner_artifact_id=?",
        (analysis["artifactId"],),
    ).fetchone()
    assert row[0] == "comparison"
    assert json.loads(row[1]) == analysis["payload"]["result"]
    inputs = connection.execute(
        "SELECT contract_owner FROM proofir_v3_contract_analysis_inputs "
        "WHERE owner_artifact_id=? ORDER BY ordinal", (analysis["artifactId"],),
    ).fetchall()
    assert inputs == [(left["artifactId"],), (right["artifactId"],)]
