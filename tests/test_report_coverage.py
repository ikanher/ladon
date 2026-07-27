from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ladon.coverage import CollectionCoverage, CoverageCause, CoverageRegistry
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_adapters import coerce_report_v2
from ladon.report_contract import Finding, ReportModelError
from ladon.report_model import ReportV2
from ladon.report_projection_coverage import register_projection_strata
from ladon.report_v3 import build_report_v3, load_report_v3_schema
from ladon.snapshot import AnalysisSnapshot


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def canonical_model() -> ReportV2:
    return run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
        )
    ).to_report_model()


def covered_model() -> ReportV2:
    model = canonical_model()
    visible = len(model.findings)
    coverage = CoverageRegistry().register(
        CollectionCoverage.exact(
            identity="report.findings",
            pointer="#/sections/findings",
            visible=visible,
            total=visible + 3,
            population="selected findings",
            scope=model.metadata.analysis_root_module,
            authority="ladon_analysis",
            causes=(
                CoverageCause(
                    kind="analysis",
                    identifier="findings.upstream_cap",
                    detail="the analysis retained a bounded finding population",
                    controlling_cap=visible,
                ),
            ),
            source_fingerprint=f"sha256:{'1' * 64}",
            scope_fingerprint="sha256:scope",
        )
    )
    snapshot = AnalysisSnapshot(
        source_index_fingerprint=f"sha256:{'1' * 64}",
        entries={},
        configuration={
            "backend": model.metadata.extraction_backend,
            "scopeFingerprint": "sha256:scope",
        },
    )
    return replace(model, coverage=coverage, snapshot=snapshot)


def test_pipeline_attaches_current_coverage_and_snapshot_authority() -> None:
    model = canonical_model()

    assert model.snapshot is not None
    assert set(model.coverage.collections) == {
        "declaration_graph.declarations",
        "declaration_integrity.co_reachable_collisions",
        "declaration_integrity.collision_candidates",
        "declaration_integrity.exact_block_duplicates",
        "declaration_integrity.exact_file_duplicates",
        "declaration_integrity.source_shape_similarities",
        "generated_family.candidates",
        "generated_family.numeric_partitions",
        "module_dag.architecture_joined_evidence",
        "module_dag.audit_commands",
        "module_dag.import_boundaries",
        "module_dag.inspection_options",
        "module_dag.inspection_proof_mechanisms",
        "module_dag.modules",
        "module_dag.resource_directives",
        "module_dag.resource_review_inputs",
        "module_dag.text_declarations",
        "proof_xray.rows",
        "report.findings",
        "report.packet_evidence",
        "report.review_regions",
    }
    assert {row.source_fingerprint for row in model.coverage.collections.values()} == {
        model.snapshot.source_index_fingerprint
    }
    assert {row.scope_fingerprint for row in model.coverage.collections.values()} == {
        model.snapshot.configuration["scopeFingerprint"]
    }


def test_report_v2_keeps_coverage_and_snapshot_out_of_frozen_wire() -> None:
    original = canonical_model()
    evidence = covered_model()
    enriched = replace(
        original,
        coverage=evidence.coverage,
        snapshot=evidence.snapshot,
    )

    assert enriched.coverage.require("report.findings").total_known is True
    assert enriched.snapshot is not None
    assert enriched.to_dict() == original.to_dict()
    assert "coverage" not in enriched.to_dict()
    assert "snapshot" not in enriched.to_dict()


def test_projection_stratum_keeps_unknown_upstream_total_unknown() -> None:
    upstream = CoverageRegistry().register(
        CollectionCoverage.unknown(
            identity="report.findings",
            pointer="#/sections/findings",
            visible=2,
            observed_lower_bound=2,
            completeness="partial",
            population="observed_findings",
            scope="fixture",
            authority="fixture",
            causes=(
                CoverageCause(
                    kind="analysis",
                    identifier="fixture.upstream_partial",
                    detail="fixture intentionally omits upstream rows",
                ),
            ),
        )
    )

    projected = register_projection_strata(
        upstream,
        [
            {
                "pointer": "#/sections/findings",
                "descriptor": {
                    "evidenceKind": "audit",
                    "severity": "warning",
                    "status": "open",
                    "population": "target_owned",
                    "role": "audit",
                },
                "visible": 1,
                "total": 2,
            }
        ],
        projection="review",
        item_limit=1,
    )
    row = next(
        value
        for identity, value in projected.collections.items()
        if identity.startswith("report.projection.stratum.")
    )

    assert row.visible == 1
    assert row.observed_lower_bound == 2
    assert row.total_known is False
    assert row.total is None
    assert row.completeness == "partial"


