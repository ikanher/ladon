"""Bounded goal-to-candidate discovery orchestration.

This service deliberately keeps lexical shortlisting and Lean checking separate:
every shortlisted candidate receives an independent terminal outcome, including
rejections and unassessed rows.  It is usable by the CLI and editor adapters
without making a lexical match look like proof authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ladon.evidence_receipt import build_evidence_receipt
from ladon.scratch_replay import replay_scratch
from ladon.semantic_candidate_worker import (
    TRUSTED_TARGET_LIMITATION,
    SemanticCandidateCheck,
    SemanticCandidateRequest,
    check_semantic_candidate,
)

DISCOVERY_SCHEMA = "ladon-verified-discovery-result-v1"
MAX_DISCOVERY_TIMEOUT_SECONDS = 600.0
MAX_DISCOVERY_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_DISCOVERY_RSS_BYTES = 64 * 1024 * 1024 * 1024
MAX_LOCAL_CONTEXT_ROWS = 256
MAX_LOCAL_CONTEXT_BYTES = 1024 * 1024
MAX_DISCOVERY_TERM_BYTES = 64 * 1024


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
        if len(self.local_context) > MAX_LOCAL_CONTEXT_ROWS:
            raise ValueError("local context exceeds the supported row cap")
        context_bytes = 0
        for row in self.local_context:
            if not row.get("name") or not row.get("type"):
                raise ValueError("local context rows require name and type")
            context_bytes += len(row["name"].encode()) + len(row["type"].encode())
        if context_bytes > MAX_LOCAL_CONTEXT_BYTES:
            raise ValueError("local context exceeds the supported byte cap")


def _validate_discovery_bounds(request: DiscoveryRequest) -> None:
    values = (
        request.max_candidates,
        request.batch_size,
        request.timeout_seconds,
        request.max_output_bytes,
        request.max_rss_bytes,
    )
    if not math.isfinite(request.timeout_seconds) or min(values) <= 0:
        raise ValueError("discovery bounds must be positive and finite (supported cap)")
    if request.max_candidates > 1000 or request.batch_size > 100:
        raise ValueError("discovery bounds exceed the supported cap")
    if request.timeout_seconds > MAX_DISCOVERY_TIMEOUT_SECONDS:
        raise ValueError("discovery timeout exceeds the supported cap")
    if request.max_output_bytes > MAX_DISCOVERY_OUTPUT_BYTES:
        raise ValueError("discovery output bound exceeds the supported cap")
    if request.max_rss_bytes > MAX_DISCOVERY_RSS_BYTES:
        raise ValueError("discovery memory bound exceeds the supported cap")
    if (
        len(request.module.encode()) > MAX_DISCOVERY_TERM_BYTES
        or len(request.goal.encode()) > MAX_DISCOVERY_TERM_BYTES
    ):
        raise ValueError("discovery module or goal exceeds the supported byte cap")


def _validate_discovery_scope(scope: str, roots: tuple[str, ...], freshness: str) -> None:
    supported = {
        "repository",
        "project",
        "external",
        "module",
        "namespace",
        "file",
        "imports",
        "closure",
        "neighborhood",
    }
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
ScratchReplayer = Callable[[str, str, Mapping[str, Any]], Mapping[str, Any]]
BatchChecker = Callable[[Sequence[str]], Mapping[str, Mapping[str, Any]]]


def discover_candidates(
    request: DiscoveryRequest,
    shortlist: Sequence[Mapping[str, Any]],
    checker: Checker,
    scratch_replayer: ScratchReplayer | None = None,
    batch_checker: BatchChecker | None = None,
) -> dict[str, Any]:
    """Check a bounded shortlist and retain every candidate outcome."""
    bounded = [
        {**dict(row), "shortlistOrdinal": index}
        for index, row in enumerate(shortlist[: request.max_candidates])
    ]
    candidates = _candidate_rows(
        bounded, checker, scratch_replayer, batch_checker, request.batch_size
    )
    ranked = sorted(
        candidates,
        key=lambda candidate: (
            _status_priority(candidate.check.get("status")),
            int(candidate.shortlist.get("shortlistOrdinal", 0)),
        ),
    )
    request_payload = _request_payload(request)
    payload: dict[str, Any] = {
        "schema": DISCOVERY_SCHEMA,
        "operation": "discover",
        "status": _discovery_status(candidates),
        "request": request_payload,
        "requestIdentity": _identity(request_payload),
        "candidates": [candidate.as_dict() for candidate in ranked],
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
            "submitted": len(candidates),
            "completed": _count_status(
                candidates, {"accepted", "applicable-with-residuals", "rejected"}
            ),
            "accepted": _count_status(candidates, {"accepted", "applicable-with-residuals"}),
            "rejected": _count_status(candidates, {"rejected"}),
            "unassessed": _count_status(candidates, {"unassessed", "timeout", "resource-limited"}),
            "scratchAttempted": sum("scratch" in candidate.check for candidate in candidates),
            "scratchCompiled": sum(
                candidate.check.get("scratch", {}).get("status") == "compiled"
                for candidate in candidates
            ),
            "truncated": len(shortlist) > request.max_candidates,
        },
        "ranking": {
            "policy": "verified-status-priority-v1",
            "contributions": [
                {
                    "candidate": candidate.name,
                    "status": candidate.check.get("status"),
                    "priority": _status_priority(candidate.check.get("status")),
                }
                for candidate in candidates
            ],
        },
        "nonclaims": [
            "Lexical shortlisting is not Lean applicability.",
            "Rejected and unassessed candidates remain visible.",
        ],
    }
    payload["resultIdentity"] = _identity(payload)
    return payload


def _request_payload(request: DiscoveryRequest) -> dict[str, Any]:
    return {
        "schema": "ladon-verified-discovery-request-v1",
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
    }


def _identity(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _candidate_rows(
    rows: Sequence[Mapping[str, Any]],
    checker: Checker,
    scratch_replayer: ScratchReplayer | None,
    batch_checker: BatchChecker | None,
    batch_size: int,
) -> list[DiscoveryCandidate]:
    if batch_checker is not None:
        return _batch_candidate_rows(rows, batch_checker, scratch_replayer, batch_size)
    return [
        candidate
        for row in rows
        if (candidate := _check_one(row, checker, scratch_replayer)) is not None
    ]


def _batch_candidate_rows(
    rows: Sequence[Mapping[str, Any]],
    batch_checker: BatchChecker,
    scratch_replayer: ScratchReplayer | None,
    batch_size: int,
) -> list[DiscoveryCandidate]:
    names = tuple(
        str(row.get("candidateName") or row.get("name"))
        for row in rows
        if row.get("candidateName") or row.get("name")
    )
    results: dict[str, Mapping[str, Any]] = {}
    for start in range(0, len(names), batch_size):
        chunk = names[start : start + batch_size]
        try:
            results.update(batch_checker(chunk))
        except Exception as error:  # noqa: BLE001 - batch isolation boundary
            results.update(_failed_batch_chunk(chunk, error))
    return [
        candidate
        for row in rows
        if (candidate := _candidate_from_batch(row, results, scratch_replayer)) is not None
    ]


def _failed_batch_chunk(names: Sequence[str], error: Exception) -> dict[str, Mapping[str, Any]]:
    return {
        name: {
            "status": "unassessed",
            "diagnostic": {"code": "batch-check-failed", "message": str(error)},
        }
        for name in names
    }


def _status_priority(status: Any) -> int:
    return {
        "accepted": 0,
        "applicable-with-residuals": 1,
        "rejected": 2,
        "timeout": 3,
        "resource-limited": 4,
        "unassessed": 5,
    }.get(status, 6)


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
    check_payload = _attach_scratch(check_payload, name, scratch_replayer)
    return DiscoveryCandidate(name, row, check_payload)


def _candidate_from_batch(
    row: Mapping[str, Any],
    results: Mapping[str, Mapping[str, Any]],
    scratch_replayer: ScratchReplayer | None,
) -> DiscoveryCandidate | None:
    name = str(row.get("candidateName") or row.get("name") or "")
    if not name:
        return None
    check_payload = dict(
        results.get(name, {"status": "unassessed", "diagnostic": {"code": "batch-row-missing"}})
    )
    check_payload = _attach_scratch(check_payload, name, scratch_replayer)
    return DiscoveryCandidate(name, row, check_payload)


def _attach_scratch(
    check_payload: Mapping[str, Any], name: str, scratch_replayer: ScratchReplayer | None
) -> dict[str, Any]:
    result = dict(check_payload)
    if scratch_replayer is None or result.get("status") != "accepted":
        return result
    try:
        receipt = result.get("evidenceReceipt")
        subject = receipt.get("subject", {}) if isinstance(receipt, Mapping) else {}
        caller_context = subject.get("localContext", ()) if isinstance(subject, Mapping) else ()
        application_term = (result.get("applicationTerm") if caller_context else name) or name
        if not isinstance(application_term, str):
            raise TypeError("candidate application term must be a string")
        result["scratch"] = dict(scratch_replayer(name, application_term, result))
    except Exception as error:  # noqa: BLE001 - candidate-scoped replay boundary
        result["scratch"] = {
            "status": "failed",
            "diagnostic": {"code": "scratch-replay-failed", "message": str(error)},
        }
    return result


def _count_status(candidates: Sequence[DiscoveryCandidate], statuses: set[str]) -> int:
    return sum(str(candidate.check.get("status")) in statuses for candidate in candidates)


def _discovery_status(candidates: Sequence[DiscoveryCandidate]) -> str:
    completed = _count_status(candidates, {"accepted", "applicable-with-residuals", "rejected"})
    if not candidates:
        return "unavailable"
    if completed == len(candidates):
        return "available"
    return "partial" if completed else "failed"


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
                local_context=request.local_context,
                execution_context_ref=request.execution_context_ref,
            )
        )

    return check


def semantic_scratch_replayer(request: DiscoveryRequest, toolchain: Any = None) -> ScratchReplayer:
    """Return an independent scratch compiler bound to the same repository."""

    def replay(
        candidate: str, application_term: str, parent: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        result = replay_scratch(
            repo_root=request.repo_root,
            module=request.module,
            goal=request.goal,
            candidate=application_term,
            toolchain=toolchain,
            timeout_seconds=request.timeout_seconds,
            local_context=request.local_context,
        ).to_dict()
        return _scratch_evidence(request, candidate, parent, result, toolchain)

    return replay


def _scratch_evidence(
    request: DiscoveryRequest,
    candidate: str,
    parent: Mapping[str, Any],
    result: Mapping[str, Any],
    toolchain: Any,
) -> dict[str, Any]:
    parent_receipt = parent.get("evidenceReceipt")
    if not isinstance(parent_receipt, Mapping):
        raise TypeError("scratch replay requires the candidate evidence receipt")
    environment_ref = parent_receipt.get("environmentRef")
    parent_check_ref = parent_receipt.get("checkRunRef")
    if not isinstance(environment_ref, str) or not isinstance(parent_check_ref, str):
        raise TypeError("scratch replay requires exact parent evidence references")
    parent_subject = parent_receipt.get("subject")
    observed_context = (
        parent_subject.get("localContext")
        if isinstance(parent_subject, Mapping)
        else [dict(row) for row in request.local_context]
    )
    check_ref = (
        "check:"
        + _identity(
            {
                "operation": "scratch-replay",
                "parentCheckRunRef": parent_check_ref,
                "sourceDigest": result.get("sourceDigest"),
                "outputDigest": result.get("outputDigest"),
                "status": result.get("status"),
            }
        )[7:]
    )
    compiled = result.get("status") == "compiled"
    receipt = build_evidence_receipt(
        subject={
            "module": request.module,
            "candidate": candidate,
            "goal": request.goal,
            "localContext": observed_context,
        },
        execution_binding=(
            "explicit-pinned"
            if toolchain is not None and toolchain.selection_mode == "explicit"
            else "ambient-observed"
        ),
        observation_state="live",
        operation_outcome="accepted" if compiled else "rejected",
        authority_basis="elaborator-check",
        analysis_completeness="complete",
        environment_match="exact" if toolchain is not None else "unknown",
        environment_ref=environment_ref,
        check_run_ref=check_ref,
        limitations=(TRUSTED_TARGET_LIMITATION,),
    )
    return {
        **dict(result),
        "checkRunRef": check_ref,
        "parentCheckRunRef": parent_check_ref,
        "environmentRef": environment_ref,
        "evidenceReceipt": receipt,
    }


__all__ = [
    "DISCOVERY_SCHEMA",
    "DiscoveryCandidate",
    "DiscoveryRequest",
    "discover_candidates",
    "semantic_checker",
    "semantic_scratch_replayer",
]
