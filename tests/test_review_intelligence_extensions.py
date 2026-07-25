from __future__ import annotations

import json
from pathlib import Path

from ladon.analysis.import_diet import summarize_import_diet
from ladon.analysis.module_readiness import summarize_module_readiness
from ladon.analysis.proof_xray import summarize_proof_xray
from ladon.analysis.refactoring_prescriptions import summarize_refactoring_prescriptions
from ladon.cli import main
from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text


def finding_by_kind(report: dict, kind: str) -> dict:
    """Return one expected finding by exact kind."""

    return next(row for row in report["findings"] if row["kind"] == kind)


def tiny_dag() -> dict:
    return {
        "module_count": 4,
        "edge_count": 3,
        "acyclic": True,
        "topological_layer_count": 2,
        "facade_module_count": 1,
        "edges": {"Pkg": ["Pkg.Core", "Pkg.Helper"], "Pkg.Core": [], "Pkg.Helper": [], "Pkg.Generated.All": ["Pkg.Core"]},
        "import_sites": {
            "Pkg": {
                "Pkg.Core": {"sourcePath": "Pkg.lean", "line": 1, "importText": "import Pkg.Core"},
                "Pkg.Helper": {"sourcePath": "Pkg.lean", "line": 2, "importText": "import Pkg.Helper"},
            }
        },
        "module_metadata": {
            "Pkg": {"path": "Pkg.lean", "roles": ["facade", "public_root_facade"], "tags": [], "importCount": 2},
            "Pkg.Core": {"path": "Pkg/Core.lean", "roles": [], "tags": [], "importCount": 0},
            "Pkg.Helper": {"path": "Pkg/Helper.lean", "roles": [], "tags": [], "importCount": 0},
            "Pkg.Generated.All": {"path": "Pkg/Generated/All.lean", "roles": ["facade", "generated_all"], "tags": ["generated"], "importCount": 1},
        },
        "top_facade_like_modules": [
            {"module": "Pkg", "path": "Pkg.lean", "fan_out": 2, "declarationCount": 0, "subtype": "public_root_facade", "tags": []},
            {"module": "Pkg.Generated.All", "path": "Pkg/Generated/All.lean", "fan_out": 1, "declarationCount": 0, "subtype": "generated_all", "tags": ["generated"]},
        ],
        "top_handwritten_fan_in": [
            {"module": "Pkg.Core", "path": "Pkg/Core.lean", "fan_in": 8, "sample_importers": ["Pkg", "Pkg.Helper"]},
        ],
        "top_fan_in": [],
        "top_fan_out": [],
        "top_facade_fan_out": [],
        "module_name_smells": [
            {"module": "Pkg.GeneratedScalarBw2Eps0p5Gamma0p8.Base", "generated": True, "reasonKinds": ["generated_encoded_parameters"]},
        ],
        "duplicate_import_family_summary": [
            {"generatorFamily": "GeneratedRows", "target": "Pkg.Core", "generated": True, "duplicateModuleCount": 3},
        ],
        "root_direct_import_closures": [{"root": "Pkg", "direct_import": "Pkg.Core", "reachable_module_count": 6}],
    }


def test_module_readiness_reports_facade_generated_and_namespace_drift() -> None:
    report = summarize_module_readiness(
        tiny_dag(),
        {
            "declarations": [
                {
                    "declaration": "Other.Namespace.proof",
                    "module": "Pkg.Core",
                    "sourcePath": "Pkg/Core.lean",
                }
            ]
        },
        {
            "artifactKind": "module_system_witness",
            "schemaVersion": 1,
            "rows": [
                {
                    "module": "Pkg",
                    "visibility": "public",
                    "backend": "lean_module_system_probe",
                    "toolVersion": "4.99.0",
                    "command": "lake env lean ...",
                    "sourcePath": "Pkg.lean",
                    "contentHash": "sha256:pkg",
                    "confidence": "high",
                }
            ],
        },
    )

    kinds = {row["kind"] for row in report["rows"]}
    assert "public_facade_pressure" in kinds
    assert "implementation_public_pressure" in kinds
    assert "generated_public_aggregation" in kinds
    assert "namespace_module_drift" in kinds
    assert "module_system_witness" in kinds
    assert report["witness"] == {"present": True, "valid": True, "rowCount": 1, "diagnosticCount": 0, "quotedOnly": True}
    witness_finding = finding_by_kind(
        report,
        "module_readiness.module_system_witness",
    )
    assert witness_finding["contentHash"] == "sha256:pkg"
    assert witness_finding["confidence"] == "high"


