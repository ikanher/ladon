"""Pipeline/report adapters for generated-family candidate evidence.

The detector core is intentionally report-neutral and side-effect free.  This
module joins it to already-captured source-index and module-DAG evidence without
rescanning source files or changing calibrated module populations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ladon.analysis.generated_family_candidate_models import (
    PRIMARY_POPULATIONS,
    GeneratedFamilyCandidate,
    GeneratedFamilyCandidateAnalysis,
)
from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    COMMAND_SKELETON_VERSION,
    CandidateProfile,
)
from ladon.analysis.generated_family_candidates import (
    CANDIDATE_COLLECTION_ID,
    PARTITION_COLLECTION_ID,
    analyze_generated_family_candidates,
)
from ladon.coverage import (
    CollectionCoverage,
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
)
from ladon.ir import LeanModule
from ladon.lexical_command_skeleton import (
    command_skeleton_evidence_complete,
    valid_command_skeleton_row,
)
from ladon.source_index_models import SourceIndex

GENERATED_FAMILY_REPORT_BASE = "#/sections/module_dag/generated_family_candidates"
GENERATED_FAMILY_CANDIDATE_COVERAGE_FIELD = "generated_family_candidate_coverage"
GENERATED_FAMILY_PARTITION_COVERAGE_FIELD = "generated_family_partition_coverage"


class CandidateIntegrationError(ValueError):
    """Canonical candidate inputs cannot be joined without guessing."""


@dataclass(frozen=True)
class GeneratedFamilyCandidateSurface:
    """One report-ready candidate analysis and its producer registrations."""

    analysis: GeneratedFamilyCandidateAnalysis
    candidate_coverage: CollectionCoverage
    partition_coverage: CollectionCoverage
    producer_registry: ProducerRegistry
    input_summary: Mapping[str, Any]

    def coverage_rows(self) -> tuple[CollectionCoverage, ...]:
        """Return the finite report coverage rows owned by this producer."""

        return (self.candidate_coverage, self.partition_coverage)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic report-local evidence with resolvable pointers."""

        payload = self.analysis.to_dict()
        payload["coverage"] = {
            "candidates": self.candidate_coverage.to_dict(),
            "partitions": self.partition_coverage.to_dict(),
        }
        _adapt_partition_rows(payload)
        _adapt_candidate_rows(payload, self.analysis.candidates)
        payload["producerRegistry"] = self.producer_registry.to_dict()
        payload["input"] = dict(self.input_summary)
        return payload

    def to_module_dag_fields(self) -> dict[str, Any]:
        """Return fields suitable for one update of the module-DAG phase."""

        return {
            "generated_family_candidates": self.to_dict(),
            GENERATED_FAMILY_CANDIDATE_COVERAGE_FIELD: (
                self.candidate_coverage.to_dict()
            ),
            GENERATED_FAMILY_PARTITION_COVERAGE_FIELD: (
                self.partition_coverage.to_dict()
            ),
        }


