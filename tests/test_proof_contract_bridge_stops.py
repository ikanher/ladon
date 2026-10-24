"""Synthetic bookkeeping only: resource stops cannot promote a bridge."""
import json
from time import monotonic

import pytest
from test_proof_contract_planned_source_preflight import _invalid_request

from ladon import proof_contract_bridge as bridge


def test_early_construction_resource_stop_has_bounded_output(monkeypatch):
    observed = {'status': 'incomplete', 'padding': 'x'*(8*1024**2),
                'diagnostic': {'code': 'resource-limit', 'message': 'memory limit reached'}}
    monkeypatch.setattr(bridge, 'instantiate_planned_source_leaf_requirement', lambda request: observed)
    result = bridge.check_planned_source_bridge(_invalid_request(), {})
    assert len(json.dumps(result, separators=(',', ':')).encode()) <= 8*1024**2
    assert result['status'] == 'incomplete'
    assert result['memoryReportBackRequired'] is True
    assert 'Stop progress and report back to user' in result['diagnostic']['message']


@pytest.mark.parametrize('flag,code', [('memory_limited', 'memory-limit'),
    ('timedOut', 'timeout'), ('outputLimited', 'output-limit')])
def test_nested_resource_stop_prevents_later_checks(flag, code, monkeypatch):
    import ladon._proof_contract_bridge_preparation as preparation
    monkeypatch.setattr(bridge, 'instantiate_planned_source_leaf_requirement',
                        lambda request: {'status': 'candidate-goal'})
    monkeypatch.setattr(preparation, 'prepare_bridge', lambda *args: {
        'adapter': {}, 'symbols': {}, 'goals': [
            {'id': name, 'goal': 'unused'} for name in bridge.GOAL_IDS]})
    calls = []

    def worker(*args, **kwargs):
        calls.append((args, kwargs))
        return {'status': 'completed', 'result': {'nested': {flag: True}}}

    monkeypatch.setattr(bridge, 'run_bridge_job', worker)
    request = _invalid_request(); request['deadlineMonotonic'] = monotonic()+10
    result = bridge.check_planned_source_bridge(request, {name: 'unused' for name in bridge.GOAL_IDS})
    assert len(calls) == 1
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == code
    assert all(goal['status'] == 'unresolved' for goal in result['goals'])
    assert result['wholeMethodAuthority'] == 'none'
