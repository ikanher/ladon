"""Native admission needs the exact source predicate and canonical Real scalars."""

from copy import deepcopy

import pytest
from test_real_bound_observation import ROOT


@pytest.fixture(scope="module")
def native_binding():
    from ladon.derivative_prefix import plan_derivative_prefix
    from ladon.proof_contract_formal import produce_formal_snapshot
    from ladon.real_bound_observation import observe_bound_snapshot

    snapshot = produce_formal_snapshot(ROOT, "NamedBound.lean", "NamedBound", "namedEstimate")
    return plan_derivative_prefix(observe_bound_snapshot(snapshot, ROOT))


def native_plan(binding):
    from ladon.real_bound_native_plan import plan_real_bound

    return plan_real_bound(binding)


def test_native_plan_requires_two_distinct_checks_without_admitting(native_binding):
    result = native_plan(native_binding)
    assert result["schema"] == "ladon-real-bound-admission-plan-v1"
    assert result["admission"] == "unresolved"
    assert result["contract"] is None
    assert [row["id"] for row in result["goals"]] == ["predicate-admission", "scalar-semantics"]
    assert result["bindingPlan"] == native_binding
    assert result["bindingPlan"]["observation"]["candidate"]["loss"] == 7


@pytest.mark.parametrize("field,value", [("admission", "checked"), ("contract", {}),
                                        ("scalarSourceDigest", "sha256:" + "0" * 64)])
def test_unchecked_native_claims_reject_before_worker(native_binding, tmp_path, field, value):
    from ladon.real_bound_native_check import check_real_bound

    value_plan = native_plan(native_binding)
    value_plan[field] = value
    with pytest.raises(ValueError, match="plan|stale"):
        check_real_bound(tmp_path, value_plan, {"predicate-admission": "by trivial",
                                              "scalar-semantics": "by trivial"})


def test_predicate_only_evidence_cannot_admit_native_contract(native_binding, tmp_path):
    from ladon.real_bound_native_check import check_real_bound

    with pytest.raises(ValueError, match="term|proof"):
        check_real_bound(tmp_path, native_plan(native_binding), {"predicate-admission": "by trivial"})


def test_rehashed_source_shape_cannot_become_a_native_fact(native_binding):
    changed = deepcopy(native_binding)
    changed["observation"]["candidate"]["loss"] = 99
    with pytest.raises(ValueError, match="shape|candidate|plan"):
        native_plan(changed)
