"""Shared closed-schema helpers for semantic observation validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon.semantic_projection_core import SemanticProjectionError

CHECKER_TERMINAL_STATUSES = frozenset(
    {"accepted", "applicable-with-residuals", "rejected", "provisional-observation"}
)
CHECKER_AUTHORITIES = frozenset(
    {"elaborator-check", "kernel-check", "process-observation"}
)
CANDIDATE_STATUSES = frozenset(
    {
        *CHECKER_TERMINAL_STATUSES,
        "timeout",
        "resource-limited",
        "output-limited",
        "memory-limited",
        "failed-checker",
        "invalid-worker-output",
        "unassessed",
    }
)
SCRATCH_STATUSES = frozenset(
    {
        "compiled",
        "not-run",
        "timeout",
        "output-limited",
        "memory-limited",
        "process-failed",
        "failed",
    }
)


def mapping(
    value: Any, message: str = "semantic evidence row is invalid"
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SemanticProjectionError(message)
    return value


def artifact_payload(artifact: Mapping[str, Any]) -> Mapping[str, Any]:
    return mapping(artifact.get("payload"), "semantic check artifact has no payload")


def artifact_receipt(artifact: Mapping[str, Any]) -> Mapping[str, Any]:
    extensions = mapping(
        artifact.get("extensions"), "semantic check artifact has no extensions"
    )
    observation = mapping(
        extensions.get("ladon.process-observation/v1"),
        "semantic check artifact has no canonical process observation",
    )
    return mapping(
        observation.get("evidenceReceipt"),
        "semantic check artifact has no canonical evidence receipt",
    )


def artifact_rows(
    check: Mapping[str, Any], kind: str
) -> list[Mapping[str, Any]]:
    artifacts = check.get("artifacts")
    if not isinstance(artifacts, list):
        return []
    return [
        artifact
        for artifact in artifacts
        if isinstance(artifact, Mapping) and artifact.get("artifactKind") == kind
    ]


def non_null_values(*values: Any) -> list[Any]:
    return [value for value in values if value is not None]


def singleton_string(values: list[Any], label: str) -> str:
    if not values or any(not isinstance(value, str) for value in values):
        raise SemanticProjectionError(
            f"semantic result has contradictory or missing {label}"
        )
    first = values[0]
    if any(value != first for value in values[1:]):
        raise SemanticProjectionError(
            f"semantic result has contradictory or missing {label}"
        )
    return first


def direct_candidate(payload: Mapping[str, Any]) -> str:
    receipt = payload.get("evidenceReceipt")
    subject = receipt.get("subject") if isinstance(receipt, Mapping) else None
    candidate = payload.get("candidate")
    if candidate is None and isinstance(subject, Mapping):
        candidate = subject.get("candidate")
    return str(candidate or "<unknown>")


def has_subject_display(descriptors: list[Any], kind: str, display: Any) -> bool:
    return any(
        isinstance(row, Mapping)
        and row.get("kind") == kind
        and row.get("display") == display
        for row in descriptors
    )


def has_candidate_subject(descriptors: list[Any], candidate: str) -> bool:
    for row in descriptors:
        if not isinstance(row, Mapping):
            continue
        if row.get("kind") == "declaration" and row.get("display") == candidate:
            return True
        shape = row.get("searchShape")
        if isinstance(shape, Mapping) and shape.get("declarationName") == candidate:
            return True
    return False


__all__ = [
    "CANDIDATE_STATUSES",
    "CHECKER_AUTHORITIES",
    "CHECKER_TERMINAL_STATUSES",
    "SCRATCH_STATUSES",
    "artifact_payload",
    "artifact_receipt",
    "artifact_rows",
    "direct_candidate",
    "has_candidate_subject",
    "has_subject_display",
    "mapping",
    "non_null_values",
    "singleton_string",
]
