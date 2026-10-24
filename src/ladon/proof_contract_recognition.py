"""Bounded formal contract recognition helpers."""

from __future__ import annotations

from typing import Any

from ladon.proof_contract_expressions import (
    _app_argument_path,
    _app_parts,
    _binder_type,
    _bound_binder,
    _const_name,
    _expr_head_name,
    _find_const_path,
    _is_builtin_nat_operation,
    _is_builtin_nat_relation,
    _same_bound_term,
    _scale_offset,
    _strip_metadata,
    _type_head,
    _type_id,
    _Unsupported,
)
from ladon.proof_contract_worker import PROFILE


def _recognize_estimate(expression: dict[str, Any]) -> dict[str, Any]:
    binders: list[dict[str, Any]] = []
    scope: list[dict[str, Any]] = []
    conclusion, scope, conclusion_path = _peel(expression, binders, scope)
    _validate_initial_telescope(binders)
    relation_path = _find_const_path(conclusion, "LE.le", conclusion_path)
    if relation_path is None:
        raise _Unsupported(
            "unsupported-expression", "statement is not a recognized Nat inequality", "conclusion"
        )
    relation_fn, relation_args = _app_parts(conclusion)
    if _const_name(relation_fn) != "LE.le" or len(relation_args) < 4:
        raise _Unsupported(
            "unsupported-expression", "inequality has an unsupported elaborated form", "conclusion"
        )
    if not _is_builtin_nat_relation(relation_args[:-2]):
        raise _Unsupported(
            "unsupported-carrier-or-instance",
            "inequality carrier or order instance is not Lean's builtin Nat order",
            "conclusion.order",
        )
    left, right = relation_args[-2:]
    left_result = _recognize_left_estimate(left, binders, scope)
    right_result = _recognize_right_estimate(
        right, binders, scope, left_result["scaleBinder"], left_result["inputBinder"],
        _app_argument_path(conclusion, len(relation_args) - 1, conclusion_path)
    )
    _validate_estimate_telescope(
        binders,
        left_result["scaleBinder"],
        left_result["inputBinder"],
        right_result["constantAnchor"],
    )
    return {
        "binders": binders,
        "scope": scope,
        **left_result,
        **right_result,
        "conclusionPath": relation_path or conclusion_path,
    }

def _validate_initial_telescope(binders):
    if len(binders) > 8:
        raise _Unsupported(
            "telescope-limit", "statement telescope exceeds the supported bound", "telescope"
        )
    for row in binders:
        domain_head = _expr_head_name(row["type"])
        if domain_head not in {"Nat"}:
            detail = (
                "membership restricted" if domain_head == "Subtype" else "dependent or unsupported"
            )
            raise _Unsupported(
                "unsupported-domain",
                f"{detail} binder domain is outside the admitted Nat profile",
                f"telescope.{row['binderId']}.type",
            )

def _recognize_left_estimate(left, binders, scope):
    left_operator, map_name, scale_term, input_term = _left_estimate_parts(left)
    scale_binder, input_binder = _validate_left_binders(scale_term, input_term, binders, scope)
    return {
        "leftOperator": left_operator,
        "map": map_name,
        "scaleBinder": scale_binder,
        "inputBinder": input_binder,
    }

def _left_estimate_parts(left):
    left_head, left_args = _app_parts(left)
    if _const_name(left_head) is None or len(left_args) != 2:
        raise _Unsupported(
            "unsupported-expression",
            "left estimate operator application is unrecognized",
            "conclusion.left",
        )
    _scale_term, mapped = left_args
    map_head, map_args = _app_parts(mapped)
    if _const_name(map_head) is None or len(map_args) != 1:
        raise _Unsupported(
            "unsupported-expression", "mapped input is not one unary application", "conclusion.left"
        )
    map_name = _const_name(map_head)
    return _const_name(left_head), map_name, left_args[0], map_args[0]

def _validate_left_binders(scale_term, input_term, binders, scope):
    scale_binder = _bound_binder(scale_term, scope)
    input_binder = _bound_binder(input_term, scope)
    if scale_binder is None or input_binder is None or scale_binder == input_binder:
        raise _Unsupported(
            "unsupported-expression",
            "estimate needs distinct bound scale and input variables",
            "telescope",
        )
    if (
        _type_head(_binder_type(binders, scale_binder)) != "Nat"
        or _type_head(_binder_type(binders, input_binder)) != "Nat"
    ):
        raise _Unsupported(
            "unsupported-domain", "estimate scale and input domains must be Nat", "telescope.domain"
        )
    if not _same_bound_term(scale_term, scale_binder, scope) or not _same_bound_term(
        input_term, input_binder, scope
    ):
        raise _Unsupported(
            "unsupported-expression",
            "operator indices must use the direct scale and input binders",
            "conclusion.left",
        )
    return scale_binder, input_binder

