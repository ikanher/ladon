from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from support.semantic_evidence import digest, semantic_evidence

from ladon import proof_search_cli
from ladon.proof_search_cli import proof_search_main
from ladon.semantic_projection_core import (
    SemanticProjectionError,
    identity,
    identity_text,
    sanitize,
)
from ladon.semantic_projection_fit import finalize_projection
from ladon.semantic_result_projection import (
    DIRECT_PROJECTION_MAX_BYTES,
    DISCOVERY_PROJECTION_MAX_BYTES,
    project_semantic_result,
    semantic_projection_bytes,
)


def _accepted_check() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    artifacts, registry, receipt = semantic_evidence(
        "check", candidate="Main.proof"
    )
    environment_ref = str(artifacts[0]["environmentRef"])
    check_artifact_id = str(artifacts[1]["artifactId"])
    check_run_id = str(artifacts[1]["payload"]["checkRunId"])
    check = {
        "status": "accepted",
        "applicationTerm": "Main.proof",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "environmentRef": environment_ref,
        "checkRunId": check_run_id,
        "checkRunRef": {
            "artifactRef": check_artifact_id,
            "kind": "check-run",
            "localId": check_run_id,
        },
        "evidenceReceipt": receipt,
        "artifacts": artifacts,
    }
    return check, registry


def _discovery(check: dict[str, Any], shortlist: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "ladon-verified-discovery-result-v1",
        "operation": "discover",
        "status": "available",
        "request": {
            "module": "Main",
            "goal": "True",
            "localContext": [],
            "scope": "repository",
            "freshness": "stored",
            "scratchMode": "none",
            "maxCandidates": 1,
        },
        "candidates": [
            {"name": "Main.proof", "shortlist": shortlist, "check": check}
        ],
        "coverage": {
            "shortlisted": 1,
            "submitted": 1,
            "completed": 1,
            "accepted": 1,
            "truncated": False,
        },
        "shortlist": {"source": "type-text-shortlist", "omissions": []},
        "ranking": {"policy": "verified-status-priority-v1", "contributions": []},
        "nonclaims": [],
    }


def test_oversized_source_labels_are_bounded_and_fingerprinted() -> None:
    check, registry = _accepted_check()
    module = "Module." + "界" * 50_000
    path = "nested/" + "δ" * 50_000 + ".lean"
    payload = _discovery(
        check,
        {"module": module, "path": path, "line": 123},
    )

    projected = project_semantic_result(
        payload, projection="llm", registered_artifacts=registry
    )

    source = projected["candidates"][0]["source"]
    assert len(source["module"].encode()) <= 512
    assert len(source["path"].encode()) <= 1024
    assert source["line"] == 123
    assert source["moduleFingerprint"] == identity_text(module)
    assert source["pathFingerprint"] == identity_text(path)
    assert len(semantic_projection_bytes(projected)) <= DISCOVERY_PROJECTION_MAX_BYTES
    assert {
        ("/candidates/0/source/module", "projection-text-byte-limit"),
        ("/candidates/0/source/path", "projection-text-byte-limit"),
    } <= {(row["pointer"], row["reason"]) for row in projected["omissions"]}


def test_omission_ledger_is_bounded_and_accounts_for_hidden_records() -> None:
    check, registry = _accepted_check()
    check["resourceAccounting"] = {
        f"measurement-{field}": "value" * 500 for field in range(30)
    }
    payload = _discovery(
        check,
        {"module": "M" * 10_000, "path": "P" * 10_000, "line": 1},
    )

    projected = project_semantic_result(
        payload, projection="review", registered_artifacts=registry
    )

    _assert_bounded_omission_population(projected)
    assert len(semantic_projection_bytes(projected)) <= DISCOVERY_PROJECTION_MAX_BYTES


def _assert_bounded_omission_population(projected: dict[str, Any]) -> None:
    population = projected["coverage"]["omissionPopulation"]
    assert len(projected["omissions"]) <= 24
    assert population["observedRecords"] > population["projectedRecords"]
    assert population["omittedRecords"] > 0
    assert population["generatedRecords"] == 1
    assert population["transportRecords"] == len(projected["omissions"])
    assert population["totalClaims"] >= population["observedRecords"]
    assert (
        population["projectedRecords"] + population["generatedRecords"]
        == population["transportRecords"]
    )
    assert any(
        row["pointer"] == "/omissions"
        and row["reason"] == "projection-collection-limit"
        for row in projected["omissions"]
    )


