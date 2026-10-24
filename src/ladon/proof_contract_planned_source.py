"""Conditional source materialization of a recomputed planner leaf."""
from __future__ import annotations

import copy
import math
import time
from pathlib import Path

from ._proof_contract_planned_source_binding import _validate_plan_provider
from ._proof_contract_planned_source_inputs import _planned_deadline, _planned_input_size
from ._proof_contract_planned_source_trace import _select_verified_plan_requirement
from ._proof_contract_source_obligations_formula import _formula_symbols
from ._proof_contract_source_obligations_prefix import check_generated_prefix
from ._proof_contract_source_obligations_roles import _requirement_symbols
from ._proof_contract_source_obligations_staging import _stage_source
from .proof_contract_formal import verify_formal_snapshot
from .proof_contract_obligation_planner import ContractObligationPlanRequest
from .proof_contract_source_obligations import (
    MAX_INPUT_BYTES,
    SourceIncomplete,
    SourceResourceLimit,
    _bounded_result,
    _check_capture_binding,
    _check_deadline,
    _check_stage_result,
    _fresh_formal_observation,
    _limits,
    _remaining,
    _require_fresh_snapshot_match,
    _result,
    _runner,
)
from .proof_slice import pinned_toolchain
from .source_goal_capture import SourceGoalCaptureRequest, capture_source_goal

_PLANNED_REQUEST_KEYS = {"repoRoot", "parentSnapshot", "providerSnapshot",
    "parentReadingId", "providerReadingId", "planRequest", "planResult",
    "routeIndex", "requirementIndex", "selectedIdentity", "deadlineMonotonic", "limits"}


def instantiate_planned_source_leaf_requirement(request: dict[str, object]) -> dict[str, object]:
    """Construct one route-local source leaf after exact whole-plan validation."""
    started = time.monotonic()
    state = {"owned": request if isinstance(request, dict) else {},
             "planVerified": False, "sourceBindingVerified": False,
             "selected": None, "parent": None, "provider": None,
             "parentFresh": None, "providerFresh": None}
    try:
        _prepare_planned_state(request, state)
        _build_planned_candidate(state)
        return _planned_success_result(state, started)
    except (SourceResourceLimit, SourceIncomplete, TimeoutError, OSError,
            ValueError, TypeError, KeyError, IndexError, OverflowError) as error:
        return _planned_failure_result(state, error, started)


def _prepare_planned_state(request, state):
    owned = state["owned"]
    if not isinstance(request, dict) or set(request) != _PLANNED_REQUEST_KEYS:
        raise TypeError("planned source request must use the closed mapping schema")
    if _planned_input_size(request) > MAX_INPUT_BYTES:
        raise ValueError("planned source request exceeds the 8 MiB bound")
    owned = state["owned"] = copy.deepcopy(request)
    deadline = owned["deadlineMonotonic"]
    if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
        raise ValueError("deadlineMonotonic must be finite")
    plan_request = owned["planRequest"]
    if not isinstance(plan_request, ContractObligationPlanRequest):
        raise TypeError("planRequest must be ContractObligationPlanRequest")
    state["deadline"] = _planned_deadline(deadline, plan_request)
    _check_deadline(state["deadline"])
    state["limits"] = _limits(owned["limits"])
    state["plannerReceipts"] = []
    state["selected"] = _select_verified_plan_requirement(plan_request,
        owned["planResult"], owned["routeIndex"], owned["requirementIndex"],
        owned["selectedIdentity"], deadline_monotonic=state["deadline"],
        limits=state["limits"], receipts=state["plannerReceipts"])
    state["planVerified"] = True
    _check_deadline(state["deadline"])
    _validate_planned_reading_labels(owned, plan_request)
    state["root"] = Path(owned["repoRoot"]).resolve(strict=True)


def _validate_planned_reading_labels(owned, plan_request):
    reading = plan_request.desired_reading_identity
    if not isinstance(owned["parentReadingId"], str) or owned["parentReadingId"] != reading.get("readingId"):
        raise ValueError("parentReadingId does not match original plan reading identity")
    if not isinstance(owned["providerReadingId"], str) or not owned["providerReadingId"] or len(owned["providerReadingId"]) > 256:
        raise ValueError("providerReadingId must be a bounded attributed label")


def _build_planned_candidate(state):
    root, owned = state["root"], state["owned"]
    plan_request, selected = owned["planRequest"], state["selected"]
    parent = state["parent"] = verify_formal_snapshot(owned["parentSnapshot"], root)
    provider = state["provider"] = verify_formal_snapshot(owned["providerSnapshot"], root)
    if parent.get("contract") != plan_request.desired_contract:
        raise ValueError("parent snapshot differs from the plan's original desired contract")
    _validate_plan_provider(selected, plan_request, provider, parent, root)
    _construct_planned_goal(state)


def _construct_planned_goal(state):
    owned, selected = state["owned"], state["selected"]
    parent, provider, root = state["parent"], state["provider"], state["root"]
    limits, deadline = state["limits"], state["deadline"]
    parent_fresh = state["parentFresh"] = _fresh_formal_observation(parent, root, _runner(deadline), limits)
    _require_fresh_snapshot_match(parent, parent_fresh)
    _check_deadline(deadline)
    provider_fresh = state["providerFresh"] = _fresh_formal_observation(provider, root, _runner(deadline), limits)
    _require_fresh_snapshot_match(provider, provider_fresh)
    expected = _planned_expected_symbols(parent_fresh, provider_fresh, selected)
    state["sourceBindingVerified"] = True
    _check_deadline(deadline)
    staged = _stage_source(root, parent, provider, expected, owned, deadline)
    _capture_planned_goal(state, expected, staged)


