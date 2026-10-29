"""Derivative plans bind an observation and fixed semantics without caller authority."""

from copy import deepcopy

import pytest
from test_real_bound_observation import ROOT


@pytest.fixture(scope="module")
def derivative_observation():
    from ladon.proof_contract_formal import produce_formal_snapshot
    from ladon.real_bound_observation import observe_bound_snapshot

    snapshot = produce_formal_snapshot(ROOT, "NamedBound.lean", "NamedBound", "namedEstimate")
    return observe_bound_snapshot(snapshot, ROOT)


def plan(value):
    from ladon.derivative_prefix import plan_derivative_prefix

    return plan_derivative_prefix(value)


def _assert_unadmitted_plan(result):
    assert result["schema"] == "ladon-derivative-prefix-plan-v1"
    assert result["status"] == "planned"
    assert result["admission"] == "unresolved"
    assert result["contract"] is None


def test_fixed_adapter_plan_preserves_full_observation_and_loss(derivative_observation):
    value = derivative_observation
    result = plan(value)
    _assert_unadmitted_plan(result)
    assert result["observation"] == value
    assert result["observation"]["candidate"]["loss"] == 7
    assert result["derivativeProfile"]["profileId"] == "joint-real-frechet-prefix-v1"
    assert result["paperNormBridge"] == "unresolved"
    assert "measure" not in result
    assert "namedEstimate" in result["goals"][0]["proposition"]
    result["observation"]["candidate"]["loss"] = 0
    assert value["candidate"]["loss"] == 7


@pytest.mark.parametrize("field,value", [("admission", "checked"), ("contract", {}),
                                        ("paperNormBridge", "checked"), ("derivativeSourceDigest", "fake")])
def test_caller_cannot_promote_or_replace_adapter(derivative_observation, tmp_path, field, value):
    from ladon.real_bound_binding_check import check_bound_prefix

    supplied = plan(derivative_observation)
    supplied[field] = value
    with pytest.raises(ValueError, match="plan|stale"):
        check_bound_prefix(tmp_path, supplied, "by trivial")


def test_replacement_goal_is_rejected_before_worker(derivative_observation, tmp_path):
    from ladon.real_bound_binding_check import check_bound_prefix

    supplied = plan(derivative_observation)
    supplied["goals"][0]["proposition"] = "True"
    with pytest.raises(ValueError, match="plan|stale"):
        check_bound_prefix(tmp_path, supplied, "by trivial")


def test_unsupported_shape_has_no_derivative_plan(derivative_observation):
    value = deepcopy(derivative_observation)
    value.update(status="unsupported", candidate=None)
    with pytest.raises(ValueError, match="observed|candidate"):
        plan(value)


def test_rehashed_shape_edit_cannot_change_loss(derivative_observation):
    value = deepcopy(derivative_observation)
    value["candidate"]["loss"] = 4
    with pytest.raises(ValueError, match="shape|candidate"):
        plan(value)


@pytest.mark.parametrize("timeout", [0, float("inf"), True])
def test_derivative_check_retains_budget_validation(derivative_observation, tmp_path, timeout):
    from ladon.real_bound_binding_check import check_bound_prefix

    with pytest.raises(ValueError, match="timeout|budget"):
        check_bound_prefix(tmp_path, plan(derivative_observation), "by trivial", timeout_seconds=timeout)
