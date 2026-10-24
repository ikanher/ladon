"""Acceptance tests for bounded exact-result reuse in application probes."""
from __future__ import annotations

import copy
import hashlib
import time
from pathlib import Path

import pytest

from ladon._proof_contract_context_preparation import _digest
from ladon.proof_contract_probe_artifacts import application_probe_artifact
from test_proof_contract_application_probe_contract import TEMPLATE, api, fixture


def _request(tmp_path):
    data = fixture()
    return {
        'repoRoot': str(tmp_path), 'context': data['context'],
        'left': data['sides'][0], 'right': data['sides'][1],
        'template': TEMPLATE, 'deadlineMonotonic': time.monotonic() + 60,
        'limits': {},
    }


def _prepared(request):
    artifact = application_probe_artifact(request['context'], request['left'],
        request['right'], request['template'], analysis_id='analysis:reuse-test')
    return {
        'status': 'prepared', 'planId': _digest({
            'artifact': artifact['artifactId'], 'root': request['repoRoot'],
            'template': request['template'], 'deadline': request['deadlineMonotonic'],
            'limits': request['limits'],
        }),
        'artifact': artifact, 'goals': copy.deepcopy(artifact['payload']['result']['goals']),
        'binding': {}, 'adapter': {}, 'symbols': {}, 'construction': {},
        'residuals': [],
    }


def _cache(tmp_path, request, plan_id='sha256:' + 'a' * 64):
    from ladon._proof_contract_route_context_evidence import store_goal_evidence

    data = _prepared(request)
    plan_id = data['planId'] if plan_id is None else plan_id
    result = {'schema': 'ladon-application-probe-v1', 'status': 'checked-local-implication',
        'planId': plan_id, 'checkerAuthority': 'checked-local-goals',
        'goals': copy.deepcopy(data['goals']), 'residuals': [],
        'sourceFidelity': 'attributed-unreviewed', 'wholeMethodAuthority': 'none',
        'mathematicalFalsity': 'not-established', 'memoryReportBackRequired': False}
    for goal in result['goals']:
        term = 'by assumption'
        goal.update(status='checked-support', term=term)
        raw = {'status': 'supported', 'completion': {
            'status': 'completed', 'termDigest': hashlib.sha256(term.encode()).hexdigest(),
            'replay': {'status': 'accepted'}, 'trust': {'accepted': True},
        }}
        goal['result'] = store_goal_evidence(tmp_path, raw)
    return result


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
