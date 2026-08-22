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
    child = EvidenceDimensions("ambient-observed", "derived", "accepted", "unknown", "unknown")
    validate_transition(parent, child)


def test_transition_rejects_contradictory_parent_state() -> None:
    parent = EvidenceDimensions(
        "explicit-pinned", "failed", "accepted", authority_basis="elaborator-check"
    )
    child = EvidenceDimensions("none", "absent", "accepted")
    with pytest.raises(ValueError, match="accepted outcome requires"):
        validate_transition(parent, child)


def test_transition_matrix_is_closed_and_machine_readable() -> None:
    matrix = transition_matrix()
    assert matrix["schema"] == "ladon-evidence-transition-matrix-v1"
    assert set(matrix["axes"]) == {
        "executionBinding",
        "observationState",
        "operationOutcome",
        "sourceFreshness",
        "environmentMatch",
        "authorityBasis",
        "analysisCompleteness",
    }
    assert "explicit-pinned" in matrix["axes"]["executionBinding"]["states"]
    assert matrix["axes"]["executionBinding"]["allowed"]["none"] == ["none"]


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
            EvidenceDimensions(
                "explicit-pinned", "live", "accepted", authority_basis="producer-assertion"
            ),
            EvidenceDimensions(
                "explicit-pinned", "live", "accepted", authority_basis="kernel-check"
            ),
            "authority basis",
        ),
    ],
)
def test_registered_transition_owner_rejects_escalation(
    parent: EvidenceDimensions, child: EvidenceDimensions, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_transition(parent, child)


@pytest.mark.parametrize(
    ("parent", "child"),
    [
        (
            EvidenceDimensions("none", "absent", "not-run"),
            EvidenceDimensions("ambient-observed", "absent", "not-run"),
        ),
        (
            EvidenceDimensions("ambient-observed", "derived", "rejected"),
            EvidenceDimensions("ambient-observed", "live", "rejected"),
        ),
        (
            EvidenceDimensions("ambient-observed", "stored", "rejected"),
            EvidenceDimensions("ambient-observed", "stored", "accepted"),
        ),
        (
            EvidenceDimensions("ambient-observed", "stored", "rejected", "unknown"),
            EvidenceDimensions("ambient-observed", "stored", "rejected", "fresh"),
        ),
        (
            EvidenceDimensions(
                "ambient-observed", "stored", "rejected", environment_match="unknown"
            ),
            EvidenceDimensions("ambient-observed", "stored", "rejected", environment_match="exact"),
        ),
    ],
)
def test_transition_matrix_rejects_reviewed_promotions(
    parent: EvidenceDimensions, child: EvidenceDimensions
) -> None:
    with pytest.raises(ValueError, match="not registered"):
        validate_transition(parent, child)
