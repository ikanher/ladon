from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

import pytest
from support.proofir_v3_native import (
    claim_artifact,
    derivation_artifact,
    native_artifacts,
)

from ladon.proof_search_index import build_proof_search_index
from ladon.proof_search_v3_projection import catalog_projection_reconciliation
from ladon.proofir_catalog import PROOFIR_CONFIG_RELATIVE_PATH
from ladon.proofir_sqlite_v3 import (
    MAX_EXTENSION_BYTES,
    V3_QUERY_ACCESS_PATHS,
    V3_QUERY_SHAPES,
    create_v3_schema,
    project_envelopes,
    publish_v3_database,
    query_plan_evidence,
    redundant_named_indexes,
    validate_v3_query_plans,
)
from ladon.proofir_v3 import detached_content_id


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    create_v3_schema(connection)
    return connection


def recursive_derivation() -> dict[str, object]:
    artifact = copy.deepcopy(derivation_artifact())
    statement = artifact["payload"]["steps"][0]["premiseRefs"][0]  # type: ignore[index]
    step = artifact["payload"]["steps"][0]  # type: ignore[index]
    step["premiseRefs"] = [statement]
    step["conclusionRef"] = statement
    artifact["payload"]["acyclic"] = False  # type: ignore[index]
    artifact["payload"]["recursion"] = {  # type: ignore[index]
        "policy": "declared-strongly-connected-components",
        "components": [
            {
                "componentId": "scc:self",
                "semantics": "declared-recursive-fixed-point",
                "statementRefs": [statement],
            }
        ],
    }
    artifact["artifactId"] = detached_content_id(artifact)
    return artifact


def _assert_catalog_rejection_rows(connection: sqlite3.Connection) -> None:
    assert connection.execute("SELECT count(*) FROM proofir_artifacts").fetchone() == (2,)
    assert connection.execute("SELECT count(*) FROM proofir_diagnostics").fetchone() == (1,)
    assert connection.execute("SELECT count(*) FROM proofir_v3_claims").fetchone() == (1,)


def _assert_catalog_diagnostic(connection: sqlite3.Connection) -> None:
    diagnostic = json.loads(
        connection.execute("SELECT details_json FROM proofir_diagnostics").fetchone()[0]
    )
    assert diagnostic["stage"] == "kind-schema-valid"
    assert diagnostic["pointer"] == "/payload/assertionState"
    assert diagnostic["sourceRecordRetained"] is True
    assert diagnostic["semanticRowsProjected"] is False
    assert diagnostic["retained"] is False


def _assert_catalog_reconciliation(connection: sqlite3.Connection) -> None:
    reconciliation = catalog_projection_reconciliation(connection)
    assert reconciliation["canonicalCandidates"] == 2
    assert reconciliation["cataloged"] == reconciliation["projectedArtifacts"] == 1
    assert reconciliation["rejected"] == reconciliation["rejectedWithDiagnostics"] == 1
    assert reconciliation["omissions"] == 0
    assert reconciliation["complete"] is True
    assert reconciliation["normalizedRows"] > reconciliation["projectedArtifacts"]


def _assert_publication_metrics(metrics: dict[str, object]) -> None:
    assert metrics["accessPathGates"] == "passed"
    assert int(metrics["constructionPid"]) > 0
    assert metrics["statisticsRefreshed"] is True
    assert metrics["integrity"] == "ok"
    assert metrics["foreignKeyViolations"] == 0


def _assert_publication_accounting(metrics: dict[str, object]) -> None:
    reconciliation = metrics["reconciliation"]
    object_bytes = metrics["objectBytes"]
    assert isinstance(reconciliation, dict) and reconciliation["complete"] is True
    assert isinstance(object_bytes, dict) and object_bytes["proofir_v3_artifacts"] > 0
    assert int(metrics["schemaBytes"]) > 0
    assert int(metrics["marginalProjectionBytes"]) >= 0
    assert int(metrics["databaseBytes"]) >= int(metrics["schemaBytes"])
    assert float(metrics["buildSeconds"]) >= 0


