"""Coverage operations for derived evidence and snapshot drift."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable

from ladon.coverage_base import (
    CollectionCoverage,
    CoverageCause,
    CoverageError,
    CoverageRegistry,
)


DERIVED_CLAIM_KINDS = frozenset(
    {"positive_witness", "exhaustive", "absence"}
)
DERIVED_COVERAGE_STATUSES = frozenset(
    {"available", "subset", "unavailable"}
)


@dataclass(frozen=True)
class DerivedCoverage:
    """Coverage disposition for evidence derived from registered collections."""

    coverage_refs: tuple[str, ...]
    claim_kind: str
    status: str
    exhaustive: bool
    component_authorities: tuple[str, ...]
    nonclaims: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_derived_inputs(self)
        _validate_derived_disposition(self)

    def to_dict(self) -> dict[str, Any]:
        """Return the generic derived-evidence coverage envelope."""

        return {
            "coverageRefs": list(self.coverage_refs),
            "claimKind": self.claim_kind,
            "status": self.status,
            "exhaustive": self.exhaustive,
            "componentAuthorities": list(self.component_authorities),
            "nonclaims": list(self.nonclaims),
        }


def derive_coverage(
    registry: CoverageRegistry,
    coverage_refs: Iterable[str],
    *,
    claim_kind: str,
) -> DerivedCoverage:
    """Classify an exhaustive, absence, or subset-safe derived claim.

    Positive witnesses remain useful over incomplete inputs, but the result is
    explicitly a visible subset. Exhaustive and absence claims fail closed
    whenever any required population is incomplete or fingerprint-incompatible.
    """

    references = tuple(sorted(set(coverage_refs)))
    _validate_derive_request(references, claim_kind)
    rows = tuple(registry.require(reference) for reference in references)
    require_compatible_fingerprints(rows)
    authorities = tuple(sorted({row.authority for row in rows}))
    if all(row.completeness == "complete" for row in rows):
        return _available_derived_coverage(
            references,
            claim_kind,
            authorities,
        )
    return _incomplete_derived_coverage(
        references,
        claim_kind,
        authorities,
    )


def mark_coverage_unstable(
    registry: CoverageRegistry,
    *,
    detail: str = (
        "registered source or configuration state changed during analysis"
    ),
) -> CoverageRegistry:
    """Return the same populations with one shared source-drift disposition."""

    cause = CoverageCause(
        kind="drift",
        identifier="source_changed_during_analysis",
        detail=detail,
    )
    return CoverageRegistry(
        {
            identity: replace(
                row,
                completeness="unstable",
                causes=(
                    row.causes
                    if cause in row.causes
                    else (*row.causes, cause)
                ),
            )
            for identity, row in registry.collections.items()
        }
    )


def require_compatible_fingerprints(
    rows: Iterable[CollectionCoverage],
) -> None:
    """Reject derivation across conflicting non-null evidence identities."""

    values = tuple(rows)
    for field_name in (
        "source_fingerprint",
        "scope_fingerprint",
        "analysis_fingerprint",
    ):
        fingerprints = {
            getattr(row, field_name)
            for row in values
            if getattr(row, field_name) is not None
        }
        if len(fingerprints) > 1:
            raise CoverageError(
                f"incompatible coverage {field_name.replace('_', ' ')}"
            )


def _validate_derive_request(
    references: tuple[str, ...],
    claim_kind: str,
) -> None:
    if not references:
        raise CoverageError(
            "derived evidence requires at least one coverage reference"
        )
    if claim_kind not in DERIVED_CLAIM_KINDS:
        raise CoverageError(
            f"unsupported derived coverage claim kind: {claim_kind}"
        )


def _available_derived_coverage(
    references: tuple[str, ...],
    claim_kind: str,
    authorities: tuple[str, ...],
) -> DerivedCoverage:
    return DerivedCoverage(
        coverage_refs=references,
        claim_kind=claim_kind,
        status="available",
        exhaustive=True,
        component_authorities=authorities,
    )


def _incomplete_derived_coverage(
    references: tuple[str, ...],
    claim_kind: str,
    authorities: tuple[str, ...],
) -> DerivedCoverage:
    if claim_kind == "positive_witness":
        return DerivedCoverage(
            coverage_refs=references,
            claim_kind=claim_kind,
            status="subset",
            exhaustive=False,
            component_authorities=authorities,
            nonclaims=(
                "The witness is present in the visible subset; omitted rows "
                "may add further witnesses.",
            ),
        )
    return DerivedCoverage(
        coverage_refs=references,
        claim_kind=claim_kind,
        status="unavailable",
        exhaustive=False,
        component_authorities=authorities,
        nonclaims=(
            "Incomplete required collections do not support an exhaustive "
            "or repository-wide absence claim.",
        ),
    )


def _validate_derived_inputs(row: DerivedCoverage) -> None:
    if not row.coverage_refs or any(not ref for ref in row.coverage_refs):
        raise CoverageError(
            "derived evidence requires canonical coverage references"
        )
    if row.claim_kind not in DERIVED_CLAIM_KINDS:
        raise CoverageError(
            f"unsupported derived coverage claim kind: {row.claim_kind}"
        )
    if row.status not in DERIVED_COVERAGE_STATUSES:
        raise CoverageError(
            f"unsupported derived coverage status: {row.status}"
        )
    if not row.component_authorities or any(
        not authority for authority in row.component_authorities
    ):
        raise CoverageError(
            "derived evidence requires its component authorities"
        )


def _validate_derived_disposition(row: DerivedCoverage) -> None:
    if row.exhaustive != (row.status == "available"):
        raise CoverageError(
            "only fully available derived evidence may be exhaustive"
        )
    if row.status != "available" and not row.nonclaims:
        raise CoverageError(
            "non-exhaustive derived evidence requires explicit nonclaims"
        )


__all__ = [
    "DERIVED_CLAIM_KINDS",
    "DERIVED_COVERAGE_STATUSES",
    "DerivedCoverage",
    "derive_coverage",
    "mark_coverage_unstable",
    "require_compatible_fingerprints",
]
