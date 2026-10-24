"""Validation of rational branch plan semantics and identities."""

from __future__ import annotations

import hashlib
import json

from ladon._proof_contract_rational_common import (
    _digest,
    _goal_digest,
    _require_digest,
    _validate_checker,
    _validate_spans,
)
from ladon.proof_contract_payloads import closed, identifier


def _validate_plan(result, payload, envelope, environment_ref):
    keys = {
        "schema",
        "branchId",
        "originalFindingId",
        "branchRecord",
        "branchKind",
        "sourceSpanIdentities",
        "baseGoalSha256",
        "derivedGoalSha256",
        "assignment",
        "goalDigests",
        "checkerIdentity",
        "workspaceIdentity",
        "planId",
        "status",
        "baseGoal",
        "derivedGoal",
        "goals",
        "generatedGoalIdentities",
        "sourceFormulaFidelity",
        "originalClaimRefuted",
        "leanPreflightStatus",
        "nonclaims",
    }
    closed(result, keys, "rational branch plan result")
    _validate_plan_authority(result, payload, environment_ref)
    _validate_plan_inputs(result)
    _validate_plan_goals(result, envelope)
    _validate_plan_identity(result)
    _validate_plan_nonclaims(result)


def _validate_plan_authority(result, payload, environment_ref):
    _validate_plan_state(result)
    _validate_plan_bindings(result, payload, environment_ref)
    _validate_branch_record(result)


def _validate_branch_record(result):
    branch = result["branchRecord"]
    closed(
        branch,
        {
            "id",
            "schema",
            "branchKind",
            "parentId",
            "originalFinding",
            "discrepancy",
            "witness",
            "constraints",
            "onlyNewConstraints",
            "nonclaims",
        },
        "rational refinement branch record",
    )
    _validate_branch_identity(branch, result)
    _validate_original_finding(branch["originalFinding"], result)
    _validate_original_evidence(branch, branch["originalFinding"])


def _validate_branch_identity(branch, result):
    if (
        branch["schema"] != "ladon-proof-contract-refinement-branch-v1"
        or branch["id"] != result["branchId"]
        or branch["branchKind"] != result["branchKind"]
        or _digest({key: value for key, value in branch.items() if key != "id"})
        != result["branchId"]
    ):
        raise ValueError("rational branch record does not match its branch identity")


def _validate_original_finding(original, result):
    closed(original, {"id", "status", "discrepancy", "witness"}, "rational branch original finding")
    identifier(result["originalFindingId"], "original finding ID")
    if (
        original["id"] != result["originalFindingId"]
        or original["status"] != "abstract-countermodel"
        or not isinstance(original["discrepancy"], dict)
        or not isinstance(original["witness"], dict)
    ):
        raise ValueError("rational branch record is bound to another original finding")


def _validate_original_evidence(branch, original):
    if branch["discrepancy"] != original.get("discrepancy") or branch["witness"] != original.get(
        "witness"
    ):
        raise ValueError("rational branch record changed its original finding evidence")


def _validate_plan_state(result):
    if (
        result["schema"] != "ladon-rational-branch-plan-v1"
        or result["status"] != "planned"
        or result["sourceFormulaFidelity"] != "unverified"
        or result["originalClaimRefuted"] is not False
        or result["leanPreflightStatus"] != "passed"
    ):
        raise ValueError("invalid rational branch plan status or authority")
    for field, label in (
        ("branchId", "branch identity"),
        ("baseGoalSha256", "base goal identity"),
        ("derivedGoalSha256", "derived goal identity"),
        ("workspaceIdentity", "workspace identity"),
    ):
        _require_digest(result[field], label)
    if result["branchKind"] not in {"proposed-repair", "source-cited-refinement"}:
        raise ValueError("unsupported rational branch kind")


def _validate_plan_bindings(result, payload, environment_ref):
    if result["workspaceIdentity"] != environment_ref:
        raise ValueError("rational branch workspace differs from its environment reference")
    if result["planId"] != payload["analysisId"] or result["branchId"] != payload["branchId"]:
        raise ValueError("rational branch plan identity differs from its owning artifact")


def _validate_plan_inputs(result):
    _goal_digest(result["baseGoal"], result["baseGoalSha256"], "base goal")
    _goal_digest(result["derivedGoal"], result["derivedGoalSha256"], "derived goal")
    if type(result["assignment"]) is not dict:
        raise ValueError("rational assignment must be an object")
    _validate_branch_semantics(result)
    _validate_spans(result["sourceSpanIdentities"])
    _validate_checker(result["checkerIdentity"])


def _validate_branch_semantics(result):
    constraints = result["branchRecord"]["constraints"]
    if type(constraints) is not list or not constraints or len(constraints) > 64:
        raise ValueError("rational branch constraints are invalid")
    expected = json.loads(json.dumps(result["baseGoal"]))
    expected_spans = []
    constraint_ids = set()
    for constraint in constraints:
        _append_constraint_semantics(constraint, expected, expected_spans, constraint_ids)
    if expected != result["derivedGoal"] or expected_spans != result["sourceSpanIdentities"]:
        raise ValueError("derived rational goal does not match its exact branch constraints")
    _validate_branch_kind(constraints, result["branchKind"])


