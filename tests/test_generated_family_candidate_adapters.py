from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from ladon.analysis.generated_family_candidate_adapters import (
    CandidateIntegrationError,
    GENERATED_FAMILY_CANDIDATE_COVERAGE_FIELD,
    GENERATED_FAMILY_PARTITION_COVERAGE_FIELD,
    GENERATED_FAMILY_REPORT_BASE,
    analyze_generated_family_candidate_surface,
)
from ladon.analysis.generated_family_candidate_profile import (
    DECLARATION_STEM_VERSION,
    CandidateProfile,
    CandidateRatio,
)
from ladon.ir import LeanCommandSkeleton, LeanModule, LeanTextDeclaration
from ladon.render_generated_family_candidates import (
    generated_family_candidate_lines,
)
from ladon.source_index_models import (
    SOURCE_FAILURE_DIAGNOSTIC,
    SourceIndex,
    SourceIndexEntry,
)


SOURCE_FINGERPRINT = "f" * 64
SCOPE_FINGERPRINT = "s" * 64
POLICY_DIGEST = "sha256:fixture-policy"


def _declaration(index: int) -> LeanTextDeclaration:
    name = f"sharedRow{index}"
    return LeanTextDeclaration(
        name=name,
        kind="theorem",
        line=2,
        column=9,
        start_offset=20,
        end_offset=20 + len(name),
        identifier=f"declaration:{index}",
        candidate_name=f"Neutral.Rows.{name}",
        candidate_status="lexical_candidate",
    )


def _module(
    name: str,
    *,
    imports: tuple[str, ...] = (),
    declaration: LeanTextDeclaration | None = None,
) -> LeanModule:
    evidence = (declaration,) if declaration is not None else ()
    return LeanModule(
        name=name,
        path=f"{name.replace('.', '/')}.lean",
        imports=imports,
        declarations=tuple(row.name for row in evidence),
        declaration_evidence=evidence,
    )


def _entry(module: LeanModule) -> SourceIndexEntry:
    digest = hashlib.sha256(module.name.encode("utf-8")).hexdigest()
    return SourceIndexEntry(
        module=module,
        content_sha256=digest,
        source_bytes=100,
    )


def _fixture_entries() -> tuple[SourceIndexEntry, ...]:
    modules = [_module("Neutral.Data")]
    modules.extend(
        _module(
            f"Neutral.Rows.Cell{index}",
            imports=("Neutral.Data",),
            declaration=_declaration(index),
        )
        for index in range(5)
    )
    modules.append(_module("Neutral.Unselected.Cell9"))
    return tuple(_entry(module) for module in modules)


def _manifest(
    entries: tuple[SourceIndexEntry, ...],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "sources": [
            {
                "module": entry.name,
                "path": entry.path,
                "status": "present",
                "bytes": entry.source_bytes,
                "sha256": entry.content_sha256,
            }
            for entry in entries
        ]
    }


def _source_index(
    *,
    reverse: bool = False,
    missing: str | None = None,
) -> SourceIndex:
    all_entries = _fixture_entries()
    visible = tuple(entry for entry in all_entries if entry.name != missing)
    if reverse:
        visible = tuple(reversed(visible))
    diagnostics = (
        (
            {
                "id": SOURCE_FAILURE_DIAGNOSTIC,
                "module": missing,
                "path": f"{missing.replace('.', '/')}.lean",
                "cause": "parse_error",
                "detail": "fixture failure",
            },
        )
        if missing is not None
        else ()
    )
    return SourceIndex(
        repo_root=Path("/fixture"),
        fingerprint=SOURCE_FINGERPRINT,
        fingerprint_manifest=_manifest(all_entries),
        layout_status="complete",
        source_roots=(),
        entries=visible,
        options={},
        index_status="partial" if missing is not None else "complete",
        diagnostics=diagnostics,
    )


