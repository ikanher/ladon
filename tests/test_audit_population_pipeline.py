from __future__ import annotations

from pathlib import Path

from ladon.audit_enrichment import audit_queries_from_elaborated_payload
from ladon.extraction import ModuleDiscovery
from ladon.ir import ExtractionBundle, LeanDeclaration
from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text
from ladon.report_v3 import build_report_v3
from ladon.source_index_models import SOURCE_FAILURE_DIAGNOSTIC


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
        """\
namespace Pkg.Owner
theorem owner : True := by trivial
end Pkg.Owner
""",
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
    assert {
        "commandOnly": facade["commandOnly"],
        "facadeSubtype": facade["facadeSubtype"],
        "roles": facade["roles"],
    } == {
        "commandOnly": True,
        "facadeSubtype": "command_only_audit_facade",
        "roles": [
            "facade",
            "command_only_audit_facade",
            "audit_surface",
        ],
    }
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
    expected = {
        (
            row["kind"],
            row["resultStatus"],
            row["candidateStatus"],
            row["candidateReferencedDeclaration"],
            row["candidateReferencedOwner"],
            row["candidateAuthority"],
        )
        for row in commands
    }
    assert expected == {
        (
            "check",
            "unavailable",
            "lexical_candidate",
            "Pkg.Owner.owner",
            "Pkg.Owner",
            "lexical_text",
        ),
        (
            "print_axioms",
            "unavailable",
            "lexical_candidate",
            "Pkg.Owner.owner",
            "Pkg.Owner",
            "lexical_text",
        ),
    }
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
    dag = _v3_sections(result)["module_dag"]

    assert_audit_surface(dag)
    assert_population_calibration(dag)

    text = render_text(payload)
    assert "Lean Audit Surfaces" in text
    assert "Population Calibration" in text
    assert "1 omitted" not in text


def test_pipeline_reuses_bounded_canonical_resource_normalization(
    tmp_path: Path,
) -> None:
    raw_value = "9" * 5_000
    (tmp_path / "Pkg").mkdir()
    (tmp_path / "Pkg" / "Huge.lean").write_text(
        f"set_option maxRecDepth {raw_value}\n",
        encoding="utf-8",
    )
    context = RunContext(
        repo_root=tmp_path,
        requested_root="Pkg/Huge.lean",
        source_cache_enabled=False,
    )

    result = run_pipeline(context)
    payload = result.to_report_payload()
    indexed = context.source_index

    assert indexed is not None
    canonical = indexed.modules["Pkg.Huge"].resource_settings[0]
    reported = payload["module_dag"]["audit_surfaces"][0]["resourceDirectives"][0]
    assert {
        "id": reported["id"],
        "rawValue": reported["rawValue"],
        "numericValue": reported["numericValue"],
        "normalizedMeaning": reported["normalizedMeaning"],
        "lexicalScope": reported["lexicalScope"],
        "status": reported["status"],
    } == {
        "id": canonical.identifier,
        "rawValue": canonical.raw_value,
        "numericValue": canonical.numeric_value,
        "normalizedMeaning": canonical.normalized_meaning,
        "lexicalScope": canonical.lexical_scope,
        "status": canonical.status,
    }
    assert len(reported["rawValue"]) == 256
    assert reported["status"] == "unresolved"
    assert reported["diagnostics"][0]["code"] == ("audit.resource_value_unparsed")


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

    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Facade.lean",
            extraction_backend="lean",
            lean_extractor=fake_extractor,
            generated_family_policy=generated_policy(),
            source_cache_enabled=False,
        )
    )
    payload = _v3_sections(result)
    commands = {
        row["kind"]: row
        for row in payload["module_dag"]["audit_surfaces"][0]["auditCommands"]
    }

    for row in commands.values():
        assert_audit_owner_contract(row)
        assert_audit_result_contract(row)
    assert commands["check"]["queryResult"]["renderedType"] == "True"
    assert commands["print_axioms"]["queryResult"]["axioms"]["items"] == []
    registrations = payload["module_dag"]["auditProducerRegistrations"][
        "producers"
    ].values()
    for registration in registrations:
        assert (
            "#/sections/module_dag/module_metadata/Pkg.Facade"
            in registration["evidenceRefs"]
        )
        assert any(
            ref.startswith("source-index:declaration:")
            for ref in registration["evidenceRefs"]
        )
        assert (
            "#/sections/declaration_graph/declarations/0"
            in registration["evidenceRefs"]
        )