def test_namespace_drift_accepts_parent_namespace_and_aggregates_unrelated_rows() -> None:
    report = summarize_module_readiness(
        tiny_dag(),
        {
            "declarations": [
                {
                    "declaration": "Pkg.Semantics.parentOwned",
                    "module": "Pkg.Semantics.Propagation",
                    "sourcePath": "Pkg/Semantics/Propagation.lean",
                },
                {
                    "declaration": "Other.Space.first",
                    "module": "Pkg.Core",
                    "sourcePath": "Pkg/Core.lean",
                },
                {
                    "declaration": "Other.Space.second",
                    "module": "Pkg.Core",
                    "sourcePath": "Pkg/Core.lean",
                },
            ]
        },
    )

    drift = [
        row
        for row in report["rows"]
        if row["kind"] == "namespace_module_drift"
    ]

    assert len(drift) == 1
    assert drift[0]["module"] == "Pkg.Core"
    assert drift[0]["namespace"] == "Other.Space"
    assert drift[0]["declarationCount"] == 2
    assert drift[0]["authority"] == "source_declaration_inventory"


def test_static_review_intelligence_fixture_runs_through_pipeline() -> None:
    fixture_root = Path(__file__).parent / "fixtures" / "review_intelligence_lean"

    payload = run_pipeline(RunContext(repo_root=fixture_root, requested_root="Pkg")).to_report_payload()

    assert payload["module_dag"]["module_count"] == 4
    assert payload["module_dag"]["source_index"]["inventoryModuleCount"] == 7
    assert payload["module_readiness"]["summary"]["public_facade_pressure"] >= 1
    assert "refactoring_prescriptions" in payload


def test_import_diet_quotes_redundant_imports_and_rejects_stale_rows() -> None:
    fresh = summarize_import_diet(
        tiny_dag(),
        {
            "artifactKind": "import_diet_witness",
            "schemaVersion": 1,
            "rows": [
                {
                    "module": "Pkg",
                    "minimizedImports": ["Pkg.Core"],
                    "toolName": "lake shake",
                    "toolVersion": "4.99.0",
                    "command": "lake shake Pkg",
                    "sourcePath": "Pkg.lean",
                    "contentHash": "sha256:pkg",
                    "confidence": "high",
                }
            ],
        },
    )

    assert fresh["rows"][0]["kind"] == "redundant_import_candidate"
    assert fresh["rows"][0]["subject"] == "Pkg -> Pkg.Helper"
    assert fresh["rows"][0]["line"] == 2
    assert fresh["rows"][0]["command"] == "lake shake Pkg"
    assert fresh["findings"][0]["contentHash"] == "sha256:pkg"
    assert fresh["findings"][0]["confidence"] == "high"

    stale = summarize_import_diet(
        tiny_dag(),
        {
            "artifactKind": "import_diet_witness",
            "schemaVersion": 1,
            "rows": [
                {
                    "module": "Missing.Module",
                    "minimizedImports": [],
                    "toolName": "lake shake",
                    "command": "lake shake Missing.Module",
                }
            ],
        },
    )
    assert stale["rows"][0]["kind"] == "stale_import_diet_witness"
    assert "does not classify imports" in stale["rows"][0]["nonclaim"]


def test_proof_xray_keeps_authority_labels_and_reports_absent_safe_malformed_rows() -> None:
    report = summarize_proof_xray(
        {
            "artifactKind": "proof_xray",
            "schemaVersion": 1,
            "rows": [
                {
                    "declarationName": "Pkg.Proof.main",
                    "kind": "tactic_skeleton",
                    "authority": "lean_elaborated",
                    "backend": "infotree",
                    "toolVersion": "4.99.0",
                    "confidence": "high",
                    "sourcePath": "Pkg/Proof.lean",
                    "sourceRange": {
                        "start": {"line": 5, "column": 0},
                        "end": {"line": 8, "column": 3},
                    },
                    "selectionRange": {
                        "start": {"line": 5, "column": 8},
                        "end": {"line": 5, "column": 12},
                    },
                    "contentHash": "sha256:proof",
                    "tacticSkeleton": ["intro", "simp", "rw", "omega", "exact"],
                },
                {
                    "declarationName": "Pkg.Proof.unsafe",
                    "kind": "trust_footprint",
                    "authority": "external_tool_quoted",
                    "backend": "print_axioms",
                    "toolVersion": "4.99.0",
                    "confidence": "medium",
                    "axioms": ["Classical.choice"],
                },
                {
                    "declarationName": "Pkg.Proof.main",
                    "kind": "dependency_context",
                    "authority": "parser_observed",
                    "backend": "text_parser",
                    "toolVersion": "0.1.0",
                    "confidence": "low",
                    "dependencies": ["Parser.Candidate"],
                },
            ],
        }
    )

    by_kind = {row["kind"]: row for row in report["rows"]}
    assert by_kind["automation_hotspot"]["authority"] == "lean_elaborated"
    assert by_kind["trust_footprint"]["authority"] == "external_tool_quoted"
    assert by_kind["dependency_context"]["authority"] == "parser_observed"
    assert by_kind["dependency_context"]["evidence"]["dependencies"] == ["Parser.Candidate"]
    finding = finding_by_kind(report, "proof_xray.automation_hotspot")
    assert finding["sourceRange"]["end"]["line"] == 8
    assert finding["selectionRange"]["start"]["column"] == 8
    assert finding["contentHash"] == "sha256:proof"

    malformed = summarize_proof_xray([])
    assert malformed["diagnostics"][0]["kind"] == "proof_xray.malformed_witness"


