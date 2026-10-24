"""Bounded source-bound obligations for witness-dependence-v2."""
from __future__ import annotations

import hashlib

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.correspondence_interpretation import lower_formula

from ._proof_contract_probe_templates import _residual, _shared_type
from ._proof_contract_probe_witness_ast import parse_witness_ast
from ._proof_contract_probe_witness_contracts import validate_witness_pair

_MAX_BYTES = 8 * 1024 * 1024
_SCOPE = "closed-nat-witness-dependence-v2"


def _result_v2(template, status, goals=None, residuals=None):
    return {
        "schema": "ladon-application-probe-plan-v1",
        "status": status,
        "template": template,
        "scope": _SCOPE,
        "goals": goals or [],
        "residuals": residuals or [],
        "checkerAuthority": "none",
        "wholeMethodAuthority": "none",
        "sourceFidelity": "attributed-unreviewed",
        "mathematicalFalsity": "not-established",
    }


def _goal_v2(goal_id, kind, formula):
    digest = hashlib.sha256(formula.encode("utf-8")).hexdigest()
    return {
        "goalId": goal_id,
        "kind": kind,
        "goal": formula,
        "goalDigest": "sha256:" + digest,
        "status": "open",
    }


def _unsupported(template, message, feature):
    return _result_v2(template, "unsupported", residuals=[
        _residual("unsupported-witness-dependence", message, feature)
    ])


def _within_input_bounds(inputs, template):
    size = _planned_input_size(inputs)
    if size > _MAX_BYTES:
        raise ValueError("witness-dependence inputs exceed the 8 MiB bound")
    if size * 4 > _MAX_BYTES:
        return _result_v2(template, "unsupported", residuals=[_residual(
            "expanded-goal-bound", "Conservative lowered-goal size exceeds 8 MiB.", "goal-size")])
    return None


def _matched_pair(left_record, right_record, left_contract, right_contract, template):
    left_ast = parse_witness_ast(left_record)
    right_ast = parse_witness_ast(right_record)
    if left_ast is None or right_ast is None:
        return None, _unsupported(template,
            "The ASTs do not match the exact two-binder Nat P(w,x) profile.", "formula")
    _pair, error = validate_witness_pair(
        left_contract, right_contract, left_ast, right_ast
    )
    if error:
        return None, _result_v2(template, "unsupported", residuals=[error])
    return (left_ast, right_ast), None


def _lower_pair(left_record, right_record, template):
    try:
        return (lower_formula(left_record["formula"], left_record["symbols"]),
                lower_formula(right_record["formula"], right_record["symbols"])), None
    except (TypeError, ValueError, KeyError, RecursionError) as cause:
        return None, _unsupported(template, str(cause)[:240], "formula")


def _planned_goals(formulas, actual, template):
    left, right = formulas
    p, q = (left, right) if template["direction"] == "left-to-right" else (right, left)
    formal = f"({right}) ↔ ({actual})"
    if template["kind"] == "implication":
        probe = f"({p}) → ({q})"
    else:
        probe = f"({p}) ∧ ¬({q})"
    result = _result_v2(template, "planned", goals=[
        _goal_v2("formal-reading", "formal-reading", formal),
        _goal_v2("probe", "probe", probe),
    ])
    if _planned_input_size(result) > _MAX_BYTES:
        raise ValueError("expanded witness-dependence plan exceeds 8 MiB")
    return result


def witness_dependence_result(
    left_record, right_record, left_contract, right_contract, shared_slice, template
):
    """Plan original-order formal-reading and directional witness obligations."""
    inputs = (left_record, right_record, left_contract, right_contract, shared_slice, template)
    bounded = _within_input_bounds(inputs, template)
    if bounded:
        return bounded
    _parsed, mismatch = _matched_pair(
        left_record, right_record, left_contract, right_contract, template
    )
    if mismatch:
        return mismatch
    actual, error = _shared_type(shared_slice)
    if error:
        return _result_v2(template, "unsupported", residuals=[error])
    formulas, mismatch = _lower_pair(left_record, right_record, template)
    if mismatch:
        return mismatch
    return _planned_goals(formulas, actual, template)
