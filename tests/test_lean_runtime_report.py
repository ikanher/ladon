from __future__ import annotations

from pathlib import Path

import pytest

from ladon.cli import apply_phase_dispositions, build_parser
from ladon.cli_execution import parse_failure_selectors
from ladon.ir import ExtractionBundle, LeanModule
from ladon.lean_runtime import EXECUTION_SAFETY_WARNING
from ladon.pipeline import PipelineResult, RunContext, run_pipeline
from ladon.report_v2 import PhaseEnvelope

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def assert_partial_lean_phase(phase: PhaseEnvelope) -> None:
    """Check the partial phase status and its controlling diagnostic."""

    assert phase.status == "partial"
    assert phase.disposition == "accepted"
    assert phase.reason == (
        "lean.fixture_failure for Tiny.Helper: fixture failure"
    )
    assert phase.counters["failed"] == 1
    assert phase.diagnostics[0].identifier == "lean.fixture_failure"


def assert_partial_lean_provenance(data: dict) -> None:
    """Check runtime and cache evidence retained in the phase payload."""

    assert data["protocolVersion"] == "ladon-lean-batch-v1"
    assert data["cache"][0]["invalidationReason"] == "source_changed"
    assert data["buildInvokedByExtraction"] is False
    assert data["executionSafetyWarning"] == EXECUTION_SAFETY_WARNING


def assert_partial_lean_dispositions(result: PipelineResult) -> None:
    """Check caller-selected and strict partial-run rejection policies."""

    selected = apply_phase_dispositions(
        result.to_report_model(),
        parse_failure_selectors(["phase:lean_extraction:partial"]),
        strict_lean=False,
    )
    strict = apply_phase_dispositions(
        result.to_report_model(),
        (),
        strict_lean=True,
    )
    assert (
        selected.phases["lean_extraction"].disposition
        == "selector-rejection"
    )
    assert strict.phases["lean_extraction"].disposition == "strict-rejection"


def test_partial_runtime_surfaces_full_report_v2_provenance() -> None:
    runtime = {
        "protocolVersion": "ladon-lean-batch-v1",
        "helperVersion": "fixture-helper",
        "leanVersion": "Lean 4.fixture",
        "commandShape": ["lake", "env", "lean", "--run", "<packaged-helper>"],
        "batchSize": 8,
        "timeoutSeconds": 120.0,
        "helperElapsedSeconds": 1.25,
        "requested": 2,
        "completed": 1,
        "failed": 1,
        "timedOut": False,
        "cancelled": False,
        "cacheFingerprintVersion": "ladon-lean-cache-v2",
        "cache": [
            {
                "module": "Tiny",
                "status": "miss",
                "invalidationReason": "source_changed",
            }
        ],
        "buildRequested": False,
        "buildInvokedByExtraction": False,
        "executionSafetyWarning": EXECUTION_SAFETY_WARNING,
    }
    diagnostic = {
        "id": "lean.fixture_failure",
        "severity": "error",
        "message": "fixture failure",
        "subject": "Tiny.Helper",
    }

    def fake_runner(_context: RunContext, _discovery) -> ExtractionBundle:
        return ExtractionBundle(
            modules={"Tiny": LeanModule("Tiny", "Tiny.lean")},
            counters={"requested": 2, "completed": 1, "failed": 1},
            diagnostics=(diagnostic,),
            runtime=runtime,
        )

    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_runner,
        )
    )
    phase = result.to_report_model().phases["lean_extraction"]

    assert_partial_lean_phase(phase)
    assert_partial_lean_provenance(phase.data)
    assert_partial_lean_dispositions(result)


def test_text_backend_starts_no_lean_extractor() -> None:
    def forbidden(_context: RunContext, _discovery):
        raise AssertionError("text-only mode started a target extractor")

    result = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="text",
            lean_extractor=forbidden,
        )
    )

    assert result.timing_by_phase()["lean_extraction"].status == "skipped"


def test_cli_exposes_finite_runtime_controls_and_safety_warning() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--lean-batch-size",
            "4",
            "--lean-timeout",
            "9",
            "--lean-strict",
        ]
    )

    assert args.lean_batch_size == 4
    assert args.lean_timeout == 9
    assert args.lean_strict is True
    assert "unsafe for untrusted repositories" in parser.format_help()


def test_cli_rejects_non_amortizing_batch_size() -> None:
    with pytest.raises(SystemExit) as caught:
        build_parser().parse_args(["--lean-batch-size", "1"])

    assert caught.value.code == 2
