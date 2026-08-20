"""Exact profile evaluation over prepared numbered-module partitions."""

from __future__ import annotations

import itertools
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field

from ladon.analysis.generated_family_candidate_coverage import (
    partition_feature_coverage,
    partition_member_coverage,
    representative_coverage,
)
from ladon.analysis.generated_family_candidate_evidence import (
    CONTENT_HASH_VERSION,
    INTERNAL_IMPORT_VERSION,
    PartitionKey,
    PreparedMember,
    anchor_sort_key,
    candidate_source_anchor,
    known_suffix,
    stable_id,
)
from ladon.analysis.generated_family_candidate_models import (
    CandidateClauseResult,
    CandidateFeature,
    CandidatePartition,
    CandidateRepresentative,
    CandidateSequence,
    CandidateSourceAnchor,
    GeneratedFamilyCandidate,
)
from ladon.analysis.generated_family_candidate_profile import (
    COMMAND_SKELETON_VERSION,
    DECLARATION_STEM_VERSION,
    FEATURE_KEY_LIMIT,
    CandidateProfile,
    CandidateRatio,
)
from ladon.coverage import CollectionCoverage
from ladon.ir import LeanTextDeclaration


def evaluate_partitions(
    numbered: Mapping[
        PartitionKey,
        tuple[PreparedMember, ...],
    ],
    *,
    inventory_complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    profile: CandidateProfile,
) -> tuple[CandidatePartition, ...]:
    """Evaluate every structural partition in deterministic key order."""

    return tuple(
        _evaluate_partition(
            key,
            members,
            inventory_complete=inventory_complete,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            profile=profile,
        )
        for key, members in sorted(numbered.items())
    )


def candidates_from_partitions(
    partitions: Iterable[CandidatePartition],
    *,
    profile: CandidateProfile,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    policy_digest: str | None,
    analysis_fingerprint: str,
) -> tuple[GeneratedFamilyCandidate, ...]:
    """Promote only exact profile matches into advisory candidates."""

    return tuple(
        _candidate_from_partition(
            partition,
            profile=profile,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            policy_digest=policy_digest,
            analysis_fingerprint=analysis_fingerprint,
        )
        for partition in partitions
        if partition.evaluation_status == "match"
    )


