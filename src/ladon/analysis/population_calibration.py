"""Evidence-backed ownership and generation population calibration.

Classification changes neither source evidence authority nor proof authority.
It records where a row belongs for review and which repository policy or
Lean-supplied compiler evidence supported that choice.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from ladon.analysis.generated_family_policy import (
    GENERATED_FAMILY_POLICY_SCHEMA,
    GENERATED_FAMILY_REVIEW_METRICS,
    FamilyProvenance,
    FamilyReviewThreshold,
    GeneratedFamilyPolicy,
    GeneratedFamilyRule,
    LEGACY_GENERATED_FAMILY_POLICY_SCHEMA,
    PolicyValidationError,
    normalize_relative_path,
    parse_generated_family_policy,
)


__all__ = [
    "AmbiguousGeneratedFamilyError",
    "FamilyProvenance",
    "FamilyReviewThreshold",
    "GENERATED_FAMILY_POLICY_SCHEMA",
    "GENERATED_FAMILY_REVIEW_METRICS",
    "GeneratedFamilyAggregate",
    "GeneratedFamilyPolicy",
    "LEGACY_GENERATED_FAMILY_POLICY_SCHEMA",
    "MatchedFamilyRule",
    "PRIMARY_POPULATIONS",
    "PolicyValidationError",
    "PopulationCandidate",
    "PopulationClassification",
    "PopulationSummary",
    "aggregate_generated_families",
    "classify_population",
    "classify_populations",
    "parse_generated_family_policy",
    "summarize_populations",
]

PRIMARY_POPULATIONS = (
    "target_owned",
    "imported",
    "compiler_generated",
    "project_generated",
    "unclassified",
)
ROW_KINDS = ("module", "declaration")
POPULATION_NONCLAIM = (
    "Ownership and generation provenance only; classification does not change "
    "source authority, establish proof correctness, replay a generator, or "
    "establish generated-source freshness."
)
FAMILY_NONCLAIM = (
    "Generated-family review aggregation only; size or repetition does not "
    "establish a generator defect, proof failure, or theorem falsity."
)


class AmbiguousGeneratedFamilyError(PolicyValidationError):
    """One concrete row matches more than one configured family."""

    def __init__(
        self,
        candidate_identifier: str,
        family_ids: Sequence[str],
        matches: Sequence[MatchedFamilyRule],
    ) -> None:
        self.candidate_identifier = candidate_identifier
        self.family_ids = tuple(sorted(family_ids))
        self.matches = tuple(matches)
        detail = ", ".join(
            f"{row.family_id}:{row.selector_kind}:{row.pattern}"
            for row in self.matches
        )
        super().__init__(
            f"population row {candidate_identifier!r} matches multiple "
            f"generated families {list(self.family_ids)} ({detail})"
        )


@dataclass(frozen=True)
class CalibrationDiagnostic:
    """One deterministic population-classification diagnostic."""

    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """Return a report-ready diagnostic row."""

        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class PopulationCandidate:
    """One module or declaration row awaiting population classification."""

    identifier: str
    kind: str
    module: str
    source_path: str | None
    source_authority: str
    compiler_generated: bool | None = None
    compiler_authority: str | None = None
    toolchain: str | None = None
    source_size_bytes: int = 0
    declaration_count: int = 0
    imports: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_candidate(self)
        object.__setattr__(self, "identifier", self.identifier.strip())
        object.__setattr__(self, "module", self.module.strip())
        object.__setattr__(
            self,
            "source_path",
            (
                normalize_relative_path(
                    self.source_path,
                    "candidate source path",
                )
                if self.source_path is not None
                else None
            ),
        )
        object.__setattr__(self, "imports", _normalized_imports(self.imports))


@dataclass(frozen=True)
class MatchedFamilyRule:
    """One exact selector that matched a population candidate."""

    family_id: str
    selector_kind: str
    pattern: str

    def to_dict(self) -> dict[str, str]:
        """Return the inspectable matched-rule identity."""

        return {
            "familyId": self.family_id,
            "selectorKind": self.selector_kind,
            "pattern": self.pattern,
        }


@dataclass(frozen=True)
class PopulationClassification:
    """One evidence-backed primary population assignment."""

    identifier: str
    population: str
    family_id: str | None
    matched_rules: tuple[MatchedFamilyRule, ...]
    policy_digest: str | None
    family_provenance: FamilyProvenance | None
    family_review_threshold: FamilyReviewThreshold | None
    classification_authority: str
    source_authority: str
    compiler_authority: str | None
    toolchain: str | None
    diagnostics: tuple[CalibrationDiagnostic, ...] = ()
    nonclaim: str = POPULATION_NONCLAIM

    def to_dict(self) -> dict[str, Any]:
        """Return the deterministic classification shape."""

        provenance = (
            self.family_provenance.to_dict()
            if self.family_provenance is not None
            else None
        )
        return {
            "id": self.identifier,
            "population": self.population,
            "familyId": self.family_id,
            "matchedRules": [row.to_dict() for row in self.matched_rules],
            "policyDigest": self.policy_digest,
            "familyProvenance": provenance,
            "familyReviewThreshold": (
                self.family_review_threshold.to_dict()
                if self.family_review_threshold is not None
                else None
            ),
            "classificationAuthority": self.classification_authority,
            "sourceAuthority": self.source_authority,
            "compilerAuthority": self.compiler_authority,
            "toolchain": self.toolchain,
            "diagnostics": [row.to_dict() for row in self.diagnostics],
            "nonclaim": self.nonclaim,
        }


@dataclass(frozen=True)
class PopulationSummary:
    """Raw and selected-population counts with an explicit denominator."""

    selected_population: str
    numerator: int
    denominator: int
    counts: Mapping[str, int]
    exclusions: Mapping[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return a stable population-sensitive metric envelope."""

        population_counts = {
            name: self.counts[name] for name in PRIMARY_POPULATIONS
        }
        exclusions = {
            name: self.exclusions[name]
            for name in PRIMARY_POPULATIONS
            if name in self.exclusions
        }
        return {
            "selectedPopulation": self.selected_population,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "rawCount": self.denominator,
            "populationCounts": population_counts,
            "exclusions": exclusions,
        }


