from __future__ import annotations

import copy
import sqlite3

import pytest
from support.proofir_v3_native import (
    ENVIRONMENT,
    check_run_artifact,
    claim_artifact,
    derivation_artifact,
    governance_observation_artifact,
    ref,
)

from ladon.proofir_derivation import navigation_path
from ladon.proofir_observations import (
    CheckRun,
    Coverage,
    EvidenceDimensions,
    EvidenceObservation,
    Limitation,
)
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3 import ProofIRV3Error, detached_content_id, validate_envelope
from ladon.proofir_v3_queries import query_v3_theorem_evidence, query_v3_triage


@pytest.mark.parametrize(
    ("field", "values"),
    [
        ("assertion_state", ("asserted", "denied", "unknown")),
        ("semantic_validation", ("unchecked", "accepted", "rejected", "failed")),
        ("freshness", ("fresh", "stale", "unknown")),
        ("attachment_result", ("exact", "strong", "ambiguous", "unattached")),
        ("coverage", ("complete", "partial", "unavailable")),
        (
            "replay_relationship",
            ("exact-input", "stale-input", "foreign-input", "unbound"),
        ),
        (
            "authority_basis",
            (
                "kernel-check",
                "elaborator-check",
                "producer-assertion",
                "source-observation",
                "external-attestation",
                "process-observation",
                "policy-observation",
            ),
        ),
        (
            "guarantee_scope",
            (
                "declaration-type",
                "declaration-value",
                "build",
                "route",
                "source-surface",
                "schema-only",
                "process-exit",
                "none",
            ),
        ),
    ],
)
def test_orthogonal_dimension_truth_table(field: str, values: tuple[str, ...]) -> None:
    for value in values:
        dimensions = EvidenceDimensions(**{field: value})
        assert (
            dimensions.to_dict()[
                {
                    "assertion_state": "assertionState",
                    "semantic_validation": "semanticValidation",
                    "freshness": "freshness",
                    "attachment_result": "attachmentResult",
                    "coverage": "coverage",
                    "replay_relationship": "replayRelationship",
                    "authority_basis": "authorityBasis",
                    "guarantee_scope": "guaranteeScope",
                }[field]
            ]
            == value
        )


def test_unknown_dimension_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="semanticValidation"):
        EvidenceDimensions(semantic_validation="verified")


@pytest.mark.parametrize(
    "producer_fields",
    [
        {"status": "verified"},
        {"sourceHash": "sha256:" + "a" * 64},
        {"processReturnCode": 0},
        {"attachmentConfidence": "exact"},
    ],
)
def test_quoted_producer_fields_do_not_promote_semantic_acceptance(
    producer_fields: dict[str, object],
) -> None:
    observation = EvidenceObservation(
        observation_id="observation:source",
        subject_ref={"kind": "statement", "localId": "statement:goal"},
        environment_ref=ENVIRONMENT,
        observation_kind="source-attachment",
        result="observed",
        dimensions=EvidenceDimensions(
            assertion_state="asserted",
            semantic_validation="unchecked",
            freshness="fresh",
            attachment_result="exact",
            authority_basis="source-observation",
            guarantee_scope="source-surface",
        ),
        producer={"name": "fixture", "version": "1"},
        limitations=(
            Limitation(
                "does-not-establish-theorem-truth",
                "Source evidence is not checker acceptance.",
            ),
        ),
        supporting_artifact_id="sha256:" + "c" * 64,
        extensions={"producer.example/v1": producer_fields},
    ).to_dict()
    assert observation["dimensions"]["semanticValidation"] == "unchecked"
    assert observation["dimensions"]["attachmentResult"] == "exact"
    assert "theoremTruth" not in observation


def test_check_run_keeps_process_outcome_separate_from_subject_results() -> None:
    row = CheckRun(
        check_run_id="check:run",
        check_kind="lean-kernel",
        checker={
            "name": "Lean",
            "version": "4.20.0",
            "implementationDigest": "sha256:" + "1" * 64,
            "executableDigest": "sha256:" + "2" * 64,
        },
        environment_ref=ENVIRONMENT,
        input_artifact_ids=("sha256:" + "3" * 64,),
        operation="check-declaration",
        process_outcome="success",
        subject_results=(),
        stdout_digest="sha256:" + "4" * 64,
        stderr_digest="sha256:" + "5" * 64,
        resource_bounds={"timeoutMs": 1000, "maxOutputBytes": 4096},
        guarantee={"scope": "none", "authorityBasis": "process-observation"},
    ).to_dict()
    assert row["processOutcome"] == "success"
    assert row["subjectResults"] == []
    assert row["guarantee"]["scope"] == "none"


