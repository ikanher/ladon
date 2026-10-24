"""Frozen contract tests for a single-deadline rational witness session."""

import pytest

from ladon import rational_witness


def _goal(*, threshold=3):
    return {
        "variables": ["x"],
        "premises": [],
        "conclusion": {
            "op": "ge",
            "left": {"var": "x"},
            "right": {"rat": threshold},
        },
    }


def _clock_expiring_after_checks(monkeypatch, check_count, *, deadline=10.0):
    """Expose a monotonic clock that expires at the next poll after N checks."""
    original_check = rational_witness.check_witness
    completed_checks = 0

    def counted_check(goal, assignment):
        nonlocal completed_checks
        result = original_check(goal, assignment)
        completed_checks += 1
        return result

    monkeypatch.setattr(rational_witness, "check_witness", counted_check)
    monkeypatch.setattr(
        rational_witness,
        "_monotonic",
        lambda: deadline if completed_checks >= check_count else 0.0,
    )


def _session(goal, candidates, **kwargs):
    return rational_witness.run_rational_witness_session(
        goal, candidates, deadline_monotonic=rational_witness._monotonic() + 10.0, **kwargs
    )


def _assert_complete_search(result, status, count, assignments):
    search = result["candidateSearch"]
    assert result["schema"] == "ladon-rational-witness-session-v1"
    assert result["status"] == status
    assert search["status"] == status
    assert search["attemptedCount"] == count
    assert search["familySize"] == count
    _assert_trace_assignments(search, assignments)
    assert result["minimization"] is None
    _assert_count_bounds(result, rounds=1, candidates=count, reductions=0)


def _assert_trace_assignments(search, assignments):
    assert [row["assignment"] for row in search["trace"]] == assignments


def _assert_count_bounds(result, rounds, candidates, reductions):
    assert result["roundCount"] == rounds
    assert result["roundLimit"] == 1
    assert result["roundsSupported"] is False
    assert result["candidateChecks"] == candidates
    assert result["reductionAttempts"] == reductions


def _assert_partial_search(result, status, count, family_size, assignments):
    search = result["candidateSearch"]
    assert result["status"] == status
    assert search["status"] == status
    assert search["attemptedCount"] == count
    assert search["familySize"] == family_size
    assert [row["assignment"] for row in search["trace"]] == assignments
    assert result["minimization"] is None
    assert result["candidateChecks"] == count


def test_complete_candidate_family_is_the_only_finite_survival_result():
    result = _session(_goal(threshold=0), {"x": [0, 1, 2]})
    _assert_complete_search(
        result, "survived-declared-scope", 3,
        [{"x": "0"}, {"x": "1"}, {"x": "2"}],
    )


def test_candidate_cap_exhaustion_keeps_exact_prefix_and_never_claims_survival():
    result = _session(
        _goal(threshold=0), {"x": [0, 1, 2]}, max_candidates=2
    )

    _assert_partial_search(
        result, "budget-exhausted", 2, 3, [{"x": "0"}, {"x": "1"}]
    )


def test_deadline_after_n_candidates_preserves_exact_prefix(monkeypatch):
    _clock_expiring_after_checks(monkeypatch, 2)

    result = _session(_goal(threshold=0), {"x": [0, 1, 2, 3]})

    _assert_partial_search(
        result, "deadline-exhausted", 2, 4, [{"x": "0"}, {"x": "1"}]
    )
    _assert_count_bounds(result, rounds=1, candidates=2, reductions=0)


def test_deadline_is_shared_by_search_and_minimization_and_retains_witness(monkeypatch):
    # The candidate check completes, then the shared absolute deadline expires
    # before the minimization stage is allowed to begin.
    _clock_expiring_after_checks(monkeypatch, 1)

    result = _session(_goal(threshold=2), {"x": [0, 1, 2, 3]}, max_reductions=4)

    _assert_before_minimization(result)


def _assert_before_minimization(result):
    search = result["candidateSearch"]
    minimization = result["minimization"]
    assert search["status"] == "abstract-countermodel"
    assert search["trace"] == [
        {"assignment": {"x": "0"}, "status": "counterexample"}
    ]
    assert result["status"] == "abstract-countermodel"
    assert minimization["status"] == "deadline-exhausted-before-start"
    assert minimization["initialAssignment"] == {"x": "0"}
    assert minimization["assignment"] == {"x": "0"}
    assert minimization["trace"] == []
    _assert_no_minimality(minimization)
    _assert_count_bounds(result, rounds=1, candidates=1, reductions=0)


