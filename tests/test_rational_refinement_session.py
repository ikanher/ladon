"""Shared budgets and immutable evidence across actual rational refinements."""

import copy
import hashlib

import pytest

from ladon import proof_contract_refinement_session as sessions
from ladon import rational_witness as rational


@pytest.fixture(autouse=True)
def stopped_clock(monkeypatch):
    monkeypatch.setattr(rational, "_monotonic", lambda: 0.0)


def _bound(value):
    return {"op": "ge", "left": {"var": "x"}, "right": {"rat": value}}


def _goal(threshold="3/4"):
    return {
        "variables": ["x"], "premises": [],
        "conclusion": {
            "op": "ge", "left": {"op": "div", "args": [{"var": "x"}, {"rat": 2}]},
            "right": {"rat": threshold},
        },
    }


def _repair(value):
    return {
        "id": f"bound-{value}", "expression": _bound(value),
        "justification": {"kind": "proposed-repair", "rationale": "Test this extra bound."},
    }


def _steps():
    return [[_repair(1)], [_repair(2)]]


def _run(tmp_path, *, goal=None, steps=None, **kwargs):
    return sessions.run_rational_refinement_session(
        _goal() if goal is None else goal, {"x": [0, 1, 2, 3]},
        _steps() if steps is None else steps, source_root=tmp_path,
        finding_id="finding-rounds", deadline_monotonic=10.0, **kwargs,
    )


def _count_checks(monkeypatch):
    calls = []
    original = rational.check_witness

    def counted(goal, assignment):
        calls.append(copy.deepcopy(assignment))
        return original(goal, assignment)

    monkeypatch.setattr(rational, "check_witness", counted)
    return calls


def _assert_first_finding(result, assignment):
    assert result["originalFinding"]["witness"]["assignment"] == assignment
    assert result["witnessHistory"][0]["assignment"] == assignment
    assert result["originalClaimRefuted"] is False
    assert result["sourceFormulaFidelity"] == "unverified"


def test_three_goal_changing_rounds_keep_original_and_exact_accounting(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    goal, steps = _goal(), _steps()
    snapshot = copy.deepcopy((goal, steps))
    result = _run(tmp_path, goal=goal, steps=steps)
    assert result["schema"] == "ladon-rational-refinement-session-v1"
    assert result["status"] == "survived-declared-scope"
    assert result["roundCount"] == 3
    _assert_exact_work(result, calls)
    assert (goal, steps) == snapshot
    _assert_first_finding(result, {"x": "0"})
    assert [w["assignment"] for w in result["witnessHistory"]] == [{"x": "0"}, {"x": "1"}]
    _assert_cumulative_rounds(result)


def _assert_exact_work(result, calls):
    assert result["candidateChecks"] == 7
    assert result["transitionChecks"] == 2
    assert result["minimizationRechecks"] == 2
    assert result["reductionAttempts"] == 1
    assert len(calls) == 12


def _assert_cumulative_rounds(result):
    rounds = result["rounds"]
    assert [len(r["candidateSearch"]["goal"]["premises"]) for r in rounds] == [0, 1, 2]
    assert [r["branchCheck"]["witnessCheck"]["status"] for r in rounds[1:]] == [
        "outside-assumptions", "outside-assumptions",
    ]
    for row in rounds[1:]:
        assert row["branch"]["originalFinding"] == result["originalFinding"]
        assert row["branch"]["branchKind"] == "proposed-repair"
    assert rounds[2]["branch"]["parentId"] == rounds[1]["branch"]["id"]
    assert rounds[2]["candidateSearch"]["goalSha256"] != rounds[0]["candidateSearch"]["goalSha256"]
    assert rounds[2]["candidateSearch"]["attemptedCount"] == 4


def test_candidate_budget_is_shared_and_retains_completed_prefix(tmp_path):
    result = _run(tmp_path, max_candidates=2)
    assert result["status"] == "budget-exhausted"
    assert result["stopReason"] == "candidate-cap"
    assert result["candidateChecks"] == 2
    assert result["roundCount"] == 2
    assert [r["candidateSearch"]["attemptedCount"] for r in result["rounds"]] == [1, 1]
    assert result["rounds"][-1]["candidateSearch"]["trace"] == [
        {"assignment": {"x": "0"}, "status": "outside-assumptions"},
    ]
    _assert_first_finding(result, {"x": "0"})


def test_round_budget_does_not_start_an_extra_transition(tmp_path):
    result = _run(tmp_path, max_rounds=2)
    assert result["status"] == "budget-exhausted"
    assert result["stopReason"] == "round-cap"
    assert result["roundCount"] == 2
    assert result["transitionChecks"] == 1
    assert len(result["witnessHistory"]) == 2


def test_reduction_budget_cannot_reset_in_later_round(tmp_path, monkeypatch):
    calls = []
    original = rational.minimize_counterexample

    def minimizer(*args, **kwargs):
        calls.append(kwargs["max_reductions"])
        return original(*args, **kwargs)

    monkeypatch.setattr(rational, "minimize_counterexample", minimizer)
    result = _run(tmp_path, goal=_goal(3), max_reductions=1)
    assert result["status"] == "budget-exhausted"
    assert result["stopReason"] == "reduction-cap"
    assert result["reductionAttempts"] == 1
    assert calls == [1, 1]
    assert len(result["witnessHistory"]) >= 2
    _assert_first_finding(result, {"x": "0"})


def test_deadline_after_first_candidate_preserves_witness_without_restarting(tmp_path, monkeypatch):
    calls = _count_checks(monkeypatch)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0 if calls else 0.0)
    result = _run(tmp_path)
    assert result["status"] == "deadline-exhausted"
    assert result["deadlineMonotonic"] == 10.0
    assert result["roundCount"] == 1
    assert result["candidateChecks"] == len(calls) == 1
    assert result["transitionChecks"] == 0
    _assert_first_finding(result, {"x": "0"})


