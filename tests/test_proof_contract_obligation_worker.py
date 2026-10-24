"""Planner supervision bounds actual Python work and retains stop instructions."""
import importlib
import json
from dataclasses import replace
from time import monotonic

import pytest
from test_proof_contract_obligation_bundles import _request

from ladon.process_supervisor import ProcessResult


def _api():
    return importlib.import_module('ladon.proof_contract_obligation_supervision')


def test_real_worker_uses_current_checkout_and_preserves_plan_input():
    _, request = _request()
    before = json.dumps(vars(request), sort_keys=True)
    result = _api().run_obligation_planner(request, deadline_monotonic=monotonic() + 30)
    assert result['status'] == 'completed', result
    assert result['result']['schema'] == 'ladon-contract-obligation-planner-v2'
    assert result['processReceipt']['requestedMaxRssBytes'] == 12 * 1024**3
    assert result['processReceipt']['requestedMaxOutputBytes'] == 8 * 1024**2
    assert json.dumps(vars(request), sort_keys=True) == before


@pytest.mark.parametrize('flag,code', [('timed_out', 'timeout'),
                                       ('output_limited', 'output-limit'),
                                       ('memory_limited', 'memory-limit')])
def test_resource_stop_returns_once_without_retry(flag, code):
    _, request = _request()
    calls = []

    def runner(command, **kwargs):
        calls.append(kwargs)
        return ProcessResult(tuple(command), -9, '', '', 0.01,
                             peak_rss_bytes=13 * 1024**3, **{flag: True})

    result = _api().run_obligation_planner(request, deadline_monotonic=monotonic()+5,
                                          runner=runner)
    assert result['status'] == 'incomplete'
    assert result['result'] is None
    assert result['diagnostic']['code'] == code
    assert len(calls) == 1
    assert 0 < calls[0]['timeout_seconds'] <= 5
    if flag == 'memory_limited':
        assert 'Stop progress and report back to user' in result['diagnostic']['message']


def test_expired_outer_deadline_launches_nothing():
    _, request = _request()

    def forbidden(*_args, **_kwargs):
        raise AssertionError('no worker may launch after expiry')

    result = _api().run_obligation_planner(request, deadline_monotonic=monotonic()-1,
                                          runner=forbidden)
    assert result['status'] == 'incomplete'
    assert result.get('processReceipt') is None


def test_expired_parent_deadline_launches_nothing():
    _, request = _request()
    request = replace(request, bounds={'deadlineUtc': '2000-01-01T00:00:00Z'})
    calls = []
    result = _api().run_obligation_planner(request, deadline_monotonic=monotonic()+30,
                                          runner=lambda *a, **k: calls.append(True))
    assert result['status'] == 'incomplete'
    assert calls == []


def test_large_request_is_rejected_before_serialization_or_launch():
    _, request = _request()
    request = replace(request, desired_reading_identity={'readingId': 'x'*(8*1024**2)})
    calls = []
    result = _api().run_obligation_planner(request, deadline_monotonic=monotonic()+30,
                                          runner=lambda *a, **k: calls.append(True))
    assert result['status'] == 'rejected'
    assert calls == []


def test_supervised_replay_matches_recorded_plan_after_utc_expiry():
    _, request = _request()
    import ladon.proof_contract_obligation_planner as planner

    plan = planner.plan_contract_obligation_bundles(request)
    result = _api().run_obligation_planner(request, deadline_monotonic=monotonic()+30,
        operation='replay-v2', deadline_observation=plan['deadlineObservation'])
    assert result['status'] == 'completed', result
    assert result['result'] == plan
