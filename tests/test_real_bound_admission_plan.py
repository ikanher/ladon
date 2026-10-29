"""Closed source-bound prefix-law plans cannot be mistaken for checked admission."""

from copy import deepcopy

import pytest


def request():
    return {"source": {"path": "PrefixExamples.lean", "sha256": "a" * 64},
            "environmentRef": "sha256:" + "b" * 64,
            "predicate": "SequenceBounds.envelope", "measure": "SequenceBounds.sample",
            "objectType": "SequenceBounds.Object", "parameterType": "Nat", "pointType": "Unit"}


def plan(value=None):
    from ladon.real_bound_admission import plan_prefix_admission

    return plan_prefix_admission(request() if value is None else value)


def test_plan_keeps_three_exact_closed_goals_and_no_admission():
    result = plan()
    assert result["status"] == "planned"
    assert result["admission"] == "unresolved"
    assert result["contract"] is None
    assert [row["id"] for row in result["goals"]] == ["predicate-equivalence", "order-prefix", "bound-monotonicity"]
    assert all("_root_.SequenceBounds.envelope" in row["proposition"] for row in result["goals"])
    assert "_root_.SequenceBounds.sample" in result["goals"][0]["proposition"]
    assert result["request"] == request()
    assert result["requiredImport"] == "LadonRealBound"


def test_unrelated_names_change_the_exact_goal_and_plan_identity():
    first = plan()
    other = request()
    other.update(predicate="Polynomial.PartialBound", measure="Polynomial.evaluate",
                 objectType="Polynomial.Coefficients")
    second = plan(other)
    assert first["planId"] != second["planId"]
    assert "_root_.Polynomial.PartialBound" in second["goals"][0]["proposition"]


@pytest.mark.parametrize("field,value", [("predicate", "x) ∨ True --"),
                                        ("measure", "by trivial"), ("pointType", "Unit\naxiom bad : False"),
                                        ("environmentRef", "unknown")])
def test_unchecked_terms_and_malformed_identities_cannot_enter_goals(field, value):
    changed = request()
    changed[field] = value
    with pytest.raises(ValueError):
        plan(changed)


@pytest.mark.parametrize("field", ["admitted", "lawsChecked", "goal", "proofReceipt"])
def test_caller_cannot_supply_acceptance_or_replace_the_expected_goal(field):
    changed = request()
    changed[field] = True
    with pytest.raises(ValueError):
        plan(changed)


def test_plan_is_detached_and_source_identity_changes_invalidate_it():
    original = request()
    frozen = deepcopy(original)
    result = plan(original)
    result["request"]["source"]["path"] = "changed"
    assert original == frozen
    original["source"]["sha256"] = "c" * 64
    assert plan(original)["planId"] != plan(frozen)["planId"]