def test_expiry_during_branch_validation_starts_no_recheck(tmp_path, monkeypatch):
    expired = False
    original = sessions.create_refinement_branch

    def create(*args, **kwargs):
        nonlocal expired
        result = original(*args, **kwargs)
        expired = True
        return result

    monkeypatch.setattr(sessions, "create_refinement_branch", create)
    monkeypatch.setattr(rational, "_monotonic", lambda: 10.0 if expired else 0.0)
    result = _run(tmp_path)
    assert result["status"] == "deadline-exhausted"
    assert result["candidateChecks"] == 1
    assert result["transitionChecks"] == 0
    _assert_first_finding(result, {"x": "0"})


def _source_step(tmp_path):
    path = tmp_path / "paper.txt"
    path.write_text("Assume x >= 1.\n")
    constraint = _repair(1)
    constraint["justification"] = {
        "kind": "source-cited-refinement",
        "source": {"path": "paper.txt", "startLine": 1, "endLine": 1,
                   "quote": "Assume x >= 1.", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
        "nonclaim": "Span validation does not certify formula fidelity.",
    }
    return path, [[constraint]]


def test_stale_source_after_initial_search_retains_original_history(tmp_path, monkeypatch):
    path, steps = _source_step(tmp_path)
    original = rational.check_witness

    def replace_source(goal, assignment):
        result = original(goal, assignment)
        path.write_text("Changed source.\n")
        return result

    monkeypatch.setattr(rational, "check_witness", replace_source)
    result = _run(tmp_path, steps=steps)
    assert result["status"] == "invalid-input"
    assert result["roundCount"] == 1
    _assert_first_finding(result, {"x": "0"})


def test_source_cited_round_stays_distinct_from_proposed_repair(tmp_path):
    _path, steps = _source_step(tmp_path)
    result = _run(tmp_path, steps=steps)
    assert result["status"] == "abstract-countermodel"
    assert result["rounds"][1]["branch"]["branchKind"] == "source-cited-refinement"
    _assert_first_finding(result, {"x": "0"})


def test_reached_undefined_expression_keeps_failing_assignment_and_prior_witness(tmp_path):
    goal = _goal(3)
    goal["premises"] = [_bound(1)]
    constraint = _repair(1)
    constraint["expression"] = {
        "op": "ge", "left": {"op": "div", "args": [{"rat": 1}, {"var": "x"}]},
        "right": {"rat": 0},
    }
    result = _run(tmp_path, goal=goal, steps=[[constraint]])
    assert result["status"] == "invalid-input"
    assert result["candidateChecks"] == 3
    assert result["rounds"][-1]["candidateSearch"]["trace"][-1]["assignment"] == {"x": "0"}
    assert result["rounds"][-1]["candidateSearch"]["trace"][-1]["status"] == "invalid-input"
    _assert_first_finding(result, {"x": "1"})


@pytest.mark.parametrize("name,cap", [
    ("max_candidates", 0), ("max_candidates", 257), ("max_reductions", 33),
    ("max_rounds", 0), ("max_rounds", 5), ("max_rounds", True),
])
def test_caps_are_strict_and_bounded(tmp_path, name, cap):
    with pytest.raises(ValueError):
        _run(tmp_path, **{name: cap})


def test_inputs_are_snapshotted_before_any_exact_check(tmp_path, monkeypatch):
    goal, steps = _goal(), _steps()
    original = rational.check_witness

    def mutate_caller_inputs(current_goal, assignment):
        goal["conclusion"]["right"] = {"rat": 100}
        steps[1][0]["expression"]["right"] = {"rat": -100}
        return original(current_goal, assignment)

    monkeypatch.setattr(rational, "check_witness", mutate_caller_inputs)
    result = _run(tmp_path, goal=goal, steps=steps)
    assert result["status"] == "survived-declared-scope"
    assert result["rounds"][-1]["candidateSearch"]["goal"]["premises"][-1] == _bound(2)
