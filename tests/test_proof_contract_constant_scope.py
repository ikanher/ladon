"""A quantified estimate constant has its own explicit choice point."""

import pytest
from support.proof_contract_native import contract_record

from ladon.proof_contracts import compare_contracts, validate_contract


def with_constant(*, before_parameter=False):
    value = contract_record()
    binder = {"binderId": "constant", "typeId": "Nat", "quantifier": "exists"}
    value["telescope"].insert(0 if before_parameter else 1, binder)
    value["features"]["constantDependencies"]["binderId"] = "constant"
    value["features"]["witnessDependencies"] = [{
        "binderId": "constant", "state": "known",
        "allowedBinderIds": [] if before_parameter else ["u"], "reason": None,
    }]
    return value


def test_anchored_constant_can_depend_on_an_earlier_parameter():
    value = with_constant()
    assert validate_contract(value) == value


def test_constant_cannot_depend_on_a_parameter_after_its_choice_point():
    with pytest.raises(ValueError):
        validate_contract(with_constant(before_parameter=True))


def test_unknown_relation_between_explicit_and_implicit_constant_choice():
    anchored = with_constant()
    implicit = with_constant()
    del implicit["features"]["constantDependencies"]["binderId"]
    assert compare_contracts(anchored, implicit)["relation"] == "unknown"


def test_explicit_constant_anchor_alpha_renames_by_scope():
    left, right = with_constant(), with_constant()
    right["telescope"][1]["binderId"] = "renamed"
    right["features"]["constantDependencies"]["binderId"] = "renamed"
    right["features"]["witnessDependencies"][0]["binderId"] = "renamed"
    assert compare_contracts(left, right)["relation"] == "equivalent"


def test_two_known_summaries_of_the_same_constant_must_use_the_same_permission_set():
    value = with_constant()
    value["features"]["witnessDependencies"][0]["allowedBinderIds"] = []
    with pytest.raises(ValueError, match="constant.*witness"):
        validate_contract(value)