def _planned_expected_symbols(parent_fresh, provider_fresh, selected):
    try:
        parent_symbols = _formula_symbols(parent_fresh["observation"]["normalizedTypeExpr"])
        provider_symbols = _formula_symbols(provider_fresh["observation"]["normalizedTypeExpr"])
    except ValueError as error:
        raise SourceIncomplete(str(error)) from error
    if parent_symbols["constantName"] != provider_symbols["constantName"]:
        raise SourceIncomplete("source leaf changes the plan's global coefficient")
    local = _requirement_symbols(selected)
    if any(local[key] != provider_symbols[key] for key in ("leftOperator", "map", "inputScale")):
        raise SourceIncomplete("selected local requirement differs from provider source symbols")
    return {"kind": "forallNat2", **provider_symbols, "offset": local["offset"]}


def _capture_planned_goal(state, expected, staged):
    parent, root = state["parent"], state["root"]
    request_digest, source_path, line, column, prefix_digest, generated_digest, generated, prefix_subject = staged
    limits, deadline = state["limits"], state["deadline"]
    context = pinned_toolchain(root)
    if context.context_identity != parent["environment"]:
        raise ValueError("staged source context differs from snapshot environment")
    prefix_check = check_generated_prefix(root, prefix_subject, context.context_identity,
        limits, _runner(deadline))
    _check_deadline(deadline)
    capture_request = SourceGoalCaptureRequest(repo_root=root, source_path=source_path,
        module="Probe", line=line, column=column, toolchain=context,
        expected_source_digest="sha256:" + generated_digest,
        timeout_seconds=_remaining(deadline, limits["timeout_seconds"]),
        max_output_bytes=limits["max_output_bytes"], max_rss_bytes=limits["max_rss_bytes"])
    captured = capture_source_goal(capture_request, runner=_runner(deadline))
    _check_stage_result(captured)
    _check_capture_binding(captured, source_path, generated_digest,
        context.context_identity, parent["selection"]["module"], expected, generated)
    state["success"] = (request_digest, source_path, line, column, prefix_digest,
        generated_digest, captured, prefix_check)


def _planned_success_result(state, started):
    request_digest, _path, _line, _column, prefix_digest, generated_digest, captured, prefix_check = state["success"]
    owned, selected = state["owned"], state["selected"]
    reading = owned["planRequest"].desired_reading_identity["readingId"]
    output = _result("candidate-goal", "captured-closed-goal",
        "One route-local source-leaf goal was captured; no route proof was attempted.",
        owned | {"desiredReadingId": reading}, selected, state["parent"], state["provider"],
        prefix_digest, generated_digest, captured, request_digest=request_digest,
        prefix_check=prefix_check, parent_fresh=state["parentFresh"],
        provider_fresh=state["providerFresh"], elapsed=time.monotonic()-started)
    output.update(_planned_result_bindings(owned, selected, True, True))
    if state.get("plannerReceipts"):
        output["plannerProcessReceipts"] = state["plannerReceipts"]
    return _bounded_result(output)


def _planned_failure_result(state, error, started):
    status, code = _planned_error_status(error)
    output = _result(status, code, str(error), state["owned"], state["selected"],
        state["parent"], state["provider"], parent_fresh=state["parentFresh"],
        provider_fresh=state["providerFresh"], elapsed=time.monotonic()-started)
    output.update(_planned_result_bindings(state["owned"], state["selected"],
        state["planVerified"], state["sourceBindingVerified"]))
    if state.get("plannerReceipts"):
        output["plannerProcessReceipts"] = state["plannerReceipts"]
    return _bounded_result(output)


def _planned_error_status(error):
    if isinstance(error, SourceResourceLimit):
        return "incomplete", "resource-limit"
    if isinstance(error, SourceIncomplete):
        return "incomplete", "unsupported-source-fragment"
    if isinstance(error, (TimeoutError, OSError)):
        return "incomplete", "resource-limit-or-io"
    return "rejected", "source-bound-validation"


def _planned_result_bindings(request, selected, plan_verified=False, source_binding_verified=False):
    plan_result = request.get("planResult") if isinstance(request, dict) else None
    if not plan_verified or not isinstance(plan_result, dict):
        return {"planStatus": None, "routeComparisons": [], "selectedRouteId": None,
                "planCoverage": None, "selectedIdentity": None,
                "planVerified": False, "sourceBindingVerified": False}
    return {"planStatus": plan_result.get("status"),
        "routeComparisons": copy.deepcopy(plan_result.get("routeComparisons", [])),
        "selectedRouteId": (request.get("selectedIdentity", {}).get("routeId")
                             if isinstance(request.get("selectedIdentity"), dict) else None),
        "planCoverage": copy.deepcopy(plan_result.get("coverage")),
        "selectedIdentity": copy.deepcopy(request.get("selectedIdentity")),
        "selectedRequirement": copy.deepcopy(selected) if selected is not None else None,
        "planVerified": True, "sourceBindingVerified": bool(source_binding_verified)}


