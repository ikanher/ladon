"""Exact AST recognizer for the restricted-domain-v2 proposition pair."""
from __future__ import annotations


def _node(value, tag, keys):
    return isinstance(value, dict) and set(value) == keys and value.get("tag") == tag


def _application(node, binder_id):
    if not _node(node, "app", {"tag", "symbol", "args"}):
        return None
    args = node["args"]
    if (not isinstance(node["symbol"], str) or not node["symbol"]
            or not isinstance(args, list) or len(args) != 1
            or not _node(args[0], "var", {"tag", "id"})
            or args[0]["id"] != binder_id):
        return None
    return node["symbol"]


def _binder_id(formula):
    if not _node(formula, "forall", {"tag", "binder", "body"}):
        return None
    binder = formula["binder"]
    if (not isinstance(binder, dict) or set(binder) != {"id", "name", "domain"}
            or not isinstance(binder.get("id"), str) or not binder["id"]
            or not isinstance(binder.get("name"), str) or not binder["name"]
            or binder["domain"] != "Nat"):
        return None
    return binder["id"]


def _guarded_application(body, binder_id):
    if not _node(body, "implies", {"tag", "premise", "conclusion"}):
        return None
    premise = body["premise"]
    if not _zero_guard(premise, binder_id):
        return None
    return _application(body["conclusion"], binder_id)


def _zero_guard(premise, binder_id):
    if not _node(premise, "le", {"tag", "left", "right"}):
        return False
    left, right = premise["left"], premise["right"]
    return (_node(left, "var", {"tag", "id"}) and left["id"] == binder_id
            and _node(right, "const", {"tag", "name"}) and right["name"] == "0")


def _symbol_mapping(record, symbol_id):
    if symbol_id is None:
        return None
    symbols = record.get("symbols")
    symbol = symbols.get(symbol_id) if isinstance(symbols, dict) else None
    if (not isinstance(symbol, dict) or set(symbol) != {"leanName", "leanType"}
            or symbol.get("leanType") != "Nat → Prop"
            or not isinstance(symbol.get("leanName"), str) or not symbol["leanName"]):
        return None
    return symbol


def parse_restricted_domain_ast(record):
    """Recognize only forall x:Nat, P x or forall x, x ≤ 0 → P x."""
    if not isinstance(record, dict):
        return None
    formula = record.get("formula")
    binder_id = _binder_id(formula)
    if binder_id is None:
        return None
    body = formula["body"]
    symbol_id = _application(body, binder_id)
    restricted = False
    if symbol_id is None:
        symbol_id = _guarded_application(body, binder_id)
        restricted = symbol_id is not None
    symbol = _symbol_mapping(record, symbol_id)
    if symbol is None:
        return None
    return {"binderId": binder_id, "symbolId": symbol_id,
            "symbol": symbol, "restricted": restricted}
