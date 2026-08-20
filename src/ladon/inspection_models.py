"""Typed, caller-neutral models for bounded artifact inspection.

Inspection rows are projections of canonical report or source-index rows.  The
models retain the owning artifact identity and canonical JSON pointer so the
projection cannot be mistaken for a second authority-bearing inventory.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

INSPECTION_PAGE_SCHEMA = "ladon-inspection-page-v1"
INSPECTION_CURSOR_SCHEMA = "ladon-inspection-cursor-v1"
INSPECTION_NOUNS = (
    "modules",
    "declarations",
    "imports",
    "audits",
    "options",
    "resources",
    "proof-mechanisms",
)
SOURCE_ANCHOR_STATUSES = frozenset({"exact", "unavailable"})
MAX_RELATED_ROWS = 8


class InspectionError(ValueError):
    """Base class for one structured inspection failure."""

    code = "inspection.error"

    def diagnostic(self) -> dict[str, Any]:
        """Return a stable machine-readable failure description."""

        return {"code": self.code, "message": str(self)}


class InspectionInvocationError(InspectionError):
    """Raised when a query is malformed or unsupported."""

    code = "inspection.invalid_query"


class InspectionCompatibilityError(InspectionError):
    """Raised when selected evidence or a cursor is incompatible."""

    code = "inspection.incompatible_evidence"


class InspectionNotFoundError(InspectionError):
    """Raised when exact stable-ID lookup has no canonical match."""

    code = "inspection.id_not_found"


@dataclass(frozen=True)
class ArtifactIdentity:
    """Immutable identity and authority boundary of one selected artifact."""

    kind: str
    schema: str
    fingerprint: str
    source_fingerprint: str | None
    scope_fingerprint: str | None = None
    analysis_fingerprint: str | None = None
    live_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the public artifact identity."""

        source_status = (
            "available" if self.source_fingerprint is not None else "unavailable"
        )
        return {
            "kind": self.kind,
            "schema": self.schema,
            "fingerprint": self.fingerprint,
            "sourceFingerprint": self.source_fingerprint,
            "sourceFingerprintStatus": source_status,
            "sourceFingerprintReason": (
                None
                if self.source_fingerprint is not None
                else "selected artifact does not record a source fingerprint"
            ),
            "scopeFingerprint": self.scope_fingerprint,
            "analysisFingerprint": self.analysis_fingerprint,
            "liveFingerprint": self.live_fingerprint,
        }


