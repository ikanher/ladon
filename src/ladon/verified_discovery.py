"""Bounded goal-to-candidate discovery orchestration.

This service deliberately keeps lexical shortlisting and Lean checking separate:
every shortlisted candidate receives an independent terminal outcome, including
rejections and unassessed rows.  It is usable by the CLI and editor adapters
without making a lexical match look like proof authority.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.scratch_replay import replay_scratch
from ladon.semantic_candidate_worker import (
    SemanticCandidateCheck,
    SemanticCandidateRequest,
    check_semantic_candidate,
)

DISCOVERY_SCHEMA = "ladon-verified-discovery-result-v1"


@dataclass(frozen=True)
class DiscoveryRequest:
    repo_root: Path
    module: str
    goal: str
    local_context: tuple[Mapping[str, str], ...] = ()
    max_candidates: int = 20
    batch_size: int = 8
    timeout_seconds: float = 120.0
    max_output_bytes: int = 8 * 1024 * 1024
    max_rss_bytes: int = 2 * 1024 * 1024 * 1024
    scope: str = "repository"
    roots: tuple[str, ...] = ()
    freshness: str = "stored"
    execution_context_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.module or not self.goal:
            raise ValueError("discovery requires module and goal")
        _validate_discovery_bounds(self)
        _validate_discovery_scope(self.scope, self.roots, self.freshness)
        for row in self.local_context:
            if not row.get("name") or not row.get("type"):
                raise ValueError("local context rows require name and type")


def _validate_discovery_bounds(request: DiscoveryRequest) -> None:
    values = (request.max_candidates, request.batch_size, request.timeout_seconds, request.max_output_bytes, request.max_rss_bytes)
    if min(values) <= 0:
        raise ValueError("discovery bounds must be positive")
    if request.max_candidates > 1000 or request.batch_size > 100:
        raise ValueError("discovery bounds exceed the supported cap")


def _validate_discovery_scope(scope: str, roots: tuple[str, ...], freshness: str) -> None:
    supported = {"repository", "project", "external", "module", "namespace", "file", "imports", "closure", "neighborhood"}
    if scope not in supported:
        raise ValueError("unsupported discovery scope")
    if scope in {"module", "namespace", "file", "imports", "closure", "neighborhood"} and not roots:
        raise ValueError("discovery scope requires roots")
    if freshness not in {"stored", "verify"}:
        raise ValueError("unsupported discovery freshness")


@dataclass(frozen=True)
class DiscoveryCandidate:
    name: str
    shortlist: Mapping[str, Any]
    check: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "shortlist": dict(self.shortlist), "check": dict(self.check)}


Checker = Callable[[str], SemanticCandidateCheck]
ScratchReplayer = Callable[[str], Mapping[str, Any]]


def discover_candidates(
    request: DiscoveryRequest,
    shortlist: Sequence[Mapping[str, Any]],
    checker: Checker,
    scratch_replayer: ScratchReplayer | None = None,
) -> dict[str, Any]:
    """Check a bounded shortlist and retain every candidate outcome."""
    candidates = [
        candidate
        for row in shortlist[: request.max_candidates]
        if (candidate := _check_one(row, checker, scratch_replayer)) is not None
    ]
    payload: dict[str, Any] = {
        "schema": DISCOVERY_SCHEMA,
        "operation": "discover",
        "status": "available",
        "request": {
            "module": request.module,
            "goal": request.goal,
            "localContext": [dict(row) for row in request.local_context],
            "maxCandidates": request.max_candidates,
            "batchSize": request.batch_size,
            "timeoutSeconds": request.timeout_seconds,
            "maxOutputBytes": request.max_output_bytes,
            "maxRssBytes": request.max_rss_bytes,
            "scope": request.scope,
            "roots": list(request.roots),
            "freshness": request.freshness,
            "executionContextRef": request.execution_context_ref,
        },
        "candidates": [candidate.as_dict() for candidate in candidates],
        "batch": {
            "protocol": "ladon-verified-discovery-v1",
            "sequence": list(range(len(candidates))),
            "candidateNames": [candidate.name for candidate in candidates],
            "goal": request.goal,
            "localContext": [dict(row) for row in request.local_context],
            "executionContextRef": request.execution_context_ref,
        },
        "coverage": {
            "shortlisted": len(shortlist),
            "checked": len(candidates),
            "truncated": len(shortlist) > request.max_candidates,
        },
        "ranking": {
            "policy": "verified-status-priority-v1",
            "contributions": [
                {"candidate": candidate.name, "status": candidate.check.get("status"), "priority": _status_priority(candidate.check.get("status"))}
                for candidate in candidates
            ],
        },
        "nonclaims": [
            "Lexical shortlisting is not Lean applicability.",
            "Rejected and unassessed candidates remain visible.",
        ],
    }
    identity = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["requestIdentity"] = "sha256:" + hashlib.sha256(identity.encode()).hexdigest()
    return payload


def _status_priority(status: Any) -> int:
    return {"accepted": 0, "applicable-with-residuals": 1, "rejected": 2, "timeout": 3, "resource-limited": 4, "unassessed": 5}.get(status, 6)


def _check_one(
    row: Mapping[str, Any], checker: Checker, scratch_replayer: ScratchReplayer | None
) -> DiscoveryCandidate | None:
    name = str(row.get("candidateName") or row.get("name") or "")
    if not name:
        return None
    try:
        check_payload: Mapping[str, Any] = checker(name).to_dict()
    except Exception as error:  # noqa: BLE001 - candidate isolation boundary
        check_payload = {
            "status": "unassessed",
            "diagnostic": {"code": "candidate-check-failed", "message": str(error)},
        }
    if scratch_replayer is not None and check_payload.get("status") == "accepted":
        check_payload = {**check_payload, "scratch": dict(scratch_replayer(name))}
    return DiscoveryCandidate(name, row, check_payload)


def semantic_checker(request: DiscoveryRequest, toolchain: Any = None) -> Checker:
    """Return a checker factory for the existing supervised Lean worker."""
    def check(candidate: str) -> SemanticCandidateCheck:
        return check_semantic_candidate(
            SemanticCandidateRequest(
                request.repo_root,
                request.module,
                request.goal,
                candidate,
                timeout_seconds=request.timeout_seconds,
                max_output_bytes=request.max_output_bytes,
                max_rss_bytes=request.max_rss_bytes,
                toolchain=toolchain,
            )
        )

    return check


def semantic_scratch_replayer(request: DiscoveryRequest, toolchain: Any = None) -> ScratchReplayer:
    """Return an independent scratch compiler bound to the same repository."""
    return lambda candidate: replay_scratch(
        repo_root=request.repo_root,
        module=request.module,
        goal=request.goal,
        candidate=candidate,
        toolchain=toolchain,
        timeout_seconds=request.timeout_seconds,
    ).to_dict()


__all__ = ["DISCOVERY_SCHEMA", "DiscoveryCandidate", "DiscoveryRequest", "discover_candidates", "semantic_checker", "semantic_scratch_replayer"]