@dataclass(frozen=True)
class GeneratedFamilyAggregate:
    """One deterministic aggregate over project-generated module rows."""

    identifier: str
    family_id: str
    policy_digest: str
    member_count: int
    source_size_bytes: int
    declaration_count: int
    internal_import_targets: tuple[str, ...]
    external_import_targets: tuple[str, ...]
    internal_import_count: int
    external_import_count: int
    representative_member_ids: tuple[str, ...]
    representative_omitted_count: int
    raw_member_ids: tuple[str, ...]
    provenance: FamilyProvenance
    review_threshold: FamilyReviewThreshold | None
    review_metric_value: int | None
    review_threshold_crossed: bool
    nonclaim: str = FAMILY_NONCLAIM

    def to_dict(self) -> dict[str, Any]:
        """Return the aggregate while preserving every raw member identity."""

        return {
            "id": self.identifier,
            "familyId": self.family_id,
            "population": "project_generated",
            "policyDigest": self.policy_digest,
            "memberCount": self.member_count,
            "sourceSizeBytes": self.source_size_bytes,
            "declarationCount": self.declaration_count,
            "importRelationships": {
                "internalTargets": list(self.internal_import_targets),
                "externalTargets": list(self.external_import_targets),
                "internalCount": self.internal_import_count,
                "externalCount": self.external_import_count,
                "totalCount": (
                    self.internal_import_count + self.external_import_count
                ),
            },
            "representativeMemberIds": list(self.representative_member_ids),
            "representativeOmittedCount": self.representative_omitted_count,
            "rawMemberIds": list(self.raw_member_ids),
            "provenance": self.provenance.to_dict(),
            "reviewThreshold": (
                self.review_threshold.to_dict()
                if self.review_threshold is not None
                else None
            ),
            "reviewMetricValue": self.review_metric_value,
            "reviewThresholdCrossed": self.review_threshold_crossed,
            "nonclaim": self.nonclaim,
        }


