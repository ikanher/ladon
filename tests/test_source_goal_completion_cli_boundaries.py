"""Completion CLI input ownership, rendering and operational exit boundaries."""
from __future__ import annotations

import json

import pytest

from ladon.proof_search_cli import build_proof_search_parser
from ladon.proof_search_goal_cli import dispatch_goal
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_terminal import semantic_payload_failed


def _args(tmp_path, payload, output="-"):
    repo = tmp_path / "repo"
    repo.mkdir()
    capture = tmp_path / "capture.json"
    capture.write_text(json.dumps(payload))
    args = build_proof_search_parser().parse_args([
        "goal", "complete", "--repo-root", str(repo), "--capture-file", str(capture),
        "--term", "True.intro", "--lean-path", "/nonexistent/lean",
        "--lake-path", "/nonexistent/lake", "--output", str(output),
    ])
    return args, repo, capture


@pytest.mark.parametrize("payload", [
    {}, {"schema": "ladon-semantic-candidate-check-result-v1", "status": "accepted"},
    {"schema": "ladon-source-goal-capture-result-v1", "status": "unavailable", "capture": None},
])
def test_incompatible_capture_files_fail_before_toolchain_resolution(tmp_path, payload):
    args, repo, _ = _args(tmp_path, payload)
    with pytest.raises(ProofSearchIndexError) as caught:
        dispatch_goal(args, repo)
    assert caught.value.code == "completion-capture-input"


def test_completion_report_cannot_replace_capture_input(tmp_path):
    args, repo, capture = _args(tmp_path, {})
    original = capture.read_bytes()
    args.output = str(capture)
    with pytest.raises(ProofSearchIndexError) as caught:
        dispatch_goal(args, repo)
    assert caught.value.code == "source-report-destination"
    assert capture.read_bytes() == original


def test_completion_text_prints_actual_residual_and_never_claims_completed():
    from ladon.source_goal_completion_cli import render_completion_text

    payload = {
        "status": "incomplete", "captureId": "captured", "termDigest": "term",
        "application": {"status": "incomplete", "originalGoal": {"typeDisplay": "goal"},
                        "residualGoals": [{"goalId": "remaining", "typeDisplay": "0 ≤ gap", "localContext": []}]},
        "replay": {"status": "not-run", "coverage": "unavailable"},
        "trust": {"accepted": False, "coverage": "unavailable", "observedAxioms": None},
        "diagnostic": None,
    }
    text = render_completion_text(payload)
    assert "incomplete" in text
    assert "0 ≤ gap" in text
    assert "not-run" in text
    assert "completed" not in text.lower()


@pytest.mark.parametrize("status", ["completed", "incomplete", "rejected", "trust-rejected"])
def test_observed_mathematical_outcomes_are_not_operational_failure(status):
    assert semantic_payload_failed("goal.complete", {"status": status}) is False


@pytest.mark.parametrize("status", ["stale", "unavailable", "timeout", "memory-limit", "output-limit", "process-failed"])
def test_unavailable_completion_has_operational_exit(status):
    assert semantic_payload_failed("goal.complete", {"status": status}) is True
