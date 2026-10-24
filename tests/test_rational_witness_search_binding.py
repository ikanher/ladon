"""Candidate-search receipts stay bound to their exact checked goal."""

import hashlib
import json

from ladon.rational_witness import search_candidates


def test_search_result_carries_canonical_goal_and_digest():
    goal = {
        "variables": ["x"],
        "premises": [{"op": "gt", "left": {"var": "x"}, "right": {"rat": 0}}],
        "conclusion": {"op": "ge", "left": {"var": "x"}, "right": {"rat": 1}},
    }

    result = search_candidates(goal, {"x": ["1/2"]})
    encoded = json.dumps(goal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    assert result["goal"] == goal
    assert result["goalSha256"] == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
