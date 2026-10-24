"""Bounded source-bound planning for inequality-direction-v2."""
from __future__ import annotations

import hashlib

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.correspondence_interpretation import lower_formula

from ._proof_contract_probe_inequality_ast import parse_inequality_ast
from ._proof_contract_probe_inequality_contracts import validate_inequality_pair
from ._proof_contract_probe_templates import _residual, _shared_type

_MAX_BYTES = 8 * 1024 * 1024
_SCOPE = "closed-nat-zero-inequality-direction-v2"


def _result(template, status, goals=None, residuals=None):
    return {"schema": "ladon-application-probe-plan-v1", "status": status,
            "template": template, "scope": _SCOPE, "goals": goals or [],
            "residuals": residuals or [], "checkerAuthority": "none",
            "wholeMethodAuthority": "none", "sourceFidelity": "attributed-unreviewed",
            "mathematicalFalsity": "not-established"}


def _goal(goal_id, kind, formula):
    digest = hashlib.sha256(formula.encode("utf-8")).hexdigest()
    return {"goalId": goal_id, "kind": kind, "goal": formula,
            "goalDigest": "sha256:" + digest, "status": "open"}


def _input_error(inputs):
    size = _planned_input_size(inputs)
    if size > _MAX_BYTES or size * 4 > _MAX_BYTES:
        return _result(None, "unsupported", residuals=[_residual(
            "expanded-goal-bound", "Inequality probe exceeds the 8 MiB bound.", "goal-size")])
    return None


def _parse_pair(left_record, right_record, left_contract, right_contract, template):
    left_ast = parse_inequality_ast(left_record)
    right_ast = parse_inequality_ast(right_record)
    if left_ast is None or right_ast is None:
        return None, _result(template, "unsupported", residuals=[_residual(
            "unsupported-inequality-shape", "Only the exact Nat zero-bound pair is modeled.", "formula")])
    _pair, error = validate_inequality_pair(left_contract, right_contract, left_ast, right_ast)
    if error:
        return None, _result(template, "unsupported", residuals=[error])
    return (left_ast, right_ast), None


def _lower_pair(left_record, right_record, template):
    try:
        return (lower_formula(left_record["formula"], left_record["symbols"]),
                lower_formula(right_record["formula"], right_record["symbols"])), None
    except (TypeError, ValueError, KeyError, RecursionError) as error:
        return None, _result(template, "unsupported", residuals=[_residual(
            "unsupported-lowering", str(error)[:240], "formula")])


def _make_plan(readings, actual, template):
    left, right = readings
    premise, conclusion = ((left, right) if template["direction"] == "left-to-right"
                           else (right, left))
    if template["kind"] == "implication":
        probe = f"({premise}) → ({conclusion})"
    else:
        probe = f"({premise}) ∧ ¬({conclusion})"
    return _result(template, "planned", goals=[
        _goal("formal-reading", "formal-reading", f"({right}) ↔ ({actual})"),
        _goal("probe", "probe", probe),
    ])


def inequality_direction_result(left_record, right_record, left_contract, right_contract,
                                shared_slice, template):
    """Plan source-bound open obligations without assigning proof authority."""
    inputs = (left_record, right_record, left_contract, right_contract, shared_slice, template)
    bounded = _input_error(inputs)
    if bounded:
        return {**bounded, "template": template}
    _, unsupported = _parse_pair(
        left_record, right_record, left_contract, right_contract, template)
    if unsupported:
        return unsupported
    actual, error = _shared_type(shared_slice)
    if error:
        return _result(template, "unsupported", residuals=[error])
    readings, error = _lower_pair(left_record, right_record, template)
    if error:
        return error
    result = _make_plan(readings, actual, template)
    if _planned_input_size(result) > _MAX_BYTES:
        raise ValueError("expanded inequality-direction plan exceeds 8 MiB")
    return result
