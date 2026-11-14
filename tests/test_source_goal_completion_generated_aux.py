"""Auxiliaries generated while checking must be available to independent replay."""
from test_source_goal_completion_lean import _assert_completed, _capture, _request

from ladon.source_goal_completion import complete_source_goal


def test_generated_theorem_is_exported_for_replay(tmp_path):
    source='import Lean\nexample : True := by\n  skip\n'
    _source,context,capture=_capture(tmp_path,source,3,6)
    term='''by
  run_tac
    Lean.addDecl (.thmDecl {
      name := `CompletionAux
      levelParams := []
      type := Lean.mkConst ``True
      value := Lean.mkConst ``True.intro })
  exact CompletionAux'''
    result=complete_source_goal(_request(tmp_path,context,capture,term))
    _assert_completed(result,capture)
    assert result['trust']['observedAxioms']==[]


def test_generated_axiom_is_preserved_and_rejected_by_trust(tmp_path):
    source='import Lean\nexample : True := by\n  skip\n'
    _source,context,capture=_capture(tmp_path,source,3,6)
    term='''by
  run_tac
    Lean.addDecl (.axiomDecl {
      name := `CompletionAxiom
      levelParams := []
      type := Lean.mkConst ``True
      isUnsafe := false })
  exact CompletionAxiom'''
    result=complete_source_goal(_request(tmp_path,context,capture,term))
    assert result['status']=='trust-rejected',result
    assert result['replay']['status']=='accepted'
    assert result['trust']['accepted'] is False
    assert 'CompletionAxiom' in result['trust']['observedAxioms']
