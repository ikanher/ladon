"""Proposed 12 GiB public memory-limit contract tests; isolated from authoritative tests."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.process_supervisor import ProcessResult

GIB = 1024**3
MIB = 1024**2


def test_theorem_cli_omission_and_explicit_override_reach_api(monkeypatch, capsys):
    import ladon.theorem_cli as cli

    observed = []
    monkeypatch.setattr(cli, "_validate_plan_output", lambda *_args: None)
    monkeypatch.setattr(cli, "_write_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_render_plan", lambda _plan: "plan")

    class Plan:
        def to_payload(self):
            return {}

    def plan(_root, _theorem, **kwargs):
        observed.append(kwargs["max_rss_bytes"])
        return Plan()

    monkeypatch.setattr(cli, "plan_theorem_capsule", plan)
    assert cli.theorem_main(["plan", "Pkg.target"]) == 0
    assert cli.theorem_main(["plan", "Pkg.target", "--max-rss-mib", "32768"]) == 0
    assert observed == [12 * GIB, 32 * GIB]
    assert capsys.readouterr().err == ""


def test_theorem_api_omission_defaults_to_12_gib():
    from inspect import signature

    from ladon.theorem_capsule_planning import plan_theorem_capsule
    from ladon.theorem_capsule_replay import replay_theorem_capsule

    for function in (plan_theorem_capsule, replay_theorem_capsule):
        assert signature(function).parameters["max_rss_bytes"].default == 12 * GIB


def test_semantic_public_request_defaults_to_12_gib_and_keeps_override(tmp_path):
    from ladon.semantic_candidate_worker import SemanticCandidateRequest

    def make(**kwargs):
        return SemanticCandidateRequest(
            repo_root=tmp_path, module="Main", goal="True", candidate="Main.proof", **kwargs
        )

    assert make().max_rss_bytes == 12 * GIB
    assert make(max_rss_bytes=32 * GIB).max_rss_bytes == 32 * GIB


def _source_request(tmp_path):
    if shutil.which("lean") is None:
        pytest.skip("Lean toolchain unavailable")
    from ladon.lean_toolchain import resolve_toolchain_context
    from ladon.source_goal_capture import SourceGoalCaptureRequest

    fixture = _repo_root() / "tests" / "fixtures" / "lean_integration"
    prefix = subprocess.run(
        ["lean", "--print-prefix"], cwd=fixture, capture_output=True,
        text=True, check=True, timeout=15,
    ).stdout.strip()
    lean = Path(prefix) / "bin/lean"
    shutil.copy2(fixture / "lean-toolchain", tmp_path / "lean-toolchain")
    (tmp_path / "Owner.lean").write_text("example : True := by\n  skip\n")
    context = resolve_toolchain_context(tmp_path, lake_path=lean.with_name("lake"), lean_path=lean)
    args = {"repo_root": tmp_path, "source_path": "Owner.lean", "module": "Owner",
            "line": 2, "column": 6, "toolchain": context}
    return SourceGoalCaptureRequest(**args)


def _repo_root():
    for parent in Path(__file__).resolve().parents:
        if (parent / "src").is_dir() and (parent / "tests").is_dir():
            return parent
    raise AssertionError("repository root not found")


def test_source_public_request_defaults_to_12_gib_and_keeps_override(tmp_path):
    from dataclasses import replace

    request = _source_request(tmp_path)
    assert request.max_rss_bytes == 12 * GIB
    assert replace(request, max_rss_bytes=32 * GIB).max_rss_bytes == 32 * GIB


def test_semantic_memory_failure_reports_actionable_configured_and_measured_limit(tmp_path):
    from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

    request = SemanticCandidateRequest(
        repo_root=tmp_path, module="Main", goal="True", candidate="Main.proof",
        max_rss_bytes=12 * GIB,
    )

    def limited(command, **_kwargs):
        return ProcessResult(tuple(command), 1, "", "", 0.1,
                             peak_rss_bytes=13 * GIB, memory_limited=True)

    result = check_semantic_candidate(request, runner=limited).to_dict()
    diagnostic = result["diagnostic"]
    message = diagnostic["message"]
    assert result["status"] == "memory-limited"
    assert message.startswith("Stop progress and report back to user:")
    assert "12 gib" in message.lower() or "12288 mib" in message.lower()
    assert "13312 mib" in message.lower() or str(13 * GIB) in message
    assert "--max-rss-mib" in message
    assert "ask the user before retrying" in message.lower()


def test_source_memory_failure_reports_actionable_configured_and_measured_limit(tmp_path):
    from ladon.source_goal_capture import capture_source_goal

    capture_request = _source_request(tmp_path)

    def limited(command, **_kwargs):
        return ProcessResult(tuple(command), 1, "", "", 0.1,
                             peak_rss_bytes=13 * GIB, memory_limited=True)

    result = capture_source_goal(capture_request, runner=limited)
    message = result["diagnostic"]["message"]
    assert result["status"] == "memory-limit"
    assert message.startswith("Stop progress and report back to user:")
    assert "12 gib" in message.lower() or "12288 mib" in message.lower()
    assert "13312 mib" in message.lower() or str(13 * GIB) in message
    assert "--max-rss-mib" in message
    assert "ask the user before retrying" in message.lower()


def test_theorem_replay_memory_error_is_reportable_with_cap_and_measured_peak(monkeypatch, tmp_path):
    from types import SimpleNamespace

    import ladon.theorem_capsule_replay as replay

    plan = SimpleNamespace(
        payload={
            "buildGraph": {"externalImports": [], "modules": []},
            "toolchain": {},
            "semanticGraph": {"trustFrontier": []},
        },
        identity="plan-id",
        target={"name": "Main.target", "module": "Main", "path": "Main.lean"},
    )
    manifest = SimpleNamespace(identity="capsule-id")

    def limited(*_args, **_kwargs):
        return ProcessResult(("lake", "build"), 1, "", "", 0.1,
                             peak_rss_bytes=13 * GIB, memory_limited=True)

    monkeypatch.setattr(replay, "run_bounded_target_process", limited)
    result = replay._execute_replay(
        manifest, plan, tmp_path, 120, 12 * GIB, "deny", {"passed": True}
    )
    assert result["status"] == "resource-limit"
    row = result["stages"][0]
    assert row["memoryLimited"] is True
    assert row["peakRssBytes"] == 13 * GIB
    diagnostic = row.get("diagnostic", "")
    assert diagnostic.startswith("Stop progress and report back to user:")
    assert "12 gib" in diagnostic.lower() or "12288 mib" in diagnostic.lower()
    assert "--max-rss-mib" in diagnostic
    assert "ask the user before retrying" in diagnostic.lower()


def test_unknown_peak_diagnostic_does_not_invent_a_measurement(tmp_path):
    from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

    request = SemanticCandidateRequest(
        repo_root=tmp_path, module="Main", goal="True", candidate="Main.proof",
        max_rss_bytes=32 * GIB,
    )

    def limited(command, **_kwargs):
        return ProcessResult(tuple(command), 1, "", "", 0.1, memory_limited=True)

    result = check_semantic_candidate(request, runner=limited).to_dict()
    message = result["diagnostic"]["message"]
    assert message.startswith("Stop progress and report back to user:")
    assert "32 gib" in message.lower() or "32768 mib" in message.lower()
    assert "peak" not in message.lower()
    assert "ask the user before retrying" in message.lower()
