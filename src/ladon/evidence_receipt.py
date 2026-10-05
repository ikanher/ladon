"""Compact, non-escalating evidence receipts shared by authority-sensitive paths."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.evidence_dimensions import (
    EvidenceDimensions,
    validate_evidence_state,
    validate_transition,
)

RECEIPT_SCHEMA = "ladon-evidence-receipt-v1"

_DIMENSION_FIELDS = {
    "executionBinding": "execution_binding",
    "observationState": "observation_state",
    "operationOutcome": "operation_outcome",
    "sourceFreshness": "source_freshness",
    "environmentMatch": "environment_match",
    "authorityBasis": "authority_basis",
    "analysisCompleteness": "analysis_completeness",
}


def project_evidence_receipt(
    receipt: Mapping[str, Any], *, projection_kind: str,
    execution_binding: str | None = None, limitations: Sequence[str] = (),
) -> dict[str, Any]:
    """Derive a view, allowing only registered weakening and added limitations."""

    parent = validate_evidence_receipt(receipt)
    values = {attribute: receipt[field] for field, attribute in _DIMENSION_FIELDS.items()}
    if projection_kind in {"sqlite-row", "dossier"} and parent.observation_state == "live":
        values["observation_state"] = "stored"
    if projection_kind == "aggregate" and parent.observation_state in {"live", "stored"}:
        values["observation_state"] = "derived"
    if execution_binding is not None:
        values["execution_binding"] = execution_binding
    child = EvidenceDimensions(**values)
    validate_transition(parent, child, projection_kind=projection_kind)
    return build_evidence_receipt(
        subject=copy.deepcopy(receipt["subject"]),
        environment_ref=receipt["environmentRef"],
        check_run_ref=receipt["checkRunRef"],
        limitations=[*receipt["limitations"], *limitations],
        **values,
    )


def validate_evidence_receipt(receipt: Mapping[str, Any]) -> EvidenceDimensions:
    """Require the exact canonical receipt shape, identity, and evidence state."""

    expected = {
        "schema", "receiptIdentity", "subject", "environmentRef", "checkRunRef",
        "limitations", *_DIMENSION_FIELDS,
    }
    if not isinstance(receipt, Mapping) or set(receipt) != expected or receipt["schema"] != RECEIPT_SCHEMA:
        raise ValueError("evidence receipt has an unsupported shape or schema")
    values = {attribute: receipt[field] for field, attribute in _DIMENSION_FIELDS.items()}
    canonical = build_evidence_receipt(
        subject=receipt["subject"], environment_ref=receipt["environmentRef"],
        check_run_ref=receipt["checkRunRef"], limitations=receipt["limitations"], **values,
    )
    if canonical != dict(receipt):
        raise ValueError("evidence receipt identity or canonical content is invalid")
    return EvidenceDimensions(**values)


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
    if "queryKind" in subject:
        _validate_query_dimensions(dimensions, environment_ref, check_run_ref)
    _validate_accepted_references(dimensions, environment_ref, check_run_ref)
    _validate_explicit_binding(dimensions)


def _validate_subject(subject: Mapping[str, Any]) -> None:
    if set(subject) == {"queryKind", "artifactRef", "queryIdentity"}:
        if (
            subject["queryKind"] != "derivation"
            or not _digest(subject["artifactRef"])
            or not _digest(subject["queryIdentity"])
        ):
            raise ValueError("derivation query receipt requires exact artifact and query identities")
        return
    if set(subject) == {"queryKind", "theorem", "sourceRef"}:
        _validate_query_subject(subject)
        return
    if set(subject) != {"module", "candidate", "goal", "localContext"}:
        raise ValueError(
            "evidence receipt subject must identify exact module, candidate, goal, and local context"
        )
    _validate_subject_names(subject)
    _validate_subject_context(subject["localContext"])


def _validate_query_subject(subject: Mapping[str, Any]) -> None:
    if subject["queryKind"] not in {"theorem-evidence", "theorem-lineage"}:
        raise ValueError("unsupported stored-query receipt subject")
    if not isinstance(subject["theorem"], str) or not subject["theorem"]:
        raise ValueError("stored-query receipt requires an exact theorem selector")
    source = subject["sourceRef"]
    if source is not None and (
        not isinstance(source, str)
        or re.fullmatch(r"lineage:[A-Za-z0-9_.:-]{1,192}", source) is None
        or subject["queryKind"] != "theorem-lineage"
    ):
        raise ValueError("stored-query receipt source reference is invalid")


def _validate_query_dimensions(
    dimensions: EvidenceDimensions, environment_ref: str | None, check_run_ref: str | None,
) -> None:
    if (
        dimensions.execution_binding != "none"
        or dimensions.operation_outcome != "not-run"
        or dimensions.authority_basis not in {"not-assessed", "stored-observation"}
        or dimensions.environment_match != "not-assessed"
        or environment_ref is not None or check_run_ref is not None
    ):
        raise ValueError("stored-query receipts cannot claim an executed theorem check")


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
    checker = dimensions.authority_basis in {"elaborator-check", "kernel-check"}
    if checker and (not _digest(environment_ref) or not _check_ref(check_run_ref)):
        raise ValueError(
            "checker-backed receipt requires exact environment and check-run references"
        )
    if observed and dimensions.authority_basis not in {
        "elaborator-check",
        "kernel-check",
        "process-observation",
    }:
        raise ValueError("observed receipt requires registered checker authority")
    if observed and dimensions.authority_basis in {"elaborator-check", "kernel-check"} and (
        not _digest(environment_ref) or not _check_ref(check_run_ref)
    ):
        raise ValueError("observed receipt requires exact environment and check-run references")
    _require_process_observation_reference(dimensions, observed, environment_ref, check_run_ref)


def _require_process_observation_reference(
    dimensions: EvidenceDimensions,
    observed: bool,
    environment_ref: str | None,
    check_run_ref: str | None,
) -> None:
    if dimensions.authority_basis != "process-observation":
        return
    if (
        observed
        and dimensions.observation_state == "live"
        and not _check_ref(check_run_ref)
    ):
        raise ValueError("live process observation requires a check-run reference")
    if dimensions.environment_match == "exact" and not _digest(environment_ref):
        raise ValueError("exact process observation requires an environment reference")


def _validate_explicit_binding(dimensions: EvidenceDimensions) -> None:
    observed = dimensions.operation_outcome in {"accepted", "rejected"}
    if (
        dimensions.execution_binding == "explicit-pinned"
        and observed
        and dimensions.environment_match != "exact"
        and dimensions.authority_basis != "process-observation"
    ):
        raise ValueError("explicit-pinned observed receipt requires an exact environment match")


def _digest(value: str | None) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _check_ref(value: str | None) -> bool:
    return isinstance(value, str) and re.fullmatch(r"check:[0-9a-f]{64}", value) is not None


__all__ = [
    "RECEIPT_SCHEMA", "build_evidence_receipt", "project_evidence_receipt",
    "validate_evidence_receipt",
]
