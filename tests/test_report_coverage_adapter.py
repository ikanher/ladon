from __future__ import annotations

from pathlib import Path
from typing import Any

from ladon.coverage import CollectionCoverage, CoverageRegistry
from ladon.ir import LeanModule, LeanTextDeclaration
from ladon.report_coverage import (
    DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
    MODULE_DAG_MODULES_COVERAGE,
    PROOF_XRAY_ROWS_COVERAGE,
    REPORT_FINDINGS_COVERAGE,
    REPORT_PACKET_EVIDENCE_COVERAGE,
    REPORT_REVIEW_REGIONS_COVERAGE,
    build_report_coverage,
)
from ladon.source_index_models import (
    SOURCE_FAILURE_DIAGNOSTIC,
    SourceIndex,
    SourceIndexEntry,
)


REPORT_IDS = (
    DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
    MODULE_DAG_MODULES_COVERAGE,
    PROOF_XRAY_ROWS_COVERAGE,
    REPORT_FINDINGS_COVERAGE,
    REPORT_PACKET_EVIDENCE_COVERAGE,
    REPORT_REVIEW_REGIONS_COVERAGE,
)


def _entry(name: str, declarations: int = 0) -> SourceIndexEntry:
    evidence = tuple(
        LeanTextDeclaration(
            name=f"{name}.decl{index}",
            kind="theorem",
            line=index + 1,
            column=1,
            start_offset=index * 10,
            end_offset=index * 10 + 8,
        )
        for index in range(declarations)
    )
    return SourceIndexEntry(
        module=LeanModule(
            name=name,
            path=f"{name.replace('.', '/')}.lean",
            declarations=tuple(row.name for row in evidence),
            declaration_evidence=evidence,
        ),
        content_sha256="a" * 64,
        source_bytes=100,
    )


def _index(
    entries: tuple[SourceIndexEntry, ...],
    *,
    manifest_entries: tuple[SourceIndexEntry, ...] | None = None,
    partial: bool = False,
) -> SourceIndex:
    inventory = entries if manifest_entries is None else manifest_entries
    diagnostics: tuple[dict[str, Any], ...] = ()
    if partial:
        missing = next(row for row in inventory if row not in entries)
        diagnostics = (
            {
                "id": SOURCE_FAILURE_DIAGNOSTIC,
                "module": missing.name,
                "path": missing.path,
                "cause": "parse_error",
                "message": f"{missing.name} could not be indexed",
            },
        )
    return SourceIndex(
        repo_root=Path("/fixture"),
        fingerprint="f" * 64,
        fingerprint_manifest={
            "sources": [
                {
                    "module": entry.name,
                    "path": entry.path,
                    "status": "present",
                    "bytes": entry.source_bytes,
                    "sha256": entry.content_sha256,
                }
                for entry in inventory
            ]
        },
        layout_status="complete",
        source_roots=(),
        entries=entries,
        options={},
        index_status="partial" if partial else "complete",
        diagnostics=diagnostics,
    )


def _complete_status(**counters: dict[str, int]) -> dict[str, dict[str, Any]]:
    return {
        phase: {"status": "complete", "counters": values}
        for phase, values in counters.items()
    }


def _empty_phase_data() -> dict[str, Any]:
    return {
        "module_dag": {"module_count": 0, "module_metadata": {}},
        "declaration_graph": {
            "declaration_count": 0,
            "declarations": [],
        },
        "review_regions": [],
        "packet_evidence": [],
        "proof_xray": {"rows": []},
    }


def _assert_complete_empty(row: CollectionCoverage) -> None:
    assert (
        row.visible,
        row.observed_lower_bound,
        row.total,
        row.omitted,
    ) == (0, 0, 0, 0)
    assert row.total_known is True
    assert row.completeness == "complete"
    assert row.causes == ()
    assert row.scope_fingerprint == "sha256:scope"
    assert row.analysis_fingerprint == "sha256:analysis"


def test_complete_empty_report_collections_are_exact_not_unavailable() -> None:
    registry = build_report_coverage(
        _index(()),
        _complete_status(
            module_dag={},
            declaration_graph={},
            findings={},
            review_regions={},
            packet_evidence={},
            proof_xray={},
        ),
        _empty_phase_data(),
        (),
        scope="fixture",
        scope_fingerprint="sha256:scope",
        analysis_fingerprint="sha256:analysis",
    )

    assert tuple(registry.collections) == REPORT_IDS
    assert all(
        row.pointer.startswith("#/sections/")
        for row in registry.collections.values()
    )
    assert all(row.pointer != "#/entries" for row in registry.collections.values())
    for row in registry.collections.values():
        _assert_complete_empty(row)


