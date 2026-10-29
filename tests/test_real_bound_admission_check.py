"""Admission checks reject unowned source/plan/terms before launching a worker."""

from copy import deepcopy

import pytest
from test_real_bound_admission_plan import plan


def check(root, supplied=None, terms=None, **options):
    from ladon.real_bound_admission_check import check_prefix_admission

    return check_prefix_admission(root, plan() if supplied is None else supplied,
                                  {} if terms is None else terms, **options)


@pytest.mark.parametrize("field,value", [("admission", "checked"), ("status", "admitted"),
                                        ("familySourceDigest", "sha256:" + "0" * 64)])
def test_mutated_plan_is_rejected_before_execution(tmp_path, field, value):
    supplied = deepcopy(plan())
    supplied[field] = value
    with pytest.raises(ValueError, match="plan|stale"):
        check(tmp_path, supplied)


def test_caller_cannot_replace_generated_proposition(tmp_path):
    supplied = plan()
    supplied["goals"][0]["proposition"] = "True"
    with pytest.raises(ValueError, match="plan|stale"):
        check(tmp_path, supplied)


@pytest.mark.parametrize("terms", [{}, {"predicate-equivalence": "by trivial"},
                                   {"predicate-equivalence": "by trivial", "order-prefix": "by trivial",
                                    "bound-monotonicity": "by trivial", "admitted": True}])
def test_missing_or_extra_proof_entries_are_invalid(tmp_path, terms):
    with pytest.raises(ValueError, match="term|proof"):
        check(tmp_path, terms=terms)


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf")])
def test_invalid_shared_budget_cannot_start_work(tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout|budget"):
        check(tmp_path, timeout_seconds=timeout)
