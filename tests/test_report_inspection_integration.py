from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from ladon.cli import main
from ladon.inspection_adapters import load_inspection_dataset
from ladon.finding_evidence import resolve_local_json_pointer
from ladon.inspection_models import (
    INSPECTION_NOUNS,
    InspectionCompatibilityError,
    InspectionPage,
)
from ladon.inspection_query import inspect_dataset
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_v3 import build_report_v3


def audit_resource_report(
    tmp_path: Path,
    *,
    projection: str = "full",
    review_item_limit: int = 100,
) -> tuple[Path, dict[str, Any]]:
    """Build a full report containing reviewable and navigation-only settings."""

    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "Audit.lean").write_text(
        """\
import Mathlib
#check Nat
set_option maxHeartbeats 0 in
set_option maxRecDepth 100 in
theorem audited : True := by trivial
""",
        encoding="utf-8",
    )
    model = run_pipeline(
        RunContext(
            repo_root=repository,
            requested_root="Audit.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    payload = build_report_v3(
        model,
        projection=projection,
        review_item_limit=review_item_limit,
    ).to_dict()
    report = tmp_path / "report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return report, payload


def multi_surface_review_report(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Build a tiny projection whose owner rows require route reconciliation."""

    repository = tmp_path / "multi-repository"
    repository.mkdir()
    (repository / "Root.lean").write_text(
        "import A\nimport B\ntheorem root : True := by trivial\n",
        encoding="utf-8",
    )
    for module, subject in (("A", "Nat"), ("B", "Bool")):
        (repository / f"{module}.lean").write_text(
            (
                f"#check {subject}\n"
                "set_option maxHeartbeats 0 in\n"
                f"theorem {module.lower()} : True := by trivial\n"
            ),
            encoding="utf-8",
        )
    model = run_pipeline(
        RunContext(
            repo_root=repository,
            requested_root="Root.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    payload = build_report_v3(
        model,
        projection="review",
        review_item_limit=1,
    ).to_dict()
    report = tmp_path / "multi-report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return report, payload


def split_surface_review_report(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Build a tiny projection with disjoint audit and resource owners."""

    repository = tmp_path / "split-repository"
    repository.mkdir()
    (repository / "Root.lean").write_text(
        "import A\nimport Z\n",
        encoding="utf-8",
    )
    (repository / "A.lean").write_text(
        "set_option maxHeartbeats 0\n",
        encoding="utf-8",
    )
    (repository / "Z.lean").write_text(
        "#check Nat\n",
        encoding="utf-8",
    )
    model = run_pipeline(
        RunContext(
            repo_root=repository,
            requested_root="Root.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    payload = build_report_v3(
        model,
        projection="review",
        review_item_limit=1,
    ).to_dict()
    report = tmp_path / "split-report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return report, payload


def declaration_integrity_report(
    tmp_path: Path,
) -> tuple[Path, dict[str, Any]]:
    """Build every declaration-integrity inspection route."""

    repository = tmp_path / "integrity-repository"
    repository.mkdir()
    shape_names = (
        "amber",
        "birch",
        "cedar",
        "dahlia",
        "elm",
        "fir",
        "ginger",
        "hazel",
        "iris",
        "juniper",
        "kestrel",
        "lilac",
        "maple",
        "nettle",
    )
    shape_modules = tuple(f"Shape{index}" for index in range(len(shape_names)))
    (repository / "Root.lean").write_text(
        "\n".join(f"import {module}" for module in ("A", "B", *shape_modules)) + "\n",
        encoding="utf-8",
    )
    duplicate = "namespace Shared\ntheorem value : True := by trivial\nend Shared\n"
    for module in ("A", "B"):
        (repository / f"{module}.lean").write_text(
            duplicate,
            encoding="utf-8",
        )
    for module, declaration in zip(shape_modules, shape_names):
        (repository / f"{module}.lean").write_text(
            f"theorem {declaration} : True := by trivial\n",
            encoding="utf-8",
        )
    model = run_pipeline(
        RunContext(
            repo_root=repository,
            requested_root="Root.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    payload = build_report_v3(model, projection="full").to_dict()
    report = tmp_path / "integrity-report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    return report, payload


def inspection_page(
    report: Path,
    noun: str,
    *,
    identifier: str | None = None,
) -> InspectionPage:
    """Inspect one report-backed noun through the public adapter boundary."""

    return inspect_dataset(
        load_inspection_dataset(
            report,
            noun,
            artifact_kind="report",
        ),
        identifier=identifier,
    )


def action_payload(
    report: Path,
    action: Mapping[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> dict[str, Any]:
    """Execute one report-owned inspection template through the CLI."""

    assert action.get("command") == "ladon"
    arguments = action.get("arguments")
    assert isinstance(arguments, list)
    assert arguments[:1] == ["inspect"]
    status = main(
        [
            *arguments,
            "--report",
            str(report),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    assert status == 0
    assert captured.err == ""
    return json.loads(captured.out)


def test_report_inspection_classifies_coverage_for_every_noun(
    tmp_path: Path,
) -> None:
    report, _ = audit_resource_report(tmp_path)

    coverage_ids = {
        noun: load_inspection_dataset(
            report,
            noun,
            artifact_kind="report",
        ).coverage["id"]
        for noun in INSPECTION_NOUNS
    }

    assert coverage_ids == {
        "modules": "module_dag.modules",
        "declarations": "module_dag.text_declarations",
        "imports": "module_dag.import_boundaries",
        "audits": "module_dag.audit_commands",
        "options": "module_dag.inspection_options",
        "resources": "module_dag.resource_directives",
        "proof-mechanisms": "module_dag.inspection_proof_mechanisms",
    }


def test_report_retains_option_navigation_rows(
    tmp_path: Path,
) -> None:
    report, payload = audit_resource_report(tmp_path)
    option_page = inspection_page(report, "options").to_dict()

    assert option_page["diagnostics"] == []
    assert option_page["coverage"]["collection"]["totalKnown"] is True
    assert option_page["coverage"]["collection"]["total"] == 2
    assert {row["fields"]["option"] for row in option_page["rows"]} == {
        "maxHeartbeats",
        "maxRecDepth",
    }
    assert_exact_navigation_rows(payload, option_page)


def test_report_retains_proof_navigation_rows(
    tmp_path: Path,
) -> None:
    report, payload = audit_resource_report(tmp_path)
    mechanism_page = inspection_page(report, "proof-mechanisms").to_dict()

    assert mechanism_page["diagnostics"] == []
    assert mechanism_page["coverage"]["collection"]["totalKnown"] is True
    assert {row["fields"]["mechanism"] for row in mechanism_page["rows"]} == {"trivial"}
    assert_exact_navigation_rows(payload, mechanism_page)


def assert_exact_navigation_rows(
    payload: Mapping[str, Any],
    page: Mapping[str, Any],
) -> None:
    """Require every navigation projection to retain its exact source owner."""

    for row in page["rows"]:
        assert resolve_local_json_pointer(payload, row["canonicalRef"])
        assert row["sourceAnchor"]["status"] == "exact"
        assert row["authority"] == "lexical_text"


def test_every_report_inspection_row_has_registered_exact_coverage(
    tmp_path: Path,
) -> None:
    report, payload = audit_resource_report(tmp_path)
    coverage_ids = set(payload["coverage"]["collections"])

    for noun in INSPECTION_NOUNS:
        dataset = load_inspection_dataset(
            report,
            noun,
            artifact_kind="report",
        )
        assert dataset.unavailable_reason is None
        assert dataset.coverage["visible"] == len(dataset.rows)
        assert {row.coverage_ref for row in dataset.rows} <= coverage_ids
        for row in dataset.rows:
            assert resolve_local_json_pointer(payload, row.canonical_ref)


def test_tiny_review_projection_keeps_navigation_nouns_and_exact_ranges(
    tmp_path: Path,
) -> None:
    report, payload = audit_resource_report(
        tmp_path,
        projection="review",
        review_item_limit=1,
    )

    for noun in ("options", "proof-mechanisms"):
        page = inspection_page(report, noun).to_dict()
        assert page["diagnostics"] == []
        assert page["rows"]
        for row in page["rows"]:
            owner = resolve_local_json_pointer(payload, row["canonicalRef"])
            source_range = owner["sourceRange"]
            assert set(source_range) == {"start", "end"}
            assert set(source_range["start"]) == {"line", "column", "offset"}
            assert set(source_range["end"]) == {"line", "column", "offset"}
            assert row["sourceAnchor"]["status"] == "exact"


def test_review_projection_preserves_each_proof_mechanism_class(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "proof-repository"
    repository.mkdir()
    (repository / "Proof.lean").write_text(
        """\
@[simp] theorem first : True := by
  simp
theorem second : True := by
  exact True.intro
""",
        encoding="utf-8",
    )
    model = run_pipeline(
        RunContext(
            repo_root=repository,
            requested_root="Proof.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    payload = build_report_v3(
        model,
        projection="review",
        review_item_limit=1,
    ).to_dict()
    report = tmp_path / "proof-report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")

    rows = load_inspection_dataset(
        report,
        "proof-mechanisms",
        artifact_kind="report",
    ).rows

    assert {
        (row.fields["kind"], row.fields["mechanism"]) for row in rows
    } == {
        ("attribute", "simp"),
        ("tactic-token", "exact"),
        ("tactic-token", "simp"),
    }


def test_report_resources_keep_finite_and_registered_unlimited_rows(
    tmp_path: Path,
) -> None:
    report, _ = audit_resource_report(tmp_path)

    audit_page = inspection_page(report, "audits").to_dict()
    resource_page = inspection_page(report, "resources").to_dict()

    assert audit_page["coverage"]["collection"]["total"] == 1
    assert resource_page["coverage"]["collection"]["totalKnown"] is True
    assert resource_page["coverage"]["collection"]["total"] == 2
    assert resource_page["coverage"]["collection"]["visible"] == 2
    assert {row["fields"]["meaning"] for row in resource_page["rows"]} == {
        "finite",
        "unlimited",
    }
    assert {row["fields"]["pressure"] for row in resource_page["rows"]} == {
        "navigation_only",
        "unlimited",
    }
    assert all(
        row["coverageRef"] == "module_dag.audit_commands" for row in audit_page["rows"]
    )
    assert all(
        row["coverageRef"] == "module_dag.resource_directives"
        for row in resource_page["rows"]
    )


def test_report_audit_inspection_survives_suppressed_registration(
    tmp_path: Path,
) -> None:
    report, payload = audit_resource_report(tmp_path)
    dag = payload["sections"]["module_dag"]
    dag["auditProducerRegistrations"]["producers"] = {}
    report.write_text(json.dumps(payload), encoding="utf-8")

    page = inspect_dataset(
        load_inspection_dataset(
            report,
            "audits",
            artifact_kind="report",
        )
    ).to_dict()

    assert page["coverage"]["collection"]["id"] == "module_dag.audit_commands"
    assert page["coverage"]["collection"]["completeness"] == "complete"
    assert [row["fields"]["subject"] for row in page["rows"]] == ["Nat"]
    assert page["rows"][0]["id"].startswith("ladon.audit.")


def test_report_owned_review_actions_resolve_inspection_rows(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report, payload = audit_resource_report(tmp_path)
    selected_kinds = {"audit_surface_region", "option_resource_region"}
    regions = [
        row
        for row in payload["sections"]["review_regions"]
        if row["kind"] in selected_kinds
    ]
    coverage_ids = set(payload["coverage"]["collections"])

    assert {row["kind"] for row in regions} == selected_kinds
    for region in regions:
        assert action_payload(
            report,
            region["inspectionAction"],
            capsys,
        )["rows"]
        for signal in region["signals"]:
            assert signal["coverageRef"] in coverage_ids
            action = signal["inspectionAction"]
            selected = action_payload(report, action, capsys)
            assert [row["id"] for row in selected["rows"]] == [action["arguments"][3]]


def test_declaration_integrity_actions_resolve_complete_group_members(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report, payload = declaration_integrity_report(tmp_path)
    integrity = payload["sections"]["module_dag"]["declaration_integrity"]
    collections = (
        ("collisionCandidates", "declarations", 2),
        ("exactBlockDuplicateCandidates", "declarations", 2),
        ("exactFileDuplicateCandidates", "modules", 2),
        ("sourceShapeSimilarityCandidates", "declarations", 16),
    )

    for collection, noun, expected_members in collections:
        assert_integrity_group_action(
            report,
            integrity[collection][0],
            noun=noun,
            expected_members=expected_members,
            capsys=capsys,
        )

    shape_group = integrity["sourceShapeSimilarityCandidates"][0]
    assert shape_group["memberCoverage"]["visible"] == 12
    assert len(shape_group["representativeMembers"]) == 12
    assert len(shape_group["canonicalMemberRefs"]) == 16

    producer = next(iter(integrity["producerRegistrations"]["producers"].values()))
    selected = action_payload(
        report,
        producer["inspectionAction"],
        capsys,
    )
    assert len(selected["rows"]) == 2


def assert_integrity_group_action(
    report: Path,
    group: Mapping[str, Any],
    *,
    noun: str,
    expected_members: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Require one group action to recover every canonical member."""

    action = group["inspectionAction"]
    assert action["arguments"][:2] == ["inspect", noun]
    assert action["arguments"][2] == "--filter"
    assert action["arguments"][3].startswith("integrity-group=")
    selected = action_payload(report, action, capsys)
    assert len(selected["rows"]) == expected_members
    assert {
        group["id"] in row["fields"]["integrity-group"] for row in selected["rows"]
    } == {True}
    assert group["memberCoverage"]["observedLowerBound"] == expected_members


def test_tiny_review_projection_keeps_region_actions_and_owners(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report, payload = audit_resource_report(
        tmp_path,
        projection="review",
        review_item_limit=1,
    )
    selected_kinds = {"audit_surface_region", "option_resource_region"}
    regions = [
        row
        for row in payload["sections"]["review_regions"]
        if row["kind"] in selected_kinds
    ]

    assert {row["kind"] for row in regions} == selected_kinds
    for region in regions:
        assert action_payload(
            report,
            region["inspectionAction"],
            capsys,
        )["rows"]
        for signal in region["signals"]:
            for reference in signal["evidenceRefs"]:
                assert resolve_local_json_pointer(payload, reference)
            action = signal["inspectionAction"]
            selected = action_payload(report, action, capsys)
            assert [row["id"] for row in selected["rows"]] == [action["arguments"][3]]


def test_tiny_review_projection_aligns_multi_surface_owner_routes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report, payload = multi_surface_review_report(tmp_path)
    regions = [
        row
        for row in payload["sections"]["review_regions"]
        if row["kind"] in {"audit_surface_region", "option_resource_region"}
    ]

    assert len(payload["sections"]["module_dag"]["audit_surfaces"]) == 1
    assert {row["kind"] for row in regions} == {
        "audit_surface_region",
        "option_resource_region",
    }
    for region in regions:
        assert len(region["signals"]) == 1
        signal = region["signals"][0]
        action = signal["inspectionAction"]
        owner = resolve_local_json_pointer(
            payload,
            signal["evidenceRefs"][0],
        )
        assert owner["id"] == action["arguments"][3]
        selected = action_payload(report, action, capsys)
        assert [row["id"] for row in selected["rows"]] == [owner["id"]]
        registration_key = {
            "audits": "auditProducerRegistrations",
            "resources": "resourceProducerRegistrations",
        }[action["arguments"][1]]
        producers = payload["sections"]["module_dag"][registration_key]["producers"]
        assert set(producers) == {signal["id"]}


def test_tiny_review_projection_retains_disjoint_audit_resource_strata(
    tmp_path: Path,
) -> None:
    report, payload = split_surface_review_report(tmp_path)
    regions = {
        row["kind"]: row
        for row in payload["sections"]["review_regions"]
        if row["kind"] in {"audit_surface_region", "option_resource_region"}
    }

    assert len(payload["sections"]["module_dag"]["audit_surfaces"]) == 2
    assert set(regions) == {"audit_surface_region", "option_resource_region"}
    assert all(len(region["signals"]) == 1 for region in regions.values())
    for noun in ("audits", "resources"):
        dataset = load_inspection_dataset(
            report,
            noun,
            artifact_kind="report",
        )
        assert len(dataset.rows) == 1
        assert dataset.coverage["visible"] == 1
        assert dataset.rows[0].coverage_ref in payload["coverage"]["collections"]


def test_dangling_report_owned_resource_action_fails_closed(
    tmp_path: Path,
) -> None:
    report, payload = audit_resource_report(tmp_path)
    producers = payload["sections"]["module_dag"]["resourceProducerRegistrations"][
        "producers"
    ]
    producer = next(iter(producers.values()))
    producer["inspectionAction"]["arguments"][3] = "resource:missing"
    report.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        InspectionCompatibilityError,
        match="do not resolve canonical resources rows",
    ):
        load_inspection_dataset(
            report,
            "resources",
            artifact_kind="report",
        )
