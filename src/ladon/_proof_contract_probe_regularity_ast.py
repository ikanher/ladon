"""Exact AST role and offset matching for the closed regularity profile."""
from __future__ import annotations

from typing import Any


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
