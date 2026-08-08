"""Deterministic bounded proof-route AND/OR planner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class GoalState:
    goal: str
    context: tuple[str, ...] = ()
    generation: str = "stored"
    registry: str = "builtin"

    @property
    def fingerprint(self) -> str:
        payload = {"goal": self.goal, "context": sorted(self.context), "generation": self.generation, "registry": self.registry}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class PlannerBounds:
    max_states: int = 1000
    max_depth: int = 32
    max_routes: int = 20

    def __post_init__(self) -> None:
        if min(self.max_states, self.max_depth, self.max_routes) < 1:
            raise ValueError("planner bounds must be positive")


def plan_routes(initial: GoalState, candidates: Mapping[str, Iterable[Mapping[str, Any]]], *, bounds: PlannerBounds | None = None) -> dict[str, Any]:
    bounds = bounds or PlannerBounds()
    queue: list[tuple[tuple[int, int, str], int, tuple[str, ...], tuple[GoalState, ...]]] = []
    heappush(queue, ((0, 0, initial.fingerprint), 0, (), (initial,)))
    routes: list[dict[str, Any]] = []
    expanded = 0
    while queue and expanded < bounds.max_states and len(routes) < bounds.max_routes:
        _, depth, transitions, goals = heappop(queue)
        expanded += 1
        if not _advance(queue, routes, goals, depth, transitions, candidates, bounds):
            break
    return {"schema": "ladon-proof-route-plan-v1", "status": "complete" if routes and any(route["status"] == "complete" for route in routes) else "bounded", "routes": routes, "expandedStates": expanded, "bounds": {"maxStates": bounds.max_states, "maxDepth": bounds.max_depth, "maxRoutes": bounds.max_routes}, "nonclaims": ["Routes require verifier evidence and are not proof certificates."]}


def _advance(queue: list[Any], routes: list[dict[str, Any]], goals: tuple[GoalState, ...], depth: int, transitions: tuple[str, ...], candidates: Mapping[str, Iterable[Mapping[str, Any]]], bounds: PlannerBounds) -> bool:
    if not goals:
        routes.append({"status": "complete", "transitions": list(transitions), "depth": depth})
        return True
    if depth >= bounds.max_depth:
        routes.append({"status": "bounded", "transitions": list(transitions), "remaining": [goal.goal for goal in goals], "depth": depth})
        return True
    selected = min(goals, key=lambda goal: (goal.goal, goal.fingerprint))
    rest = tuple(goal for goal in goals if goal is not selected)
    _enqueue_candidates(queue, selected, rest, depth, transitions, candidates.get(selected.goal, ()))
    return True


def _enqueue_candidates(queue: list[Any], selected: GoalState, rest: tuple[GoalState, ...], depth: int, transitions: tuple[str, ...], candidates: Iterable[Mapping[str, Any]]) -> None:
    for candidate in sorted(candidates, key=lambda row: (str(row.get("cost", 0)), str(row.get("name", "")))):
        if candidate.get("verification") not in {"verified", "lean_verified"}:
            continue
        residuals = tuple(GoalState(str(residual), selected.context, selected.generation, selected.registry) for residual in candidate.get("residuals", ()))
        transition = {"goal": selected.goal, "candidate": candidate.get("name"), "authority": candidate.get("verification"), "cost": candidate.get("cost", 0)}
        heappush(queue, ((int(candidate.get("cost", 0)), len(rest) + len(residuals), selected.fingerprint), depth + 1, transitions + (json.dumps(transition, sort_keys=True),), rest + residuals))


def replay_route(route: Mapping[str, Any], runner: Any) -> dict[str, Any]:
    """Permit a route to become replayed only after an injected runner succeeds."""

    try:
        success = bool(runner(route))
    except Exception as exc:  # supervised boundary reports a bounded diagnostic
        return {"status": "replay_failed", "diagnostic": str(exc)}
    return {"status": "replayed" if success else "replay_failed"}


__all__ = ["GoalState", "PlannerBounds", "plan_routes", "replay_route"]
