"""Frozen acceptance candidate for exact rational-goal to Lean encoding.

This intentionally checks the public result rather than internal rendering
helpers.  The proposed API is ``encode_rational_goal(goal, assignment)`` in
``ladon.rational_lean``.
"""

from __future__ import annotations

import copy
import re

import pytest

from ladon.rational_lean import encode_rational_goal
from ladon.rational_witness import check_witness, validate_goal


def rat(value):
    return {"rat": value}


def var(name):
    return {"var": name}


def op(name, *args):
    return {"op": name, "args": list(args)}


def pred(name, left, right):
    return {"op": name, "left": left, "right": right}


def goal(premises, conclusion, variables=("x",)):
    return {"variables": list(variables), "premises": premises, "conclusion": conclusion}


def _obligations(result):
    assert result["schema"] == "ladon-rational-lean-encoding-v1"
    assert result["sourceSemanticsStatus"] == "unverified"
    assert isinstance(result["leanGoalText"], str)
    obligations = result["obligations"]
    assert isinstance(obligations, list)
    assert len({item["id"] for item in obligations}) == len(obligations)
    return obligations


def _encoder_matrix():
    # Every expression operator appears in at least one evaluated proposition;
    # variable substitution also proves that generated propositions are closed.
    expressions = [
        (op("add", var("x"), rat("1/2")), "le", rat("7/2"), " + "),
        (op("sub", rat(3), var("x")), "lt", rat(1), " - "),
        (op("mul", var("x"), rat(2)), "eq", rat(6), " * "),
        (op("div", rat(6), var("x")), "ne", rat(2), " / "),
        ({"op": "neg", "args": [var("x")]}, "ge", rat(-3), "-") ,
        ({"op": "abs", "args": [op("neg", var("x"))]}, "gt", rat(0), "abs"),
        ({"op": "pow", "args": [var("x")], "exponent": 2}, "le", rat(9), " ^ "),
        ({"op": "pow", "args": [var("x")], "exponent": 0}, "eq", rat(1), " ^ "),
    ]
    comparisons = [("le", "≤"), ("lt", "<"), ("eq", "="), ("ne", "≠"), ("ge", "≥"), ("gt", ">")]
    premises = [pred(cmp_op, expr, rhs) for expr, cmp_op, rhs, _fragment in expressions]
    # Explicit comparison coverage is independent of the expression sweep.
    premises.extend(pred(cmp_op, var("x"), rat(0)) for cmp_op, _glyph in comparisons)
    conclusion = pred("eq", op("add", op("abs", var("x")), op("neg", rat(1))), rat(2))
    g = goal(premises, conclusion)
    assignment = {"x": 3}
    return expressions, comparisons, premises, g, assignment


def _assert_encoder_matrix(result, checked, expressions, comparisons, premises):
    obligations = _obligations(result)
    assert len(obligations) == len(premises) + 1
    assert [item["expectedHolds"] for item in obligations] == [
        item["holds"] for item in checked["premises"]
    ] + [checked["conclusion"]["holds"]]
    assert [item["kind"] for item in obligations] == ["premise"] * len(premises) + ["conclusion"]
    assert all(not re.search(r"\bx\b", item["leanProposition"]) for item in obligations)
    for item, (_expr, _cmp, _rhs, fragment) in zip(obligations, expressions):
        assert fragment in item["leanProposition"]
    for item, (_cmp, glyph) in zip(obligations[len(expressions):], comparisons):
        assert glyph in item["leanProposition"]
    assert "by" not in result["leanGoalText"]


def test_encodes_every_expression_operator_and_comparison_with_closed_rationals():
    expressions, comparisons, premises, g, assignment = _encoder_matrix()
    validate_goal(g)
    checked = check_witness(g, assignment)
    result = encode_rational_goal(g, assignment)
    _assert_encoder_matrix(result, checked, expressions, comparisons, premises)


def test_exact_canonical_signed_fraction_formatting_and_determinism():
    g = goal(
        [pred("eq", op("add", var("x"), rat("-1/2")), rat("1/3"))],
        pred("lt", op("div", var("x"), rat("-2")), rat(0)),
    )
    assignment = {"x": "5/6"}
    first = encode_rational_goal(g, assignment)
    second = encode_rational_goal(copy.deepcopy(g), dict(assignment))
    assert first == second
    obligations = _obligations(first)
    assert len(obligations) == 2
    assert "(5 : ℚ) / (6 : ℚ)" in first["leanGoalText"]
    assert "(-1 : ℚ) / (2 : ℚ)" in first["leanGoalText"]
    assert "(1 : ℚ) / (3 : ℚ)" in first["leanGoalText"]
    assert "(0 : ℚ)" in first["leanGoalText"]
    assert all(item["expectedHolds"] is check_witness(g, assignment)["premises"][0]["holds"]
               for item in obligations[:1])


@pytest.mark.parametrize("bad", [
    {"op": "sqrt", "args": [var("x")]},
    {"op": "add", "args": [var("x")]},
    {"op": "add", "args": [var("x"), rat(1)], "lean": "True"},
    {"rat": True},
    {"rat": "1/0"},
    {"var": "x", "name": "injected"},
    {"op": "pow", "args": [var("x")], "exponent": 9},
])
def test_rejects_malformed_or_unsupported_expression_before_returning_obligations(bad):
    g = goal([], pred("eq", bad, rat(0)))
    with pytest.raises((TypeError, ValueError)):
        encode_rational_goal(g, {"x": 0})


@pytest.mark.parametrize("assignment", [{}, {"x": 1, "extra": 2}, {"x": "1/0"}, {"x": True}])
def test_rejects_nonexact_assignment_before_returning_obligations(assignment):
    g = goal([], pred("eq", var("x"), rat(0)))
    with pytest.raises((TypeError, ValueError)):
        encode_rational_goal(g, assignment)


def test_rejects_evaluated_division_by_zero_before_emitting_any_obligations():
    g = goal([], pred("eq", op("div", rat(1), var("x")), rat(0)))
    with pytest.raises(ValueError, match="division by zero"):
        encode_rational_goal(g, {"x": 0})


def test_rejects_goal_and_intermediate_bounds_before_emitting_any_obligations():
    too_many = goal([pred("eq", rat(0), rat(0)) for _ in range(65)], pred("eq", rat(0), rat(0)))
    with pytest.raises(ValueError):
        encode_rational_goal(too_many, {"x": 0})

    def balanced_add(depth):
        if depth == 0:
            return rat(0)
        return op("add", balanced_add(depth - 1), balanced_add(depth - 1))

    over_node_limit = goal([], pred("eq", balanced_add(12), rat(0)))
    with pytest.raises(ValueError, match="nodes"):
        encode_rational_goal(over_node_limit, {"x": 0})


def test_each_obligation_is_exactly_the_python_decision_for_its_corresponding_predicate():
    g = goal(
        [pred("le", var("x"), rat(1)), pred("ne", op("abs", var("x")), rat(0))],
        pred("gt", {"op": "pow", "args": [var("x")], "exponent": 2}, rat(1)),
    )
    assignment = {"x": "1/2"}
    expected = check_witness(g, assignment)
    result = encode_rational_goal(g, assignment)
    obligations = _obligations(result)
    assert [o["expectedHolds"] for o in obligations] == [
        expected["premises"][0]["holds"], expected["premises"][1]["holds"], expected["conclusion"]["holds"]
    ]
    for obligation, holds in zip(obligations, [True, True, False]):
        assert obligation["leanProposition"].endswith(f") = {'true' if holds else 'false'}")
