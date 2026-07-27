from __future__ import annotations

import json
from pathlib import Path

from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text
from ladon.render_v3 import render_report_v3_text
from ladon.report_v3 import build_report_v3


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "scope_join_integrity"


def expected_boundaries() -> dict:
    return json.loads(
        (FIXTURE_ROOT / "expected-boundaries.json").read_text(encoding="utf-8")
    )


def test_portable_scope_boundary_fixture_classifies_every_import() -> None:
    expected = expected_boundaries()
    scope = expected["scope"]
    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root=scope["root"],
            analysis_scope=scope["kind"],
            max_context_modules=scope["maxContextModules"],
            source_cache_enabled=False,
        )
    )
    rows = result.module_dag["import_boundaries"]

    assert_import_boundaries(rows, expected)
    assert_missing_internal_import(result.module_dag)
    assert_boundary_membership(result.module_dag, rows)


def assert_import_boundaries(rows: list[dict], expected: dict) -> None:
    """Check exact import classifications and shared lexical authority."""

    actual = [
        {
            "line": row["line"],
            "target": row["targetModule"],
            "classification": row["classification"],
        }
        for row in rows
    ]
    assert actual == expected["imports"]
    assert {row["authority"] for row in rows} == {expected["authority"]}


def assert_missing_internal_import(dag: dict) -> None:
    """Check the conventional-path diagnostic and its explicit nonclaim."""

    assert dag["missing_internal_imports"] == [
        {
            "sourceModule": "Fixture.Owner",
            "sourcePath": "Fixture/Owner.lean",
            "targetModule": "Fixture.Absent",
            "line": 4,
            "importText": "import Fixture.Absent",
            "authority": "lexical_text",
            "nonclaim": (
                "Missing conventional source-path evidence only; not a Lean "
                "resolver or compilation diagnostic."
            ),
        }
    ]


def assert_boundary_membership(dag: dict, rows: list[dict]) -> None:
    """Check coverage, inventory membership, and ordinary inspection routes."""

    coverage = dag["import_boundary_coverage"]
    assert (
        coverage["visible"],
        coverage["total"],
        coverage["omitted"],
        coverage["completeness"],
    ) == (4, 4, 0, "complete")
    membership = dag["source_index"]["boundaryMembershipEvidence"]
    assert {row["module"]: row["present"] for row in membership} == {
        "External.Library": False,
        "Fixture.Absent": False,
        "Fixture.Context": True,
        "Fixture.Outside": True,
    }
    assert_boundary_inspection_actions(rows)


def assert_boundary_inspection_actions(rows: list[dict]) -> None:
    """Check every boundary points back into inventory evidence."""

    for row in rows:
        assert row["inspectionAction"]["arguments"][:2] == [
            "inspect",
            "imports",
        ]
        inventory_ref = next(
            ref
            for ref in row["evidenceRefs"]
            if ref["type"] == "source_index_inventory"
        )
        assert inventory_ref["pointer"].startswith(
            "#/sections/module_dag/source_index/boundaryMembershipEvidence/"
        )


def test_boundary_report_coverage_uses_same_snapshot_authority() -> None:
    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Fixture.Owner",
            analysis_scope="owner",
            max_context_modules=1,
            source_cache_enabled=False,
        )
    )
    model = result.to_report_model()
    snapshot = model.snapshot
    coverage = model.coverage.require("module_dag.import_boundaries")

    assert snapshot is not None
    assert coverage.source_fingerprint == snapshot.source_index_fingerprint
    assert coverage.scope_fingerprint == snapshot.configuration["scopeFingerprint"]


def test_inventory_pipeline_is_rootless_without_navigation_request() -> None:
    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            analysis_scope="inventory",
            source_cache_enabled=False,
        )
    )

    assert result.module_dag["module_count"] == 3
    assert result.module_dag["root_reachability"] == {
        "status": "not_applicable",
        "reason": "inventory scope has no explicit navigation root",
        "roots": [],
        "population": "inventory_module_population",
        "coverageRef": "module_dag.modules",
        "authority": "module_import_graph",
        "nonclaim": (
            "Root-relative reachability is a navigation view over the selected "
            "module graph, not mathematical relevance or Lean elaboration."
        ),
    }
    assert result.module_dag["root_direct_import_closures"] == []
    assert "source_modules_not_reachable_from_chosen_roots_count" not in (
        result.module_dag
    )
    assert_rootless_report_contract(result)


def assert_rootless_report_contract(result) -> None:
    """Check metadata and both text projections preserve rootless semantics."""

    model = result.to_report_model()
    metadata = model.metadata
    assert metadata.analysis_root == ""
    assert metadata.analysis_root_module == ""
    assert metadata.report_anchor == str(result.discovery.report_anchor_file)
    assert (
        metadata.report_anchor_module
        == result.discovery.report_anchor_module
    )
    v2_text = render_text(model)
    v3_text = render_report_v3_text(
        build_report_v3(model, projection="full")
    )
    assert "Analysis root:" not in v2_text
    assert "Analysis root:" not in v3_text
    expected_anchor = f"Report anchor: {metadata.report_anchor_module}"
    assert expected_anchor in v2_text
    assert expected_anchor in v3_text


def test_inventory_navigation_root_is_an_auxiliary_view_only() -> None:
    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Fixture.Owner",
            analysis_scope="inventory",
            source_cache_enabled=False,
        )
    )

    scope = result.module_dag["analysis_scope"]
    assert scope["primaryPopulation"]["selectedCount"] == 3
    assert scope["navigationRoots"]["resolved"] == ["Fixture.Owner"]
    assert result.module_dag["root_reachability"]["status"] == "auxiliary"
    assert result.module_dag["root_reachability"]["roots"] == ["Fixture.Owner"]
    metadata = result.to_report_model().metadata
    assert metadata.analysis_root_module == "Fixture.Owner"
    assert metadata.analysis_root.endswith("Fixture/Owner.lean")
    assert "Navigation root: Fixture.Owner" in render_text(
        result.to_report_model()
    )


def test_unreadable_manifest_module_remains_known_inventory_boundary(
    tmp_path: Path,
) -> None:
    package = tmp_path / "Pkg"
    package.mkdir()
    (package / "Owner.lean").write_text(
        "import Pkg.Unreadable\n\ndef owner : Nat := 1\n",
        encoding="utf-8",
    )
    (package / "Unreadable.lean").write_bytes(b"\xff\xfe")

    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg.Owner",
            analysis_scope="owner",
            source_cache_enabled=False,
        )
    )
    dag = result.module_dag

    assert dag["source_index"]["status"] == "partial"
    assert dag["missing_internal_imports"] == []
    assert dag["import_boundaries"][0]["classification"] == ("known_inventory_boundary")
    membership = dag["source_index"]["boundaryMembershipEvidence"][0]
    assert {
        "module": membership["module"],
        "present": membership["present"],
        "path": membership["path"],
        "indexEntryStatus": membership["indexEntryStatus"],
        "authority": membership["authority"],
    } == {
        "module": "Pkg.Unreadable",
        "present": True,
        "path": "Pkg/Unreadable.lean",
        "indexEntryStatus": "unavailable",
        "authority": "source_index_manifest",
    }
    inventory_ref = next(
        row
        for row in dag["import_boundaries"][0]["evidenceRefs"]
        if row["type"] == "source_index_inventory"
    )
    assert inventory_ref["present"] is True
    assert inventory_ref["indexEntryStatus"] == "unavailable"