def _source_index_with_bad_skeleton(
    *,
    status: str = "observed",
    authority: str = "lexical_text",
) -> SourceIndex:
    entries = list(_fixture_entries())
    target = entries[5]
    row = LeanCommandSkeleton(
        identifier="ladon.command_skeleton.fixture",
        module=target.name,
        path=target.path,
        value=f"sha256:{'a' * 64}",
        token_count=4,
        normalization_version="command-skeleton-v1",
        status=status,
        authority=authority,
    )
    entries[5] = replace(
        target,
        module=replace(target.module, command_skeletons=(row,)),
    )
    frozen = tuple(entries)
    return SourceIndex(
        repo_root=Path("/fixture"),
        fingerprint=SOURCE_FINGERPRINT,
        fingerprint_manifest=_manifest(frozen),
        layout_status="complete",
        source_roots=(),
        entries=frozen,
        options={},
    )


def _module_dag(
    *,
    reverse: bool = False,
    include_import_target: bool = True,
) -> dict[str, Any]:
    selected = [
        *(f"Neutral.Rows.Cell{index}" for index in range(5)),
    ]
    if include_import_target:
        selected.insert(0, "Neutral.Data")
    if reverse:
        selected.reverse()
    metadata = {
        name: {
            "path": f"{name.replace('.', '/')}.lean",
            "population": (
                "project_generated" if name == "Neutral.Rows.Cell2" else "target_owned"
            ),
        }
        for name in selected
    }
    return {
        "module_metadata": metadata,
        "analysis_scope": {
            "fingerprint": SCOPE_FINGERPRINT,
            "sourceIndexFingerprint": SOURCE_FINGERPRINT,
            "completeness": "complete",
            "truncated": False,
        },
        "population_calibration": {
            "policy": {"policyDigest": POLICY_DIGEST},
            "rows": [],
        },
    }


