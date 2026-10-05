"""Synthetic projection contracts use the real field residual, not a proof fixture."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from support.semantic_evidence import semantic_evidence

from ladon.proof_search_cli import _render_text
from ladon.semantic_result_delivery import deliver_semantic_result

BOUNDARY_GAP = "0 ≤ Mf.DP.fixedEpochCenterGap point h boundary"
OTHER_RESIDUALS = tuple(
    {"typeDisplay": f"AdditionalPremise {index}", "typeStructural": f"extra-{index}"}
    for index in range(5)
)


def _check(label: str, candidate: str, status: str, residuals: list[dict[str, str]]) -> dict[str, Any]:
    artifacts, _resolver, receipt = semantic_evidence(
        label,
        candidate=candidate,
        status=status,
        residual_premises=residuals,
        application_term=candidate + " ?hBoundaryGap" if residuals else candidate,
    )
    environment, check_artifact = artifacts
    check_ref = check_artifact["payload"]["checkRunId"]
    return {
        "status": status,
        "applicationTerm": candidate + " ?hBoundaryGap" if residuals else candidate,
        "substitutions": [],
        "residualPremises": residuals,
        "dischargedHypotheses": [],
        "environmentRef": environment["environmentRef"],
        "checkRunId": check_ref,
        "checkRunRef": {
            "artifactRef": check_artifact["artifactId"],
            "kind": "check-run",
            "localId": check_ref,
        },
        "evidenceReceipt": receipt,
        "artifacts": artifacts,
        "diagnostic": None,
        "failureStage": "candidate-not-found" if status == "rejected" else None,
        "resourceAccounting": {},
        "limitations": [],
    }


def _canonical(operation: str) -> dict[str, Any]:
    boundary_gap = {"typeDisplay": BOUNDARY_GAP, "typeStructural": "synthetic-boundary-gap-expression"}
    partial = _check(
        f"{operation}-partial",
        "Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg",
        "applicable-with-residuals",
        [boundary_gap, *OTHER_RESIDUALS],
    )
    accepted = _check(f"{operation}-complete", "Main.closed", "accepted", [])
    rejected = _check(f"{operation}-rejected", "Main.wrong", "rejected", [])
    if operation == "check-candidate":
        return {
            "schema": "ladon-semantic-candidate-check-result-v1",
            "operation": operation,
            "status": partial["status"],
            "candidate": "Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg",
            **partial,
        }
    return {
        "schema": "ladon-verified-discovery-result-v1",
        "operation": operation,
        "status": "available",
        "request": {"module": "Main", "goal": "True", "maxCandidates": 3},
        "candidates": [
            {"name": "Main.closed", "check": accepted, "shortlist": {}},
            {
                "name": "Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg",
                "check": partial,
                "shortlist": {},
            },
            {"name": "Main.wrong", "check": rejected, "shortlist": {}},
        ],
        "coverage": {"shortlisted": 3, "truncated": False},
        "shortlist": {"source": "fixture"},
        "artifacts": [],
    }


def _delivered(operation: str, tmp_path: Path) -> dict[str, Any]:
    return deliver_semantic_result(
        _canonical(operation),
        projection="llm",
        repo_root=tmp_path,
        registry_path=tmp_path / f"{operation}.sqlite",
    )


@pytest.mark.parametrize("operation", ["check-candidate", "discover"])
@pytest.mark.parametrize("projection", ["llm", "review"])
def test_text_shows_projected_propositions_before_their_own_receipt(
    tmp_path: Path, operation: str, projection: str,
) -> None:
    projected = deliver_semantic_result(
        _canonical(operation), projection=projection, repo_root=tmp_path,
        registry_path=tmp_path / "evidence.sqlite",
    )
    before = copy.deepcopy(projected)
    text = _render_text(projected)
    assert projected == before
    candidates = projected.get("candidates", [projected.get("candidate")])
    for candidate in candidates:
        _assert_proposition_order(text, candidate)
        _assert_receipt_references(text, candidate["check"])
    assert BOUNDARY_GAP in text
    assert "?hBoundaryGap" in text
    assert "goal is false" not in text
    assert "proof complete" not in text


def _assert_proposition_order(text: str, candidate: dict[str, Any]) -> None:
    check = candidate["check"]
    start = text.index(f"- {candidate['name']} [{check['status']}]")
    receipt = text.index("evidenceReceipt:", start)
    for residual in check["residualPremises"]:
        marker = "remaining goal: " + residual["typeDisplay"]
        assert start < text.index(marker, start) < receipt


def _assert_receipt_references(text: str, check: dict[str, Any]) -> None:
    for key in ("checkRunRef", "environmentRef"):
        assert json.dumps(check[key], sort_keys=True, ensure_ascii=False) in text
    assert "analysisCompleteness=" + check["authority"]["analysisCompleteness"] in text


@pytest.mark.parametrize("operation", ["check-candidate", "discover"])
def test_text_discloses_projection_omissions_and_accounting(tmp_path: Path, operation: str) -> None:
    projected = _delivered(operation, tmp_path)
    before = copy.deepcopy(projected)
    text = _render_text(projected)
    residual_omissions = [
        row for row in projected["omissions"]
        if row["pointer"].endswith("/residualPremises")
        and row["reason"] == "projection-collection-limit"
    ]
    assert residual_omissions
    for row in projected["omissions"]:
        assert "omission: " + json.dumps(row, sort_keys=True, ensure_ascii=False) in text
    assert "omissionPopulation" in text
    assert projected == before
