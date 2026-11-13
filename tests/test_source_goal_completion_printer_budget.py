"""A large valid proof must not acquire omissions during closed serialization."""

from test_source_goal_completion_lean import _assert_completed, _capture, _request

from ladon.source_goal_completion import complete_source_goal


def test_large_closed_proof_replays_without_printer_omissions(tmp_path):
    text = "set_option pp.maxSteps 50\nexample : True := by\n  skip\n"
    _source, context, capture = _capture(tmp_path, text, 3, 4)
    statements = "\n".join(f"  have h{i} : True := True.intro" for i in range(440))
    term = f"by\n{statements}\n  exact h439"
    result = complete_source_goal(_request(tmp_path, context, capture, term))
    _assert_completed(result, capture)
    assert "⋯" not in result["replay"]["generatedSource"]
