"""Search identity rejects Python containers with divergent views."""

import pytest

from ladon.rational_witness import search_candidates


class DivergentGoal(dict):
    def __getitem__(self, key):
        if key == "conclusion":
            return {"op": "lt", "left": {"var": "x"}, "right": {"rat": 0}}
        return super().__getitem__(key)


def test_goal_subclass_cannot_make_checked_formula_differ_from_hashed_goal():
    goal = DivergentGoal(
        {
            "variables": ["x"],
            "premises": [],
            "conclusion": {"op": "ge", "left": {"var": "x"}, "right": {"rat": 0}},
        }
    )

    with pytest.raises(ValueError, match="JSON-native"):
        search_candidates(goal, {"x": ["1"]})
