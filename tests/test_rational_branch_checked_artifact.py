"""Mutation checks for the native checked rational-branch ProofIR artifact."""
from __future__ import annotations

import copy

import pytest
from test_rational_branch_receipts_v3 import (
    _plan,
    _replay_hook,
    _terms,
    request,
)

import ladon.proof_contract_rational_probes as route


def _checked_batch(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch)
    result = route.check_rational_branch_probe(req, plan["planId"], _terms(plan))
    assert result["status"] == "checked-rational-branch", result
    return [plan["artifact"], *result["artifacts"], result["checkedArtifact"]]


def _rebind(artifact):
    from ladon.proofir_v3 import detached_content_id

    artifact["artifactId"] = detached_content_id(artifact)


def test_native_checked_artifact_accepts_exact_closed_batch(monkeypatch):
    from ladon.proofir_v3 import validate_envelope_batch

    checked = _checked_batch(monkeypatch)
    assert validate_envelope_batch(checked)


def test_native_plan_rejects_mutated_original_finding_under_rebound_envelope(monkeypatch):
    from ladon.proofir_v3 import validate_envelope_batch

    checked = copy.deepcopy(_checked_batch(monkeypatch))
    plan = checked[0]
    plan["payload"]["result"]["branchRecord"]["originalFinding"]["id"] = "other-finding"
    _rebind(plan)

    with pytest.raises(ValueError, match="branch record"):
        validate_envelope_batch(checked)


def test_native_plan_rejects_branch_constraint_that_no_longer_builds_goal(monkeypatch):
    from ladon._proof_contract_rational_native import _digest
    from ladon.proofir_v3 import validate_envelope

    plan = copy.deepcopy(_checked_batch(monkeypatch)[0])
    result = plan["payload"]["result"]
    branch = result["branchRecord"]
    changed = {"op": "gt", "left": {"var": "x"}, "right": {"rat": "0"}}
    branch["constraints"][0]["expression"] = changed
    branch["onlyNewConstraints"][0]["expression"] = copy.deepcopy(changed)
    branch["id"] = _digest({key: value for key, value in branch.items() if key != "id"})
    result["branchId"] = branch["id"]
    plan["payload"]["branchId"] = branch["id"]

    identity = {key: result[key] for key in (
        "schema", "branchId", "originalFindingId", "branchKind",
        "sourceSpanIdentities", "baseGoalSha256", "derivedGoalSha256",
        "assignment", "goalDigests", "checkerIdentity", "workspaceIdentity",
    )}
    result["planId"] = _digest(identity)
    plan["payload"]["analysisId"] = result["planId"]
    plan["subjectRefs"][0]["localId"] = result["planId"]
    _rebind(plan)

    with pytest.raises(ValueError, match="derived rational goal"):
        validate_envelope(plan)


@pytest.mark.parametrize("mutation", ["trust-policy", "trust-coverage", "axiom"])
def test_native_check_run_rejects_rebound_untrusted_receipt_fields(monkeypatch, mutation):
    from ladon.proofir_v3 import validate_envelope_batch

    checked = copy.deepcopy(_checked_batch(monkeypatch))
    run = checked[1]
    old_id = run["artifactId"]
    completion = run["extensions"]["ladon.rational-branch-receipt/v1"]["completion"]
    if mutation == "trust-policy":
        completion["trustPolicy"] = "different-policy"
    elif mutation == "trust-coverage":
        completion["trustCoverage"] = "partial"
    else:
        completion["observedAxioms"] = ["sorryAx"]
    _rebind(run)

    analysis = checked[-1]
    refs = analysis["payload"]["checkRunRefs"]
    for ref in refs:
        if ref["artifactRef"] == old_id:
            ref["artifactRef"] = run["artifactId"]
    analysis["payload"]["result"]["checkRunRefs"] = copy.deepcopy(refs)
    _rebind(analysis)

    with pytest.raises(ValueError):
        validate_envelope_batch(checked)


@pytest.mark.parametrize("mutation", [
    "branch", "source", "goal", "assignment", "checker", "workspace",
    "base-goal", "inventory", "missing-check-run",
])
def test_native_checked_artifact_rejects_rebound_semantic_mutations(monkeypatch, mutation):
    from ladon.proofir_v3 import validate_envelope_batch

    checked = copy.deepcopy(_checked_batch(monkeypatch))
    analysis = checked[-1]
    payload = analysis["payload"]
    receipt = payload["result"]
    if mutation == "branch":
        digest = "sha256:" + "a" * 64
        payload["branchId"] = digest
        receipt["branchId"] = digest
    elif mutation == "source":
        receipt["sourceSpanIdentities"] = [{
            "constraintId": "mutated-source",
            "path": "paper.txt",
            "startLine": 1,
            "endLine": 1,
            "sha256": "sha256:" + "b" * 64,
            "quoteIdentity": "sha256:" + "c" * 64,
        }]
    elif mutation == "goal":
        receipt["goalDigests"][0] = "sha256:" + "d" * 64
    elif mutation == "base-goal":
        receipt["baseGoalSha256"] = "sha256:" + "0" * 64
    elif mutation == "assignment":
        payload["result"]["assignment"]["x"] = "2"
    elif mutation == "checker":
        receipt["proofCheckerIdentity"]["helperDigest"] = "sha256:" + "e" * 64
    elif mutation == "workspace":
        receipt["workspaceIdentity"] = "sha256:" + "f" * 64
    elif mutation == "inventory":
        digest = "sha256:" + "1" * 64
        receipt["compiledInventoryDigest"] = digest
        receipt["compiledInventoryDigestsByGoal"] = {
            goal_id: digest for goal_id in receipt["compiledInventoryDigestsByGoal"]
        }
    else:
        payload["checkRunRefs"].pop()
        payload["result"]["checkRunRefs"] = copy.deepcopy(payload["checkRunRefs"])
    _rebind(analysis)

    with pytest.raises(ValueError):
        validate_envelope_batch(checked)