def test_owner_counts_preserve_pre_report_caps_exactly() -> None:
    entries = (_entry("Pkg", declarations=4),)
    data = {
        "module_dag": {
            "module_count": 1,
            "module_metadata": {"Pkg": {"path": "Pkg.lean"}},
        },
        "declaration_graph": {
            "declaration_count": 4,
            "declarations": [{"name": "Pkg.first"}, {"name": "Pkg.second"}],
        },
        "review_regions": [{"id": "region-1"}],
        "packet_evidence": [{"profile": "review"}],
    }
    registry = build_report_coverage(
        _index(entries),
        _complete_status(
            module_dag={"modules": 1},
            declaration_graph={"declarations": 4},
            findings={"findings": 5},
            review_regions={"regions": 3},
            packet_evidence={"packet_dirs": 2},
        ),
        data,
        ({"id": "finding-1"}, {"id": "finding-2"}),
        scope="fixture",
    )

    expected = {
        DECLARATION_GRAPH_DECLARATIONS_COVERAGE: (2, 4, 2),
        MODULE_DAG_MODULES_COVERAGE: (1, 1, 0),
        REPORT_FINDINGS_COVERAGE: (2, 5, 3),
        REPORT_PACKET_EVIDENCE_COVERAGE: (1, 2, 1),
        REPORT_REVIEW_REGIONS_COVERAGE: (1, 3, 2),
    }
    for identity, counts in expected.items():
        row = registry.require(identity)
        assert (row.visible, row.total, row.omitted) == counts
        assert row.total_known is True
        assert row.completeness == (
            "complete" if counts[2] == 0 else "partial"
        )
    declaration_cause = registry.require(
        DECLARATION_GRAPH_DECLARATIONS_COVERAGE
    ).causes
    assert declaration_cause[0].identifier.endswith(".owner_cap")
    assert declaration_cause[0].controlling_cap == 2


def _partial_source_registry() -> CoverageRegistry:
    indexed = _entry("Pkg", declarations=1)
    missing = _entry("Pkg.Missing", declarations=3)
    data = {
        "module_dag": {
            "module_count": 1,
            "module_metadata": {"Pkg": {"path": "Pkg.lean"}},
        },
        "declaration_graph": {
            "declaration_count": 1,
            "declarations": [{"name": "Pkg.decl0"}],
        },
        "review_regions": [{"id": "region-1"}],
        "packet_evidence": [],
    }
    return build_report_coverage(
        _index(
            (indexed,),
            manifest_entries=(indexed, missing),
            partial=True,
        ),
        _complete_status(
            module_dag={},
            declaration_graph={},
            findings={},
            review_regions={},
            packet_evidence={},
        ),
        data,
        ({"id": "finding-1"},),
        scope="fixture",
        module_dag_is_full_inventory=True,
    )


def test_partial_source_preserves_known_full_inventory_module_total() -> None:
    registry = _partial_source_registry()
    modules = registry.require(MODULE_DAG_MODULES_COVERAGE)
    assert (modules.visible, modules.total, modules.omitted) == (1, 2, 1)
    assert modules.total_known is True
    assert modules.completeness == "partial"
    assert modules.causes[0].kind == "extraction"


def test_partial_source_leaves_derived_collection_totals_unknown() -> None:
    registry = _partial_source_registry()
    rows = tuple(
        registry.require(identity)
        for identity in (
            DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
            REPORT_FINDINGS_COVERAGE,
            REPORT_REVIEW_REGIONS_COVERAGE,
        )
    )

    assert {row.visible for row in rows} == {1}
    assert all(row.observed_lower_bound >= 1 for row in rows)
    assert {row.total_known for row in rows} == {False}
    assert {row.total for row in rows} == {None}
    assert {row.omitted for row in rows} == {None}
    assert {row.completeness for row in rows} == {"partial"}
    assert all(
        any(cause.kind == "extraction" for cause in row.causes)
        for row in rows
    )


def test_partial_source_does_not_taint_independent_packet_collection() -> None:
    registry = _partial_source_registry()
    packet = registry.require(REPORT_PACKET_EVIDENCE_COVERAGE)
    assert packet.total_known is True
    assert packet.total == 0
    assert packet.completeness == "complete"


def test_partial_source_subset_scope_does_not_adopt_inventory_total() -> None:
    registry = _partial_source_registry()
    indexed = _entry("Pkg", declarations=1)
    missing = _entry("Pkg.Missing", declarations=3)
    subset = build_report_coverage(
        _index(
            (indexed,),
            manifest_entries=(indexed, missing),
            partial=True,
        ),
        _complete_status(
            module_dag={},
            declaration_graph={},
            findings={},
            review_regions={},
            packet_evidence={},
        ),
        {
            "module_dag": {
                "module_count": 1,
                "module_metadata": {"Pkg": {"path": "Pkg.lean"}},
            },
            "declaration_graph": {
                "declaration_count": 1,
                "declarations": [{"name": "Pkg.decl0"}],
            },
            "review_regions": [],
            "packet_evidence": [],
        },
        (),
        scope="owner-slice",
        module_dag_is_full_inventory=False,
    )

    assert registry.require(MODULE_DAG_MODULES_COVERAGE).total == 2
    modules = subset.require(MODULE_DAG_MODULES_COVERAGE)
    assert modules.visible == 1
    assert modules.total_known is False
    assert modules.total is None
    assert modules.omitted is None


