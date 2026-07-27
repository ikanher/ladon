"""Typed evidence models for generated-family candidate analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ladon.coverage import CollectionCoverage
from ladon.ir import LeanModule


PRIMARY_POPULATIONS = frozenset(
    {
        "target_owned",
        "project_generated",
        "compiler_generated",
        "imported",
        "unclassified",
    }
)


@dataclass(frozen=True)
class CandidateNonclaim:
    """One stable boundary on what advisory regularity establishes."""

    identifier: str
    text: str

    def to_dict(self) -> dict[str, str]:
        """Return a stable nonclaim row."""

        return {"id": self.identifier, "text": self.text}


CANDIDATE_NONCLAIMS = (
    CandidateNonclaim(
        "candidate.nonclaim.generator_existence",
        "Generated-looking evidence does not establish that a generator exists.",
    ),
    CandidateNonclaim(
        "candidate.nonclaim.generator_identity_execution",
        "Generated-looking evidence does not establish generator identity or execution.",
    ),
    CandidateNonclaim(
        "candidate.nonclaim.provenance_freshness_reproducibility",
        "Generated-looking evidence does not establish provenance, freshness, or reproducibility.",
    ),
    CandidateNonclaim(
        "candidate.nonclaim.defect_authorship",
        "Generated-looking evidence does not establish a generator defect or source authorship.",
    ),
    CandidateNonclaim(
        "candidate.nonclaim.proof",
        "Generated-looking evidence does not establish proof correctness or theorem truth.",
    ),
    CandidateNonclaim(
        "candidate.nonclaim.policy_mutation",
        "Candidate analysis does not create, modify, select, or activate a generated-family policy.",
    ),
)


@dataclass(frozen=True)
class CandidateModuleEvidence:
    """Canonical inputs for one module without changing its population."""

    module: LeanModule
    population: str = "unclassified"
    content_sha256: str | None = None
    command_skeletons: tuple[str, ...] = ()
    structural_complete: bool = True
    imports_complete: bool = True
    lexical_complete: bool = True

    def __post_init__(self) -> None:
        if self.population not in PRIMARY_POPULATIONS:
            raise ValueError(
                f"unsupported calibrated population {self.population!r}"
            )
        if not self.module.name or not self.module.path:
            raise ValueError("candidate module identity must be non-empty")
        if any(not row for row in self.command_skeletons):
            raise ValueError("command skeleton values must be non-empty")
        object.__setattr__(
            self,
            "command_skeletons",
            tuple(sorted(set(self.command_skeletons))),
        )


@dataclass(frozen=True)
class CandidateSourceAnchor:
    """One bounded lexical declaration witness."""

    module: str
    path: str
    declaration_name: str
    declaration_kind: str
    line: int
    column: int
    candidate_name: str | None = None
    declaration_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a stable source anchor."""

        return {
            "module": self.module,
            "path": self.path,
            "declarationName": self.declaration_name,
            "declarationKind": self.declaration_kind,
            "line": self.line,
            "column": self.column,
            "candidateName": self.candidate_name,
            "declarationId": self.declaration_id,
        }


@dataclass(frozen=True)
class CandidateMember:
    """One source module and its preserved calibrated population."""

    identifier: str
    path: str
    population: str
    parent: str | None
    basename_prefix: str | None
    suffix_value: int | None
    suffix_spelling: str | None
    direct_internal_imports: tuple[str, ...]
    declaration_stems: tuple[str, ...]
    command_skeletons: tuple[str, ...]
    content_sha256: str | None
    normalized_block_hashes: tuple[str, ...]
    structural_complete: bool
    imports_complete: bool
    lexical_complete: bool

    def to_dict(self) -> dict[str, Any]:
        """Return member evidence without inferring provenance."""

        return {
            "id": self.identifier,
            "module": self.identifier,
            "path": self.path,
            "population": self.population,
            "sequence": {
                "parent": self.parent,
                "basenamePrefix": self.basename_prefix,
                "suffixValue": self.suffix_value,
                "suffixSpelling": self.suffix_spelling,
            },
            "directInternalImports": list(self.direct_internal_imports),
            "declarationStems": list(self.declaration_stems),
            "commandSkeletons": list(self.command_skeletons),
            "contentSha256": self.content_sha256,
            "normalizedDeclarationBlockHashes": list(
                self.normalized_block_hashes
            ),
            "completeness": {
                "structural": self.structural_complete,
                "imports": self.imports_complete,
                "lexical": self.lexical_complete,
            },
        }


