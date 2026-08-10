from __future__ import annotations

from ladon.proofir_validation import v3_diagnostics


def test_v3_invalid_version_has_stable_diagnostic_vector() -> None:
    rows = v3_diagnostics({"artifactId": "sha256:invalid", "proofirVersion": "2.0"})
    assert [row.to_dict() for row in rows] == [{
        "artifactId": "sha256:invalid",
        "stage": "envelope-valid",
        "code": "unsupported-version",
        "message": "unsupported ProofIR version",
        "pointer": "/proofirVersion",
        "retained": False,
    }]
