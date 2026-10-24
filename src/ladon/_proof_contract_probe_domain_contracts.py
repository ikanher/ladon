"""Contract checks for the exact restricted-domain-v2 proposition pair."""
from __future__ import annotations

from ladon.proof_contracts import validate_contract

from ._proof_contract_probe_templates import _residual


def _side(raw, parsed):
    contract = validate_contract(raw)
    expected = [{"binderId": parsed["binderId"], "typeId": "Nat", "quantifier": "forall"}]
    if contract["telescope"] != expected:
        raise ValueError("contract telescope conflicts with the recognized original AST")
    if contract["assumptions"]:
        return contract, _residual("unsupported-restricted-domain",
            "Scoped assumptions are outside the restricted-domain profile.", "assumptions")
    issue = _unsupported_features(contract)
    return contract, issue


def _unsupported_features(contract):
    features = contract["features"]
    regularity = features["regularity"]
    constants = features["constantDependencies"]
    checks = (
        (regularity["state"] != "unknown" or regularity["offset"] is not None
         or regularity["scaleId"] != contract["context"]["scaleId"],
         "Regularity must remain unknown in this profile.", "regularity"),
        ("binderId" in constants or constants["state"] != "unknown"
         or constants["allowedBinderIds"] is not None or features["witnessDependencies"],
         "Constant and witness dependencies must remain unknown or absent in this profile.", "features"),
    )
    for invalid, message, feature in checks:
        if invalid:
            return _residual("unsupported-restricted-domain", message, feature)
    return None


def validate_restricted_domain_pair(left_raw, right_raw, left_ast, right_ast):
    left, le = _side(left_raw, left_ast)
    right, re = _side(right_raw, right_ast)
    issue = le or re
    if issue:
        return None, issue
    issue = _pair_issue(left, right, left_ast, right_ast)
    if issue:
        return None, issue
    return (left, right), None


def _pair_issue(left, right, left_ast, right_ast):
    for key in ("profileId", "endpointId", "context", "assumptions", "conclusionId", "features"):
        if left[key] != right[key]:
            return _residual("unsupported-restricted-domain",
                "Contract context and out-of-scope feature metadata must agree exactly.", "contract")
    if left_ast["binderId"] != right_ast["binderId"]:
        return _residual("unsupported-restricted-domain",
            "Both readings must use the same binder identity.", "formula")
    if left_ast["symbolId"] != right_ast["symbolId"] or left_ast["symbol"] != right_ast["symbol"]:
        return _residual("unsupported-restricted-domain",
            "Both readings must share the same typed predicate mapping.", "symbols")
    if _endpoint_mismatch(left, right, left_ast):
        return _residual("unsupported-restricted-domain",
            "Contract endpoint and conclusion must identify the parsed predicate symbol.", "endpoint")
    if left_ast["restricted"] == right_ast["restricted"]:
        return _residual("unsupported-restricted-domain",
            "Exactly one reading must carry the fixed restricted-domain premise.", "formula")
    return None


def _endpoint_mismatch(left, right, parsed):
    expected = "predicate:" + parsed["symbolId"]
    return any(contract[field] != expected for contract in (left, right)
               for field in ("endpointId", "conclusionId"))
