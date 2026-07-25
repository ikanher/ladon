from __future__ import annotations

from pathlib import Path
from typing import Any

from ladon.analysis.findings import generated_family_pressure_findings
from ladon.finding_workflow import validate_finding_evidence
from ladon.large_inventory_gate import normalized_report_bytes
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_v3 import build_report_v3


def generated_policy(at_least: int) -> dict[str, Any]:
    """Return a portable v2 policy with an explicit family threshold."""

    return {
        "schema": "ladon-generated-family-policy-v2",
        "families": [
            {
                "id": "fixture.rows",
                "pathPatterns": ["Pkg/Generated/*.lean"],
                "reviewThreshold": {
                    "metric": "memberCount",
                    "atLeast": at_least,
                },
            }
        ],
    }


def family_row(
    *,
    member_count: int,
    threshold: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the aggregate fields consumed by finding promotion."""

    return {
        "id": "ladon.generated_family.fixture",
        "familyId": "fixture.rows",
        "population": "project_generated",
        "policyDigest": "a" * 64,
        "memberCount": member_count,
        "reviewThreshold": threshold,
        "reviewMetricValue": (
            member_count if threshold is not None else None
        ),
        "reviewThresholdCrossed": (
            threshold is not None
            and member_count >= int(threshold["atLeast"])
        ),
    }


def test_family_findings_require_and_quote_the_configured_threshold() -> None:
    threshold = {"metric": "memberCount", "atLeast": 2}
    promoted = generated_family_pressure_findings(
        {
            "population_calibration": {
                "generatedFamilies": [
                    family_row(member_count=2, threshold=threshold)
                ]
            }
        }
    )
    unconfigured = generated_family_pressure_findings(
        {
            "population_calibration": {
                "generatedFamilies": [
                    family_row(member_count=1000, threshold=None)
                ]
            }
        }
    )
    below = generated_family_pressure_findings(
        {
            "population_calibration": {
                "generatedFamilies": [
                    family_row(member_count=1, threshold=threshold)
                ]
            }
        }
    )

    assert len(promoted) == 1
    finding = promoted[0]
    assert finding["kind"] == "generated_family_review_pressure"
    assert finding["promotion_population"] == "project_generated"
    assert finding["promotion_threshold"] == 2
    assert finding["review_metric"] == "memberCount"
    assert "review pressure only" in finding["message"]
    assert "does not establish a generator defect" in finding["message"]
    assert unconfigured == []
    assert below == []


def test_pipeline_family_finding_resolves_to_exact_full_report_row(
    tmp_path: Path,
) -> None:
    write_generated_fixture(tmp_path)
    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg.lean",
            generated_family_policy=generated_policy(at_least=2),
            source_cache_enabled=False,
        )
    )
    report = build_report_v3(
        result.to_report_model(),
        projection="full",
    ).to_dict()
    finding = next(
        row
        for row in report["sections"]["findings"]
        if row["kind"] == "generated_family_review_pressure"
    )
    evidence = finding["evidenceRefs"][0]
    aggregate = (
        report["sections"]["module_dag"]["population_calibration"][
            "generatedFamilies"
        ][0]
    )
    validate_finding_evidence(report, report["sections"]["findings"])

    assert evidence["pointer"] == (
        "#/sections/module_dag/population_calibration/generatedFamilies/0"
    )
    assert evidence["identity"] == {
        "id": aggregate["id"],
        "familyId": "fixture.rows",
        "population": "project_generated",
        "policyDigest": aggregate["policyDigest"],
        "reviewThreshold": {"metric": "memberCount", "atLeast": 2},
        "reviewMetricValue": 2,
    }
    assert aggregate["rawMemberIds"] == [
        "module:Pkg.Generated.Row1",
        "module:Pkg.Generated.Row2",
    ]
    assert aggregate["representativeMemberIds"] == aggregate["rawMemberIds"]
    assert aggregate["reviewThresholdCrossed"] is True


def test_repeated_calibrated_pipeline_has_equal_normalized_report_bytes(
    tmp_path: Path,
) -> None:
    write_generated_fixture(tmp_path)

    def analyze() -> dict[str, Any]:
        result = run_pipeline(
            RunContext(
                repo_root=tmp_path,
                requested_root="Pkg.lean",
                analysis_scope="inventory",
                generated_family_policy=generated_policy(at_least=2),
                source_cache_enabled=False,
            )
        )
        return build_report_v3(
            result.to_report_model(),
            projection="full",
        ).to_dict()

    first = analyze()
    second = analyze()

    assert first["sections"]["module_dag"]["population_calibration"] == (
        second["sections"]["module_dag"]["population_calibration"]
    )
    assert normalized_report_bytes(first)[0] == normalized_report_bytes(second)[0]


def write_generated_fixture(root: Path) -> None:
    """Write a small import graph with two policy-owned generated members."""

    generated = root / "Pkg" / "Generated"
    generated.mkdir(parents=True)
    (root / "Pkg.lean").write_text(
        "import Pkg.Generated.Row1\nimport Pkg.Generated.Row2\n",
        encoding="utf-8",
    )
    (generated / "Row1.lean").write_text(
        "theorem row1 : True := by trivial\n",
        encoding="utf-8",
    )
    (generated / "Row2.lean").write_text(
        "import Pkg.Generated.Row1\n"
        "theorem row2 : True := by trivial\n",
        encoding="utf-8",
    )
