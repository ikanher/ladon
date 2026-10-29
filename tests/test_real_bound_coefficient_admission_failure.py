"""Incomplete admission keeps its process evidence and stops the rule worker."""

import pytest


@pytest.mark.parametrize('reason', ['timeout', 'memory', 'rejected'])
def test_incomplete_admission_retains_receipt_and_diagnostic(monkeypatch, reason):
    from ladon import real_bound_native_analysis as shared
    from ladon import real_bound_native_coefficient as live

    calls = []
    diagnostic = ('Stop progress and report back to user: the memory limit 12 GiB was not enough.'
                  if reason == 'memory' else reason)
    run = {'status': 'completed', 'result': {'status': 'unresolved', 'diagnostic': diagnostic},
           'processReceipt': {'timedOut': reason == 'timeout', 'memoryLimited': reason == 'memory'}}
    monkeypatch.setattr(live.production_api, '_verify_production', lambda _p: None)
    monkeypatch.setattr(live.production_api, '_current_source', lambda _p, _r: None)
    monkeypatch.setattr(live.production_api, 'replay_real_bound', lambda *_args, **_kwargs:
                        {'status': 'unresolved', 'authority': 'none', 'check': run})
    monkeypatch.setattr(shared, 'replay_real_bound', live.production_api.replay_real_bound)
    monkeypatch.setattr(live, 'check_coefficient_relation', lambda *_args, **_kwargs: calls.append('rule'))
    result = live.check_coefficient_implication({}, '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert result['rule'] is None
    assert result['relationCheckRun'] is None
    assert result['admissionCheckRun'] == run
    assert result['diagnostic'] == diagnostic
    assert calls == []
