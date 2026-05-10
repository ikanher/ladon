from __future__ import annotations

from pathlib import Path

from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule
from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def test_pipeline_payload_includes_quality_baseline() -> None:
    payload = run_pipeline(RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")).to_report_payload()

    assert payload["quality_baseline"]["method"] == "project_local_metric_distribution"
    assert "module_fan_in" in payload["quality_baseline"]["metrics"]


def test_findings_receive_quality_baseline_calibration() -> None:
    declarations = {
        "Tiny.root": LeanDeclaration(
            name="Tiny.root",
            module="Tiny",
            references=(
                "Tiny.a",
                "Tiny.b",
                "Tiny.c",
                "Tiny.d",
                "Tiny.e",
                "Tiny.f",
            ),
        ),
        **{
            f"Tiny.{name}": LeanDeclaration(name=f"Tiny.{name}", module="Tiny")
            for name in ("a", "b", "c", "d", "e", "f")
        },
    }
    modules = {
        "Tiny": LeanModule(
            name="Tiny",
            path="Tiny.lean",
            declarations=tuple(declarations),
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

    fan_out = next(
        finding
        for finding in payload["findings"]
        if finding["kind"] == "declaration_fan_out_hotspot"
    )
    assert fan_out["baseline"]["metric"] == "declaration_fan_out"
    assert fan_out["baseline"]["rank_desc"] == 1
    assert "Quality Baseline" in render_text(payload)
    assert "declaration_fan_out pctl=" in render_text(payload)
