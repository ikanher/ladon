"""Red acceptance proposals for the bounded contract record/comparator.

These live outside the product test tree. The shared production implementation
is root-owned; the proposals intentionally target the frozen API recorded on
the proof-contract board.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from ladon.proof_contracts import compare_contracts, validate_contract


def record(**changes):
    value = {
        "profileId": "norm-scale-v1",
        "endpointId": "endpoint:estimate",
        "context": {
            "objectId": "object:operator-f",
            "domainId": "domain:all-inputs",
            "scaleId": "scale:C1",
            "representationId": "repr:canonical",
        },
        "telescope": [
            {"binderId": "x", "typeId": "type:X", "quantifier": "forall"},
            {"binderId": "c", "typeId": "type:Nat", "quantifier": "exists"},
        ],
        "assumptions": [{"predicateId": "predicate:input-valid"}],
        "conclusionId": "conclusion:estimate",
        "features": {
            "regularity": {
                "state": "known",
                "scaleId": "scale:C1",
                "offset": 2,
                "reason": None,
            },
            "constantDependencies": {
                "state": "known",
                "allowedBinderIds": ["x"],
                "reason": None,
            },
            "witnessDependencies": [
                {
                    "binderId": "c",
                    "state": "known",
                    "allowedBinderIds": ["x"],
                    "reason": None,
                }
            ],
        },
    }
    value.update(changes)
    return value


def _relation(left, right):
    return compare_contracts(left, right)["relation"]


def test_validator_returns_detached_closed_record():
    source = record()
    validated = validate_contract(source)
    assert validated == source
    assert validated is not source
    assert validated["features"] is not source["features"]

    extra = deepcopy(source)
    extra["unreviewedMeaning"] = "must not be silently accepted"
    with pytest.raises(ValueError):
        validate_contract(extra)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: c["telescope"].append(
            {"binderId": "x", "typeId": "type:Y", "quantifier": "forall"}
        ),
        lambda c: c["features"]["constantDependencies"].update(
            allowedBinderIds=["not-in-scope"]
        ),
        lambda c: c["features"]["witnessDependencies"][0].update(
            allowedBinderIds=["c"]
        ),
        lambda c: c["features"]["regularity"].update(offset=-1),
        lambda c: c["features"]["regularity"].update(offset=True),
        lambda c: c["features"]["regularity"].update(unreviewedState="certain"),
        lambda c: c["features"]["regularity"].update(state="unknown", offset=None),
        lambda c: c["features"]["constantDependencies"].update(
            state="unknown", allowedBinderIds=[], reason="not captured"
        ),
    ],
)
def test_malformed_scope_or_state_is_rejected(mutation):
    candidate = record()
    mutation(candidate)
    with pytest.raises(ValueError):
        validate_contract(candidate)


def test_known_empty_dependency_permission_is_not_unknown():
    known_empty = record()
    known_empty["features"]["constantDependencies"]["allowedBinderIds"] = []
    unknown = record()
    unknown["features"]["constantDependencies"] = {
        "state": "unknown",
        "allowedBinderIds": None,
        "reason": "source did not state uniformity",
    }

    checked_empty = validate_contract(known_empty)
    checked_unknown = validate_contract(unknown)
    assert checked_empty != checked_unknown
    assert checked_empty["features"]["constantDependencies"]["allowedBinderIds"] == []
    assert checked_unknown["features"]["constantDependencies"]["allowedBinderIds"] is None
    assert _relation(checked_empty, checked_unknown) == "unknown"


def test_unknown_regular_feature_cannot_be_used_to_claim_dominance():
    known = record()
    unknown = record()
    unknown["features"]["regularity"] = {
        "state": "unknown",
        "scaleId": "scale:C1",
        "offset": None,
        "reason": "interpretation omitted the estimate loss",
    }
    assert _relation(known, unknown) == "unknown"
    assert _relation(unknown, known) == "unknown"


def test_unsupported_witness_dependency_is_retained_and_stays_unknown():
    unsupported = record()
    unsupported["features"]["witnessDependencies"][0] = {
        "binderId": "c",
        "state": "unsupported",
        "allowedBinderIds": None,
        "reason": "opaque witness construction",
    }
    checked = validate_contract(unsupported)
    assert checked["features"]["witnessDependencies"][0]["allowedBinderIds"] is None
    assert _relation(checked, validate_contract(record())) == "unknown"


def test_comparator_preserves_correlated_route_tradeoff():
    lower_loss_route = record()
    lower_loss_route["features"]["regularity"]["offset"] = 3
    lower_loss_route["features"]["constantDependencies"]["allowedBinderIds"] = ["x"]
    lower_loss_route["features"]["witnessDependencies"][0]["allowedBinderIds"] = ["x"]

    more_independent_route = record()
    more_independent_route["features"]["regularity"]["offset"] = 5
    more_independent_route["features"]["constantDependencies"]["allowedBinderIds"] = []
    more_independent_route["features"]["witnessDependencies"][0]["allowedBinderIds"] = []

    assert _relation(lower_loss_route, more_independent_route) == "incomparable"
    assert _relation(more_independent_route, lower_loss_route) == "incomparable"


def test_dominance_requires_the_whole_tuple_to_improve():
    better = record()
    better["features"]["regularity"]["offset"] = 3
    better["features"]["constantDependencies"]["allowedBinderIds"] = []
    better["features"]["witnessDependencies"][0]["allowedBinderIds"] = []
    worse = record()
    worse["features"]["regularity"]["offset"] = 5

    assert _relation(better, worse) == "dominates"
    assert _relation(worse, better) == "dominated"


def test_binder_alpha_renaming_preserves_semantics_but_not_source_record():
    original = validate_contract(record())
    renamed_value = record()
    renamed_value["telescope"] = [
        {"binderId": "arg", "typeId": "type:X", "quantifier": "forall"},
        {"binderId": "constant", "typeId": "type:Nat", "quantifier": "exists"},
    ]
    renamed_value["features"]["constantDependencies"]["allowedBinderIds"] = ["arg"]
    renamed_value["features"]["witnessDependencies"][0].update(
        binderId="constant", allowedBinderIds=["arg"]
    )
    renamed = validate_contract(renamed_value)
    assert renamed["telescope"][0]["binderId"] == "arg"
    assert _relation(original, renamed) == "equivalent"


@pytest.mark.parametrize(
    "field,value", [("endpointId", "endpoint:other")]
)
def test_incompatible_endpoint_or_scale_is_unknown_without_checked_bridge(field, value):
    left = validate_contract(record())
    right_source = record(**{field: value})
    right = validate_contract(right_source)
    assert _relation(left, right) == "unknown"
    assert _relation(right, left) == "unknown"


def test_different_scale_context_is_unknown_without_checked_bridge():
    left = validate_contract(record())
    right_source = record()
    right_source["context"]["scaleId"] = "scale:C2"
    right_source["features"]["regularity"]["scaleId"] = "scale:C2"
    right = validate_contract(right_source)
    assert _relation(left, right) == "unknown"
    assert _relation(right, left) == "unknown"


def test_regular_feature_scale_must_match_its_contract_context():
    candidate = record()
    candidate["context"]["scaleId"] = "scale:C2"
    with pytest.raises(ValueError):
        validate_contract(candidate)
