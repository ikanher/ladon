"""Refinement evidence accepts only lossless JSON-native records."""

import pytest

from ladon.proof_contract_refinement import classify_lift_result


@pytest.mark.parametrize(
    "assignment",
    [
        {"x": ("1/2",)},
        {"x": {"nested": {1: "1/2"}}},
    ],
)
def test_evidence_projection_rejects_lossy_python_values(assignment):
    witness = {"id": "w-1", "status": "abstract-countermodel", "assignment": assignment}
    attempt = {
        "status": "search-incomplete",
        "reason": "deadline-exhausted",
        "evidence": "lift-attempt-1",
    }

    with pytest.raises(ValueError, match="JSON-native"):
        classify_lift_result(witness, attempt)