def test_last_resort_projection_preserves_authority_bearing_skeleton() -> None:
    check, registry = _accepted_check()
    check["resourceAccounting"] = {
        f"measurement-{index}": "large-value" * 500 for index in range(24)
    }
    canonical = {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        "status": "accepted",
        "limitations": ["Accepted result requires explicit audit expansion."],
        **check,
    }
    canonical_identity = identity(canonical)

    projected = project_semantic_result(
        canonical, projection="review", registered_artifacts=registry
    )

    _assert_minimal_projection_context(projected, canonical_identity)
    _assert_minimal_candidate(projected, canonical)
    _assert_minimal_coverage(projected)
    _assert_minimal_audit_expansion(projected)
    assert len(semantic_projection_bytes(projected)) <= DIRECT_PROJECTION_MAX_BYTES


def _assert_minimal_projection_context(
    projected: dict[str, Any], canonical_identity: str
) -> None:
    projected_check = projected["candidate"]["check"]
    assert projected["status"] == "accepted"
    assert projected["projection"]["canonicalPayloadIdentity"] == canonical_identity
    assert projected["request"]["moduleFingerprint"] == identity_text("Main")
    assert projected["request"]["goalFingerprint"] == identity_text("True")
    assert projected_check["status"] == "accepted"
    assert projected_check["authority"]["authorityBasis"] == "elaborator-check"


def _assert_minimal_candidate(
    projected: dict[str, Any], canonical: dict[str, Any]
) -> None:
    projected_check = projected["candidate"]["check"]
    assert projected_check["environmentRef"] == {
        "environmentRef": canonical["environmentRef"],
        "artifactRef": canonical["artifacts"][0]["artifactId"],
    }
    assert projected_check["checkRunRef"] == canonical["checkRunRef"]


def _assert_minimal_coverage(projected: dict[str, Any]) -> None:
    assert projected["coverage"]["candidatePopulation"]["statusCounts"] == {
        "accepted": 1
    }
    assert projected["coverage"]["canonical"] is None
    assert projected["coverage"]["operationalFailure"] is False
    omission_population = projected["coverage"]["omissionPopulation"]
    assert omission_population["projectedRecords"] == 0
    assert omission_population["generatedRecords"] == 1
    assert omission_population["transportRecords"] == 1
    assert omission_population["totalClaims"] > 0
    assert projected["omissions"] == [
        {
            "pointer": "/projection",
            "reason": "projection-byte-limit",
            "omitted": 1,
        }
    ]


def _assert_minimal_audit_expansion(projected: dict[str, Any]) -> None:
    assert projected["requiresAuditExpansion"] is True
    assert projected["limitationCount"] == 2
    assert projected["limitationsFingerprint"].startswith("sha256:")


@pytest.mark.parametrize("line", [True, False, 0, -1, 1.0, "1"])
def test_source_line_requires_positive_integer_or_absent(line: Any) -> None:
    check, registry = _accepted_check()
    payload = _discovery(
        check,
        {"module": "Main", "path": "Main.lean", "line": line},
    )

    with pytest.raises(SemanticProjectionError, match="positive integer or absent"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts=registry
        )


