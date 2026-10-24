"""Validate witness AST roles against each side's attributed contract."""
from __future__ import annotations

from ladon.proof_contracts import validate_contract


def _unsupported(message, feature):
    return {"code": "unsupported-witness-dependence", "message": message, "feature": feature}


def _validate_telescope(contract, parsed):
    expected = [
        {"binderId": identity, "typeId": "Nat", "quantifier": quantifier}
        for identity, quantifier in parsed["rows"]
    ]
    if contract["telescope"] != expected:
        raise ValueError("contract telescope conflicts with the recognized original AST order")
    return contract["features"]


def _validate_regularity(regularity):
    if (regularity["state"] != "unknown" or regularity["offset"] is not None
            or not isinstance(regularity["reason"], str)):
        return _unsupported("Regularity must remain unknown in the witness profile.", "regularity")
    return None


def _validate_constants(constants):
    if ("binderId" in constants or constants["state"] != "unknown"
            or constants["allowedBinderIds"] is not None):
        return _unsupported(
            "Constant dependencies must be unanchored and unknown in the witness profile.",
            "constantDependencies",
        )
    return None


def _validate_witness(rows, parsed):
    if len(rows) != 1 or rows[0]["binderId"] != parsed["witnessId"]:
        raise ValueError("witness dependency row conflicts with the recognized existential binder")
    witness = rows[0]
    if witness["state"] != "known":
        return _unsupported("Witness permissions must be known for this profile.", "witnessDependencies")
    expected = [parsed["parameterId"]] if parsed["kind"] == "weak" else []
    if witness["allowedBinderIds"] != expected:
        raise ValueError("witness permissions conflict with the original AST quantifier order")
    return None


def _validate_side(raw_contract, parsed):
    contract = validate_contract(raw_contract)
    features = _validate_telescope(contract, parsed)
    errors = (
        _validate_regularity(features["regularity"]),
        _validate_constants(features["constantDependencies"]),
        _validate_witness(features["witnessDependencies"], parsed),
    )
    return contract, next((error for error in errors if error is not None), None)


def _same_nonorder_metadata(left, right):
    for key in ("profileId", "endpointId", "context", "assumptions", "conclusionId"):
        if left[key] != right[key]:
            return False
    lf, rf = left["features"], right["features"]
    if lf["regularity"] != rf["regularity"]:
        return False
    if lf["constantDependencies"] != rf["constantDependencies"]:
        return False
    lw, rw = lf["witnessDependencies"][0], rf["witnessDependencies"][0]
    return {**lw, "allowedBinderIds": None} == {**rw, "allowedBinderIds": None}


def validate_witness_pair(left_raw, right_raw, left_ast, right_ast):
    """Return a residual outside the exact profile; reject recognized conflicts."""
    left, left_error = _validate_side(left_raw, left_ast)
    right, right_error = _validate_side(right_raw, right_ast)
    if left_error or right_error:
        return None, left_error or right_error
    if not _same_nonorder_metadata(left, right):
        return None, _unsupported(
            "Contract endpoints, context, assumptions, or non-witness features differ.",
            "contract",
        )
    if (left_ast["witnessId"] != right_ast["witnessId"]
            or left_ast["parameterId"] != right_ast["parameterId"]):
        return None, _unsupported("The readings do not share witness and parameter identities.", "formula")
    if left_ast["symbolId"] != right_ast["symbolId"] or left_ast["symbol"] != right_ast["symbol"]:
        return None, _unsupported("The readings do not use the same typed predicate symbol mapping.", "symbols")
    return (left, right), None
