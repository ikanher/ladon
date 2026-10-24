"""Versioned rational-branch plans with mutation-free local Lean preflight."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import time
from pathlib import Path

from ladon.lean_toolchain import (
    LeanToolchainError,
    resolve_toolchain_context,
    sanitize_execution_environment,
    verify_toolchain_identities,
)
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_bridge_supervision import bridge_limits
from ladon.proof_contract_obligation_supervision import _execute_job
from ladon.proof_contract_rational_workspace import rational_workspace_identity
from ladon.proof_contract_refinement import check_rational_refinement
from ladon.rational_lean import encode_rational_goal
from ladon.semantic_lean_execution import (
    DirectLeanPreflightError,
    prepare_direct_lean_execution,
)

_SCHEMA = "ladon-rational-branch-plan-v1"
RATIONAL_BRANCH_PROFILE = {
    "schema": _SCHEMA,
    "arithmetic": "exact rational arithmetic over the bounded rational-witness AST",
    "assignment": "one exact finite rational assignment",
    "booleanEncoding": "decide each predicate equals its Python checker result",
    "divisionByZero": "reject before Lean goal generation",
    "sourceFormulaFidelity": "unverified",
}
_REQUEST_KEYS = {
    "sourceRoot", "workspaceRoot", "branch", "baseGoal", "assignment",
    "deadlineMonotonic", "limits",
}
_DEFAULT_LIMITS = {
    "timeout_seconds": 30,
    "max_output_bytes": 8 * 1024**2,
    "max_rss_bytes": 12 * 1024**3,
}
_NONCLAIMS = [
    "A source citation does not establish source formula fidelity.",
    "These generated obligations concern only the supplied finite assignment over rationals.",
    "A planned branch is not evidence for or against the original claim.",
    "A passing Lean preflight does not establish universal validity over all rational values.",
]
_TOOLCHAIN_CACHE = {}


def plan_rational_branch_probe(request):
    """Regenerate bounded branch obligations and preflight them in pinned Mathlib.

    The returned plan is not a checked receipt. It binds a finite assignment,
    generated closed goals, and the local toolchain identity while retaining the
    source-formula fidelity limitation.
    """
    owned, limits = _own_request(request)
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired before input regeneration.")
    source_root = Path(owned["sourceRoot"]).resolve(strict=True)
    workspace_root = Path(owned["workspaceRoot"]).resolve(strict=True)
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired while resolving inputs.")
    checked, encoded = _derive_request(owned, source_root, workspace_root)
    if encoded is None:
        return checked
    goals = encoded["obligations"]
    preflight = _preflight_workspace(workspace_root, goals, limits,
                                     owned["deadlineMonotonic"])
    if isinstance(preflight, dict):
        return preflight
    context_identity = preflight
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired after Lean preflight.",
                           context_identity)
    current = check_rational_refinement(
        owned["branch"], owned["baseGoal"], owned["assignment"],
        source_root=source_root,
    )
    if current["checkId"] != checked["checkId"]:
        return _incomplete("stale-input", "Branch or cited source changed during Lean preflight.",
                           context_identity)
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired during source revalidation.",
                           context_identity)
    goal_digests = _goal_digests(goals)
    plan = _plan(checked, owned["branch"], encoded, goals, goal_digests, context_identity)
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired before artifact creation.",
                           context_identity)
    plan["artifact"] = _proofir_artifact(plan)
    return plan


def _derive_request(owned, source_root, workspace_root):
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired before branch checking."), None
    try:
        checked = check_rational_refinement(
            owned["branch"], owned["baseGoal"], owned["assignment"],
            source_root=source_root,
        )
    except ValueError as error:
        if str(error) == "division by zero":
            stopped = _stopped("rejected", "undefined-rational-arithmetic", str(error),
                               _workspace_hint(workspace_root))
            return stopped, None
        raise
    if _deadline_expired(owned["deadlineMonotonic"]):
        return _incomplete("timeout", "Shared rational-branch deadline expired before Lean encoding."), None
    encoded = encode_rational_goal(checked["derivedGoal"], checked["assignment"])
    if _deadline_expired(owned["deadlineMonotonic"]):
        stopped = _incomplete("timeout", "Shared rational-branch deadline expired before Lean preflight.")
        return stopped, None
    return checked, encoded


def _deadline_expired(deadline):
    return time.monotonic() >= deadline


def _preflight_workspace(workspace_root, goals, limits, deadline):
    if _deadline_expired(deadline):
        return _incomplete("timeout", "Shared rational-branch deadline expired before toolchain setup.")
    try:
        toolchain = _toolchain_context(workspace_root)
        if _deadline_expired(deadline):
            return _incomplete("timeout", "Shared rational-branch deadline expired during toolchain setup.",
                               toolchain.context_identity)
        workspace = rational_workspace_identity(workspace_root, toolchain, deadline, limits)
        if workspace.get("status") != "resolved":
            if workspace.get("reason") == "unsupported":
                return _unsupported(workspace.get("diagnostic", "Pinned Lean executable is unavailable."),
                                    _workspace_hint(workspace_root))
            return _incomplete(workspace.get("reason", "toolchain-identity"),
                               workspace.get("diagnostic", "Pinned Lean executable identity is incomplete."),
                               _workspace_hint(workspace_root))
        workspace_identity = workspace["workspaceIdentity"]
        execution = prepare_direct_lean_execution(workspace_root, "Mathlib", toolchain)
    except (LeanToolchainError, DirectLeanPreflightError, OSError, ValueError) as error:
        return _unsupported(str(error), _workspace_hint(workspace_root))

    source = _lean_preflight_source(goals)
    if time.monotonic() >= deadline:
        return _incomplete("timeout", "Shared rational-branch deadline expired before Lean preflight.",
                           workspace_identity)
    result = _run_preflight_process(
        workspace_root, execution, source, limits, deadline, toolchain,
    )
    if isinstance(result, dict):
        return result
    if result.returncode != 0:
        return _unsupported(
            "The selected Mathlib workspace could not normalize every generated rational proposition.",
            workspace_identity,
        )
    return workspace_identity


def _run_preflight_process(workspace_root, execution, source, limits, deadline, toolchain):
    remaining = min(
        limits["timeout_seconds"], deadline - time.monotonic(),
    )
    if remaining <= 0:
        return _incomplete("timeout", "Shared rational-branch deadline expired before Lean preflight.",
                           toolchain.context_identity)
    try:
        result = run_bounded_target_process(
            [*execution.command, "--stdin"],
            cwd=workspace_root,
            env=execution.environment,
            timeout_seconds=remaining,
            max_output_bytes=limits["max_output_bytes"],
            max_rss_bytes=limits["max_rss_bytes"],
            input_bytes=source.encode("utf-8"),
        )
        verify_toolchain_identities(toolchain)
    except (OSError, LeanToolchainError, ValueError) as error:
        return _unsupported(str(error), toolchain.context_identity)

    if result.timed_out or result.memory_limited or result.output_limited:
        code = "timeout" if result.timed_out else "memory-limit" if result.memory_limited else "output-limit"
        return _incomplete(code, "Bounded Lean preflight did not complete.", toolchain.context_identity)
    return result


def _goal_digests(goals):
    return [
        "sha256:" + hashlib.sha256(goal["leanProposition"].encode("utf-8")).hexdigest()
        for goal in goals
    ]


def _own_request(request):
    if type(request) is not dict or set(request) != _REQUEST_KEYS:
        raise ValueError(f"rational branch request requires exactly {sorted(_REQUEST_KEYS)}")
    _validate_request_roots(request)
    deadline = _request_deadline(request)
    limits = _request_limits(request)
    return {**request, "deadlineMonotonic": deadline}, limits


def _validate_request_roots(request):
    for key in ("sourceRoot", "workspaceRoot"):
        if (type(request[key]) is not str or not request[key].strip()
                or len(request[key].encode("utf-8")) > 4096):
            raise ValueError(f"{key} must be nonempty bounded text (max 4096 bytes)")


def _request_deadline(request):
    deadline = request["deadlineMonotonic"]
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("rational branch deadline must be finite")
    return float(deadline)


def _request_limits(request):
    supplied = request["limits"]
    if type(supplied) is not dict or not set(supplied) <= set(_DEFAULT_LIMITS):
        raise ValueError("invalid rational branch limits")
    return bridge_limits({**_DEFAULT_LIMITS, **supplied})


def _toolchain_context(root):
    environment_key = tuple(sorted(sanitize_execution_environment().items()))
    key = (root, environment_key)
    context = _TOOLCHAIN_CACHE.get(key)
    if context is not None:
        try:
            verify_toolchain_identities(context)
        except LeanToolchainError:
            _TOOLCHAIN_CACHE.pop(key, None)
        else:
            return context
    context = resolve_toolchain_context(root, selection_mode="ambient")
    _TOOLCHAIN_CACHE[key] = context
    return context


def _lean_preflight_source(goals):
    lines = ["import Mathlib", ""]
    lines.extend(
        f"example : {goal['leanProposition']} := by norm_num" for goal in goals
    )
    return "\n".join(lines) + "\n"


def _plan(checked, branch, encoded, goals, goal_digests, workspace_identity):
    spans = _source_span_identities(branch)
    identity_payload = {
        "schema": _SCHEMA,
        "branchId": checked["branchId"],
        "originalFindingId": checked["originalFindingId"],
        "branchKind": checked["branchKind"],
        "sourceSpanIdentities": spans,
        "baseGoalSha256": checked["baseGoalSha256"],
        "derivedGoalSha256": checked["derivedGoalSha256"],
        "assignment": checked["assignment"],
        "goalDigests": goal_digests,
        "checkerIdentity": encoded["checkerIdentity"],
        "workspaceIdentity": workspace_identity,
    }
    plan_id = _digest(identity_payload)
    return {
        **identity_payload,
        "planId": plan_id,
        "status": "planned",
        "branchRecord": copy.deepcopy(branch),
        "baseGoal": checked["baseGoal"],
        "derivedGoal": checked["derivedGoal"],
        "goals": goals,
        "generatedGoalIdentities": [goal["id"] for goal in goals],
        "sourceFormulaFidelity": "unverified",
        "originalClaimRefuted": False,
        "leanPreflightStatus": "passed",
        "nonclaims": list(_NONCLAIMS),
    }


def _source_span_identities(branch):
    spans = []
    for constraint in branch["constraints"]:
        justification = constraint["justification"]
        if justification["kind"] == "source-cited-refinement":
            span = justification["source"]
            spans.append({
                "constraintId": constraint["id"],
                "path": span["path"],
                "startLine": span["startLine"],
                "endLine": span["endLine"],
                "sha256": (span["sha256"] if span["sha256"].startswith("sha256:")
                           else "sha256:" + span["sha256"]),
                "quoteIdentity": _digest({"quote": span["quote"]}),
            })
    return spans


def _digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


RATIONAL_BRANCH_PROFILE_DIGEST = _digest(RATIONAL_BRANCH_PROFILE)


def _proofir_artifact(plan):
    from ladon.proofir_v3 import make_envelope

    result = {key: copy.deepcopy(value) for key, value in plan.items() if key != "artifact"}
    limitations = [
        {"id": "source-formula-fidelity-unverified",
         "message": "Branch source citations leave source formula fidelity unverified."},
        {"id": "finite-assignment-only",
         "message": "The generated goals concern one finite assignment over rationals."},
        {"id": "universal-validity-unestablished",
         "message": "The plan does not establish universal validity over rationals."},
        {"id": "planning-only-no-checked-support",
         "message": "This plan contains no checked receipt or theorem authority."},
    ]
    return make_envelope(
        artifact_kind="proofir.contract-analysis",
        producer={"name": "ladon-rational-branch-plan", "version": "1"},
        environment_ref=plan["workspaceIdentity"],
        subject_refs=[{"kind": "contract-analysis", "localId": plan["planId"]}],
        coverage={"status": "complete", "observed": len(plan["goals"])},
        payload={
            "analysisId": plan["planId"],
            "profileDigest": RATIONAL_BRANCH_PROFILE_DIGEST,
            "stage": "rational-branch",
            "contractRefs": [],
            "branchId": plan["branchId"],
            "result": result,
            "checkRunRefs": [],
            "residuals": [],
        },
        limitations=limitations,
    ).to_dict()


def _workspace_hint(root):
    return _digest({"workspaceRoot": str(root), "availability": "unavailable"})


def _unsupported(message, workspace_identity):
    return _stopped("unsupported", "mathlib-unavailable", message, workspace_identity)


def _incomplete(code, message, workspace_identity=None):
    return _stopped("incomplete", code, message, workspace_identity)


def _stopped(status, code, message, workspace_identity):
    return {
        "schema": _SCHEMA,
        "status": status,
        "reason": code,
        "diagnostic": message[:500],
        "workspaceIdentity": workspace_identity,
        "goals": [],
        "generatedGoalIdentities": [],
        "checkedSupport": None,
        "receipt": None,
        "sourceFormulaFidelity": "unverified",
        "originalClaimRefuted": False,
        "nonclaims": list(_NONCLAIMS),
    }


__all__ = ["RATIONAL_BRANCH_PROFILE", "RATIONAL_BRANCH_PROFILE_DIGEST",
           "check_rational_branch_probe", "plan_rational_branch_probe"]


def check_rational_branch_probe(request, plan_id, terms, *, cached_result=None):
    """Regenerate a rational branch plan and check each submitted Lean term.

    ``cached_result`` is accepted for API compatibility and size accounting,
    but never substitutes for fresh Lean replay because it is unauthenticated.
    """
    from ladon.proof_contract_rational_check import check_rational_branch_probe as check
    return check(
        request, plan_id, terms, cached_result=cached_result,
        plan=plan_rational_branch_probe, execute_job=_execute_job,
    )
