"""Closed ProofIR payload validation for rational-branch planning artifacts."""

from __future__ import annotations

from ladon._proof_contract_rational_common import _digest, _require_digest
from ladon._proof_contract_rational_plan import _validate_plan
from ladon._proof_contract_rational_receipts import _validate_check_run, _validate_checked_receipt
from ladon.proof_contract_payloads import closed, identifier, residuals
from ladon.proof_contract_rational_probes import RATIONAL_BRANCH_PROFILE_DIGEST

__all__ = [
    "recompute_rational_branch_check",
    "validate_rational_branch_check_payload",
    "validate_rational_branch_payload",
]


def validate_rational_branch_payload(payload, value, subjects, environment_ref):
    closed(
        payload,
        {
            "analysisId",
            "profileDigest",
            "stage",
            "contractRefs",
            "branchId",
            "result",
            "checkRunRefs",
            "residuals",
        },
        "rational branch analysis payload",
    )
    identifier(payload["analysisId"], "analysis ID")
    if ("contract-analysis", payload["analysisId"]) not in subjects:
        raise ValueError("rational branch analysis must own its exact typed subject")
    if (
        payload["stage"] != "rational-branch"
        or payload["profileDigest"] != RATIONAL_BRANCH_PROFILE_DIGEST
    ):
        raise ValueError("unsupported rational branch profile or stage")
    if payload["contractRefs"] != [] or payload["checkRunRefs"] != []:
        raise ValueError("rational branch plans cannot contain native contract or check references")
    residuals(payload["residuals"])
    result = payload["result"]
    _validate_plan(result, payload, value, environment_ref)
    limitation_ids = {row["id"] for row in value["limitations"]}
    required = {
        "source-formula-fidelity-unverified",
        "finite-assignment-only",
        "planning-only-no-checked-support",
    }
    if not required <= limitation_ids:
        raise ValueError("rational branch plan must retain its fidelity and scope limitations")


def validate_rational_branch_check_payload(payload, value, subjects, environment_ref):
    closed(
        payload,
        {
            "analysisId",
            "profileDigest",
            "stage",
            "planRef",
            "branchId",
            "result",
            "checkRunRefs",
            "residuals",
        },
        "rational branch checked analysis payload",
    )
    identifier(payload["analysisId"], "analysis ID")
    if ("contract-analysis", payload["analysisId"]) not in subjects:
        raise ValueError("rational branch check must own its exact typed subject")
    if (
        payload["stage"] != "rational-branch-check"
        or payload["profileDigest"] != RATIONAL_BRANCH_PROFILE_DIGEST
    ):
        raise ValueError("unsupported rational branch checked profile or stage")
    plan_ref = payload["planRef"]
    if (
        not isinstance(plan_ref, dict)
        or plan_ref.get("kind") != "contract-analysis"
        or "artifactRef" not in plan_ref
    ):
        raise ValueError("rational branch check requires an external plan reference")
    _require_digest(payload["branchId"], "branch identity")
    _refs_check_runs(payload["checkRunRefs"], value, subjects, environment_ref)
    residuals(payload["residuals"])
    result = payload["result"]
    _validate_checked_receipt(result, payload, environment_ref)
    limitation_ids = {row["id"] for row in value["limitations"]}
    required = {
        "source-formula-fidelity-unverified",
        "finite-assignment-only",
        "original-claim-not-refuted",
    }
    if not required <= limitation_ids:
        raise ValueError("rational branch checked result omits its scope limitations")


def _refs_check_runs(refs, value, subjects, environment_ref):
    from ladon.proof_contract_payloads import rows
    from ladon.proofir_v3 import _require_ref

    rows(refs, "rational branch check-run references", minimum=1)
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict) or ref.get("kind") != "check-run" or "artifactRef" not in ref:
            raise ValueError("rational branch check-run references must be external check-runs")
        _require_ref(
            ref, f"/payload/checkRunRefs/{index}", subjects, environment_ref, value, "check-run"
        )


def recompute_rational_branch_check(artifacts, payload):
    plan_artifact = _load_plan_artifact(artifacts, payload["planRef"])
    plan_payload = plan_artifact["payload"]
    plan = plan_payload["result"]
    receipt = payload["result"]
    _validate_plan_receipt_binding(payload, plan_payload, plan, receipt)
    goals = {row["goalId"]: row for row in plan["goals"]}
    _validate_receipt_plan_coverage(receipt, plan, payload, goals)
    checked_rows = [
        _validate_check_run(artifacts, plan_artifact, plan, receipt, ref)
        for ref in payload["checkRunRefs"]
    ]
    _validate_checked_goals(checked_rows, goals)
    _validate_shared_proof_checker(checked_rows, receipt)


def _load_plan_artifact(artifacts, plan_ref):
    plan_artifact = artifacts.get(plan_ref.get("artifactRef"))
    if (
        not isinstance(plan_artifact, dict)
        or plan_artifact.get("artifactKind") != "proofir.contract-analysis"
        or plan_artifact.get("payload", {}).get("stage") != "rational-branch"
    ):
        raise ValueError("rational branch check plan reference is not an exact native plan")
    return plan_artifact


def _validate_plan_receipt_binding(payload, plan_payload, plan, receipt):
    plan_ref = payload["planRef"]
    if (
        plan_ref.get("localId") != plan_payload["analysisId"]
        or payload["branchId"] != plan["branchId"]
    ):
        raise ValueError("rational branch checked result does not match its exact plan")
    for key in (
        "planId",
        "originalFindingId",
        "branchKind",
        "sourceSpanIdentities",
        "baseGoalSha256",
        "derivedGoalSha256",
        "assignment",
        "goalDigests",
        "checkerIdentity",
    ):
        if receipt[key] != plan[key]:
            raise ValueError("rational branch checked result does not match its exact plan")


def _validate_receipt_plan_coverage(receipt, plan, payload, goals):
    if len(receipt["goalDigests"]) != len(plan["generatedGoalIdentities"]) or set(
        receipt["termDigests"]
    ) != set(plan["generatedGoalIdentities"]):
        raise ValueError("rational branch receipt goal identities differ from its plan")
    if len(payload["checkRunRefs"]) != len(goals):
        raise ValueError("rational branch checked result requires one check-run per generated goal")


def _validate_checked_goals(checked_rows, goals):
    seen = {row[0] for row in checked_rows}
    if len(seen) != len(checked_rows) or seen != set(goals):
        raise ValueError("rational branch check-run set does not cover each generated goal once")


def _validate_shared_proof_checker(checked_rows, receipt):
    checkers = {_digest(row[1]) for row in checked_rows}
    if len(checkers) != 1 or receipt["proofCheckerIdentity"] != checked_rows[0][1]:
        raise ValueError("rational branch proof checker differs from its per-goal receipts")
