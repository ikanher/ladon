"""Coverage envelopes for generated-family candidate analysis."""

from __future__ import annotations

from ladon.analysis.generated_family_candidate_evidence import PreparedMember
from ladon.analysis.generated_family_candidate_models import (
    CandidatePartition,
    GeneratedFamilyCandidate,
)
from ladon.coverage import CollectionCoverage, CoverageCause

CANDIDATE_COLLECTION_ID = "generated_family.candidates"
PARTITION_COLLECTION_ID = "generated_family.numeric_partitions"


def representative_coverage(
    candidate_id: str,
    visible: int,
    total: int,
    *,
    limit: int,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    """Describe the bounded representative projection of candidate members."""

    causes = (
        (
            CoverageCause(
                kind="projection",
                identifier="coverage.representative_limit",
                detail=(
                    "Candidate representatives are bounded; canonical raw "
                    "member identities remain available."
                ),
                controlling_cap=limit,
            ),
        )
        if visible < total
        else ()
    )
    return CollectionCoverage.exact(
        identity=f"{candidate_id}.representatives",
        pointer=(
            "#/sections/generated_family_candidates/candidates/"
            f"{candidate_id}/representatives"
        ),
        visible=visible,
        total=total,
        population="candidate_member_modules",
        scope=candidate_id,
        authority="ladon_derived_projection",
        causes=causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def partition_member_coverage(
    partition_id: str,
    members: tuple[PreparedMember, ...],
    *,
    inventory_complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    """Describe exact or lower-bound membership for one numeric partition."""

    visible = len(members)
    complete = inventory_complete and all(
        row.public.structural_complete for row in members
    )
    common = {
        "identity": f"{partition_id}.members",
        "pointer": (
            "#/sections/generated_family_candidates/partitions/"
            f"{partition_id}/members"
        ),
        "visible": visible,
        "population": "observed_numeric_partition_members",
        "scope": partition_id,
        "authority": "source_index_path",
        "source_fingerprint": source_fingerprint,
        "scope_fingerprint": scope_fingerprint,
        "analysis_fingerprint": analysis_fingerprint,
    }
    if complete:
        return CollectionCoverage.exact(total=visible, **common)
    return CollectionCoverage.unknown(
        observed_lower_bound=visible,
        completeness="partial",
        causes=(incomplete_cause(partition_id),),
        **common,
    )


def partition_feature_coverage(
    partition_id: str,
    *,
    visible: int,
    total: int,
    per_kind_version_limit: int,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    """Describe bounded feature-key retention with an exact source total."""

    causes = (
        (
            CoverageCause(
                kind="projection",
                identifier="candidate.feature_key_limit",
                detail=(
                    "Feature keys retain the strongest bounded rows per kind "
                    "and version; exact key cardinality remains reported."
                ),
                controlling_cap=per_kind_version_limit,
            ),
        )
        if visible < total
        else ()
    )
    return CollectionCoverage.exact(
        identity=f"{partition_id}.features",
        pointer=(
            "#/sections/generated_family_candidates/partitions/"
            f"{partition_id}/features"
        ),
        visible=visible,
        total=total,
        observed_lower_bound=total,
        population="observed_aggregate_feature_keys",
        scope=partition_id,
        authority="ladon_derived_aggregation",
        causes=causes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )


def analysis_coverage(
    candidates: tuple[GeneratedFamilyCandidate, ...],
    partitions: tuple[CandidatePartition, ...],
    members: tuple[PreparedMember, ...],
    *,
    inventory_complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    """Describe the visibility of exact-profile candidate matches."""

    unavailable = tuple(
        partition.identifier
        for partition in partitions
        if partition.evaluation_status == "unavailable"
    )
    structural_unknown = any(
        not row.public.structural_complete for row in members
    )
    common = {
        "identity": CANDIDATE_COLLECTION_ID,
        "pointer": "#/sections/generated_family_candidates/candidates",
        "visible": len(candidates),
        "population": "exact_profile_matches",
        "scope": "selected_analysis_scope",
        "authority": "ladon_derived_heuristic",
        "source_fingerprint": source_fingerprint,
        "scope_fingerprint": scope_fingerprint,
        "analysis_fingerprint": analysis_fingerprint,
    }
    if inventory_complete and not structural_unknown and not unavailable:
        return CollectionCoverage.exact(total=len(candidates), **common)
    causes = candidate_coverage_causes(
        inventory_complete=inventory_complete,
        structural_unknown=structural_unknown,
        unavailable=unavailable,
    )
    return CollectionCoverage.unknown(
        observed_lower_bound=len(candidates),
        completeness="partial",
        causes=causes,
        **common,
    )


def partition_coverage(
    partitions: tuple[CandidatePartition, ...],
    members: tuple[PreparedMember, ...],
    *,
    inventory_complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> CollectionCoverage:
    """Describe visibility of structural numbered-module partitions."""

    visible = len(partitions)
    complete = inventory_complete and all(
        row.public.structural_complete for row in members
    )
    common = {
        "identity": PARTITION_COLLECTION_ID,
        "pointer": "#/sections/generated_family_candidates/partitions",
        "visible": visible,
        "population": "numeric_structural_partitions",
        "scope": "selected_analysis_scope",
        "authority": "source_index_path",
        "source_fingerprint": source_fingerprint,
        "scope_fingerprint": scope_fingerprint,
        "analysis_fingerprint": analysis_fingerprint,
    }
    if complete:
        return CollectionCoverage.exact(total=visible, **common)
    return CollectionCoverage.unknown(
        observed_lower_bound=visible,
        completeness="partial",
        causes=(incomplete_cause(PARTITION_COLLECTION_ID),),
        **common,
    )


def candidate_coverage_causes(
    *,
    inventory_complete: bool,
    structural_unknown: bool,
    unavailable: tuple[str, ...],
) -> tuple[CoverageCause, ...]:
    """Return every typed cause limiting candidate collection coverage."""

    causes: list[CoverageCause] = []
    if not inventory_complete:
        causes.append(
            CoverageCause(
                kind="extraction",
                identifier="candidate.source_inventory_incomplete",
                detail=(
                    "The source inventory is incomplete, so unobserved "
                    "candidate partitions may exist."
                ),
            )
        )
    if structural_unknown:
        causes.append(
            CoverageCause(
                kind="extraction",
                identifier="candidate.structural_evidence_incomplete",
                detail=(
                    "One or more module path identities are incomplete."
                ),
            )
        )
    if unavailable:
        causes.append(
            CoverageCause(
                kind="analysis",
                identifier="candidate.required_evidence_unavailable",
                detail=(
                    f"{len(unavailable)} numeric partitions lack complete "
                    "required import or lexical evidence."
                ),
            )
        )
    return tuple(causes)


def incomplete_cause(subject: str) -> CoverageCause:
    """Return the shared structural lower-bound cause."""

    return CoverageCause(
        kind="extraction",
        identifier="candidate.structural_population_incomplete",
        detail=(
            "Numeric partition membership is an observed lower bound because "
            f"required structural evidence is incomplete for {subject}."
        ),
    )


__all__ = [
    "CANDIDATE_COLLECTION_ID",
    "PARTITION_COLLECTION_ID",
    "analysis_coverage",
    "partition_coverage",
    "partition_feature_coverage",
    "partition_member_coverage",
    "representative_coverage",
]
