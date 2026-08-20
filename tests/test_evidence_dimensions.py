from __future__ import annotations

import pytest

from ladon.evidence_dimensions import EvidenceDimensions, transition_matrix, validate_transition


def test_evidence_dimensions_reject_authority_and_observation_escalation() -> None:
    parent = EvidenceDimensions("ambient-observed", "stored", "accepted", "stale", "mismatched")
    child = EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact")
    with pytest.raises(ValueError, match="stored"):
        validate_transition(parent, child)


def test_evidence_dimensions_accept_weakened_projection() -> None:
    parent = EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact")
    child = EvidenceDimensions("ambient-observed", "derived", "rejected", "unknown", "unknown")
    validate_transition(parent, child)


def test_transition_matrix_is_closed_and_machine_readable() -> None:
    matrix = transition_matrix()
    assert set(matrix) == {
        "executionBinding",
        "observationState",
        "operationOutcome",
        "sourceFreshness",
        "environmentMatch",
        "authorityBasis",
        "analysisCompleteness",
    }
    assert "explicit-pinned" in matrix["executionBinding"]


@pytest.mark.parametrize(
    ("parent", "child", "message"),
    [
        (
            EvidenceDimensions("none", "absent", "not-run"),
            EvidenceDimensions("explicit-pinned", "live", "accepted"),
            "absent",
        ),
        (
            EvidenceDimensions("explicit-pinned", "live", "accepted", "stale", "mismatched"),
            EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact"),
            "stale",
        ),
        (
            EvidenceDimensions("explicit-pinned", "live", "accepted", authority_basis="producer-assertion"),
            EvidenceDimensions("explicit-pinned", "live", "accepted", authority_basis="kernel-check"),
            "authority basis",
        ),
    ],
)
def test_registered_transition_owner_rejects_escalation(
    parent: EvidenceDimensions, child: EvidenceDimensions, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_transition(parent, child)
