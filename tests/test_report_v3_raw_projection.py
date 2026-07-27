from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from ladon.coverage import CollectionCoverage, CoverageRegistry
from ladon.report_contract import Finding
from ladon.report_model import ReportV2
from ladon.report_v3 import build_report_v3
from test_report_v3 import (
    canonical_model,
    model_with_large_payload,
    resolve_json_pointer,
)


def test_limit_below_stratum_count_retains_every_present_stratum() -> None:
    model = model_with_stratified_findings()
    payload = build_report_v3(
        model,
        projection="review",
        review_item_limit=1,
    ).to_dict()

    selected = payload["sections"]["findings"]
    assert len(selected) == 3
    assert {row["severity"] for row in selected} == {
        "error",
        "warning",
        "info",
    }
    assert finding_stratum_counts(payload) == [
        (1, 2, 1, "partial"),
        (1, 2, 1, "partial"),
        (1, 2, 1, "partial"),
    ]
    omission = next(
        row
        for row in payload["projection"]["omissions"]
        if row["pointer"] == "#/sections/findings"
    )
    assert omission["omitted_count"] == 3
    assert omission["coverageRef"] == "report.findings"
    assert payload["projection"]["limits"] == {
        "max_collection_items": None,
        "max_unstratified_collection_items": 1,
        "max_items_per_present_stratum": 1,
        "selection_policy": "per_present_stratum",
    }


def test_per_stratum_selection_is_insertion_order_independent() -> None:
    model = model_with_stratified_findings()
    findings = model.findings
    reports = [
        build_report_v3(
            replace(model, findings=rows),
            projection="review",
            review_item_limit=1,
        ).to_dict()
        for rows in (findings, tuple(reversed(findings)))
    ]

    assert [
        row["id"] for row in reports[0]["sections"]["findings"]
    ] == [
        row["id"] for row in reports[1]["sections"]["findings"]
    ]
    assert finding_stratum_counts(reports[0]) == finding_stratum_counts(
        reports[1]
    )


def test_stratified_regions_rebind_signal_coverage_to_projected_owner() -> None:
    model = model_with_reorderable_review_regions()
    full = build_report_v3(model, projection="full").to_dict()
    review = build_report_v3(
        model,
        projection="review",
        review_item_limit=1,
    ).to_dict()

    assert [row["id"] for row in full["sections"]["review_regions"]] == [
        "region:proof",
        "region:audit",
    ]
    assert [row["id"] for row in review["sections"]["review_regions"]] == [
        "region:audit",
        "region:proof",
    ]
    assert_projected_region_coverage(review)
    audit = review["sections"]["review_regions"][0]
    audit_coverage = review["coverage"]["collections"][audit["coverageRef"]]
    assert audit_coverage["total"] == 2
    assert audit_coverage["omitted"] == 1


def assert_projected_region_coverage(report: Mapping[str, Any]) -> None:
    """Assert every projected region owns its synchronized signal coverage."""

    regions = report["sections"]["review_regions"]
    collections = report["coverage"]["collections"]
    for index, region in enumerate(regions):
        coverage = collections[region["coverageRef"]]
        pointer = f"#/sections/review_regions/{index}/signals"
        assert coverage["pointer"] == pointer
        assert resolve_json_pointer(report, pointer) == region["signals"]
        assert coverage["visible"] == len(region["signals"])
        assert region["signal_count"] == len(region["signals"])
        assert region["coverage"] == coverage
        assert region["inspectionAction"]["arguments"] == [
            "inspect",
            "modules",
        ]


def model_with_reorderable_review_regions() -> ReportV2:
    """Return two covered regions whose canonical order stratification changes."""

    model = canonical_model()
    source_fingerprint = model.snapshot.source_index_fingerprint
    scope_fingerprint = model.snapshot.configuration["scopeFingerprint"]
    proof = region_signal_coverage(
        "report.review_regions.proof.fixture.signals",
        index=0,
        visible=1,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )
    audit = region_signal_coverage(
        "report.review_regions.audit.fixture.signals",
        index=1,
        visible=2,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )
    regions = [
        covered_region("region:proof", "proof_family_region", proof),
        covered_region("region:audit", "audit_surface_region", audit),
    ]
    review_phase = model.phases["review_regions"]
    phases = {
        **model.phases,
        "review_regions": replace(
            review_phase,
            data=regions,
            counters={"regions": len(regions)},
        ),
    }
    retained = {
        identity: row
        for identity, row in model.coverage.collections.items()
        if not identity.startswith("report.review_regions.")
    }
    coverage = CoverageRegistry(retained).register(proof).register(audit)
    return replace(model, phases=phases, coverage=coverage)


def region_signal_coverage(
    identity: str,
    *,
    index: int,
    visible: int,
    source_fingerprint: str,
    scope_fingerprint: str,
) -> CollectionCoverage:
    """Return exact fixture coverage for one canonical region position."""

    return CollectionCoverage.exact(
        identity=identity,
        pointer=f"#/sections/review_regions/{index}/signals",
        visible=visible,
        total=visible,
        population=f"{identity}.population",
        scope="fixture",
        authority="fixture",
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )


