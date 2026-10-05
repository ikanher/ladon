"""No source capture may be published after bounded execution or invalid input."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import ProcessResult

pytestmark = pytest.mark.skipif(shutil.which("lean") is None, reason="Lean toolchain unavailable")
FIXTURE = Path(__file__).parent / "fixtures" / "lean_integration"


@pytest.fixture
def capture_request(tmp_path):
    from ladon.source_goal_capture import SourceGoalCaptureRequest

    prefix = subprocess.run(
        ["lean", "--print-prefix"], cwd=FIXTURE, capture_output=True,
        text=True, check=True, timeout=15,
    ).stdout.strip()
    lean = Path(prefix) / "bin/lean"
    shutil.copy2(FIXTURE / "lean-toolchain", tmp_path / "lean-toolchain")
    (tmp_path / "Owner.lean").write_text("example : True := by\n  skip\n")
    context = resolve_toolchain_context(
        tmp_path, lake_path=lean.with_name("lake"), lean_path=lean,
    )
    return SourceGoalCaptureRequest(
        repo_root=tmp_path, source_path="Owner.lean", module="Owner",
        line=2, column=6, toolchain=context,
    )


@pytest.mark.parametrize(("flag", "status"), [
    ("timed_out", "timeout"), ("memory_limited", "memory-limit"),
    ("output_limited", "output-limit"), (None, "process-failed"),
])
def test_bounded_process_failure_never_returns_capture(capture_request, flag, status):
    from ladon.source_goal_capture import capture_source_goal

    calls = []

    def failed(command, **options):
        calls.append((command, options))
        flags = {flag: True} if flag else {}
        return ProcessResult(
            tuple(command), 1, "", "bounded failure", 0.25,
            peak_rss_bytes=1024, **flags,
        )

    result = capture_source_goal(capture_request, runner=failed)
    assert result["status"] == status, result
    assert result["capture"] is None
    assert result["resourceAccounting"]["peakRssBytes"] == 1024
    assert len(calls) == 1
    assert calls[0][1]["max_rss_bytes"] == 32 * 1024**3


@pytest.mark.parametrize("text", ["{}", "not a frame", "LADON_GOAL_FRAME {}"])
def test_unbound_helper_output_never_becomes_source_evidence(capture_request, text):
    from ladon.source_goal_capture import capture_source_goal

    def unbound(command, **_options):
        return ProcessResult(tuple(command), 0, text, "", 0.1, peak_rss_bytes=1024)

    result = capture_source_goal(capture_request, runner=unbound)
    assert result["status"] == "unavailable", result
    assert result["capture"] is None


def test_stale_expected_digest_is_rejected_before_execution(capture_request):
    from ladon.source_goal_capture import capture_source_goal

    def unexpected(*_args, **_kwargs):
        pytest.fail("stale source must fail before execution")

    result = capture_source_goal(
        replace(capture_request, expected_source_digest="sha256:" + "0" * 64),
        runner=unexpected,
    )
    assert result["status"] == "stale", result
    assert result["capture"] is None


@pytest.mark.parametrize("path", ["../Owner.lean", "/tmp/Owner.lean"])
def test_escaping_source_path_cannot_execute(capture_request, path):
    from ladon.source_goal_capture import capture_source_goal

    def unexpected(*_args, **_kwargs):
        pytest.fail("unsafe source path must fail before execution")

    result = capture_source_goal(replace(capture_request, source_path=path), runner=unexpected)
    assert result["status"] == "unavailable", result
    assert result["capture"] is None
