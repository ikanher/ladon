from __future__ import annotations

import pytest

from ladon.proofir_result_dimensions import derive_analysis_completeness, project_dimensions


@pytest.mark.parametrize(
    ("name", "operation_valid", "populations", "residuals", "omissions", "truncated", "expected"),
    [
        ("explicit-live", True, 1, 0, 0, False, "complete"),
        ("ambient-live", True, 1, 0, 0, False, "complete"),
        ("stored-observation", True, 1, 0, 0, False, "complete"),
        ("residual-application", True, 1, 1, 0, False, "partial"),
        ("partial-coverage", True, 1, 0, 1, False, "partial"),
        ("invalid-child", False, 1, 0, 0, False, "invalid"),
        ("truncated", True, 1, 0, 0, True, "partial"),
        ("analysis-not-run", True, 0, 0, 0, False, "not-assessed"),
    ],
)
def test_projection_corpus_keeps_authority_and_completeness_orthogonal(
    name: str,
    operation_valid: bool,
    populations: int,
    residuals: int,
    omissions: int,
    truncated: bool,
    expected: str,
) -> None:
    completeness = derive_analysis_completeness(
        operation_valid=operation_valid,
        required_populations=populations,
        residuals=residuals,
        omissions=omissions,
        truncated=truncated,
    )
    authority = "ambient-selected-application-check" if name == "ambient-live" else "stored-observation" if name == "stored-observation" else "explicit-pinned-application-check"
    assert project_dimensions(authority, completeness) == (authority, expected)
