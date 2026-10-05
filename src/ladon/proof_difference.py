"""Bounded proof-goal difference and route-card evidence models."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.type_normalization import peel_binder_signature


@dataclass(frozen=True)
class DifferenceRequest:
    goal: str
    candidate: str
    module: str | None = None
    assumptions: tuple[str, ...] = ()
    suggestion_cap: int = 10
    freshness: str = "stored"
    raw_signature: bool = False

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


def analyze_difference(request: DifferenceRequest, *, candidate_signature: str | None = None, candidate_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify a compact structural mismatch without overclaiming Lean authority."""

    signature = request.candidate if candidate_signature is None else candidate_signature
    candidate_conclusion, peeled_binders, peel_error = (signature, [], None) if request.raw_signature else peel_binder_signature(signature)
    classification, reason, matched = _classify_difference(
        request.goal, candidate_conclusion, peel_error, bool(peeled_binders)
    )
    route = RouteCard(request.goal, request.candidate, request.module, "stored", request.freshness, False, reason, ({"classification": classification},))
    discharged, residuals = _binder_evidence(
        peeled_binders, request.assumptions, matched, request.goal
    )
    return _difference_payload(
        request,
        candidate_conclusion,
        peeled_binders,
        classification,
        reason,
        matched,
        discharged,
        residuals,
        route,
        candidate_evidence,
    )


def _binder_evidence(
    binders: Sequence[str], assumptions: Sequence[str], matched: bool, goal: str
) -> tuple[list[str], list[str]]:
    discharged = [binder for binder in binders if binder in assumptions]
    residuals = [binder for binder in binders if binder not in assumptions]
    return discharged, residuals or ([] if matched else [goal])


def _difference_payload(
    request: DifferenceRequest,
    conclusion: str,
    binders: Sequence[str],
    classification: str,
    reason: str,
    matched: bool,
    discharged: Sequence[str],
    residuals: Sequence[str],
    route: RouteCard,
    candidate_evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema": "ladon-proof-difference-result-v1",
        "schemaVersion": 2,
        "operation": "explain",
        "status": "available",
        "goal": request.goal,
        "candidate": request.candidate,
        "classification": classification,
        "reason": reason,
        "attempts": [{"pass": "rendered-structure", "status": "matched" if matched else "not-matched"}],
        "substitutions": {},
        "dischargedBinders": list(discharged),
        "residuals": list(residuals),
        "unresolvedGoals": list(residuals),
        "mismatches": [] if matched else [{"kind": classification, "goal": request.goal, "candidate": request.candidate}],
        "suggestions": [],
        "candidateEvidence": dict(candidate_evidence) if candidate_evidence else None,
        "normalization": {"identity": "raw-signature-v1" if request.raw_signature else "binder-peeling-v1", "originalCandidate": request.candidate, "peeledConclusion": conclusion, "peeledBinders": list(binders)},
        "coverage": {"authority": "binder-aware_structural_analysis", "suggestionCap": request.suggestion_cap},
        "routeCard": route.as_dict(),
        "nonclaims": [
            "Structural difference analysis is not proof-term verification or Lean applicability.",
            "Use proof-search check or discover for explicit Lean candidate checking.",
        ],
    }


def _classify_difference(goal: str, conclusion: str, error: str | None, has_binders: bool) -> tuple[str, str, bool]:
    if error:
        return "indeterminate-structural", error, False
    if goal == conclusion and has_binders:
        return "rendered-conclusion-with-binders", "exact-rendered-conclusion-with-binders", True
    if goal == conclusion:
        return "exact-rendered-conclusion", "exact-rendered-conclusion", True
    if goal.casefold() == conclusion.casefold():
        return "casefold-text-near-match", "casefold-equivalent", False
    return "no-structural-match", "rendered-conclusion-mismatch", False




def suggest_one_level(residual: str, candidates: Sequence[Mapping[str, Any]], *, cap: int = 10) -> list[dict[str, Any]]:
    """Attach bounded, explicitly unverified one-level premise suggestions."""

    return [{"premise": residual, "candidate": str(row.get("name", "")), "authority": "sqlite_shortlist", "verification": "not_requested"} for row in candidates[:cap] if row.get("name")]


__all__ = ["DifferenceRequest", "RouteCard", "analyze_difference", "suggest_one_level"]
