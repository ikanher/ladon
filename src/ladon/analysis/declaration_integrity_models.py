"""Typed declaration-integrity evidence and coverage-bearing serialization."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.coverage import (
    CollectionCoverage,
    CoverageCause,
    InspectionAction,
    ProducerRegistry,
)


DECLARATION_INTEGRITY_SCHEMA = "ladon-declaration-integrity-v2"
DECLARATION_INTEGRITY_ANALYSIS_VERSION = "ladon-declaration-integrity-analysis-v2"
DEFAULT_GROUP_LIMIT = 100
DEFAULT_MEMBER_LIMIT = 12
COLLISION_COLLECTION_ID = "declaration_integrity.collision_candidates"
BLOCK_DUPLICATE_COLLECTION_ID = "declaration_integrity.exact_block_duplicates"
FILE_DUPLICATE_COLLECTION_ID = "declaration_integrity.exact_file_duplicates"
SOURCE_SHAPE_COLLECTION_ID = "declaration_integrity.source_shape_similarities"
CO_REACHABLE_COLLECTION_ID = "declaration_integrity.co_reachable_collisions"
INTEGRITY_POINTER = "#/sections/module_dag/declaration_integrity"

COLLISION_NONCLAIMS = (
    "Equal lexical candidate names do not confirm that the declarations "
    "coexist in one Lean environment.",
    "This candidate is not a Lean name-resolution error, compilation failure, "
    "theorem defect, or proof conflict.",
)
BLOCK_DUPLICATE_NONCLAIMS = (
    "Equal normalized lexical blocks do not establish equal Lean declarations, "
    "statements, proofs, or theorem meaning.",
    "This exact normalized-block candidate is not evidence of a generator "
    "defect or compilation failure.",
)
FILE_DUPLICATE_NONCLAIMS = (
    "Equal source bytes do not establish that Lean loads both modules, assigns "
    "the same declarations, or rejects either file.",
    "This exact-source candidate is not proof equivalence, theorem identity, "
    "authorship, provenance, or a generator defect.",
)
SOURCE_SHAPE_NONCLAIMS = (
    "Equal lexical token-category shapes do not establish equal Lean "
    "declarations, statements, proofs, theorem meaning, or behavior.",
    "This source-shape similarity is not parsed Lean syntax, elaborated proof "
    "shape, generated provenance, a generator defect, or exact duplication.",
)
CO_REACHABLE_NONCLAIMS = (
    "The selected graph witness establishes only lexical module-import "
    "co-reachability.",
    *COLLISION_NONCLAIMS,
)


@dataclass(frozen=True)
class DeclarationIntegrityMember:
    """One canonical lexical declaration member retained by a partition."""

    module: str
    path: str
    declaration_id: str
    written_name: str
    candidate_name: str | None
    candidate_status: str
    kind: str
    line: int
    column: int
    privacy: str
    locality: str
    normalized_block_sha256: str | None
    block_normalization_version: str | None
    normalized_source_shape_sha256: str | None
    source_shape_normalization_version: str | None
    source_fingerprint: str

    @property
    def canonical_ref(self) -> str:
        """Return the source-index declaration identity used by inspection."""

        return f"source-index:declaration:{self.declaration_id}"

    def to_dict(self) -> dict[str, Any]:
        """Return one source-located lexical member."""

        return {
            "module": self.module,
            "path": self.path,
            "declarationId": self.declaration_id,
            "canonicalRef": self.canonical_ref,
            "writtenName": self.written_name,
            "candidateName": self.candidate_name,
            "candidateStatus": self.candidate_status,
            "kind": self.kind,
            "line": self.line,
            "column": self.column,
            "privacy": self.privacy,
            "locality": self.locality,
            "normalizedBlockSha256": self.normalized_block_sha256,
            "blockNormalizationVersion": self.block_normalization_version,
            "normalizedSourceShapeSha256": (self.normalized_source_shape_sha256),
            "sourceShapeNormalizationVersion": (
                self.source_shape_normalization_version
            ),
            "authority": "lexical_text",
            "sourceIndexFingerprint": self.source_fingerprint,
        }


@dataclass(frozen=True)
class SourceFileIntegrityMember:
    """One source-index module member in an exact-file partition."""

    module: str
    path: str
    content_sha256: str
    source_fingerprint: str

    @property
    def canonical_ref(self) -> str:
        """Return the source-index module identity used by inspection."""

        return f"source-index:module:{self.module}"

    def to_dict(self) -> dict[str, str]:
        """Return one exact source-file member."""

        return {
            "module": self.module,
            "path": self.path,
            "contentSha256": self.content_sha256,
            "canonicalRef": self.canonical_ref,
            "authority": "source_index_content_hash",
            "sourceIndexFingerprint": self.source_fingerprint,
        }


IntegrityMember = DeclarationIntegrityMember | SourceFileIntegrityMember


@dataclass(frozen=True)
class SelectedContextAssessment:
    """Availability or one exact selected-context graph witness."""

    status: str
    reason: str
    witness_kind: str | None = None
    context_module: str | None = None
    member_modules: tuple[str, ...] = ()
    witness: Mapping[str, Any] | None = None
    evidence_refs: tuple[str, ...] = ()
    coverage_ref: str | None = None
    source_fingerprint: str | None = None
    scope_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {
            "co_reachable",
            "not_observed",
            "unavailable",
        }:
            raise ValueError(f"unsupported selected-context status {self.status!r}")
        if not self.reason:
            raise ValueError("selected-context reason must be non-empty")
        if self.status == "co_reachable":
            self._validate_witness()

    def _validate_witness(self) -> None:
        """Require every identity needed by a co-reachable registration."""

        if (
            self.witness_kind is None
            or self.context_module is None
            or len(self.member_modules) < 2
            or self.witness is None
            or not self.evidence_refs
            or self.coverage_ref is None
        ):
            raise ValueError("co-reachable status requires a complete graph witness")

    def to_dict(self) -> dict[str, Any]:
        """Return selected-context status without inventing coexistence."""

        return {
            "status": self.status,
            "reason": self.reason,
            "witnessKind": self.witness_kind,
            "contextModule": self.context_module,
            "memberModules": list(self.member_modules),
            "witness": dict(self.witness) if self.witness is not None else None,
            "evidenceRefs": list(self.evidence_refs),
            "coverageRef": self.coverage_ref,
            "authority": (
                "module_import_graph" if self.status == "co_reachable" else None
            ),
            "sourceIndexFingerprint": self.source_fingerprint,
            "scopeFingerprint": self.scope_fingerprint,
            "nonclaim": (
                "Selected module-import graph evidence only; not Lean name "
                "resolution, elaboration, compilation, or theorem evidence."
            ),
        }


@dataclass(frozen=True)
class DeclarationIntegrityGroup:
    """One exact keyed partition with bounded serialized representatives."""

    identifier: str
    evidence_kind: str
    key: str
    key_version: str
    authority: str
    members: tuple[IntegrityMember, ...]
    representative_limit: int
    member_coverage: CollectionCoverage
    nonclaims: tuple[str, ...]
    inspection_action: InspectionAction
    selected_context: SelectedContextAssessment | None = None

    def __post_init__(self) -> None:
        if len(self.members) < 2:
            raise ValueError("integrity groups require at least two members")
        if len({member.module for member in self.members}) < 2:
            raise ValueError("integrity groups require members from distinct modules")
        if self.member_coverage.observed_lower_bound != len(self.members):
            raise ValueError(
                "member coverage must count every observed partition member"
            )
        if self.member_coverage.visible != min(
            self.representative_limit,
            len(self.members),
        ):
            raise ValueError("member coverage must count bounded representatives")

    @property
    def representatives(self) -> tuple[IntegrityMember, ...]:
        """Return the deterministic bounded member prefix."""

        return self.members[: self.representative_limit]

    def to_dict(self) -> dict[str, Any]:
        """Return the bounded report/inspection summary for this partition."""

        return {
            "id": self.identifier,
            "evidenceKind": self.evidence_kind,
            "key": self.key,
            "keyVersion": self.key_version,
            "authority": self.authority,
            "memberCount": len(self.members),
            "canonicalMemberRefs": [member.canonical_ref for member in self.members],
            "representativeMembers": [
                member.to_dict() for member in self.representatives
            ],
            "memberCoverage": self.member_coverage.to_dict(),
            "inspectionAction": self.inspection_action.to_dict(),
            "selectedContext": (
                self.selected_context.to_dict()
                if self.selected_context is not None
                else None
            ),
            "nonclaims": list(self.nonclaims),
        }


@dataclass(frozen=True)
class DeclarationIntegrityResult:
    """All canonical partitions, bounded projections, and producer rows."""

    analysis_fingerprint: str
    collision_groups: tuple[DeclarationIntegrityGroup, ...]
    exact_block_duplicate_groups: tuple[DeclarationIntegrityGroup, ...]
    exact_file_duplicate_groups: tuple[DeclarationIntegrityGroup, ...]
    source_shape_similarity_groups: tuple[DeclarationIntegrityGroup, ...]
    collision_coverage: CollectionCoverage
    block_duplicate_coverage: CollectionCoverage
    file_duplicate_coverage: CollectionCoverage
    source_shape_coverage: CollectionCoverage
    co_reachable_coverage: CollectionCoverage
    producer_registry: ProducerRegistry

    @property
    def coverage_rows(self) -> tuple[CollectionCoverage, ...]:
        """Return every finite collection coverage row for report registration."""

        return (
            self.collision_coverage,
            self.block_duplicate_coverage,
            self.file_duplicate_coverage,
            self.source_shape_coverage,
            self.co_reachable_coverage,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return bounded canonical payloads without duplicating member tables."""

        collision_rows = self.collision_groups[: self.collision_coverage.visible]
        block_rows = self.exact_block_duplicate_groups[
            : self.block_duplicate_coverage.visible
        ]
        file_rows = self.exact_file_duplicate_groups[
            : self.file_duplicate_coverage.visible
        ]
        shape_rows = self.source_shape_similarity_groups[
            : self.source_shape_coverage.visible
        ]
        return {
            "schema": DECLARATION_INTEGRITY_SCHEMA,
            "analysisFingerprint": self.analysis_fingerprint,
            "collisionCandidates": [group.to_dict() for group in collision_rows],
            "exactBlockDuplicateCandidates": [group.to_dict() for group in block_rows],
            "exactFileDuplicateCandidates": [group.to_dict() for group in file_rows],
            "sourceShapeSimilarityCandidates": [
                group.to_dict() for group in shape_rows
            ],
            "coverage": {row.identity: row.to_dict() for row in self.coverage_rows},
            "producerRegistrations": self.producer_registry.to_dict(),
        }


