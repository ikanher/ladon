"""Closed authority and completeness dimensions for ProofIR projections."""

from __future__ import annotations

AUTHORITY_SELECTIONS = frozenset(
    {
        "not-assessed",
        "ambient-selected-application-check",
        "explicit-pinned-application-check",
        "stored-observation",
    }
)
ANALYSIS_COMPLETENESS = frozenset({"complete", "partial", "invalid", "not-assessed"})
_COMPLETENESS_RANK = {"not-assessed": 0, "partial": 1, "complete": 2, "invalid": -1}


def derive_analysis_completeness(
    *,
    operation_valid: bool,
    required_populations: int,
    residuals: int = 0,
    omissions: int = 0,
    truncated: bool = False,
) -> str:
    """Derive one closed state without treating absent analysis as complete."""
    if not operation_valid:
        return "invalid"
    if required_populations <= 0:
        return "not-assessed"
    if residuals or omissions or truncated:
        return "partial"
    return "complete"


def project_dimensions(
    authority: str,
    completeness: str,
    *,
    parent_authority: str | None = None,
    parent_completeness: str | None = None,
) -> tuple[str, str]:
    """Validate a projection and reject authority/completeness escalation."""
    _validate_dimensions(authority, completeness, parent_authority, parent_completeness)
    _validate_authority_transition(parent_authority, authority)
    if parent_completeness is not None and _COMPLETENESS_RANK[completeness] > _COMPLETENESS_RANK[parent_completeness]:
        raise ValueError("projection cannot strengthen analysis completeness")
    return authority, completeness


def _validate_dimensions(
    authority: str,
    completeness: str,
    parent_authority: str | None,
    parent_completeness: str | None,
) -> None:
    if authority not in AUTHORITY_SELECTIONS:
        raise ValueError(f"unsupported authority selection: {authority}")
    if completeness not in ANALYSIS_COMPLETENESS:
        raise ValueError(f"unsupported analysis completeness: {completeness}")
    if parent_authority is not None and parent_authority not in AUTHORITY_SELECTIONS:
        raise ValueError(f"unsupported parent authority selection: {parent_authority}")
    if parent_completeness is not None and parent_completeness not in ANALYSIS_COMPLETENESS:
        raise ValueError(f"unsupported parent analysis completeness: {parent_completeness}")


def _validate_authority_transition(parent: str | None, child: str) -> None:
    if parent == "stored-observation" and child != "stored-observation":
        raise ValueError("stored observations cannot gain live authority")
    if parent in {"ambient-selected-application-check", "not-assessed"} and child == "explicit-pinned-application-check":
        raise ValueError("authority projection cannot promote to explicit-pinned evidence")


__all__ = [
    "ANALYSIS_COMPLETENESS",
    "AUTHORITY_SELECTIONS",
    "derive_analysis_completeness",
    "project_dimensions",
]
