"""Compact, non-escalating evidence receipts shared by authority-sensitive paths."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.evidence_dimensions import EvidenceDimensions, validate_evidence_state

RECEIPT_SCHEMA = "ladon-evidence-receipt-v1"


def build_evidence_receipt(
    *,
    subject: Mapping[str, Any],
    execution_binding: str,
    observation_state: str,
    operation_outcome: str,
    authority_basis: str,
    analysis_completeness: str,
    source_freshness: str = "unknown",
    environment_match: str = "unknown",
    environment_ref: str | None = None,
    check_run_ref: str | None = None,
    limitations: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a canonical receipt without promoting any authority dimension."""
    dimensions = EvidenceDimensions(
        execution_binding,
        observation_state,
        operation_outcome,
        source_freshness,
        environment_match,
        authority_basis,
        analysis_completeness,
    )
    validate_evidence_state(dimensions)
    _validate_receipt_references(subject, dimensions, environment_ref, check_run_ref)
    body: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "subject": dict(subject),
        "executionBinding": execution_binding,
        "observationState": observation_state,
        "operationOutcome": operation_outcome,
        "authorityBasis": authority_basis,
        "analysisCompleteness": analysis_completeness,
        "sourceFreshness": source_freshness,
        "environmentMatch": environment_match,
        "environmentRef": environment_ref,
        "checkRunRef": check_run_ref,
        "limitations": sorted({str(item) for item in limitations}),
    }
    identity_payload = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["receiptIdentity"] = "sha256:" + hashlib.sha256(identity_payload.encode()).hexdigest()
    return body


def _validate_receipt_references(
    subject: Mapping[str, Any],
    dimensions: EvidenceDimensions,
    environment_ref: str | None,
    check_run_ref: str | None,
) -> None:
    _validate_subject(subject)
    _validate_accepted_references(dimensions, environment_ref, check_run_ref)
    _validate_explicit_binding(dimensions)


def _validate_subject(subject: Mapping[str, Any]) -> None:
    if set(subject) != {"module", "candidate", "goal", "localContext"}:
        raise ValueError(
            "evidence receipt subject must identify exact module, candidate, goal, and local context"
        )
    _validate_subject_names(subject)
    _validate_subject_context(subject["localContext"])


def _validate_subject_names(subject: Mapping[str, Any]) -> None:
    if not all(
        isinstance(subject[field], str) and subject[field]
        for field in ("module", "candidate", "goal")
    ):
        raise ValueError("evidence receipt subject names must be non-empty strings")


def _validate_subject_context(context: Any) -> None:
    if not isinstance(context, list) or any(
        not isinstance(row, Mapping)
        or set(row) != {"name", "type"}
        or not all(isinstance(row[field], str) and row[field] for field in ("name", "type"))
        for row in context
    ):
        raise ValueError("evidence receipt local context is invalid")


def _validate_accepted_references(
    dimensions: EvidenceDimensions,
    environment_ref: str | None,
    check_run_ref: str | None,
) -> None:
    observed = dimensions.operation_outcome in {"accepted", "rejected"}
    if observed and dimensions.authority_basis not in {"elaborator-check", "kernel-check"}:
        raise ValueError("observed receipt requires registered checker authority")
    if observed and (not _digest(environment_ref) or not _check_ref(check_run_ref)):
        raise ValueError("observed receipt requires exact environment and check-run references")


def _validate_explicit_binding(dimensions: EvidenceDimensions) -> None:
    observed = dimensions.operation_outcome in {"accepted", "rejected"}
    if (
        dimensions.execution_binding == "explicit-pinned"
        and observed
        and dimensions.environment_match != "exact"
    ):
        raise ValueError("explicit-pinned observed receipt requires an exact environment match")


def _digest(value: str | None) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _check_ref(value: str | None) -> bool:
    return isinstance(value, str) and re.fullmatch(r"check:[0-9a-f]{64}", value) is not None


__all__ = ["RECEIPT_SCHEMA", "build_evidence_receipt"]
