"""Orchestration controls are not Lean validity evidence."""

import copy
import json

import pytest
from test_real_bound_chain_persistence import recorded
from test_real_bound_prefix_persistence import FIXTURE


def install(monkeypatch, *, limited=False, foreign=False):
    from ladon import real_bound_native_chain as live
    from ladon import real_bound_native_production as production

    data = json.loads(FIXTURE.read_text())
    calls = []
    monkeypatch.setattr(production, '_current_source', lambda *_: None)
    monkeypatch.setattr(live, 'native_checker_identity', lambda: data['relationRun']['result']['checkerIdentity'])

    def admit(value, root, timeout_seconds):
        calls.append(('admission', timeout_seconds))
        return copy.deepcopy(data['productions'][1] if foreign else value)

    def check(*args, timeout_seconds):
        calls.append(('prefix', timeout_seconds))
        run = copy.deepcopy(data['relationRun'])
        if limited:
            run['processReceipt']['memoryLimited'] = True
        return run

    monkeypatch.setattr(live, '_fresh', admit)
    monkeypatch.setattr(live, 'check_prefix_relation', check)
    return data, calls


def test_replay_admits_each_position_once_then_checks_every_edge(monkeypatch):
    from ladon.real_bound_native_chain_bundle import replay_chain_bundle

    _data, calls = install(monkeypatch)
    result = replay_chain_bundle(recorded(), '/root', timeout_seconds=30)
    assert result['authority'] == 'fresh-source-predicate-scalar-and-edge-checks'
    assert [r[0] for r in calls] == ['admission', 'admission', 'prefix']
    budgets = [r[1] for r in calls]
    assert 30 >= budgets[0] >= budgets[1] >= budgets[2] > 0


def test_saved_success_does_not_override_failed_edge(monkeypatch):
    from ladon.real_bound_native_chain_bundle import replay_chain_bundle

    install(monkeypatch, limited=True)
    result = replay_chain_bundle(recorded(), '/root')
    assert result['status'] == 'unresolved'
    assert result['failedEdge'] == 0
    assert 'artifacts' not in result


def test_fresh_owner_substitution_rejects(monkeypatch):
    from ladon.real_bound_native_chain_bundle import replay_chain_bundle

    install(monkeypatch, foreign=True)
    with pytest.raises(ValueError, match='owner'):
        replay_chain_bundle(recorded(), '/root')


@pytest.mark.parametrize('rules', [[], ['identity-v1', 'identity-v1'], ['fake-rule']])
def test_invalid_rule_sequence_stops_before_workers(monkeypatch, rules):
    from ladon.real_bound_native_chain_bundle import produce_chain_bundle

    data, calls = install(monkeypatch)
    with pytest.raises(ValueError):
        produce_chain_bundle(data['productions'], rules, '/root')
    assert calls == []


def test_stale_source_stops_before_any_worker(monkeypatch):
    from ladon import real_bound_native_production as production
    from ladon.real_bound_native_chain_bundle import replay_chain_bundle

    _data, calls = install(monkeypatch)

    def stale(*_):
        raise ValueError('stale source')

    monkeypatch.setattr(production, '_current_source', stale)
    with pytest.raises(ValueError, match='stale'):
        replay_chain_bundle(recorded(), '/root')
    assert calls == []
