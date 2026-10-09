from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

import pytest
from support.semantic_evidence import (
    check_ref as _check_ref,
)
from support.semantic_evidence import (
    digest as _digest,
)
from support.semantic_evidence import (
    semantic_evidence,
    semantic_receipt,
)

from ladon.semantic_result_projection import (
    DIRECT_PROJECTION_MAX_BYTES,
    DISCOVERY_PROJECTION_MAX_BYTES,
    SemanticProjectionError,
    project_semantic_result,
    semantic_projection_bytes,
)


def _artifacts(
    label: str = "main",
    *,
    candidate: str | None = None,
    status: str = "accepted",
    scratch: bool = False,
    application_term: str | None = None,
    substitutions: tuple[dict[str, Any], ...] = (),
    residual_premises: tuple[dict[str, Any], ...] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    artifacts, registry, _receipt = semantic_evidence(
        label,
        candidate=candidate,
        status=status,
        scratch=scratch,
        application_term=application_term,
        substitutions=substitutions,
        residual_premises=residual_premises,
    )
    return artifacts, registry


def _receipt(
    label: str = "main",
    *,
    candidate: str | None = None,
    status: str = "accepted",
    scratch: bool = False,
) -> dict[str, Any]:
    return semantic_receipt(
        label,
        candidate=candidate,
        status=status,
        scratch=scratch,
    )


def _direct_payload() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    substitutions = (
        {
            "variable": "α",
            "termDisplay": "Nat",
            "termStructural": "Lean.Expr.const `Nat []",
        },
    )
    artifacts, registry = _artifacts(substitutions=substitutions)
    environment_ref = artifacts[0]["environmentRef"]
    check_artifact_ref = artifacts[1]["artifactId"]
    return (
        {
            "schema": "ladon-semantic-candidate-check-result-v1",
            "operation": "check-candidate",
            "status": "accepted",
            "applicationTerm": "Main.main",
            "substitutions": list(substitutions),
            "residualPremises": [],
            "dischargedHypotheses": [],
            "checkRunId": _check_ref("main"),
            "checkRunRef": {
                "artifactRef": check_artifact_ref,
                "kind": "check-run",
                "localId": _check_ref("main"),
            },
            "environmentRef": environment_ref,
            "evidenceReceipt": _receipt(),
            "artifacts": artifacts,
            "diagnostic": None,
            "resourceAccounting": {"elapsedSeconds": 0.25, "peakRssBytes": 1024},
            "limitations": [{"id": "authority", "message": "bounded observation"}],
        },
        registry,
    )


def _discovery_payload() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    artifacts, registry = _artifacts()
    accepted = {
        "status": "accepted",
        "applicationTerm": "Main.main",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "environmentRef": artifacts[0]["environmentRef"],
        "checkRunRef": _check_ref("main"),
        "evidenceReceipt": _receipt(),
        "artifacts": artifacts,
        "candidateSubject": {
            "typeDisplay": "True",
            "typeStructural": "Lean.Expr.const `True []",
        },
    }
    failed = {
        "status": "failed-checker",
        "diagnostic": {"code": "process-failed", "message": "Lean exited"},
        "failureStage": "checker-process",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "artifacts": [],
    }
    payload = {
        "schema": "ladon-verified-discovery-result-v1",
        "operation": "discover",
        "status": "partial",
        "request": {
            "module": "Main",
            "goal": "True",
            "localContext": [],
            "scope": "repository",
            "roots": [],
            "freshness": "stored",
            "maxCandidates": 2,
        },
        "candidates": [
            {
                "name": "Main.main",
                "shortlist": {
                    "module": "Main",
                    "path": "Main.lean",
                    "line": 1,
                    "bucket": "exact",
                    "shortlistOrdinal": 0,
                    "fieldContributions": {"typeText": True},
                    "typeText": "True",
                },
                "check": accepted,
            },
            {
                "name": "Main.failed",
                "shortlist": {
                    "module": "Main",
                    "path": "Main.lean",
                    "line": 2,
                    "shortlistOrdinal": 1,
                },
                "check": failed,
            },
        ],
        "coverage": {
            "shortlisted": 2,
            "submitted": 2,
            "completed": 1,
            "failed": 1,
            "truncated": False,
        },
        "shortlist": {
            "source": "type-text-shortlist",
            "pattern": "True",
            "coverage": {"returned": 2},
            "omissions": [],
        },
        "ranking": {
            "policy": "verified-status-priority-v1",
            "contributions": [
                {"candidate": "Main.main", "status": "accepted", "priority": 0},
                {"candidate": "Main.failed", "status": "failed-checker", "priority": 6},
            ],
        },
        "nonclaims": ["Lexical shortlisting is not Lean applicability."],
    }
    return payload, registry


def _mapping_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        return set(value).union(*(_mapping_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_mapping_keys(item) for item in value), set())
    return set()


def test_audit_is_an_unchanged_detached_canonical_payload() -> None:
    payload, _registry = _direct_payload()
    projected = project_semantic_result(payload, projection="audit")

    assert projected == payload
    assert projected is not payload
    projected["artifacts"].clear()
    assert payload["artifacts"]
@pytest.mark.parametrize("projection", ["llm", "review"])
def test_direct_projection_is_compact_reference_closed_and_nonstructural(
    projection: str,
) -> None:
    payload, registry = _direct_payload()
    projected = project_semantic_result(
        payload, projection=projection, registered_artifacts=registry
    )

    check = projected["candidate"]["check"]
    assert projected["schema"] == "ladon-semantic-candidate-projection-v1"
    assert check["environmentRef"] == {
        "artifactRef": payload["artifacts"][0]["artifactId"],
        "environmentRef": payload["artifacts"][0]["environmentRef"],
    }
    assert check["checkRunRef"] == {
        "artifactRef": payload["artifacts"][1]["artifactId"],
        "kind": "check-run",
        "localId": _check_ref("main"),
    }
    assert "artifacts" not in _mapping_keys(projected)
    assert not {"typeStructural", "termStructural", "valueStructural"} & _mapping_keys(projected)
    assert projected["coverage"]["operationalFailure"] is False
    assert len(semantic_projection_bytes(projected)) <= DIRECT_PROJECTION_MAX_BYTES


def test_discovery_projection_retains_complete_status_accounting_and_failure() -> None:
    payload, registry = _discovery_payload()
    projected = project_semantic_result(payload, projection="llm", registered_artifacts=registry)

    population = projected["coverage"]["candidatePopulation"]
    assert population == {
        "observed": 2,
        "projected": 2,
        "omitted": 0,
        "statusCounts": {"accepted": 1, "failed-checker": 1},
        "scratchStatusCounts": {},
        "closedAccepted": 1,
        "applicableWithResiduals": 0,
    }
    assert projected["coverage"]["operationalFailure"] is True
    assert [row["check"]["status"] for row in projected["candidates"]] == [
        "accepted",
        "failed-checker",
    ]
    assert len(semantic_projection_bytes(projected)) <= DISCOVERY_PROJECTION_MAX_BYTES


def test_projection_fails_closed_for_missing_or_mismatched_registration() -> None:
    payload, registry = _direct_payload()
    check_artifact_ref = payload["artifacts"][1]["artifactId"]
    registry.pop(check_artifact_ref)
    with pytest.raises(SemanticProjectionError, match="not registered"):
        project_semantic_result(payload, projection="llm", registered_artifacts=registry)

    _payload, registry = _direct_payload()
    check_artifact_ref = _payload["artifacts"][1]["artifactId"]
    registry[check_artifact_ref]["artifactKind"] = "proofir.environment"
    with pytest.raises(SemanticProjectionError, match="mismatched kind"):
        project_semantic_result(_payload, projection="llm", registered_artifacts=registry)

    payload, registry = _direct_payload()
    payload["checkRunRef"]["artifactRef"] = _digest("foreign-check")
    with pytest.raises(SemanticProjectionError, match="artifact-qualified"):
        project_semantic_result(payload, projection="llm", registered_artifacts=registry)


def test_scratch_uses_qualified_evidence_and_never_exposes_bare_parent_ref() -> None:
    payload, registry = _direct_payload()
    scratch_artifacts, scratch_registry = _artifacts(
        "scratch", candidate="Main.main", status="compiled", scratch=True
    )
    registry.update(scratch_registry)
    payload["scratch"] = {
        "status": "compiled",
        "applicationTerm": "Main.main",
        "sourceDigest": _digest("scratch-source:scratch"),
        "environmentRef": scratch_artifacts[0]["environmentRef"],
        "checkRunRef": _check_ref("scratch"),
        "parentCheckRunRef": _check_ref("main"),
        "evidenceReceipt": _receipt(
            "scratch", candidate="Main.main", status="compiled", scratch=True
        ),
        "artifacts": scratch_artifacts,
    }

    projected = project_semantic_result(payload, projection="review", registered_artifacts=registry)

    scratch = projected["candidate"]["check"]["scratch"]
    assert scratch["environmentRef"] == {
        "environmentRef": scratch_artifacts[0]["environmentRef"],
        "artifactRef": scratch_artifacts[0]["artifactId"],
    }
    assert scratch["checkRunRef"] == {
        "artifactRef": scratch_artifacts[1]["artifactId"],
        "kind": "check-run",
        "localId": _check_ref("scratch"),
    }
    assert "parentCheckRunRef" not in _mapping_keys(projected)


def test_projection_is_deterministic_and_does_not_mutate_canonical_result() -> None:
    payload, registry = _discovery_payload()
    original = copy.deepcopy(payload)
    first = project_semantic_result(payload, projection="review", registered_artifacts=registry)
    second = project_semantic_result(payload, projection="review", registered_artifacts=registry)

    assert first == second
    assert first["projection"]["projectionIdentity"].startswith("sha256:")
    assert payload == original


def test_bloated_discovery_is_bounded_with_explicit_population_omissions() -> None:
    payload, registry = _discovery_payload()
    template = payload["candidates"][0]
    payload["candidates"] = []
    for index in range(40):
        candidate = "Main." + ("longName" * 200) + str(index)
        application_term = "term " * 2000
        residual_premises = tuple(
            {"typeDisplay": "premise " * 500, "typeStructural": "hidden"}
            for _ in range(20)
        )
        artifacts, row_registry = _artifacts(
            f"candidate-{index}",
            candidate=candidate,
            status="applicable-with-residuals",
            application_term=application_term,
            residual_premises=residual_premises,
        )
        registry.update(row_registry)
        receipt = _receipt(
            f"candidate-{index}",
            candidate=candidate,
            status="applicable-with-residuals",
        )
        row = copy.deepcopy(template)
        row["name"] = candidate
        row["check"].update(
            {
                "status": "applicable-with-residuals",
                "applicationTerm": application_term,
                "environmentRef": artifacts[0]["environmentRef"],
                "checkRunRef": _check_ref(f"candidate-{index}"),
                "evidenceReceipt": receipt,
                "artifacts": artifacts,
                "residualPremises": list(residual_premises),
            }
        )
        payload["candidates"].append(row)
    payload["status"] = "available"
    payload["request"]["maxCandidates"] = 40
    payload["coverage"] = {
        "shortlisted": 40,
        "submitted": 40,
        "completed": 40,
        "accepted": 40,
        "truncated": False,
    }

    projected = project_semantic_result(payload, projection="review", registered_artifacts=registry)

    population = projected["coverage"]["candidatePopulation"]
    assert population["observed"] == 40
    assert population["closedAccepted"] == 0
    assert population["applicableWithResiduals"] == 40
    assert projected["coverage"]["canonical"]["accepted"] == 40
    assert population["omitted"] > 0
    assert any(row["pointer"] == "/candidates" for row in projected["omissions"])
    assert len(semantic_projection_bytes(projected)) <= DISCOVERY_PROJECTION_MAX_BYTES


def test_checker_backed_direct_result_requires_exact_canonical_rows() -> None:
    payload, registry = _direct_payload()
    payload.pop("substitutions")
    payload.pop("residualPremises")

    with pytest.raises(SemanticProjectionError, match="substitutions disagrees"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts=registry
        )
