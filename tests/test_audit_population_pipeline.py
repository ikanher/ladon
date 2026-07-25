from __future__ import annotations

from pathlib import Path

from ladon.audit_enrichment import audit_queries_from_elaborated_payload
from ladon.extraction import ModuleDiscovery
from ladon.ir import ExtractionBundle, LeanDeclaration
from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text


def write_fixture(root: Path) -> None:
    (root / "Pkg" / "Generated").mkdir(parents=True)
    (root / "Pkg" / "Facade.lean").write_text(
        """\
import Pkg.Owner
import Pkg.Generated.Row
#check Pkg.Owner.owner
#print axioms Pkg.Owner.owner
set_option maxHeartbeats 0 in
""",
        encoding="utf-8",
    )
    (root / "Pkg" / "Owner.lean").write_text(
        "theorem owner : True := by trivial\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Generated" / "Row.lean").write_text(
        "theorem row : True := by trivial\n",
        encoding="utf-8",
    )


def generated_policy() -> dict:
    return {
        "schema": "ladon-generated-family-policy-v1",
        "families": [
            {
                "id": "rows",
                "pathPatterns": ["Pkg/Generated/*.lean"],
                "generator": {"name": "fixture-generator", "version": "1"},
            }
        ],
    }


def assert_audit_surface(dag: dict) -> None:
    """Check command-only ownership and deliberately unavailable results."""

    facade = dag["module_metadata"]["Pkg.Facade"]
    assert facade["commandOnly"] is True
    assert dag["audit_summary"] == {
        "modules": 1,
        "commandOnlyModules": 1,
        "auditCommands": 2,
        "resourceDirectives": 1,
        "backend": "text",
        "authority": "lexical_text",
    }
    surface = dag["audit_surfaces"][0]
    commands = surface["auditCommands"]
    assert {row["kind"] for row in commands} == {"check", "print_axioms"}
    assert all(row["resultStatus"] == "unavailable" for row in commands)
    assert surface["resourceDirectives"][0]["normalizedMeaning"] == "unlimited"


def assert_population_calibration(dag: dict) -> None:
    """Check authored/generated population separation and ranking scope."""

    populations = {
        row["module"]: row["population"]
        for row in dag["population_calibration"]["rows"]
    }
    assert populations == {
        "Pkg.Facade": "target_owned",
        "Pkg.Generated.Row": "project_generated",
        "Pkg.Owner": "target_owned",
    }
    family = dag["population_calibration"]["generatedFamilies"][0]
    assert family["familyId"] == "rows"
    assert family["memberCount"] == 1
    assert dag["top_target_owned_fan_in"][0]["population"] == (
        "target_owned_importers_to_target_owned_targets"
    )


def test_pipeline_reports_command_only_audit_and_calibrated_populations(
    tmp_path: Path,
) -> None:
    write_fixture(tmp_path)
    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Facade.lean",
            generated_family_policy=generated_policy(),
            source_cache_enabled=False,
        )
    )
    payload = result.to_report_payload()
    dag = payload["module_dag"]

    assert_audit_surface(dag)
    assert_population_calibration(dag)

    text = render_text(payload)
    assert "Lean Audit Surfaces" in text
    assert "Population Calibration" in text
    assert "1 omitted" not in text


def test_pipeline_threads_exact_lean_query_authority_and_populations(
    tmp_path: Path,
) -> None:
    write_fixture(tmp_path)

    def fake_extractor(
        _context: RunContext,
        discovery: ModuleDiscovery,
    ) -> ExtractionBundle:
        source_path = "Pkg/Facade.lean"
        source_text = (tmp_path / source_path).read_text(encoding="utf-8")
        query_payload = {
            "version": "2",
            "helperVersion": "fixture-elaborated-helper",
            "leanVersion": "4.fixture",
            "declarations": [
                {
                    "fullyQualifiedName": "Pkg.Owner.owner",
                    "ownerModule": "Pkg.Owner",
                    "status": "complete",
                    "renderedType": "True",
                    "renderedTypeTruncated": False,
                    "axioms": {
                        "items": [],
                        "total": 0,
                        "truncated": False,
                        "status": "complete",
                    },
                }
            ],
        }
        return ExtractionBundle(
            modules=discovery.modules,
            declarations={
                "Pkg.Owner.owner": LeanDeclaration(
                    name="Pkg.Owner.owner",
                    module="Pkg.Owner",
                    extraction_backend="lean_elaborated_helper",
                    name_resolution_method="lean_environment",
                    confidence="lean_environment",
                )
            },
            audit_queries=audit_queries_from_elaborated_payload(
                "Pkg.Facade",
                source_path,
                source_text,
                query_payload,
            ),
        )

    payload = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Facade.lean",
            extraction_backend="lean",
            lean_extractor=fake_extractor,
            generated_family_policy=generated_policy(),
            source_cache_enabled=False,
        )
    ).to_report_payload()
    commands = {
        row["kind"]: row
        for row in payload["module_dag"]["audit_surfaces"][0][
            "auditCommands"
        ]
    }

    for row in commands.values():
        assert_audit_owner_contract(row)
        assert_audit_result_contract(row)
    assert commands["check"]["queryResult"]["renderedType"] == "True"
    assert commands["print_axioms"]["queryResult"]["axioms"]["items"] == []


def assert_audit_owner_contract(row: dict) -> None:
    """Require lexical, containing-owner, and referenced-owner provenance."""

    assert row["backend"] == "text"
    assert row["authority"] == "lexical_text"
    assert row["containingOwner"] == "Pkg.Facade"
    assert row["containingPopulation"] == "target_owned"
    assert row["referencedDeclaration"] == "Pkg.Owner.owner"
    assert row["referencedOwner"] == "Pkg.Owner"
    assert row["referencedPopulation"] == "target_owned"


def assert_audit_result_contract(row: dict) -> None:
    """Require result backend, authority, and independent nonclaims."""

    assert row["referencedBackend"] == "lean_elaborated_helper"
    assert row["resultStatus"] == "complete"
    assert row["resultBackend"] == "lean_elaborated_helper"
    assert row["resultAuthority"] == "lean_environment"
    assert "theorem truth" in row["resultNonclaim"]
    assert "Lexical #" in row["nonclaim"]


def test_resource_directive_findings_require_source_pattern_policy(
    tmp_path: Path,
) -> None:
    write_fixture(tmp_path)
    default = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Facade.lean",
            source_cache_enabled=False,
        )
    )
    assert all(
        finding.get("patternKind") != "lean_resource_directive"
        for finding in default.findings
    )

    promoted = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Facade.lean",
            source_cache_enabled=False,
            source_pattern_policy={
                "id": "fixture-resource-policy",
                "patterns": [
                    {
                        "id": "unlimited-heartbeats",
                        "pattern": "set_option maxHeartbeats 0",
                        "kind": "lean_resource_directive",
                        "severity": "warning",
                    }
                ],
            },
        )
    )
    matches = promoted.source_patterns["matches"]
    findings = [
        row
        for row in promoted.findings
        if row.get("patternKind") == "lean_resource_directive"
    ]

    assert len(matches) == 1
    assert matches[0]["module"] == "Pkg.Facade"
    assert len(findings) == 1
    assert findings[0]["kind"] == "source_pattern.match"
    assert findings[0]["authority"] == "lexical_text"