def test_native_check_run_requires_exact_outputs_bounds_and_scoped_acceptance() -> None:
    artifact = check_run_artifact()
    artifact["payload"]["outputs"]["stdoutDigest"] = "not-a-digest"
    artifact["artifactId"] = detached_content_id(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.pointer == "/payload/outputs/stdoutDigest"

    artifact = check_run_artifact()
    artifact["payload"]["results"] = []
    artifact["artifactId"] = detached_content_id(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.code == "unscoped-checker-guarantee"


def test_coverage_is_population_scoped_and_validates_monotone_counts() -> None:
    row = Coverage(
        status="partial",
        population_kind="declarations-in-import-closure",
        selector={"theorem": "Fixture.goal"},
        universe_known=True,
        expected=2,
        discovered=2,
        decoded=2,
        valid=1,
        projected=1,
        query_matched=0,
        omitted=(
            {
                "pointer": "/subjects/1",
                "stage": "semantic-valid",
                "reasonCode": "timeout",
            },
        ),
        bounds={"maxSubjects": 10},
    ).to_dict()
    assert row["status"] == "partial"
    assert row["population"]["selector"] == {"theorem": "Fixture.goal"}
    assert row["queryMatched"] == 0
    with pytest.raises(ValueError, match="coverage counts"):
        Coverage(
            status="complete",
            population_kind="declarations",
            selector={},
            universe_known=True,
            expected=1,
            discovered=1,
            decoded=2,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "complete", "universe_known": False},
        {
            "status": "complete",
            "omitted": ({"pointer": "/subjects/0", "reasonCode": "timeout"},),
        },
        {
            "status": "unavailable",
            "universe_known": True,
            "expected": 1,
            "discovered": 1,
            "decoded": 1,
            "valid": 1,
            "projected": 1,
            "query_matched": 1,
        },
    ],
)
def test_coverage_status_cannot_contradict_population_evidence(
    overrides: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "status": "complete",
        "population_kind": "declarations",
        "selector": {"theorem": "Fixture.goal"},
        "universe_known": True,
        "expected": 1,
        "discovered": 1,
        "decoded": 1,
        "valid": 1,
        "projected": 1,
        "query_matched": 1,
    }
    values.update(overrides)
    with pytest.raises(ValueError, match="coverage status"):
        Coverage(**values)


def test_native_coverage_rejects_the_same_status_contradictions() -> None:
    artifact = claim_artifact()
    artifact["coverage"]["universeKnown"] = False
    artifact["artifactId"] = detached_content_id(artifact)
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope(artifact)
    assert captured.value.diagnostic.code == "contradictory-coverage-status"
    assert captured.value.diagnostic.pointer == "/coverage/status"


@pytest.mark.parametrize("bad_count", [1.5, "1", True])
def test_coverage_rejects_non_integer_counts(bad_count: object) -> None:
    with pytest.raises(ValueError, match="coverage counts"):
        Coverage(
            status="partial",
            population_kind="theorem-evidence",
            selector={"theorem": "Fixture.goal"},
            universe_known=True,
            expected=bad_count,
        )


def test_dossier_renders_typed_dimensions_and_stable_limitations() -> None:
    artifact = governance_observation_artifact()
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [artifact])
    dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=20)
    row = dossier["observations"]["rows"][0]
    assert row["dimensions"] == artifact["payload"]["dimensions"]
    assert row["producer"] == artifact["producer"]
    assert row["environmentRef"] == ENVIRONMENT
    assert row["supportingArtifactId"] == artifact["artifactId"]
    assert row["limitations"] == artifact["limitations"]
    assert row["sourcePointer"] == "/payload"
    assert {item["id"] for item in dossier["limitations"]["rows"]} >= {
        "evidence-not-theorem-truth",
        "navigation-not-complete-proof-slice",
    }


def test_theorem_absence_never_borrows_repository_wide_coverage() -> None:
    artifact = claim_artifact()
    artifact["coverage"]["population"]["selector"] = {"repository": "fixture"}
    artifact["artifactId"] = detached_content_id(artifact)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [artifact])
    dossier = query_v3_theorem_evidence(connection, "statement:missing", limit=20)
    assert dossier["status"] == "not-observed"
    assert dossier["coverage"]["applicability"] == "unavailable"
    assert dossier["coverage"]["rows"] == []
    assert dossier["coverage"]["reason"] == "no exact theorem selector"


