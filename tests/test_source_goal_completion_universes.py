"""Polymorphic completion retains distinct universes through empty-scope replay."""

from test_source_goal_completion_lean import _assert_completed, _capture, _request

from ladon.source_goal_completion import complete_source_goal

SOURCE = """universe u v
example : ∀ (α : Type u) (β : Type v), α → β → α := by
  skip
"""


def test_polymorphic_completion_preserves_independent_universes(tmp_path):
    source, context, capture = _capture(tmp_path, SOURCE, 3, 4)
    term = "fun α β (a : α) (_b : β) => a"
    result = complete_source_goal(_request(tmp_path, context, capture, term))
    _assert_completed(result, capture)
    assert result["application"]["residualGoals"] == []
    assert result["trust"]["observedAxioms"] == []
    assert "Type u" in result["replay"]["generatedSource"]
    assert "Type v" in result["replay"]["generatedSource"]
    assert source.read_text() == SOURCE