def analyze_generated_family_candidate_surface(
    module_dag: Mapping[str, Any],
    source_index: SourceIndex,
    *,
    profile: CandidateProfile = BUILTIN_CANDIDATE_PROFILE,
) -> GeneratedFamilyCandidateSurface:
    """Analyze the selected DAG from canonical source-index evidence.

    Call this after population calibration has attached ``population`` to each
    selected ``module_metadata`` row.  The source index supplies complete
    lexical declarations and content hashes; bounded report declaration rows
    are deliberately not used as detector inputs.
    """

    metadata = _module_metadata(module_dag)
    scope_fingerprint = _scope_fingerprint(module_dag, source_index)
    indexed_modules = source_index.modules
    internal_module_names = source_index.discovered_module_paths
    selected_modules, missing_modules = _selected_source_modules(
        metadata,
        indexed_modules,
    )
    populations = _selected_populations(metadata, selected_modules)
    content_hashes = {
        entry.name: entry.content_sha256
        for entry in source_index.entries
        if entry.name in selected_modules
    }
    command_skeletons, incomplete_command_skeleton_modules = (
        _selected_command_skeletons(selected_modules)
    )
    required_incomplete_skeleton_modules = (
        incomplete_command_skeleton_modules
        if COMMAND_SKELETON_VERSION in profile.lexical_features
        else ()
    )
    selected_scope_complete = _selected_candidate_scope_complete(
        module_dag,
        missing_modules,
    )
    inventory_complete = (
        source_index.index_status == "complete"
        and selected_scope_complete
    )
    policy_digest = _policy_digest(module_dag)
    analysis = analyze_generated_family_candidates(
        selected_modules,
        populations=populations,
        content_hashes=content_hashes,
        command_skeletons=command_skeletons,
        incomplete_lexical_modules=required_incomplete_skeleton_modules,
        internal_module_names=internal_module_names,
        inventory_complete=inventory_complete,
        evaluation_complete=selected_scope_complete,
        source_fingerprint=source_index.fingerprint,
        scope_fingerprint=scope_fingerprint,
        policy_digest=policy_digest,
        profile=profile,
    )
    candidate_coverage = replace(
        analysis.candidate_coverage,
        pointer=f"{GENERATED_FAMILY_REPORT_BASE}/candidates",
    )
    partition_coverage = replace(
        analysis.partition_coverage,
        pointer=f"{GENERATED_FAMILY_REPORT_BASE}/partitions",
    )
    return GeneratedFamilyCandidateSurface(
        analysis=analysis,
        candidate_coverage=candidate_coverage,
        partition_coverage=partition_coverage,
        producer_registry=_producer_registry(analysis),
        input_summary={
            "selectedModuleCount": len(metadata),
            "indexedSelectedModuleCount": len(selected_modules),
            "missingSelectedModuleCount": len(missing_modules),
            "missingSelectedModules": list(missing_modules),
            "incompleteCommandSkeletonModuleCount": len(
                incomplete_command_skeleton_modules
            ),
            "incompleteCommandSkeletonModules": list(
                incomplete_command_skeleton_modules
            ),
            "commandSkeletonRequired": (
                COMMAND_SKELETON_VERSION in profile.lexical_features
            ),
            "sourceIndexStatus": source_index.index_status,
            "selectedScopeComplete": selected_scope_complete,
            "selectedInputsComplete": (
                selected_scope_complete
                and not required_incomplete_skeleton_modules
            ),
            "inventoryComplete": inventory_complete,
            "sourceIndexFingerprint": source_index.fingerprint,
            "internalInventoryModuleCount": len(internal_module_names),
            "internalInventoryFingerprint": (analysis.internal_inventory_fingerprint),
            "scopeFingerprint": scope_fingerprint,
            "policyDigest": policy_digest,
            "complete": (
                inventory_complete and not required_incomplete_skeleton_modules
            ),
            "authority": (
                "source_index_manifest_population_calibration_and_module_import_graph"
            ),
        },
    )


