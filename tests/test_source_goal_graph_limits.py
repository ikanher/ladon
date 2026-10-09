"""Compact structural graphs preserve the declared helper output bound."""
from test_source_goal_completion_lean import _capture

from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal


def test_real_graph_capture_still_rejects_an_undersized_output_budget(tmp_path):
    _, context, _ = _capture(tmp_path, 'example : True := by\n  skip\n', 2, 6)
    result = capture_source_goal(SourceGoalCaptureRequest(
        repo_root=tmp_path, source_path='Owner.lean', module='Owner',
        line=2, column=6, toolchain=context, max_output_bytes=1024,
    ))
    assert result['status'] == 'output-limit', result
    assert result['capture'] is None
    assert result['diagnostic']['outputSize']['maxOutputBytes'] == 1024
    assert result['processReceipts'][0]['outputLimited'] is True
