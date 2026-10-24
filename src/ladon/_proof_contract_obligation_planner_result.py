"""Bounded planner result assembly."""

from __future__ import annotations

import hashlib

from ladon._contract_propagation_budget import OutputBudget, encoded_size, fingerprint
from ladon.proof_contracts import compare_contracts

from ._proof_contract_obligation_planner_validation import _canonical, _refkey


def _assemble_result(
    request,
    raw,
    forward,
    route_rows,
    all_requirements,
    residuals,
    caps,
    steps,
    ledger,
    planner_pending,
    budget,
):
    work = _work_budget(ledger)
    pending = _pending_rows(request, forward, planner_pending, steps)
    coverage = _coverage(forward, pending, work, steps, ledger)
    endpoint = _endpoint(forward, request, request.desired_contract)
    if budget.exhausted or not _reserve_pending(pending, budget):
        coverage["pendingBranches"] = [_pending_summary(pending, request)]
        coverage["unvisitedApplications"] = coverage["pendingBranches"]
    result = _result_header(request, forward, coverage, endpoint)
    retained_routes, retained_requirements, retained_comparisons = [], [], []
    for row in route_rows:
        retained_routes.append(row)
        retained_requirements.extend(row["backwardRequirements"])
        retained_comparisons.extend(row["comparisons"])
    result["routeComparisons"] = retained_routes
    result["comparisons"] = retained_comparisons
    result["backwardRequirements"] = retained_requirements
    for item in residuals:
        if not budget.reserve(item, overhead=8):
            _append_pending_summary(coverage, request)
            break
        result["residuals"].append(item)
    for item in forward.get("prunings", []):
        if not budget.reserve(item, overhead=8):
            _append_pending_summary(coverage, request)
            break
        result["prunings"].append(item)
    result["status"] = _status(forward, coverage["pendingBranches"], retained_routes, endpoint)
    result["requestDigest"] = "sha256:" + fingerprint(raw).hex()
    result["analysisId"] = "sha256:" + fingerprint(result).hex()
    if encoded_size(result, caps["maxOutputBytes"]) > caps["maxOutputBytes"]:
        raise ValueError("output metadata exceeds maxOutputBytes")
    return result


def _reserve_mandatory_output(request, forward, caps):
    budget = OutputBudget(caps["maxOutputBytes"])
    step_refs = [
        row["stepRef"] for row in request.derivation_artifact.get("payload", {}).get("steps", [])
    ]
    maximum_explored = step_refs[: min(len(step_refs), caps["maxEvaluatedSteps"])]
    empty_work = {
        key: 0
        for key in (
            "forwardSteps",
            "plannerSteps",
            "totalSteps",
            "forwardCombinations",
            "plannerCombinations",
            "totalCombinations",
        )
    }
    header = {
        "schema": "ladon-contract-obligation-planner-v1",
        "status": "partial",
        "authority": "conditional-profile",
        "checkerAuthority": "none",
        "mathematicalFalsity": "not-established",
        "minimalityClaim": "none",
        "limitations": [
            "source-contract-binding-unchecked",
            "evidence-binding-unchecked",
            "clock-binding-unchecked",
        ],
        "desired": {
            "contractRecord": request.desired_contract,
            "readingIdentity": request.desired_reading_identity,
        },
        "analysisInputs": {
            "goalRef": request.goal_ref,
            "bounds": request.bounds or {},
            "desiredReadingIdentity": request.desired_reading_identity,
        },
        "routeComparisons": [],
        "comparisons": [],
        "backwardRequirements": [],
        "residuals": [],
        "prunings": [],
        "endpoint": {"status": "unresolved"},
        "priorityPolicy": ["source-location", "route-identity", "explicit-heuristic"],
        "coverage": {
            "exploredStepRefs": maximum_explored,
            "unvisitedApplications": [],
            "pendingBranches": [],
            "workBudget": empty_work,
            "forwardCoverage": {
                "counts": forward.get("coverage", {}).get("counts", {}),
                "pending": [],
            },
        },
        "requestDigest": "sha256:" + "0" * 64,
        "analysisId": "sha256:" + "0" * 64,
    }
    if not budget.reserve(header, overhead=128):
        raise ValueError("output metadata exceeds maxOutputBytes")
    pending_slot = {
        "applicationRef": request.goal_ref,
        "reason": "additional-work-omitted",
        "omittedCount": 1,
        "pendingDigest": "sha256:" + "0" * 64,
    }
    if not budget.reserve(pending_slot, copies=2, overhead=8):
        raise ValueError("output metadata exceeds maxOutputBytes")
    for item in forward.get("coverage", {}).get("pending", []):
        if not budget.reserve(item, overhead=8):
            raise ValueError("output metadata exceeds maxOutputBytes")
    return budget


