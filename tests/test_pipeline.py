from __future__ import annotations

from pathlib import Path

from ladon.analysis.generated_family_candidate_profile import (
    COMMAND_SKELETON_VERSION,
)
from ladon.extraction import discover_modules, parse_lean_module
from ladon.pipeline import (
    REQUIRED_PHASES,
    RunContext,
    adapt_modules,
    run_pipeline,
)
from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule
from ladon.render import render_text


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def _write_command_skeleton_family(repo: Path) -> None:
    """Write a declaration-free numbered family for the ordinary text route."""

    rows = repo / "Neutral" / "Rows"
    rows.mkdir(parents=True)
    data = repo / "Neutral" / "Data.lean"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("#check Nat\n", encoding="utf-8")
    for index in range(5):
        source = "import Neutral.Data\n#check Nat\n" if index < 4 else "#check Bool\n"
        (rows / f"Cell{index}.lean").write_text(source, encoding="utf-8")


def _selected_candidate_feature(
    analysis: dict,
    candidate: dict,
) -> dict:
    partition = next(
        row for row in analysis["partitions"] if row["id"] == candidate["partitionId"]
    )
    return next(
        row
        for row in partition["features"]
        if row["id"] == candidate["lexicalFeatureId"]
    )


def _assert_command_skeleton_candidate(
    analysis: dict,
    candidate: dict,
) -> None:
    selected = _selected_candidate_feature(analysis, candidate)
    assert len(analysis["candidates"]) == 1
    assert [row["module"] for row in candidate["members"]] == [
        f"Neutral.Rows.Cell{index}" for index in range(5)
    ]
    assert all(not row["declarationStems"] for row in candidate["members"])
    assert selected["kind"] == "command_skeleton"
    assert selected["version"] == COMMAND_SKELETON_VERSION
    assert selected["memberCount"] == 4


def _assert_command_skeleton_clauses(candidate: dict) -> None:
    clauses = {row["id"]: row for row in candidate["clauses"]}
    imports = clauses["common_direct_internal_import"]["operands"]
    lexical = clauses["common_lexical_witness"]["operands"]
    assert (
        imports["observedNumerator"],
        imports["observedDenominator"],
    ) == (4, 5)
    assert (
        lexical["observedNumerator"],
        lexical["observedDenominator"],
    ) == (4, 5)


def _assert_source_index_has_skeletons(context: RunContext) -> None:
    assert context.source_index is not None
    assert all(
        context.source_index.modules[f"Neutral.Rows.Cell{index}"].command_skeletons
        for index in range(5)
    )


def test_pipeline_records_required_phase_timings() -> None:
    context = RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")

    result = run_pipeline(context)

    timings = result.timing_by_phase()
    assert set(REQUIRED_PHASES).issubset(timings)
    for phase in REQUIRED_PHASES:
        assert timings[phase].name == phase
        assert timings[phase].elapsed_seconds >= 0
        assert timings[phase].status in {"ok", "skipped"}
    assert timings["lean_extraction"].status == "skipped"
    assert timings["declaration_graph"].status == "skipped"
    assert timings["findings"].status == "ok"


def test_text_pipeline_detects_declaration_free_command_skeleton_family(
    tmp_path: Path,
) -> None:
    _write_command_skeleton_family(tmp_path)
    context = RunContext(
        repo_root=tmp_path,
        analysis_scope="inventory",
        source_cache_enabled=False,
    )

    payload = run_pipeline(context).to_report_payload()
    analysis = payload["module_dag"]["generated_family_candidates"]
    candidate = analysis["candidates"][0]
    _assert_command_skeleton_candidate(analysis, candidate)
    _assert_command_skeleton_clauses(candidate)
    _assert_source_index_has_skeletons(context)