def test_repository_population_with_theorem_key_is_not_theorem_coverage() -> None:
    artifact = claim_artifact()
    other = {"kind": "statement", "localId": "statement:other"}
    artifact["subjectRefs"] = [other]
    artifact["payload"]["statementRef"] = other
    artifact["coverage"]["population"] = {
        "kind": "repository",
        "selector": {"theorem": "statement:goal"},
    }
    artifact["coverage"]["queryMatched"] = 0
    artifact["artifactId"] = detached_content_id(artifact)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [artifact])
    dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=20)
    assert dossier["coverage"]["applicability"] == "unavailable"
    assert dossier["coverage"]["rows"] == []


def test_exact_theorem_population_can_report_observed_absence() -> None:
    artifact = claim_artifact()
    other = {"kind": "statement", "localId": "statement:other"}
    artifact["subjectRefs"] = [other]
    artifact["payload"]["statementRef"] = other
    artifact["coverage"]["population"] = {
        "kind": "theorem-evidence",
        "selector": {"theorem": "statement:goal"},
    }
    artifact["coverage"]["queryMatched"] = 0
    artifact["artifactId"] = detached_content_id(artifact)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [artifact])
    dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=20)
    assert dossier["status"] == "not-observed"
    assert dossier["coverage"]["applicability"] == "applicable"
    coverage = dossier["coverage"]["rows"][0]
    assert coverage["queryMatched"] == 0
    assert coverage["status"] == "complete"
    assert coverage["universeKnown"]
    assert coverage["expected"] == coverage["discovered"] == coverage["decoded"]
    assert coverage["valid"] == coverage["projected"]
    assert coverage["bounds"] == {"maxSubjects": 1000}


def test_theorem_lookup_does_not_match_non_statement_local_id() -> None:
    artifact = governance_observation_artifact()
    declaration = {"kind": "declaration", "localId": "statement:goal"}
    artifact["subjectRefs"] = [declaration]
    artifact["payload"]["subjectRef"] = declaration
    artifact["artifactId"] = detached_content_id(artifact)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [artifact])
    dossier = query_v3_theorem_evidence(connection, "statement:goal", limit=20)
    assert dossier["status"] == "not-observed"
    assert dossier["subjects"]["rows"] == []
    assert dossier["observations"]["rows"] == []


def test_theorem_coverage_query_has_selector_index() -> None:
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [claim_artifact()])
    indexes = {
        tuple(info[2] for info in connection.execute(f"PRAGMA index_info({row[1]})"))
        for row in connection.execute("PRAGMA index_list(proofir_v3_coverage)")
    }
    # Supersedes the population-first assertion: the production query selects
    # one selector across accepted populations and orders by artifact identity.
    assert ("selector_json", "content_artifact_id", "population_kind") in indexes
    plan = " ".join(
        str(row[3])
        for row in connection.execute(
            "EXPLAIN QUERY PLAN SELECT content_artifact_id FROM proofir_v3_coverage "
            "WHERE population_kind IN ('theorem-evidence','artifact-subjects') "
            "AND selector_json=? "
            "ORDER BY content_artifact_id LIMIT ?",
            ('{"theorem":"Fixture.goal"}', 20),
        )
    )
    assert "idx_v3_coverage_selector" in plan
    assert "TEMP B-TREE" not in plan


def test_navigation_result_has_stable_limitation_identifier() -> None:
    result = navigation_path(
        derivation_artifact(),
        ref("statement", "statement:a"),
        ref("statement", "statement:goal"),
    )
    assert {
        "id": "navigation-not-complete-proof-slice",
        "message": "A navigation route is not a complete derivation slice.",
    } in result["limitations"]


@pytest.mark.parametrize("semantic_result", ["rejected", "failed"])
def test_triage_uses_semantic_validation_not_free_form_result(
    semantic_result: str,
) -> None:
    artifact = governance_observation_artifact()
    artifact = copy.deepcopy(artifact)
    artifact["payload"]["result"] = "producer-verified"
    artifact["payload"]["dimensions"]["semanticValidation"] = semantic_result
    artifact["artifactId"] = detached_content_id(artifact)
    connection = sqlite3.connect(":memory:")
    project_envelopes(connection, [artifact])
    triage = query_v3_triage(connection, limit=20)
    assert triage == [
        {
            "artifactId": artifact["artifactId"],
            "observationId": "observation:1",
            "subject": {
                "ownerArtifactId": artifact["artifactId"],
                "kind": "statement",
                "localId": "statement:goal",
            },
            "result": "producer-verified",
            "semanticValidation": semantic_result,
            "ruleId": "v3_observation_issue",
        }
    ]
