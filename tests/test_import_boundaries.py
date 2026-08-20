from __future__ import annotations

import json
from pathlib import Path

from ladon.analysis.import_boundaries import IMPORT_BOUNDARY_AUTHORITY
from ladon.analysis.module_dag import (
    classify_import_boundaries,
    summarize_module_dag,
)
from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.extraction import parse_lean_module
from ladon.ir import LeanImport, LeanModule

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "scope_join_integrity"
INVENTORY_FINGERPRINT = "sha256:scope-boundary-inventory"
SCOPE_FINGERPRINT = "sha256:scope-boundary-plan"


def fixture_modules() -> dict[str, LeanModule]:
    """Load the portable boundary fixture through the production text scanner."""

    modules = (
        parse_lean_module(FIXTURE_ROOT, path)
        for path in sorted(FIXTURE_ROOT.rglob("*.lean"))
    )
    return {module.name: module for module in modules}


def fixture_expectations() -> dict:
    """Return the tracked target-neutral boundary oracle."""

    return json.loads(
        (FIXTURE_ROOT / "expected-boundaries.json").read_text(
            encoding="utf-8"
        )
    )


def test_import_boundaries_classify_every_portable_fixture_site() -> None:
    inventory = fixture_modules()
    selected = {
        name: inventory[name]
        for name in ("Fixture.Context", "Fixture.Owner")
    }

    summary = summarize_module_dag(
        selected,
        chosen_roots=("Fixture.Owner",),
        full_inventory_modules=inventory,
        full_inventory_fingerprint=INVENTORY_FINGERPRINT,
        scope_source_fingerprint=INVENTORY_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    _assert_fixture_boundary_rows(summary, fixture_expectations())
    _assert_fixture_boundary_coverage(summary)
    _assert_fixture_boundary_determinism(summary, selected, inventory)


def _assert_fixture_boundary_rows(summary: dict, expected: dict) -> None:
    """Check fixture classes, authority, summary counts, and compatibility."""

    assert [
        {
            "line": row["line"],
            "target": row["targetModule"],
            "classification": row["classification"],
        }
        for row in summary["import_boundaries"]
    ] == expected["imports"]
    assert {
        row["targetModule"]: row["authority"]
        for row in summary["import_boundaries"]
    } == {
        row["target"]: expected["authority"]
        for row in expected["imports"]
    }
    assert summary["import_boundary_summary"] == {
        "selected_internal": 1,
        "known_inventory_boundary": 1,
        "external_boundary": 1,
        "missing_internal": 1,
        "unavailable": 0,
    }
    assert [
        row["targetModule"]
        for row in summary["missing_internal_imports"]
    ] == ["Fixture.Absent"]


def _assert_fixture_boundary_coverage(summary: dict) -> None:
    """Check the shared exact-known coverage envelope."""

    coverage = summary["import_boundary_coverage"]
    assert coverage["id"] == "module_dag.import_boundaries"
    assert coverage["pointer"] == "#/sections/module_dag/import_boundaries"
    assert coverage["visible"] == coverage["total"] == 4
    assert coverage["omitted"] == 0
    assert coverage["completeness"] == "complete"
    assert all(
        row["coverageRef"] == coverage["id"]
        for row in summary["import_boundaries"]
    )


def _assert_fixture_boundary_determinism(
    summary: dict,
    selected: dict[str, LeanModule],
    inventory: dict[str, LeanModule],
) -> None:
    """Check identity order is independent of full-inventory iteration order."""

    assert summary == summarize_module_dag(
        selected,
        chosen_roots=("Fixture.Owner",),
        full_inventory_modules=reversed(tuple(inventory)),
        full_inventory_fingerprint=INVENTORY_FINGERPRINT,
        scope_source_fingerprint=INVENTORY_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )


def test_import_boundary_refs_retain_source_scope_and_inventory_evidence() -> None:
    inventory = fixture_modules()
    selected = {"Fixture.Owner": inventory["Fixture.Owner"]}

    result = classify_import_boundaries(
        selected,
        chosen_roots=("Fixture.Owner",),
        full_inventory_modules=inventory,
        full_inventory_fingerprint=INVENTORY_FINGERPRINT,
        scope_source_fingerprint=INVENTORY_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )
    first = result.row_dicts()[0]

    assert first["sourcePath"] == "Fixture/Owner.lean"
    assert first["line"] == 1
    assert first["authority"] == IMPORT_BOUNDARY_AUTHORITY
    assert first["classificationAuthority"] == "ladon_derived"
    assert first["sourceIndexFingerprint"] == INVENTORY_FINGERPRINT
    assert first["scopeFingerprint"] == SCOPE_FINGERPRINT
    assert first["evidenceRefs"] == [
        {
            "type": "source",
            "pointer": "#/sections/module_dag/import_boundaries/0",
            "path": "Fixture/Owner.lean",
            "line": 1,
        },
        {
            "type": "scope_population",
            "pointer": "#/sections/module_dag/analysis_scope",
            "fingerprint": SCOPE_FINGERPRINT,
        },
        {
            "type": "source_index_inventory",
            "pointer": "#/sections/module_dag/source_index",
            "module": "Fixture.Context",
            "fingerprint": INVENTORY_FINGERPRINT,
        },
    ]
    assert "not a Lean resolver" in first["nonclaim"]


def test_inventory_fingerprint_mismatch_fails_membership_rows_closed() -> None:
    inventory = fixture_modules()
    selected = {
        name: inventory[name]
        for name in ("Fixture.Context", "Fixture.Owner")
    }

    summary = summarize_module_dag(
        selected,
        chosen_roots=("Fixture.Owner",),
        full_inventory_modules=inventory,
        full_inventory_fingerprint=INVENTORY_FINGERPRINT,
        scope_source_fingerprint="sha256:stale-scope",
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    by_target = {
        row["targetModule"]: row for row in summary["import_boundaries"]
    }
    assert by_target["Fixture.Context"]["classification"] == (
        "selected_internal"
    )
    for target in (
        "Fixture.Outside",
        "External.Library",
        "Fixture.Absent",
    ):
        assert by_target[target]["classification"] == "unavailable"
        assert by_target[target]["unavailableReason"] == (
            "source_index_fingerprint_mismatch"
        )
    assert summary["missing_internal_imports"] == []
    assert summary["import_boundary_coverage"]["completeness"] == "complete"


def test_partial_selected_import_population_produces_unknown_coverage() -> None:
    inventory = fixture_modules()
    selected = {"Fixture.Owner": inventory["Fixture.Owner"]}
    upstream = CollectionCoverage.unknown(
        identity="selected.imports",
        pointer="#/selected/imports",
        visible=4,
        observed_lower_bound=4,
        completeness="partial",
        population="selected_lexical_import_occurrences",
        scope="owner:Fixture.Owner",
        authority="lexical_text",
        causes=(
            CoverageCause(
                kind="extraction",
                identifier="source_index.source_failed",
                detail="One selected source could not be indexed.",
            ),
        ),
        source_fingerprint=INVENTORY_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    result = classify_import_boundaries(
        selected,
        chosen_roots=("Fixture.Owner",),
        full_inventory_modules=inventory,
        full_inventory_fingerprint=INVENTORY_FINGERPRINT,
        scope_source_fingerprint=INVENTORY_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        selected_import_coverage=upstream,
    )

    assert result.counts()["unavailable"] == 0
    assert result.coverage.visible == 4
    assert result.coverage.observed_lower_bound == 4
    assert result.coverage.total is None
    assert result.coverage.omitted is None
    assert result.coverage.completeness == "partial"
    assert result.coverage.causes == upstream.causes


def test_imports_without_site_rows_receive_deterministic_synthetic_anchors() -> None:
    modules = {
        "Pkg.Owner": LeanModule(
            name="Pkg.Owner",
            path="Pkg/Owner.lean",
            imports=("Pkg.Core", "External.Library"),
        ),
        "Pkg.Core": LeanModule(name="Pkg.Core", path="Pkg/Core.lean"),
    }

    result = classify_import_boundaries(
        modules,
        chosen_roots=("Pkg.Owner",),
        full_inventory_modules=modules,
        full_inventory_fingerprint=INVENTORY_FINGERPRINT,
        scope_source_fingerprint=INVENTORY_FINGERPRINT,
    )

    assert [
        (
            row.target_module,
            row.classification,
            row.line,
            row.import_text,
            row.synthetic,
        )
        for row in result.rows
    ] == [
        ("External.Library", "external_boundary", None, "import External.Library", True),
        ("Pkg.Core", "selected_internal", None, "import Pkg.Core", True),
    ]
    assert [row.site_ordinal for row in result.rows] == [0, 1]


def test_legacy_summary_keeps_missing_import_compatibility_shape() -> None:
    modules = {
        "A.Owner": LeanModule(
            name="A.Owner",
            path="A/Owner.lean",
            imports=("A.Missing", "External.Library"),
            import_sites=(
                LeanImport(
                    module="A.Missing",
                    line=1,
                    text="import A.Missing",
                ),
                LeanImport(
                    module="External.Library",
                    line=2,
                    text="import External.Library",
                ),
            ),
        )
    }

    summary = summarize_module_dag(
        modules,
        chosen_roots=("A.Owner",),
    )

    assert [
        row["targetModule"]
        for row in summary["missing_internal_imports"]
    ] == ["A.Missing"]
    assert {
        row["classification"] for row in summary["import_boundaries"]
    } == {"unavailable"}
    assert summary["import_boundary_coverage"]["completeness"] == "complete"
