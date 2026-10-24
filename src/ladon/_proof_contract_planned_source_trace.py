"""Exact planner recomputation and source-leaf occurrence selection."""
from __future__ import annotations

import copy

from ._proof_contract_planned_source_inputs import _planned_input_size
from .proof_contract_obligation_planner import (
    ContractObligationPlanRequest,
    plan_contract_obligations,
)
from .proof_contract_source_obligations import MAX_INPUT_BYTES, _plain


def _select_verified_plan_requirement(plan_request, plan_result, route_index,
                                     requirement_index, selected_identity, *,
                                     deadline_monotonic=None, limits=None, receipts=None):
    recomputed = _recompute_verified_plan(plan_request, plan_result,
        deadline_monotonic=deadline_monotonic, limits=limits, receipts=receipts)
    route, selected = _indexed_plan_row(recomputed, route_index, requirement_index)
    _validate_plan_occurrence(recomputed, route, selected, selected_identity)
    _validate_plan_trace(plan_request, selected, route)
    _validate_plan_desired(plan_request, recomputed)
    return copy.deepcopy(selected)


def _recompute_verified_plan(plan_request, plan_result, *, deadline_monotonic=None,
                            limits=None, receipts=None):
    if not isinstance(plan_request, ContractObligationPlanRequest):
        raise TypeError("planRequest must be ContractObligationPlanRequest")
    if _planned_input_size(plan_request) > MAX_INPUT_BYTES:
        raise ValueError("planner request exceeds the 8 MiB bound")
    if not isinstance(plan_result, dict):
        raise TypeError("planResult must be a mapping")
    schema = plan_result.get("schema")
    if schema == "ladon-contract-obligation-planner-v2":
        recomputed = _recompute_v2(plan_request, plan_result, deadline_monotonic,
                                   limits, receipts)
    elif schema == "ladon-contract-obligation-planner-v1":
        recomputed = plan_contract_obligations(plan_request)
    else:
        raise ValueError("unsupported obligation planner result schema")
    if _plain(recomputed) != _plain(plan_result):
        raise ValueError("planResult differs from exact whole-plan recomputation")
    return recomputed


def _recompute_v2(request, result, deadline, limits, receipts):
    from .proof_contract_obligation_planner import _plan_contract_obligation_bundles
    from .proof_contract_obligation_supervision import run_obligation_planner
    from .proof_contract_source_obligations import SourceResourceLimit

    trace = result.get("deadlineObservation")
    if deadline is None:
        return _plan_contract_obligation_bundles(request, _deadline_replay=trace)
    checked = run_obligation_planner(request, deadline_monotonic=deadline,
        limits=limits, operation="replay-v2", deadline_observation=trace)
    if receipts is not None and checked.get("processReceipt") is not None:
        receipts.append(checked["processReceipt"])
    if checked["status"] == "incomplete":
        raise SourceResourceLimit(checked["diagnostic"]["message"])
    if checked["status"] != "completed":
        raise ValueError("supervised plan replay failed: " + checked["diagnostic"]["message"])
    return checked["result"]


def _indexed_plan_row(recomputed, route_index, requirement_index):
    if type(route_index) is not int or type(requirement_index) is not int:
        raise TypeError("route and requirement indices must be integers")
    if route_index < 0 or requirement_index < 0:
        raise ValueError("route and requirement indices must be nonnegative")
    routes = recomputed.get("routeComparisons")
    try:
        route = routes[route_index]
        selected = route["backwardRequirements"][requirement_index]
    except (IndexError, KeyError, TypeError) as error:
        raise ValueError("selected plan route or requirement is absent") from error
    return route, selected


def _validate_plan_occurrence(recomputed, route, selected, selected_identity):
    _validate_selected_identity(route, selected, selected_identity)
    _validate_top_level_requirement(recomputed, selected)
    _validate_unique_route_occurrence(recomputed, route, selected)


