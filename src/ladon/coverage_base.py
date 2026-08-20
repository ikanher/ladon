"""Canonical collection-coverage value objects and validation.

This module owns only the collection-level contract.  Derived-claim logic and
report-producer registrations live in separate modules so changes to those
surfaces cannot silently entangle the base evidence envelope.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

COVERAGE_SCHEMA = "ladon-collection-coverage-v1"
COVERAGE_COMPLETENESS = frozenset(
    {"complete", "partial", "unavailable", "unstable"}
)
COVERAGE_CAUSE_KINDS = frozenset(
    {"extraction", "analysis", "projection", "drift", "compatibility"}
)


class CoverageError(ValueError):
    """Raised when collection coverage would overstate observed evidence."""


@dataclass(frozen=True)
class CoverageCause:
    """One typed reason that a collection is not fully visible or stable."""

    kind: str
    identifier: str
    detail: str
    controlling_cap: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in COVERAGE_CAUSE_KINDS:
            raise CoverageError(f"unsupported coverage cause kind: {self.kind}")
        if not self.identifier or not self.detail:
            raise CoverageError(
                "coverage cause identifier and detail must be non-empty"
            )
        if self.controlling_cap is not None:
            nonnegative_int(self.controlling_cap, "controlling_cap")

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible cause."""

        return {
            "kind": self.kind,
            "id": self.identifier,
            "detail": self.detail,
            "controllingCap": self.controlling_cap,
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> CoverageCause:
        """Parse one canonical coverage cause."""

        cap = row.get("controllingCap")
        return cls(
            kind=str(row.get("kind", "")),
            identifier=str(row.get("id", "")),
            detail=str(row.get("detail", "")),
            controlling_cap=(
                nonnegative_int(cap, "controllingCap")
                if cap is not None
                else None
            ),
        )


@dataclass(frozen=True)
class CollectionCoverage:
    """Truthful visibility for one canonical evidence collection."""

    identity: str
    pointer: str
    visible: int
    observed_lower_bound: int
    total_known: bool
    total: int | None
    omitted: int | None
    completeness: str
    population: str
    scope: str
    authority: str
    source_fingerprint: str | None = None
    scope_fingerprint: str | None = None
    analysis_fingerprint: str | None = None
    causes: tuple[CoverageCause, ...] = ()

    def __post_init__(self) -> None:
        visible, observed = _validate_coverage_identity_and_counts(self)
        _validate_coverage_total(self, visible=visible, observed=observed)
        _validate_coverage_causes(self)

    @classmethod
    def exact(
        cls,
        *,
        identity: str,
        pointer: str,
        visible: int,
        total: int,
        population: str,
        scope: str,
        authority: str,
        observed_lower_bound: int | None = None,
        causes: Iterable[CoverageCause] = (),
        source_fingerprint: str | None = None,
        scope_fingerprint: str | None = None,
        analysis_fingerprint: str | None = None,
    ) -> CollectionCoverage:
        """Build known coverage, complete exactly when nothing is omitted."""

        cause_rows = tuple(causes)
        omitted = total - visible
        completeness = (
            "complete" if omitted == 0 and not cause_rows else "partial"
        )
        return cls(
            identity=identity,
            pointer=pointer,
            visible=visible,
            observed_lower_bound=(
                visible
                if observed_lower_bound is None
                else observed_lower_bound
            ),
            total_known=True,
            total=total,
            omitted=omitted,
            completeness=completeness,
            population=population,
            scope=scope,
            authority=authority,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            causes=cause_rows,
        )

    @classmethod
    def unknown(
        cls,
        *,
        identity: str,
        pointer: str,
        visible: int,
        observed_lower_bound: int,
        completeness: str,
        population: str,
        scope: str,
        authority: str,
        causes: Iterable[CoverageCause],
        source_fingerprint: str | None = None,
        scope_fingerprint: str | None = None,
        analysis_fingerprint: str | None = None,
    ) -> CollectionCoverage:
        """Build explicit unknown-total coverage without inventing omission."""

        return cls(
            identity=identity,
            pointer=pointer,
            visible=visible,
            observed_lower_bound=observed_lower_bound,
            total_known=False,
            total=None,
            omitted=None,
            completeness=completeness,
            population=population,
            scope=scope,
            authority=authority,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            causes=tuple(causes),
        )

    def projected(
        self,
        *,
        identity: str,
        pointer: str,
        visible: int,
        cause: CoverageCause,
    ) -> CollectionCoverage:
        """Derive a bounded surface while retaining upstream population truth."""

        visible = nonnegative_int(visible, "visible")
        if visible > self.visible:
            raise CoverageError(
                "a projection cannot expose more rows than its source surface"
            )
        causes = (*self.causes, cause)
        common = {
            "identity": identity,
            "pointer": pointer,
            "visible": visible,
            "population": self.population,
            "scope": self.scope,
            "authority": self.authority,
            "causes": causes,
            "source_fingerprint": self.source_fingerprint,
            "scope_fingerprint": self.scope_fingerprint,
            "analysis_fingerprint": self.analysis_fingerprint,
        }
        if self.total_known:
            if self.total is None:
                raise AssertionError("validated known coverage lost its total")
            return CollectionCoverage.exact(
                total=self.total,
                observed_lower_bound=self.observed_lower_bound,
                **common,
            )
        return CollectionCoverage.unknown(
            observed_lower_bound=self.observed_lower_bound,
            completeness=self.completeness,
            **common,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical JSON-compatible coverage envelope."""

        return {
            "id": self.identity,
            "pointer": self.pointer,
            "visible": self.visible,
            "observedLowerBound": self.observed_lower_bound,
            "totalKnown": self.total_known,
            "total": self.total,
            "omitted": self.omitted,
            "completeness": self.completeness,
            "population": self.population,
            "scope": self.scope,
            "authority": self.authority,
            "sourceFingerprint": self.source_fingerprint,
            "scopeFingerprint": self.scope_fingerprint,
            "analysisFingerprint": self.analysis_fingerprint,
            "causes": [cause.to_dict() for cause in self.causes],
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> CollectionCoverage:
        """Parse one canonical coverage envelope."""

        return cls(
            identity=str(row.get("id", "")),
            pointer=str(row.get("pointer", "")),
            visible=nonnegative_int(row.get("visible"), "visible"),
            observed_lower_bound=nonnegative_int(
                row.get("observedLowerBound"),
                "observedLowerBound",
            ),
            total_known=boolean(row.get("totalKnown"), "totalKnown"),
            total=optional_nonnegative_int(row.get("total"), "total"),
            omitted=optional_nonnegative_int(row.get("omitted"), "omitted"),
            completeness=str(row.get("completeness", "")),
            population=str(row.get("population", "")),
            scope=str(row.get("scope", "")),
            authority=str(row.get("authority", "")),
            source_fingerprint=optional_string(row.get("sourceFingerprint")),
            scope_fingerprint=optional_string(row.get("scopeFingerprint")),
            analysis_fingerprint=optional_string(
                row.get("analysisFingerprint")
            ),
            causes=tuple(
                CoverageCause.from_mapping(cause)
                for cause in mapping_rows(row.get("causes"))
            ),
        )


@dataclass(frozen=True)
class CoverageRegistry:
    """Immutable canonical owner for collection coverage rows."""

    collections: Mapping[str, CollectionCoverage] = field(default_factory=dict)
    schema: str = COVERAGE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != COVERAGE_SCHEMA:
            raise CoverageError(f"unsupported coverage schema: {self.schema}")
        rows = dict(self.collections)
        for identity, coverage in rows.items():
            if identity != coverage.identity:
                raise CoverageError(
                    "coverage registry key must match collection identity"
                )
        object.__setattr__(
            self,
            "collections",
            MappingProxyType(dict(sorted(rows.items()))),
        )

    def register(self, coverage: CollectionCoverage) -> CoverageRegistry:
        """Return a registry with one unique canonical collection."""

        rows = dict(self.collections)
        existing = rows.get(coverage.identity)
        if existing is not None and existing != coverage:
            raise CoverageError(
                f"coverage identity already registered: {coverage.identity}"
            )
        rows[coverage.identity] = coverage
        return CoverageRegistry(rows)

    def require(self, identity: str) -> CollectionCoverage:
        """Return one registered collection or fail closed."""

        try:
            return self.collections[identity]
        except KeyError as exc:
            raise CoverageError(
                f"unknown coverage reference: {identity}"
            ) from exc

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical registry payload."""

        return {
            "schema": self.schema,
            "collections": {
                identity: row.to_dict()
                for identity, row in self.collections.items()
            },
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> CoverageRegistry:
        """Parse a canonical registry and reject malformed rows."""

        raw_collections = raw.get("collections", {})
        if not isinstance(raw_collections, Mapping):
            raise CoverageError("coverage collections must be an object")
        malformed = [
            str(identity)
            for identity, row in raw_collections.items()
            if not isinstance(row, Mapping)
        ]
        if malformed:
            raise CoverageError(
                "coverage collection rows must be objects: "
                f"{sorted(malformed)}"
            )
        return cls(
            collections={
                str(identity): CollectionCoverage.from_mapping(row)
                for identity, row in raw_collections.items()
            },
            schema=str(raw.get("schema", "")),
        )


def legacy_unknown_coverage(
    *,
    identity: str,
    pointer: str,
    visible: int,
    population: str,
    scope: str,
    authority: str,
) -> CollectionCoverage:
    """Represent absent legacy coverage as unknown, never complete."""

    return CollectionCoverage.unknown(
        identity=identity,
        pointer=pointer,
        visible=visible,
        observed_lower_bound=visible,
        completeness="unavailable",
        population=population,
        scope=scope,
        authority=authority,
        causes=(
            CoverageCause(
                kind="compatibility",
                identifier="coverage.legacy_missing",
                detail=(
                    "legacy input did not carry canonical collection coverage"
                ),
            ),
        ),
    )


def _validate_coverage_identity_and_counts(
    row: CollectionCoverage,
) -> tuple[int, int]:
    if not row.identity:
        raise CoverageError("coverage identity must be non-empty")
    if not row.pointer.startswith("#/"):
        raise CoverageError("coverage pointer must be a canonical JSON pointer")
    visible = nonnegative_int(row.visible, "visible")
    observed = nonnegative_int(
        row.observed_lower_bound,
        "observed_lower_bound",
    )
    if observed < visible:
        raise CoverageError(
            "observed lower bound must be at least the visible count"
        )
    if row.completeness not in COVERAGE_COMPLETENESS:
        raise CoverageError(
            f"unsupported coverage completeness: {row.completeness}"
        )
    if not row.population or not row.scope or not row.authority:
        raise CoverageError(
            "coverage population, scope, and authority must be non-empty"
        )
    return visible, observed


def _validate_coverage_total(
    row: CollectionCoverage,
    *,
    visible: int,
    observed: int,
) -> None:
    if row.total_known:
        _validate_known_coverage_total(
            row,
            visible=visible,
            observed=observed,
        )
        return
    if row.total is not None or row.omitted is not None:
        raise CoverageError(
            "unknown coverage must use null total and omitted counts"
        )
    if row.completeness == "complete":
        raise CoverageError("unknown-total coverage cannot be complete")


def _validate_known_coverage_total(
    row: CollectionCoverage,
    *,
    visible: int,
    observed: int,
) -> None:
    if row.total is None or row.omitted is None:
        raise CoverageError(
            "known coverage requires exact total and omitted counts"
        )
    total = nonnegative_int(row.total, "total")
    omitted = nonnegative_int(row.omitted, "omitted")
    if total < observed:
        raise CoverageError(
            "known total must be at least the observed lower bound"
        )
    if omitted != total - visible:
        raise CoverageError("known omitted count must equal total - visible")
    if row.completeness == "complete" and omitted:
        raise CoverageError(
            "complete coverage cannot contain omitted members"
        )


def _validate_coverage_causes(row: CollectionCoverage) -> None:
    if row.completeness != "complete" and not row.causes:
        raise CoverageError(
            "non-complete coverage requires at least one typed cause"
        )


def mapping_rows(raw: Any) -> tuple[Mapping[str, Any], ...]:
    """Return only mapping rows from a JSON-compatible array."""

    if not isinstance(raw, list):
        return ()
    return tuple(row for row in raw if isinstance(row, Mapping))


def nonnegative_int(raw: Any, label: str) -> int:
    """Validate one canonical non-negative integer."""

    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise CoverageError(f"{label} must be a non-negative integer")
    return raw


def boolean(raw: Any, label: str) -> bool:
    """Validate one canonical Boolean."""

    if not isinstance(raw, bool):
        raise CoverageError(f"{label} must be a boolean")
    return raw


def optional_nonnegative_int(raw: Any, label: str) -> int | None:
    """Validate an optional canonical non-negative integer."""

    return None if raw is None else nonnegative_int(raw, label)


def optional_string(raw: Any) -> str | None:
    """Normalize one optional string field."""

    return None if raw is None else str(raw)


__all__ = [
    "COVERAGE_CAUSE_KINDS",
    "COVERAGE_COMPLETENESS",
    "COVERAGE_SCHEMA",
    "CollectionCoverage",
    "CoverageCause",
    "CoverageError",
    "CoverageRegistry",
    "legacy_unknown_coverage",
]