def _append_constraint_semantics(constraint, expected, expected_spans, constraint_ids):
    closed(constraint, {"id", "expression", "justification"}, "rational branch constraint")
    identifier(constraint["id"], "constraint ID")
    if constraint["id"] in constraint_ids:
        raise ValueError("rational branch constraint IDs must be unique")
    constraint_ids.add(constraint["id"])
    expected["premises"].append(constraint["expression"])
    justification = constraint["justification"]
    if not isinstance(justification, dict):
        raise TypeError("rational branch justification must be an object")
    kind = justification.get("kind")
    if kind == "source-cited-refinement":
        expected_spans.append(_source_constraint_span(constraint, justification))
    elif kind == "proposed-repair":
        closed(justification, {"kind", "rationale"}, "proposed repair justification")
    else:
        raise ValueError("unsupported rational branch constraint justification")


def _source_constraint_span(constraint, justification):
    closed(justification, {"kind", "source", "nonclaim"}, "source-cited refinement justification")
    span = justification["source"]
    closed(span, {"path", "startLine", "endLine", "quote", "sha256"}, "rational branch source span")
    source_digest = span["sha256"]
    if not source_digest.startswith("sha256:"):
        source_digest = "sha256:" + source_digest
    return {
        "constraintId": constraint["id"],
        "path": span["path"],
        "startLine": span["startLine"],
        "endLine": span["endLine"],
        "sha256": source_digest,
        "quoteIdentity": _digest({"quote": span["quote"]}),
    }


def _validate_branch_kind(constraints, branch_kind):
    kinds = {row["justification"]["kind"] for row in constraints}
    expected_kind = (
        "proposed-repair"
        if kinds == {"proposed-repair"}
        else "source-cited-refinement"
        if kinds == {"source-cited-refinement"}
        else "mixed-refinement-and-repair"
    )
    if branch_kind != expected_kind:
        raise ValueError("rational branch kind does not match its constraints")


def _validate_plan_goals(result, envelope):
    goals = result["goals"]
    identities = result["generatedGoalIdentities"]
    digests = result["goalDigests"]
    if (
        type(goals) is not list
        or not goals
        or len(goals) > 65
        or type(identities) is not list
        or type(digests) is not list
        or len(identities) != len(goals)
        or len(digests) != len(goals)
    ):
        raise ValueError("rational branch goal rows are invalid")
    expected_ids = [
        _validate_goal_row(goal, index, len(goals), digests[index])
        for index, goal in enumerate(goals)
    ]
    if identities != expected_ids:
        raise ValueError("rational branch generated goal identities changed")
    _validate_regenerated_semantics(result)
    _validate_coverage(envelope, len(goals))


def _validate_regenerated_semantics(result):
    from ladon.rational_lean import encode_rational_goal

    encoded = encode_rational_goal(result["derivedGoal"], result["assignment"])
    if (
        result["checkerIdentity"] != encoded["checkerIdentity"]
        or result["goals"] != encoded["obligations"]
    ):
        raise ValueError("rational branch goals differ from regenerated checker semantics")


def _validate_goal_row(goal, index, count, expected_digest):
    closed(
        goal, {"id", "goalId", "kind", "expectedHolds", "leanProposition"}, "rational branch goal"
    )
    expected_id = f"premise-{index:04d}" if index < count - 1 else "conclusion"
    if (
        goal["goalId"] != goal["id"]
        or goal["id"] != expected_id
        or goal["kind"] not in {"premise", "conclusion"}
        or type(goal["expectedHolds"]) is not bool
        or type(goal["leanProposition"]) is not str
    ):
        raise ValueError("rational branch generated goal is malformed")
    digest = "sha256:" + hashlib.sha256(goal["leanProposition"].encode()).hexdigest()
    if expected_digest != digest:
        raise ValueError("rational branch generated goal digest changed")
    return goal["goalId"]


def _validate_plan_identity(result):
    identity_payload = {
        key: result[key]
        for key in (
            "schema",
            "branchId",
            "originalFindingId",
            "branchKind",
            "sourceSpanIdentities",
            "baseGoalSha256",
            "derivedGoalSha256",
            "assignment",
            "goalDigests",
            "checkerIdentity",
            "workspaceIdentity",
        )
    }
    if _digest(identity_payload) != result["planId"]:
        raise ValueError("rational branch plan digest does not match its semantic inputs")


def _validate_plan_nonclaims(result):
    if not isinstance(result["nonclaims"], list) or not result["nonclaims"]:
        raise ValueError("rational branch plan nonclaims are missing")
    if "universal" not in " ".join(result["nonclaims"]).lower():
        raise ValueError("rational branch plan must disclaim universal claims")


def _validate_coverage(envelope, goal_count):
    if any(
        envelope["coverage"][key] != goal_count
        for key in (
            "expected",
            "discovered",
            "decoded",
            "valid",
            "projected",
            "queryMatched",
        )
    ):
        raise ValueError("rational branch coverage does not match generated goals")
