"""Public lift ownership retains resource stops and rejects stale worker bindings."""
import copy
import hashlib
import time

import pytest

from ladon import proof_contract_lift_check as owner
from ladon.proof_contract_lift_goals import plan_nat_rational_lift
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


def _request(tmp_path):
    source = b'import Init.Data.Rat.Lemmas\n'
    (tmp_path / 'Fixture.lean').write_bytes(source)
    request = {'repoRoot': str(tmp_path), 'goal': {'variables': ['x'], 'premises': [],
        'conclusion': {'op': 'eq', 'left': {'var': 'x'}, 'right': {'rat': 0}}},
        'witness': {'id': 'w', 'status': 'abstract-countermodel', 'assignment': {'x': '1'}},
        'interpretation': {'profile': 'nat-cast-v1',
            'source': {'path': 'Fixture.lean', 'sha256': hashlib.sha256(source).hexdigest()},
            'formalClaim': 'Fixture.Claim', 'formalPredicate': 'Fixture.Predicate'},
        'mode': 'realization', 'deadlineMonotonic': time.monotonic() + 30, 'limits': {}}
    plan = plan_nat_rational_lift(request['goal'], request['witness'],
                                  request['interpretation'], mode=request['mode'])
    return request, plan


def _stopped(code):
    message = memory_limit_message(DEFAULT_MAX_RSS_BYTES) if code == 'memory-limit' else code
    return {'status': 'incomplete', 'result': None,
            'diagnostic': {'code': code, 'message': message},
            'processReceipt': None, 'workerInputDigest': None, 'bounds': None}


@pytest.mark.parametrize('code', ['memory-limit', 'timeout', 'output-limit', 'goal-scratch-cleanup-required'])
def test_public_resource_or_cleanup_stop_never_promotes_or_retries(tmp_path, monkeypatch, code):
    request, plan = _request(tmp_path)
    calls = []
    monkeypatch.setattr(owner, '_checker_identity', lambda: 'sha256:checker')

    def stop(job, bounds):
        calls.append((job, bounds))
        return _stopped(code)

    monkeypatch.setattr(owner, '_run', stop)
    result = owner.check_nat_rational_lift(request, plan['planId'], 'by trivial')
    assert len(calls) == 1
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == code
    assert result['witness'] == request['witness']
    assert result['planId'] == plan['planId']
    assert result['formalClaimRefuted'] is False
    assert result['checkId'] is None
    if code == 'memory-limit':
        assert 'Stop progress and report back to user' in result['diagnostic']['message']


def test_resource_caps_and_absolute_deadline_are_forwarded_without_reset(tmp_path, monkeypatch):
    request, plan = _request(tmp_path)
    request['limits'] = {'timeout_seconds': 10000, 'max_rss_bytes': 32 * 1024**3}
    observed = []
    monkeypatch.setattr(owner, '_checker_identity', lambda: 'sha256:checker')

    def stop(_job, bounds):
        observed.append(bounds)
        return _stopped('timeout')

    monkeypatch.setattr(owner, '_run', stop)
    owner.check_nat_rational_lift(request, plan['planId'], 'by trivial')
    assert observed == [{'timeout_seconds': 120, 'max_rss_bytes': DEFAULT_MAX_RSS_BYTES,
        'max_output_bytes': 8 * 1024**2, 'deadlineMonotonic': request['deadlineMonotonic']}]


def test_output_overflow_discards_positive_receipt_but_retains_original_witness(tmp_path):
    request, plan = _request(tmp_path)
    expanded = {'status': 'lifted-counterexample', 'checkId': 'forged',
                'nativeEvidence': 'x' * (8 * 1024**2 + 1)}
    result = owner._bound_result(expanded, request['witness'], plan)
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == 'output-limit'
    assert result['planId'] == plan['planId']
    assert result['witness'] == request['witness']
    assert result['checkId'] is None
    assert result['realizationEvidence'] is None


@pytest.mark.parametrize('key', ['attemptId', 'checkerIdentity', 'planId', 'goal', 'witness',
                                'interpretation', 'mode', 'termDigest', 'root', 'source', 'sourceDigest'])
def test_old_or_unrelated_worker_binding_rejected(tmp_path, key):
    from ladon.proof_contract_lift_worker import _binding
    request, plan = _request(tmp_path)
    job = owner._worker_job(request, plan['planId'], 'by trivial', 'sha256:checker')
    binding = _binding(job, plan, (tmp_path / 'Fixture.lean').read_bytes())
    native = {'planId': plan['planId'], 'witness': request['witness'], 'binding': binding}
    owner._validate_binding(native, job, plan, request)
    bad = copy.deepcopy(native)
    bad['binding'][key] = None
    with pytest.raises((TypeError, ValueError)):
        owner._validate_binding(bad, job, plan, request)
