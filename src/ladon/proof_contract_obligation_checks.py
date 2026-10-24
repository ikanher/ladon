"""Bounded public source checks over exact validated obligation bundles."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ._proof_contract_obligation_check_inputs import (
    MAX_MESSAGE,
    _provider_index,
    _ref_key,
    _requirements_for_demand,
    _selected_identity,
    _validate_and_own,
    _validation_plan,
    _verify_parent_identity,
)
from ._proof_contract_obligation_check_reporting import (
    _bounded_validation_report,
    _contract_declaration,
    _declaration,
    _finish,
    _mkdir,
    _require_fresh_output,
    _reserve_summary,
    _save_json,
    _slug,
)
from .proof_contract_source_obligations import _plain


def check_obligation_sources(request: dict[str, Any]) -> dict[str, Any]:
    """Validate native inputs, preserve source evidence, and report local checks.

    This operation deliberately makes no whole-method or falsity claim. A
    successful source check is support for one exact conditional leaf only.
    """
    started = time.monotonic()
    state: dict[str, Any] = {"sourceChecks": [], "providerSliceRequests": [],
                             "files": [], "bytes": 0, "summaryReserve": 256 * 1024,
                             "outputOwned": False, "attempts": 0}
    out = None
    try:
        owned = _validate_and_own(request)
        out = Path(owned["outputDir"])
        _require_fresh_output(out)
        out.mkdir(parents=True, exist_ok=False)
        state["outputOwned"] = True
        _mkdir(out / "source-requests")
        _mkdir(out / "source-wrappers")
        _mkdir(out / "constructions")
        _mkdir(out / "proof-attempts")
        return _run_validated(out, owned, state, started)
    except (ValueError, TypeError, KeyError, OSError, OverflowError) as error:
        state["inputFailure"] = {"code": "invalid-source-check-request",
                                  "message": str(error)[:MAX_MESSAGE]}
        return _finish(out, request if isinstance(request, dict) else {}, state, started)



def _run_validated(out, owned, state, started):
    from ladon.proof_contract_obligation_supervision import run_obligation_validation

    if not _save_json(out, state, "input.json", owned):
        state.update(stopped=True, stopReason="aggregate evidence budget exhausted before validation")
        return _finish(out, owned, state, started)
    checked = run_obligation_validation(owned["analysisArtifact"], owned["context"],
        deadline_monotonic=owned["deadlineMonotonic"], limits=owned["limits"])
    state["validation"] = _bounded_validation_report(checked)
    valid = checked.get("status") == "completed" and isinstance(checked.get("result"), dict)
    if valid:
        plan_request, plan_result = _validation_plan(checked, owned["context"])
        _initialize_coverage(state, plan_result.get("routeComparisons", []))
        _reserve_summary(state)
    if not _save_json(out, state, "validation.json", _validation_receipt(checked)):
        state.update(stopped=True, stopReason="aggregate evidence budget exhausted saving validation")
        return _finish(out, owned, state, started)
    if not valid:
        state["stopped"] = checked.get("status") == "incomplete"
        if state["stopped"]:
            diagnostic = checked.get("diagnostic") or {}
            state["stopReason"] = str(diagnostic.get("message", "native validation stopped"))[:MAX_MESSAGE]
            state["memoryReportBackRequired"] = diagnostic.get("code") == "memory-limit"
        return _finish(out, owned, state, started)
    routes = plan_result.get("routeComparisons", [])
    _check_routes(out, owned, state, plan_request, plan_result, routes)
    return _finish(out, owned, state, started)



def _validation_receipt(checked):
    return {'schema': 'ladon-obligation-validation-receipt-v1',
        'validatedArtifactRef': (checked.get('result') or {}).get('artifactId'),
        'supervision': {key: value for key, value in checked.items() if key != 'result'}}



def _check_routes(out, owned, state, plan_request, plan_result, routes):
    providers = _provider_index(owned["sourceBindings"]["providers"])
    _verify_parent_identity(plan_request, owned["sourceBindings"]["parentReadingId"])
    for route_index, route in enumerate(routes):
        for demand in _source_demands(route):
            if state.get("stopped"):
                return
            if time.monotonic() >= owned["deadlineMonotonic"]:
                state.update(stopped=True, stopReason="shared absolute deadline expired")
                return
            _check_demand(out, state, owned, plan_request, plan_result,
                          route, route_index, demand, providers)



def _check_demand(out, state, owned, plan_request, plan_result, route,
                  route_index, demand, providers):
    matches = _requirements_for_demand(route.get("backwardRequirements", []), demand)
    if not matches:
        return
    requirement_index, row = matches[0]
    check = state["coverageIndex"][(route["routeId"], demand["demandId"])]
    check["providerDeclaration"] = _contract_declaration(row.get("forwardContractRef"))
    provider = providers.get(_ref_key(row.get("forwardContractRef")))
    if provider is None:
        _missing_provider(state, check, demand, route, row, owned)
    else:
        _check_one(out, state, check, owned, plan_request, plan_result, route,
                   route_index, requirement_index, row, demand, provider)



def _source_demands(route):
    demands = route.get("obligationBundle", {}).get("demands", [])
    return [row for row in demands if row.get("status") == "requires-source-check"]



def _initialize_coverage(state, routes):
    state["coverageIndex"] = {}
    state["routeCoverage"] = []
    for route in routes:
        bundle = route.get("obligationBundle", {})
        demands = bundle.get("demands", [])
        coverage = {"routeId": route.get("routeId"),
            "describedRoute": bool(route.get("describedRoute")),
            "bundleStatus": bundle.get("status"),
            "pending": bundle.get("pending", []),
            "residuals": bundle.get("residuals", []),
            "sourceDemandIds": [], "sourceCheckStatus": "unresolved"}
        state["routeCoverage"].append(coverage)
        for demand in demands:
            if demand.get("status") != "requires-source-check":
                continue
            check = {"providerDeclaration": None, "status": "unresolved",
                "sourceRequest": None, "construction": None,
                "demandId": demand.get("demandId"),
                "sourceRef": demand.get("witnessRef"),
                "incomingOccurrences": demand.get("incomingOccurrences", []),
                "routes": [{"describedRoute": coverage["describedRoute"],
                    "routeId": coverage["routeId"], "sourceCheckStatus": "unresolved"}]}
            state["sourceChecks"].append(check)
            state["coverageIndex"][(coverage["routeId"], demand.get("demandId"))] = check
            coverage["sourceDemandIds"].append(demand.get("demandId"))



def _check_one(out, state, check, request, plan_request, plan_result, route, route_index,
               requirement_index, requirement, demand, provider):
    source = _source_request(request, plan_request, plan_result, route, route_index,
                             requirement_index, requirement, demand, provider)
    stem = _slug(provider["providerSnapshot"])
    key = f"{stem}-{demand['demandId'][-16:]}"
    req_path, construction_path = f"source-requests/{key}.json", f"constructions/{key}.json"
    if not _save_source_inputs(out, state, req_path, source, route, demand, provider, key):
        return
    construction = _construct_source_leaf(source)
    if not _save_json(out, state, construction_path, construction):
        state.update(stopped=True, stopReason="aggregate evidence budget exhausted after construction")
        return
    check.update(providerDeclaration=_declaration(provider["providerSnapshot"]),
                 sourceRequest=req_path, construction=construction_path)
    _attempt_terms(out, state, check, request, construction, provider, key, demand)
    check["routes"][0]["sourceCheckStatus"] = (
        "checked" if check["status"] == "checked-support" else "unresolved")



def _source_request(request, plan_request, plan_result, route, route_index,
                    requirement_index, requirement, demand, provider):
    return {"repoRoot": str(Path(request["repoRoot"]).resolve()),
        "parentSnapshot": request["sourceBindings"]["parentSnapshot"],
        "providerSnapshot": provider["providerSnapshot"],
        "parentReadingId": request["sourceBindings"]["parentReadingId"],
        "providerReadingId": provider["providerReadingId"],
        "planRequest": plan_request, "planResult": plan_result,
        "routeIndex": route_index, "requirementIndex": requirement_index,
        "selectedIdentity": _selected_identity(route, requirement),
        "deadlineMonotonic": request["deadlineMonotonic"], "limits": request["limits"]}



def _save_source_inputs(out, state, request_path, request, route, demand, provider, key):
    if not _save_json(out, state, request_path, _plain(request)):
        state.update(stopped=True, stopReason="evidence budget exhausted before construction")
        return False
    wrapper = {"routeId": route["routeId"], "demand": demand,
        "providerDeclaration": _declaration(provider["providerSnapshot"]),
        "sourceRequest": request_path}
    if not _save_json(out, state, f"source-wrappers/{key}.json", wrapper):
        state.update(stopped=True, stopReason="evidence budget exhausted before construction")
        return False
    return True



def _construct_source_leaf(request):
    from ladon.proof_contract_source_obligations import instantiate_planned_source_leaf_requirement
    return instantiate_planned_source_leaf_requirement(request)



def _attempt_terms(out, state, check, request, construction, provider, key, demand):
    if construction.get("status") != "candidate-goal" or not isinstance(construction.get("capture"), dict):
        _construction_stop(state, construction)
        return
    for index, term in enumerate(provider["terms"], 1):
        if state["attempts"] >= request["maxCheckAttempts"] or state.get("stopped"):
            return
        state["attempts"] += 1
        completion = _complete_term(state, request, construction["capture"], term)
        if completion is None:
            return
        path = f"proof-attempts/{key}-{index}.json"
        if not _save_json(out, state, path, completion):
            state.update(stopped=True, stopReason="evidence budget exhausted during proof attempt")
            return
        if _completion_accepted(completion):
            check["status"] = "checked-support"
            return
        if completion.get("status") in {"timeout", "memory-limit", "output-limit"}:
            _completion_stop(state, completion)
            return



def _complete_term(state, request, capture, term):
    from ladon.proof_contract_source_obligations import SourceResourceLimit, _runner
    from ladon.proof_slice import pinned_toolchain
    from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

    deadline = request["deadlineMonotonic"]
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        state.update(stopped=True, stopReason="shared absolute deadline expired during source completion")
        return None
    try:
        return complete_source_goal(SourceGoalCompletionRequest(
            repo_root=Path(request["repoRoot"]), capture=capture, term=term,
            toolchain=pinned_toolchain(Path(request["repoRoot"])),
            timeout_seconds=min(float(request["limits"]["timeout_seconds"]), remaining),
            max_output_bytes=request["limits"]["max_output_bytes"],
            max_rss_bytes=request["limits"]["max_rss_bytes"]), runner=_runner(deadline))
    except SourceResourceLimit as error:
        message = str(error)
        state.update(stopped=True, stopReason=message[:MAX_MESSAGE],
                     memoryReportBackRequired="memory" in message.lower())
        return {"status": "incomplete", "diagnostic": {
            "code": "source-completion-resource-stop", "message": message[:MAX_MESSAGE]}}



def _completion_stop(state, completion):
    diagnostic = completion.get("diagnostic", {})
    message = diagnostic.get("message") if isinstance(diagnostic, dict) else None
    state.update(stopped=True, stopReason=str(message or completion.get("status"))[:MAX_MESSAGE],
                 memoryReportBackRequired=completion.get("status") == "memory-limit")



def _construction_stop(state, construction):
    diagnostic = construction.get("diagnostic", {})
    if diagnostic.get("code") in {"resource-limit", "resource-limit-or-io"}:
        message = diagnostic.get("message", "source construction resource stop")
        state.update(stopped=True, stopReason=str(message)[:MAX_MESSAGE],
                     memoryReportBackRequired="memory" in str(message).lower())



def _missing_provider(state, check, demand, route, requirement, request):
    from .proof_contract_provider_expansion import make_provider_slice_request

    generated = make_provider_slice_request(request['analysisArtifact'], request['context'],
        route, demand, requirement, request['deadlineMonotonic'], request['limits'])
    if not _admit_provider_request(state, generated):
        return
    state['providerSliceRequests'].append(generated)
    check.update(providerDeclaration=_contract_declaration(requirement.get('forwardContractRef')),
                 status='unavailable-provider')



def _admit_provider_request(state, generated):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    # Pending requests are saved in the final summary. Reserve their bytes now
    # so subsequent proof files and requests cannot consume the same capacity.
    required = _planned_input_size(generated)+1
    reserve = state['summaryReserve']+required
    if state['bytes']+reserve > 8*1024**2:
        state.update(stopped=True, stopReason='aggregate evidence budget exhausted retaining provider requests')
        return False
    state['summaryReserve'] = reserve
    return True


def _completion_accepted(result):
    replay, trust = result.get("replay"), result.get("trust")
    return (result.get("status") == "completed" and isinstance(replay, dict)
            and replay.get("status") == "accepted" and isinstance(trust, dict)
            and trust.get("accepted") is True)
