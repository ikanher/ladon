"""Check recognized AST roles against validated authored contract metadata."""
from __future__ import annotations

from ladon.proof_contracts import validate_contract


def _unsupported(message, feature):
    return {"code": "unsupported-constant-uniformity", "message": message, "feature": feature}


def _expected_permissions(parsed):
    return [] if parsed["kind"] == "strong" else [parsed["roles"]["s"]]


def _known_or_unsupported(contract, parsed):
    features = contract["features"]
    regularity = features["regularity"]
    constant = features["constantDependencies"]
    witnesses = features["witnessDependencies"]
    if regularity["state"] != "known" or constant["state"] != "known":
        return _unsupported("Regularity and constant dependencies must be known.", "features")
    if any(row["state"] != "known" for row in witnesses):
        return _unsupported("Every existential witness dependency must be known.", "witnessDependencies")
    return None


def _verify_telescope(contract, parsed):
    expected_telescope = [{"binderId": identity, "typeId": "Nat", "quantifier": quantifier}
                          for identity, quantifier in parsed["rows"]]
    if contract["telescope"] != expected_telescope:
        raise ValueError("contract telescope conflicts with the recognized original AST order")


def _verify_permissions(contract, parsed):
    roles = parsed["roles"]
    constant = contract["features"]["constantDependencies"]
    witnesses = contract["features"]["witnessDependencies"]
    if constant.get("binderId") != roles["c"]:
        raise ValueError("constant dependency anchor conflicts with the AST coefficient binder")
    if len(witnesses) != 1 or witnesses[0]["binderId"] != roles["c"]:
        raise ValueError("witness dependency rows conflict with the AST existential binder")
    permissions = _expected_permissions(parsed)
    if constant["allowedBinderIds"] != permissions:
        raise ValueError("constant permissions conflict with the AST quantifier order")
    if witnesses[0]["allowedBinderIds"] != permissions:
        raise ValueError("witness permissions conflict with the AST quantifier order")


def _verify_regularity(contract, parsed):
    regularity = contract["features"]["regularity"]
    if regularity["offset"] != parsed["offset"]:
        raise ValueError("regularity offset conflicts with its designated AST literal")


def _verify_recognized(contract, parsed):
    if contract["assumptions"]:
        raise ValueError("constant-uniformity profile does not allow assumptions")
    _verify_telescope(contract, parsed)
    unsupported = _known_or_unsupported(contract, parsed)
    if unsupported:
        return unsupported
    _verify_permissions(contract, parsed)
    _verify_regularity(contract, parsed)
    return None


def validate_uniformity_contract(raw_contract, parsed):
    """Validate native contract structure, then reject known AST/summary conflicts."""
    contract = validate_contract(raw_contract)
    return contract, _verify_recognized(contract, parsed)


def _feature_without_permissions(feature):
    return {key: value for key, value in feature.items() if key != "allowedBinderIds"}


def _same_nonorder_metadata(left, right):
    for key in ("profileId", "endpointId", "context", "assumptions", "conclusionId"):
        if left[key] != right[key]:
            return False
    lf, rf = left["features"], right["features"]
    if lf["regularity"] != rf["regularity"]:
        return False
    if _feature_without_permissions(lf["constantDependencies"]) != _feature_without_permissions(rf["constantDependencies"]):
        return False
    lw, rw = lf["witnessDependencies"], rf["witnessDependencies"]
    return len(lw) == len(rw) == 1 and _feature_without_permissions(lw[0]) == _feature_without_permissions(rw[0])


def uniformity_pair_residual(left, right, left_ast, right_ast):
    if not _same_nonorder_metadata(left, right):
        return _unsupported("Contract endpoint, context, assumptions, conclusion, or regularity differs.", "contract")
    if left_ast["roles"] != right_ast["roles"] or left_ast["offset"] != right_ast["offset"]:
        return _unsupported("The readings do not share binder roles and the same regularity literal.", "regularity")
    if left_ast["symbolIds"] != right_ast["symbolIds"]:
        return _unsupported("The readings use different typed body symbols.", "symbols")
    for identity in left_ast["symbolIds"]:
        if left_ast["symbols"][identity] != right_ast["symbols"][identity]:
            return _unsupported("The readings use different typed body symbol mappings.", "symbols")
    return None
