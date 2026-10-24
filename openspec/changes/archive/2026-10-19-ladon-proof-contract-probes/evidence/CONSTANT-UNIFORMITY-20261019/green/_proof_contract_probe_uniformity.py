"""Pure planning for closed, quantified Nat constant-uniformity probes."""
from __future__ import annotations

import hashlib

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.correspondence_interpretation import lower_formula

from ._proof_contract_probe_uniformity_ast import parse_uniformity_ast
from ._proof_contract_probe_uniformity_contracts import (
    uniformity_pair_residual,
    validate_uniformity_contract,
)

_MAX_BYTES = 8 * 1024 * 1024
_SCOPE = "closed-nat-constant-uniformity-v2"


def _goal(goal_id, kind, formula):
    digest = hashlib.sha256(formula.encode("utf-8")).hexdigest()
    return {"goalId": goal_id, "kind": kind, "goal": formula,
            "goalDigest": "sha256:" + digest, "status": "open"}


def _result(template, status, goals=None, residuals=None):
    return {"schema": "ladon-application-probe-plan-v1", "status": status,
            "template": template, "scope": _SCOPE, "goals": goals or [],
            "residuals": residuals or [], "checkerAuthority": "none",
            "wholeMethodAuthority": "none", "sourceFidelity": "attributed-unreviewed",
            "mathematicalFalsity": "not-established"}


def _residual(code, message, feature):
    return {"code": code, "message": message, "feature": feature}


def _validate_template(template):
    keys = {"familyId", "version", "direction", "kind"}
    if not isinstance(template, dict) or set(template) != keys:
        raise ValueError("template selectors must be a closed object")
    if any(not isinstance(value, str) for value in template.values()):
        raise ValueError("template selectors must be strings")
    if template["familyId"] != "constant-uniformity":
        raise ValueError("constant uniformity requires its registered family selector")
    if template["version"] not in {"constant-uniformity-v1", "constant-uniformity-v2"}:
        raise ValueError("unknown constant-uniformity template version")
    if template["direction"] not in {"left-to-right", "right-to-left"}:
        raise ValueError("invalid probe direction")
    if template["kind"] not in {"implication", "counterexample"}:
        raise ValueError("invalid probe kind")
    return {key: template[key] for key in ("familyId", "version", "direction", "kind")}


def _size_preflight(inputs):
    size = _planned_input_size(inputs)
    if size > _MAX_BYTES:
        raise ValueError("constant-uniformity input exceeds 8 MiB")
    if size * 4 > _MAX_BYTES:
        return _residual("expanded-goal-bound", "Conservative lowered-goal size exceeds 8 MiB.", "goal-size")
    return None


def _record_budget(record):
    symbols = record.get("symbols") if isinstance(record, dict) else None
    if not isinstance(symbols, dict):
        return False
    widest = max((_planned_input_size(row) for row in symbols.values()), default=1)
    formula_size = _planned_input_size(record.get("formula"))
    return formula_size * (widest + 32) <= _MAX_BYTES


def _closed_application(shared_slice):
    if not isinstance(shared_slice, dict) or shared_slice.get("localContext") != []:
        return None
    if shared_slice.get("complete") is not True or shared_slice.get("status") != "extracted":
        return None
    nodes = shared_slice.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 1:
        return None
    row = nodes[0]
    if not isinstance(row, dict) or row.get("kind") != "application" or row.get("premises") != []:
        return None
    return row


def _slice_type(shared_slice):
    row = _closed_application(shared_slice)
    if row is None:
        return None
    value = row.get("closedType")
    return value if isinstance(value, str) and value and len(value.encode("utf-8")) <= _MAX_BYTES else None


def _normalize_body(parsed):
    body = parsed["body"]
    right = body["right"]
    n_app = right["args"][1]
    add_app = n_app["args"][0]
    literal = add_app["args"][1]
    normalized_add = {**add_app, "args": [add_app["args"][0], {**literal, "name": "<offset>"}]}
    normalized_n = {**n_app, "args": [normalized_add, n_app["args"][1]]}
    normalized_right = {**right, "args": [right["args"][0], normalized_n]}
    return {**body, "right": normalized_right}


def _body_agrees(left, right):
    if left["roles"] != right["roles"] or left["symbolIds"] != right["symbolIds"]:
        return False
    if _normalize_body(left) != _normalize_body(right):
        return False
    return all(left["symbols"][key] == right["symbols"][key] for key in left["symbolIds"])


def _unsupported(template, message, feature):
    return _result(template, "unsupported", residuals=[_residual("unsupported-constant-uniformity", message, feature)])


def _lower_pair(left_record, right_record, left_ast, right_ast):
    try:
        left = lower_formula(left_ast["formula"], left_record["symbols"])
        right = lower_formula(right_ast["formula"], right_record["symbols"])
    except (TypeError, ValueError, KeyError, RecursionError) as error:
        return None, _residual("unsupported-lowering", str(error)[:240], "formula")
    return (left, right), None


def _goals(template, readings, actual):
    left, right = readings
    p, q = (left, right) if template["direction"] == "left-to-right" else (right, left)
    formal = f"({right}) ↔ ({actual})"
    probe = f"({p}) → ({q})" if template["kind"] == "implication" else f"({p}) ∧ ¬({q})"
    return [_goal("formal-reading", "formal-reading", formal), _goal("probe", "probe", probe)]


def constant_uniformity_result(left_record, right_record, left_contract, right_contract,
                               shared_slice, template):
    """Plan two open obligations while preserving both original quantifier orders."""
    bound = _size_preflight((left_record, right_record, left_contract, right_contract, shared_slice, template))
    selected = _validate_template(template)
    if bound:
        return _result(selected, "unsupported", residuals=[bound])
    if selected["version"] == "constant-uniformity-v1":
        return _result(selected, "unsupported", residuals=[_residual(
            "legacy-template", "The historical v1 family remains unsupported.", "constant-uniformity")])
    if not _record_budget(left_record) or not _record_budget(right_record):
        return _result(selected, "unsupported", residuals=[_residual(
            "expanded-goal-bound", "A formula and symbol map exceed the expansion budget.", "goal-size")])
    return _plan_supported(left_record, right_record, left_contract, right_contract, shared_slice, selected)


def _plan_supported(left_record, right_record, left_contract, right_contract, shared_slice, template):
    left_ast, right_ast = parse_uniformity_ast(left_record), parse_uniformity_ast(right_record)
    if left_ast is None or right_ast is None:
        return _unsupported(template, "The ASTs do not match the exact quantified Nat constant profile.", "formula")
    left_valid, left_state = validate_uniformity_contract(left_contract, left_ast)
    right_valid, right_state = validate_uniformity_contract(right_contract, right_ast)
    if left_state or right_state:
        return _result(template, "unsupported", residuals=[left_state or right_state])
    residual = uniformity_pair_residual(left_valid, right_valid, left_ast, right_ast)
    if residual:
        return _result(template, "unsupported", residuals=[residual])
    actual = _slice_type(shared_slice)
    if actual is None:
        return _result(template, "unsupported", residuals=[_residual(
            "nonclosed-shared-context", "The selected slice is not one closed premise-free application.", "shared-slice")])
    readings, error = _lower_pair(left_record, right_record, left_ast, right_ast)
    if error:
        return _result(template, "unsupported", residuals=[error])
    result = _result(template, "planned", goals=_goals(template, readings, actual))
    if _planned_input_size(result) > _MAX_BYTES:
        raise ValueError("expanded constant-uniformity plan exceeds 8 MiB")
    return result
