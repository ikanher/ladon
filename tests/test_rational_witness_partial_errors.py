"""A session can retain checked prefixes when a later evaluation is undefined."""

import pytest

from ladon import rational_witness as rational


def _reciprocal_goal(op):
    return {"variables": ["x"], "premises": [], "conclusion": {
        "op": op, "left": {"op": "div", "args": [{"rat": 1}, {"var": "x"}]},
        "right": {"rat": 1},
    }}


def test_search_retains_completed_prefix_and_invalid_attempt_when_requested():
    goal, candidates = _reciprocal_goal("ge"), {"x": [1, 0, -1]}
    with pytest.raises(ValueError, match="division by zero"):
        rational.search_candidates(goal, candidates)
    result = rational.search_candidates(goal, candidates, capture_invalid=True)
    assert result["status"] == "invalid-input"
    assert result["attemptedCount"] == 2
    assert result["trace"][0] == {"assignment": {"x": "1"}, "status": "not-counterexample"}
    assert result["trace"][1]["assignment"] == {"x": "0"}
    assert result["trace"][1]["status"] == "invalid-input"


def test_minimizer_retains_initial_witness_when_predecessor_is_undefined():
    goal, candidates = _reciprocal_goal("lt"), {"x": [0, 1]}
    with pytest.raises(ValueError, match="division by zero"):
        rational.minimize_counterexample(goal, candidates, {"x": 1})
    result = rational.minimize_counterexample(
        goal, candidates, {"x": 1}, capture_invalid=True,
    )
    assert result["status"] == "invalid-input"
    assert result["assignment"] == {"x": "1"}
    assert result["assignmentChecked"] is True
    assert result["attemptCount"] == 1
    assert result["minimality"] is False
    assert result["trace"][0]["assignment"] == {"x": "0"}
    assert result["trace"][0]["result"] == "invalid-input"