def test_pipeline_json_payload_has_additive_timing_namespace() -> None:
    context = RunContext(
        repo_root=FIXTURE_ROOT,
        requested_root="Tiny.lean",
        generated_at_utc="2026-05-10T00:00:00+00:00",
    )

    payload = run_pipeline(context).to_report_payload()

    assert payload["metadata"]["analysis_root_module"] == "Tiny"
    assert payload["module_dag"]["module_count"] == 3
    assert "pipeline" in payload
    assert "timings" in payload["pipeline"]
    assert payload["pipeline"]["timings"]["module_dag"]["status"] == "complete"
    assert payload["pipeline"]["timings"]["declaration_graph"]["status"] == "skipped"
    assert payload["pipeline"]["timings"]["architecture_policy"]["status"] == "complete"
    assert payload["architecture_policy"]["status"] == "skipped_no_policy"
    assert any(
        finding["kind"] == "architecture_policy.skipped_no_policy"
        for finding in payload["findings"]
    )


def test_pipeline_applies_architecture_policy_findings() -> None:
    context = RunContext(
        repo_root=FIXTURE_ROOT,
        requested_root="Tiny.lean",
        architecture_policy={
            "id": "tiny-policy",
            "groups": {
                "root": ["Tiny"],
                "helper": ["Tiny.Helper"],
            },
            "rules": [
                {
                    "id": "root-helper-boundary",
                    "kind": "forbid_direct_imports",
                    "from": ["root"],
                    "to": ["helper"],
                }
            ],
        },
    )

    payload = run_pipeline(context).to_report_payload()

    assert payload["architecture_policy"]["policyId"] == "tiny-policy"
    assert payload["pipeline"]["timings"]["architecture_policy"]["status"] == "complete"
    assert any(
        finding["kind"] == "architecture_policy.direct_forbidden_import"
        and finding["subject"] == "Tiny -> Tiny.Helper"
        for finding in payload["findings"]
    )


def test_pipeline_applies_source_pattern_policy_findings() -> None:
    context = RunContext(
        repo_root=FIXTURE_ROOT,
        requested_root="Tiny.lean",
        source_pattern_policy={
            "id": "tiny-source-policy",
            "patterns": [
                {
                    "id": "theorem-keyword",
                    "pattern": "theorem",
                    "kind": "keyword_scan",
                    "severity": "info",
                }
            ],
        },
    )

    payload = run_pipeline(context).to_report_payload()

    assert payload["source_patterns"]["policyId"] == "tiny-source-policy"
    assert payload["source_patterns"]["matchCount"] == 1
    assert payload["pipeline"]["timings"]["source_patterns"]["status"] == "complete"
    assert any(
        finding["kind"] == "source_pattern.match"
        and finding["sourcePath"] == "Tiny/Core.lean"
        for finding in payload["findings"]
    )


def test_pipeline_skips_source_patterns_without_policy() -> None:
    payload = run_pipeline(
        RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")
    ).to_report_payload()

    assert "source_patterns" not in payload
    assert payload["pipeline"]["timings"]["source_patterns"]["status"] == "skipped"


def test_current_extraction_modules_adapt_to_stable_ir() -> None:
    discovery = discover_modules(FIXTURE_ROOT, "Tiny.lean")

    adapted = adapt_modules(discovery.modules)

    assert adapted == discovery.modules
    assert adapted["Tiny"].imports == ("Tiny.Core", "Tiny.Helper")


def test_pipeline_reports_declaration_graph_when_lean_bundle_has_declarations() -> None:
    modules = {
        "Tiny": LeanModule(
            name="Tiny", path="Tiny.lean", declarations=("Tiny.root", "Tiny.leaf")
        )
    }
    declarations = {
        "Tiny.root": LeanDeclaration(
            name="Tiny.root",
            module="Tiny",
            references=("Tiny.leaf",),
            source_path="Tiny.lean",
            source_range={"startLine": 1, "endLine": 3},
            content_hash="sha256:tiny",
            extraction_backend="lean_parser_helper",
            extractor_version="1",
            name_resolution_method="parser_namespace_stack",
            confidence="parser_source_range",
        ),
        "Tiny.leaf": LeanDeclaration(name="Tiny.leaf", module="Tiny"),
    }

    def fake_runner(_context: RunContext, _discovered) -> ExtractionBundle:
        return ExtractionBundle(modules=modules, declarations=declarations)

    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
        )
    )
    payload = result.to_report_payload()

    assert result.timing_by_phase()["declaration_graph"].status == "ok"
    assert payload["declaration_graph"]["edge_count"] == 1
    row = payload["declaration_graph"]["declarations"][1]
    expected = {
        "declaration": "Tiny.root",
        "module": "Tiny",
        "sourcePath": "Tiny.lean",
        "sourceRange": {"startLine": 1, "endLine": 3},
        "contentHash": "sha256:tiny",
        "extractionBackend": "lean_parser_helper",
        "extractorVersion": "1",
        "nameResolutionMethod": "parser_namespace_stack",
        "confidence": "parser_source_range",
    }
    assert {key: row[key] for key in expected} == expected
    assert_parser_only_surface_is_unavailable(row)
    assert payload["declaration_graph"]["top_fan_in"][0]["declaration"] == "Tiny.leaf"


