"""Pure, bounded template matching for source-bound application probes.

Templates plan obligations; separate actual checkers establish local support.
"""
from __future__ import annotations

import hashlib
from typing import Any

from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.correspondence_interpretation import lower_formula

from ._proof_contract_probe_regularity_ast import _normalize_offset
from ._proof_contract_probe_regularity_match import _regularity_shape, _summary_offset_mismatch

FAMILIES = (
    "regularity-boundary",
    "constant-uniformity",
    "witness-dependence",
    "restricted-domain",
    "inequality-direction",
)
_SCOPE = "closed-nat-regularity-v1"
_MAX_INPUT = 8 * 1024 * 1024


def _template_versions(family):
    versions = {f"{family}-v1"}
    if family == "constant-uniformity":
        versions.add("constant-uniformity-v2")
    if family == "witness-dependence":
        versions.add("witness-dependence-v2")
    if family == "restricted-domain":
        versions.add("restricted-domain-v2")
    if family == "inequality-direction":
        versions.add("inequality-direction-v2")
    return versions


def validate_template(template: Any) -> dict[str, str]:
    if not isinstance(template, dict) or set(template) != {"familyId", "version", "direction", "kind"}:
        raise ValueError("template selectors must be a closed object")
    family = template["familyId"]
    if not all(isinstance(template[key], str) for key in template):
        raise ValueError("template selectors must be strings")
    if family not in FAMILIES or template["version"] not in _template_versions(family):
        raise ValueError("unknown template family or version")
    if template["direction"] not in {"left-to-right", "right-to-left"}:
        raise ValueError("invalid template direction")
    if template["kind"] not in {"implication", "counterexample"}:
        raise ValueError("invalid template kind")
    return {key: template[key] for key in ("familyId", "version", "direction", "kind")}


def application_probe_profile() -> dict[str, dict[str, Any]]:
    result = {family: {"version": f"{family}-v1", "implemented": family == FAMILIES[0]}
              for family in FAMILIES}
    result["constant-uniformity"] = {"version": "constant-uniformity-v2", "implemented": True}
    result["witness-dependence"] = {"version": "witness-dependence-v2", "implemented": True}
    result["restricted-domain"] = {"version": "restricted-domain-v2", "implemented": True}
    result["inequality-direction"] = {"version": "inequality-direction-v2", "implemented": True}
    return result


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
    """Dispatch versioned templates without reinterpreting historical plans."""
    selected = validate_template(template)
    if selected["version"] == "constant-uniformity-v2":
        from ._proof_contract_probe_uniformity import constant_uniformity_result

        return constant_uniformity_result(left_record, right_record, left_contract,
                                          right_contract, shared_slice, selected)
    if selected["version"] == "witness-dependence-v2":
        from ._proof_contract_probe_witness import witness_dependence_result

        return witness_dependence_result(left_record, right_record, left_contract,
                                         right_contract, shared_slice, selected)
    if selected["version"] == "restricted-domain-v2":
        from ._proof_contract_probe_domain import restricted_domain_result

        return restricted_domain_result(left_record, right_record, left_contract,
                                        right_contract, shared_slice, selected)
    if selected["version"] == "inequality-direction-v2":
        from ._proof_contract_probe_inequality import inequality_direction_result

        return inequality_direction_result(left_record, right_record, left_contract,
                                           right_contract, shared_slice, selected)
    return _legacy_template_result(left_record, right_record, left_contract,
                                   right_contract, shared_slice, selected)


def _legacy_template_result(left_record, right_record, left_contract, right_contract, shared_slice, template):
    """Preserve the original v1 result, including unsupported family plans."""
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