def _resolve_pointer(document: Any, pointer: str) -> Any:
    assert pointer.startswith("#/")
    selected = document
    for raw_token in pointer[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        selected = (
            selected[int(token)] if isinstance(selected, list) else selected[token]
        )
    return selected


def _cell_partition(surface):
    return next(
        row
        for row in surface.analysis.partitions
        if row.sequence.basename_prefix == "Cell"
    )


def _candidate_member(partition, identity: str):
    return next(
        row for row in partition.members if row.identifier == identity
    )


def _assert_complete_internal_import_evidence(partition) -> None:
    assert all(
        member.direct_internal_imports == ("Neutral.Data",)
        for member in partition.members
    )
    assert any(
        feature.kind == "direct_internal_import"
        and feature.value == "Neutral.Data"
        and feature.member_count == 5
        for feature in partition.features
    )


def _assert_top_level_candidate_coverage(
    surface: Any,
    fields: dict[str, Any],
) -> None:
    assert (
        surface.candidate_coverage.pointer
        == f"{GENERATED_FAMILY_REPORT_BASE}/candidates"
    )
    assert (
        surface.partition_coverage.pointer
        == f"{GENERATED_FAMILY_REPORT_BASE}/partitions"
    )
    assert {row.identity for row in surface.coverage_rows()} == {
        "generated_family.candidates",
        "generated_family.numeric_partitions",
    }
    assert (
        fields[GENERATED_FAMILY_CANDIDATE_COVERAGE_FIELD]["id"]
        == "generated_family.candidates"
    )
    assert (
        fields[GENERATED_FAMILY_PARTITION_COVERAGE_FIELD]["id"]
        == "generated_family.numeric_partitions"
    )


def _assert_candidate_pointers(
    report: dict[str, Any],
    candidate: dict[str, Any],
) -> None:
    assert _resolve_pointer(report, candidate["canonicalRef"]) == candidate
    assert (
        _resolve_pointer(
            report,
            candidate["memberCoverage"]["pointer"],
        )
        == candidate["members"]
    )
    assert all(
        _resolve_pointer(report, pointer)["path"].endswith(".lean")
        for pointer in candidate["memberRefs"]
    )


def _assert_candidate_registration(
    report: dict[str, Any],
    registration: dict[str, Any],
) -> None:
    assert registration["kind"] == "generated_family_candidate"
    assert registration["coverageRef"] == "generated_family.candidates"
    assert registration["authority"] == "ladon_derived_heuristic"
    assert len(registration["nonclaims"]) == 6
    assert registration["inspectionAction"] == {
        "command": "ladon",
        "arguments": [
            "inspect",
            "modules",
            "--filter",
            "module=Neutral.Rows.Cell0",
        ],
    }
    assert all(
        _resolve_pointer(report, pointer) is not None
        for pointer in registration["evidenceRefs"]
    )
    assert "signals" not in registration
    assert "title" not in registration


def test_adapter_joins_selected_dag_to_canonical_source_evidence() -> None:
    dag = _module_dag()
    original = deepcopy(dag)

    surface = analyze_generated_family_candidate_surface(
        dag,
        _source_index(),
    )

    assert dag == original
    assert len(surface.analysis.candidates) == 1
    candidate = surface.analysis.candidates[0]
    assert [member.identifier for member in candidate.members] == [
        f"Neutral.Rows.Cell{index}" for index in range(5)
    ]
    assert [member.population for member in candidate.members] == [
        "target_owned",
        "target_owned",
        "project_generated",
        "target_owned",
        "target_owned",
    ]
    assert candidate.source_fingerprint == SOURCE_FINGERPRINT
    assert candidate.scope_fingerprint == SCOPE_FINGERPRINT
    assert candidate.policy_digest == POLICY_DIGEST
    assert all(member.content_sha256 for member in candidate.members)
    assert "Neutral.Unselected.Cell9" not in {
        member.identifier
        for partition in surface.analysis.partitions
        for member in partition.members
    }


def test_adapter_uses_full_inventory_for_internal_import_membership() -> None:
    surface = analyze_generated_family_candidate_surface(
        _module_dag(include_import_target=False),
        _source_index(),
    )

    assert len(surface.analysis.candidates) == 1
    candidate = surface.analysis.candidates[0]
    assert all(
        member.direct_internal_imports == ("Neutral.Data",)
        for member in candidate.members
    )
    assert "Neutral.Data" not in {
        member.identifier
        for partition in surface.analysis.partitions
        for member in partition.members
    }
    assert surface.input_summary["selectedModuleCount"] == 5
    assert surface.input_summary["internalInventoryModuleCount"] == 7
    assert surface.input_summary["internalInventoryFingerprint"] == (
        surface.analysis.internal_inventory_fingerprint
    )


def test_report_adapter_exposes_resolvable_coverage_and_registration() -> None:
    dag = _module_dag()
    surface = analyze_generated_family_candidate_surface(
        dag,
        _source_index(),
    )
    fields = surface.to_module_dag_fields()
    dag.update(fields)
    payload = fields["generated_family_candidates"]
    report = {"sections": {"module_dag": dag}}

    _assert_top_level_candidate_coverage(surface, fields)
    candidate = payload["candidates"][0]
    _assert_candidate_pointers(report, candidate)
    registration = next(iter(payload["producerRegistry"]["producers"].values()))
    _assert_candidate_registration(report, registration)


def test_incomplete_selected_source_is_unknown_not_observed_negative() -> None:
    surface = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index(missing="Neutral.Rows.Cell4"),
    )

    assert surface.analysis.candidates == ()
    partition = next(
        row
        for row in surface.analysis.partitions
        if row.sequence.basename_prefix == "Cell"
    )
    assert partition.evaluation_status == "unavailable"
    assert surface.candidate_coverage.total_known is False
    assert surface.candidate_coverage.total is None
    assert surface.input_summary["complete"] is False
    assert surface.input_summary["missingSelectedModules"] == ["Neutral.Rows.Cell4"]