def _recognize_right_estimate(right, binders, scope, scale_binder, input_binder, right_path):
    product_fn, product_args = _app_parts(right)
    if _const_name(product_fn) != "HMul.hMul" or len(product_args) < 6:
        raise _Unsupported(
            "unsupported-expression",
            "right estimate must multiply a constant by an indexed input scale",
            "conclusion.right",
        )
    if not _is_builtin_nat_operation(product_args[:-2], "instHMul", "instMulNat"):
        raise _Unsupported(
            "unsupported-carrier-or-instance",
            "estimate multiplication is not Lean's builtin Nat multiplication",
            "conclusion.right.multiply",
        )
    constant_term, indexed_scale = product_args[-2:]
    input_head, input_args = _app_parts(indexed_scale)
    if _const_name(input_head) is None or len(input_args) != 2:
        raise _Unsupported(
            "unsupported-expression",
            "right estimate scale application is unrecognized",
            "conclusion.right",
        )
    input_scale_name = _const_name(input_head)
    shifted_scale, right_input = input_args
    if not _same_bound_term(right_input, input_binder, scope):
        raise _Unsupported(
            "unsupported-expression",
            "input scale must use the same input binder",
            "conclusion.right",
        )
    offset = _scale_offset(shifted_scale, scale_binder, scope)

    constant_anchor, constant_name, existentials = _recognize_constant(
        constant_term, binders, scope
    )
    return {
        "regularityOriginPath": _app_argument_path(right, len(product_args) - 1, right_path),
        "constantOriginPath": _app_argument_path(right, len(product_args) - 2, right_path),
        "inputScale": input_scale_name,
        "offset": offset,
        "constantAnchor": constant_anchor,
        "constantName": constant_name,
        "existentials": existentials,
    }

def _recognize_constant(constant_term, binders, scope):
    existentials = [row for row in binders if row["quantifier"] == "exists"]
    _validate_existential_count(existentials)
    constant_binder = _bound_binder(constant_term, scope)
    if constant_binder is not None:
        _validate_constant_binder(constant_binder, binders, existentials)
        return constant_binder, None, existentials
    constant_name = _global_coefficient_name(constant_term, existentials)
    return None, constant_name, existentials

def _validate_existential_count(existentials):
    if len(existentials) > 1:
        raise _Unsupported(
            "unsupported-quantifier",
            "only one existential estimate constant is supported",
            "telescope",
        )

def _validate_constant_binder(constant_binder, binders, existentials):
    row = next((item for item in binders if item["binderId"] == constant_binder), None)
    if row is None or row["quantifier"] != "exists":
        raise _Unsupported(
            "unsupported-constant",
            "an explicit estimate constant must be existentially quantified",
            "features.constantDependencies",
        )
    if len(existentials) != 1 or existentials[0]["binderId"] != constant_binder:
        raise _Unsupported(
            "unsupported-quantifier",
            "existential binders must identify the estimate constant",
            "telescope",
        )

def _global_coefficient_name(constant_term, existentials):
    constant_fn, constant_args = _app_parts(constant_term)
    if constant_args or _const_name(constant_fn) is None:
        raise _Unsupported(
            "unsupported-constant",
            "estimate coefficient must be one observed constant or existential",
            "features.constantDependencies",
        )
    if existentials:
        raise _Unsupported(
            "unsupported-constant",
            "existential binder does not supply the estimate coefficient",
            "features.constantDependencies",
        )
    return _const_name(constant_fn)

def _validate_estimate_telescope(binders, scale_binder, input_binder, constant_anchor):
    supported_ids = {scale_binder, input_binder}
    if constant_anchor is not None:
        supported_ids.add(constant_anchor)
    _reject_extra_binders(binders, supported_ids)
    _validate_estimate_binder_types(binders, scale_binder, input_binder)

def _reject_extra_binders(binders, supported_ids):
    if {row["binderId"] for row in binders} == supported_ids:
        return
    unsupported = next(row for row in binders if row["binderId"] not in supported_ids)
    if _type_head(unsupported["type"]) != "Nat":
        raise _Unsupported(
            "unsupported-domain",
            "dependent or restricted binder domain is outside the admitted profile",
            f"telescope.{unsupported['binderId']}.type",
        )
    raise _Unsupported(
        "unsupported-quantifier",
        "extra statement binders are outside the admitted profile",
        f"telescope.{unsupported['binderId']}",
    )

