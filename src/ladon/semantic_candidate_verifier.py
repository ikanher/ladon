"""Bounded candidate-verification contracts and deterministic result projection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class PatternRequest:
    request_id: str
    module: str
    pattern: str
    assumptions: tuple[str, ...] = ()
    max_candidates: int = 100
    max_diagnostics: int = 100

    def __post_init__(self) -> None:
        if not self.request_id or not self.module or not self.pattern:
            raise ValueError("candidate pattern request requires identity and pattern")
        if min(self.max_candidates, self.max_diagnostics) < 1:
            raise ValueError("candidate bounds must be positive")


@dataclass(frozen=True)
class CandidateResult:
    name: str
    status: str
    match_kind: str = "none"
    substitutions: Mapping[str, str] = None
    residual_goals: tuple[str, ...] = ()
    unresolved_instances: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status, "matchKind": self.match_kind, "substitutions": dict(self.substitutions or {}), "residualGoals": list(self.residual_goals), "unresolvedInstances": list(self.unresolved_instances), "diagnostics": list(self.diagnostics)}


def verify_candidates(request: PatternRequest, candidates: Iterable[Mapping[str, object]]) -> list[CandidateResult]:
    """Run a finite lexical precheck; Lean authority remains an explicit status."""

    results: list[CandidateResult] = []
    for candidate in list(candidates)[: request.max_candidates]:
        name = str(candidate.get("name", ""))
        if not name:
            continue
        if candidate.get("stale"):
            results.append(CandidateResult(name, "stale", diagnostics=("candidate identity is stale",)))
            continue
        candidate_type = str(candidate.get("type", ""))
        pattern = request.pattern
        if _matches(pattern, candidate_type):
            results.append(CandidateResult(name, "matched", "wildcard" if "_" in pattern else "exact"))
        elif pattern.replace("_", "") == candidate_type.replace("_", ""):
            results.append(CandidateResult(name, "matched", "binder-renaming"))
        elif candidate_type:
            results.append(CandidateResult(name, "residual", "unresolved", residual_goals=(pattern,)))
        else:
            results.append(CandidateResult(name, "missing", diagnostics=("candidate type unavailable",)))
    return results


def _matches(pattern: str, candidate_type: str) -> bool:
    if pattern == candidate_type:
        return True
    pattern_parts = pattern.split()
    candidate_parts = candidate_type.split()
    if len(pattern_parts) != len(candidate_parts):
        return False
    return all(left == "_" or left == right for left, right in zip(pattern_parts, candidate_parts))


__all__ = ["CandidateResult", "PatternRequest", "verify_candidates"]