@dataclass(frozen=True)
class CandidateFeature:
    """One aggregate feature with its original component authority."""

    identifier: str
    kind: str
    version: str
    value: str
    authority: str
    member_ids: tuple[str, ...]
    occurrence_count: int
    representative_member_ids: tuple[str, ...]
    representative_omitted_count: int
    source_anchors: tuple[CandidateSourceAnchor, ...] = ()
    source_anchor_omitted_count: int = 0
    complete: bool = True

    @property
    def member_count(self) -> int:
        """Return member rather than occurrence coverage."""

        return len(self.member_ids)

    def to_dict(self) -> dict[str, Any]:
        """Return bounded representatives and exact aggregate counts."""

        return {
            "id": self.identifier,
            "kind": self.kind,
            "version": self.version,
            "value": self.value,
            "authority": self.authority,
            "memberIds": list(self.member_ids),
            "memberCount": self.member_count,
            "occurrenceCount": self.occurrence_count,
            "representativeMemberIds": list(
                self.representative_member_ids
            ),
            "representativeOmittedCount": (
                self.representative_omitted_count
            ),
            "sourceAnchors": [
                anchor.to_dict() for anchor in self.source_anchors
            ],
            "sourceAnchorOmittedCount": self.source_anchor_omitted_count,
            "complete": self.complete,
        }


