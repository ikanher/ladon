"""Binding planning bounds untrusted expressions before recursive encoding."""

from copy import deepcopy

import pytest
from test_real_bound_shape import estimate, observe

from ladon.real_bound_binding import plan_bound_prefix


def observation():
    expr = estimate()
    return {"status": "observed", "candidate": observe(expr)["candidate"],
            "statementSnapshot": {"selection": {"declaration": "Example.estimate"},
                                  "observation": {"normalizedTypeExpr": expr}}}


def test_candidate_must_match_the_supplied_expression():
    value = observation()
    value["candidate"]["loss"] = 123
    with pytest.raises(ValueError, match="candidate|shape"):
        plan_bound_prefix(value, {"declaration": "Example.sample", "arguments": []})


def test_deep_expression_rejects_before_recursive_goal_encoding():
    value = observation()
    expr = deepcopy(value["statementSnapshot"]["observation"]["normalizedTypeExpr"])
    for _ in range(200):
        expr = {"app": [expr, {"nat": 0}]}
    value["statementSnapshot"]["observation"]["normalizedTypeExpr"] = expr
    with pytest.raises(ValueError, match="candidate|shape|depth"):
        plan_bound_prefix(value, {"declaration": "Example.sample", "arguments": []})
