"""Closed planner request and route metadata validation."""

from __future__ import annotations

import json

from ladon._contract_propagation_input_budget import input_bytes_exceeded
from ladon._contract_propagation_inputs import read_bounds
from ladon.proof_contracts import validate_contract


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _refkey(value):
    if type(value) is not dict or set(value) != {"kind", "localId"}:
        raise ValueError("reference must have kind and localId")
    if not isinstance(value["kind"], str) or not isinstance(value["localId"], str):
        raise TypeError("reference kind and localId must be strings")
    return value["kind"], value["localId"]


def _priority_key(row):
    location = row.get("sourceLocation")
    if location is None:
        location_key = (1, row["sourceId"], 0, 0)
    else:
        location_key = (0, location["path"], location["line"], location["column"])
    return location_key


def _preflight(request):
    raw = {
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
    _validate_size(raw)
    caps, deadline = read_bounds(request.bounds)
    steps, step_by_key = _read_steps(request)
    selected = _validate_selection(request, step_by_key)
    owned = set(step_by_key)
    _validate_priorities(request.route_priorities, owned, len(steps))
    choice_by_key = _validate_choices(request.per_application_backward_choices, owned, len(steps))
    _validate_reading(request.desired_reading_identity)
    desired = validate_contract(request.desired_contract)
    return raw, caps, deadline, steps, step_by_key, selected, choice_by_key, desired


def _validate_size(raw):
    if input_bytes_exceeded(raw) is not None:
        raise ValueError("aggregate input exceeds 8 MiB")


def _read_steps(request):
    steps = request.derivation_artifact.get("payload", {}).get("steps", [])
    if not isinstance(steps, list) or len(steps) > 8192:
        raise ValueError("derivation exceeds the step cap")
    step_by_key = {}
    for step in steps:
        key = _refkey(step.get("stepRef"))
        if key[0] != "derivation-step" or key in step_by_key:
            raise ValueError("derivation step references must be unique derivation-step refs")
        step_by_key[key] = step
    return steps, step_by_key


def _validate_selection(request, step_by_key):
    refs = request.described_route_step_refs
    if not isinstance(refs, list) or not refs:
        raise ValueError("described route must be a nonempty ordered step list")
    selected = []
    for value in refs:
        key = _refkey(value)
        if key not in step_by_key:
            raise ValueError("described route contains a foreign or wrong-kind step")
        selected.append(step_by_key[key])
    if any(
        left.get("conclusionRef")
        not in [
            premise for right in selected[index + 1 :] for premise in right.get("premiseRefs", [])
        ]
        for index, left in enumerate(selected[:-1])
    ):
        raise ValueError("described route steps are disconnected or out of order")
    if selected[-1].get("conclusionRef") != request.goal_ref:
        raise ValueError("described route must end at requested goal")
    return selected


def _validate_priorities(priorities, owned, step_count):
    if not isinstance(priorities, list) or len(priorities) > step_count:
        raise ValueError("route priorities must be a bounded list")
    seen = set()
    for row in priorities:
        key = _validate_priority_row(row, owned)
        if key in seen:
            raise ValueError("priority root must be unique")
        seen.add(key)


def _validate_priority_row(row, owned):
    fields = {"rootStepRef", "sourceLocation", "sourceId", "line", "column", "heuristicPriority"}
    if type(row) is not dict or set(row) != fields:
        raise ValueError("priority metadata has an invalid shape")
    key = _refkey(row["rootStepRef"])
    if key not in owned or key[0] != "derivation-step":
        raise ValueError("priority root must be a graph-owned derivation step")
    _validate_location(row)
    value = row["heuristicPriority"]
    if type(value) is not int or not -1000000 <= value <= 1000000:
        raise ValueError("heuristic priority must be a bounded integer")
    return key


def _validate_location(row):
    location = row["sourceLocation"]
    if location is None:
        _validate_fallback_location(row)
        return
    _validate_source_location(location, row)


def _validate_source_location(location, row):
    fields = {"path", "line", "column"}
    if type(location) is not dict or set(location) != fields:
        raise ValueError("source location has invalid fields")
    if location["line"] != row["line"] or location["column"] != row["column"]:
        raise ValueError("source location must agree with duplicate line and column")
    if not isinstance(location["path"], str) or not location["path"]:
        raise ValueError("source location path must be nonempty")
    _validate_location_numbers(location)


def _validate_location_numbers(location):
    if type(location["line"]) is not int or location["line"] < 1:
        raise ValueError("source location line must be positive")
    if type(location["column"]) is not int or location["column"] < 1:
        raise ValueError("source location column must be positive")


def _validate_fallback_location(row):
    if not isinstance(row["sourceId"], str) or not row["sourceId"]:
        raise ValueError("null source location requires stable sourceId")
    if row["line"] is not None or row["column"] is not None:
        raise ValueError("null source location requires null line/column")


def _validate_choices(choice_rows, owned, step_count):
    if not isinstance(choice_rows, list) or len(choice_rows) > step_count:
        raise ValueError("backward choices must be a bounded list")
    choice_by_key = {}
    for row in choice_rows:
        if type(row) is not dict or set(row) != {"stepRef", "choices"}:
            raise ValueError("backward choice row has invalid shape")
        key = _refkey(row["stepRef"])
        if key not in owned or key in choice_by_key or type(row["choices"]) is not dict:
            raise ValueError("backward choices must bind unique graph-owned steps")
        choice_by_key[key] = row["choices"]
    return choice_by_key


def _validate_reading(reading):
    if (
        type(reading) is not dict
        or set(reading) != {"readingId", "interpretationDigest"}
        or not all(isinstance(v, str) and v for v in reading.values())
    ):
        raise ValueError("desired reading identity has invalid shape")
