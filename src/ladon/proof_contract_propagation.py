"""Bounded conditional contract propagation over native AND/OR derivations.

Results preserve full route correlations and scoped, shared witness identities.
They are conditional summaries, never formal discharge or source fidelity.
"""

import hashlib

from ladon._contract_propagation_budget import encoded_size
from ladon._contract_propagation_common import (
    _canonical,
    _identifier,
    _input_context,
    _object,
    _partial_result,
    _plain,
)
from ladon._contract_propagation_deadline import DeadlineObservation
from ladon._contract_propagation_evaluator import Evaluation
from ladon._contract_propagation_input_budget import input_bytes_exceeded
from ladon._contract_propagation_inputs import (
    preflight_size,
    read_bounds,
    read_contracts,
    reference_count,
)
from ladon._contract_propagation_validation import _validate_inputs
from ladon._proofir_derivation_core import _Graph, _ref
from ladon.proof_contract_rules import PROFILE_DIGEST
from ladon.proofir_v3 import validate_envelope


def propagate_contracts(
    derivation_artifact,
    contract_artifacts,
    *,
    goal_ref,
    rule_bindings,
    endpoint_interfaces,
    scope_bindings=(),
    bounds=None,
):
    """Evaluate complete routes under fixed profile limits and one shared deadline."""
    return _propagate_contracts(
        derivation_artifact,
        contract_artifacts,
        goal_ref=goal_ref,
        rule_bindings=rule_bindings,
        endpoint_interfaces=endpoint_interfaces,
        scope_bindings=scope_bindings,
        bounds=bounds,
    )


def _propagate_contracts(
    derivation_artifact,
    contract_artifacts,
    *,
    goal_ref,
    rule_bindings,
    endpoint_interfaces,
    scope_bindings=(),
    bounds=None,
    _deadline_replay=None,
):
    _goal_shape(goal_ref)
    caps, deadline = read_bounds(bounds)
    deadline_observation = DeadlineObservation(deadline, replay=_deadline_replay)
    count = preflight_size(
        derivation_artifact, contract_artifacts, rule_bindings, endpoint_interfaces, scope_bindings
    )
    if count > caps["maxGraphReferences"]:
        return _with_deadline_trace(
            _small_partial(goal_ref, "graph-reference-cap", count, caps), deadline_observation, caps
        )
    size = input_bytes_exceeded([
        derivation_artifact, contract_artifacts, goal_ref, rule_bindings,
        endpoint_interfaces, scope_bindings, bounds,
    ])
    if size is not None:
        return _with_deadline_trace(
            _small_partial(goal_ref, "input-byte-cap", size, caps), deadline_observation, caps
        )
    if deadline_observation.expired():
        return _with_deadline_trace(
            _small_partial(goal_ref, "deadline", count, caps), deadline_observation, caps
        )
    derivation = validate_envelope(derivation_artifact).to_dict()
    graph = _Graph.build(derivation)
    goal, error = graph.local_ref(goal_ref, "/goalRef")
    if error:
        raise ValueError(error["message"])
    contracts = read_contracts(contract_artifacts, derivation["environmentRef"])
    bindings, interfaces, scopes = _validate_inputs(
        rule_bindings, endpoint_interfaces, scope_bindings, graph.subjects, contracts, graph
    )
    count = reference_count(graph, contracts, bindings, interfaces, scopes)
    context = _input_context(graph, contracts, bindings, interfaces, scopes, caps, deadline)
    if count > caps["maxGraphReferences"]:
        return _with_deadline_trace(
            _small_partial(goal_ref, "graph-reference-cap", count, caps, context),
            deadline_observation,
            caps,
        )
    state = Evaluation(graph, contracts, bindings, interfaces, scopes, caps, deadline_observation, count)
    if not state.budget.reserve(_result(goal, state, context), overhead=512):
        return _with_deadline_trace(
            _small_partial(goal_ref, "output-size-cap", state.budget.limit, caps, context),
            deadline_observation,
            caps,
        )
    if derivation["payload"]["acyclic"] is False:
        result = _cycles(derivation, goal, state, context)
    else:
        state.evaluate(goal)
        result = _result(goal, state, context)
    result["deadlineObservation"] = deadline_observation.finish()
    return _finish(result, goal_ref, caps, context)


def _with_deadline_trace(result, observation, caps):
    result["deadlineObservation"] = observation.finish()
    result.pop("analysisId", None)
    result["analysisId"] = "sha256:" + "0" * 64
    if encoded_size(result, caps["maxOutputBytes"]) > caps["maxOutputBytes"]:
        raise ValueError("output metadata exceeds maxOutputBytes")
    result.pop("analysisId")
    result["analysisId"] = "sha256:" + hashlib.sha256(_canonical(result)).hexdigest()
    return result


def _result(goal, state, context):
    complete = not any((state.uncertainty, state.pending, state.residuals, state.budget.exhausted))
    notice = (
        [{"code": "output-size-cap", "scope": "remaining-output"}] if state.budget.exhausted else []
    )
    return {
        "schema": "ladon-contract-propagation-v1",
        "status": "complete" if complete else "partial",
        "complete": complete,
        "goalRef": _ref(goal),
        "frontiers": [
            {"statementRef": _ref(statement), "contracts": rows}
            for statement, rows in sorted(state.frontiers.items())
        ],
        "prunings": state.prunings,
        "residuals": list(state.residuals) + notice,
        "coverage": {"counts": state.counts, "pending": list(state.pending) + notice},
        "witnesses": [
            {"witnessRef": key, "routeWitness": state.witnesses[key]}
            for key in sorted(state.witnesses)
        ],
        "analysisInputs": context,
        "profileDigest": PROFILE_DIGEST,
        "authority": "conditional-profile",
        "mathematicalFalsity": "not-established",
        "limitations": ["source-contract-binding-unchecked"],
    }


def _cycles(derivation, goal, state, context):
    components = derivation["payload"].get("recursion", {}).get("components", [])
    state.residuals.extend(
        {"code": "unsupported-cycle", "component": _plain(row)} for row in components
    )
    if not state.residuals:
        state.residuals.append({"code": "unsupported-cycle", "statementRef": _ref(goal)})
    result = _result(goal, state, context)
    result["status"] = "unsupported-cycle"
    result["coverage"]["pending"] = list(result["residuals"])
    return result


def _finish(result, goal, caps, context):
    provisional = {**result, "analysisId": "sha256:" + "0" * 64}
    if encoded_size(provisional, caps["maxOutputBytes"]) > caps["maxOutputBytes"]:
        raise ValueError("output metadata exceeds maxOutputBytes")
    result["analysisId"] = "sha256:" + hashlib.sha256(_canonical(result)).hexdigest()
    return result


def _small_partial(goal, code, count, caps, context=None):
    result = _partial_result(goal, code, count, context)
    if encoded_size(result, caps["maxOutputBytes"]) > caps["maxOutputBytes"]:
        raise ValueError("output metadata exceeds maxOutputBytes")
    return result


def _goal_shape(goal):
    _object(goal, {"kind", "localId"}, "goal_ref")
    _identifier(goal["localId"], "goal_ref.localId")
    if goal["kind"] != "statement":
        raise ValueError("goal_ref.kind must be statement")