def declaration_group(
    *,
    evidence_kind: str,
    key: str,
    key_version: str,
    authority: str,
    members: tuple[DeclarationIntegrityMember, ...],
    index: int,
    collection_key: str,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    inventory_complete: bool,
    member_limit: int,
    nonclaims: tuple[str, ...],
    selected_context: SelectedContextAssessment | None = None,
) -> DeclarationIntegrityGroup:
    """Construct one lexical partition with truthful member coverage."""

    identifier = _group_identifier(evidence_kind, key_version, key)
    pointer = f"{INTEGRITY_POINTER}/{collection_key}/{index}/representativeMembers"
    coverage = _member_coverage(
        identity=f"{identifier}.members",
        pointer=pointer,
        member_count=len(members),
        member_limit=member_limit,
        complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
        population=f"{evidence_kind}_members",
        authority=authority,
    )
    return DeclarationIntegrityGroup(
        identifier=identifier,
        evidence_kind=evidence_kind,
        key=key,
        key_version=key_version,
        authority=authority,
        members=members,
        representative_limit=member_limit,
        member_coverage=coverage,
        nonclaims=nonclaims,
        inspection_action=InspectionAction(
            noun="declarations",
            filters=(("integrity-group", identifier),),
        ),
        selected_context=selected_context,
    )


