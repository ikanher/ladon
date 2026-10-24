"""Exact AST roles for quantified Nat constant-uniformity probes."""
from __future__ import annotations

import re


def _node(value, tag, keys):
    return isinstance(value, dict) and set(value) == keys and value.get("tag") == tag


def _valid_binder(binder):
    return (isinstance(binder, dict) and set(binder) == {"id", "name", "domain"}
            and binder.get("domain") == "Nat" and isinstance(binder.get("id"), str)
            and bool(binder["id"]) and isinstance(binder.get("name"), str))


def _binder_rows(formula):
    rows, node = [], formula
    while isinstance(node, dict) and node.get("tag") in {"forall", "exists"}:
        if not _node(node, node["tag"], {"tag", "binder", "body"}):
            return None
        binder = node["binder"]
        if not _valid_binder(binder):
            return None
        rows.append((binder["id"], node["tag"]))
        node = node["body"]
    return (rows, node) if len(rows) == 3 else None


def _roles(rows):
    ids, quantifiers = [r[0] for r in rows], [r[1] for r in rows]
    if len(set(ids)) != 3:
        return None
    if quantifiers == ["exists", "forall", "forall"]:
        return {"c": ids[0], "s": ids[1], "x": ids[2]}, "strong"
    if quantifiers == ["forall", "exists", "forall"]:
        return {"s": ids[0], "c": ids[1], "x": ids[2]}, "weak"
    return None


def _var(value, identity):
    return _node(value, "var", {"tag", "id"}) and value["id"] == identity


def _app(value, arity):
    return (_node(value, "app", {"tag", "symbol", "args"}) and isinstance(value["symbol"], str)
            and isinstance(value["args"], list) and len(value["args"]) == arity)


def _left_roles(body, roles):
    left = body["left"]
    if not _app(left, 2) or not _var(left["args"][0], roles["s"]):
        return None
    function = left["args"][1]
    if not _app(function, 1) or not _var(function["args"][0], roles["x"]):
        return None
    return left["symbol"], function["symbol"]


def _right_roles(body, roles):
    right = body["right"]
    if not _app(right, 2) or not _coefficient(right["args"][0], roles["c"]):
        return None
    application = right["args"][1]
    if not _app(application, 2) or not _var(application["args"][1], roles["x"]):
        return None
    addition = application["args"][0]
    if not _app(addition, 2) or not _var(addition["args"][0], roles["s"]):
        return None
    literal = addition["args"][1]
    if not _node(literal, "const", {"tag", "name"}):
        return None
    if not isinstance(literal["name"], str) or not re.fullmatch(r"[0-9]{1,20}", literal["name"]):
        return None
    ids = (application["symbol"], right["symbol"], addition["symbol"])
    return ids, literal["name"]


def _coefficient(value, constant_id):
    if not _node(value, "var", {"tag", "id"}):
        return False
    if value["id"] != constant_id:
        raise ValueError("coefficient variable conflicts with the existential constant anchor")
    return True


def _symbol_rows(symbol_ids, symbols):
    if len(set(symbol_ids)) != 5 or any(identity not in symbols for identity in symbol_ids):
        return None
    expected = ("Nat → Nat → Nat", "Nat → Nat", "Nat → Nat → Nat",
                "Nat → Nat → Nat", "Nat → Nat → Nat")
    rows = [symbols[identity] for identity in symbol_ids]
    if any(not isinstance(row, dict) or row.get("leanType") != signature
           for row, signature in zip(rows, expected)):
        return None
    return rows


def _typed_symbols(symbol_ids, symbols):
    rows = _symbol_rows(symbol_ids, symbols)
    if rows is None or rows[3].get("leanName") != "Nat.mul" or rows[4].get("leanName") != "Nat.add":
        return False
    return all(isinstance(row.get("leanName"), str) and row["leanName"]
               and len(row["leanName"]) <= 200 for row in rows)


def _body_roles(body, roles, symbols):
    if not _node(body, "le", {"tag", "left", "right"}):
        return None
    left_ids = _left_roles(body, roles)
    right_data = _right_roles(body, roles)
    if left_ids is None or right_data is None:
        return None
    ids, literal = left_ids + right_data[0], right_data[1]
    if not _typed_symbols(ids, symbols):
        return None
    return {"offset": int(literal), "roles": roles, "body": body,
            "symbolIds": ids, "symbols": symbols}


def parse_uniformity_ast(record):
    """Return role data for the exact supported quantified body, else None."""
    if not isinstance(record, dict) or not isinstance(record.get("formula"), dict):
        return None
    symbols = record.get("symbols")
    if not isinstance(symbols, dict):
        return None
    nested = _binder_rows(record["formula"])
    if nested is None:
        return None
    rows, body = nested
    role_result = _roles(rows)
    if role_result is None:
        return None
    roles, kind = role_result
    parsed = _body_roles(body, roles, symbols)
    if parsed is None:
        return None
    parsed.update({"formula": record["formula"], "rows": rows, "kind": kind})
    return parsed
