"""Isolated red contract for bounded exact-rational finite candidate search."""

from __future__ import annotations


def _pred(op, left, right):
    return {"op": op, "left": left, "right": right}


def _rat(value):
    return {"rat": value}


def _goal():
    return {
        "variables": ["x", "y"],
        "premises": [_pred("ge", {"var": "x"}, _rat(0))],
        "conclusion": _pred("gt", {"var": "x"}, {"var": "y"}),
    }


def _search(goal, candidate_lists, *, max_candidates=256):
    from ladon.rational_witness import search_candidates

    return search_candidates(
        goal, candidate_lists, max_candidates=max_candidates
    )


def test_finds_exact_countermodel_and_preserves_declared_family_and_trace():
    result = _search(_goal(), {"x": ["0", "1"], "y": ["0", "1"]})

    assert result["schema"] == "ladon-rational-candidate-search-v1"
    assert result["status"] == "abstract-countermodel"
    assert result["attemptedCount"] == 1
    assert result["declaredFamily"] == {
        "x": ["0", "1"],
        "y": ["0", "1"],
    }
    assert result["trace"] == [
        {"assignment": {"x": "0", "y": "0"}, "status": "counterexample"}
    ]
    assert "encoded goal" in " ".join(result["nonclaims"])
    assert "source" in " ".join(result["nonclaims"])


def test_false_premise_is_traced_as_outside_assumptions_not_countermodel():
    goal = {
        "variables": ["x"],
        "premises": [_pred("gt", {"var": "x"}, _rat(0))],
        "conclusion": _pred("lt", {"var": "x"}, _rat(0)),
    }
    result = _search(goal, {"x": ["0", "1"]})

    assert result["status"] == "abstract-countermodel"
    assert result["attemptedCount"] == 2
    assert result["trace"] == [
        {"assignment": {"x": "0"}, "status": "outside-assumptions"},
        {"assignment": {"x": "1"}, "status": "counterexample"},
    ]
    assert all(row["status"] != "counterexample" for row in result["trace"][:1])


def test_exhausted_family_reports_only_declared_scope_survival():
    goal = {
        "variables": ["x"],
        "premises": [],
        "conclusion": _pred("ge", {"var": "x"}, _rat(0)),
    }
    result = _search(goal, {"x": ["0", "1", "2"]})

    assert result["status"] == "survived-declared-scope"
    assert result["attemptedCount"] == 3
    assert result["declaredFamily"] == {"x": ["0", "1", "2"]}
    assert any("universal" in text.lower() for text in result["nonclaims"])


def test_cap_reports_truncation_and_deterministic_prefix():
    goal = {
        "variables": ["x", "y"],
        "premises": [],
        "conclusion": _pred("ge", _rat(0), _rat(0)),
    }
    family = {"x": ["0", "1"], "y": ["0", "1", "2"]}
    result = _search(goal, family, max_candidates=4)

    assert result["status"] == "budget-exhausted"
    assert result["attemptedCount"] == 4
    assert [row["assignment"] for row in result["trace"]] == [
        {"x": "0", "y": "0"},
        {"x": "0", "y": "1"},
        {"x": "0", "y": "2"},
        {"x": "1", "y": "0"},
    ]


def test_every_variable_requires_a_nonempty_valid_rational_candidate_list():
    goal = _goal()
    for family in (
        {"x": ["0"]},
        {"x": ["0"], "y": []},
        {"x": ["0"], "y": ["1"], "z": ["2"]},
        {"x": ["0"], "y": [True]},
        {"x": ["0"], "y": ["1/0"]},
    ):
        try:
            _search(goal, family)
        except ValueError:
            continue
        raise AssertionError(f"invalid candidate family accepted: {family!r}")


def test_search_cap_must_be_a_positive_integer_at_most_256():
    goal = {"variables": [], "premises": [], "conclusion": _pred("eq", _rat(0), _rat(0))}
    for cap in (0, -1, 257, True, 1.5):
        try:
            _search(goal, {}, max_candidates=cap)
        except ValueError:
            continue
        raise AssertionError(f"invalid cap accepted: {cap!r}")
