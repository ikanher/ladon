"""Closed evidence dimensions and non-escalating transition validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXECUTION_BINDINGS = frozenset({"explicit-pinned", "ambient-observed", "none"})
OBSERVATION_STATES = frozenset({"live", "stored", "derived", "absent", "failed"})
OPERATION_OUTCOMES = frozenset({"accepted", "rejected", "failed", "not-run"})
SOURCE_FRESHNESS = frozenset({"fresh", "stale", "unknown", "not-assessed"})
ENVIRONMENT_MATCHES = frozenset({"exact", "mismatched", "unknown", "not-assessed"})
AUTHORITY_BASES = frozenset(
    {
        "not-assessed",
        "producer-assertion",
        "source-observation",
        "elaborator-check",
        "kernel-check",
        "stored-observation",
    }
)
ANALYSIS_COMPLETENESS = frozenset({"complete", "partial", "invalid", "not-assessed"})

_TRANSITIONS = {
    "executionBinding": {
        "explicit-pinned": EXECUTION_BINDINGS,
        "ambient-observed": frozenset({"ambient-observed", "none"}),
        "none": frozenset({"none"}),
    },
    "observationState": {
        "live": OBSERVATION_STATES,
        "stored": frozenset({"stored", "derived", "failed", "absent"}),
        "derived": frozenset({"derived", "failed", "absent"}),
        "failed": frozenset({"failed", "absent"}),
        "absent": frozenset({"absent"}),
    },
    "operationOutcome": {
        "accepted": frozenset({"accepted"}),
        "rejected": frozenset({"rejected", "failed", "not-run"}),
        "failed": frozenset({"failed", "not-run"}),
        "not-run": frozenset({"not-run"}),
    },
    "sourceFreshness": {
        "fresh": SOURCE_FRESHNESS,
        "stale": frozenset({"stale", "unknown", "not-assessed"}),
        "unknown": frozenset({"unknown", "not-assessed"}),
        "not-assessed": frozenset({"not-assessed"}),
    },
    "environmentMatch": {
        "exact": ENVIRONMENT_MATCHES,
        "mismatched": frozenset({"mismatched", "unknown", "not-assessed"}),
        "unknown": frozenset({"unknown", "not-assessed"}),
        "not-assessed": frozenset({"not-assessed"}),
    },
    "authorityBasis": {
        "kernel-check": AUTHORITY_BASES,
        "elaborator-check": frozenset(
            {
                "elaborator-check",
                "source-observation",
                "producer-assertion",
                "stored-observation",
                "not-assessed",
            }
        ),
        "source-observation": frozenset(
            {"source-observation", "producer-assertion", "stored-observation", "not-assessed"}
        ),
        "producer-assertion": frozenset(
            {"producer-assertion", "stored-observation", "not-assessed"}
        ),
        "stored-observation": frozenset({"stored-observation", "not-assessed"}),
        "not-assessed": frozenset({"not-assessed"}),
    },
    "analysisCompleteness": {
        "complete": ANALYSIS_COMPLETENESS,
        "partial": frozenset({"partial", "invalid", "not-assessed"}),
        "not-assessed": frozenset({"not-assessed", "invalid"}),
        "invalid": frozenset({"invalid"}),
    },
}

_ATTRS = {
    "executionBinding": "execution_binding",
    "observationState": "observation_state",
    "operationOutcome": "operation_outcome",
    "sourceFreshness": "source_freshness",
    "environmentMatch": "environment_match",
    "authorityBasis": "authority_basis",
    "analysisCompleteness": "analysis_completeness",
}


@dataclass(frozen=True)
class EvidenceDimensions:
    execution_binding: str
    observation_state: str
    operation_outcome: str
    source_freshness: str = "unknown"
    environment_match: str = "unknown"
    authority_basis: str = "not-assessed"
    analysis_completeness: str = "not-assessed"

    def __post_init__(self) -> None:
        fields = {
            "execution_binding": (self.execution_binding, EXECUTION_BINDINGS),
            "observation_state": (self.observation_state, OBSERVATION_STATES),
            "operation_outcome": (self.operation_outcome, OPERATION_OUTCOMES),
            "source_freshness": (self.source_freshness, SOURCE_FRESHNESS),
            "environment_match": (self.environment_match, ENVIRONMENT_MATCHES),
            "authority_basis": (self.authority_basis, AUTHORITY_BASES),
            "analysis_completeness": (self.analysis_completeness, ANALYSIS_COMPLETENESS),
        }
        for name, (value, allowed) in fields.items():
            if value not in allowed:
                raise ValueError(f"unsupported evidence dimension {name}: {value}")


def validate_transition(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    """Reject transitions that strengthen an observation or authority axis."""
    violations = [
        _transition_error(axis, parent_value, child_value)
        for axis, attribute in _ATTRS.items()
        if (parent_value := getattr(parent, attribute))
        and (child_value := getattr(child, attribute)) not in _TRANSITIONS[axis][parent_value]
    ]
    violations.extend(_state_violations(child))
    if violations:
        raise ValueError("; ".join(violations))


def transition_matrix() -> dict[str, Any]:
    """Expose every registered state and allowed projection transition."""
    return {
        "schema": "ladon-evidence-transition-matrix-v1",
        "axes": {
            axis: {
                "states": sorted(transitions),
                "allowed": {
                    parent: sorted(children) for parent, children in sorted(transitions.items())
                },
            }
            for axis, transitions in _TRANSITIONS.items()
        },
    }


def validate_evidence_state(dimensions: EvidenceDimensions) -> None:
    """Reject internally contradictory dimension combinations."""
    violations = _state_violations(dimensions)
    if violations:
        raise ValueError("; ".join(violations))


def _transition_error(axis: str, parent: str, child: str) -> str:
    if axis == "observationState" and parent == "stored" and child == "live":
        return "stored observations cannot gain live authority"
    if axis == "analysisCompleteness":
        return "projection cannot strengthen analysis completeness"
    if axis == "authorityBasis":
        return f"authority basis transition {parent} -> {child} is not registered"
    return f"authority-safe {axis} transition {parent} -> {child} is not registered"


def _state_violations(dimensions: EvidenceDimensions) -> list[str]:
    violations: list[str] = []
    if dimensions.operation_outcome == "accepted" and dimensions.observation_state in {
        "absent",
        "failed",
    }:
        violations.append("accepted outcome requires an attributable observation")
    if dimensions.observation_state == "live" and dimensions.execution_binding == "none":
        violations.append("live observation requires an executed binding")
    if dimensions.operation_outcome == "not-run" and (
        dimensions.observation_state == "live"
        or dimensions.authority_basis in {"elaborator-check", "kernel-check"}
        or dimensions.analysis_completeness == "complete"
    ):
        violations.append(
            "not-run outcome cannot claim live checker authority or complete analysis"
        )
    if dimensions.authority_basis in {
        "elaborator-check",
        "kernel-check",
    } and dimensions.observation_state in {"absent", "failed"}:
        violations.append("checker authority requires an attributable observation")
    if (
        dimensions.execution_binding == "explicit-pinned"
        and dimensions.environment_match == "mismatched"
    ):
        violations.append("explicit-pinned execution cannot use a mismatched environment")
    return violations


__all__ = [
    "ANALYSIS_COMPLETENESS",
    "AUTHORITY_BASES",
    "ENVIRONMENT_MATCHES",
    "EXECUTION_BINDINGS",
    "OBSERVATION_STATES",
    "OPERATION_OUTCOMES",
    "SOURCE_FRESHNESS",
    "EvidenceDimensions",
    "transition_matrix",
    "validate_evidence_state",
    "validate_transition",
]
