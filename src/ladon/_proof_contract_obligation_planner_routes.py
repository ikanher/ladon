"""Native route replay, route-local findings, and backward templates."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from ladon.proof_contract_propagation import propagate_contracts
from ladon.proof_contracts import compare_contracts

from ._proof_contract_obligation_bundle import finish_bundle, new_bundle
from ._proof_contract_obligation_planner_backward import _backward_for_route
from ._proof_contract_obligation_planner_comparisons import (
    _earliest_unresolved,
    _final_goal_comparison,
    _local_requirement_comparisons,
    _route_endpoint,
    _route_priority,
    _unresolved_explanation,
)
from ._proof_contract_obligation_planner_replay import replay_context, replay_route
from ._proof_contract_obligation_planner_validation import _canonical, _priority_key, _refkey


def _witness_paths(forward, step_by_key, goal_ref, maximum_paths, maximum_depth):
    witnesses = {row["witnessRef"]: row["routeWitness"] for row in forward.get("witnesses", [])}
    roots = [
        key
        for key, witness in witnesses.items()
        if witness.get("stepRef")
        in [
            step["stepRef"]
            for step in step_by_key.values()
            if step.get("conclusionRef") == goal_ref
        ]
    ]
    paths, truncated = [], False

    def descend(ref, seen, active, ordered):
        nonlocal truncated
        if ref not in witnesses:
            return
        if ref in active:
            truncated = True
            return
        if ref in seen:
            return
        if len(seen) >= maximum_depth:
            truncated = True
            return
        witness = witnesses[ref]
        seen.add(ref)
        active.add(ref)
        for parent in witness.get("parentWitnessRefs", []):
            descend(parent, seen, active, ordered)
        active.remove(ref)
        ordered.append((ref, witness))

    for root in roots:
        remaining = maximum_paths - len(paths)
        if remaining <= 0:
            truncated = True
            break
        ordered = []
        descend(root, set(), set(), ordered)
        if ordered:
            paths.append(ordered)
    return paths, truncated


def _route_id(step_refs, witness_refs):
    return (
        "sha256:"
        + hashlib.sha256(
            _canonical(
                {
                    "stepRefs": step_refs,
                    "forwardRouteWitnessRefs": witness_refs,
                }
            )
        ).hexdigest()
    )


def _application_map(rows):
    return {_refkey(row["stepRef"]): row for row in rows}


def _run_forward(request, *, deadline_replay=None):
    if deadline_replay is not None:
        from .proof_contract_propagation import _propagate_contracts

        return _propagate_contracts(
            request.derivation_artifact,
            request.contract_artifacts,
            goal_ref=request.goal_ref,
            rule_bindings=request.rule_bindings,
            endpoint_interfaces=request.endpoint_interfaces,
            scope_bindings=request.scope_bindings,
            bounds=request.bounds,
            _deadline_replay=deadline_replay,
        )
    return propagate_contracts(
        request.derivation_artifact,
        request.contract_artifacts,
        goal_ref=request.goal_ref,
        rule_bindings=request.rule_bindings,
        endpoint_interfaces=request.endpoint_interfaces,
        scope_bindings=request.scope_bindings,
        bounds=request.bounds,
    )


def _analyze_routes(
    request, forward, desired, steps, step_by_key, selected, choices, caps, deadline, output_budget,
    *, bundle_mode=False, deadline_observation=None,
):
    priority_rows = {_refkey(row["rootStepRef"]): row for row in request.route_priorities}
    paths, paths_truncated = _witness_paths(
        forward,
        step_by_key,
        request.goal_ref,
        caps["maxWitnessCandidates"],
        caps["maxDepth"],
    )
    described_keys = [_refkey(step["stepRef"]) for step in selected]
    described_found = _described_route_found(paths, described_keys)
    frontier_by_statement = {
        tuple(row["statementRef"].values()): row["contracts"]
        for row in forward.get("frontiers", [])
    }
    binding_map = _application_map(request.rule_bindings)
    replay = replay_context(request, forward)
    counts = forward.get("coverage", {}).get("counts", {})
    ledger = {
        "forwardSteps": counts.get("steps", 0),
        "plannerSteps": 0,
        "plannerStepRefs": [],
        "totalSteps": counts.get("steps", 0),
        "forwardCombinations": counts.get("combinations", 0),
        "plannerCombinations": 0,
        "totalCombinations": counts.get("combinations", 0),
        "maxCombinationsPerStep": caps["maxCombinationsPerStep"],
        "maxOutputBytes": caps["maxOutputBytes"],
        "maxBackwardBranches": min(128, caps["maxCombinationsPerStep"]),
        "deadlineUtc": (request.bounds or {}).get("deadlineUtc"),
        "stepsRemaining": max(0, caps["maxEvaluatedSteps"] - counts.get("steps", 0)),
        "combinationsRemaining": max(
            0, caps["maxTotalCombinations"] - counts.get("combinations", 0)
        ),
    }
    route_rows, all_requirements, planner_pending = [], [], []
    planner_pending.extend(_missing_described_pending(selected, described_found))
    if paths_truncated:
        planner_pending.append(
            {"applicationRef": request.goal_ref, "reason": "witness-candidate-cap"}
        )
    residuals = list(forward.get("residuals", []))
    for path_index, path in enumerate(paths):
        if _deadline_reached(deadline, deadline_observation):
            planner_pending.extend(_expired_path_pending(paths[path_index:]))
            break
        row, requirements, route_residuals, route_pending = _analyze_one_route(
            request,
            path,
            desired,
            step_by_key,
            binding_map,
            choices,
            frontier_by_statement,
            priority_rows,
            described_keys,
            ledger,
            deadline,
            replay,
            desired,
            output_budget,
            bundle_mode=bundle_mode,
            deadline_observation=deadline_observation,
        )
        if row is not None:
            route_rows.append(row)
            all_requirements.extend(requirements)
        residuals.extend(route_residuals)
        planner_pending.extend(route_pending)
    route_rows.sort(
        key=lambda row: (
            _priority_key(row["priorityKey"]),
            row["routeId"],
            row["priorityKey"]["heuristicPriority"],
        )
    )
    return route_rows, all_requirements, residuals, ledger, planner_pending


def _described_route_found(paths, described_keys):
    return any(
        [_refkey(witness["stepRef"]) for _, witness in path if "stepRef" in witness]
        == described_keys
        for path in paths
    )


def _missing_described_pending(selected, described_found):
    if not selected or described_found:
        return []
    return [{"stepRef": selected[-1]["stepRef"], "reason": "described-route-witness-unavailable"}]


def _expired_path_pending(paths):
    rows = []
    for path in paths:
        steps = [row[1]["stepRef"] for row in path if "stepRef" in row[1]]
        if steps:
            rows.append(
                {
                    "stepRef": steps[-1],
                    "branchRef": _route_id(steps, [ref for ref, _ in path]),
                    "reason": "deadline",
                }
            )
    return rows


def _deadline_reached(deadline, observation=None):
    if observation is not None:
        return observation.expired()
    return deadline is not None and datetime.now(UTC) >= deadline


def _analyze_one_route(
    request,
    path,
    desired,
    step_by_key,
    bindings,
    choices,
    frontier,
    priorities,
    described_keys,
    ledger,
    deadline,
    replay,
    goal_desired,
    output_budget,
    *, bundle_mode=False, deadline_observation=None,
):
    application_path, path_steps, keys = _path_metadata(path)
    if not keys or keys[-1] not in step_by_key:
        return None, [], [], []
    priority = _route_priority(keys[0], priorities)
    row = {
        "routeId": _route_id(path_steps, [ref for ref, _ in path]),
        "stepRefs": path_steps,
        "forwardRouteWitnessRefs": [ref for ref, _ in path],
        "describedRoute": keys == described_keys,
        "priorityKey": priority,
        "status": "conditional-analysis",
        "comparisons": [],
        "endpoint": {"status": "unresolved"},
        "backwardRequirements": [],
        # Prepay the largest possible explanation before retaining children.
        "earliestUnresolved": _unresolved_explanation(2**53 - 1),
    }
    bundle = _initial_bundle(row, request) if bundle_mode else None
    if bundle_mode:
        row["obligationBundle"] = bundle
        row["residuals"] = []
    if not output_budget.reserve(row, overhead=256):
        pending = {
            "stepRef": path_steps[-1],
            "branchRef": row["routeId"],
            "reason": "output-size-cap",
        }
        return None, [], [], [pending]
    residuals = []
    requirements, more_residuals, route_pending, bundle = _run_route_backward(
        path,
        desired,
        step_by_key,
        bindings,
        request.endpoint_interfaces,
        choices,
        ledger,
        deadline,
        output_budget,
        row,
        bundle=bundle,
        bundle_mode=bundle_mode,
        deadline_observation=deadline_observation,
    )
    if bundle_mode:
        row["obligationBundle"] = bundle
    residuals.extend(more_residuals)
    comparisons, local_residuals = _local_requirement_comparisons(
        requirements, frontier, output_budget
    )
    residuals.extend(local_residuals)
    endpoint = _resolve_route_endpoint(
        application_path,
        path,
        desired,
        goal_desired,
        request.goal_ref,
        frontier,
        replay,
        ledger,
        deadline,
        route_pending,
        residuals,
        deadline_observation=deadline_observation,
    )
    comparisons.extend(
        _final_goal_comparison(path, goal_desired, request.goal_ref, replay, output_budget)
    )
    row.update(
        {"comparisons": comparisons, "endpoint": endpoint, "backwardRequirements": requirements,
         "earliestUnresolved": _earliest_unresolved(comparisons, path_steps)}
    )
    if bundle_mode:
        _finish_route_bundle(row, residuals, route_pending)
    _retain_route_output_stop(row, path_steps, route_pending, output_budget)
    return row, requirements, residuals, route_pending


def _retain_route_output_stop(row, path_steps, pending, budget):
    if budget.exhausted:
        pending.append({"stepRef": path_steps[-1], "branchRef": row["routeId"],
                        "reason": "output-size-cap"})


def _initial_bundle(row, request):
    from ladon._contract_propagation_budget import fingerprint

    digest = "sha256:" + fingerprint(_request_identity(request)).hex()
    return new_bundle(row["routeId"], digest)


def _run_route_backward(
    path, desired, step_by_key, bindings, interfaces, choices, ledger, deadline,
    output_budget, row, bundle, bundle_mode, deadline_observation,
):
    result = _backward_for_route(
        path,
        desired,
        step_by_key,
        bindings,
        interfaces,
        choices,
        ledger,
        deadline,
        ledger,
        output_budget,
        route_id=row["routeId"] if bundle_mode else None,
        request_digest=bundle["requestDigest"] if bundle_mode else None,
        bundle_mode=bundle_mode,
        deadline_observation=deadline_observation,
    )
    if bundle_mode:
        return result
    requirements, residuals, pending = result
    return requirements, residuals, pending, None


def _finish_route_bundle(row, residuals, pending):
    row["residuals"] = list(residuals)
    bundle = row["obligationBundle"]
    bundle["residuals"] = list(residuals)
    row["obligationBundle"] = finish_bundle(bundle, pending, residuals)


def _request_identity(request):
    return {
        "derivationArtifact": request.derivation_artifact,
        "contractArtifacts": request.contract_artifacts,
        "goalRef": request.goal_ref,
        "ruleBindings": request.rule_bindings,
        "endpointInterfaces": request.endpoint_interfaces,
        "scopeBindings": request.scope_bindings,
        "desiredContract": request.desired_contract,
        "desiredReadingIdentity": request.desired_reading_identity,
        "describedRouteStepRefs": request.described_route_step_refs,
        "perApplicationBackwardChoices": request.per_application_backward_choices,
        "routePriorities": request.route_priorities,
        "bounds": request.bounds,
    }


def _resolve_route_endpoint(
    application_path,
    path,
    desired,
    goal_desired,
    goal_ref,
    frontier,
    replay,
    ledger,
    deadline,
    pending,
    residuals,
    *, deadline_observation=None,
):
    endpoint = _route_endpoint(application_path, desired, goal_ref, frontier, [])
    if endpoint["status"] != "unresolved":
        return endpoint
    replayed, errors = replay_route(
        path, replay, ledger, deadline, deadline_observation=deadline_observation
    )
    if replayed is not None and compare_contracts(replayed, goal_desired)["relation"] in {
        "dominates",
        "equivalent",
    }:
        return {"status": "conditional-profile-support", "supportKind": "profile-dominance"}
    for error in errors:
        if error.get("code") in {"replay-work-budget-exhausted", "replay-output-budget-exhausted"}:
            pending.append(
                {
                    "stepRef": error["stepRef"],
                    "branchRef": error["witnessRef"],
                    "reason": "shared-replay-budget",
                }
            )
        else:
            residuals.append(error)
    return endpoint


def _path_metadata(path):
    applications = [row for row in path if "stepRef" in row[1]]
    steps = [row[1]["stepRef"] for row in applications]
    return applications, steps, [_refkey(value) for value in steps]
