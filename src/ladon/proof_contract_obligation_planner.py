"""Route-local conditional contract comparison and backward-template planning."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from ladon._contract_propagation_budget import encoded_size
from ladon._contract_propagation_deadline import DeadlineObservation

from ._proof_contract_obligation_planner_result import (
    _assemble_result,
    _reserve_mandatory_output,
    _result_shell,
)
from ._proof_contract_obligation_planner_routes import _analyze_routes, _run_forward
from ._proof_contract_obligation_planner_validation import _preflight


@dataclass(frozen=True)
class ContractObligationPlanRequest:
    derivation_artifact: Any
    contract_artifacts: Any
    goal_ref: Any
    rule_bindings: Any
    endpoint_interfaces: Any
    scope_bindings: Any
    desired_contract: Any
    desired_reading_identity: Any
    described_route_step_refs: Any
    per_application_backward_choices: Any
    route_priorities: Any
    bounds: Any = None


def plan_contract_obligations(request: ContractObligationPlanRequest) -> dict[str, Any]:
    """Compare native routes and emit bounded conditional profile templates."""
    return _plan(request, bundle_mode=False)


def plan_contract_obligation_bundles(
    request: ContractObligationPlanRequest,
) -> dict[str, Any]:
    """Emit planner-v2 with route-local OR-of-AND obligation demand bundles."""
    return _plan(request, bundle_mode=True)


def _plan_contract_obligation_bundles(request, *, _deadline_replay):
    """Replay planner-v2 with explicit forward and planner deadline traces."""
    if type(_deadline_replay) is not dict or set(_deadline_replay) != {"forward", "planner"}:
        raise ValueError("planner-v2 replay requires forward and planner deadline traces")
    from ladon._contract_propagation_deadline import validate_deadline_trace

    traces = {key: validate_deadline_trace(_deadline_replay[key]) for key in ("forward", "planner")}
    return _plan(request, bundle_mode=True, deadline_replay=traces)


def _plan(request, *, bundle_mode, deadline_replay=None):
    if not isinstance(request, ContractObligationPlanRequest):
        raise TypeError("request must be ContractObligationPlanRequest")
    raw, caps, deadline, steps, step_by_key, selected, choices, desired = _preflight(request)
    deadline_observation = (
        DeadlineObservation(
            deadline,
            replay=deadline_replay.get("planner") if deadline_replay else None,
        ) if bundle_mode else None
    )
    forward = _run_forward(
        request,
        deadline_replay=deadline_replay.get("forward") if bundle_mode and deadline_replay else None,
    )
    if forward.get("status") == "unsupported-cycle":
        return _owned(
            _version_bundle_result(
                _result_shell(request, raw, desired, forward, "unsupported-cycle", [], [], caps),
                deadline_observation,
                forward.get("deadlineObservation"),
                caps["maxOutputBytes"],
            ) if bundle_mode else
            _result_shell(request, raw, desired, forward, "unsupported-cycle", [], [], caps)
        )
    output_budget = _reserve_mandatory_output(request, forward, caps)
    routes, requirements, residuals, ledger, planner_pending = _analyze_routes(
        request,
        forward,
        desired,
        steps,
        step_by_key,
        selected,
        choices,
        caps,
        deadline,
        output_budget,
        bundle_mode=bundle_mode,
        deadline_observation=deadline_observation,
    )
    result = _assemble_result(
            request,
            raw,
            forward,
            routes,
            requirements,
            residuals,
            caps,
            steps,
            ledger,
            planner_pending,
            output_budget,
        )
    if bundle_mode:
        result = _version_bundle_result(
            result, deadline_observation, forward.get("deadlineObservation"),
            caps["maxOutputBytes"],
        )
    return _owned(result)


def _version_bundle_result(result, observation, forward_observation, max_output_bytes):
    import hashlib

    from ._proof_contract_obligation_planner_validation import _canonical

    result["schema"] = "ladon-contract-obligation-planner-v2"
    result["deadlineObservation"] = {
        "forward": forward_observation,
        "planner": observation.finish(),
    }
    result.pop("analysisId", None)
    result["analysisId"] = "sha256:" + hashlib.sha256(_canonical(result)).hexdigest()
    if encoded_size(result, max_output_bytes) > max_output_bytes:
        raise ValueError("planner-v2 output exceeds maxOutputBytes")
    return result


def _owned(result):
    return deepcopy(result)
