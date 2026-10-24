"""Pure, bounded template matching for source-bound application probes.

This scratch module intentionally does not check proofs or establish source fidelity.
"""
from __future__ import annotations

import hashlib
from typing import Any

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.correspondence_interpretation import lower_formula

FAMILIES = (
    "regularity-boundary",
    "constant-uniformity",
    "witness-dependence",
    "restricted-domain",
    "inequality-direction",
)
_SCOPE = "closed-nat-regularity-v1"
_MAX_INPUT = 8 * 1024 * 1024
_EXPECTED = {
    "profileId": "norm-scale-v1",
}


def validate_template(template: Any) -> dict[str, str]:
    if not isinstance(template, dict) or set(template) != {"familyId", "version", "direction", "kind"}:
        raise ValueError("template selectors must be a closed object")
    family = template["familyId"]
    if not all(isinstance(template[key], str) for key in template):
        raise ValueError("template selectors must be strings")
    if family not in FAMILIES or template["version"] != f"{family}-v1":
        raise ValueError("unknown template family or version")
    if template["direction"] not in {"left-to-right", "right-to-left"}:
        raise ValueError("invalid template direction")
    if template["kind"] not in {"implication", "counterexample"}:
        raise ValueError("invalid template kind")
    return {key: template[key] for key in ("familyId", "version", "direction", "kind")}


def application_probe_profile() -> dict[str, dict[str, Any]]:
    return {family: {"version": f"{family}-v1", "implemented": family == FAMILIES[0]}
            for family in FAMILIES}


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _is_node(value, tag, keys):
    return isinstance(value, dict) and set(value) == keys and value.get("tag") == tag


def _is_var(value, identity):
    return _is_node(value, "var", {"tag", "id"}) and value.get("id") == identity


def _is_const(value, name):
    return _is_node(value, "const", {"tag", "name"}) and value.get("name") == name


def _formula_parts(formula, s_id, x_id):
    if not _is_node(formula, "forall", {"tag", "binder", "body"}):
        return None
    if formula["binder"].get("id") != s_id or formula["binder"].get("domain") != "Nat":
        return None
    second = formula["body"]
    if not _is_node(second, "forall", {"tag", "binder", "body"}):
        return None
    if second["binder"].get("id") != x_id or second["binder"].get("domain") != "Nat":
        return None
    body = second["body"]
    if not _is_node(body, "le", {"tag", "left", "right"}):
        return None
    return body["left"], body["right"]


def _left_symbols(left, s_id, x_id):
    if not _is_node(left, "app", {"tag", "symbol", "args"}) or len(left["args"]) != 2:
        return None
    fun = left["args"][1]
    if not _is_var(left["args"][0], s_id) or not _is_node(fun, "app", {"tag", "symbol", "args"}):
        return None
    if len(fun["args"]) != 1 or not _is_var(fun["args"][0], x_id):
        return None
    return left["symbol"], fun["symbol"]


def _right_n_args(constant, n_app, x_id):
    if not (_is_node(constant, "const", {"tag", "name"})
            and _is_node(n_app, "app", {"tag", "symbol", "args"})):
        return None
    if not (len(n_app["args"]) == 2 and _is_var(n_app["args"][1], x_id)):
        return None
    add_app = n_app["args"][0]
    return _right_add_args(constant, n_app, add_app, x_id)


def _right_add_args(constant, n_app, add_app, x_id):
    if not (_is_node(add_app, "app", {"tag", "symbol", "args"}) and len(add_app["args"]) == 2):
        return None
    return constant, n_app, add_app


def _right_symbols(right, offset, s_id, x_id):
    if not (_is_node(right, "app", {"tag", "symbol", "args"}) and len(right["args"]) == 2):
        return None
    constant, n_app = right["args"]
    parsed = _right_n_args(constant, n_app, x_id)
    if parsed is None:
        return None
    constant, n_app, add_app = parsed
    if not (_is_var(add_app["args"][0], s_id) and _is_const(add_app["args"][1], str(offset))):
        return None
    return constant["name"], right["symbol"], n_app["symbol"], add_app["symbol"]


def _typed_rows(symbols, names):
    if any(name not in symbols for name in names):
        return None
    return [symbols[name] for name in names]


def _typed_roles(symbols, left_roles, right_roles):
    if left_roles is None or right_roles is None:
        return False
    constant, mul_id, n_id, add_id = right_roles
    names = (*left_roles, n_id, mul_id, add_id, constant)
    if len(set(names)) != 6:
        return False
    rows = _typed_rows(symbols, names)
    if rows is None:
        return False
    signatures = ["Nat → Nat → Nat", "Nat → Nat", "Nat → Nat → Nat",
                  "Nat → Nat → Nat", "Nat → Nat → Nat"]
    types_match = all(row.get("leanType") == sig for row, sig in zip(rows[:-1], signatures))
    arithmetic_match = rows[3].get("leanName") == "Nat.mul" and rows[4].get("leanName") == "Nat.add"
    return types_match and arithmetic_match and rows[-1].get("leanType") == "Nat"