def _evaluate_partition(
    key: PartitionKey,
    members: tuple[PreparedMember, ...],
    *,
    inventory_complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    profile: CandidateProfile,
) -> CandidatePartition:
    partition_id = _partition_id(key, members, profile)
    sequence = _sequence(key, members, profile.representative_limit)
    features, feature_total = _partition_features(
        partition_id,
        members,
        feature_key_limit=FEATURE_KEY_LIMIT,
        representative_limit=profile.representative_limit,
    )
    selected_import = _best_feature(
        features,
        versions=(INTERNAL_IMPORT_VERSION,),
    )
    selected_lexical = _best_feature(
        features,
        versions=profile.lexical_features,
    )
    clauses = _predicate_clauses(
        members,
        sequence,
        selected_import,
        selected_lexical,
        inventory_complete=inventory_complete,
        profile=profile,
    )
    coverage = partition_member_coverage(
        partition_id,
        members,
        inventory_complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    feature_coverage = partition_feature_coverage(
        partition_id,
        visible=len(features),
        total=feature_total,
        per_kind_version_limit=FEATURE_KEY_LIMIT,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    return CandidatePartition(
        identifier=partition_id,
        sequence=sequence,
        members=tuple(row.public for row in members),
        features=features,
        feature_coverage=feature_coverage,
        clauses=clauses,
        evaluation_status=_evaluation_status(clauses),
        selected_import_feature_id=_feature_id(selected_import),
        selected_lexical_feature_id=_feature_id(selected_lexical),
        member_coverage=coverage,
    )


def _partition_id(
    key: PartitionKey,
    members: tuple[PreparedMember, ...],
    profile: CandidateProfile,
) -> str:
    return stable_id(
        "ladon.generated_family_partition",
        {
            "groupingVersion": profile.grouping_version,
            "parent": key[0],
            "prefix": key[1],
            "suffixSpellingWidth": key[2],
            "members": [
                {
                    "id": row.public.identifier,
                    "path": row.public.path,
                    "suffix": row.public.suffix_value,
                }
                for row in members
            ],
        },
    )


def _feature_id(feature: CandidateFeature | None) -> str | None:
    return feature.identifier if feature is not None else None


def _sequence(
    key: PartitionKey,
    members: tuple[PreparedMember, ...],
    representative_limit: int,
) -> CandidateSequence:
    suffix_values = tuple(known_suffix(row.public) for row in members)
    occupied = tuple(sorted(set(suffix_values)))
    minimum = occupied[0]
    maximum = occupied[-1]
    span = maximum - minimum + 1
    ranges = _gap_ranges(occupied)
    visible_ranges = ranges[:representative_limit]
    return CandidateSequence(
        parent=key[0],
        basename_prefix=key[1],
        member_count=len(members),
        suffix_values=suffix_values,
        occupied_suffix_values=occupied,
        minimum_suffix=minimum,
        maximum_suffix=maximum,
        inclusive_span=span,
        gap_count=span - len(occupied),
        gap_ranges=visible_ranges,
        gap_range_omitted_count=len(ranges) - len(visible_ranges),
    )


def _gap_ranges(values: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (left + 1, right - 1)
        for left, right in itertools.pairwise(values)
        if right - left > 1
    )


FeatureKey = tuple[str, str, str, str]


@dataclass
class _FeatureCount:
    """Exact compact counts used to select bounded aggregate keys."""

    member_count: int = 0


@dataclass
class _FeatureState:
    """Bounded evidence retained only for selected aggregate keys."""

    member_ids: set[str] = field(default_factory=set)
    occurrence_count: int = 0
    anchors: list[CandidateSourceAnchor] = field(default_factory=list)
    anchor_count: int = 0


def _partition_features(
    partition_id: str,
    members: tuple[PreparedMember, ...],
    *,
    feature_key_limit: int,
    representative_limit: int,
) -> tuple[tuple[CandidateFeature, ...], int]:
    counts = _feature_counts(members)
    selected_keys = _retained_feature_keys(
        counts,
        limit=feature_key_limit,
    )
    states = _selected_feature_states(
        members,
        selected_keys,
        anchor_limit=representative_limit,
    )
    order = {member.public.identifier: index for index, member in enumerate(members)}
    completeness = _feature_completeness(members)
    return (
        tuple(
            _aggregate_feature(
                partition_id,
                key,
                states[key],
                order=order,
                representative_limit=representative_limit,
                complete=completeness.get(key[0], True),
            )
            for key in selected_keys
        ),
        len(counts),
    )


def _feature_counts(
    members: tuple[PreparedMember, ...],
) -> dict[FeatureKey, _FeatureCount]:
    counts: dict[FeatureKey, _FeatureCount] = {}
    for member in members:
        for key in _member_feature_keys(member):
            counts.setdefault(key, _FeatureCount())
            counts[key].member_count += 1
    return counts


def _retained_feature_keys(
    counts: Mapping[FeatureKey, _FeatureCount],
    *,
    limit: int,
) -> tuple[FeatureKey, ...]:
    grouped: defaultdict[tuple[str, str], list[FeatureKey]] = defaultdict(list)
    for key in counts:
        grouped[(key[0], key[1])].append(key)
    retained = {
        key
        for group in grouped.values()
        for key in sorted(
            group,
            key=lambda row: (
                -counts[row].member_count,
                row[2],
                row[3],
            ),
        )[:limit]
    }
    return tuple(sorted(retained))


def _selected_feature_states(
    members: tuple[PreparedMember, ...],
    selected_keys: tuple[FeatureKey, ...],
    *,
    anchor_limit: int,
) -> dict[FeatureKey, _FeatureState]:
    selected = frozenset(selected_keys)
    states = {key: _FeatureState() for key in selected_keys}
    for member in members:
        for key, declaration in _member_feature_occurrences(member):
            if key not in selected:
                continue
            state = states[key]
            state.member_ids.add(member.public.identifier)
            state.occurrence_count += 1
            if declaration is not None:
                state.anchor_count += 1
                _retain_anchor(
                    state.anchors,
                    candidate_source_anchor(member.public, declaration),
                    limit=anchor_limit,
                )
    return states


def _member_feature_keys(member: PreparedMember) -> set[FeatureKey]:
    """Return distinct aggregate keys without allocating contribution rows."""

    return {
        key
        for key, _ in _member_feature_occurrences(member)
    }


def _member_feature_occurrences(
    member: PreparedMember,
) -> Iterable[tuple[FeatureKey, LeanTextDeclaration | None]]:
    """Yield compact aggregate operands for one prepared member."""

    public = member.public
    for value in public.direct_internal_imports:
        yield (
            (
                "direct_internal_import",
                INTERNAL_IMPORT_VERSION,
                value,
                "module_import_graph",
            ),
            None,
        )
    for stem, declaration in member.declaration_anchors:
        yield (
            (
                "declaration_stem",
                DECLARATION_STEM_VERSION,
                stem,
                "lexical_text",
            ),
            declaration,
        )
    for value in public.command_skeletons:
        yield (
            (
                "command_skeleton",
                COMMAND_SKELETON_VERSION,
                value,
                "lexical_text",
            ),
            None,
        )
    if public.content_sha256 is not None:
        yield (
            (
                "exact_source_hash",
                CONTENT_HASH_VERSION,
                public.content_sha256,
                "source_index_content_hash",
            ),
            None,
        )
    for version, value in member.block_hash_versions:
        yield (
            (
                "normalized_declaration_block_hash",
                version,
                value,
                "lexical_declaration_block_hash",
            ),
            None,
        )


def _retain_anchor(
    anchors: list[CandidateSourceAnchor],
    anchor: CandidateSourceAnchor,
    *,
    limit: int,
) -> None:
    anchors.append(anchor)
    anchors.sort(key=anchor_sort_key)
    if len(anchors) > limit:
        anchors.pop()


def _aggregate_feature(
    partition_id: str,
    key: FeatureKey,
    state: _FeatureState,
    *,
    order: Mapping[str, int],
    representative_limit: int,
    complete: bool,
) -> CandidateFeature:
    kind, version, value, authority = key
    member_ids = tuple(
        sorted(
            state.member_ids,
            key=lambda member_id: (order[member_id], member_id),
        )
    )
    representatives = member_ids[:representative_limit]
    visible_anchors = tuple(state.anchors)
    return CandidateFeature(
        identifier=stable_id(
            "ladon.generated_family_feature",
            {
                "partitionId": partition_id,
                "kind": kind,
                "version": version,
                "value": value,
            },
        ),
        kind=kind,
        version=version,
        value=value,
        authority=authority,
        member_ids=member_ids,
        occurrence_count=state.occurrence_count,
        representative_member_ids=representatives,
        representative_omitted_count=len(member_ids) - len(representatives),
        source_anchors=visible_anchors,
        source_anchor_omitted_count=(
            state.anchor_count - len(visible_anchors)
        ),
        complete=complete,
    )


def _feature_completeness(
    members: tuple[PreparedMember, ...],
) -> dict[str, bool]:
    """Compute partition-wide availability once rather than per feature key."""

    imports_complete = all(row.public.imports_complete for row in members)
    lexical_complete = all(row.public.lexical_complete for row in members)
    return {
        "direct_internal_import": imports_complete,
        "declaration_stem": lexical_complete,
        "command_skeleton": lexical_complete,
        "normalized_declaration_block_hash": lexical_complete,
    }


def _best_feature(
    features: tuple[CandidateFeature, ...],
    *,
    versions: Collection[str],
) -> CandidateFeature | None:
    eligible = [feature for feature in features if feature.version in versions]
    if not eligible:
        return None
    version_order = {version: index for index, version in enumerate(versions)}
    return min(
        eligible,
        key=lambda feature: (
            -feature.member_count,
            version_order[feature.version],
            feature.value,
            feature.identifier,
        ),
    )


def _predicate_clauses(
    members: tuple[PreparedMember, ...],
    sequence: CandidateSequence,
    import_feature: CandidateFeature | None,
    lexical_feature: CandidateFeature | None,
    *,
    inventory_complete: bool,
    profile: CandidateProfile,
) -> tuple[CandidateClauseResult, ...]:
    member_count = len(members)
    imports_complete = inventory_complete and all(
        row.public.imports_complete for row in members
    )
    lexical_complete = inventory_complete and all(
        row.public.lexical_complete for row in members
    )
    structural_complete = inventory_complete and all(
        row.public.structural_complete for row in members
    )
    import_count = import_feature.member_count if import_feature is not None else 0
    lexical_count = lexical_feature.member_count if lexical_feature is not None else 0
    return (
        _minimum_member_clause(member_count, profile.minimum_members),
        _ratio_clause(
            "numeric_density",
            sequence.occupied_count,
            sequence.inclusive_span,
            profile.minimum_density,
            complete=structural_complete,
            witness=None,
            evidence_label="numeric sibling density",
        ),
        _ratio_clause(
            "common_direct_internal_import",
            import_count,
            member_count,
            profile.direct_import_coverage,
            complete=imports_complete,
            witness=import_feature,
            evidence_label="direct internal-import member coverage",
        ),
        _ratio_clause(
            "common_lexical_witness",
            lexical_count,
            member_count,
            profile.lexical_coverage,
            complete=lexical_complete,
            witness=lexical_feature,
            evidence_label="normalized lexical member coverage",
        ),
        _completeness_clause(
            members,
            inventory_complete=inventory_complete,
        ),
    )


def _minimum_member_clause(
    observed: int,
    required: int,
) -> CandidateClauseResult:
    passed = observed >= required
    return CandidateClauseResult(
        identifier="minimum_member_count",
        status="passed" if passed else "failed",
        observed_numerator=observed,
        observed_denominator=1,
        threshold_numerator=required,
        threshold_denominator=1,
        required_count=required,
        witness_feature_id=None,
        reason=(f"observed {observed} members; at least {required} are required"),
    )


def _ratio_clause(
    identifier: str,
    observed: int,
    population: int,
    threshold: CandidateRatio,
    *,
    complete: bool,
    witness: CandidateFeature | None,
    evidence_label: str,
) -> CandidateClauseResult:
    required = threshold.required_count(population)
    if not complete:
        status = "unavailable"
        reason = f"{evidence_label} is incomplete or unknown"
    else:
        passed = threshold.satisfied_by(observed, population)
        status = "passed" if passed else "failed"
        reason = (
            f"observed {observed}/{population}; required at least "
            f"{threshold.numerator}/{threshold.denominator} "
            f"({required} members)"
        )
    return CandidateClauseResult(
        identifier=identifier,
        status=status,
        observed_numerator=observed,
        observed_denominator=population,
        threshold_numerator=threshold.numerator,
        threshold_denominator=threshold.denominator,
        required_count=required,
        witness_feature_id=_feature_id(witness),
        reason=reason,
    )


def _completeness_clause(
    members: tuple[PreparedMember, ...],
    *,
    inventory_complete: bool,
) -> CandidateClauseResult:
    complete_members = sum(
        row.public.structural_complete
        and row.public.imports_complete
        and row.public.lexical_complete
        for row in members
    )
    complete = inventory_complete and complete_members == len(members)
    return CandidateClauseResult(
        identifier="required_evidence_complete",
        status="passed" if complete else "unavailable",
        observed_numerator=complete_members,
        observed_denominator=len(members),
        threshold_numerator=1,
        threshold_denominator=1,
        required_count=len(members),
        witness_feature_id=None,
        reason=(
            "all required structural, import, and lexical inputs are complete"
            if complete
            else "one or more required inputs or the inventory are unknown"
        ),
    )


def _evaluation_status(
    clauses: tuple[CandidateClauseResult, ...],
) -> str:
    substantive = clauses[:-1]
    if any(clause.status == "unavailable" for clause in clauses):
        return "unavailable"
    if any(clause.status == "failed" for clause in substantive):
        return "non_match"
    return "match"


def _candidate_from_partition(
    partition: CandidatePartition,
    *,
    profile: CandidateProfile,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    policy_digest: str | None,
    analysis_fingerprint: str,
) -> GeneratedFamilyCandidate:
    _require_candidate_witnesses(partition)
    candidate_id = _candidate_id(partition, profile)
    representatives = tuple(
        CandidateRepresentative(
            member_id=member.identifier,
            suffix_value=known_suffix(member),
            rank=index,
        )
        for index, member in enumerate(
            partition.members[: profile.representative_limit],
            start=1,
        )
    )
    member_coverage = _candidate_member_coverage(
        candidate_id,
        partition,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    representative_rows = representative_coverage(
        candidate_id,
        len(representatives),
        len(partition.members),
        limit=profile.representative_limit,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    return GeneratedFamilyCandidate(
        identifier=candidate_id,
        profile_version=profile.profile_version,
        profile_digest=profile.digest,
        partition_id=partition.identifier,
        sequence=partition.sequence,
        members=partition.members,
        clauses=partition.clauses,
        import_feature_id=_required_feature_id(partition.selected_import_feature_id),
        lexical_feature_id=_required_feature_id(partition.selected_lexical_feature_id),
        representatives=representatives,
        representative_coverage=representative_rows,
        member_coverage=member_coverage,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        policy_digest=policy_digest,
        analysis_fingerprint=analysis_fingerprint,
    )


def _require_candidate_witnesses(partition: CandidatePartition) -> None:
    if (
        partition.selected_import_feature_id is None
        or partition.selected_lexical_feature_id is None
    ):
        raise AssertionError("matched partition lost a required witness")


def _required_feature_id(identity: str | None) -> str:
    if identity is None:
        raise AssertionError("matched partition lost a required witness")
    return identity


def _candidate_id(
    partition: CandidatePartition,
    profile: CandidateProfile,
) -> str:
    return stable_id(
        "ladon.generated_family_candidate",
        {
            "profileVersion": profile.profile_version,
            "profileDigest": profile.digest,
            "partitionId": partition.identifier,
            "members": [
                {
                    "id": member.identifier,
                    "path": member.path,
                    "suffix": member.suffix_value,
                }
                for member in partition.members
            ],
        },
    )


def _candidate_member_coverage(
    candidate_id: str,
    partition: CandidatePartition,
    *,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    return CollectionCoverage.exact(
        identity=f"{candidate_id}.members",
        pointer=(
            f"#/sections/generated_family_candidates/candidates/{candidate_id}/members"
        ),
        visible=len(partition.members),
        total=len(partition.members),
        population="candidate_member_modules",
        scope=partition.identifier,
        authority="source_index_path",
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


__all__ = [
    "candidates_from_partitions",
    "evaluate_partitions",
]