def test_refactoring_prescriptions_prioritize_core_boundary_over_generated_name() -> None:
    report = summarize_refactoring_prescriptions(
        module_dag=tiny_dag(),
        findings=[
            {
                "kind": "large_handwritten_module",
                "subject": "Pkg.Huge",
                "count": 9000,
                "message": "huge",
            }
        ],
        architecture_policy={
            "sharedDependencySummary": [
                {"targetModule": "Pkg.Shared", "confidence": "high", "confidenceScore": 42}
            ],
            "findings": [
                {
                    "kind": "architecture_policy.direct_forbidden_import",
                    "subject": "Pkg.A -> Pkg.B",
                    "policyContext": "core-looking",
                    "triageSeverity": "error",
                }
            ],
        },
    )

    assert report["rows"][0]["action"] == "demote_implementation_import"
    assert report["rows"][0]["subject"] == "Pkg.A -> Pkg.B"
    assert any(row["action"] == "extract_common_lower_layer" for row in report["rows"])
    assert any(row["action"] == "move_generated_parameters_to_manifest" for row in report["rows"])


def test_text_report_renders_review_intelligence_sections() -> None:
    payload = {
        "metadata": {"repo_root": "/repo", "analysis_root_module": "Pkg"},
        "warnings": [],
        "module_dag": {
            **tiny_dag(),
            "top_fan_in": [],
            "top_fan_out": [],
            "facade_modules": [],
            "source_modules_not_reachable_from_chosen_roots": [],
            "source_modules_not_reachable_from_chosen_roots_count": 0,
        },
        "module_readiness": {"summary": {"public_facade_pressure": 1}, "witness": {"present": False, "valid": False}, "rows": [{"kind": "public_facade_pressure", "module": "Pkg", "severity": "info"}]},
        "import_diet": {"summary": {"redundant_import_candidate": 1}, "rows": [{"kind": "redundant_import_candidate", "subject": "Pkg -> Pkg.Helper", "confidence": "high"}]},
        "proof_xray": {"summary": {"automation_hotspot": 1}, "rows": [{"kind": "automation_hotspot", "subject": "Pkg.Proof.main", "authority": "lean_elaborated"}]},
        "refactoring_prescriptions": {"summary": {"run_import_diet": 1}, "rows": [{"action": "run_import_diet", "subject": "Pkg -> Pkg.Helper", "priority": 46, "confidence": "high"}]},
        "findings": [],
        "pipeline": {"timings": {}},
    }

    text = render_text(payload)

    assert "Module Readiness" in text
    assert "Import Diet" in text
    assert "Proof X-Ray" in text
    assert "Refactoring Prescriptions" in text


def test_cli_accepts_import_diet_and_proof_xray_witnesses(tmp_path: Path) -> None:
    (tmp_path / "Pkg").mkdir()
    (tmp_path / "Pkg.lean").write_text("import Pkg.Core\nimport Pkg.Helper\n", encoding="utf-8")
    (tmp_path / "Pkg" / "Core.lean").write_text("def core : Nat := 1\n", encoding="utf-8")
    (tmp_path / "Pkg" / "Helper.lean").write_text("def helper : Nat := 2\n", encoding="utf-8")
    import_witness = tmp_path / "import-diet.json"
    import_witness.write_text(
        json.dumps(
            {
                "artifactKind": "import_diet_witness",
                "schemaVersion": 1,
                "rows": [
                    {
                        "module": "Pkg",
                        "minimizedImports": ["Pkg.Core"],
                        "toolName": "lake shake",
                        "toolVersion": "4.99.0",
                        "command": "lake shake Pkg",
                        "confidence": "high",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    proof_xray = tmp_path / "proof-xray.json"
    proof_xray.write_text(
        json.dumps(
            {
                "artifactKind": "proof_xray",
                "schemaVersion": 1,
                "rows": [
                    {
                        "declarationName": "Pkg.main",
                        "authority": "lean_elaborated",
                        "backend": "infotree",
                        "toolVersion": "4.99.0",
                        "confidence": "high",
                        "tacticSkeleton": ["intro", "simp", "rw", "omega", "exact"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "report.json"

    status = main([
        "--repo-root",
        str(tmp_path),
        "--root",
        "Pkg",
        "--import-diet-witness",
        str(import_witness),
        "--proof-xray",
        str(proof_xray),
        "--output-json",
        str(output),
    ])

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["import_diet"]["summary"]["redundant_import_candidate"] == 1
    assert payload["proof_xray"]["summary"]["automation_hotspot"] == 1
