"""Completion must preserve instance names needed by later binder types."""

import pytest

from ladon.source_goal_completion import complete_source_goal
from test_source_goal_completion_lean import _assert_completed, _capture, _request

SOURCE = """class Carrier (α : Type) where
  value : α
class Ready (α : Type) [Carrier α] : Prop where
  ready : True
example : ∀ {α : Type} [c : Carrier α] [r : @Ready α c], True → True := by
  skip
"""


@pytest.mark.parametrize("body", ["h", "@Ready.ready α c r"])
def test_completion_roundtrips_dependent_instance_binders(tmp_path, body):
    source, context, capture = _capture(tmp_path, SOURCE, 6, 4)
    term = f"fun {{α : Type}} [c : Carrier α] [r : @Ready α c] (h : True) => {body}"
    result = complete_source_goal(_request(tmp_path, context, capture, term))
    _assert_completed(result, capture)
    assert result["application"]["residualGoals"] == []
    assert result["trust"]["observedAxioms"] == []
    assert source.read_text() == SOURCE
