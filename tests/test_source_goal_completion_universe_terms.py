"""Submitted terms use universe names from the captured original context."""

from test_source_goal_completion_lean import _assert_completed, _capture, _request
from test_source_goal_completion_universes import SOURCE

from ladon.source_goal_completion import complete_source_goal


def test_submitted_term_can_name_original_universes(tmp_path):
    _source, context, capture = _capture(tmp_path, SOURCE, 3, 4)
    term = "fun (α : Type u) (β : Type v) (a : α) (_b : β) => a"
    result = complete_source_goal(_request(tmp_path, context, capture, term))
    _assert_completed(result, capture)
    assert result["trust"]["observedAxioms"] == []