def classify_population(
    candidate: PopulationCandidate,
    *,
    target_source_roots: Sequence[str],
    policy: GeneratedFamilyPolicy | None = None,
) -> PopulationClassification:
    """Assign exactly one primary population or fail closed as unclassified."""

    roots = _normalized_source_roots(target_source_roots)
    matches, family = _matched_family(candidate, policy)
    common = _common_classification_fields(candidate, policy, matches, family)
    target_owned = _target_owned(candidate.source_path, roots)
    if target_owned is None:
        return _unclassified(
            **common,
            code="population.ownership_unavailable",
            message="target source-root ownership could not be established",
        )
    if not target_owned:
        return _outside_target_classification(common, family)
    if candidate.compiler_generated:
        return _compiler_classification(candidate, common)
    if family is not None:
        return PopulationClassification(
            **common,
            population="project_generated",
            family_id=family.identifier,
            classification_authority="generated_family_policy",
        )
    return PopulationClassification(
        **common,
        population="target_owned",
        family_id=None,
        classification_authority="target_source_roots",
    )


def classify_populations(
    candidates: Sequence[PopulationCandidate],
    *,
    target_source_roots: Sequence[str],
    policy: GeneratedFamilyPolicy | None = None,
) -> tuple[PopulationClassification, ...]:
    """Classify unique rows in deterministic identifier order."""

    _require_unique_candidate_ids(candidates)
    return tuple(
        classify_population(
            candidate,
            target_source_roots=target_source_roots,
            policy=policy,
        )
        for candidate in sorted(candidates, key=lambda row: row.identifier)
    )


def summarize_populations(
    classifications: Sequence[PopulationClassification],
    *,
    selected_population: str = "target_owned",
) -> PopulationSummary:
    """Summarize raw and calibrated counts without fallback populations."""

    _validate_selected_population(selected_population)
    counts = _population_counts(classifications)
    denominator = len(classifications)
    numerator = (
        denominator
        if selected_population == "all"
        else counts[selected_population]
    )
    exclusions = (
        {}
        if selected_population == "all"
        else {
            name: count
            for name, count in counts.items()
            if name != selected_population
        }
    )
    return PopulationSummary(
        selected_population=selected_population,
        numerator=numerator,
        denominator=denominator,
        counts=counts,
        exclusions=exclusions,
    )


def aggregate_generated_families(
    candidates: Sequence[PopulationCandidate],
    classifications: Sequence[PopulationClassification],
    *,
    representative_limit: int = 5,
) -> tuple[GeneratedFamilyAggregate, ...]:
    """Aggregate project-generated module rows and retain raw identities."""

    if representative_limit < 1:
        raise ValueError("representative_limit must be positive")
    _require_unique_candidate_ids(candidates)
    groups = _generated_module_groups(
        candidates,
        _classification_map(classifications),
    )
    return tuple(
        _family_aggregate(family_id, rows, representative_limit)
        for family_id, rows in sorted(groups.items())
    )


def _common_classification_fields(
    candidate: PopulationCandidate,
    policy: GeneratedFamilyPolicy | None,
    matches: tuple[MatchedFamilyRule, ...],
    family: GeneratedFamilyRule | None,
) -> dict[str, Any]:
    """Return fields preserved across every primary-population outcome."""

    return {
        "identifier": candidate.identifier,
        "matched_rules": matches,
        "policy_digest": policy.digest if policy else None,
        "family_provenance": family.provenance if family else None,
        "family_review_threshold": (
            family.review_threshold if family else None
        ),
        "source_authority": candidate.source_authority,
        "compiler_authority": candidate.compiler_authority,
        "toolchain": candidate.toolchain,
    }


