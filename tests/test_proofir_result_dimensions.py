from __future__ import annotations

import pytest

from ladon.proofir_result_dimensions import (
    derive_analysis_completeness,
    project_dimensions,
)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"operation_valid": False, "required_populations": 1}, "invalid"),
        ({"operation_valid": True, "required_populations": 0}, "not-assessed"),
        ({"operation_valid": True, "required_populations": 1, "residuals": 1}, "partial"),
        ({"operation_valid": True, "required_populations": 1}, "complete"),
    ],
)
def test_completeness_is_closed_and_exhaustive(kwargs: dict[str, object], expected: str) -> None:
    assert derive_analysis_completeness(**kwargs) == expected  # type: ignore[arg-type]


def test_projection_rejects_dimension_escalation() -> None:
    with pytest.raises(ValueError, match="stored observations"):
        project_dimensions(
            "explicit-pinned-application-check",
            "partial",
            parent_authority="stored-observation",
        )
    with pytest.raises(ValueError, match="strengthen"):
        project_dimensions(
            "stored-observation",
            "complete",
            parent_completeness="partial",
        )
