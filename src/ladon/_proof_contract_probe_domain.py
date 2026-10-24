"""Bounded source-bound planning for restricted-domain-v2."""
from __future__ import annotations

import hashlib

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.correspondence_interpretation import lower_formula

from ._proof_contract_probe_domain_ast import parse_restricted_domain_ast
from ._proof_contract_probe_domain_contracts import validate_restricted_domain_pair
from ._proof_contract_probe_templates import _residual, _shared_type

_MAX_BYTES = 8 * 1024 * 1024
_SCOPE = "closed-nat-zero-restricted-domain-v2"


def _result(template, status, goals=None, residuals=None):
    return {"schema": "ladon-application-probe-plan-v1", "status": status,
            "template": template, "scope": _SCOPE, "goals": goals or [],
            "residuals": residuals or [], "checkerAuthority": "none",
            "wholeMethodAuthority": "none", "sourceFidelity": "attributed-unreviewed",
            "mathematicalFalsity": "not-established"}


def _goal(goal_id, kind, text):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {"goalId": goal_id, "kind": kind, "goal": text,
            "goalDigest": "sha256:" + digest, "status": "open"}


def _input_residual(inputs, template):
    size = _planned_input_size(inputs)
    if size > _MAX_BYTES:
        raise ValueError("restricted-domain inputs exceed the 8 MiB bound")
    if size * 4 > _MAX_BYTES:
        return _result(template, "unsupported", residuals=[_residual(
            "expanded-goal-bound", "Conservative lowered-goal size exceeds 8 MiB.", "goal-size")])
    return None


def _matched_pair(left_record, right_record, left_contract, right_contract, template):
    left_ast = parse_restricted_domain_ast(left_record)
    right_ast = parse_restricted_domain_ast(right_record)
    if left_ast is None or right_ast is None:
        return None, _result(template, "unsupported", residuals=[_residual(
            "unsupported-restricted-domain", "ASTs are outside the exact Nat zero-guard profile.", "formula")])
    _pair, residual = validate_restricted_domain_pair(
        left_contract, right_contract, left_ast, right_ast)
    if residual:
        return None, _result(template, "unsupported", residuals=[residual])
    return (left_ast, right_ast), None


def _lower_readings(left_record, right_record, template):
    try:
        return (lower_formula(left_record["formula"], left_record["symbols"]),
                lower_formula(right_record["formula"], right_record["symbols"])), None
    except (TypeError, ValueError, KeyError, RecursionError) as error:
        return None, _result(template, "unsupported", residuals=[_residual(
            "unsupported-lowering", str(error)[:240], "formula")])


def _planned_goals(left, right, actual, template):
    p, q = (left, right) if template["direction"] == "left-to-right" else (right, left)
    probe = f"({p}) → ({q})" if template["kind"] == "implication" else f"({p}) ∧ ¬({q})"
    return _result(template, "planned", [
        _goal("formal-reading", "formal-reading", f"({right}) ↔ ({actual})"),
        _goal("probe", "probe", probe),
    ])


def restricted_domain_result(left_record, right_record, left_contract, right_contract,
                             shared_slice, template):
    inputs = (left_record, right_record, left_contract, right_contract, shared_slice, template)
    residual = _input_residual(inputs, template)
    if residual:
        return residual
    _pair, unsupported = _matched_pair(
        left_record, right_record, left_contract, right_contract, template)
    if unsupported:
        return unsupported
    actual, residual = _shared_type(shared_slice)
    if residual:
        return _result(template, "unsupported", residuals=[residual])
    readings, unsupported = _lower_readings(left_record, right_record, template)
    if unsupported:
        return unsupported
    result = _planned_goals(*readings, actual, template)
    if _planned_input_size(result) > _MAX_BYTES:
        raise ValueError("expanded restricted-domain plan exceeds 8 MiB")
    return result
