"""Validate contracts against the exact Nat inequality-direction AST."""
from __future__ import annotations

from ladon.proof_contracts import validate_contract

from ._proof_contract_probe_templates import _residual

_RELATION_ID = "relation:Nat.le"
_NAT_ORDER_CONTEXT = {
    "objectId": "object:nat-order",
    "domainId": "domain:Nat",
    "scaleId": "scale:none",
    "representationId": "representation:original",
}


def _unsupported(message, feature):
    return _residual("unsupported-inequality-direction", message, feature)


def _telescope_error(contract, parsed):
    expected = [{"binderId": parsed["binderId"], "typeId": "Nat", "quantifier": "forall"}]
    if contract["telescope"] != expected:
        raise ValueError("contract telescope conflicts with the recognized Nat inequality AST")


def _endpoint_error(contract):
    if contract["endpointId"] != _RELATION_ID or contract["conclusionId"] != _RELATION_ID:
        return _unsupported("Endpoint and conclusion must identify the recognized Nat.le relation.",
                            "endpoint")
    return None


def _context_error(contract):
    if contract["context"] != _NAT_ORDER_CONTEXT:
        return _unsupported("Only the registered built-in Nat order context is supported.", "context")
    return None


def _feature_error(contract):
    if contract["assumptions"]:
        return _unsupported("Assumptions are outside this profile.", "assumptions")
    features = contract["features"]
    regularity = features["regularity"]
    if regularity["state"] != "unknown" or regularity["offset"] is not None:
        return _unsupported("Regularity is not modeled by this profile.", "regularity")
    constants = features["constantDependencies"]
    if ("binderId" in constants or constants["state"] != "unknown"
            or constants["allowedBinderIds"] is not None or features["witnessDependencies"]):
        return _unsupported("Dependencies are outside this profile.", "features")
    return None


def _side(raw, parsed):
    contract = validate_contract(raw)
    _telescope_error(contract, parsed)
    if contract["profileId"] != "norm-scale-v1":
        return contract, _unsupported("Only the registered norm-scale contract profile is supported.",
                                      "profile")
    error = _endpoint_error(contract) or _context_error(contract) or _feature_error(contract)
    return contract, error


def validate_inequality_pair(left_raw, right_raw, left_ast, right_ast):
    left, left_error = _side(left_raw, left_ast)
    right, right_error = _side(right_raw, right_ast)
    if left_error or right_error:
        return None, left_error or right_error
    if left != right:
        return None, _unsupported("Contract context and feature metadata must agree exactly.", "contract")
    if left_ast["binderId"] != right_ast["binderId"]:
        return None, _unsupported("Both readings must share the same source binder identity.", "formula")
    if left_ast["direction"] == right_ast["direction"]:
        return None, _unsupported("Exactly one reading must reverse the Nat zero-bound operands.", "formula")
    return (left, right), None