def _validate_selected_identity(route, selected, selected_identity):
    fields_ = ("stepRef", "witnessRef", "branchRef", "branchIndex", "premiseOrdinal",
               "forwardContractRef", "statementRef", "parentWitnessRef", "interfaceId")
    expected_identity = {"routeId": route["routeId"]} | {
        key: copy.deepcopy(selected[key]) for key in fields_
    }
    if not isinstance(selected_identity, dict) or set(selected_identity) != set(expected_identity):
        raise ValueError("selectedIdentity has an invalid closed schema")
    if _plain(selected_identity) != _plain(expected_identity):
        raise ValueError("selectedIdentity differs from exact route requirement")


def _validate_top_level_requirement(recomputed, selected):
    top_level_matches = [row for row in recomputed.get("backwardRequirements", [])
                         if row == selected]
    if len(top_level_matches) != 1:
        raise ValueError("selected requirement is absent from top-level plan output")


def _validate_unique_route_occurrence(recomputed, route, selected):
    routes = recomputed.get("routeComparisons", [])
    locator = (route["routeId"], selected["stepRef"], selected["witnessRef"],
               selected["branchRef"], selected["branchIndex"], selected["premiseOrdinal"])
    matches = []
    for candidate_route in routes:
        for row in candidate_route.get("backwardRequirements", []):
            key = (candidate_route["routeId"], row.get("stepRef"), row.get("witnessRef"),
                   row.get("branchRef"), row.get("branchIndex"), row.get("premiseOrdinal"))
            if key == locator:
                matches.append(row)
    if len(matches) != 1 or matches[0] != selected:
        raise ValueError("selected route occurrence is not unique")


def _validate_plan_trace(plan_request, selected, route):
    _validate_route_witness(route, selected)
    _validate_derivation_premise(plan_request, selected)
    _validate_interface_scope(plan_request, selected)


def _validate_route_witness(route, selected):
    if selected["witnessRef"] not in route.get("forwardRouteWitnessRefs", []):
        raise ValueError("selected witness is outside the route witness set")
    if selected["forwardContractRef"].get("kind") != "contract":
        raise ValueError("selected requirement is not an exposed source-contract leaf")


def _validate_derivation_premise(plan_request, selected):
    derivation = plan_request.derivation_artifact
    steps = derivation.get("payload", {}).get("steps", [])
    step_rows = [row for row in steps if row.get("stepRef") == selected["stepRef"]]
    if len(step_rows) != 1:
        raise ValueError("selected derivation step is missing or ambiguous")
    premises = step_rows[0].get("premiseRefs", [])
    ordinal = selected["premiseOrdinal"]
    if type(ordinal) is not int or not 0 <= ordinal < len(premises) or premises[ordinal] != selected["statementRef"]:
        raise ValueError("selected statement is not the exact derivation premise occurrence")


def _validate_interface_scope(plan_request, selected):
    interfaces = [row for row in plan_request.endpoint_interfaces
                  if row.get("interfaceId") == selected["interfaceId"]]
    scopes = [row for row in plan_request.scope_bindings
              if row.get("statementRef") == selected["statementRef"]]
    if len(interfaces) != 1 or interfaces[0].get("contractRef") != selected["forwardContractRef"]:
        raise ValueError("selected interface does not bind the source contract")
    if len(scopes) != 1 or scopes[0].get("contractRef") != selected["forwardContractRef"]:
        raise ValueError("selected statement scope does not bind the source contract")


def _validate_plan_desired(plan_request, recomputed):
    desired = recomputed.get("desired", {})
    analysis = recomputed.get("analysisInputs", {})
    if (desired.get("contractRecord") != plan_request.desired_contract
            or desired.get("readingIdentity") != plan_request.desired_reading_identity
            or analysis.get("desiredReadingIdentity") != plan_request.desired_reading_identity):
        raise ValueError("recomputed plan lost its original desired record or reading identity")


