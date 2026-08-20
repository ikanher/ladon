from __future__ import annotations

import pytest

from ladon.evidence_dimensions import EvidenceDimensions, validate_transition


def test_evidence_dimensions_reject_authority_and_observation_escalation() -> None:
    parent = EvidenceDimensions("ambient-observed", "stored", "accepted", "stale", "mismatched")
    child = EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact")
    with pytest.raises(ValueError, match="stored"):
        validate_transition(parent, child)


def test_evidence_dimensions_accept_weakened_projection() -> None:
    parent = EvidenceDimensions("explicit-pinned", "live", "accepted", "fresh", "exact")
    child = EvidenceDimensions("ambient-observed", "derived", "rejected", "unknown", "unknown")
    validate_transition(parent, child)
