from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from typing import Any

import pytest

from ladon.semantic_result_projection import (
    DIRECT_PROJECTION_MAX_BYTES,
    DISCOVERY_PROJECTION_MAX_BYTES,
    SemanticProjectionError,
    project_semantic_result,
    semantic_projection_bytes,
)


def _digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def _check_ref(label: str) -> str:
    return "check:" + hashlib.sha256(label.encode()).hexdigest()


def _artifacts(label: str = "main") -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    environment_ref = _digest("environment")
    check_ref = _check_ref(label)
    environment = {
        "artifactId": _digest("environment-artifact"),
        "artifactKind": "proofir.environment",
        "environmentRef": environment_ref,
        "payload": {"compiledModules": [{"module": "Main", "digest": _digest("olean")}]},
    }
    check = {
        "artifactId": _digest(f"check-artifact:{label}"),
        "artifactKind": "proofir.check-run",
        "environmentRef": environment_ref,
        "payload": {"checkRunId": check_ref},
    }
    registry = {
        row["artifactId"]: {
            "artifactId": row["artifactId"],
            "artifactKind": row["artifactKind"],
        }
        for row in (environment, check)
    }
    return [environment, check], registry


def _receipt(label: str = "main") -> dict[str, Any]:
    return {
        "schema": "ladon-evidence-receipt-v1",
        "subject": {
            "module": "Main",
            "candidate": f"Main.{label}",
            "goal": "True",
            "localContext": [],
        },
        "executionBinding": "explicit-pinned",
        "observationState": "live",
        "operationOutcome": "accepted",
        "authorityBasis": "elaborator-check",
        "analysisCompleteness": "complete",
        "sourceFreshness": "cached-observed",
        "environmentMatch": "exact",
        "environmentRef": _digest("environment"),
        "checkRunRef": _check_ref(label),
        "receiptIdentity": _digest(f"receipt:{label}"),
        "limitations": [],
    }


def _direct_payload() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    artifacts, registry = _artifacts()
    return (
        {
            "schema": "ladon-semantic-candidate-check-result-v1",
            "operation": "check-candidate",
            "status": "accepted",
            "applicationTerm": "Main.main",
            "substitutions": [
                {
                    "variable": "α",
                    "termDisplay": "Nat",
                    "termStructural": "Lean.Expr.const `Nat []",
                }
            ],
            "residualPremises": [],
            "dischargedHypotheses": [],
            "checkRunId": _check_ref("main"),
            "checkRunRef": {
                "artifactRef": _digest("check-artifact:main"),
                "kind": "check-run",
                "localId": _check_ref("main"),
            },
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
        "environmentRef": _digest("environment"),
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
        "resultIdentity": _digest("producer-result"),
        "request": {
            "module": "Main",
            "goal": "True",
            "localContext": [],
            "scope": "repository",
            "roots": [],
            "freshness": "stored",
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
        "coverage": {"submitted": 2, "completed": 1, "failed": 1},
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
        "artifactRef": _digest("environment-artifact"),
        "environmentRef": _digest("environment"),
    }
    assert check["checkRunRef"] == {
        "artifactRef": _digest("check-artifact:main"),
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
    }
    assert projected["coverage"]["operationalFailure"] is True
    assert [row["check"]["status"] for row in projected["candidates"]] == [
        "accepted",
        "failed-checker",
    ]
    assert len(semantic_projection_bytes(projected)) <= DISCOVERY_PROJECTION_MAX_BYTES


def test_projection_fails_closed_for_missing_or_mismatched_registration() -> None:
    payload, registry = _direct_payload()
    registry.pop(_digest("check-artifact:main"))
    with pytest.raises(SemanticProjectionError, match="not registered"):
        project_semantic_result(payload, projection="llm", registered_artifacts=registry)

    _payload, registry = _direct_payload()
    registry[_digest("check-artifact:main")]["artifactKind"] = "proofir.environment"
    with pytest.raises(SemanticProjectionError, match="mismatched kind"):
        project_semantic_result(_payload, projection="llm", registered_artifacts=registry)

    payload, registry = _direct_payload()
    payload["checkRunRef"]["artifactRef"] = _digest("foreign-check")
    with pytest.raises(SemanticProjectionError, match="artifact-qualified"):
        project_semantic_result(payload, projection="llm", registered_artifacts=registry)


def test_scratch_uses_qualified_evidence_and_never_exposes_bare_parent_ref() -> None:
    payload, registry = _direct_payload()
    scratch_artifacts, scratch_registry = _artifacts("scratch")
    registry.update(scratch_registry)
    payload["scratch"] = {
        "status": "compiled",
        "environmentRef": _digest("environment"),
        "checkRunRef": _check_ref("scratch"),
        "parentCheckRunRef": _check_ref("main"),
        "evidenceReceipt": _receipt("scratch"),
        "artifacts": scratch_artifacts,
    }

    projected = project_semantic_result(payload, projection="review", registered_artifacts=registry)

    scratch = projected["candidate"]["check"]["scratch"]
    assert scratch["environmentRef"] == {
        "environmentRef": _digest("environment"),
        "artifactRef": _digest("environment-artifact"),
    }
    assert scratch["checkRunRef"] == {
        "artifactRef": _digest("check-artifact:scratch"),
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
        artifacts, row_registry = _artifacts(f"candidate-{index}")
        registry.update(row_registry)
        receipt = _receipt(f"candidate-{index}")
        row = copy.deepcopy(template)
        row["name"] = "Main." + ("longName" * 200) + str(index)
        row["check"].update(
            {
                "applicationTerm": "term " * 2000,
                "environmentRef": _digest("environment"),
                "checkRunRef": _check_ref(f"candidate-{index}"),
                "evidenceReceipt": receipt,
                "artifacts": artifacts,
                "residualPremises": [
                    {"typeDisplay": "premise " * 500, "typeStructural": "hidden"} for _ in range(20)
                ],
            }
        )
        payload["candidates"].append(row)

    projected = project_semantic_result(payload, projection="review", registered_artifacts=registry)

    population = projected["coverage"]["candidatePopulation"]
    assert population["observed"] == 40
    assert population["omitted"] > 0
    assert any(row["pointer"] == "/candidates" for row in projected["omissions"])
    assert len(semantic_projection_bytes(projected)) <= DISCOVERY_PROJECTION_MAX_BYTES


def test_missing_direct_canonical_rows_are_disclosed_instead_of_invented() -> None:
    payload, registry = _direct_payload()
    payload.pop("substitutions")
    payload.pop("residualPremises")

    projected = project_semantic_result(payload, projection="llm", registered_artifacts=registry)

    assert projected["candidate"]["check"]["substitutions"] is None
    assert projected["candidate"]["check"]["residualPremises"] is None
    assert {(row["pointer"], row["reason"]) for row in projected["omissions"]} >= {
        ("/candidate/check/substitutions", "canonical-field-unavailable"),
        ("/candidate/check/residualPremises", "canonical-field-unavailable"),
    }