def _outside_target_classification(
    common: dict[str, Any],
    family: GeneratedFamilyRule | None,
) -> PopulationClassification:
    """Prefer imported ownership unless project policy contradicts it."""

    if family is not None:
        return _unclassified(
            **common,
            code="population.policy_ownership_conflict",
            message=(
                "generated-family policy matched a row outside every "
                "configured target source root"
            ),
        )
    return PopulationClassification(
        **common,
        population="imported",
        family_id=None,
        classification_authority="target_source_roots",
    )


def _compiler_classification(
    candidate: PopulationCandidate,
    common: dict[str, Any],
) -> PopulationClassification:
    """Require Lean/toolchain provenance before compiler classification."""

    if not candidate.compiler_authority or not candidate.toolchain:
        return _unclassified(
            **common,
            code="population.compiler_provenance_incomplete",
            message=(
                "compiler-generation evidence requires both backend authority "
                "and toolchain provenance"
            ),
        )
    return PopulationClassification(
        **common,
        population="compiler_generated",
        family_id=None,
        classification_authority=candidate.compiler_authority,
    )


def _unclassified(
    *,
    identifier: str,
    matched_rules: tuple[MatchedFamilyRule, ...],
    policy_digest: str | None,
    family_provenance: FamilyProvenance | None,
    family_review_threshold: FamilyReviewThreshold | None,
    source_authority: str,
    compiler_authority: str | None,
    toolchain: str | None,
    code: str,
    message: str,
) -> PopulationClassification:
    """Build one explicit fail-closed population row."""

    return PopulationClassification(
        identifier=identifier,
        population="unclassified",
        family_id=None,
        matched_rules=matched_rules,
        policy_digest=policy_digest,
        family_provenance=family_provenance,
        family_review_threshold=family_review_threshold,
        classification_authority="insufficient_or_contradictory_evidence",
        source_authority=source_authority,
        compiler_authority=compiler_authority,
        toolchain=toolchain,
        diagnostics=(CalibrationDiagnostic(code, message),),
    )


def _matched_family(
    candidate: PopulationCandidate,
    policy: GeneratedFamilyPolicy | None,
) -> tuple[tuple[MatchedFamilyRule, ...], GeneratedFamilyRule | None]:
    """Resolve one family or reject concrete overlapping selectors."""

    if policy is None:
        return (), None
    matches = [
        match
        for family in policy.families
        for match in _rule_matches(candidate, family)
    ]
    matches.sort(key=lambda row: (row.family_id, row.selector_kind, row.pattern))
    family_ids = sorted({row.family_id for row in matches})
    if len(family_ids) > 1:
        raise AmbiguousGeneratedFamilyError(
            candidate.identifier,
            family_ids,
            matches,
        )
    family_by_id = {family.identifier: family for family in policy.families}
    family = family_by_id[family_ids[0]] if family_ids else None
    return tuple(matches), family


def _rule_matches(
    candidate: PopulationCandidate,
    family: GeneratedFamilyRule,
) -> list[MatchedFamilyRule]:
    """Return every inspectable selector match within one family."""

    matches = [
        MatchedFamilyRule(family.identifier, "module", pattern)
        for pattern in family.module_patterns
        if fnmatch.fnmatchcase(candidate.module, pattern)
    ]
    if candidate.source_path is None:
        return matches
    return [
        *matches,
        *(
            MatchedFamilyRule(family.identifier, "path", pattern)
            for pattern in family.path_patterns
            if fnmatch.fnmatchcase(candidate.source_path, pattern)
        ),
    ]


def _population_counts(
    classifications: Sequence[PopulationClassification],
) -> dict[str, int]:
    """Count every primary population, including explicit zeroes."""

    counts = {name: 0 for name in PRIMARY_POPULATIONS}
    for row in classifications:
        if row.population not in counts:
            raise ValueError(f"unsupported classification population: {row.population}")
        counts[row.population] += 1
    return counts


