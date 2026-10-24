"""Exact coefficient and selected occurrence symbol-role checks."""
from __future__ import annotations


def _requirement_symbols(selected):
    contract = selected["contractRecord"]
    if contract["assumptions"] or len(contract["telescope"]) != 2:
        raise ValueError("selected requirement changes the parent quantifier context")
    conclusion = contract["conclusionId"].split(":")
    if len(conclusion) < 5 or conclusion[0] != "estimate":
        raise ValueError("selected requirement lacks ordered source symbol roles")
    return {"leftOperator": conclusion[1], "map": contract["context"]["objectId"].removeprefix("operator:"),
        "inputScale": contract["features"]["regularity"]["scaleId"].removeprefix("scale:"),
        "offset": contract["features"]["regularity"]["offset"]}


def _require_supported_symbol_transport(parent, provider, selected):
    if parent["constantName"] != provider["constantName"]:
        raise ValueError("global coefficient identity differs between parent and provider")
    if selected.get("constantName") is not None and selected["constantName"] != provider["constantName"]:
        raise ValueError("selected requirement changes global coefficient identity")
    for role in ("leftOperator", "map", "inputScale"):
        if selected.get(role) is not None and provider[role] != selected[role]:
            raise ValueError("selected requirement disagrees with provider " + role)
    for role in ("leftOperator", "map", "constantName", "inputScale"):
        if not isinstance(provider.get(role), str) or not provider[role]:
            raise ValueError("source symbol role is unresolved: " + role)


