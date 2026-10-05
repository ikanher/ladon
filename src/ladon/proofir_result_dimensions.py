"""Closed authority and completeness dimensions for ProofIR projections."""

from __future__ import annotations

from ladon.evidence_dimensions import EvidenceDimensions, validate_transition

AUTHORITY_SELECTIONS = frozenset(
    {
        "not-assessed",
        "ambient-selected-application-check",
        "explicit-pinned-application-check",
        "stored-observation",
    }
)
ANALYSIS_COMPLETENESS = frozenset({"complete", "partial", "invalid", "not-assessed"})


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
    projection_kind: str = "json-renderer",
) -> tuple[str, str]:
    """Validate a projection and reject authority/completeness escalation."""
    _validate_dimensions(authority, completeness, parent_authority, parent_completeness)
    if parent_authority is not None or parent_completeness is not None:
        parent = _projection_dimensions(parent_authority, parent_completeness)
        child = _projection_dimensions(authority, completeness)
        validate_transition(parent, child, projection_kind=projection_kind)
    return authority, completeness


def _projection_dimensions(authority: str | None, completeness: str | None) -> EvidenceDimensions:
    """Adapt the legacy ProofIR pair to the shared transition owner."""

    if authority in {None, "not-assessed"}:
        return EvidenceDimensions("none", "absent", "not-run", analysis_completeness=completeness or "not-assessed")
    if authority == "stored-observation":
        return EvidenceDimensions("none", "stored", "accepted", analysis_completeness=completeness or "not-assessed", authority_basis="stored-observation")
    if authority == "ambient-selected-application-check":
        return EvidenceDimensions("ambient-observed", "live", "accepted", analysis_completeness=completeness or "not-assessed", authority_basis="elaborator-check")
    return EvidenceDimensions("explicit-pinned", "live", "accepted", analysis_completeness=completeness or "not-assessed", authority_basis="elaborator-check")


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


__all__ = [
    "ANALYSIS_COMPLETENESS",
    "AUTHORITY_SELECTIONS",
    "derive_analysis_completeness",
    "project_dimensions",
]
