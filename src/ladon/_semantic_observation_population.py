"""Closed aggregate algebra for canonical discovery observations."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from typing import Any

from ladon.semantic_projection_core import SemanticProjectionError

_COMPLETED = frozenset({"accepted", "applicable-with-residuals", "rejected"})
_ACCEPTED = frozenset({"accepted", "applicable-with-residuals"})
_UNASSESSED = frozenset(
    {
        "provisional-observation",
        "unassessed",
        "timeout",
        "resource-limited",
        "output-limited",
        "memory-limited",
    }
)
_FAILED = frozenset({"failed-checker", "invalid-worker-output"})


def validate_discovery_aggregate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return only population-derived canonical coverage claims."""

    rows = payload.get("candidates")
    if not isinstance(rows, list):
        raise SemanticProjectionError(
            "canonical discovery result has no candidate population"
        )
    statuses, scratch_statuses = _population_statuses(rows)
    expected_status = _availability(statuses)
    if payload.get("status") != expected_status:
        raise SemanticProjectionError(
            "discovery availability disagrees with its candidate population"
        )
    expected = _canonical_counts(statuses, scratch_statuses)
    coverage = payload.get("coverage")
    if coverage is not None and not isinstance(coverage, Mapping):
        raise SemanticProjectionError("discovery coverage is not a mapping")
    reported = coverage if isinstance(coverage, Mapping) else {}
    _validate_reported_counts(reported, expected)
    _validate_producer_identities(payload)
    return _projectable_coverage(payload, reported, expected)


def _population_statuses(rows: list[Any]) -> tuple[list[str], list[str]]:
    candidate_statuses: list[str] = []
    scratch_statuses: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("check"), Mapping):
            raise SemanticProjectionError("discovery candidate population is invalid")
        check = row["check"]
        candidate_statuses.append(str(check.get("status")))
        scratch = check.get("scratch")
        if scratch is not None:
            if not isinstance(scratch, Mapping):
                raise SemanticProjectionError("discovery scratch observation is invalid")
            scratch_statuses.append(str(scratch.get("status")))
    return candidate_statuses, scratch_statuses


def _availability(statuses: list[str]) -> str:
    completed = sum(status in _COMPLETED for status in statuses)
    if not statuses:
        return "unavailable"
    if completed == len(statuses):
        return "available"
    if completed or "provisional-observation" in statuses:
        return "partial"
    return "failed"


def _canonical_counts(
    statuses: list[str], scratch_statuses: list[str]
) -> dict[str, int]:
    counts = Counter(statuses)
    scratch_counts = Counter(scratch_statuses)
    return {
        "submitted": len(statuses),
        "completed": sum(counts[status] for status in _COMPLETED),
        "accepted": sum(counts[status] for status in _ACCEPTED),
        "rejected": counts["rejected"],
        "unassessed": sum(counts[status] for status in _UNASSESSED),
        "failed": sum(counts[status] for status in _FAILED),
        "timeouts": counts["timeout"],
        "outputLimited": counts["output-limited"],
        "memoryLimited": counts["memory-limited"],
        "invalidWorkerOutput": counts["invalid-worker-output"],
        "scratchAttempted": len(scratch_statuses),
        "scratchCompiled": scratch_counts["compiled"],
    }


def _validate_reported_counts(
    reported: Mapping[str, Any], expected: Mapping[str, int]
) -> None:
    for field, expected_value in expected.items():
        if field not in reported:
            continue
        value = reported[field]
        if isinstance(value, bool) or not isinstance(value, int) or value != expected_value:
            raise SemanticProjectionError(
                f"discovery coverage {field} disagrees with its candidate population"
            )


def _projectable_coverage(
    payload: Mapping[str, Any],
    reported: Mapping[str, Any],
    expected: Mapping[str, int],
) -> dict[str, Any]:
    projected: dict[str, Any] = dict(expected)
    shortlist = _validated_shortlist_coverage(payload, reported, expected["submitted"])
    projected.update(shortlist)
    return projected


def _validated_shortlist_coverage(
    payload: Mapping[str, Any], reported: Mapping[str, Any], submitted: int
) -> dict[str, Any]:
    request = payload.get("request")
    maximum = request.get("maxCandidates") if isinstance(request, Mapping) else None
    shortlisted = reported.get("shortlisted")
    truncated = reported.get("truncated")
    if shortlisted is None or truncated is None or maximum is None:
        return {}
    if not _valid_shortlist_bounds(shortlisted, maximum, submitted):
        raise SemanticProjectionError("discovery shortlist coverage is invalid")
    if not _valid_truncation(truncated, shortlisted, maximum):
        raise SemanticProjectionError(
            "discovery truncation disagrees with its shortlist population"
        )
    return {"shortlisted": shortlisted, "truncated": truncated}


def _valid_shortlist_bounds(shortlisted: Any, maximum: Any, submitted: int) -> bool:
    integers = (
        isinstance(shortlisted, int)
        and not isinstance(shortlisted, bool)
        and isinstance(maximum, int)
        and not isinstance(maximum, bool)
    )
    return (
        integers
        and shortlisted >= submitted
        and maximum > 0
        and submitted <= maximum
    )


def _valid_truncation(truncated: Any, shortlisted: int, maximum: int) -> bool:
    return isinstance(truncated, bool) and truncated == (shortlisted > maximum)


def _validate_producer_identities(payload: Mapping[str, Any]) -> None:
    request_identity = payload.get("requestIdentity")
    if request_identity is not None:
        request = payload.get("request")
        if not isinstance(request, Mapping) or request_identity != _identity(request):
            raise SemanticProjectionError(
                "discovery request identity disagrees with its canonical request"
            )
    result_identity = payload.get("resultIdentity")
    if result_identity is not None:
        body = dict(payload)
        body.pop("resultIdentity", None)
        if result_identity != _identity(body):
            raise SemanticProjectionError(
                "discovery result identity disagrees with its canonical body"
            )


def _identity(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = ["validate_discovery_aggregate"]