def test_legacy_v2_mapping_restores_unknown_not_complete_coverage() -> None:
    model = canonical_model()
    restored = coerce_report_v2(model.to_dict())

    assert set(restored.coverage.collections) == {
        "declaration_graph.declarations",
        "report.findings",
        "report.packet_evidence",
        "report.review_regions",
    }
    assert all(
        row.completeness == "unavailable"
        and row.total_known is False
        and row.total is None
        and row.omitted is None
        and row.causes[0].identifier == "coverage.legacy_missing"
        for row in restored.coverage.collections.values()
    )


def test_v3_full_preserves_upstream_omission_and_snapshot_identity() -> None:
    model = covered_model()
    payload = build_report_v3(model, projection="full").to_dict()
    coverage = payload["coverage"]["collections"]["report.findings"]

    Draft202012Validator(load_report_v3_schema()).validate(payload)
    assert coverage["visible"] == len(model.findings)
    assert coverage["total"] == len(model.findings) + 3
    assert coverage["omitted"] == 3
    assert coverage["completeness"] == "partial"
    assert (
        coverage["analysisFingerprint"] == payload["projection"]["analysis_fingerprint"]
    )
    assert [cause["kind"] for cause in coverage["causes"]] == ["analysis"]
    assert payload["projection"]["omissions"] == []
    assert payload["snapshot"] == {
        "schema": model.snapshot.schema,
        "identity": model.snapshot.identity,
        "sourceIndexFingerprint": model.snapshot.source_index_fingerprint,
        "decision": model.snapshot_decision.to_dict(),
    }


def test_v3_review_adds_projection_cause_without_losing_upstream_total() -> None:
    baseline = covered_model()
    template = baseline.findings[0].to_dict()
    model = replace(
        baseline,
        findings=(
            baseline.findings[0],
            Finding.from_mapping({**template, "id": "fixture.same-stratum-second"}),
        ),
    )
    review = build_report_v3(
        model,
        projection="review",
        review_item_limit=1,
    )
    full = build_report_v3(model, projection="full")
    payload = review.to_dict()
    coverage = payload["coverage"]["collections"]["report.findings"]
    finding_omission = next(
        row
        for row in payload["projection"]["omissions"]
        if row["pointer"] == "#/sections/findings"
    )

    Draft202012Validator(load_report_v3_schema()).validate(payload)
    assert coverage["visible"] == 1
    assert coverage["observedLowerBound"] == len(model.findings)
    assert coverage["total"] == len(model.findings) + 3
    assert coverage["omitted"] == len(model.findings) + 2
    assert [cause["kind"] for cause in coverage["causes"]] == [
        "analysis",
        "projection",
    ]
    assert finding_omission["coverageRef"] == "report.findings"
    assert review.analysis_fingerprint == full.analysis_fingerprint


def test_v3_schema_rejects_invented_totals_for_unknown_coverage() -> None:
    payload = build_report_v3(
        coerce_report_v2(canonical_model().to_dict()),
        projection="full",
    ).to_dict()
    invalid = deepcopy(payload)
    row = invalid["coverage"]["collections"]["report.findings"]
    row["total"] = row["visible"]
    row["omitted"] = 0

    errors = list(Draft202012Validator(load_report_v3_schema()).iter_errors(invalid))

    assert any(error.validator == "type" for error in errors)


def test_analysis_fingerprint_includes_coverage_and_snapshot_identity() -> None:
    model = covered_model()
    changed_coverage = CoverageRegistry().register(
        replace(
            model.coverage.require("report.findings"),
            total=len(model.findings) + 4,
            omitted=4,
        )
    )
    changed_snapshot = AnalysisSnapshot(
        source_index_fingerprint=f"sha256:{'1' * 64}",
        entries={},
        configuration={
            "backend": model.metadata.extraction_backend,
            "scopeFingerprint": "sha256:scope",
            "mode": "changed",
        },
    )

    baseline = build_report_v3(model).analysis_fingerprint
    assert (
        build_report_v3(replace(model, coverage=changed_coverage)).analysis_fingerprint
        != baseline
    )
    assert (
        build_report_v3(replace(model, snapshot=changed_snapshot)).analysis_fingerprint
        != baseline
    )


def test_report_rejects_mixed_snapshot_and_coverage_authority() -> None:
    model = covered_model()
    mismatched = CoverageRegistry().register(
        replace(
            model.coverage.require("report.findings"),
            source_fingerprint=f"sha256:{'9' * 64}",
        )
    )

    with pytest.raises(ReportModelError, match="does not match snapshot"):
        replace(model, coverage=mismatched)
