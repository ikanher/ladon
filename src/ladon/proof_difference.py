"""Bounded proof-goal difference and route-card evidence models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class DifferenceRequest:
    goal: str
    candidate: str
    module: str | None = None
    assumptions: tuple[str, ...] = ()
    suggestion_cap: int = 10
    freshness: str = "stored"

    def __post_init__(self) -> None:
        if not self.goal or not self.candidate:
            raise ValueError("goal and candidate are required")
        if self.suggestion_cap < 1:
            raise ValueError("suggestion_cap must be positive")
        if self.freshness not in {"stored", "verify"}:
            raise ValueError("freshness must be stored or verify")


@dataclass(frozen=True)
class RouteCard:
    goal: str
    candidate: str
    module: str | None
    generation: str
    policy: str
    accepted: bool
    reason: str
    evidence: tuple[Mapping[str, Any], ...] = ()
    omissions: tuple[Mapping[str, Any], ...] = ()

    @property
    def identity(self) -> str:
        payload = {"goal": self.goal, "candidate": self.candidate, "module": self.module, "generation": self.generation, "policy": self.policy, "evidence": list(self.evidence)}
        return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {"schema": "ladon-proof-route-card-v1", "identity": self.identity, "goal": self.goal, "candidate": self.candidate, "module": self.module, "generation": self.generation, "policy": self.policy, "accepted": self.accepted, "reason": self.reason, "evidence": list(self.evidence), "omissions": list(self.omissions), "nonclaims": ["A route card is bounded planning evidence, not Lean proof verification."]}


def analyze_difference(request: DifferenceRequest) -> dict[str, Any]:
    """Classify a compact structural mismatch without overclaiming Lean authority."""

    if request.goal == request.candidate:
        classification, reason, accepted = "applicable", "exact-conclusion", True
    elif request.goal.casefold() == request.candidate.casefold():
        classification, reason, accepted = "representation-boundary", "casefold-equivalent", False
    else:
        classification, reason, accepted = "not-applicable", "conclusion-mismatch", False
    route = RouteCard(request.goal, request.candidate, request.module, "stored", request.freshness, accepted, reason, ({"classification": classification},))
    return {"schema": "ladon-proof-difference-result-v1", "operation": "explain", "status": "available", "goal": request.goal, "candidate": request.candidate, "classification": classification, "reason": reason, "attempts": [{"pass": "exact", "status": "accepted" if accepted else "rejected"}], "substitutions": {}, "dischargedBinders": [], "residuals": [] if accepted else [request.goal], "unresolvedGoals": [] if accepted else [request.goal], "mismatches": [] if accepted else [{"kind": classification, "goal": request.goal, "candidate": request.candidate}], "suggestions": [], "coverage": {"authority": "bounded_structural_analysis", "suggestionCap": request.suggestion_cap}, "routeCard": route.as_dict(), "nonclaims": ["Structural difference analysis is not proof-term verification."]}


def suggest_one_level(residual: str, candidates: Sequence[Mapping[str, Any]], *, cap: int = 10) -> list[dict[str, Any]]:
    """Attach bounded, explicitly unverified one-level premise suggestions."""

    return [{"premise": residual, "candidate": str(row.get("name", "")), "authority": "sqlite_shortlist", "verification": "not_requested"} for row in candidates[:cap] if row.get("name")]


__all__ = ["DifferenceRequest", "RouteCard", "analyze_difference", "suggest_one_level"]
