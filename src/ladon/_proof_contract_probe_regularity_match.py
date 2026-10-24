"""Match attributed contract features against the original typed formula."""
from ._proof_contract_probe_regularity_ast import _formula_shape, _walk

_EXPECTED = {"profileId": "norm-scale-v1"}


def _contract_features(contract):
    features = contract.get("features", {})
    regularity = features.get("regularity", {})
    if set(features) != {"regularity", "constantDependencies", "witnessDependencies"}:
        return None
    if regularity.get("state") != "known" or type(regularity.get("offset")) is not int or regularity["offset"] < 0:
        return None
    if regularity.get("reason") is not None:
        return None
    constants = features.get("constantDependencies", {})
    if constants.get("state") != "known" or constants.get("allowedBinderIds") != []:
        return None
    if constants.get("reason") is not None or features.get("witnessDependencies") != []:
        return None
    return regularity["offset"]

def _contract_offset(contract):
    if not isinstance(contract, dict) or any(contract.get(k) != v for k, v in _EXPECTED.items()):
        return None
    if contract.get("assumptions") != []:
        return None
    return _contract_features(contract)

def _telescope_rows(telescope):
    if not isinstance(telescope, list) or len(telescope) != 2:
        return None
    if any(not isinstance(row, dict) for row in telescope):
        return None
    if any(row.get("typeId") != "Nat" or row.get("quantifier") != "forall" for row in telescope):
        return None
    return telescope

def _valid_telescope(contract):
    telescope = _telescope_rows(contract.get("telescope"))
    if telescope is None:
        return None
    binder_ids = [row.get("binderId") for row in telescope]
    if any(not isinstance(identity, str) or not identity for identity in binder_ids):
        return None
    return binder_ids if binder_ids[0] != binder_ids[1] else None

def _bounded_symbols(symbols):
    return isinstance(symbols, dict) and all(
        isinstance(row, dict) and isinstance(row.get("leanName"), str)
        and row["leanName"] and len(row["leanName"]) <= 200 for row in symbols.values())

def _formula_binders(formula):
    return [node.get("binder", {}) for node in _walk(formula) if node.get("tag") in {"forall", "exists"}]

def _record_matches(record, contract, offset):
    if not isinstance(record, dict):
        return False
    formula = record.get("formula")
    symbols = record.get("symbols")
    if not isinstance(formula, dict) or not _bounded_symbols(symbols):
        return False
    binder_ids = _valid_telescope(contract)
    if binder_ids is None:
        return False
    binders = _formula_binders(formula)
    return (len(binders) == 2 and all(b.get("domain") == "Nat" for b in binders)
            and [b.get("id") for b in binders] == binder_ids
            and _formula_shape(formula, symbols, offset, *binder_ids))

def _summary_offset_mismatch(record, contract):
    offset = _contract_offset(contract)
    if offset is None or not isinstance(record, dict):
        return False
    formula, symbols = record.get("formula"), record.get("symbols")
    binder_ids = _valid_telescope(contract)
    if not isinstance(formula, dict) or not _bounded_symbols(symbols) or binder_ids is None:
        return False
    try:
        literal = formula["body"]["body"]["right"]["args"][1]["args"][0]["args"][1]
        actual_offset = int(literal.get("name"))
    except (KeyError, IndexError, TypeError, ValueError):
        return False
    return (type(literal.get("name")) is str and literal.get("name") == str(actual_offset)
            and actual_offset != offset and _formula_shape(formula, symbols, actual_offset, *binder_ids))

def _regularity_shape(record, contract):
    offset = _contract_offset(contract)
    return offset is not None and _record_matches(record, contract, offset)
