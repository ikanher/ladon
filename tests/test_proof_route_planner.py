from __future__ import annotations

from ladon.proof_route_planner import GoalState, PlannerBounds, plan_routes


def test_planner_requires_verifier_evidence_and_finds_complete_route() -> None:
    initial = GoalState("goal")
    rejected = plan_routes(initial, {"goal": [{"name": "lexical", "verification": "not_requested"}]})
    assert rejected["routes"] == []
    complete = plan_routes(initial, {"goal": [{"name": "lemma", "verification": "lean_verified", "residuals": []}]})
    assert complete["routes"][0]["status"] == "complete"


def test_planner_is_bounded_and_fingerprints_context() -> None:
    assert GoalState("g", ("x",)).fingerprint != GoalState("g", ("y",)).fingerprint
    result = plan_routes(GoalState("g"), {"g": [{"name": "loop", "verification": "lean_verified", "residuals": ["g"]}]}, bounds=PlannerBounds(max_depth=1))
    assert result["routes"][0]["status"] == "bounded"
