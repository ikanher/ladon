"""Outer stops preserve the lease and clean nested scratch without promotion."""

from pathlib import Path

import pytest

from ladon import real_prose_connection as api
from ladon.bounded_json_transport import unpack_json
from ladon.process_supervisor import ProcessResult
from ladon.real_prose_connection_inputs import REQUEST_SCHEMA


@pytest.mark.parametrize('flag', ['timed_out','memory_limited','output_limited'])
def test_outer_stop_cleans_owned_workspace_and_never_claims_connection(tmp_path,monkeypatch,flag):
    seen = {}
    def stop(command,**options):
        job = unpack_json(options['input_bytes'])
        workspace = Path(job['workspace'])
        nested = workspace/'scratch'/'child'
        nested.mkdir(parents=True)
        (nested/'partial').write_text('untrusted partial receipt')
        seen.update({'workspace':workspace,'options':options,'job':job})
        return ProcessResult(tuple(command),-1,'','',0.1,peak_rss_bytes=123,**{flag:True})
    monkeypatch.setattr(api,'run_bounded_target_process',stop)
    request = {'schema':REQUEST_SCHEMA,'term':'by intro h; exact h','premises':[]}
    result = api.connect_real_prose_bound({}, {},tmp_path,tmp_path,request,timeout_seconds=30)
    assert result['status'] == 'unavailable' and result['authority'] == 'none'
    assert 'Stop progress and report back to user' in result['check']['diagnostic']
    assert not seen['workspace'].exists()
    assert seen['options']['timeout_seconds'] <= 30
    assert seen['options']['max_rss_bytes'] == 12*1024**3
    assert seen['options']['max_output_bytes'] == 8*1024**2
    assert seen['job']['deadlineMonotonic'] == seen['job']['startedMonotonic']+30


def test_profile_caps_cannot_be_increased(tmp_path):
    request = {'schema':REQUEST_SCHEMA,'term':'by trivial','premises':[]}
    for limits in [{'timeout_seconds':601},{'max_rss_bytes':12*1024**3+1},
                   {'max_output_bytes':8*1024**2+1}]:
        with pytest.raises(ValueError):
            api.connect_real_prose_bound({}, {},tmp_path,tmp_path,request,**limits)


def test_preparation_expiration_returns_stop_guidance_without_launch(tmp_path,monkeypatch):
    calls = []
    clock = iter([10.0,12.0])
    monkeypatch.setattr(api.time,'monotonic',lambda:next(clock,12.0))
    def forbidden(*_args,**_kwargs):
        calls.append(True)
        raise AssertionError('expired request launched a worker')
    monkeypatch.setattr(api,'run_bounded_target_process',forbidden)
    request = {'schema':REQUEST_SCHEMA,'term':'by trivial','premises':[]}
    result = api.connect_real_prose_bound({}, {},tmp_path,tmp_path,request,timeout_seconds=1)
    assert result['status'] == 'unavailable'
    assert 'Stop progress and report back to user' in result['check']['diagnostic']
    assert calls == []
