"""Compact, non-escalating evidence receipts shared by authority-sensitive paths."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

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
    check_run_ref: str | None = None,
    limitations: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a canonical receipt without promoting any authority dimension."""
    allowed = {
        "executionBinding": {"explicit-pinned", "ambient-observed", "none"},
        "observationState": {"live", "stored", "derived", "absent", "failed"},
        "operationOutcome": {"accepted", "rejected", "failed", "not-run"},
        "sourceFreshness": {"fresh", "stale", "unknown", "not-assessed"},
        "environmentMatch": {"exact", "mismatched", "unknown", "not-assessed"},
        "analysisCompleteness": {"complete", "partial", "invalid", "not-assessed"},
    }
    values = {
        "executionBinding": execution_binding,
        "observationState": observation_state,
        "operationOutcome": operation_outcome,
        "sourceFreshness": source_freshness,
        "environmentMatch": environment_match,
        "analysisCompleteness": analysis_completeness,
    }
    for name, value in values.items():
        if value not in allowed[name]:
            raise ValueError(f"unsupported evidence receipt dimension: {name}={value}")
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
        "checkRunRef": check_run_ref,
        "limitations": sorted({str(item) for item in limitations}),
    }
    identity_payload = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["receiptIdentity"] = "sha256:" + hashlib.sha256(identity_payload.encode()).hexdigest()
    return body


__all__ = ["RECEIPT_SCHEMA", "build_evidence_receipt"]
