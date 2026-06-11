from __future__ import annotations

import json
from pathlib import Path

from ladon.atlas import build_report_atlas
from ladon.atlas_workflow import build_atlas_workflow, render_atlas_workflow_markdown


def test_atlas_workflow_answers_reviewer_routing_questions(tmp_path: Path) -> None:
    before_root = tmp_path / "before"
    after_root = tmp_path / "after"
    write_report(before_root / "quux" / "one.json", sample_report("Quux.One", fan_in=3))
    write_report(after_root / "quux" / "one.json", sample_report("Quux.One", fan_in=8))
    write_report(after_root / "mf" / "two.json", sample_report("Mf.Two", fan_in=8))

    workflow = build_atlas_workflow(
        build_report_atlas(after_root),
        before_atlas=build_report_atlas(before_root),
        bridge_reports=[sample_bridge_report()],
    )

    sections = workflow["sections"]
    assert workflow["canonicalMachineReadableSurface"] == "atlas_json"
    assert sections["changedRows"]["summary"]["changed"] > 0
    assert sections["recurringHotspots"][0]["subject"] == "Shared.Hotspot"
    assert sections["reviewPriorityRoots"][0]["root"] == "Quux.One"
    assert sections["lowConfidenceJoins"][0]["matchKind"] == "basename_only"
    assert sections["incompleteOrStaleEvidence"]
    cards = {card["root"]: card for card in workflow["reviewerCards"]}
    assert cards["Quux.One"]["bridge_diagnostics"]["diagnostic_count"] == 1


def test_atlas_workflow_without_bridge_has_stable_empty_bridge_sections(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "one.json", sample_report("Quux.One", fan_in=8))

    workflow = build_atlas_workflow(build_report_atlas(tmp_path))
    markdown = render_atlas_workflow_markdown(workflow)

    assert workflow["inputs"]["bridgeReportCount"] == 0
    assert workflow["sections"]["lowConfidenceJoins"] == []
    assert "# Ladon Atlas Review Workflow" in markdown
    assert "## Low Confidence Joins\n- none" in markdown


def test_atlas_workflow_imports_quux_bridge_snapshot_as_optional_evidence(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "one.json", sample_report("Quux.One", fan_in=8))

    workflow = build_atlas_workflow(
        build_report_atlas(tmp_path),
        bridge_reports=[sample_bridge_snapshot()],
    )

    sections = workflow["sections"]
    assert workflow["inputs"]["bridgeReportCount"] == 1
    assert sections["reviewPriorityRoots"][0]["root"] == "Quux.One"
    assert sections["reviewPriorityRoots"][0]["bridgePressure"] == 2
    assert sections["lowConfidenceJoins"][0] == {
        "root": "Quux.One",
        "surfaceId": "surface.quux.minimum_path_sum.exact_value_satisfies",
        "declarationName": "Quux.Problems.MinimumPathSum.exact_value_satisfies",
        "matchKind": "root_module_source_anchor",
        "confidence": "low",
        "warningOnly": True,
    }
    cards = {card["root"]: card for card in workflow["reviewerCards"]}
    assert cards["Quux.One"]["bridge_diagnostics"]["diagnostic_counts"] == {
        "proofir.status_quoted_not_promoted": 1
    }
    assert any(
        "not Ladon proof truth" in rule
        for rule in cards["Quux.One"]["bridge_diagnostics"]["trust_rules"]
    )


def test_atlas_workflow_keeps_source_line_anchor_snapshot_join_warning_only(tmp_path: Path) -> None:
    write_report(tmp_path / "quux" / "one.json", sample_report("Quux.One", fan_in=8))
    snapshot = sample_bridge_snapshot()
    snapshot["bridgeReport"]["joins"][0]["matchKind"] = "source_line_anchor_decl"

    workflow = build_atlas_workflow(
        build_report_atlas(tmp_path),
        bridge_reports=[snapshot],
    )

    assert workflow["sections"]["lowConfidenceJoins"][0]["matchKind"] == "source_line_anchor_decl"
    assert workflow["sections"]["lowConfidenceJoins"][0]["confidence"] == "low"
    assert workflow["sections"]["lowConfidenceJoins"][0]["warningOnly"] is True


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def sample_report(root: str, *, fan_in: int) -> dict:
    return {
        "metadata": {"analysis_root_module": root},
        "module_dag": {"module_count": 1, "edge_count": 0},
        "declaration_graph": {
            "declaration_count": 1,
            "edge_count": 0,
            "top_fan_in": [{"declaration": "Shared.Hotspot", "fan_in": fan_in}],
            "top_fan_out": [],
        },
        "findings": [
            {
                "kind": "declaration_fan_in_hotspot",
                "subject": "Shared.Hotspot",
                "count": fan_in,
            }
        ],
        "packet_evidence": [
            {
                "packet_dir": "/packets/review",
                "status": "partial",
                "profile_status": "partial",
            }
        ],
        "review_regions": [
            {
                "kind": "packet_evidence_region",
                "title": "Packet evidence",
                "signal_count": 1,
                "signals": [
                    {
                        "kind": "packet_evidence",
                        "subject": "/packets/review",
                        "count": 1,
                    }
                ],
            }
        ],
    }


def sample_bridge_report() -> dict:
    return {
        "reviewerCards": [{"root": "Quux.One"}],
        "joins": [
            {
                "surfaceId": "surface.name_only",
                "declarationName": "target",
                "matchKind": "basename_only",
                "confidence": "low",
                "warningOnly": True,
            }
        ],
        "diagnostics": [
            {
                "ruleId": "proofir.name_only_join_warning",
                "level": "warning",
                "subject": "surface.name_only",
            }
        ],
        "trustRules": ["name-only joins are warning-only"],
    }


def sample_bridge_snapshot() -> dict:
    return {
        "artifactKind": "ladon_proofir_bridge_snapshot",
        "sourceLadonReport": {
            "analysisRootModule": "Quux.One",
            "path": "docs/generated/minimum-path-sum-ladon-report.json",
        },
        "surfaces": [
            {
                "surfaceId": "surface.quux.minimum_path_sum.exact_value_satisfies",
                "claimId": "claim.quux.minimum_path_sum.exact_value_satisfies",
                "declarationName": "Quux.Problems.MinimumPathSum.exact_value_satisfies",
                "status": "established_external_lean",
                "authority": ["lean_kernel_external"],
            }
        ],
        "bridgeReport": {
            "joins": [
                {
                    "surfaceId": "surface.quux.minimum_path_sum.exact_value_satisfies",
                    "claimId": "claim.quux.minimum_path_sum.exact_value_satisfies",
                    "analysisRootModule": "Quux.One",
                    "matchKind": "root_module_source_anchor",
                }
            ],
            "diagnostics": [
                {
                    "diagnosticId": "proofir.status_quoted_not_promoted",
                    "severity": "info",
                    "message": "External status is quoted, not promoted.",
                }
            ],
        },
    }