def _validate_selected_population(selected_population: str) -> None:
    """Reject implicit fallback to unknown populations."""

    if selected_population not in {*PRIMARY_POPULATIONS, "all"}:
        raise ValueError(f"unsupported selected population: {selected_population}")


def _generated_module_groups(
    candidates: Sequence[PopulationCandidate],
    by_id: Mapping[str, PopulationClassification],
) -> dict[str, list[tuple[PopulationCandidate, PopulationClassification]]]:
    """Group only policy-classified module rows by family."""

    groups: dict[str, list[tuple[PopulationCandidate, PopulationClassification]]] = {}
    for candidate in candidates:
        classification = by_id.get(candidate.identifier)
        if classification is None:
            raise ValueError(
                f"candidate {candidate.identifier!r} has no population classification"
            )
        if _is_project_generated_module(candidate, classification):
            assert classification.family_id is not None
            groups.setdefault(classification.family_id, []).append(
                (candidate, classification)
            )
    return groups


def _is_project_generated_module(
    candidate: PopulationCandidate,
    classification: PopulationClassification,
) -> bool:
    """Return whether a row belongs in module-level family aggregation."""

    return (
        candidate.kind == "module"
        and classification.population == "project_generated"
        and classification.family_id is not None
    )


def _family_aggregate(
    family_id: str,
    rows: Sequence[tuple[PopulationCandidate, PopulationClassification]],
    representative_limit: int,
) -> GeneratedFamilyAggregate:
    """Build one family aggregate from classified module rows."""

    ordered = sorted(rows, key=lambda row: row[0].identifier)
    policy_digest = _consistent_policy_digest(family_id, ordered)
    provenance = _consistent_provenance(family_id, ordered)
    threshold = _consistent_review_threshold(family_id, ordered)
    members = [row[0] for row in ordered]
    internal, external, internal_count, external_count = (
        _family_import_relationships(members)
    )
    member_ids = tuple(member.identifier for member in members)
    metrics = {
        "memberCount": len(members),
        "sourceSizeBytes": sum(
            member.source_size_bytes for member in members
        ),
        "declarationCount": sum(
            member.declaration_count for member in members
        ),
        "importRelationshipCount": internal_count + external_count,
    }
    metric_value = metrics[threshold.metric] if threshold is not None else None
    return GeneratedFamilyAggregate(
        identifier=_stable_family_id(family_id),
        family_id=family_id,
        policy_digest=policy_digest,
        member_count=len(members),
        source_size_bytes=metrics["sourceSizeBytes"],
        declaration_count=metrics["declarationCount"],
        internal_import_targets=internal,
        external_import_targets=external,
        internal_import_count=internal_count,
        external_import_count=external_count,
        representative_member_ids=member_ids[:representative_limit],
        representative_omitted_count=max(0, len(member_ids) - representative_limit),
        raw_member_ids=member_ids,
        provenance=provenance,
        review_threshold=threshold,
        review_metric_value=metric_value,
        review_threshold_crossed=(
            metric_value is not None
            and threshold is not None
            and metric_value >= threshold.at_least
        ),
    )


def _consistent_policy_digest(
    family_id: str,
    rows: Sequence[tuple[PopulationCandidate, PopulationClassification]],
) -> str:
    """Require one non-null policy digest per aggregate."""

    digests = {row[1].policy_digest for row in rows}
    if None in digests or len(digests) != 1:
        raise ValueError(
            f"generated family {family_id!r} has inconsistent policy digests"
        )
    digest = next(iter(digests))
    assert digest is not None
    return digest


def _consistent_provenance(
    family_id: str,
    rows: Sequence[tuple[PopulationCandidate, PopulationClassification]],
) -> FamilyProvenance:
    """Require one policy provenance record per aggregate."""

    provenance_rows = [
        row[1].family_provenance
        for row in rows
        if row[1].family_provenance is not None
    ]
    normalized = {
        json.dumps(row.to_dict(), sort_keys=True, separators=(",", ":"))
        for row in provenance_rows
    }
    if len(provenance_rows) != len(rows) or len(normalized) != 1:
        raise ValueError(
            f"generated family {family_id!r} has inconsistent provenance"
        )
    return provenance_rows[0]


