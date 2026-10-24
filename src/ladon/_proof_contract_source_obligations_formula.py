"""Narrow normalized-expression parser for the source-bound atomic fragment."""
from __future__ import annotations


def _formula_symbols(expr):
    body = _two_nat_binders(expr)
    _inequality(body)
    # Reuse the repository's full recognizer for builtin instances, carrier,
    # telescope and coefficient checks. The local shape checks keep this API
    # limited to the explicit two-binder fragment.
    from ladon.proof_contract_expressions import _Unsupported
    from ladon.proof_contract_recognition import _recognize_estimate
    try:
        summary = _recognize_estimate(expr)
    except _Unsupported as error:
        raise ValueError(str(error)) from error
    if len(summary["binders"]) != 2 or any(
        row["quantifier"] != "forall" or row["type"].get("const") != "Nat"
        for row in summary["binders"]
    ):
        raise ValueError("source formula must have exactly two universal Nat binders")
    symbols = {"leftOperator": summary["leftOperator"], "map": summary["map"],
        "constantName": summary["constantName"], "inputScale": summary["inputScale"],
        "offset": summary["offset"]}
    if any(value is None for value in symbols.values()):
        raise ValueError("source formula requires a global coefficient")
    return {"kind": "forallNat2", **symbols}


def _two_nat_binders(expr):
    first = expr.get("forallE") if isinstance(expr, dict) else None
    if not _explicit_nat(first):
        raise ValueError("source formula is not an explicit Nat forall")
    second = first["body"].get("forallE") if isinstance(first["body"], dict) else None
    if not _explicit_nat(second) or "forallE" in second["body"]:
        raise ValueError("source formula must have exactly two explicit Nat binders")
    return second["body"]


def _explicit_nat(binder):
    return (isinstance(binder, dict) and binder.get("binderInfo") == "explicit"
            and _is_nat(binder.get("type")))


def _inequality(body):
    head, args = _flatten(body)
    if _const(head) != "LE.le" or len(args) != 4 or not _is_nat(args[0]):
        raise ValueError("source formula is not a Nat inequality")
    return args[2], args[3]


def _is_nat(expr):
    return isinstance(expr, dict) and _const(expr) == "Nat"


def _const(expr):
    return expr.get("const") if isinstance(expr, dict) else None


def _flatten(expr):
    args = []
    while isinstance(expr, dict) and "app" in expr:
        row = expr["app"]
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("malformed application AST")
        args.append(row[1])
        expr = row[0]
    args.reverse()
    return expr, args