def test_deadline_inside_minimization_keeps_every_completed_reduction(monkeypatch):
    # The first satisfying premise assignment is a counterexample after eight
    # family checks. Initial recheck plus two completed predecessor checks then
    # precede expiry, leaving a partial scan over three eligible coordinates.
    _clock_expiring_after_checks(monkeypatch, 11)
    goal = _three_variable_goal()
    result = _session(goal, {"x": [0, 1], "y": [0, 1], "z": [0, 1]}, max_reductions=8)
    _assert_minimization_deadline(result, goal)


def _three_variable_goal():
    return {
        "variables": ["x", "y", "z"],
        "premises": [
            {"op": "ge", "left": {"var": name}, "right": {"rat": 1}}
            for name in ("x", "y", "z")
        ],
        "conclusion": {
            "op": "ge",
            "left": {
                "op": "add",
                "args": [
                    {"op": "add", "args": [{"var": "x"}, {"var": "y"}]},
                    {"var": "z"},
                ],
            },
            "right": {"rat": 4},
        },
    }


def _assert_minimization_deadline(result, goal):
    minimization = result["minimization"]
    assert result["status"] == "abstract-countermodel"
    assert minimization["status"] == "deadline-exhausted"
    assert minimization["attemptCount"] == 2
    _assert_interrupted_reduction_trace(minimization)
    _assert_counterexample_assignment(minimization, goal)
    _assert_no_minimality(minimization)
    _assert_count_bounds(result, rounds=1, candidates=8, reductions=2)


def _assert_interrupted_reduction_trace(minimization):
    attempts = [row for row in minimization["trace"] if row.get("result") != "interrupted"]
    assert len(attempts) == 2
    assert all(row["result"] == "outside-assumptions" for row in attempts)
    assert minimization["trace"][-1] == {
        "result": "interrupted", "reason": "deadline-exhausted"
    }


def _assert_counterexample_assignment(minimization, goal):
    assignment = {"x": "1", "y": "1", "z": "1"}
    assert minimization["assignment"] == assignment
    checked = rational_witness.check_witness(goal, minimization["assignment"])
    assert checked["status"] == "counterexample"


def _assert_no_minimality(minimization):
    assert minimization["minimality"] is False
    assert minimization["minimalityScope"] is None


def test_completed_final_candidate_survives_even_when_clock_crosses_deadline(monkeypatch):
    # Expire immediately after the third and final family member is checked.
    _clock_expiring_after_checks(monkeypatch, 3)

    result = _session(_goal(threshold=0), {"x": [0, 1, 2]})

    assert result["candidateSearch"]["trace"] == [
        {"assignment": {"x": "0"}, "status": "not-counterexample"},
        {"assignment": {"x": "1"}, "status": "not-counterexample"},
        {"assignment": {"x": "2"}, "status": "not-counterexample"},
    ]
    assert result["candidateSearch"]["status"] == "survived-declared-scope"
    assert result["status"] == "survived-declared-scope"
    assert result["minimization"] is None


def test_already_expired_deadline_starts_no_candidate_round(monkeypatch):
    _clock_expiring_after_checks(monkeypatch, 0)

    result = rational_witness.run_rational_witness_session(
        _goal(), {"x": [0, 1]}, deadline_monotonic=10.0
    )

    assert result["status"] == "deadline-exhausted"
    assert result["candidateSearch"]["status"] == "deadline-exhausted"
    assert result["candidateSearch"]["attemptedCount"] == 0
    assert result["candidateSearch"]["trace"] == []
    assert result["candidateChecks"] == 0
    assert result["roundCount"] == 0
    assert result["roundLimit"] == 1
    assert result["roundsSupported"] is False


@pytest.mark.parametrize("deadline", [True, False, float("nan"), float("inf"), float("-inf"), "10", None])
def test_deadline_must_be_finite_numeric_and_not_boolean(deadline):
    with pytest.raises(ValueError):
        rational_witness.run_rational_witness_session(
            _goal(), {"x": [0, 1]}, deadline_monotonic=deadline
        )


@pytest.mark.parametrize("cap", [0, -1, 257, True, 1.5, "2"])
def test_candidate_caps_retain_existing_strict_integer_bounds(cap):
    with pytest.raises(ValueError):
        _session(_goal(), {"x": [0, 1]}, max_candidates=cap)


@pytest.mark.parametrize("cap", [0, -1, 33, True, 1.5, "2"])
def test_reduction_caps_retain_existing_strict_integer_bounds(cap):
    with pytest.raises(ValueError):
        _session(_goal(threshold=2), {"x": [0, 1, 2]}, max_reductions=cap)