@dataclass(frozen=True)
class SourceAnchor:
    """Repository-relative source navigation or an explicit absence reason."""

    status: str
    path: str | None
    source_range: Mapping[str, Any] | None
    reason: str | None

    def __post_init__(self) -> None:
        if self.status not in SOURCE_ANCHOR_STATUSES:
            raise ValueError(f"unsupported source-anchor status: {self.status}")
        if self.status == "exact" and not self.path:
            raise ValueError("an exact source anchor requires a relative path")
        if self.status == "unavailable" and not self.reason:
            raise ValueError("an unavailable source anchor requires a reason")

    @classmethod
    def exact(
        cls,
        path: str,
        source_range: Mapping[str, Any] | None = None,
    ) -> SourceAnchor:
        """Build an exact repository-relative source anchor."""

        return cls("exact", path, source_range, None)

    @classmethod
    def unavailable(cls, reason: str) -> SourceAnchor:
        """Build an explicit no-anchor result."""

        return cls("unavailable", None, None, reason)

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical source-navigation shape."""

        return {
            "status": self.status,
            "path": self.path,
            "range": (
                dict(self.source_range) if self.source_range is not None else None
            ),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class InspectionRow:
    """One bounded projection of a canonical artifact row."""

    identifier: str
    noun: str
    canonical_ref: str
    artifact_fingerprint: str
    source_fingerprint: str | None
    schema_version: str
    population: str
    scope: str
    authority: str
    source_anchor: SourceAnchor
    coverage_ref: str
    fields: Mapping[str, Any]
    order_key: tuple[str, ...]
    related: tuple[Mapping[str, Any], ...] = ()
    enrichments: tuple[Mapping[str, Any], ...] = ()
    nonclaims: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.noun not in INSPECTION_NOUNS:
            raise ValueError(f"unsupported inspection noun: {self.noun}")
        required = (
            self.identifier,
            self.canonical_ref,
            self.artifact_fingerprint,
            self.schema_version,
            self.population,
            self.scope,
            self.authority,
            self.coverage_ref,
        )
        if any(not value for value in required):
            raise ValueError("inspection row identity fields must be non-empty")
        if len(self.related) > MAX_RELATED_ROWS:
            raise ValueError("inspection related rows exceed the bounded limit")

    def to_dict(self) -> dict[str, Any]:
        """Return one stable inspection-row projection."""

        source_status = (
            "available" if self.source_fingerprint is not None else "unavailable"
        )
        return {
            "id": self.identifier,
            "noun": self.noun,
            "canonicalRef": self.canonical_ref,
            "artifactFingerprint": self.artifact_fingerprint,
            "sourceFingerprint": self.source_fingerprint,
            "sourceFingerprintStatus": source_status,
            "sourceFingerprintReason": (
                None
                if self.source_fingerprint is not None
                else "canonical artifact does not record a source fingerprint"
            ),
            "schemaVersion": self.schema_version,
            "population": self.population,
            "scope": self.scope,
            "authority": self.authority,
            "sourceAnchor": self.source_anchor.to_dict(),
            "coverageRef": self.coverage_ref,
            "fields": dict(self.fields),
            "related": [dict(row) for row in self.related],
            "enrichments": [dict(row) for row in self.enrichments],
            "nonclaims": list(self.nonclaims),
        }


@dataclass(frozen=True)
class InspectionDataset:
    """All visible canonical rows for one noun in one immutable artifact."""

    noun: str
    artifact: ArtifactIdentity
    coverage: Mapping[str, Any]
    rows: tuple[InspectionRow, ...]
    unavailable_reason: str | None = None


@dataclass(frozen=True)
class InspectionQuery:
    """One normalized finite query over a registered inspection noun."""

    noun: str
    filters: tuple[tuple[str, str], ...]
    identifier: str | None
    limit: int
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Return the stable query identity shown in text and JSON."""

        return {
            "noun": self.noun,
            "filters": [
                {"field": field, "value": value} for field, value in self.filters
            ],
            "id": self.identifier,
            "limit": self.limit,
            "fingerprint": self.fingerprint,
            "ordering": "noun-stable-key-v1",
        }


@dataclass(frozen=True)
class InspectionPage:
    """One deterministic page selected from immutable artifact evidence."""

    artifact: ArtifactIdentity
    query: InspectionQuery
    collection_coverage: Mapping[str, Any]
    rows: tuple[InspectionRow, ...]
    matching_total: int
    before_count: int
    after_count: int
    next_cursor: str | None
    diagnostics: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    schema: str = INSPECTION_PAGE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        """Return the single text/JSON rendering source."""

        collection_complete = self.collection_coverage.get("completeness") == "complete"
        omitted = (
            self.matching_total - len(self.rows)
            if collection_complete
            else None
        )
        return {
            "schema": self.schema,
            "artifact": self.artifact.to_dict(),
            "query": self.query.to_dict(),
            "coverage": {
                "collection": dict(self.collection_coverage),
                "pageVisible": len(self.rows),
                "matchingVisibleTotal": self.matching_total,
                "matchingTotalKnown": collection_complete,
                "matchingTotal": (self.matching_total if collection_complete else None),
                "observedMatchingLowerBound": self.matching_total,
                "omitted": omitted,
                "before": self.before_count,
                "after": self.after_count,
                "completeness": self.collection_coverage.get("completeness"),
                "pageExhaustsMatches": (
                    collection_complete
                    and self.before_count == 0
                    and self.after_count == 0
                ),
            },
            "rows": [row.to_dict() for row in self.rows],
            "nextCursor": self.next_cursor,
            "diagnostics": [dict(row) for row in self.diagnostics],
        }


__all__ = [
    "INSPECTION_CURSOR_SCHEMA",
    "INSPECTION_NOUNS",
    "INSPECTION_PAGE_SCHEMA",
    "MAX_RELATED_ROWS",
    "ArtifactIdentity",
    "InspectionCompatibilityError",
    "InspectionDataset",
    "InspectionError",
    "InspectionInvocationError",
    "InspectionNotFoundError",
    "InspectionPage",
    "InspectionQuery",
    "InspectionRow",
    "SourceAnchor",
]