def _reserve_pending(pending, budget):
    for row in pending:
        if not budget.reserve(row, copies=2, overhead=8):
            return False
    return True


def _pending_summary(pending, request):
    return {
        "applicationRef": request.goal_ref,
        "reason": "additional-work-omitted",
        "omittedCount": len(pending),
        "pendingDigest": "sha256:" + fingerprint(pending).hex(),
    }


def _append_pending_summary(coverage, request):
    rows = coverage["pendingBranches"]
    if not any(row.get("reason") == "additional-work-omitted" for row in rows):
        summary = _pending_summary(rows, request)
        rows[:] = [summary]
        coverage["unvisitedApplications"] = rows


def _result_header(request, forward, coverage, endpoint):
    result = {
        "schema": "ladon-contract-obligation-planner-v1",
        "status": "partial",
        "authority": "conditional-profile",
        "checkerAuthority": "none",
        "mathematicalFalsity": "not-established",
        "minimalityClaim": "none",
        "limitations": [
            "source-contract-binding-unchecked",
            "evidence-binding-unchecked",
            "clock-binding-unchecked",
        ],
        "desired": {
            "contractRecord": request.desired_contract,
            "readingIdentity": request.desired_reading_identity,
        },
        "analysisInputs": {
            "goalRef": request.goal_ref,
            "bounds": request.bounds or {},
            "desiredReadingIdentity": request.desired_reading_identity,
        },
        "routeComparisons": [],
        "comparisons": [],
        "backwardRequirements": [],
        "residuals": [],
        "prunings": [],
        "endpoint": endpoint,
        "priorityPolicy": ["source-location", "route-identity", "explicit-heuristic"],
        "coverage": coverage,
        "requestDigest": "sha256:" + "0" * 64,
        "analysisId": "sha256:" + "0" * 64,
    }
    return result


def _work_budget(ledger):
    return {
        key: ledger[key]
        for key in (
            "forwardSteps",
            "plannerSteps",
            "totalSteps",
            "forwardCombinations",
            "plannerCombinations",
            "totalCombinations",
        )
    }


def _pending_rows(request, forward, planner_pending, steps):
    pending = list(planner_pending)
    if forward.get("status") != "complete":
        pending.extend(
            {
                "applicationRef": row.get("stepRef") or row.get("statementRef") or request.goal_ref,
                "reason": row.get("code", "forward-budget"),
            }
            for row in forward.get("coverage", {}).get("pending", [])
        )
        if not pending:
            pending.extend(_fallback_pending(request, steps))
    return pending


def _fallback_pending(request, steps):
    described = {_refkey(value) for value in request.described_route_step_refs}
    return [
        {"applicationRef": step["stepRef"], "reason": "forward-budget"}
        for step in steps
        if _refkey(step["stepRef"]) not in described
    ]


