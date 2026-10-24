"""Exact AST roles for the closed Nat zero-bound direction profile."""
from __future__ import annotations


def _node(value, tag, keys):
    return isinstance(value, dict) and set(value) == keys and value.get("tag") == tag


def _binder(formula):
    if not _node(formula, "forall", {"tag", "binder", "body"}):
        return None
    value = formula["binder"]
    if not isinstance(value, dict) or set(value) != {"id", "name", "domain"}:
        return None
    identity = value.get("id")
    if (value.get("domain") != "Nat" or not isinstance(identity, str) or not identity
            or not isinstance(value.get("name"), str) or not value["name"]):
        return None
    return identity


def _zero(node):
    return _node(node, "const", {"tag", "name"}) and node.get("name") == "0"


def _variable(node, identity):
    return _node(node, "var", {"tag", "id"}) and node.get("id") == identity


def _direction(body, identity):
    if not _node(body, "le", {"tag", "left", "right"}):
        return None
    left, right = body["left"], body["right"]
    if _variable(left, identity) and _zero(right):
        return "to-zero"
    if _zero(left) and _variable(right, identity):
        return "from-zero"
    return None


def parse_inequality_ast(record):
    """Recognize only forall x:Nat, x <= 0 or forall x:Nat, 0 <= x."""
    if not isinstance(record, dict) or not isinstance(record.get("symbols"), dict):
        return None
    if record["symbols"]:
        return None
    formula = record.get("formula")
    identity = _binder(formula)
    if identity is None:
        return None
    direction = _direction(formula["body"], identity)
    if direction is None:
        return None
    return {"binderId": identity, "direction": direction, "formula": formula}