def _formula_shape(formula, symbols, offset, s_id, x_id):
    parts = _formula_parts(formula, s_id, x_id)
    return parts is not None and _typed_roles(
        symbols, _left_symbols(parts[0], s_id, x_id), _right_symbols(parts[1], offset, s_id, x_id))


def _contract_features(contract):
    features = contract.get("features", {})
    regularity = features.get("regularity", {})
    if set(features) != {"regularity", "constantDependencies", "witnessDependencies"}:
        return None
    if regularity.get("state") != "known" or type(regularity.get("offset")) is not int or regularity["offset"] < 0:
        return None
    if regularity.get("reason") is not None:
        return None
    constants = features.get("constantDependencies", {})
    if constants.get("state") != "known" or constants.get("allowedBinderIds") != []:
        return None
    if constants.get("reason") is not None or features.get("witnessDependencies") != []:
        return None
    return regularity["offset"]


def _contract_offset(contract):
    if not isinstance(contract, dict) or any(contract.get(k) != v for k, v in _EXPECTED.items()):
        return None
    if contract.get("assumptions") != []:
        return None
    return _contract_features(contract)


def _telescope_rows(telescope):
    if not isinstance(telescope, list) or len(telescope) != 2:
        return None
    if any(not isinstance(row, dict) for row in telescope):
        return None
    if any(row.get("typeId") != "Nat" or row.get("quantifier") != "forall" for row in telescope):
        return None
    return telescope


def _valid_telescope(contract):
    telescope = _telescope_rows(contract.get("telescope"))
    if telescope is None:
        return None
    binder_ids = [row.get("binderId") for row in telescope]
    if any(not isinstance(identity, str) or not identity for identity in binder_ids):
        return None
    return binder_ids if binder_ids[0] != binder_ids[1] else None


def _bounded_symbols(symbols):
    return isinstance(symbols, dict) and all(
        isinstance(row, dict) and isinstance(row.get("leanName"), str)
        and row["leanName"] and len(row["leanName"]) <= 200 for row in symbols.values())


def _formula_binders(formula):
    return [node.get("binder", {}) for node in _walk(formula) if node.get("tag") in {"forall", "exists"}]


def _record_matches(record, contract, offset):
    if not isinstance(record, dict):
        return False
    formula = record.get("formula")
    symbols = record.get("symbols")
    if not isinstance(formula, dict) or not _bounded_symbols(symbols):
        return False
    binder_ids = _valid_telescope(contract)
    if binder_ids is None:
        return False
    binders = _formula_binders(formula)
    return (len(binders) == 2 and all(b.get("domain") == "Nat" for b in binders)
            and [b.get("id") for b in binders] == binder_ids
            and _formula_shape(formula, symbols, offset, *binder_ids))


def _summary_offset_mismatch(record, contract):
    offset = _contract_offset(contract)
    if offset is None or not isinstance(record, dict):
        return False
    formula, symbols = record.get("formula"), record.get("symbols")
    binder_ids = _valid_telescope(contract)
    if not isinstance(formula, dict) or not _bounded_symbols(symbols) or binder_ids is None:
        return False
    try:
        literal = formula["body"]["body"]["right"]["args"][1]["args"][0]["args"][1]
        actual_offset = int(literal.get("name"))
    except (KeyError, IndexError, TypeError, ValueError):
        return False
    return (type(literal.get("name")) is str and literal.get("name") == str(actual_offset)
            and actual_offset != offset and _formula_shape(formula, symbols, actual_offset, *binder_ids))


def _regularity_shape(record, contract):
    offset = _contract_offset(contract)
    return offset is not None and _record_matches(record, contract, offset)


def _normalize_offset(formula: dict[str, Any], offset: int) -> dict[str, Any]:
    body = formula["body"]["body"]
    n_application = body["right"]["args"][1]
    add_application = n_application["args"][0]
    literal = add_application["args"][1]
    if literal.get("tag") != "const" or literal.get("name") != str(offset):
        raise ValueError("regularity offset does not match the designated AST literal")
    return {**formula, "body": {**formula["body"], "body": {
        **body, "right": {**body["right"], "args": [body["right"]["args"][0], {
            **n_application, "args": [{**add_application, "args": [
                add_application["args"][0], {**literal, "name": "0"}]}, n_application["args"][1]]}]}}}}


def _residual(code: str, message: str, feature: str) -> dict[str, str]:
    return {"code": code, "message": message, "feature": feature}


def _result(template: dict[str, str], status: str, goals=None, residuals=None):
    return {"schema": "ladon-application-probe-plan-v1", "status": status,
            "template": template, "scope": _SCOPE, "goals": goals or [],
            "residuals": residuals or [], "checkerAuthority": "none",
            "wholeMethodAuthority": "none", "sourceFidelity": "attributed-unreviewed",
            "mathematicalFalsity": "not-established"}


