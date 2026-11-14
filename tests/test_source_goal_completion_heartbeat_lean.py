"""A caller budget limits checking; acceptance still needs replay and trust."""
from dataclasses import replace

from test_source_goal_completion_lean import _assert_completed, _capture, _request

from ladon.source_goal_completion import complete_source_goal


def test_low_budget_exhausts_and_default_completes_same_source_goal(tmp_path):
    text='import Lean\nexample : True := by\n  skip\n'
    _source,context,capture=_capture(tmp_path,text,3,6)
    term='by\n  run_tac\n    for _ in [:10000] do\n      let _ ← Lean.Meta.isDefEq (Lean.mkConst ``True) (Lean.mkConst ``True)\n      pure ()\n  exact True.intro'
    req=_request(tmp_path,context,capture,term)
    low=complete_source_goal(replace(req,max_heartbeats=1))
    assert low['status'] in {'rejected','process-failed'}, low
    assert 'heartbeat' in str(low['diagnostic']).lower()
    assert low['replay']['status']=='not-run'
    assert low['trust']['accepted'] is False
    default=complete_source_goal(req)
    _assert_completed(default,capture)
    assert default['resourceAccounting']['maxHeartbeats']==800000
