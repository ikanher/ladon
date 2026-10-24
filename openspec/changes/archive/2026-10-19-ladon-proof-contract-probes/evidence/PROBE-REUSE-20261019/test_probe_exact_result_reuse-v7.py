"""Acceptance tests for bounded exact-result reuse in application probes."""
from __future__ import annotations

from pathlib import Path

import pytest
from test_probe_reuse_support import cache as _cache
from test_probe_reuse_support import prepared as _prepared
from test_probe_reuse_support import request as _request
from test_proof_contract_application_probe_contract import api


def test_exact_cache_reuses_only_checked_goal_and_keeps_fresh_prepare(tmp_path, monkeypatch):
    _, _, _, checker = api()
    import ladon.proof_contract_probes as probes

    request = _request(tmp_path)
    cached = _cache(tmp_path, request, plan_id=None)
    stages = []

    def stage(operation, payload, owned):
        stages.append(operation)
        if operation == 'prepare-probe':
            return {'status': 'completed', 'result': _prepared(request)}
        raise AssertionError('exact cached goals must not launch checker workers')

    monkeypatch.setattr(probes, '_stage', stage)
    result = checker(request, cached['planId'], {}, cached_result=cached)
    assert result['status'] == 'checked-local-nonimplication'
    assert stages == ['prepare-probe']
    assert all(goal['status'] == 'checked-support' for goal in result['goals'])
    assert all(goal['reused'] is True for goal in result['goals'])


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(deadlineMonotonic=r['deadlineMonotonic'] + 1),
    lambda r: r.update(limits={'timeout_seconds': 20}),
    lambda r: r.update(template={**r['template'], 'direction': 'left-to-right', 'kind': 'implication'}),
    lambda r: r.update(repoRoot=str(Path(r['repoRoot']).parent / 'another-source-tree')),
])
def test_changed_plan_identity_never_reuses_cached_support(tmp_path, monkeypatch, mutation):
    _, _, _, checker = api()
    import ladon.proof_contract_probes as probes

    request = _request(tmp_path)
    cached = _cache(tmp_path, request, plan_id=None)
    mutation(request)
    monkeypatch.setattr(probes, '_stage', lambda *args: {
        'status': 'completed', 'result': _prepared(request)})
    result = checker(request, cached['planId'], {}, cached_result=cached)
    assert result['status'] == 'rejected'
    assert result['checkerAuthority'] == 'none'


def test_forged_status_or_corrupt_cached_evidence_cannot_grant_support(tmp_path, monkeypatch):
    _, _, _, checker = api()
    import ladon.proof_contract_probes as probes

    request = _request(tmp_path)
    cached = _cache(tmp_path, request, plan_id=None)
    cached['goals'][0]['result']['completion']['trust']['accepted'] = False
    cached['goals'][1]['result']['completion']['trust']['accepted'] = False
    monkeypatch.setattr(probes, '_stage', lambda operation, payload, owned: {
        'status': 'completed', 'result': _prepared(request)} if operation == 'prepare-probe'
        else {'status': 'rejected', 'result': None, 'diagnostic': 'unexpected cache miss checker'})
    result = checker(request, cached['planId'], {}, cached_result=cached)
    assert result['checkerAuthority'] == 'none'
    assert all(goal['status'] == 'unresolved' for goal in result['goals'])


def test_cached_receipt_cannot_be_transplanted_between_goals(tmp_path, monkeypatch):
    _, _, _, checker = api()
    import ladon.proof_contract_probes as probes

    request = _request(tmp_path)
    cached = _cache(tmp_path, request, plan_id=None)
    cached['goals'][0]['result'], cached['goals'][1]['result'] = (
        cached['goals'][1]['result'], cached['goals'][0]['result'])
    calls = []

    def stage(operation, payload, owned):
        calls.append(operation)
        if operation == 'prepare-probe':
            return {'status': 'completed', 'result': _prepared(request)}
        return {'status': 'rejected', 'result': None,
                'diagnostic': {'code': 'expected-cache-miss'}}

    monkeypatch.setattr(probes, '_stage', stage)
    result = checker(request, cached['planId'], {}, cached_result=cached)
    assert result['checkerAuthority'] == 'none'
    assert all(goal['reused'] is False for goal in result['goals'])
    assert calls == ['prepare-probe']


def test_expired_deadline_never_reuses_cache_or_starts_checker(tmp_path, monkeypatch):
    _, _, _, checker = api()
    import ladon.proof_contract_probes as probes

    request = _request(tmp_path)
    cached = _cache(tmp_path, request, plan_id=None)
    request['deadlineMonotonic'] = 0
    stages = []
    monkeypatch.setattr(probes, '_stage', lambda operation, payload, owned: stages.append(operation))
    result = checker(request, cached['planId'], {}, cached_result=cached)
    assert result['status'] == 'incomplete'
    assert result['checkerAuthority'] == 'none'
    assert stages == []