def test_unreadable_manifest_import_target_remains_internal_evidence() -> None:
    surface = analyze_generated_family_candidate_surface(
        _module_dag(include_import_target=False),
        _source_index(missing="Neutral.Data"),
    )
    partition = next(
        row
        for row in surface.analysis.partitions
        if row.sequence.basename_prefix == "Cell"
    )

    assert partition.evaluation_status == "match"
    assert len(surface.analysis.candidates) == 1
    _assert_complete_internal_import_evidence(partition)
    assert surface.input_summary["internalInventoryModuleCount"] == 7
    assert surface.input_summary["selectedScopeComplete"] is True
    assert surface.input_summary["complete"] is False
    assert surface.candidate_coverage.total_known is False
    assert partition.member_coverage.total_known is True


def test_failed_unselected_source_does_not_poison_complete_partition() -> None:
    surface = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index(missing="Neutral.Unselected.Cell9"),
    )
    partition = _cell_partition(surface)

    assert partition.evaluation_status == "match"
    assert len(surface.analysis.candidates) == 1
    assert surface.input_summary["missingSelectedModuleCount"] == 0
    assert surface.input_summary["selectedInputsComplete"] is True
    assert surface.input_summary["inventoryComplete"] is False
    assert surface.candidate_coverage.total_known is False
    assert surface.partition_coverage.total_known is False
    assert partition.member_coverage.total_known is True


@pytest.mark.parametrize(
    ("status", "authority"),
    [
        ("unavailable", "lexical_text"),
        ("observed", "report_metadata"),
    ],
)
def test_unusable_command_skeleton_row_makes_member_lexically_incomplete(
    status: str,
    authority: str,
) -> None:
    baseline = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index(),
    )
    surface = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index_with_bad_skeleton(
            status=status,
            authority=authority,
        ),
    )
    partition = _cell_partition(surface)
    bad_member = _candidate_member(partition, "Neutral.Rows.Cell4")

    assert surface.analysis.candidates == ()
    assert partition.evaluation_status == "unavailable"
    assert bad_member.lexical_complete is False
    assert surface.input_summary["complete"] is False
    assert surface.input_summary["incompleteCommandSkeletonModules"] == [
        "Neutral.Rows.Cell4"
    ]
    assert (
        surface.analysis.analysis_fingerprint != baseline.analysis.analysis_fingerprint
    )


def test_declaration_only_profile_does_not_require_command_skeleton_rows() -> None:
    profile = CandidateProfile(
        profile_version="declaration-only-numbered-family-v1",
        minimum_members=4,
        minimum_density=CandidateRatio(4, 5),
        direct_import_coverage=CandidateRatio(4, 5),
        lexical_coverage=CandidateRatio(4, 5),
        lexical_features=(DECLARATION_STEM_VERSION,),
        representative_limit=12,
    )

    surface = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index_with_bad_skeleton(status="unavailable"),
        profile=profile,
    )

    assert len(surface.analysis.candidates) == 1
    assert surface.input_summary["commandSkeletonRequired"] is False
    assert surface.input_summary["complete"] is True
    assert surface.input_summary["incompleteCommandSkeletonModules"] == [
        "Neutral.Rows.Cell4"
    ]


def test_adapter_is_order_deterministic_and_checks_join_identity() -> None:
    first = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index(),
    )
    second = analyze_generated_family_candidate_surface(
        _module_dag(reverse=True),
        _source_index(reverse=True),
    )

    assert first.to_dict() == second.to_dict()

    stale = _module_dag()
    stale["analysis_scope"]["sourceIndexFingerprint"] = "0" * 64
    with pytest.raises(CandidateIntegrationError, match="fingerprints"):
        analyze_generated_family_candidate_surface(stale, _source_index())


def test_candidate_renderer_is_bounded_and_uses_population_not_authorship() -> None:
    surface = analyze_generated_family_candidate_surface(
        _module_dag(),
        _source_index(),
    )
    lines = generated_family_candidate_lines(
        {"generated_family_candidates": surface.to_dict()}
    )
    text = "\n".join(lines)

    assert "Generated-Looking Family Candidates (Advisory)" in text
    assert "common-import=5/5:passed" in text
    assert "common-lexical=5/5:passed" in text
    assert "project_generated=1" in text
    assert "target_owned=4" in text
    assert "handwritten" not in text.lower()
