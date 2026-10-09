"""Independent replay of selected goals with preceding source declarations."""
from __future__ import annotations

from test_source_goal_completion_lean import _assert_completed, _capture, _request

from ladon.source_goal_completion import complete_source_goal


def test_preceding_definition_replays_without_compiling_unfinished_tail(tmp_path):
    text = (
        "namespace Outer.Inner\n"
        "noncomputable section\n"
        "def prior (x : Nat) : Nat := x\n"
        "example (x : Nat) : prior x = x := by\n"
        "  skip\n"
        "theorem unfinished : False := by\n"
        "  skip\n"
        "end Outer.Inner\n"
    )
    _, context, capture = _capture(tmp_path, text, 5, 6)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    result = complete_source_goal(_request(tmp_path, context, capture, "rfl"))
    _assert_completed(result, capture)
    assert result['trust']['observedAxioms'] == []
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert after == before


def test_preceding_admitted_theorem_remains_a_disallowed_dependency(tmp_path):
    text = "theorem prior : False := by sorry\nexample : False := by\n  skip\n"
    _, context, capture = _capture(tmp_path, text, 3, 6)
    result = complete_source_goal(_request(tmp_path, context, capture, "prior"))
    assert result['status'] == 'trust-rejected', result
    assert result['replay']['status'] == 'accepted'
    assert result['trust']['coverage'] == 'complete'
    assert 'sorryAx' in result['trust']['observedAxioms']
    assert result['trust']['accepted'] is False