def test_pipeline_keeps_ambiguous_and_unresolved_lexical_owners(
    tmp_path: Path,
) -> None:
    (tmp_path / "Pkg").mkdir()
    for module in ("Left", "Right"):
        (tmp_path / "Pkg" / f"{module}.lean").write_text(
            """\
namespace Shared
theorem duplicate : True := by trivial
end Shared
""",
            encoding="utf-8",
        )
    (tmp_path / "Pkg" / "Audit.lean").write_text(
        """\
import Pkg.Left
import Pkg.Right
#check Shared.duplicate
#check Nat
""",
        encoding="utf-8",
    )

    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Audit.lean",
            source_cache_enabled=False,
        )
    )
    payload = _v3_sections(result)
    commands = {
        row["subject"]: row
        for row in payload["module_dag"]["audit_surfaces"][0]["auditCommands"]
    }

    ambiguous = commands["Shared.duplicate"]
    assert ambiguous["candidateStatus"] == "ambiguous"
    assert ambiguous["candidateMatchCount"] == 2
    assert {
        row["candidateReferencedOwner"] for row in ambiguous["candidateMatches"]
    } == {"Pkg.Left", "Pkg.Right"}
    assert ambiguous["candidateReferencedOwner"] is None
    unresolved = commands["Nat"]
    assert unresolved["candidateStatus"] == "unresolved"
    assert unresolved["candidateMatches"] == []
    assert unresolved["resultStatus"] == "unavailable"


def _v3_sections(result) -> dict:
    """Return current additive report sections for pipeline integration tests."""

    return build_report_v3(
        result.to_report_model(),
        projection="full",
    ).to_dict()["sections"]


def write_partial_index_audit_fixture(root: Path) -> None:
    """Write one readable owner plus an unreadable inventory member."""

    package = root / "Pkg"
    package.mkdir()
    (package / "Audit.lean").write_text(
        """\
import Pkg.Known
import Pkg.Unreadable
#check Shared.value
#check Missing.value
set_option maxHeartbeats 0 in
""",
        encoding="utf-8",
    )
    (package / "Known.lean").write_text(
        """\
namespace Shared
theorem value : True := by trivial
end Shared
""",
        encoding="utf-8",
    )
    (package / "Unreadable.lean").write_bytes(b"\xff\xfe")


def assert_unavailable_candidate(command: dict, observed_matches: int) -> None:
    """Require an observed lower bound without an exact owner claim."""

    assert {
        "status": command["candidateStatus"],
        "matches": command["candidateMatchCount"],
        "owner": command["candidateReferencedOwner"],
    } == {
        "status": "unavailable",
        "matches": observed_matches,
        "owner": None,
    }
    assert_partial_source_failure_coverage(command["candidateCoverage"])


def assert_partial_source_failure_coverage(coverage: dict) -> None:
    """Require one unknown total controlled by the source failure."""

    assert coverage["totalKnown"] is False
    assert coverage["total"] is None
    assert coverage["omitted"] is None
    assert coverage["completeness"] == "partial"
    assert coverage["causes"][0]["id"] == SOURCE_FAILURE_DIAGNOSTIC


def assert_partial_audit_registration_coverage(dag: dict) -> None:
    """Require observed registrations without exact producer totals."""

    assert len(dag["auditProducerRegistrations"]["producers"]) == 2
    assert len(dag["resourceProducerRegistrations"]["producers"]) == 1
    assert_partial_source_failure_coverage(dag["audit_command_coverage"])
    assert_partial_source_failure_coverage(dag["resource_review_coverage"])


def test_partial_index_cannot_establish_unique_or_empty_audit_owners(
    tmp_path: Path,
) -> None:
    write_partial_index_audit_fixture(tmp_path)
    dag = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg.Audit",
            analysis_scope="owner",
            source_cache_enabled=False,
        )
    ).module_dag
    commands = {
        row["subject"]: row for row in dag["audit_surfaces"][0]["auditCommands"]
    }

    assert_unavailable_candidate(commands["Shared.value"], 1)
    assert_unavailable_candidate(commands["Missing.value"], 0)
    assert_partial_audit_registration_coverage(dag)


def assert_audit_owner_contract(row: dict) -> None:
    """Require lexical, containing-owner, and referenced-owner provenance."""

    fields = (
        "backend",
        "authority",
        "containingOwner",
        "containingPopulation",
        "candidateStatus",
        "candidateReferencedDeclaration",
        "candidateReferencedOwner",
        "candidateAuthority",
        "referencedDeclaration",
        "referencedOwner",
        "referencedPopulation",
    )
    assert {field: row[field] for field in fields} == {
        "backend": "text",
        "authority": "lexical_text",
        "containingOwner": "Pkg.Facade",
        "containingPopulation": "target_owned",
        "candidateStatus": "lexical_candidate",
        "candidateReferencedDeclaration": "Pkg.Owner.owner",
        "candidateReferencedOwner": "Pkg.Owner",
        "candidateAuthority": "lexical_text",
        "referencedDeclaration": "Pkg.Owner.owner",
        "referencedOwner": "Pkg.Owner",
        "referencedPopulation": "target_owned",
    }


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
