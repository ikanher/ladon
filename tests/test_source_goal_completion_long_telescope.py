"""Completion must not inherit the separate slice traversal depth allowance."""

from test_source_goal_completion_lean import _assert_completed, _capture, _request

from ladon.source_goal_completion import complete_source_goal


def test_completion_preserves_long_telescope_support(tmp_path):
    binders = " ".join(f"(n{i} : Nat)" for i in range(70))
    text = f"example : ∀ {binders}, True := by\n  skip\n"
    source, context, capture = _capture(tmp_path, text, 2, 4)
    term = f"fun {binders} => True.intro"
    result = complete_source_goal(_request(tmp_path, context, capture, term))
    _assert_completed(result, capture)
    assert result["trust"]["observedAxioms"] == []
    assert source.read_text() == text