def _goal(goal_id: str, kind: str, goal: str) -> dict[str, str]:
    return {"goalId": goal_id, "kind": kind, "goal": goal,
            "goalDigest": "sha256:" + hashlib.sha256(goal.encode("utf-8")).hexdigest(), "status": "open"}


def _pair_inputs(left_record, right_record, left_contract, right_contract):
    if (_summary_offset_mismatch(left_record, left_contract)
            or _summary_offset_mismatch(right_record, right_contract)):
        raise ValueError("regularity AST literal disagrees with its contract feature offset")
    if not _regularity_shape(left_record, left_contract) or not _regularity_shape(right_record, right_contract):
        return _residual("unsupported-regularity-shape", "Interpretations or contract features exceed the closed profile.", "regularity"), None
    left = left_record["formula"]
    right = right_record["formula"]
    left_offset = left_contract["features"]["regularity"]["offset"]
    right_offset = right_contract["features"]["regularity"]["offset"]
    if _normalize_offset(left, left_offset) != _normalize_offset(right, right_offset):
        return _residual("regularity-feature-mismatch", "Formula structures differ beyond the declared offset.", "regularity"), None
    expected = {**right_contract, "features": {**right_contract["features"], "regularity": {
        **right_contract["features"]["regularity"], "offset": left_offset}}}
    if left_contract != expected:
        return _residual("contract-feature-mismatch", "Contract fields differ beyond the regularity offset.", "contract"), None
    return None, (left, right, left_offset, right_offset)


def _valid_closed_slice(shared_slice):
    if (not isinstance(shared_slice, dict) or shared_slice.get("localContext") != []
            or shared_slice.get("complete") is not True or shared_slice.get("status") != "extracted"):
        return False
    nodes = shared_slice.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 1:
        return False
    row = nodes[0]
    return isinstance(row, dict) and row.get("kind") == "application" and row.get("premises") == []


def _shared_type(shared_slice):
    if not _valid_closed_slice(shared_slice):
        return None, _residual("nonclosed-shared-context", "The selected application context is not closed, complete, and premise-free.", "shared-context")
    row = shared_slice["nodes"][0]
    actual = row.get("closedType")
    if not isinstance(actual, str) or not actual or len(actual) > _MAX_INPUT:
        return None, _residual("missing-closed-type", "The selected application has no bounded closed type.", "shared-slice")
    return actual, None


def _lower_readings(left_record, right_record, formulas, offsets):
    left_formula, right_formula = formulas
    left_offset, right_offset = offsets
    try:
        left = lower_formula(left_formula, left_record["symbols"])
        right = lower_formula(right_formula, right_record["symbols"])
        normalized_left = lower_formula(_normalize_offset(left_formula, left_offset), left_record["symbols"])
        normalized_right = lower_formula(_normalize_offset(right_formula, right_offset), right_record["symbols"])
    except (TypeError, ValueError, KeyError, RecursionError) as error:
        return None, _residual("unsupported-lowering", str(error)[:240], "formula")
    if normalized_left != normalized_right or any(op not in left + right for op in ("Nat.add", "Nat.mul")):
        return None, _residual("unsupported-lowered-formula", "Lowered readings do not match the typed regularity shape.", "formula")
    return (left, right), None


def template_result(left_record, right_record, left_contract, right_contract, shared_slice, template):
    """Match one closed regularity template and produce two open Lean goals."""
    selected = validate_template(template)
    inputs = (left_record, right_record, left_contract, right_contract, shared_slice)
    input_size = _planned_input_size(inputs)
    if input_size > _MAX_INPUT:
        raise ValueError("template inputs exceed the 8 MiB bound")
    if input_size * 4 > _MAX_INPUT:
        return _result(selected, "unsupported", residuals=[_residual(
            "expanded-goal-bound", "The conservative lowered-goal size bound exceeds 8 MiB.", "goal-size")])
    if selected["familyId"] != FAMILIES[0]:
        return _result(selected, "unsupported", residuals=[_residual(
            "unsupported-template-family", "This registered family has no implemented matcher.", selected["familyId"])])
    error, pair = _pair_inputs(left_record, right_record, left_contract, right_contract)
    if error:
        return _result(selected, "unsupported", residuals=[error])
    formulas, offsets = pair[:2], pair[2:]
    actual, error = _shared_type(shared_slice)
    if error:
        return _result(selected, "unsupported", residuals=[error])
    readings, error = _lower_readings(left_record, right_record, formulas, offsets)
    if error:
        return _result(selected, "unsupported", residuals=[error])
    left, right = readings
    p, q = (left, right) if selected["direction"] == "left-to-right" else (right, left)
    reading = f"({right}) ↔ ({actual})"
    probe = f"({p}) → ({q})" if selected["kind"] == "implication" else f"({p}) ∧ ¬({q})"
    result = _result(selected, "planned", [_goal("formal-reading", "formal-reading", reading),
                                            _goal("probe", "probe", probe)])
    if _planned_input_size(result) > _MAX_INPUT:
        raise ValueError("expanded probe plan exceeds the 8 MiB output bound")
    return result
