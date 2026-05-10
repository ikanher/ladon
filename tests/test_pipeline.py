from __future__ import annotations

from pathlib import Path

from ladon.extraction import discover_modules
from ladon.pipeline import (
    REQUIRED_PHASES,
    RunContext,
    adapt_modules,
    run_pipeline,
)
from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule
from ladon.render import render_text


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


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
    assert payload["pipeline"]["timings"]["module_dag"]["status"] == "ok"
    assert payload["pipeline"]["timings"]["declaration_graph"]["status"] == "skipped"


def test_current_extraction_modules_adapt_to_stable_ir() -> None:
    discovery = discover_modules(FIXTURE_ROOT, "Tiny.lean")

    adapted = adapt_modules(discovery.modules)

    assert adapted == discovery.modules
    assert adapted["Tiny"].imports == ("Tiny.Core", "Tiny.Helper")


def test_pipeline_reports_declaration_graph_when_lean_bundle_has_declarations() -> None:
    modules = {
        "Tiny": LeanModule(name="Tiny", path="Tiny.lean", declarations=("Tiny.root", "Tiny.leaf"))
    }
    declarations = {
        "Tiny.root": LeanDeclaration(name="Tiny.root", module="Tiny", references=("Tiny.leaf",)),
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
    assert payload["declaration_graph"]["top_fan_in"][0]["declaration"] == "Tiny.leaf"


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
