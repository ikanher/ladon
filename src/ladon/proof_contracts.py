"""Validation and structural comparison for bounded proof contracts.

This module checks record shape and declared profile data. It does not inspect
Lean source or establish mathematical truth.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_RECORD_KEYS = {
    "profileId", "endpointId", "context", "telescope", "assumptions",
    "conclusionId", "features",
}
_CONTEXT_KEYS = {"objectId", "domainId", "scaleId", "representationId"}
_BINDER_KEYS = {"binderId", "typeId", "quantifier"}
_ASSUMPTION_KEYS = {"predicateId"}
_REGULARITY_KEYS = {"state", "scaleId", "offset", "reason"}
_DEPENDENCY_KEYS = {"state", "allowedBinderIds", "reason"}
_WITNESS_KEYS = {"binderId", "state", "allowedBinderIds", "reason"}
_FEATURE_KEYS = {"regularity", "constantDependencies", "witnessDependencies"}
_STATES = {"known", "unknown", "unsupported"}
_MAX_ROWS = 4096
_MAX_INTEGER = 2**53 - 1


def _object(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must be an object with exactly {sorted(keys)}")


def _identifier(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > 512:
        raise ValueError(f"{label} must be a nonempty string")


def _bounded_rows(value: Any, label: str) -> None:
    if not isinstance(value, list) or len(value) > _MAX_ROWS:
        raise ValueError(f"{label} must be a bounded list")


def _id_list(value: Any, label: str) -> None:
    _bounded_rows(value, label)
    for item in value:
        _identifier(item, label + " entry")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} must not contain duplicates")


def _state(value: Any, allowed: Any, reason: Any, label: str) -> None:
    if not isinstance(value, str) or value not in _STATES:
        raise ValueError(f"{label}.state must be known, unknown, or unsupported")
    if value == "known":
        if reason is not None:
            raise ValueError(f"{label}.reason must be null when known")
        if allowed is None:
            raise ValueError(f"{label} permissions must be explicit when known")
        _id_list(allowed, label + ".allowedBinderIds")
    else:
        _identifier(reason, label + ".reason")
        if allowed is not None:
            raise ValueError(f"{label}.allowedBinderIds must be null when state is not known")


def _validate_telescope(telescope: Any) -> tuple[dict[str, str], dict[str, int]]:
    _bounded_rows(telescope, "telescope")
    quantifiers: dict[str, str] = {}
    positions: dict[str, int] = {}
    for index, binder in enumerate(telescope):
        _object(binder, _BINDER_KEYS, f"telescope[{index}]")
        binder_id = binder["binderId"]
        _identifier(binder_id, f"telescope[{index}].binderId")
        _identifier(binder["typeId"], f"telescope[{index}].typeId")
        if binder["quantifier"] not in ("forall", "exists"):
            raise ValueError(f"telescope[{index}].quantifier is invalid")
        if binder_id in quantifiers:
            raise ValueError("binderId values must be unique")
        quantifiers[binder_id] = binder["quantifier"]
        positions[binder_id] = index
    return quantifiers, positions


def _validate_assumptions(assumptions: Any) -> None:
    _bounded_rows(assumptions, "assumptions")
    seen: set[str] = set()
    for index, assumption in enumerate(assumptions):
        _object(assumption, _ASSUMPTION_KEYS, f"assumptions[{index}]")
        predicate = assumption["predicateId"]
        _identifier(predicate, f"assumptions[{index}].predicateId")
        if predicate in seen:
            raise ValueError("predicateId values must be unique")
        seen.add(predicate)


def _validate_regularity(value: Any, scale_id: str) -> None:
    _object(value, _REGULARITY_KEYS, "features.regularity")
    state = value["state"]
    if not isinstance(state, str) or state not in _STATES:
        raise ValueError("features.regularity.state is invalid")
    _identifier(value["scaleId"], "features.regularity.scaleId")
    if value["scaleId"] != scale_id:
        raise ValueError("regularity scaleId must match context.scaleId")
    _regularity_state(state, value["offset"], value["reason"])


def _regularity_state(state, offset, reason):
    if state == "known":
        if type(offset) is not int or not 0 <= offset <= _MAX_INTEGER or reason is not None:
            raise ValueError("known regularity needs a nonnegative integer offset and null reason")
    else:
        if offset is not None:
            raise ValueError("unknown regularity needs null offset")
        _identifier(reason, "regularity reason")


def _validate_constant(value: Any, quantifiers: dict[str, str], positions) -> None:
    anchored = isinstance(value, dict) and "binderId" in value
    keys = _DEPENDENCY_KEYS | ({"binderId"} if anchored else set())
    _object(value, keys, "features.constantDependencies")
    _state(value["state"], value["allowedBinderIds"], value["reason"],
           "features.constantDependencies")
    allowed = value["allowedBinderIds"]
    if allowed is not None and any(quantifiers.get(binder) != "forall" for binder in allowed):
        raise ValueError("constant permission must reference a forall binder")
    if anchored:
        _identifier(value["binderId"], "constant anchor")
        if quantifiers.get(value["binderId"]) != "exists":
            raise ValueError("constant anchor must be an existential binder")
        _witness_permissions(value, quantifiers, positions)


def _validate_witnesses(
    witnesses: Any, quantifiers: dict[str, str], positions: dict[str, int]
) -> None:
    _bounded_rows(witnesses, "features.witnessDependencies")
    seen: set[str] = set()
    for index, witness in enumerate(witnesses):
        _object(witness, _WITNESS_KEYS, f"features.witnessDependencies[{index}]")
        binder = witness["binderId"]
        _identifier(binder, f"features.witnessDependencies[{index}].binderId")
        if quantifiers.get(binder) != "exists":
            raise ValueError("witness dependency must refer to an existential binder")
        if binder in seen:
            raise ValueError("witness dependency binders must be unique")
        seen.add(binder)
        _witness_permissions(witness, quantifiers, positions)
    expected = {binder for binder, kind in quantifiers.items() if kind == "exists"}
    if seen != expected:
        raise ValueError("every existential binder needs exactly one witness dependency row")


def _witness_permissions(witness, quantifiers, positions):
    allowed = witness["allowedBinderIds"]
    _state(witness["state"], allowed, witness["reason"], "witness permissions")
    if allowed is None:
        return
    for permitted in allowed:
        if quantifiers.get(permitted) != "forall":
            raise ValueError("witness permission must reference an earlier forall binder")
        if positions[permitted] >= positions[witness["binderId"]]:
            raise ValueError("witness permission must reference an earlier forall binder")


def _constant_witness_coherence(features):
    constant = features["constantDependencies"]
    anchor = constant.get("binderId")
    if anchor is None or constant["state"] != "known":
        return
    witness = next(row for row in features["witnessDependencies"] if row["binderId"] == anchor)
    if witness["state"] != "known":
        return
    if set(constant["allowedBinderIds"]) != set(witness["allowedBinderIds"]):
        raise ValueError("constant and witness summaries must agree on known permissions")


def validate_contract(record: Any) -> dict[str, Any]:
    """Validate a closed contract record and return an independent copy."""
    _object(record, _RECORD_KEYS, "record")
    _identifier(record["profileId"], "profileId")
    if record["profileId"] != "norm-scale-v1":
        raise ValueError("unsupported profileId")
    _identifier(record["endpointId"], "endpointId")
    _identifier(record["conclusionId"], "conclusionId")

    context = record["context"]
    _object(context, _CONTEXT_KEYS, "context")
    for key, value in context.items():
        _identifier(value, "context." + key)

    quantifiers, positions = _validate_telescope(record["telescope"])
    _validate_assumptions(record["assumptions"])

    features = record["features"]
    _object(features, _FEATURE_KEYS, "features")
    _validate_regularity(features["regularity"], context["scaleId"])
    _validate_constant(features["constantDependencies"], quantifiers, positions)
    _validate_witnesses(features["witnessDependencies"], quantifiers, positions)
    _constant_witness_coherence(features)
    return deepcopy(record)


def _canonical(record: dict[str, Any]) -> dict[str, Any]:
    """Replace binder names by telescope positions for semantic comparison."""
    positions = {row["binderId"]: f"b{index}" for index, row in enumerate(record["telescope"])}
    telescope = [
        {"binderId": positions[row["binderId"]], "typeId": row["typeId"],
         "quantifier": row["quantifier"]}
        for row in record["telescope"]
    ]
    features = record["features"]
    constant = features["constantDependencies"]
    witnesses = features["witnessDependencies"]
    return {
        "profileId": record["profileId"],
        "endpointId": record["endpointId"],
        "context": record["context"],
        "telescope": telescope,
        "assumptions": record["assumptions"],
        "conclusionId": record["conclusionId"],
        "constantAnchor": positions.get(constant.get("binderId"), "implicit-after-telescope"),
        "regularity": features["regularity"],
        "constant": {
            "state": constant["state"],
            "allowed": None if constant["allowedBinderIds"] is None else
                sorted(positions[b] for b in constant["allowedBinderIds"]),
            "reason": constant["reason"],
        },
        "witnesses": sorted((
            positions[w["binderId"]], w["state"],
            None if w["allowedBinderIds"] is None else
                tuple(sorted(positions[b] for b in w["allowedBinderIds"])),
            w["reason"],
        ) for w in witnesses),
    }


def _all_features_known(record: dict[str, Any]) -> bool:
    features = record["features"]
    states = [features["regularity"]["state"],
              features["constantDependencies"]["state"]]
    states.extend(row["state"] for row in features["witnessDependencies"])
    return all(state == "known" for state in states)


def _permission_sets(record: dict[str, Any]) -> list[set[str]]:
    positions = {row["binderId"]: f"b{index}" for index, row in enumerate(record["telescope"])}
    features = record["features"]
    values = [features["constantDependencies"]["allowedBinderIds"]]
    witnesses = sorted(
        features["witnessDependencies"], key=lambda row: positions[row["binderId"]]
    )
    values.extend(row["allowedBinderIds"] for row in witnesses)
    return [{positions[binder] for binder in row} for row in values]


def _at_least_as_strong(
    offset: int, permissions: list[set[str]],
    other_offset: int, other_permissions: list[set[str]],
) -> bool:
    return offset <= other_offset and all(
        own <= other for own, other in zip(permissions, other_permissions)
    )


def _relation(left: dict[str, Any], right: dict[str, Any]) -> tuple[str, list[str]]:
    a, b = _canonical(left), _canonical(right)
    gates = ("profileId", "endpointId", "context", "telescope", "assumptions", "conclusionId",
             "constantAnchor")
    if any(a[key] != b[key] for key in gates):
        return "unknown", ["contracts have different endpoints, contexts, assumptions, or conclusions"]
    if not _all_features_known(left) or not _all_features_known(right):
        return "unknown", ["one or more comparison features are unknown or unsupported"]
    left_features, right_features = left["features"], right["features"]
    left_sets, right_sets = _permission_sets(left), _permission_sets(right)
    left_offset = left_features["regularity"]["offset"]
    right_offset = right_features["regularity"]["offset"]
    left_better = _at_least_as_strong(left_offset, left_sets, right_offset, right_sets)
    right_better = _at_least_as_strong(right_offset, right_sets, left_offset, left_sets)
    if left_better and right_better:
        return "equivalent", ["all declared profile bounds are equal"]
    if left_better:
        return "dominates", ["left has no larger offset and no broader permissions"]
    if right_better:
        return "dominated", ["right has no larger offset and no broader permissions"]
    return "incomparable", ["profile improvements trade off across the required tuple"]


def compare_contracts(left: Any, right: Any) -> dict[str, Any]:
    """Compare validated profile records using declared structural guarantees."""
    left_checked = validate_contract(left)
    right_checked = validate_contract(right)
    relation, reasons = _relation(left_checked, right_checked)
    return {
        "relation": relation,
        "reasons": reasons,
        "authority": "profile-structural",
        "mathematicalFalsity": "not-established",
    }