def test_declaration_population_and_ranking_use_recomputed_owned_edges() -> None:
    modules = {
        "Tiny": LeanModule(
            name="Tiny",
            path="Tiny.lean",
            declarations=("Tiny.root", "Tiny.leaf"),
        ),
        "Tiny.Generated.Row": LeanModule(
            name="Tiny.Generated.Row",
            path="Tiny/Generated/Row.lean",
            declarations=("Tiny.Generated.Row.value",),
        ),
    }
    declarations = {
        "Tiny.root": LeanDeclaration(
            name="Tiny.root",
            module="Tiny",
            references=("Tiny.leaf", "Tiny._aux", "Dep.value"),
        ),
        "Tiny.leaf": LeanDeclaration(name="Tiny.leaf", module="Tiny"),
        "Tiny._aux": LeanDeclaration(
            name="Tiny._aux",
            module="Tiny",
            compiler_generated=True,
            compiler_authority="lean_environment",
            compiler_toolchain="Lean 4.32.1",
        ),
        "Dep.value": LeanDeclaration(
            name="Dep.value",
            module="Dep",
            is_imported_stub=True,
        ),
        "Tiny.Generated.Row.value": LeanDeclaration(
            name="Tiny.Generated.Row.value",
            module="Tiny.Generated.Row",
        ),
    }

    def fake_runner(_context: RunContext, _discovered) -> ExtractionBundle:
        return ExtractionBundle(modules=modules, declarations=declarations)

    graph = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
            generated_family_policy={
                "schema": "ladon-generated-family-policy-v1",
                "families": [
                    {
                        "id": "fixture.rows",
                        "pathPatterns": ["Tiny/Generated/*.lean"],
                    }
                ],
            },
        )
    ).to_report_payload()["declaration_graph"]

    assert graph["population_calibration"]["counts"] == {
        "compiler_generated": 1,
        "imported": 1,
        "project_generated": 1,
        "target_owned": 2,
    }
    assert graph["chosen_roots"] == ["Tiny.leaf", "Tiny.root"]
    root = next(
        row
        for row in graph["top_target_owned_fan_out"]
        if row["declaration"] == "Tiny.root"
    )
    assert root["fan_out"] == 1
    assert root["rawMetric"] == 3
    assert root["exclusions"]["nonTargetOwnedEndpoints"] == 2


def assert_parser_only_surface_is_unavailable(row: dict) -> None:
    """Require explicit unavailable elaborated fields in legacy fake bundles."""

    assert row["parserCandidates"]["status"] == "unavailable"
    assert row["typeDependencies"]["status"] == "unavailable"
    assert row["valueDependencies"]["status"] == "unavailable"
    assert row["surface"]["status"] == "unavailable"


def test_text_report_renders_declaration_graph_triage_rows() -> None:
    modules = {
        "Tiny": LeanModule(
            name="Tiny",
            path="Tiny.lean",
            declarations=("Tiny.root", "Tiny.helper", "Tiny.leaf"),
        )
    }
    declarations = {
        "Tiny.root": LeanDeclaration(
            name="Tiny.root",
            module="Tiny",
            references=("Tiny.helper", "Tiny.leaf", "missing"),
        ),
        "Tiny.helper": LeanDeclaration(
            name="Tiny.helper",
            module="Tiny",
            references=("Tiny.leaf", "missing"),
        ),
        "Tiny.leaf": LeanDeclaration(name="Tiny.leaf", module="Tiny"),
    }

    def fake_runner(_context: RunContext, _discovered) -> ExtractionBundle:
        return ExtractionBundle(modules=modules, declarations=declarations)

    payload = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
        )
    ).to_report_payload()

    text = render_text(payload)

    assert "Top Declaration Fan-In\n- Tiny.leaf: 2" in text
    assert "Top Declaration Fan-Out\n- Tiny.root: 2" in text
    assert "Top Unresolved References\n- missing: 2" in text


