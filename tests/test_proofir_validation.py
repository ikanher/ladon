from __future__ import annotations

import pytest

from ladon.proofir_validation import VALIDATION_STAGES, ProofIRDiagnostic, omission


def test_validation_diagnostics_are_stable_and_attributable() -> None:
    diagnostic = omission(
        "sha256:artifact",
        stage="reference-valid",
        code="missing-endpoint",
        message="edge endpoint is absent",
        pointer="/edges/0/target",
    )
    assert diagnostic.to_dict() == {
        "artifactId": "sha256:artifact",
        "stage": "reference-valid",
        "code": "missing-endpoint",
        "message": "edge endpoint is absent",
        "pointer": "/edges/0/target",
        "retained": False,
    }


def test_unknown_validation_stage_is_rejected() -> None:
    assert "projected" in VALIDATION_STAGES
    with pytest.raises(ValueError, match="validation stage"):
        ProofIRDiagnostic("a", "not-a-stage", "code", "message")
