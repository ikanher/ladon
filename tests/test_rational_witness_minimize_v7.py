"""Contract tests for declared-relation rational witness minimization."""

import pytest

from ladon.rational_witness import check_witness, minimize_counterexample


def _goal():
    return {
        "variables": ["x", "y"],
        "premises": [
            {"op": "ge", "left": {"var": "x"}, "right": {"rat": 1}},
            {"op": "ge", "left": {"var": "y"}, "right": {"rat": 1}},
        ],
        "conclusion": {
            "op": "ge",
            "left": {"op": "add", "args": [{"var": "x"}, {"var": "y"}]},
            "right": {"rat": 8},
        },
    }


def _domains():
    # Deliberately ordered and non-symmetric so coordinate order is observable.
    return {"x": [0, 1, 2, 3], "y": [0, 1, 2, 3]}


def _rank_sum(assignment, domains):
    return sum(
        next(i for i, candidate in enumerate(domains[name]) if str(candidate) == value)
        for name, value in assignment.items()
    )


def _assert_predecessor(row, current, proposed, domains):
    changed = [name for name in current if current[name] != proposed[name]]
    assert len(changed) == 1
    variable = changed[0]
    index = next(i for i, value in enumerate(domains[variable]) if str(value) == current[variable])
    assert proposed[variable] == str(domains[variable][index - 1])
    assert row["measureAfter"] < row["measureBefore"]
    assert row["measureBefore"] == _rank_sum(current, domains)
    assert row["measureAfter"] == _rank_sum(proposed, domains)


def _assert_attempt(row, current, goal, domains):
    assert row["assignmentBefore"] == current
    proposed = row["assignment"]
    _assert_predecessor(row, current, proposed, domains)
    replay = check_witness(goal, proposed)
    if row["accepted"]:
        assert replay["status"] == "counterexample"
        return proposed
    assert replay["status"] != "counterexample"
    return current


def _assert_trace(result, goal, domains):
    current = result["initialAssignment"]
    for row in result["trace"]:
        current = _assert_attempt(row, current, goal, domains)
    assert current == result["assignment"]


def _assert_complete_final_scan(result):
    final_scan = [row for row in result["trace"] if row["assignmentBefore"] == result["assignment"]]
    assert [row["variable"] for row in final_scan] == ["x", "y"]
    assert all(not row["accepted"] for row in final_scan)


def test_minimizer_accepts_only_replayed_immediate_predecessors_and_decreases_rank():
    goal, domains = _goal(), _domains()
    result = minimize_counterexample(goal, domains, {"x": 3, "y": 3})

    assert result["initialAssignment"] == {"x": "3", "y": "3"}
    assert result["assignment"] == {"x": "1", "y": "1"}
    assert result["status"] == "locally-irreducible"
    assert result["minimality"] is True
    assert "declared immediate-predecessor" in result["minimalityScope"]
    assert result["reductionCount"] == sum(row["accepted"] for row in result["trace"])
    assert result["attemptCount"] == len(result["trace"])
    _assert_trace(result, goal, domains)
    _assert_complete_final_scan(result)


def test_reduction_cap_preserves_current_witness_and_never_claims_minimality():
    result = minimize_counterexample(_goal(), _domains(), {"x": 3, "y": 3}, max_reductions=1)

    assert result["assignment"] == {"x": "2", "y": "3"}
    assert result["trace"]
    assert result["trace"][0]["accepted"] is True
    assert result["minimality"] is False
    assert result["status"] == "budget-exhausted"
    assert result["trace"][-1]["result"] == "interrupted"
    assert check_witness(_goal(), result["assignment"])["status"] == "counterexample"


def test_interruption_during_a_rejected_scan_does_not_claim_irreducibility():
    start = {"x": 1, "y": 3}
    result = minimize_counterexample(_goal(), _domains(), start, max_reductions=1)

    assert result["assignment"] == {"x": "1", "y": "3"}
    assert result["trace"]
    assert result["minimality"] is False
    assert result["status"] == "budget-exhausted"
    assert check_witness(_goal(), result["assignment"])["status"] == "counterexample"


def test_default_reduction_cap_is_32_and_interruption_keeps_the_trace():
    # A 32-reduction cap is observable as a bound even on a larger declared family.
    variables = [f"v{i}" for i in range(9)]
    goal = {
        "variables": variables,
        "premises": [],
        "conclusion": {
            "op": "lt",
            "left": {"op": "add", "args": [{"var": "v0"}, {"var": "v1"}]},
            "right": {"rat": 0},
        },
    }
    domains = {name: list(range(5)) for name in variables}
    start = {name: 4 for name in variables}
    result = minimize_counterexample(goal, domains, start)

    assert result["attemptCount"] <= 32
    assert result["reductionCount"] == sum(row.get("accepted", False) for row in result["trace"])
    assert result["minimality"] is False
    assert result["status"] == "budget-exhausted"
    assert len(result["trace"]) >= result["reductionCount"]
    assert check_witness(goal, result["assignment"])["status"] == "counterexample"


@pytest.mark.parametrize(
    "assignment",
    [{"x": 0, "y": 3}, {"x": 3, "y": 4}, {"x": 3}],
)
def test_initial_assignment_must_be_an_exact_counterexample(assignment):
    with pytest.raises(ValueError):
        minimize_counterexample(_goal(), _domains(), assignment)


@pytest.mark.parametrize(
    "domains",
    [
        {"x": [0, 1]},
        {"x": [0, 1], "y": [0, 1], "z": [2]},
        {"x": [], "y": [0, 1]},
        {"x": [0, "0"], "y": [0, 1]},
        {"x": [False, 1], "y": [0, 1]},
    ],
)
def test_candidate_domains_must_be_exact_valid_and_nonempty(domains):
    with pytest.raises(ValueError):
        minimize_counterexample(_goal(), domains, {"x": 3, "y": 3})


@pytest.mark.parametrize("cap", [0, -1, 33, True, 1.5, "1"])
def test_reduction_cap_must_be_an_integer_from_one_through_32(cap):
    with pytest.raises(ValueError):
        minimize_counterexample(_goal(), _domains(), {"x": 3, "y": 3}, max_reductions=cap)