def _coverage(forward, pending, work, steps, ledger):
    known = _known_step_refs(forward, ledger)
    pending_keys = {
        _refkey(row["applicationRef"])
        for row in pending
        if row.get("applicationRef", {}).get("kind") == "derivation-step"
    }
    ordered = [
        row["stepRef"]
        for row in steps
        if _refkey(row["stepRef"]) in known and _refkey(row["stepRef"]) not in pending_keys
    ]
    return {
        "exploredStepRefs": ordered,
        "unvisitedApplications": pending,
        "pendingBranches": pending,
        "workBudget": work,
        "forwardCoverage": forward.get("coverage", {}),
    }


def _known_step_refs(forward, ledger):
    known = {
        _refkey(row["routeWitness"]["stepRef"]): row["routeWitness"]["stepRef"]
        for row in forward.get("witnesses", [])
        if row.get("routeWitness", {}).get("stepRef")
    }
    for row in forward.get("residuals", []):
        if row.get("stepRef"):
            known[_refkey(row["stepRef"])] = row["stepRef"]
    for value in ledger.get("plannerStepRefs", []):
        known[_refkey(value)] = value
    return known


def _endpoint(forward, request, desired):
    goal_candidates = _frontier_map(forward).get(
        (request.goal_ref["kind"], request.goal_ref["localId"]), []
    )
    endpoint_supported = any(
        compare_contracts(row["contractRecord"], desired)["relation"] in {"dominates", "equivalent"}
        for row in goal_candidates
    )
    return {
        "status": "conditional-profile-support" if endpoint_supported else "unresolved",
        "supportKind": "profile-dominance" if endpoint_supported else None,
    }


def _status(forward, pending, route_rows, endpoint):
    status = "complete"
    if (
        forward.get("status") != "complete"
        or pending
        or endpoint["status"] != "conditional-profile-support"
    ):
        status = (
            "partial"
            if route_rows or forward.get("status") != "unsupported-cycle"
            else "unsupported"
        )
    return status


def _frontier_map(forward):
    return {
        (row["statementRef"]["kind"], row["statementRef"]["localId"]): row["contracts"]
        for row in forward.get("frontiers", [])
    }


def _result_shell(request, raw, desired, forward, status, routes, residuals, caps):
    from ladon._contract_propagation_budget import encoded_size

    result = {
        "schema": "ladon-contract-obligation-planner-v1",
        "status": status,
        "authority": "conditional-profile",
        "checkerAuthority": "none",
        "mathematicalFalsity": "not-established",
        "minimalityClaim": "none",
        "limitations": ["source-contract-binding-unchecked", "evidence-binding-unchecked"],
        "desired": {
            "contractRecord": request.desired_contract,
            "readingIdentity": request.desired_reading_identity,
        },
        "analysisInputs": {
            "goalRef": request.goal_ref,
            "bounds": request.bounds or {},
            "desiredReadingIdentity": request.desired_reading_identity,
        },
        "routeComparisons": routes,
        "comparisons": [],
        "backwardRequirements": [],
        "residuals": residuals or forward.get("residuals", []),
        "prunings": list(forward.get("prunings", [])),
        "endpoint": {"status": "unresolved"},
        "priorityPolicy": ["source-location", "route-identity", "explicit-heuristic"],
        "coverage": {
            "workBudget": {
                "forwardSteps": 0,
                "plannerSteps": 0,
                "totalSteps": 0,
                "forwardCombinations": 0,
                "plannerCombinations": 0,
                "totalCombinations": 0,
            },
            "pendingBranches": forward.get("coverage", {}).get("pending", []),
            "unvisitedApplications": forward.get("coverage", {}).get("pending", []),
        },
    }
    result["requestDigest"] = "sha256:" + "0" * 64
    result["analysisId"] = "sha256:" + "0" * 64
    if encoded_size(result, caps["maxOutputBytes"]) > caps["maxOutputBytes"]:
        raise ValueError("output metadata exceeds maxOutputBytes")
    result["requestDigest"] = "sha256:" + hashlib.sha256(_canonical(raw)).hexdigest()
    result["analysisId"] = "sha256:" + hashlib.sha256(_canonical(result)).hexdigest()
    return result