def covered_region(
    identity: str,
    kind: str,
    coverage: CollectionCoverage,
) -> dict[str, Any]:
    """Return one complete report-owned region fixture."""

    signals = [
        {
            "id": f"{identity}:signal:{index}",
            "kind": kind,
            "subject": identity,
        }
        for index in range(coverage.visible)
    ]
    return {
        "id": identity,
        "kind": kind,
        "title": identity,
        "signal_count": len(signals),
        "signals": signals,
        "coverageRef": coverage.identity,
        "coverage": coverage.to_dict(),
        "upstreamCoverageRefs": ["module_dag.modules"],
        "authority": "fixture",
        "authorities": ["fixture"],
        "nonclaims": ["Fixture navigation only."],
        "inspectionAction": {
            "command": "ladon",
            "arguments": ["inspect", "modules"],
        },
    }


def stratified_findings() -> tuple[Finding, ...]:
    """Return three two-member evidence strata in non-severity order."""

    descriptors = [
        ("architecture", "info", "open", "target_owned", "owner"),
        ("architecture", "info", "open", "target_owned", "owner"),
        ("audit", "warning", "unresolved", "target_owned", "audit"),
        ("audit", "warning", "unresolved", "target_owned", "audit"),
        ("snapshot", "error", "changed", "inventory", "integrity"),
        ("snapshot", "error", "changed", "inventory", "integrity"),
    ]
    return tuple(
        Finding.from_mapping(
            {
                "id": f"finding:{index}",
                "kind": kind,
                "severity": severity,
                "status": status,
                "population": population,
                "role": role,
                "subject": f"Fixture.subject{index}",
                "message": "review",
                "authority": "fixture",
                "evidence_count": 1,
            }
        )
        for index, (kind, severity, status, population, role) in enumerate(descriptors)
    )


def model_with_stratified_findings() -> ReportV2:
    """Return three covered two-member strata for projection regression tests."""

    model = canonical_model()
    findings = stratified_findings()
    source = model.coverage.require("report.findings")
    coverage = CoverageRegistry(
        {
            **model.coverage.collections,
            "report.findings": replace(
                source,
                visible=len(findings),
                observed_lower_bound=len(findings),
                total=len(findings),
                omitted=0,
            ),
        }
    )
    return replace(model, findings=findings, coverage=coverage)


def finding_stratum_counts(payload: dict) -> list[tuple]:
    """Return stable count tuples for projected finding strata."""

    rows = [
        row
        for identity, row in payload["coverage"]["collections"].items()
        if identity.startswith("report.projection.stratum.")
        and row["pointer"] == "#/sections/findings"
    ]
    return sorted(
        (
            row["visible"],
            row["total"],
            row["omitted"],
            row["completeness"],
        )
        for row in rows
    )


def test_nested_reordered_declarations_mint_final_evidence_pointers() -> None:
    model = canonical_model()
    source = model.phases["module_dag"]
    groups = [
        {
            "id": identity,
            "kind": "declaration_group",
            "declarations": [
                {
                    "declaration": f"Fixture.{identity}",
                    "authority": f"authority-{identity}",
                }
            ],
        }
        for identity in ("z", "a")
    ]
    phases = {
        **model.phases,
        "module_dag": replace(source, data={"groups": groups}),
    }

    payload = build_report_v3(
        replace(model, phases=phases),
        projection="review",
    ).to_dict()
    selected = payload["sections"]["module_dag"]["groups"]

    assert [row["id"] for row in selected] == ["a", "z"]
    for group in selected:
        declaration = group["declarations"][0]
        evidence = resolve_json_pointer(payload, declaration["evidenceRef"])
        assert evidence["fields"]["/authority"] == (
            f"authority-{group['id']}"
        )


def test_omitted_raw_row_changes_projection_independent_fingerprint() -> None:
    model = model_with_large_payload()
    source = model.phases["module_dag"]
    first_data = dict(source.data)
    second_data = dict(source.data)
    second_rows = [dict(row) for row in second_data["rows"]]
    second_rows[-1]["source_bytes"] += 1
    second_data["rows"] = second_rows
    first = replace(
        model,
        phases={
            **model.phases,
            "module_dag": replace(source, data=first_data),
        },
    )
    second = replace(
        model,
        phases={
            **model.phases,
            "module_dag": replace(source, data=second_data),
        },
    )

    first_review = build_report_v3(
        first,
        projection="review",
        review_item_limit=1,
    )
    second_review = build_report_v3(
        second,
        projection="review",
        review_item_limit=1,
    )
    second_full = build_report_v3(second, projection="full")

    assert first_review.payload["sections"] == second_review.payload["sections"]
    assert first_review.analysis_fingerprint != second_review.analysis_fingerprint
    assert second_review.analysis_fingerprint == second_full.analysis_fingerprint