def _skewed_native_artifacts() -> list[dict[str, object]]:
    templates = native_artifacts()
    templates.pop("proofir.environment")
    templates["proofir.recursive-fixture"] = recursive_derivation()
    artifacts = []
    for kind, template in templates.items():
        for index in range(40):
            artifact = copy.deepcopy(template)
            artifact["extensions"] = {
                "fixture.nonce/v1": {"index": index, "kind": kind}
            }
            if kind == "proofir.claim":
                artifact["extensions"]["unknown.large/v1"] = {  # type: ignore[index]
                    "blob": "x" * (MAX_EXTENSION_BYTES + 1),
                    "index": index,
                }
            artifact["artifactId"] = detached_content_id(artifact)
            artifacts.append(artifact)
    return artifacts


def _assert_registered_plan_evidence(connection: sqlite3.Connection) -> None:
    evidence = query_plan_evidence(connection)
    assert V3_QUERY_SHAPES.keys() == V3_QUERY_ACCESS_PATHS.keys()
    assert all(" LIMIT ?" in sql for sql in V3_QUERY_SHAPES.values())
    assert set(evidence) == set(V3_QUERY_SHAPES)
    assert all(row["tableRows"] > 0 for row in evidence.values())
    assert all(not row["temporaryOrder"] for row in evidence.values())
    assert all(row["selectionRequired"] for row in evidence.values())
    assert all(row["selected"] for row in evidence.values())


def test_recursive_derivation_projection_is_normalized_and_attributable() -> None:
    connection = database()
    artifact = recursive_derivation()
    project_envelopes(connection, [artifact])

    assert connection.execute(
        "SELECT derivation_id,acyclic,recursion_policy,source_pointer "
        "FROM proofir_v3_derivations"
    ).fetchone() == (
        "derivation:goal",
        0,
        "declared-strongly-connected-components",
        "/payload",
    )
    assert connection.execute(
        "SELECT component_id,ordinal,semantics,source_pointer "
        "FROM proofir_v3_derivation_sccs"
    ).fetchone() == (
        "scc:self",
        0,
        "declared-recursive-fixed-point",
        "/payload/recursion/components/0",
    )
    assert connection.execute(
        "SELECT component_id,ordinal,subject_kind,subject_local_id,source_pointer "
        "FROM proofir_v3_scc_members"
    ).fetchone() == (
        "scc:self",
        0,
        "statement",
        "statement:a",
        "/payload/recursion/components/0/statementRefs/0",
    )


def test_source_pointer_constraints_reject_non_pointer_and_bad_escape() -> None:
    connection = database()
    project_envelopes(connection, [claim_artifact()])
    for pointer in ("not-a-pointer", "/payload/~x", "/payload/~"):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE proofir_v3_claims SET source_pointer=?", (pointer,)
            )


def test_typed_reference_columns_reject_semantically_wrong_kinds() -> None:
    connection = database()
    project_envelopes(connection, [derivation_artifact()])
    for table, column, value in (
        ("proofir_v3_derivation_steps", "rule_kind", "statement"),
        ("proofir_v3_derivation_steps", "context_kind", "term"),
        ("proofir_v3_step_premises", "subject_kind", "declaration"),
        ("proofir_v3_step_conclusions", "subject_kind", "term"),
        ("proofir_v3_substitutions", "term_kind", "statement"),
    ):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE {table} SET {column}=?", (value,))


def test_large_unknown_extension_is_digest_bound_and_omitted_from_core() -> None:
    artifact = claim_artifact()
    artifact["extensions"] = {"unknown.large/v1": {"blob": "x" * (MAX_EXTENSION_BYTES + 1)}}
    artifact["artifactId"] = detached_content_id(artifact)
    connection = database()
    project_envelopes(connection, [artifact])

    payload_json, digest, state, original_bytes = connection.execute(
        "SELECT payload_json,payload_digest,storage_state,original_bytes "
        "FROM proofir_v3_extensions"
    ).fetchone()
    sentinel = json.loads(payload_json)
    assert state == "digest-sentinel"
    assert original_bytes > MAX_EXTENSION_BYTES
    assert sentinel == {
        "originalBytes": original_bytes,
        "sha256": digest,
        "truncated": True,
    }
    assert connection.execute(
        "SELECT reason_code,source_pointer FROM proofir_v3_omissions"
    ).fetchone() == (
        "extension-payload-byte-limit",
        "/extensions/unknown.large~1v1",
    )
    assert connection.execute(
        "SELECT assertion_state FROM proofir_v3_claims"
    ).fetchone() == ("asserted",)


