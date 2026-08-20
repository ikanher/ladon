"""Owned, orthogonal ProofIR observation and coverage value types."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ladon.proofir_result_dimensions import ANALYSIS_COMPLETENESS
from ladon.proofir_v3 import canonical_bytes

ASSERTION_STATES = frozenset({"asserted", "denied", "unknown"})
SEMANTIC_VALIDATIONS = frozenset({"unchecked", "accepted", "rejected", "failed"})
FRESHNESS_STATES = frozenset({"fresh", "stale", "unknown"})
ATTACHMENT_RESULTS = frozenset({"exact", "strong", "ambiguous", "unattached"})
COVERAGE_STATES = frozenset({"complete", "partial", "unavailable"})
REPLAY_RELATIONSHIPS = frozenset(
    {"exact-input", "stale-input", "foreign-input", "unbound"}
)
AUTHORITY_BASES = frozenset(
    {
        "kernel-check",
        "elaborator-check",
        "producer-assertion",
        "source-observation",
        "external-attestation",
        "process-observation",
        "policy-observation",
        "explicit-pinned-application-check",
        "ambient-selected-application-check",
        "stored-observation",
    }
)
GUARANTEE_SCOPES = frozenset(
    {
        "declaration-type",
        "declaration-value",
        "build",
        "route",
        "source-surface",
        "schema-only",
        "process-exit",
        "none",
    }
)


def _owned(value: Any) -> Any:
    return json.loads(canonical_bytes(_json_value(value)).decode("utf-8"))


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _enum(field_name: str, value: str, allowed: frozenset[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}")


def _own_attributes(instance: Any, field_names: tuple[str, ...]) -> None:
    """Detach producer-owned JSON values from caller mutation."""

    for field_name in field_names:
        object.__setattr__(instance, field_name, _owned(getattr(instance, field_name)))


def _validate_optional_digest(field_name: str, value: str | None) -> None:
    if value is not None and not _digest(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _validate_check_run(run: CheckRun) -> None:
    if not run.check_run_id or not run.check_kind or not run.operation:
        raise ValueError("check run identity, kind, and operation must be non-empty")
    if not _digest(run.environment_ref):
        raise ValueError("check run environment must be a sha256 digest")
    if not all(_digest(artifact_id) for artifact_id in run.input_artifact_ids):
        raise ValueError("check run input artifacts must be sha256 digests")
    _validate_optional_digest("stdoutDigest", run.stdout_digest)
    _validate_optional_digest("stderrDigest", run.stderr_digest)


def _validate_observation(observation: EvidenceObservation) -> None:
    if not observation.observation_id or not observation.observation_kind:
        raise ValueError("observation identity, kind, and result must be non-empty")
    if not observation.result:
        raise ValueError("observation identity, kind, and result must be non-empty")
    if not _digest(observation.environment_ref):
        raise ValueError("observation environment and support must be sha256 digests")
    if not _digest(observation.supporting_artifact_id):
        raise ValueError("observation environment and support must be sha256 digests")
    _validate_observation_attribution(observation)


def _validate_observation_attribution(observation: EvidenceObservation) -> None:
    allowed_subject_fields = (
        {"kind", "localId"},
        {"artifactRef", "kind", "localId"},
    )
    if set(observation.subject_ref) not in allowed_subject_fields:
        raise ValueError("observation subject must be a typed subject reference")
    if not observation.producer.get("name") or not observation.producer.get("version"):
        raise ValueError("observation producer requires name and version")
    if not all("/" in namespace for namespace in observation.extensions):
        raise ValueError("observation extension names must be versioned namespaces")


@dataclass(frozen=True)
class EvidenceDimensions:
    """Independent evidence dimensions; no field strengthens another."""

    assertion_state: str = "unknown"
    semantic_validation: str = "unchecked"
    freshness: str = "unknown"
    attachment_result: str = "unattached"
    coverage: str = "unavailable"
    replay_relationship: str = "unbound"
    authority_basis: str = "producer-assertion"
    guarantee_scope: str = "none"
    analysis_completeness: str = "not-assessed"

    def __post_init__(self) -> None:
        fields = (
            ("assertionState", self.assertion_state, ASSERTION_STATES),
            ("semanticValidation", self.semantic_validation, SEMANTIC_VALIDATIONS),
            ("freshness", self.freshness, FRESHNESS_STATES),
            ("attachmentResult", self.attachment_result, ATTACHMENT_RESULTS),
            ("coverage", self.coverage, COVERAGE_STATES),
            ("replayRelationship", self.replay_relationship, REPLAY_RELATIONSHIPS),
            ("authorityBasis", self.authority_basis, AUTHORITY_BASES),
            ("guaranteeScope", self.guarantee_scope, GUARANTEE_SCOPES),
            ("analysisCompleteness", self.analysis_completeness, ANALYSIS_COMPLETENESS),
        )
        for field_name, value, allowed in fields:
            _enum(field_name, value, allowed)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> EvidenceDimensions:
        expected = {
            "assertionState",
            "semanticValidation",
            "freshness",
            "attachmentResult",
            "coverage",
            "replayRelationship",
            "authorityBasis",
            "guaranteeScope",
        }
        if set(value) not in (expected, expected | {"analysisCompleteness"}):
            raise ValueError("dimensions must use the closed native field set")
        return cls(
            assertion_state=value["assertionState"],
            semantic_validation=value["semanticValidation"],
            freshness=value["freshness"],
            attachment_result=value["attachmentResult"],
            coverage=value["coverage"],
            replay_relationship=value["replayRelationship"],
            authority_basis=value["authorityBasis"],
            guarantee_scope=value["guaranteeScope"],
            analysis_completeness=value.get("analysisCompleteness", "not-assessed"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "assertionState": self.assertion_state,
            "semanticValidation": self.semantic_validation,
            "freshness": self.freshness,
            "attachmentResult": self.attachment_result,
            "coverage": self.coverage,
            "replayRelationship": self.replay_relationship,
            "authorityBasis": self.authority_basis,
            "guaranteeScope": self.guarantee_scope,
            "analysisCompleteness": self.analysis_completeness,
        }


@dataclass(frozen=True)
class Limitation:
    """Stable machine identifier paired with a human-readable nonclaim."""

    limitation_id: str
    message: str

    def __post_init__(self) -> None:
        if not self.limitation_id or not self.message:
            raise ValueError("limitation ID and message must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {"id": self.limitation_id, "message": self.message}


@dataclass(frozen=True)
class CheckRun:
    """Supervised process observation with separate per-subject results."""

    check_run_id: str
    check_kind: str
    checker: Mapping[str, Any]
    environment_ref: str
    input_artifact_ids: tuple[str, ...]
    operation: str
    process_outcome: str
    subject_results: tuple[Mapping[str, Any], ...] = ()
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    resource_bounds: Mapping[str, Any] = field(default_factory=dict)
    guarantee: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_check_run(self)
        _own_attributes(
            self, ("checker", "subject_results", "resource_bounds", "guarantee")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkRunId": self.check_run_id,
            "checkKind": self.check_kind,
            "checker": _owned(self.checker),
            "environmentRef": self.environment_ref,
            "inputArtifactIds": list(self.input_artifact_ids),
            "operation": self.operation,
            "processOutcome": self.process_outcome,
            "subjectResults": _owned(self.subject_results),
            "stdoutDigest": self.stdout_digest,
            "stderrDigest": self.stderr_digest,
            "resourceBounds": _owned(self.resource_bounds),
            "guarantee": _owned(self.guarantee),
        }


@dataclass(frozen=True)
class EvidenceObservation:
    """One producer observation about one exact environment-scoped subject."""

    observation_id: str
    subject_ref: Mapping[str, Any]
    environment_ref: str
    observation_kind: str
    result: str
    dimensions: EvidenceDimensions
    producer: Mapping[str, Any]
    limitations: tuple[Limitation, ...]
    supporting_artifact_id: str
    checker_ref: Mapping[str, Any] | None = None
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_observation(self)
        _own_attributes(self, ("subject_ref", "producer", "checker_ref", "extensions"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "observationId": self.observation_id,
            "subjectRef": _owned(self.subject_ref),
            "environmentRef": self.environment_ref,
            "observationKind": self.observation_kind,
            "result": self.result,
            "dimensions": self.dimensions.to_dict(),
            "producer": _owned(self.producer),
            "limitations": [row.to_dict() for row in self.limitations],
            "supportingArtifactId": self.supporting_artifact_id,
            "checker": _owned(self.checker_ref),
            "extensions": _owned(self.extensions),
        }


@dataclass(frozen=True)
class Coverage:
    """Population-scoped completeness with attributable omissions."""

    status: str
    population_kind: str
    selector: Mapping[str, Any]
    universe_known: bool
    expected: int
    discovered: int = 0
    decoded: int = 0
    valid: int = 0
    projected: int = 0
    query_matched: int = 0
    omitted: tuple[Mapping[str, Any], ...] = ()
    bounds: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _enum("coverage status", self.status, COVERAGE_STATES)
        if not self.population_kind or not isinstance(self.universe_known, bool):
            raise ValueError("coverage population and universe state are required")
        counts = (
            self.expected,
            self.discovered,
            self.decoded,
            self.valid,
            self.projected,
            self.query_matched,
        )
        if any(
            not isinstance(count, int) or isinstance(count, bool) or count < 0
            for count in counts
        ):
            raise ValueError("coverage counts must be non-negative integers")
        if (
            not (
                self.expected
                >= self.discovered
                >= self.decoded
                >= self.valid
                >= self.projected
            )
            or self.query_matched > self.projected
        ):
            raise ValueError("coverage counts must be monotone and query-scoped")
        self._validate_status_consistency()
        for field_name in ("selector", "omitted", "bounds"):
            object.__setattr__(self, field_name, _owned(getattr(self, field_name)))

    def _validate_status_consistency(self) -> None:
        population_counts = (
            self.expected,
            self.discovered,
            self.decoded,
            self.valid,
            self.projected,
        )
        if self.status == "complete" and (
            not self.universe_known or self.omitted or len(set(population_counts)) != 1
        ):
            raise ValueError(
                "coverage status complete requires a known, omission-free population"
            )
        unavailable_counts = (
            self.discovered,
            self.decoded,
            self.valid,
            self.projected,
            self.query_matched,
        )
        if self.status == "unavailable" and any(unavailable_counts):
            raise ValueError(
                "coverage status unavailable cannot report observed or projected evidence"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "population": {
                "kind": self.population_kind,
                "selector": _owned(self.selector),
            },
            "universeKnown": self.universe_known,
            "expected": self.expected,
            "discovered": self.discovered,
            "decoded": self.decoded,
            "valid": self.valid,
            "projected": self.projected,
            "queryMatched": self.query_matched,
            "omitted": _owned(self.omitted),
            "bounds": _owned(self.bounds),
        }


__all__ = [
    "ASSERTION_STATES",
    "ATTACHMENT_RESULTS",
    "AUTHORITY_BASES",
    "COVERAGE_STATES",
    "FRESHNESS_STATES",
    "GUARANTEE_SCOPES",
    "REPLAY_RELATIONSHIPS",
    "SEMANTIC_VALIDATIONS",
    "CheckRun",
    "Coverage",
    "EvidenceDimensions",
    "EvidenceObservation",
    "Limitation",
]