def _module_metadata(
    module_dag: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    raw = module_dag.get("module_metadata")
    if not isinstance(raw, Mapping):
        raise CandidateIntegrationError(
            "generated-family analysis requires module-DAG metadata"
        )
    rows: dict[str, Mapping[str, Any]] = {}
    for name, row in raw.items():
        if not isinstance(name, str) or not name or not isinstance(row, Mapping):
            raise CandidateIntegrationError(
                "module-DAG metadata contains a malformed selected-module row"
            )
        rows[name] = row
    return rows


def _scope_fingerprint(
    module_dag: Mapping[str, Any],
    source_index: SourceIndex,
) -> str | None:
    raw = module_dag.get("analysis_scope")
    if not isinstance(raw, Mapping):
        return None
    fingerprint = _optional_text(raw.get("fingerprint"))
    scope_source = _optional_text(raw.get("sourceIndexFingerprint"))
    if scope_source is not None and scope_source != source_index.fingerprint:
        raise CandidateIntegrationError(
            "analysis scope and source index have incompatible fingerprints"
        )
    return fingerprint


def _selected_source_modules(
    metadata: Mapping[str, Mapping[str, Any]],
    index_modules: Mapping[str, LeanModule],
) -> tuple[dict[str, LeanModule], tuple[str, ...]]:
    selected: dict[str, LeanModule] = {}
    missing: list[str] = []
    for name, row in sorted(metadata.items()):
        module = index_modules.get(name)
        if module is None:
            missing.append(name)
            continue
        expected_path = _optional_text(row.get("path"))
        if expected_path is not None and expected_path != module.path:
            raise CandidateIntegrationError(
                f"module-DAG/source-index path mismatch for {name}"
            )
        selected[name] = module
    return selected, tuple(missing)


def _selected_populations(
    metadata: Mapping[str, Mapping[str, Any]],
    modules: Mapping[str, LeanModule],
) -> dict[str, str]:
    populations: dict[str, str] = {}
    for name in modules:
        raw = metadata[name].get("population", "unclassified")
        if not isinstance(raw, str) or raw not in PRIMARY_POPULATIONS:
            raise CandidateIntegrationError(
                f"unsupported calibrated population for {name}: {raw!r}"
            )
        populations[name] = raw
    return populations


def _selected_command_skeletons(
    modules: Mapping[str, LeanModule],
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    """Read valid canonical rows and retain modules with unusable rows."""

    result: dict[str, tuple[str, ...]] = {}
    incomplete: list[str] = []
    for name, module in modules.items():
        values = {
            row.value
            for row in module.command_skeletons
            if valid_command_skeleton_row(row, module)
        }
        if values:
            result[name] = tuple(sorted(values))
        if not command_skeleton_evidence_complete(module):
            incomplete.append(name)
    return result, tuple(incomplete)


def _selected_candidate_scope_complete(
    module_dag: Mapping[str, Any],
    missing_modules: tuple[str, ...],
) -> bool:
    if missing_modules:
        return False
    scope = module_dag.get("analysis_scope")
    if isinstance(scope, Mapping):
        if scope.get("completeness") not in {None, "complete"}:
            return False
        if scope.get("truncated") is True:
            return False
    phase = module_dag.get("completeness")
    return not (isinstance(phase, Mapping) and phase.get("status") not in {None, "complete", "ok"})


def _policy_digest(module_dag: Mapping[str, Any]) -> str | None:
    calibration = module_dag.get("population_calibration")
    if not isinstance(calibration, Mapping):
        return None
    policy = calibration.get("policy")
    if isinstance(policy, Mapping):
        digest = _optional_text(policy.get("policyDigest"))
        if digest is None:
            raise CandidateIntegrationError(
                "configured generated-family policy lacks a digest"
            )
        return digest
    row_digests = {
        digest
        for row in _mapping_sequence(calibration.get("rows"))
        for digest in [_optional_text(row.get("policyDigest"))]
        if digest is not None
    }
    if len(row_digests) > 1:
        raise CandidateIntegrationError(
            "population rows cite conflicting generated-family policy digests"
        )
    return next(iter(row_digests), None)


def _producer_registry(
    analysis: GeneratedFamilyCandidateAnalysis,
) -> ProducerRegistry:
    registry = ProducerRegistry()
    partition_indexes = {
        partition.identifier: index
        for index, partition in enumerate(analysis.partitions)
    }
    for candidate_index, candidate in enumerate(analysis.candidates):
        registration = _candidate_registration(
            candidate,
            candidate_index=candidate_index,
            partition_index=partition_indexes[candidate.partition_id],
            partition=analysis.partitions[partition_indexes[candidate.partition_id]],
        )
        registry = registry.register_producer(registration)
    return registry


def _candidate_registration(
    candidate: GeneratedFamilyCandidate,
    *,
    candidate_index: int,
    partition_index: int,
    partition: Any,
) -> ProducerRegistration:
    candidate_pointer = f"{GENERATED_FAMILY_REPORT_BASE}/candidates/{candidate_index}"
    partition_pointer = f"{GENERATED_FAMILY_REPORT_BASE}/partitions/{partition_index}"
    feature_indexes = {
        feature.identifier: index for index, feature in enumerate(partition.features)
    }
    required_feature_ids = (
        candidate.import_feature_id,
        candidate.lexical_feature_id,
    )
    if any(feature_id not in feature_indexes for feature_id in required_feature_ids):
        raise CandidateIntegrationError(
            f"candidate {candidate.identifier} has a dangling feature reference"
        )
    evidence_refs = (
        candidate_pointer,
        partition_pointer,
        f"{candidate_pointer}/members",
        *(
            f"{partition_pointer}/features/{feature_indexes[feature_id]}"
            for feature_id in required_feature_ids
        ),
    )
    representative = candidate.representatives[0]
    return ProducerRegistration(
        identity=f"{candidate.identifier}.review",
        kind="generated_family_candidate",
        evidence_refs=evidence_refs,
        coverage_ref=CANDIDATE_COLLECTION_ID,
        authority=candidate.authority.conclusion,
        nonclaims=tuple(row.text for row in candidate.nonclaims),
        action=InspectionAction(
            noun="modules",
            filters=(("module", representative.member_id),),
        ),
    )


def _adapt_partition_rows(payload: dict[str, Any]) -> None:
    partitions = payload.get("partitions")
    if not isinstance(partitions, list):
        raise CandidateIntegrationError("candidate partitions are malformed")
    for index, row in enumerate(partitions):
        if not isinstance(row, dict):
            raise CandidateIntegrationError("candidate partition row is malformed")
        pointer = f"{GENERATED_FAMILY_REPORT_BASE}/partitions/{index}"
        row["canonicalRef"] = pointer
        row["coverageRef"] = PARTITION_COLLECTION_ID
        _rewrite_coverage_pointer(row.get("memberCoverage"), f"{pointer}/members")
        _rewrite_coverage_pointer(row.get("featureCoverage"), f"{pointer}/features")


def _adapt_candidate_rows(
    payload: dict[str, Any],
    candidates: tuple[GeneratedFamilyCandidate, ...],
) -> None:
    rows = payload.get("candidates")
    if not isinstance(rows, list) or len(rows) != len(candidates):
        raise CandidateIntegrationError("candidate rows are malformed")
    for index, (row, candidate) in enumerate(zip(rows, candidates)):
        if not isinstance(row, dict):
            raise CandidateIntegrationError("candidate row is malformed")
        pointer = f"{GENERATED_FAMILY_REPORT_BASE}/candidates/{index}"
        row["canonicalRef"] = pointer
        row["coverageRef"] = CANDIDATE_COLLECTION_ID
        row["inspectionAction"] = InspectionAction(
            noun="modules",
            filters=(("module", candidate.representatives[0].member_id),),
        ).to_dict()
        row["memberRefs"] = [
            (
                "#/sections/module_dag/module_metadata/"
                f"{_pointer_token(member.identifier)}"
            )
            for member in candidate.members
        ]
        _rewrite_coverage_pointer(row.get("memberCoverage"), f"{pointer}/members")
        _rewrite_coverage_pointer(
            row.get("representativeCoverage"),
            f"{pointer}/representatives",
        )


def _rewrite_coverage_pointer(raw: Any, pointer: str) -> None:
    if not isinstance(raw, dict):
        raise CandidateIntegrationError("nested candidate coverage is malformed")
    raw["pointer"] = pointer


def _mapping_sequence(raw: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()
    return tuple(row for row in raw if isinstance(row, Mapping))


def _optional_text(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


__all__ = [
    "GENERATED_FAMILY_CANDIDATE_COVERAGE_FIELD",
    "GENERATED_FAMILY_PARTITION_COVERAGE_FIELD",
    "GENERATED_FAMILY_REPORT_BASE",
    "CandidateIntegrationError",
    "GeneratedFamilyCandidateSurface",
    "analyze_generated_family_candidate_surface",
]