def _consistent_review_threshold(
    family_id: str,
    rows: Sequence[tuple[PopulationCandidate, PopulationClassification]],
) -> FamilyReviewThreshold | None:
    """Require one policy threshold value, including an explicit absence."""

    thresholds = {row[1].family_review_threshold for row in rows}
    if len(thresholds) != 1:
        raise ValueError(
            f"generated family {family_id!r} has inconsistent review thresholds"
        )
    return next(iter(thresholds))


def _family_import_relationships(
    members: Sequence[PopulationCandidate],
) -> tuple[tuple[str, ...], tuple[str, ...], int, int]:
    """Split and count family-module import relationships."""

    family_modules = {member.module for member in members}
    targets = {target for member in members for target in member.imports}
    internal_count = sum(
        target in family_modules
        for member in members
        for target in member.imports
    )
    external_count = sum(
        target not in family_modules
        for member in members
        for target in member.imports
    )
    return (
        tuple(sorted(targets & family_modules)),
        tuple(sorted(targets - family_modules)),
        internal_count,
        external_count,
    )


def _classification_map(
    rows: Sequence[PopulationClassification],
) -> dict[str, PopulationClassification]:
    """Return unique classifications by candidate identity."""

    result: dict[str, PopulationClassification] = {}
    for row in rows:
        if row.identifier in result:
            raise ValueError(f"duplicate classification id: {row.identifier}")
        result[row.identifier] = row
    return result


def _validate_candidate(candidate: PopulationCandidate) -> None:
    """Validate fields before normalizing a frozen candidate."""

    if not candidate.identifier.strip():
        raise ValueError("population candidate identifier must be non-empty")
    if candidate.kind not in ROW_KINDS:
        raise ValueError(f"unsupported population candidate kind: {candidate.kind}")
    if not candidate.module.strip() or not candidate.source_authority.strip():
        raise ValueError("candidate module and source authority must be non-empty")
    if candidate.compiler_generated not in {True, False, None}:
        raise ValueError("compiler_generated must be true, false, or unknown")
    if candidate.source_size_bytes < 0 or candidate.declaration_count < 0:
        raise ValueError("candidate size and declaration count must be non-negative")


def _normalized_imports(imports: Sequence[str]) -> tuple[str, ...]:
    """Return unique non-empty module identities in stable order."""

    return tuple(sorted({name.strip() for name in imports if name.strip()}))


def _require_unique_candidate_ids(
    candidates: Sequence[PopulationCandidate],
) -> None:
    """Reject ambiguous raw-row identities."""

    identifiers = [candidate.identifier for candidate in candidates]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("population candidate identifiers must be unique")


def _target_owned(
    source_path: str | None,
    roots: tuple[str, ...],
) -> bool | None:
    """Return source-root ownership, or unknown when evidence is absent."""

    if source_path is None or not roots:
        return None
    path = PurePosixPath(source_path)
    return any(_path_is_under_root(path, root) for root in roots)


def _path_is_under_root(path: PurePosixPath, root: str) -> bool:
    """Test equality or ancestry for one normalized source root."""

    return (
        root == "."
        or path == PurePosixPath(root)
        or PurePosixPath(root) in path.parents
    )


def _normalized_source_roots(roots: Sequence[str]) -> tuple[str, ...]:
    """Normalize unique repository-relative source roots."""

    return tuple(sorted({_normalized_source_root(root) for root in roots}))


def _normalized_source_root(root: str) -> str:
    """Preserve the explicit whole-repository root spelling."""

    return (
        "."
        if root.strip() == "."
        else normalize_relative_path(root, "target source root")
    )


def _stable_family_id(family_id: str) -> str:
    """Derive an aggregate identity from the policy's stable family identity."""

    digest = hashlib.sha256(family_id.encode("utf-8")).hexdigest()[:20]
    return f"ladon.generated_family.{digest}"
