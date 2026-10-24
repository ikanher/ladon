"""Memory exhaustion remains visible through user-facing result projections."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from ladon.process_supervisor import ProcessResult

GIB = 1024**3
PREFIX = "Stop progress and report back to user:"


def _limited(command=("lean",), **_kwargs):
    return ProcessResult(tuple(command), -9, "original stdout", "original stderr", 0.1,
                         memory_limited=True, peak_rss_bytes=13 * GIB)


def test_analysis_rss_failure_reports_actual_override(monkeypatch):
    from ladon.progress import ResourceLimitExceeded, RunBudget, RunLimits

    monkeypatch.setattr("ladon.progress.process_tree_rss_bytes", lambda _pid: 33 * GIB)
    with pytest.raises(ResourceLimitExceeded) as error:
        RunBudget(RunLimits(rss_bytes=32 * GIB)).check("extract")
    assert error.value.kind == "process_tree_rss"
    assert str(error.value).startswith(PREFIX)
    assert "32 GiB" in str(error.value)
    assert str(33 * GIB) in str(error.value)
    assert "--max-rss-mib" in str(error.value)


def test_proof_slice_failure_reports_fixed_limit_without_changing_streams(tmp_path, monkeypatch):
    from ladon import _proof_slice_runtime as runtime

    monkeypatch.setattr(runtime, "run_bounded_target_process", _limited)
    result = {"frontiers": [], "processReceipts": []}
    runner = runtime.SliceRunner(tmp_path, SimpleNamespace(command=("lean",)), {}, result)
    process = runner.run(["helper.lean"])
    frontier = json.dumps(result["frontiers"])
    assert not process.succeeded
    assert PREFIX in frontier
    assert "12 GiB" in frontier
    assert "--max-rss-mib" not in frontier
    assert process.stdout == "original stdout"
    assert process.stderr == "original stderr"
    assert result["processReceipts"][0]["stderr"] == "original stderr"


def test_preparation_failure_reports_fixed_limit():
    from ladon.correspondence_preparation import SourcePreparationFailure

    error = SourcePreparationFailure(_limited())
    assert str(error).startswith(PREFIX)
    assert "12 GiB" in str(error)
    assert "--max-rss-mib" not in str(error)
    assert error.process.memory_limited


def test_source_completion_keeps_stop_message(tmp_path, monkeypatch):
    from test_source_goal_completion_workflow import _workflow

    result, sequence, _source, _request = _workflow(
        tmp_path, monkeypatch, application_limit="memory_limited",
    )
    assert result["status"] == "memory-limit"
    assert result["diagnostic"]["message"].startswith(PREFIX)
    assert "12 GiB" in result["diagnostic"]["message"]
    assert [kind for kind, _ in sequence][-1] == "application"


def test_source_association_keeps_stop_message(tmp_path):
    from test_source_association import _api, _context, _request, _stored_checked_artifacts

    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    result = capture(_request(tmp_path, context, artifacts), artifacts, process_runner=_limited)
    assert result["status"] == "memory-limited"
    assert result["diagnostic"]["message"].startswith(PREFIX)
    assert "12 GiB" in result["diagnostic"]["message"]
    assert result["artifacts"] == []


@pytest.mark.parametrize("stdout", ["", "LADON_FRAME {truncated"])
def test_batch_memory_exhaustion_keeps_stop_message(tmp_path, stdout):
    from ladon.semantic_candidate_batch_worker import check_semantic_candidates
    from ladon.semantic_candidate_worker import SemanticCandidateRequest

    request = SemanticCandidateRequest(tmp_path, "Main", "True", "Main.fact")

    def limited(command, **_kwargs):
        return ProcessResult(tuple(command), -9, stdout, "", 0.1,
                             memory_limited=True, peak_rss_bytes=13 * GIB)

    result = check_semantic_candidates(request, ["Main.fact"], runner=limited)
    assert result.status != "available"
    assert result.diagnostic["message"].startswith(PREFIX)
    assert "12 GiB" in result.diagnostic["message"]
    assert not result.terminal


def test_scratch_failure_keeps_stop_message(tmp_path, monkeypatch):
    from ladon import scratch_replay

    monkeypatch.setattr(scratch_replay, "prepare_direct_lean_execution",
                        lambda *_args, **_kwargs: SimpleNamespace(command=("lean",), environment={}))
    result = scratch_replay.replay_scratch(
        repo_root=tmp_path, module="Main", goal="True", candidate="True.intro",
        toolchain=SimpleNamespace(), runner=_limited,
    )
    assert result.status == "memory-limited"
    assert result.diagnostic.startswith(PREFIX)
    assert "12 GiB" in result.diagnostic


def test_theorem_text_replay_exposes_stage_memory_diagnostic(monkeypatch, capsys):
    from ladon.theorem_cli import theorem_main

    message = PREFIX + " the 12 GiB process-memory limit was exceeded."
    receipt = {"status": "resource-limit", "stages": [{"memoryLimited": True,
                                                       "diagnostic": message}]}
    monkeypatch.setattr("ladon.theorem_capsule_replay.replay_theorem_capsule",
                        lambda *_args, **_kwargs: receipt)
    assert theorem_main(["replay", "/unused/capsule", "--format", "text"]) != 0
    assert message in capsys.readouterr().out


def test_timeout_does_not_claim_memory_exhaustion(tmp_path):
    from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

    request = SemanticCandidateRequest(tmp_path, "Main", "True", "Main.fact")

    def timeout(command, **_kwargs):
        return ProcessResult(tuple(command), -9, "", "", 0.1, timed_out=True)

    result = check_semantic_candidate(request, runner=timeout)
    assert result.status == "timeout"
    assert PREFIX not in result.diagnostic["message"]