@pytest.mark.parametrize("line", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_source_line_is_rejected_before_projection(line: float) -> None:
    check, registry = _accepted_check()
    payload = _discovery(
        check,
        {"module": "Main", "path": "Main.lean", "line": line},
    )

    with pytest.raises(SemanticProjectionError, match="positive integer or absent"):
        project_semantic_result(
            payload, projection="llm", registered_artifacts=registry
        )


def test_nested_non_finite_values_are_rejected_before_discovery_projection() -> None:
    check, registry = _accepted_check()
    payload = _discovery(
        check,
        {"module": "Main", "path": "Main.lean", "line": 1},
    )
    payload["coverage"]["quality"] = float("inf")
    payload["ranking"]["contributions"] = [
        {"candidate": "Main.proof", "score": float("nan")}
    ]

    with pytest.raises(SemanticProjectionError, match="non-finite number"):
        project_semantic_result(
            payload, projection="review", registered_artifacts=registry
        )


def test_non_finite_diagnostic_and_resource_values_are_rejected() -> None:
    payload = {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        "status": "failed-checker",
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "failureStage": "checker-process",
        "diagnostic": {"code": "process-failed", "score": float("nan")},
        "resourceAccounting": {"ratio": float("-inf")},
        "artifacts": [],
    }

    with pytest.raises(SemanticProjectionError, match="non-finite number"):
        project_semantic_result(payload, projection="review", registered_artifacts={})


def test_last_resort_bounds_and_fingerprints_untrusted_metadata() -> None:
    status = "status-" + "s" * 100_000
    canonical_schema = "schema-" + "c" * 100_000
    producer_identity = "producer-" + "p" * 100_000
    projected = {
        "schema": "ladon-semantic-candidate-projection-v1",
        "operation": "check-candidate",
        "status": status,
        "projection": {
            "name": "review",
            "canonicalSchema": canonical_schema,
            "canonicalPayloadIdentity": digest("canonical"),
            "producerResultIdentity": producer_identity,
            "limits": {"maxBytes": DIRECT_PROJECTION_MAX_BYTES},
        },
        "request": {
            "moduleFingerprint": digest("module"),
            "goalFingerprint": digest("goal"),
        },
        "candidate": {
            "nameFingerprint": digest("candidate"),
            "source": None,
            "check": {
                "status": "accepted",
                "authority": {"authorityBasis": "elaborator-check"},
                "environmentRef": {"environmentRef": digest("environment")},
                "checkRunRef": {
                    "artifactRef": digest("check"),
                    "kind": "check-run",
                    "localId": "check:" + "1" * 64,
                },
            },
        },
        "coverage": {
            "candidatePopulation": {"observed": 1, "projected": 1, "omitted": 0},
            "operationalFailure": False,
        },
        "omissions": [],
    }

    bounded = finalize_projection(projected, DIRECT_PROJECTION_MAX_BYTES)

    assert bounded["statusFingerprint"] == identity_text(status)
    assert len(bounded["status"].encode()) <= 128
    header = bounded["projection"]
    assert header["canonicalSchemaFingerprint"] == identity_text(canonical_schema)
    assert header["producerResultIdentityFingerprint"] == identity_text(
        producer_identity
    )
    assert len(header["canonicalSchema"].encode()) <= 128
    assert len(header["producerResultIdentity"].encode()) <= 128
    assert len(semantic_projection_bytes(bounded)) <= DIRECT_PROJECTION_MAX_BYTES


def test_internal_optional_non_finite_value_is_sanitized_defensively() -> None:
    omissions: list[dict[str, Any]] = []

    value = sanitize(float("nan"), "llm", omissions, "/optional/score")

    assert value is None
    assert omissions == [
        {
            "pointer": "/optional/score",
            "reason": "projection-non-finite-number",
            "omitted": 1,
        }
    ]
    assert json.loads(semantic_projection_bytes({"score": value})) == {"score": None}


def test_audit_cli_json_bytes_are_exact_and_registry_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    canonical = {
        "schema": "ladon-semantic-candidate-check-result-v1",
        "operation": "check-candidate",
        "status": "accepted",
        "applicationTerm": "Main.δοκιμή",
        "artifacts": [{"payload": {"exact": ["α", {"β": True}]}}],
    }
    registry_path = tmp_path / "semantic.sqlite"
    monkeypatch.setattr(
        proof_search_cli,
        "_dispatch_check",
        lambda _args, _repo_root: copy.deepcopy(canonical),
    )

    status = proof_search_main(
        [
            "check",
            "candidate",
            "--repo-root",
            str(tmp_path),
            "--module",
            "Main",
            "--goal",
            "True",
            "--candidate",
            "Main.proof",
            "--projection",
            "audit",
            "--evidence-store",
            str(registry_path),
            "--format",
            "json",
        ]
    )

    expected = (
        json.dumps(canonical, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    captured = capsys.readouterr()
    assert status == 0
    assert captured.out.encode() == expected
    assert captured.err == ""
    assert not registry_path.exists()