@dataclass(frozen=True)
class CandidateClauseResult:
    """One exact predicate clause and all of its count operands."""

    identifier: str
    status: str
    observed_numerator: int | None
    observed_denominator: int | None
    threshold_numerator: int | None
    threshold_denominator: int | None
    required_count: int | None
    witness_feature_id: str | None
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {"passed", "failed", "unavailable"}:
            raise ValueError(f"unsupported clause status {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic clause result with exact fractions."""

        return {
            "id": self.identifier,
            "status": self.status,
            "operands": {
                "observedNumerator": self.observed_numerator,
                "observedDenominator": self.observed_denominator,
                "thresholdNumerator": self.threshold_numerator,
                "thresholdDenominator": self.threshold_denominator,
                "requiredCount": self.required_count,
            },
            "witnessFeatureId": self.witness_feature_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CandidateSequence:
    """Exact numbered-sibling sequence evidence."""

    parent: str
    basename_prefix: str
    member_count: int
    suffix_values: tuple[int, ...]
    occupied_suffix_values: tuple[int, ...]
    minimum_suffix: int
    maximum_suffix: int
    inclusive_span: int
    gap_count: int
    gap_ranges: tuple[tuple[int, int], ...]
    gap_range_omitted_count: int

    @property
    def occupied_count(self) -> int:
        """Return the number of distinct observed suffix values."""

        return len(self.occupied_suffix_values)

    def to_dict(self) -> dict[str, Any]:
        """Return exact density operands and bounded gap ranges."""

        return {
            "parent": self.parent,
            "basenamePrefix": self.basename_prefix,
            "memberCount": self.member_count,
            "suffixValues": list(self.suffix_values),
            "occupiedSuffixValues": list(self.occupied_suffix_values),
            "occupiedValueCount": self.occupied_count,
            "minimumSuffix": self.minimum_suffix,
            "maximumSuffix": self.maximum_suffix,
            "inclusiveSpan": self.inclusive_span,
            "density": {
                "numerator": self.occupied_count,
                "denominator": self.inclusive_span,
            },
            "gapCount": self.gap_count,
            "gapRanges": [
                {"first": first, "last": last}
                for first, last in self.gap_ranges
            ],
            "gapRangeOmittedCount": self.gap_range_omitted_count,
        }


@dataclass(frozen=True)
class CandidateAuthority:
    """Component and derived authorities kept deliberately separate."""

    structure: str = "source_index_path"
    imports: str = "module_import_graph"
    lexical: str = "lexical_text"
    content_hash: str = "source_index_content_hash"
    declaration_block_hash: str = "lexical_declaration_block_hash"
    population: str = "population_calibration"
    conclusion: str = "ladon_derived_heuristic"

    def to_dict(self) -> dict[str, str]:
        """Return authority labels without upgrading any component."""

        return {
            "structure": self.structure,
            "imports": self.imports,
            "lexical": self.lexical,
            "contentHash": self.content_hash,
            "declarationBlockHash": self.declaration_block_hash,
            "population": self.population,
            "conclusion": self.conclusion,
        }


@dataclass(frozen=True)
class CandidateRepresentative:
    """One deterministically selected candidate member."""

    member_id: str
    suffix_value: int
    rank: int
    selection_rule: str = "suffix-then-module-identity-v1"

    def to_dict(self) -> dict[str, Any]:
        """Return the bounded representative row."""

        return {
            "memberId": self.member_id,
            "suffixValue": self.suffix_value,
            "rank": self.rank,
            "selectionRule": self.selection_rule,
        }


@dataclass(frozen=True)
class CandidatePartition:
    """One numeric structural partition, qualifying or otherwise."""

    identifier: str
    sequence: CandidateSequence
    members: tuple[CandidateMember, ...]
    features: tuple[CandidateFeature, ...]
    feature_coverage: CollectionCoverage
    clauses: tuple[CandidateClauseResult, ...]
    evaluation_status: str
    selected_import_feature_id: str | None
    selected_lexical_feature_id: str | None
    member_coverage: CollectionCoverage
    nonclaims: tuple[CandidateNonclaim, ...] = CANDIDATE_NONCLAIMS

    def __post_init__(self) -> None:
        if self.evaluation_status not in {
            "match",
            "non_match",
            "unavailable",
        }:
            raise ValueError(
                f"unsupported evaluation status {self.evaluation_status!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the full inspectable structural evaluation."""

        return {
            "id": self.identifier,
            "sequence": self.sequence.to_dict(),
            "members": [member.to_dict() for member in self.members],
            "features": [feature.to_dict() for feature in self.features],
            "featureCoverage": self.feature_coverage.to_dict(),
            "clauses": [clause.to_dict() for clause in self.clauses],
            "evaluationStatus": self.evaluation_status,
            "selectedImportFeatureId": self.selected_import_feature_id,
            "selectedLexicalFeatureId": self.selected_lexical_feature_id,
            "memberCoverage": self.member_coverage.to_dict(),
            "authority": CandidateAuthority().to_dict(),
            "nonclaims": [
                nonclaim.to_dict() for nonclaim in self.nonclaims
            ],
        }


@dataclass(frozen=True)
class GeneratedFamilyCandidate:
    """One exact predicate match represented as an advisory relation."""

    identifier: str
    profile_version: str
    profile_digest: str
    partition_id: str
    sequence: CandidateSequence
    members: tuple[CandidateMember, ...]
    clauses: tuple[CandidateClauseResult, ...]
    import_feature_id: str
    lexical_feature_id: str
    representatives: tuple[CandidateRepresentative, ...]
    representative_coverage: CollectionCoverage
    member_coverage: CollectionCoverage
    source_fingerprint: str
    scope_fingerprint: str | None
    policy_digest: str | None
    analysis_fingerprint: str
    authority: CandidateAuthority = CandidateAuthority()
    nonclaims: tuple[CandidateNonclaim, ...] = CANDIDATE_NONCLAIMS

    def to_dict(self) -> dict[str, Any]:
        """Return candidate evidence without a provenance or proof claim."""

        populations = {
            population: sum(
                member.population == population for member in self.members
            )
            for population in sorted(PRIMARY_POPULATIONS)
        }
        return {
            "id": self.identifier,
            "profileVersion": self.profile_version,
            "profileDigest": self.profile_digest,
            "partitionId": self.partition_id,
            "sequence": self.sequence.to_dict(),
            "members": [member.to_dict() for member in self.members],
            "memberIds": [
                member.identifier for member in self.members
            ],
            "memberPopulations": populations,
            "clauses": [clause.to_dict() for clause in self.clauses],
            "importFeatureId": self.import_feature_id,
            "lexicalFeatureId": self.lexical_feature_id,
            "representatives": [
                representative.to_dict()
                for representative in self.representatives
            ],
            "representativeCoverage": (
                self.representative_coverage.to_dict()
            ),
            "memberCoverage": self.member_coverage.to_dict(),
            "sourceFingerprint": self.source_fingerprint,
            "scopeFingerprint": self.scope_fingerprint,
            "policyDigest": self.policy_digest,
            "analysisFingerprint": self.analysis_fingerprint,
            "authority": self.authority.to_dict(),
            "status": "advisory",
            "nonclaims": [
                nonclaim.to_dict() for nonclaim in self.nonclaims
            ],
        }


@dataclass(frozen=True)
class GeneratedFamilyCandidateAnalysis:
    """Complete core result before pipeline/report projection."""

    profile: dict[str, Any]
    feature_projection: dict[str, Any]
    analysis_fingerprint: str
    candidates: tuple[GeneratedFamilyCandidate, ...]
    partitions: tuple[CandidatePartition, ...]
    ungrouped_members: tuple[CandidateMember, ...]
    candidate_coverage: CollectionCoverage
    partition_coverage: CollectionCoverage
    internal_inventory_fingerprint: str | None = None
    nonclaims: tuple[CandidateNonclaim, ...] = CANDIDATE_NONCLAIMS

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-ready core evidence."""

        return {
            "profile": dict(self.profile),
            "featureProjection": dict(self.feature_projection),
            "analysisFingerprint": self.analysis_fingerprint,
            "internalInventoryFingerprint": (
                self.internal_inventory_fingerprint
            ),
            "candidates": [
                candidate.to_dict() for candidate in self.candidates
            ],
            "partitions": [
                partition.to_dict() for partition in self.partitions
            ],
            "ungroupedMembers": [
                _ungrouped_member_dict(member)
                for member in self.ungrouped_members
            ],
            "coverage": {
                "candidates": self.candidate_coverage.to_dict(),
                "partitions": self.partition_coverage.to_dict(),
            },
            "nonclaims": [
                nonclaim.to_dict() for nonclaim in self.nonclaims
            ],
        }


def _ungrouped_member_dict(member: CandidateMember) -> dict[str, Any]:
    """Route non-numbered modules without duplicating their source evidence."""

    return {
        "id": member.identifier,
        "module": member.identifier,
        "path": member.path,
        "population": member.population,
        "status": "not_partitioned",
        "reason": "final_segment_has_no_decimal_suffix",
    }
