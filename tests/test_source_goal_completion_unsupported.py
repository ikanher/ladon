"""Public-runner regression proposal for expected completion-helper failures.

Scripted ProcessResult values test result classification only; they are not Lean,
proof, compiler replay, or trust evidence. The fixtures are imported from the
frozen workflow test, and production internals are not mocked.
"""
from __future__ import annotations

import json

import pytest
from test_source_goal_completion_workflow import (
    _fixture,
    _source_observation,
    _valid_capture,
)

from ladon.process_supervisor import ProcessResult


@pytest.mark.parametrize(
    ("stderr", "expected_status"),
    [
        ("no goal at selected position", "unavailable"),
        ("ambiguous source observations", "unavailable"),
        ("unrelated Lean helper failure", "process-failed"),
    ],
)
def test_expected_observation_failures_are_unavailable_but_other_failures_stay_errors(
    tmp_path, monkeypatch, stderr, expected_status,
):
    repo, source_path, context, capture_request, capture_source_goal = _fixture(
        tmp_path, monkeypatch,
    )
    capture = _valid_capture(context, source_path, capture_source_goal, capture_request)
    from ladon.source_goal_completion import (
        SourceGoalCompletionRequest,
        complete_source_goal,
    )

    request = SourceGoalCompletionRequest(
        repo_root=repo, capture=capture, term="True.intro", toolchain=context,
    )

    def runner(command, **options):
        text = options["input_bytes"].decode()
        if text.startswith("LADON_GOAL_REQUEST "):
            payload = json.loads(text.split(" ", 1)[1])
            output = _source_observation(payload, context)
            return ProcessResult(tuple(command), 0, output, "", 0.01, peak_rss_bytes=1024)
        assert text.startswith("LADON_COMPLETION_REQUEST ")
        return ProcessResult(
            tuple(command), 1, "", stderr, 0.01, peak_rss_bytes=1024,
        )

    result = complete_source_goal(request, runner=runner)

    assert result["status"] == expected_status
    assert result["application"] is None
    assert result["replay"]["status"] == "not-run"
    assert result["trust"]["accepted"] is False
    assert result["trust"]["coverage"] == "unavailable"
    assert len(result["processReceipts"]) == 3
