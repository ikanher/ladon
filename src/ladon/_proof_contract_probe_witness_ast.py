"""Exact two-binder AST roles for witness-dependence-v2."""
from __future__ import annotations


def _node(value, tag, keys):
    return isinstance(value, dict) and set(value) == keys and value.get("tag") == tag


def _binder_row(node):
    if not isinstance(node, dict) or node.get("tag") not in {"exists", "forall"}:
        return None
    if set(node) != {"tag", "binder", "body"}:
        return None
    binder = node["binder"]
    if not isinstance(binder, dict) or set(binder) != {"id", "name", "domain"}:
        return None
    if binder.get("domain") != "Nat" or not isinstance(binder.get("id"), str):
        return None
    if not binder["id"] or not isinstance(binder.get("name"), str):
        return None
    return (binder["id"], node["tag"]), node["body"]


def _valid_binder_order(rows):
    identities = [row[0] for row in rows]
    quantifiers = [row[1] for row in rows]
    orders = (["exists", "forall"], ["forall", "exists"])
    return len(set(identities)) == 2 and quantifiers in orders


def _binder_rows(formula):
    rows, node = [], formula
    for _ in range(2):
        parsed = _binder_row(node)
        if parsed is None:
            return None
        row, node = parsed
        rows.append(row)
    if not _valid_binder_order(rows):
        return None
    return rows, node


def _predicate_symbol(body, witness, parameter):
    if not _node(body, "app", {"tag", "symbol", "args"}):
        return None
    symbol_id = body["symbol"]
    if not isinstance(symbol_id, str) or not symbol_id:
        return None
    args = body["args"]
    if not isinstance(args, list) or len(args) != 2:
        return None
    roles = ((args[0], witness), (args[1], parameter))
    if any(not _node(arg, "var", {"tag", "id"}) or arg["id"] != identity
           for arg, identity in roles):
        return None
    return symbol_id


def _typed_symbol(symbols, symbol_id):
    if not isinstance(symbols, dict):
        return None
    symbol = symbols.get(symbol_id)
    if not isinstance(symbol, dict) or symbol.get("leanType") != "Nat → Nat → Prop":
        return None
    if not isinstance(symbol.get("leanName"), str) or not symbol["leanName"]:
        return None
    return symbol


def parse_witness_ast(record):
    """Recognize only P(w,x) under one of the two exact Nat quantifier orders."""
    if not isinstance(record, dict):
        return None
    nested = _binder_rows(record.get("formula"))
    if nested is None:
        return None
    rows, body = nested
    witness = next(identity for identity, kind in rows if kind == "exists")
    parameter = next(identity for identity, kind in rows if kind == "forall")
    symbol_id = _predicate_symbol(body, witness, parameter)
    symbol = _typed_symbol(record.get("symbols"), symbol_id)
    if symbol is None:
        return None
    return {
        "rows": rows,
        "witnessId": witness,
        "parameterId": parameter,
        "symbolId": symbol_id,
        "symbol": symbol,
        "formula": record["formula"],
        "kind": "strong" if rows[0][1] == "exists" else "weak",
    }
