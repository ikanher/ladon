"""Closed evidence dimensions and non-escalating transition validation."""

from __future__ import annotations

from dataclasses import dataclass

EXECUTION_BINDINGS = frozenset({"explicit-pinned", "ambient-observed", "none"})
OBSERVATION_STATES = frozenset({"live", "stored", "derived", "absent", "failed"})
OPERATION_OUTCOMES = frozenset({"accepted", "rejected", "failed", "not-run"})
SOURCE_FRESHNESS = frozenset({"fresh", "stale", "unknown", "not-assessed"})
ENVIRONMENT_MATCHES = frozenset({"exact", "mismatched", "unknown", "not-assessed"})


@dataclass(frozen=True)
class EvidenceDimensions:
    execution_binding: str
    observation_state: str
    operation_outcome: str
    source_freshness: str = "unknown"
    environment_match: str = "unknown"

    def __post_init__(self) -> None:
        fields = {
            "execution_binding": (self.execution_binding, EXECUTION_BINDINGS),
            "observation_state": (self.observation_state, OBSERVATION_STATES),
            "operation_outcome": (self.operation_outcome, OPERATION_OUTCOMES),
            "source_freshness": (self.source_freshness, SOURCE_FRESHNESS),
            "environment_match": (self.environment_match, ENVIRONMENT_MATCHES),
        }
        for name, (value, allowed) in fields.items():
            if value not in allowed:
                raise ValueError(f"unsupported evidence dimension {name}: {value}")


def validate_transition(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    """Reject transitions that strengthen an observation or authority axis."""
    _validate_observation(parent, child)
    _validate_authority(parent, child)
    _validate_freshness(parent, child)


def _validate_observation(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.observation_state == "stored" and child.observation_state == "live":
        raise ValueError("stored evidence cannot become live")
    if parent.observation_state == "absent" and child.observation_state not in {"absent", "failed"}:
        raise ValueError("absent evidence cannot gain an observation")


def _validate_authority(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.execution_binding != "explicit-pinned" and child.execution_binding == "explicit-pinned":
        raise ValueError("execution binding cannot be promoted to explicit-pinned")
    if parent.environment_match == "mismatched" and child.environment_match == "exact":
        raise ValueError("mismatched environment cannot become exact")


def _validate_freshness(parent: EvidenceDimensions, child: EvidenceDimensions) -> None:
    if parent.source_freshness == "stale" and child.source_freshness == "fresh":
        raise ValueError("stale source evidence cannot become fresh")


__all__ = [
    "ENVIRONMENT_MATCHES",
    "EXECUTION_BINDINGS",
    "OBSERVATION_STATES",
    "OPERATION_OUTCOMES",
    "SOURCE_FRESHNESS",
    "EvidenceDimensions",
    "validate_transition",
]
