"""Closed evidence dimensions and non-escalating transition validation."""

from __future__ import annotations

from dataclasses import dataclass

EXECUTION_BINDINGS = frozenset({"explicit-pinned", "ambient-observed", "none"})
OBSERVATION_STATES = frozenset({"live", "stored", "derived", "absent", "failed"})
OPERATION_OUTCOMES = frozenset({"accepted", "rejected", "failed", "not-run"})
SOURCE_FRESHNESS = frozenset({"fresh", "stale", "unknown", "not-assessed"})
ENVIRONMENT_MATCHES = frozenset({"exact", "mismatched", "unknown", "not-assessed"})
AUTHORITY_BASES = frozenset(
    {"not-assessed", "producer-assertion", "source-observation", "elaborator-check", "kernel-check", "stored-observation"}
)
ANALYSIS_COMPLETENESS = frozenset({"complete", "partial", "invalid", "not-assessed"})


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
    violations: list[str] = []
    for validator in (
        _validate_freshness,
        _validate_authority,
        _validate_completeness,
        _validate_observation,
        _validate_outcome,
        _validate_basis,
    ):
        try:
            validator(parent, child)
        except ValueError as error:
            violations.append(str(error))
    if violations:
        raise ValueError("; ".join(violations))


def transition_matrix() -> dict[str, tuple[str, ...]]:
    """Expose the registered closed states for machine-readable gate generation."""
    return {
        "executionBinding": tuple(sorted(EXECUTION_BINDINGS)),
        "observationState": tuple(sorted(OBSERVATION_STATES)),
        "operationOutcome": tuple(sorted(OPERATION_OUTCOMES)),
        "sourceFreshness": tuple(sorted(SOURCE_FRESHNESS)),
        "environmentMatch": tuple(sorted(ENVIRONMENT_MATCHES)),
        "authorityBasis": tuple(sorted(AUTHORITY_BASES)),
        "analysisCompleteness": tuple(sorted(ANALYSIS_COMPLETENESS)),
    }


def _validate_observation(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.observation_state == "stored" and child.observation_state == "live":
        raise ValueError("stored observations cannot gain live authority")
    if parent.observation_state == "absent" and child.observation_state not in {"absent", "failed"}:
        raise ValueError("absent evidence cannot gain an observation")


def _validate_authority(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.execution_binding != "explicit-pinned" and child.execution_binding == "explicit-pinned":
        raise ValueError("authority execution binding cannot be promoted to explicit-pinned")
    if parent.environment_match == "mismatched" and child.environment_match == "exact":
        raise ValueError("mismatched environment cannot become exact")


def _validate_freshness(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.source_freshness == "stale" and child.source_freshness == "fresh":
        raise ValueError("stale source evidence cannot become fresh")


def _validate_outcome(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.operation_outcome in {"not-run", "failed"} and child.operation_outcome == "accepted":
        raise ValueError("an unrun or failed operation cannot become accepted")


def _validate_completeness(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    rank = {"invalid": -1, "not-assessed": 0, "partial": 1, "complete": 2}
    if rank[child.analysis_completeness] > rank[parent.analysis_completeness]:
        raise ValueError("projection cannot strengthen analysis completeness")


def _validate_basis(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    rank = {"not-assessed": 0, "producer-assertion": 1, "source-observation": 1, "stored-observation": 1, "elaborator-check": 2, "kernel-check": 3}
    if rank[child.authority_basis] > rank[parent.authority_basis] and parent.authority_basis != "not-assessed":
        raise ValueError("authority basis cannot be promoted")


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
    "validate_transition",
]
