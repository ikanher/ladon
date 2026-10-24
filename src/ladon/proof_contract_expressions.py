"""Bounded formal contract expressions helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ladon.proof_contract_worker import MAX_EXPR_NODES


class _Unsupported(Exception):
    def __init__(self, code: str, message: str, feature: str) -> None:
        super().__init__(message)
        self.code = code
        self.feature = feature

def _scale_offset(expression, scale_binder, scope):
    resolved, resolved_scope = _resolve_let(expression, scope)
    binder = _bound_binder(resolved, resolved_scope)
    if binder == scale_binder and _same_bound_term(resolved, scale_binder, resolved_scope):
        return 0
    head, args = _app_parts(resolved)
    if _const_name(head) != "HAdd.hAdd" or len(args) < 6:
        raise _Unsupported(
            "unsupported-scale",
            "input scale must be the same index or that index plus an explicit Nat offset",
            "features.regularity",
        )
    if not _is_builtin_nat_operation(args[:-2], "instHAdd", "instAddNat"):
        raise _Unsupported(
            "unsupported-carrier-or-instance",
            "scale addition is not Lean's builtin Nat addition",
            "features.regularity",
        )
    left, right = args[-2:]
    if not _same_bound_term(left, scale_binder, resolved_scope):
        raise _Unsupported(
            "unsupported-scale",
            "offset must be added to the same universally quantified scale",
            "features.regularity",
        )
    right_resolved, _right_scope = _resolve_let(right, resolved_scope)
    offset = _nat_literal(right_resolved)
    if offset is None:
        raise _Unsupported(
            "unsupported-scale",
            "scale offset must be an observed Nat literal",
            "features.regularity",
        )
    return offset

def _nat_literal(expression):
    if "nat" in expression:
        return expression["nat"] if type(expression["nat"]) is int else None
    head, args = _app_parts(expression)
    if _const_name(head) != "OfNat.ofNat" or len(args) != 3:
        return None
    carrier, numeral, instance = args
    value = numeral.get("nat") if isinstance(numeral, dict) else None
    if _const_name(carrier) != "Nat" or type(value) is not int:
        return None
    _validate_nat_numeral_instance(instance, value)
    return value

def _validate_nat_numeral_instance(instance, value):
    instance_head, instance_args = _app_parts(instance)
    if _const_name(instance_head) != "instOfNatNat" or len(instance_args) != 1:
        raise _Unsupported(
            "unsupported-carrier-or-instance",
            "scale offset uses a non-builtin Nat numeral instance",
            "features.regularity",
        )
    instance_value = instance_args[0].get("nat") if isinstance(instance_args[0], dict) else None
    if type(instance_value) is not int or instance_value != value:
        raise _Unsupported(
            "unsupported-carrier-or-instance",
            "builtin Nat numeral instance does not match the observed offset",
            "features.regularity",
        )

def _resolve_let(expression, scope, depth=0):
    if depth > 16:
        raise _Unsupported(
            "let-depth-limit", "local let alias depth exceeds the supported bound", "statement"
        )
    expression = _strip_metadata(expression)
    if "bvar" not in expression:
        return expression, scope
    index = expression["bvar"]
    if type(index) is not int or index < 0 or index >= len(scope):
        return expression, scope
    resolved = scope[-index - 1]
    if resolved["kind"] == "binder":
        return expression, scope
    return _resolve_let(resolved["value"], resolved["scope"], depth + 1)

def _bound_binder(expression, scope):
    expression, scope = _resolve_let(expression, scope)
    if "bvar" not in expression:
        return None
    index = expression["bvar"]
    if type(index) is not int or index < 0 or index >= len(scope):
        return None
    row = scope[-index - 1]
    return row.get("binderId") if row["kind"] == "binder" else None

def _same_bound_term(expression, binder_id, scope):
    return _bound_binder(expression, scope) == binder_id

def _binder_type(binders, binder_id):
    return next(row["type"] for row in binders if row["binderId"] == binder_id)

def _type_head(expression):
    expression = _strip_metadata(expression)
    return _expr_head_name(expression)

def _expr_head_name(expression):
    head, _args = _app_parts(expression)
    return _const_name(head)

def _type_id(expression):
    canonical = _canonical_expr(expression)
    return "type:sha256:" + _sha256(_canonical_json(canonical).encode("utf-8"))

def _canonical_expr(value):
    if isinstance(value, list):
        return [_canonical_expr(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: _canonical_expr(child)
        for key, child in sorted(value.items())
        if key not in {"name", "binderInfo"}
    }

def _strip_metadata(value):
    return value

def _app_parts(expression):
    args = []
    current = expression
    while isinstance(current, dict) and "app" in current:
        pair = current["app"]
        if not isinstance(pair, list) or len(pair) != 2:
            break
        current, argument = pair
        args.append(argument)
    args.reverse()
    return current, args

def _app_argument_path(expression, index, path):
    arguments = []
    current = expression
    current_path = path
    while isinstance(current, dict) and "app" in current:
        pair = current["app"]
        if not isinstance(pair, list) or len(pair) != 2:
            break
        function, _argument = pair
        arguments.append(current_path + "/app/1")
        current, current_path = function, current_path + "/app/0"
    arguments.reverse()
    return arguments[index] if 0 <= index < len(arguments) else path

def _const_name(expression):
    return expression.get("const") if isinstance(expression, dict) else None

def _is_builtin_nat_relation(type_arguments):
    return (
        len(type_arguments) == 2
        and _const_name(type_arguments[0]) == "Nat"
        and _const_name(type_arguments[1]) == "instLENat"
    )

def _is_builtin_nat_operation(type_arguments_and_instance, instance_head, nat_instance):
    if len(type_arguments_and_instance) != 4:
        return False
    type_arguments = type_arguments_and_instance[:3]
    instance = type_arguments_and_instance[3]
    if any(_const_name(value) != "Nat" for value in type_arguments):
        return False
    instance_fn, instance_args = _app_parts(instance)
    return (
        _const_name(instance_fn) == instance_head
        and len(instance_args) == 2
        and _const_name(instance_args[0]) == "Nat"
        and _const_name(instance_args[1]) == nat_instance
    )

def _find_const_path(expression, name, base_path="/typeExpr"):
    stack: list[tuple[Any, str]] = [(expression, base_path)]
    seen = 0
    while stack:
        value, path = stack.pop()
        seen += 1
        if seen > MAX_EXPR_NODES:
            raise _Unsupported(
                "expression-node-limit",
                "statement expression exceeds the supported node bound",
                "statement",
            )
        if not isinstance(value, dict):
            continue
        if value.get("const") == name:
            return path
        for key, child in reversed(list(value.items())):
            if isinstance(child, list):
                stack.extend(
                    (item, f"{path}/{key}/{index}")
                    for index, item in reversed(list(enumerate(child)))
                )
            elif isinstance(child, dict):
                stack.append((child, f"{path}/{key}"))
    return None

def _sha256(value):
    return hashlib.sha256(value).hexdigest()

def _canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