def file_group(
    *,
    digest: str,
    members: tuple[SourceFileIntegrityMember, ...],
    index: int,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    inventory_complete: bool,
    member_limit: int,
) -> DeclarationIntegrityGroup:
    """Construct one exact source-file partition."""

    evidence_kind = "exact_source_file_duplicate"
    identifier = _group_identifier(
        evidence_kind,
        "source-content-sha256-v1",
        digest,
    )
    coverage = _member_coverage(
        identity=f"{identifier}.members",
        pointer=(
            f"{INTEGRITY_POINTER}/exactFileDuplicateCandidates/{index}/"
            "representativeMembers"
        ),
        member_count=len(members),
        member_limit=member_limit,
        complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
        population="exact_source_file_duplicate_members",
        authority="source_index_content_hash",
    )
    return DeclarationIntegrityGroup(
        identifier=identifier,
        evidence_kind=evidence_kind,
        key=digest,
        key_version="source-content-sha256-v1",
        authority="source_index_content_hash",
        members=members,
        representative_limit=member_limit,
        member_coverage=coverage,
        nonclaims=FILE_DUPLICATE_NONCLAIMS,
        inspection_action=InspectionAction(
            noun="modules",
            filters=(("integrity-group", identifier),),
        ),
    )


def group_collection_coverage(
    identity: str,
    collection_key: str,
    count: int,
    *,
    group_limit: int,
    complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    population: str,
    authority: str,
) -> CollectionCoverage:
    """Build coverage for one bounded group collection."""

    visible = min(count, group_limit)
    causes = _coverage_causes(
        complete=complete,
        omitted=max(0, count - visible),
        controlling_cap=group_limit,
    )
    values = _CoverageValues(
        identity=identity,
        pointer=f"{INTEGRITY_POINTER}/{collection_key}",
        visible=visible,
        observed=count,
        population=population,
        scope="source_index_inventory",
        authority=authority,
        causes=causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    return _known_or_unknown_coverage(values, complete=complete)


def co_reachable_coverage(
    *,
    visible: int,
    observed: int,
    complete: bool,
    unavailable_reason: str | None,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    """Build coverage for the bounded selected-context registrations."""

    causes = _co_reachable_causes(
        visible=visible,
        observed=observed,
        complete=complete,
        unavailable_reason=unavailable_reason,
    )
    values = _CoverageValues(
        identity=CO_REACHABLE_COLLECTION_ID,
        pointer=f"{INTEGRITY_POINTER}/producerRegistrations/producers",
        visible=visible,
        observed=observed,
        population="selected_context_collision_registrations",
        scope="selected_module_graph",
        authority="lexical_text_and_module_import_graph",
        causes=causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    if complete:
        return _known_or_unknown_coverage(values, complete=True)
    completeness = (
        "unavailable" if unavailable_reason is not None and observed == 0 else "partial"
    )
    return _unknown_coverage(values, completeness=completeness)


@dataclass(frozen=True)
class _CoverageValues:
    """Shared operands for known and unknown collection coverage."""

    identity: str
    pointer: str
    visible: int
    observed: int
    population: str
    scope: str
    authority: str
    causes: Sequence[CoverageCause]
    source_fingerprint: str
    scope_fingerprint: str | None
    analysis_fingerprint: str


def _member_coverage(
    *,
    identity: str,
    pointer: str,
    member_count: int,
    member_limit: int,
    complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    population: str,
    authority: str,
) -> CollectionCoverage:
    visible = min(member_count, member_limit)
    values = _CoverageValues(
        identity=identity,
        pointer=pointer,
        visible=visible,
        observed=member_count,
        population=population,
        scope="source_index_inventory",
        authority=authority,
        causes=_coverage_causes(
            complete=complete,
            omitted=max(0, member_count - visible),
            controlling_cap=member_limit,
        ),
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    return _known_or_unknown_coverage(values, complete=complete)


def _known_or_unknown_coverage(
    values: _CoverageValues,
    *,
    complete: bool,
) -> CollectionCoverage:
    if complete:
        return CollectionCoverage.exact(
            identity=values.identity,
            pointer=values.pointer,
            visible=values.visible,
            total=values.observed,
            observed_lower_bound=values.observed,
            population=values.population,
            scope=values.scope,
            authority=values.authority,
            causes=values.causes,
            source_fingerprint=values.source_fingerprint,
            scope_fingerprint=values.scope_fingerprint,
            analysis_fingerprint=values.analysis_fingerprint,
        )
    return _unknown_coverage(values, completeness="partial")


def _unknown_coverage(
    values: _CoverageValues,
    *,
    completeness: str,
) -> CollectionCoverage:
    return CollectionCoverage.unknown(
        identity=values.identity,
        pointer=values.pointer,
        visible=values.visible,
        observed_lower_bound=values.observed,
        completeness=completeness,
        population=values.population,
        scope=values.scope,
        authority=values.authority,
        causes=values.causes,
        source_fingerprint=values.source_fingerprint,
        scope_fingerprint=values.scope_fingerprint,
        analysis_fingerprint=values.analysis_fingerprint,
    )


def _coverage_causes(
    *,
    complete: bool,
    omitted: int,
    controlling_cap: int,
) -> tuple[CoverageCause, ...]:
    rows: list[CoverageCause] = []
    if not complete:
        rows.append(
            CoverageCause(
                kind="extraction",
                identifier="declaration_integrity.inventory_incomplete",
                detail=(
                    "One or more source-index members or content hashes were "
                    "unavailable, so the partition total is unknown."
                ),
            )
        )
    if omitted:
        rows.append(
            CoverageCause(
                kind="projection",
                identifier="declaration_integrity.representative_limit",
                detail=(
                    f"The deterministic projection omitted {omitted} observed rows."
                ),
                controlling_cap=controlling_cap,
            )
        )
    return tuple(rows)


def _co_reachable_causes(
    *,
    visible: int,
    observed: int,
    complete: bool,
    unavailable_reason: str | None,
) -> tuple[CoverageCause, ...]:
    causes: list[CoverageCause] = []
    if not complete:
        causes.append(
            CoverageCause(
                kind="analysis",
                identifier="declaration_integrity.selected_graph_unavailable",
                detail=(
                    unavailable_reason
                    or "Selected graph or source inventory is incomplete."
                ),
            )
        )
    if visible < observed:
        causes.append(
            CoverageCause(
                kind="projection",
                identifier="declaration_integrity.collision_projection",
                detail=(
                    f"The collision projection omitted {observed - visible} "
                    "observed co-reachable registrations."
                ),
            )
        )
    return tuple(causes)


def _group_identifier(
    evidence_kind: str,
    key_version: str,
    key: str,
) -> str:
    payload = json.dumps(
        [evidence_kind, key_version, key],
        separators=(",", ":"),
    ).encode()
    digest = hashlib.sha256(payload).hexdigest()[:24]
    return f"ladon.declaration_integrity.{evidence_kind}.{digest}"
