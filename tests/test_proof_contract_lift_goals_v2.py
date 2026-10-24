"""Independent red contract for the bounded Nat/rational lift planner."""

import re
from copy import deepcopy

import pytest

from ladon.proof_contract_lift_goals import plan_nat_rational_lift

GOAL = {
    "variables": ["x"],
    "premises": [
        {"op": "ge", "left": {"var": "x"}, "right": {"rat": 0}},
        {"op": "lt", "left": {"var": "x"}, "right": {"rat": 2}},
    ],
    "conclusion": {"op": "eq", "left": {"var": "x"}, "right": {"rat": 0}},
}
WITNESS = {
    "id": "w-1",
    "status": "abstract-countermodel",
    "assignment": {"x": "1"},
}
INTERPRETATION = {
    "profile": "nat-cast-v1",
    "source": {"path": "Fixture/Lift.lean", "sha256": "a" * 64},
    "formalClaim": "Fixture.claim",
    "formalPredicate": "Fixture.predicate",
}


def _texts(value):
    """Collect generated text without prescribing a presentation wrapper."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _texts(item)]
    if isinstance(value, list):
        return [text for item in value for text in _texts(item)]
    return []


def _plan(goal=GOAL, witness=WITNESS, interpretation=INTERPRETATION, mode="realization"):
    return plan_nat_rational_lift(goal, witness, interpretation, mode=mode)


def test_realization_binds_all_assumptions_and_exact_natural_witness():
    result = _plan()
    texts = "\n".join(_texts(result["components"]))

    _assert_plan_bindings(result)
    _assert_realization_text(result, texts)


def _assert_plan_bindings(result):
    assert result["schema"]
    assert result["status"] == "planned"
    assert result["goalInput"] == GOAL
    assert result["witness"] == WITNESS
    assert result["interpretation"] == INTERPRETATION
    assert result["mode"] == "realization"
    assert isinstance(result["goal"], str) and result["goal"]
    _assert_planning_authority(result)


def _assert_planning_authority(result):
    assert result["sourceVerified"] is False
    assert result["sourceFormulaFidelity"] == "unverified"
    assert result["originalClaimRefuted"] is False
    assert result["liftStatus"] == "pending-checks"


def _assert_realization_text(result, texts):
    assert "Fixture.claim" in texts and "Fixture.predicate" in texts
    mapping = "\n".join(_texts(result["components"]["objectMapping"]))
    outcome = "\n".join(_texts(result["components"]["outcome"]))
    refutation = "\n".join(_texts(result["components"]["formalRefutation"]))
    mapping = re.sub(r"\((-?\d+) : _root_\.Rat\)", r"\1", mapping)
    # Both assumptions must occur in the pointwise implication, together with its
    # conclusion; silently dropping either premise changes the source-to-object map.
    assert "≥ 0" in mapping or ">= 0" in mapping or "0 ≤" in mapping or "0 <=" in mapping
    assert "< 2" in mapping
    assert "= 0" in mapping
    assert "Nat" in outcome and "1" in outcome
    assert "Rat.ofInt" in outcome and "Int.ofNat" in outcome
    assert "Fixture.claim" in refutation
    assert "¬" in refutation or "not" in refutation.lower()


def test_realization_has_full_claim_mapping_and_exact_q_outcome():
    result = _plan()
    assert set(result["components"]) == {"fullClaimMapping", "objectMapping", "outcome", "formalRefutation"}
    full = "\n".join(_texts(result["components"]["fullClaimMapping"]))
    outcome = "\n".join(_texts(result["components"]["outcome"]))
    refutation = "\n".join(_texts(result["components"]["formalRefutation"]))
    # Check the three logically distinct obligations: source claim identity,
    # per-object predicate identity, and this witness's exact realization.
    assert "Fixture.claim" in full and "Fixture.predicate" in full
    assert "↔" in full or "<->" in full or "iff" in full.lower()
    assert "∀" in full or "forall" in full.lower()
    assert "∃" in outcome or "exists" in outcome.lower()
    assert "Nat" in outcome
    assert "Fixture.claim" in refutation and ("¬" in refutation or "not" in refutation.lower())


def test_incompatibility_only_claims_this_rational_is_out_of_nat_range():
    result = _plan(mode="incompatibility")
    texts = "\n".join(_texts(result["components"]))
    assert set(result["components"]) == {"fullClaimMapping", "objectMapping", "outcome"}
    assert result["status"] == "planned"
    assert "¬" in texts or "not" in texts.lower()
    assert "∃" in texts or "exists" in texts.lower()
    assert "Nat" in texts
    assert "Rat.ofInt" in texts and "Int.ofNat" in texts
    assert "formalRefutation" not in result["components"]


def test_witness_assignment_must_really_refute_implication():
    false_witness = deepcopy(WITNESS)
    false_witness["assignment"] = {"x": "0"}  # satisfies the conclusion
    with pytest.raises(ValueError):
        _plan(witness=false_witness)

    premise_violating = deepcopy(WITNESS)
    premise_violating["assignment"] = {"x": "3"}  # fails x < 2
    with pytest.raises(ValueError):
        _plan(witness=premise_violating)


def test_plan_identity_changes_when_any_bound_input_changes():
    base = _plan()
    variants = []
    for field, value in (("path", "Fixture/Other.lean"), ("sha256", "b" * 64)):
        altered = deepcopy(INTERPRETATION)
        altered["source"][field] = value
        variants.append(_plan(interpretation=altered))
    altered = deepcopy(INTERPRETATION)
    altered["formalClaim"] = "Other.claim"
    variants.append(_plan(interpretation=altered))
    altered_goal = deepcopy(GOAL)
    altered_goal["premises"].append(
        {"op": "ne", "left": {"var": "x"}, "right": {"rat": 4}}
    )
    variants.append(_plan(goal=altered_goal))
    altered_witness = deepcopy(WITNESS)
    altered_witness["id"] = "w-2"
    variants.append(_plan(witness=altered_witness))
    variants.append(_plan(mode="incompatibility"))

    assert len({base["planId"], *(item["planId"] for item in variants)}) == 1 + len(variants)
    assert base["planId"] == _plan()["planId"]


def test_unsupported_profile_and_division_are_explicit_and_nonpositive():
    unsupported_profile = deepcopy(INTERPRETATION)
    unsupported_profile["profile"] = "analytic-v9"
    result = _plan(interpretation=unsupported_profile)
    assert result["status"] == "unsupported"
    assert result["witness"] == WITNESS
    assert result["goal"] is None
    assert result["components"] == {}
    assert result.get("originalClaimRefuted") is False
    assert result.get("liftStatus") == "unsupported"
    assert result.get("reason")



def test_division_is_explicit_and_nonpositive():
    division_goal = deepcopy(GOAL)
    division_goal["conclusion"]["left"] = {
        "op": "div", "args": [{"var": "x"}, {"rat": 2}]
    }
    division_result = _plan(goal=division_goal)
    assert division_result["status"] == "unsupported"
    assert division_result["witness"] == WITNESS
    assert division_result["goal"] is None
    assert division_result["components"] == {}
    assert division_result.get("originalClaimRefuted") is False


def test_input_shapes_are_native_exact_and_safe():
    with pytest.raises(ValueError):
        _plan(witness={**WITNESS, "extra": "ignored?"})
    with pytest.raises(ValueError):
        _plan(interpretation={**INTERPRETATION, "extra": True})
    with pytest.raises(ValueError):
        _plan(mode="anything-else")
    with pytest.raises(ValueError):
        _plan(interpretation={**INTERPRETATION, "source": {"path": "../escape", "sha256": "a" * 64}})
    with pytest.raises(ValueError):
        _plan(interpretation={**INTERPRETATION, "source": {"path": "\\absolute", "sha256": "a" * 64}})
    with pytest.raises(ValueError):
        _plan(interpretation={**INTERPRETATION, "formalPredicate": "Fixture.predicate := by sorry"})

    oversized = deepcopy(WITNESS)
    oversized["id"] = "w" * (1024 * 1024)
    with pytest.raises(ValueError):
        _plan(witness=oversized)

    tuple_witness = deepcopy(WITNESS)
    tuple_witness["assignment"]["x"] = ("1",)
    with pytest.raises(ValueError, match="JSON-native"):
        _plan(witness=tuple_witness)


def test_variable_free_and_multiple_variable_goals_are_unsupported():
    no_variables = {
        "variables": [], "premises": [],
        "conclusion": {"op": "eq", "left": {"rat": 0}, "right": {"rat": 1}},
    }
    no_variable_witness = {**WITNESS, "assignment": {}}
    result = _plan(goal=no_variables, witness=no_variable_witness)
    assert result["status"] == "unsupported"
    assert result["witness"] == no_variable_witness

    two_variables = deepcopy(GOAL)
    two_variables["variables"] = ["x", "y"]
    two_variables["conclusion"] = {
        "op": "eq", "left": {"var": "x"}, "right": {"var": "y"}
    }
    two_witness = deepcopy(WITNESS)
    two_witness["assignment"] = {"x": "1", "y": "0"}
    result = _plan(goal=two_variables, witness=two_witness)
    assert result["status"] == "unsupported"
    assert result["witness"] == two_witness


def test_plan_does_not_mutate_inputs_and_representation_remains_bound():
    goal, witness, interpretation = deepcopy(GOAL), deepcopy(WITNESS), deepcopy(INTERPRETATION)
    before = deepcopy((goal, witness, interpretation))
    first = _plan(goal, witness, interpretation)
    assert (goal, witness, interpretation) == before
    witness["assignment"]["x"] = "2/2"
    second = _plan(goal, witness, interpretation)
    assert first["components"] == second["components"]
    assert first["planId"] != second["planId"]
    assert first["witness"] == WITNESS


@pytest.mark.parametrize("name", ["", "A; sorry", "_root_.A", "A\n", "A" * 257])
def test_formal_identifiers_cannot_inject_source(name):
    with pytest.raises(ValueError):
        _plan(interpretation={**INTERPRETATION, "formalClaim": name})


@pytest.mark.parametrize("path", ["", "/tmp/Lift.lean", "a/../b", "a/./b", "a//b"])
def test_source_path_must_be_canonical_relative(path):
    with pytest.raises(ValueError):
        _plan(interpretation={**INTERPRETATION, "source": {"path": path, "sha256": "a" * 64}})


def test_dictionary_subclass_cannot_be_normalized_into_trusted_input():
    class Fake(dict):
        pass

    with pytest.raises(ValueError, match="JSON-native"):
        _plan(witness=Fake(WITNESS))