def test_pipeline_surfaces_lean_extraction_cache_counters() -> None:
    modules = {"Tiny": LeanModule(name="Tiny", path="Tiny.lean")}

    def fake_runner(_context: RunContext, _discovered) -> ExtractionBundle:
        return ExtractionBundle(
            modules=modules,
            declarations={},
            counters={"lean_cache_hits": 2, "lean_cache_misses": 1},
        )

    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
        )
    )
    counters = result.timing_by_phase()["lean_extraction"].counters

    assert counters["lean_cache_hits"] == 2
    assert counters["lean_cache_misses"] == 1


def test_lean_root_backend_preserves_text_module_inventory() -> None:
    modules = {
        "Tiny": LeanModule(
            name="Tiny",
            path="Tiny.lean",
            imports=("Tiny.Core",),
            declarations=("Tiny.root",),
        )
    }

    def fake_runner(_context: RunContext, _discovered) -> ExtractionBundle:
        return ExtractionBundle(modules=modules, declarations={})

    payload = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
        )
    ).to_report_payload()

    assert payload["module_dag"]["module_count"] == 3
    assert payload["module_dag"]["edges"]["Tiny"] == ["Tiny.Core"]
    assert payload["module_dag"]["edges"]["Tiny.Helper"] == ["Tiny.Core"]


def test_merge_module_inventory_prefers_helper_rows() -> None:
    from ladon.pipeline import merge_module_inventory

    text_modules = {
        "Tiny": LeanModule(name="Tiny", path="Tiny.lean", imports=("Tiny.Helper",)),
        "Tiny.Helper": LeanModule(name="Tiny.Helper", path="Tiny/Helper.lean"),
    }
    helper_modules = {
        "Tiny": LeanModule(name="Tiny", path="Tiny.lean", imports=("Tiny.Core",)),
    }

    merged = merge_module_inventory(text_modules, helper_modules)

    assert merged["Tiny"].imports == ("Tiny.Core",)
    assert "Tiny.Helper" in merged


def test_merge_module_inventory_preserves_text_navigation_rows(
    tmp_path: Path,
) -> None:
    from ladon.pipeline import merge_module_inventory

    path = tmp_path / "Pkg.lean"
    path.write_text(
        """\
namespace Pkg
set_option maxHeartbeats 0 in
@[simp] theorem routed : True := by simp
end Pkg
""",
        encoding="utf-8",
    )
    text_module = parse_lean_module(tmp_path, path)
    helper_module = LeanModule(
        name="Pkg",
        path="Pkg.lean",
        declarations=("Pkg.routed",),
    )

    merged = merge_module_inventory(
        {"Pkg": text_module},
        {"Pkg": helper_module},
    )["Pkg"]

    assert merged.scope_context_commands == text_module.scope_context_commands
    assert merged.scope_contexts == text_module.scope_contexts
    assert merged.option_rows == text_module.option_rows
    assert merged.resource_settings == text_module.resource_settings
    assert merged.proof_mechanisms == text_module.proof_mechanisms


def test_pipeline_passes_text_declaration_inventory_to_declaration_graph() -> None:
    modules = {
        "Tiny": LeanModule(
            name="Tiny",
            path="Tiny.lean",
            declarations=("Tiny.root",),
        )
    }
    declarations = {
        "Tiny.root": LeanDeclaration(
            name="Tiny.root",
            module="Tiny",
            references=("coreTruth", "TrulyMissingThing"),
        )
    }

    def fake_runner(_context: RunContext, _discovered) -> ExtractionBundle:
        return ExtractionBundle(modules=modules, declarations=declarations)

    payload = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
        )
    ).to_report_payload()

    rows = {
        row["candidate"]: row
        for row in payload["declaration_graph"]["top_unresolved_references"]
    }
    assert rows["coreTruth"]["classification"] == "known_inventory_candidate"
    assert rows["TrulyMissingThing"]["classification"] == "actionable_unknown"
