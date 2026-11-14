"""Completion budgets apply outside the submitted term without changing the source capture."""
from dataclasses import replace
from pathlib import Path

import pytest
from test_source_goal_completion_api_contract import _toolchain

from ladon.proof_search_cli import build_proof_search_parser
from ladon.source_goal_completion import SourceGoalCompletionRequest, _helper_request


def test_cli_default_and_explicit_completion_budget():
    parser=build_proof_search_parser()
    argv=['goal','complete','--capture-file','capture.json','--term','True.intro',
          '--lean-path','/lean','--lake-path','/lake']
    assert parser.parse_args(argv).max_heartbeats == 800000
    assert parser.parse_args(argv+['--max-heartbeats','12345']).max_heartbeats == 12345


@pytest.mark.parametrize('budget',[0,-1,True,1.5,'800000'])
def test_invalid_api_budgets_fail_before_execution(tmp_path,budget):
    repo,_source,toolchain=_toolchain(tmp_path)
    with pytest.raises((ValueError,TypeError),match='heartbeat'):
        SourceGoalCompletionRequest(repo,{},'True.intro',toolchain,max_heartbeats=budget)


def test_request_budget_reaches_helper_without_altering_capture(tmp_path):
    from test_source_goal_completion_api_contract import _capture
    repo,source,toolchain=_toolchain(tmp_path)
    capture=_capture(toolchain,source)
    req=SourceGoalCompletionRequest(repo,capture,'True.intro',toolchain)
    assert req.max_heartbeats == 800000
    body=_helper_request(capture,Path('snapshot.lean'),req.term,req.max_heartbeats)
    assert body['maxHeartbeats']==800000
    assert capture['environment']['optionsStructural']=='[]'
    assert replace(req,max_heartbeats=12345).max_heartbeats == 12345


def test_replay_budget_covers_the_independent_compiler():
    from ladon._source_goal_completion_replay import replay_source
    frame={'directImports':[],'sourceContextModule':'PrivateContext',
           'closedTargetText':'True','closedProofText':'True.intro'}
    req={'requestId':'abc','captureId':'cap','termDigest':'term','maxHeartbeats':12345}
    source,_=replay_source(frame,req,'context')
    assert 'set_option maxHeartbeats 12345\n' in source.decode()


@pytest.mark.parametrize('budget',['0','-1','18446744073709552'])
def test_invalid_cli_budget_is_rejected_before_toolchain_resolution(tmp_path,budget,capsys):
    from ladon.entrypoint import main
    assert main(['proof-search','goal','complete','--repo-root',str(tmp_path),
                 '--capture-file','absent.json','--term','True.intro',
                 '--lean-path','/missing/lean','--lake-path','/missing/lake',
                 '--max-heartbeats',budget]) == 2
    assert 'heartbeat' in capsys.readouterr().err