def test_extension_changes_identity_but_not_core_claim_decisions() -> None:
    first = claim_artifact()
    second = copy.deepcopy(first)
    second["extensions"] = {"unknown.policy/v9": {"assertionState": "accepted"}}
    second["artifactId"] = detached_content_id(second)
    observed = []
    for artifact in (first, second):
        connection = database()
        project_envelopes(connection, [artifact])
        observed.append(
            connection.execute(
                "SELECT claim_id,statement_kind,statement_local_id,assertion_state,source_pointer "
                "FROM proofir_v3_claims"
            ).fetchone()
        )
    assert first["artifactId"] != second["artifactId"]
    assert observed[0] == observed[1] == (
        "claim:goal",
        "statement",
        "statement:goal",
        "asserted",
        "/payload",
    )


def test_catalog_retains_invalid_diagnostic_without_semantic_projection(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    (repository / "valid.json").write_text(
        json.dumps(claim_artifact()), encoding="utf-8"
    )
    invalid = claim_artifact()
    invalid["payload"]["assertionState"] = "verified"  # type: ignore[index]
    invalid["artifactId"] = detached_content_id(invalid)
    (repository / "invalid.json").write_text(json.dumps(invalid), encoding="utf-8")
    config = repository / PROOFIR_CONFIG_RELATIVE_PATH
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps({"artifacts": ["valid.json", "invalid.json"]}), encoding="utf-8"
    )

    result = build_proof_search_index(repository)
    with sqlite3.connect(result.index_path) as connection:
        _assert_catalog_rejection_rows(connection)
        _assert_catalog_diagnostic(connection)
        _assert_catalog_reconciliation(connection)


def test_populated_coverage_query_uses_covering_selector_index() -> None:
    artifacts = []
    for index in range(80):
        artifact = claim_artifact()
        artifact["coverage"]["population"]["selector"] = {"theorem": f"goal:{index}"}
        artifact["artifactId"] = detached_content_id(artifact)
        artifacts.append(artifact)
    connection = database()
    project_envelopes(connection, artifacts)
    connection.execute("ANALYZE")
    selector = json.dumps({"theorem": "goal:40"}, separators=(",", ":"), sort_keys=True)
    plan = connection.execute(
        "EXPLAIN QUERY PLAN SELECT content_artifact_id FROM proofir_v3_coverage "
        "WHERE population_kind IN ('theorem-evidence','artifact-subjects') "
        "AND selector_json=? ORDER BY content_artifact_id LIMIT ?",
        (selector, 10),
    ).fetchall()
    rendered = " ".join(str(row) for row in plan)
    assert "SEARCH proofir_v3_coverage USING COVERING INDEX idx_v3_coverage_selector" in rendered


def test_publication_reports_accounting_pid_and_preserves_prior_on_budget_failure(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "proofir.sqlite3"
    metrics = publish_v3_database(destination, [claim_artifact()])
    prior = destination.read_bytes()
    _assert_publication_metrics(metrics)
    _assert_publication_accounting(metrics)
    assert all(
        f".{destination.name}.{metrics['constructionPid']}." not in path.name
        for path in tmp_path.iterdir()
    )

    with pytest.raises(ValueError, match="complete-database byte limit"):
        publish_v3_database(
            destination, [recursive_derivation()], max_database_bytes=1
        )
    assert destination.read_bytes() == prior


def test_registered_query_plan_gate_passes_on_native_population() -> None:
    connection = database()
    project_envelopes(connection, _skewed_native_artifacts())
    connection.execute("ANALYZE")
    validate_v3_query_plans(connection)
    _assert_registered_plan_evidence(connection)
    assert redundant_named_indexes(connection) == []
