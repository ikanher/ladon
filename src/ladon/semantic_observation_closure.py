"""Resolve compact semantic claims against canonical ProofIR evidence.

Compact transport may omit artifact bodies only after every candidate and
scratch row—including rows omitted from cards—has been resolved and checked.
The private evidence and contract modules own the detailed schema invariants;
this module keeps the public full-population validation seam small.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ladon._semantic_observation_contract import (
    validate_observation_semantics,
    validate_scratch_parent,
    validate_status,
    validate_weak_observation,
)
from ladon._semantic_observation_evidence import (
    requires_canonical_evidence,
    resolve_observation_evidence,
    validate_canonical_receipt,
)
from ladon._semantic_observation_population import validate_discovery_aggregate
from ladon._semantic_observation_support import direct_candidate, mapping
from ladon.semantic_projection_core import SemanticProjectionError


@dataclass(frozen=True)
class ResolvedSemanticObservation:
    """The content-addressed evidence owner of one public semantic row."""

    candidate: str
    status: str
    environment_ref: str | None
    environment_artifact_ref: str | None
    check_run_id: str | None
    check_artifact_ref: str | None
    scratch: bool = False


def validate_semantic_observation_population(
    payload: Mapping[str, Any],
    registered_artifacts: Mapping[str, Mapping[str, Any]],
) -> tuple[ResolvedSemanticObservation, ...]:
    """Resolve every canonical observation before compact selection or counting."""

    operation = payload.get("operation")
    expected_schema = {
        "check-candidate": "ladon-semantic-candidate-check-result-v1",
        "discover": "ladon-verified-discovery-result-v1",
    }.get(operation)
    if expected_schema is None:
        raise SemanticProjectionError(
            f"unsupported canonical semantic operation: {operation or '<missing>'}"
        )
    if payload.get("schema") != expected_schema:
        raise SemanticProjectionError(
            "canonical semantic operation has a mismatched result schema"
        )
    if operation == "check-candidate":
        return _resolve_direct_population(payload, registered_artifacts)
    if operation == "discover":
        return _resolve_discovery_population(payload, registered_artifacts)
    raise AssertionError("closed semantic operation dispatch is incomplete")


def _resolve_direct_population(
    payload: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[ResolvedSemanticObservation, ...]:
    candidate = direct_candidate(payload)
    observation = _resolve_observation(payload, candidate, registry)
    scratch = payload.get("scratch")
    if scratch is None:
        return (observation,)
    scratch_observation = _resolve_observation(
        mapping(scratch, "semantic direct check has invalid scratch evidence"),
        candidate,
        registry,
        scratch=True,
        parent=observation,
    )
    return observation, scratch_observation


def _resolve_discovery_population(
    payload: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[ResolvedSemanticObservation, ...]:
    rows = payload.get("candidates")
    if not isinstance(rows, list):
        raise SemanticProjectionError(
            "canonical discovery result has no candidate population"
        )
    request = mapping(payload.get("request"))
    resolved: list[ResolvedSemanticObservation] = []
    for index, row_value in enumerate(rows):
        resolved.extend(_resolve_discovery_row(row_value, index, request, registry))
    validate_discovery_aggregate(payload)
    return tuple(resolved)


def _resolve_discovery_row(
    row_value: Any,
    index: int,
    request: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> list[ResolvedSemanticObservation]:
    row = mapping(row_value, f"semantic candidate row {index} is invalid")
    candidate = row.get("name")
    if not isinstance(candidate, str) or not candidate:
        raise SemanticProjectionError(f"semantic candidate row {index} has no name")
    check = mapping(
        row.get("check"), f"semantic candidate row {index} has no check observation"
    )
    observation = _resolve_observation(
        check,
        candidate,
        registry,
        request=request,
    )
    result = [observation]
    scratch = check.get("scratch")
    if scratch is not None:
        result.append(
            _resolve_observation(
                mapping(
                    scratch,
                    f"semantic candidate row {index} has invalid scratch evidence",
                ),
                candidate,
                registry,
                request=request,
                scratch=True,
                parent=observation,
            )
        )
    return result


def _resolve_observation(
    check: Mapping[str, Any],
    candidate: str,
    registry: Mapping[str, Mapping[str, Any]],
    *,
    request: Mapping[str, Any] | None = None,
    scratch: bool = False,
    parent: ResolvedSemanticObservation | None = None,
) -> ResolvedSemanticObservation:
    status = str(check.get("status", "unknown"))
    validate_status(status, scratch)
    receipt_value = check.get("evidenceReceipt")
    receipt = receipt_value if isinstance(receipt_value, Mapping) else None
    if receipt is not None:
        validate_canonical_receipt(receipt)
    requires_evidence = requires_canonical_evidence(check, status, receipt, scratch)
    if not requires_evidence:
        if receipt is not None:
            validate_weak_observation(check, receipt, candidate, status, request)
        return ResolvedSemanticObservation(candidate, status, None, None, None, None)
    if receipt is None:
        raise SemanticProjectionError(
            f"checker-backed semantic observation for {candidate} has no evidence receipt"
        )
    evidence = resolve_observation_evidence(check, receipt, registry)
    validate_observation_semantics(
        check,
        receipt,
        evidence.check_artifact,
        candidate,
        status,
        request=request,
        scratch=scratch,
    )
    if parent is not None:
        validate_scratch_parent(
            check,
            parent.environment_ref,
            parent.check_run_id,
            evidence.environment_ref,
        )
    return ResolvedSemanticObservation(
        candidate=candidate,
        status=status,
        environment_ref=evidence.environment_ref,
        environment_artifact_ref=str(evidence.environment_artifact["artifactId"]),
        check_run_id=evidence.check_run_id,
        check_artifact_ref=str(evidence.check_artifact["artifactId"]),
        scratch=scratch,
    )


__all__ = [
    "ResolvedSemanticObservation",
    "validate_semantic_observation_population",
]
