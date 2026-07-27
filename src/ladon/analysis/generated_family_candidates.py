"""Pure advisory detection for regular numbered Lean module families.

This public module orchestrates canonical evidence preparation, exact profile
evaluation, and truthful coverage accounting.  The individual phases live in
small pure modules; callers retain the original detector API.
"""

from __future__ import annotations

import hashlib
import json
from typing import Collection, Iterable, Mapping, Sequence

from ladon.analysis.generated_family_candidate_coverage import (
    CANDIDATE_COLLECTION_ID,
    PARTITION_COLLECTION_ID,
    analysis_coverage,
    partition_coverage,
)
from ladon.analysis.generated_family_candidate_evaluation import (
    candidates_from_partitions,
    evaluate_partitions,
)
from ladon.analysis.generated_family_candidate_evidence import (
    candidate_module_evidence,
    declaration_stem_v1,
    internal_module_universe,
    internal_module_universe_fingerprint,
    partition_members,
    prepare_members,
    validate_evidence_population,
)
from ladon.analysis.generated_family_candidate_models import (
    CandidateModuleEvidence,
    GeneratedFamilyCandidateAnalysis,
)
from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    FEATURE_KEY_LIMIT,
    FEATURE_KEY_PROJECTION_VERSION,
    CandidateProfile,
    candidate_analysis_fingerprint,
)
from ladon.ir import LeanModule


def analyze_generated_family_candidates(
    modules: Mapping[str, LeanModule],
    *,
    populations: Mapping[str, str] | None = None,
    content_hashes: Mapping[str, str] | None = None,
    command_skeletons: Mapping[str, Sequence[str]] | None = None,
    internal_module_names: Collection[str] | None = None,
    incomplete_structural_modules: Collection[str] = (),
    incomplete_import_modules: Collection[str] = (),
    incomplete_lexical_modules: Collection[str] = (),
    inventory_complete: bool = True,
    evaluation_complete: bool | None = None,
    source_fingerprint: str,
    scope_fingerprint: str | None = None,
    policy_digest: str | None = None,
    profile: CandidateProfile = BUILTIN_CANDIDATE_PROFILE,
) -> GeneratedFamilyCandidateAnalysis:
    """Evaluate the selected exact profile over canonical module evidence.

    ``modules`` is the candidate-eligible selected population.
    ``internal_module_names`` may additionally name the full discovered
    inventory used to classify direct imports; it never adds candidate members.
    Omitting it preserves selected-population import membership.
    """

    evidence = candidate_module_evidence(
        modules,
        populations=populations,
        content_hashes=content_hashes,
        command_skeletons=command_skeletons,
        incomplete_structural_modules=incomplete_structural_modules,
        incomplete_import_modules=incomplete_import_modules,
        incomplete_lexical_modules=incomplete_lexical_modules,
    )
    return analyze_candidate_evidence(
        evidence,
        inventory_complete=inventory_complete,
        evaluation_complete=evaluation_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        policy_digest=policy_digest,
        profile=profile,
        internal_module_names=internal_module_names,
    )


def analyze_candidate_evidence(
    evidence: Iterable[CandidateModuleEvidence],
    *,
    inventory_complete: bool,
    evaluation_complete: bool | None = None,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    policy_digest: str | None,
    profile: CandidateProfile = BUILTIN_CANDIDATE_PROFILE,
    internal_module_names: Collection[str] | None = None,
) -> GeneratedFamilyCandidateAnalysis:
    """Evaluate adapted candidates against an optional larger internal universe."""

    rows = tuple(sorted(evidence, key=lambda row: row.module.name))
    validate_evidence_population(rows)
    internal_modules = internal_module_universe(rows, internal_module_names)
    internal_inventory_fingerprint = _optional_inventory_fingerprint(
        internal_modules,
        requested=internal_module_names is not None,
    )
    partition_inputs_complete = (
        inventory_complete
        if evaluation_complete is None
        else evaluation_complete
    )
    completeness_fingerprint = _completeness_fingerprint(
        rows,
        inventory_complete=inventory_complete,
        evaluation_complete=partition_inputs_complete,
    )
    fingerprint = candidate_analysis_fingerprint(
        profile,
        source_index_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        policy_digest=policy_digest,
        internal_inventory_fingerprint=internal_inventory_fingerprint,
        completeness_fingerprint=completeness_fingerprint,
    )
    prepared = prepare_members(rows, internal_modules)
    numbered, ungrouped = partition_members(
        prepared,
        grouping_version=profile.grouping_version,
    )
    partitions = evaluate_partitions(
        numbered,
        inventory_complete=partition_inputs_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        profile=profile,
    )
    candidates = candidates_from_partitions(
        partitions,
        profile=profile,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        policy_digest=policy_digest,
        analysis_fingerprint=fingerprint,
    )
    candidate_rows = analysis_coverage(
        candidates,
        partitions,
        prepared,
        inventory_complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
    )
    partition_rows = partition_coverage(
        partitions,
        prepared,
        inventory_complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
    )
    return GeneratedFamilyCandidateAnalysis(
        profile=profile.to_dict(),
        feature_projection={
            "version": FEATURE_KEY_PROJECTION_VERSION,
            "perKindVersionLimit": FEATURE_KEY_LIMIT,
            "selection": "member-count-descending-then-value-authority-v1",
            "population": "observed_aggregate_feature_keys",
        },
        analysis_fingerprint=fingerprint,
        candidates=candidates,
        partitions=partitions,
        ungrouped_members=tuple(row.public for row in ungrouped),
        candidate_coverage=candidate_rows,
        partition_coverage=partition_rows,
        internal_inventory_fingerprint=internal_inventory_fingerprint,
    )


def _optional_inventory_fingerprint(
    internal_modules: Collection[str],
    *,
    requested: bool,
) -> str | None:
    if not requested:
        return None
    return internal_module_universe_fingerprint(internal_modules)


def _completeness_fingerprint(
    rows: tuple[CandidateModuleEvidence, ...],
    *,
    inventory_complete: bool,
    evaluation_complete: bool,
) -> str:
    """Bind match/non-match decisions to their exact availability inputs."""

    encoded = json.dumps(
        {
            "schema": "ladon-generated-family-completeness-v1",
            "inventoryComplete": inventory_complete,
            "evaluationComplete": evaluation_complete,
            "members": [
                {
                    "module": row.module.name,
                    "structuralComplete": row.structural_complete,
                    "importsComplete": row.imports_complete,
                    "lexicalComplete": row.lexical_complete,
                }
                for row in rows
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


__all__ = [
    "CANDIDATE_COLLECTION_ID",
    "PARTITION_COLLECTION_ID",
    "analyze_candidate_evidence",
    "analyze_generated_family_candidates",
    "candidate_module_evidence",
    "declaration_stem_v1",
    "internal_module_universe_fingerprint",
]
