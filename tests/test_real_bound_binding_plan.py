"""Exact application plans are immutable obligations, never caller admission."""

from copy import deepcopy

import pytest
from test_real_bound_observation import ROOT


@pytest.fixture(scope="module")
def bound_snapshot():
    from ladon.proof_contract_formal import produce_formal_snapshot

    return produce_formal_snapshot(ROOT, "NamedBound.lean", "NamedBound", "namedEstimate")


def observed(value):
    from ladon.real_bound_observation import observe_bound_snapshot

    return observe_bound_snapshot(value, ROOT)


def plan(observation, measure=None):
    from ladon.real_bound_binding import plan_bound_prefix

    return plan_bound_prefix(observation, measure or {"declaration": "Other.sample", "arguments": []})


def test_binding_plan_retains_exact_observation_and_remains_unadmitted(bound_snapshot):
    observation = observed(bound_snapshot)
    result = plan(observation)
    assert result["observation"] == observation
    assert result["contract"] is None
    assert result["admission"] == "unresolved"
    assert result["status"] == "planned"
    assert result["goals"][0]["id"] == "predicate-admission"
    assert "namedEstimate" in result["goals"][0]["proposition"]
    changed = deepcopy(observation)
    changed["statementSnapshot"]["selection"]["declaration"] = "Other.estimate"
    assert plan(changed)["planId"] != result["planId"]
    result["observation"]["candidate"]["loss"] = 42
    assert observation["candidate"]["loss"] == 7


@pytest.mark.parametrize("measure", [
    {"declaration": "x) --", "arguments": []},
    {"declaration": "Other.sample", "arguments": ["b999"]},
    {"declaration": "Other.sample", "arguments": [True]},
    {"declaration": "Other.sample", "arguments": [], "admitted": True},
    {"declaration": "Other.sample", "arguments": "b0"},
])
def test_unchecked_measure_terms_and_claims_are_rejected(bound_snapshot, measure):
    with pytest.raises(ValueError):
        plan(observed(bound_snapshot), measure)


def test_unsupported_observation_cannot_plan_laws(bound_snapshot):
    observation = observed(bound_snapshot)
    observation.update(status="unsupported", candidate=None)
    with pytest.raises(ValueError, match="observed|candidate"):
        plan(observation)


def test_exact_measure_application_is_part_of_identity(bound_snapshot):
    observation = observed(bound_snapshot)
    first = plan(observation)
    second = plan(observation, {"declaration": "Other.sample", "arguments": ["b0"]})
    assert first["planId"] != second["planId"]


@pytest.mark.parametrize("field,value", [("admission", "checked"), ("contract", {}),
                                        ("status", "checked-binding")])
def test_rehashed_claim_cannot_launch_checker(bound_snapshot, tmp_path, field, value):
    from ladon.real_bound_binding_check import check_bound_prefix

    supplied = plan(observed(bound_snapshot))
    supplied[field] = value
    with pytest.raises(ValueError, match="plan|stale"):
        check_bound_prefix(tmp_path, supplied, "by trivial")