def _validate_estimate_binder_types(binders, scale_binder, input_binder):
    domain_type = _binder_type(binders, input_binder)
    scale_type = _binder_type(binders, scale_binder)
    if _type_head(domain_type) != "Nat" or _type_head(scale_type) != "Nat":
        raise _Unsupported(
            "unsupported-domain",
            "only Nat-indexed scales and inputs are supported",
            "telescope.domain",
        )
    for row in binders:
        if row["quantifier"] == "exists" and _type_head(row["type"]) != "Nat":
            raise _Unsupported(
                "unsupported-domain",
                "existential estimate constant must have type Nat",
                f"telescope.{row['binderId']}.type",
            )

def _peel(expression, binders, scope, path="/normalizedTypeExpr"):
    expression = _strip_metadata(expression)
    if "letE" in expression:
        let = expression["letE"]
        let_scope = [*scope, {"kind": "let", "value": let["value"], "scope": list(scope)}]
        return _peel(let["body"], binders, let_scope, path + "/letE/body")
    if "forallE" in expression:
        row = expression["forallE"]
        binder_id = f"b{len(binders)}"
        binder = {
            "binderId": binder_id,
            "type": row["type"],
            "quantifier": "forall",
            "originPath": path,
        }
        binders.append(binder)
        scope.append({"kind": "binder", "binderId": binder_id})
        return _peel(row["body"], binders, scope, path + "/forallE/body")
    fn, args = _app_parts(expression)
    if _const_name(fn) == "Exists" and args and "lam" in args[-1]:
        predicate = args[-1]["lam"]
        binder_id = f"b{len(binders)}"
        binders.append(
            {
                "binderId": binder_id,
                "type": predicate["type"],
                "quantifier": "exists",
                "originPath": path,
            }
        )
        scope.append({"kind": "binder", "binderId": binder_id})
        predicate_path = _app_argument_path(expression, len(args) - 1, path)
        return _peel(predicate["body"], binders, scope, predicate_path + "/lam/body")
    return expression, scope, path

def _contract_record(summary):
    binders = summary["binders"]
    scale_id, input_id, endpoint = _contract_ids(summary)
    constant = _constant_feature(summary, binders)
    witnesses = _witness_features(summary["existentials"], binders)
    return {
        "profileId": PROFILE,
        "endpointId": endpoint,
        "context": {
            "objectId": f"operator:{summary['map']}",
            "domainId": input_id,
            "scaleId": scale_id,
            "representationId": "representation:original",
        },
        "telescope": [
            {
                "binderId": row["binderId"],
                "typeId": _type_id(row["type"]),
                "quantifier": row["quantifier"],
            }
            for row in binders
        ],
        "assumptions": [],
        "conclusionId": endpoint + ":conclusion",
        "features": {
            "regularity": {
                "state": "known",
                "scaleId": scale_id,
                "offset": summary["offset"],
                "reason": None,
            },
            "constantDependencies": constant,
            "witnessDependencies": witnesses,
        },
    }

def _contract_ids(summary):
    binders = summary["binders"]
    scale_id = f"scale:{summary['inputScale']}"
    input_id = f"domain:{_type_id(_binder_type(binders, summary['inputBinder']))}"
    endpoint = f"estimate:{summary['leftOperator']}:{summary['inputScale']}:{summary['map']}"
    return scale_id, input_id, endpoint

def _constant_feature(summary, binders):
    anchor = summary["constantAnchor"]
    allowed = _prior_universals(binders, anchor) if anchor is not None else []
    result = {"state": "known", "allowedBinderIds": allowed, "reason": None}
    if anchor is not None:
        result["binderId"] = anchor
    return result

def _prior_universals(binders, anchor):
    positions = {row["binderId"]: index for index, row in enumerate(binders)}
    anchor_position = positions[anchor]
    return [
        row["binderId"]
        for row in binders
        if row["quantifier"] == "forall" and positions[row["binderId"]] < anchor_position
    ]

def _witness_features(existentials, binders):
    positions = {row["binderId"]: index for index, row in enumerate(binders)}
    return [_witness_feature(row, binders, positions) for row in existentials]

def _witness_feature(existential, binders, positions):
    position = positions[existential["binderId"]]
    allowed = [
        row["binderId"]
        for row in binders
        if row["quantifier"] == "forall" and positions[row["binderId"]] < position
    ]
    return {
        "binderId": existential["binderId"],
        "state": "known",
        "allowedBinderIds": allowed,
        "reason": None,
    }