def test_partial_or_failed_phase_never_uses_its_observed_count_as_total() -> None:
    entry = _entry("Pkg", declarations=2)
    data = {
        "module_dag": {
            "module_count": 1,
            "module_metadata": {"Pkg": {"path": "Pkg.lean"}},
        },
        "declaration_graph": {
            "declaration_count": 2,
            "declarations": [{"name": "Pkg.decl0"}],
        },
        "review_regions": [],
        "packet_evidence": [],
    }
    statuses = _complete_status(
        module_dag={},
        findings={},
        review_regions={},
        packet_evidence={},
    )
    statuses["declaration_graph"] = {
        "status": "partial",
        "counters": {"declarations": 2},
        "reason": "helper returned one of two batches",
    }
    statuses["review_regions"] = {
        "status": "failed",
        "reason": "region synthesis stopped",
    }

    registry = build_report_coverage(
        _index((entry,)),
        statuses,
        data,
        (),
        scope="fixture",
    )

    declarations = registry.require(
        DECLARATION_GRAPH_DECLARATIONS_COVERAGE
    )
    assert declarations.visible == 1
    assert declarations.observed_lower_bound == 2
    assert declarations.total_known is False
    assert declarations.causes[0].identifier == (
        "declaration_graph.phase_partial"
    )
    regions = registry.require(REPORT_REVIEW_REGIONS_COVERAGE)
    assert regions.total_known is False
    assert regions.completeness == "unavailable"
    assert regions.causes[0].identifier == "review_regions.phase_failed"


def test_missing_source_index_is_unknown_only_for_source_derived_rows() -> None:
    data = _empty_phase_data()
    registry = build_report_coverage(
        None,
        _complete_status(
            module_dag={},
            declaration_graph={},
            findings={},
            review_regions={},
            packet_evidence={},
        ),
        data,
        (),
        scope="legacy-current-analysis",
    )

    for identity in (
        MODULE_DAG_MODULES_COVERAGE,
        DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
        REPORT_FINDINGS_COVERAGE,
        REPORT_REVIEW_REGIONS_COVERAGE,
    ):
        row = registry.require(identity)
        assert row.total_known is False
        assert row.total is None
        assert row.omitted is None
        assert row.completeness == "partial"
        assert row.causes[0].identifier == "coverage.source_index_unavailable"

    packet = registry.require(REPORT_PACKET_EVIDENCE_COVERAGE)
    assert (packet.visible, packet.total, packet.omitted) == (0, 0, 0)
    assert packet.completeness == "complete"


def test_registered_review_region_coverage_joins_upstream_registry() -> None:
    source_fingerprint = "f" * 64
    candidate_coverage = CollectionCoverage.exact(
        identity="generated_family.candidates",
        pointer=(
            "#/sections/module_dag/generated_family_candidates/candidates"
        ),
        visible=2,
        total=2,
        population="generated_family_candidates",
        scope="fixture",
        authority="ladon_derived_heuristic",
        source_fingerprint=source_fingerprint,
    )
    region_coverage = CollectionCoverage.exact(
        identity="report.review_regions.generated_family.fixture.signals",
        pointer="#/sections/review_regions/0/signals",
        visible=2,
        total=2,
        population="generated_family_candidates",
        scope="fixture",
        authority="ladon_derived_heuristic",
        source_fingerprint=source_fingerprint,
    )
    data = _empty_phase_data()
    data["module_dag"].update(
        {
            "generated_family_candidates": {
                "candidates": [{"id": "a"}, {"id": "b"}],
            },
            "generated_family_candidate_coverage": (
                candidate_coverage.to_dict()
            ),
        }
    )
    data["review_regions"] = [
        {
            "kind": "generated_family_candidate_region",
            "signals": [{"id": "a"}, {"id": "b"}],
            "coverageRef": region_coverage.identity,
            "coverage": region_coverage.to_dict(),
            "upstreamCoverageRefs": [candidate_coverage.identity],
        }
    ]

    registry = build_report_coverage(
        _index(()),
        _complete_status(
            module_dag={},
            declaration_graph={},
            findings={},
            review_regions={"regions": 1},
            packet_evidence={},
        ),
        data,
        (),
        scope="fixture",
    )

    assert registry.require(region_coverage.identity) == region_coverage
    assert registry.require(candidate_coverage.identity) == (
        candidate_coverage
    )
