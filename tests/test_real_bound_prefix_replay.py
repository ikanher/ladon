"""Replay orchestration controls; mocks here do not establish Lean validity."""

import copy
import json

import pytest
from test_real_bound_comparison_persistence import analysis
from test_real_bound_prefix_persistence import FIXTURE, recorded


def install(monkeypatch, *, limited=False, foreign=False):
    from ladon import real_bound_native_prefix as live
    from ladon import real_bound_native_production as production

    data = json.loads(FIXTURE.read_text())
    calls = []
    monkeypatch.setattr(production, '_current_source', lambda *_: None)
    monkeypatch.setattr(live, 'native_checker_identity', lambda: data['relationRun']['result']['checkerIdentity'])

    def fresh(value, root, timeout_seconds):
        calls.append(('admission', timeout_seconds))
        return copy.deepcopy(data['productions'][1] if foreign else value)

    def relation(*args, timeout_seconds):
        calls.append(('prefix', timeout_seconds))
        run = copy.deepcopy(data['relationRun'])
        if limited:
            run['processReceipt']['memoryLimited'] = True
        return run

    monkeypatch.setattr(live, '_fresh', fresh)
    monkeypatch.setattr(live, 'check_prefix_relation', relation)
    return calls


def test_replay_checks_both_owners_and_relation_under_one_deadline(monkeypatch):
    from ladon.real_bound_native_prefix_bundle import replay_prefix_bundle

    calls = install(monkeypatch)
    fresh = replay_prefix_bundle(recorded(), '/root', timeout_seconds=30)
    assert fresh['authority'] == 'fresh-source-predicate-scalar-and-prefix-checks'
    assert analysis(fresh)['payload']['result']['authority'] == 'none'
    assert [row[0] for row in calls] == ['admission', 'admission', 'prefix']
    budgets = [row[1] for row in calls]
    assert 30 >= budgets[0] >= budgets[1] >= budgets[2] > 0


def test_failed_fresh_check_cannot_reuse_saved_success(monkeypatch):
    from ladon.real_bound_native_prefix_bundle import replay_prefix_bundle

    install(monkeypatch, limited=True)
    result = replay_prefix_bundle(recorded(), '/root')
    assert result['status'] == 'unresolved'
    assert result['relation'] is None
    assert 'artifacts' not in result


def test_substituted_fresh_owner_rejects(monkeypatch):
    from ladon.real_bound_native_prefix_bundle import replay_prefix_bundle

    install(monkeypatch, foreign=True)
    with pytest.raises(ValueError, match='owner'):
        replay_prefix_bundle(recorded(), '/root')


def test_stale_source_fails_before_workers(monkeypatch):
    from ladon import real_bound_native_production as production
    from ladon.real_bound_native_prefix_bundle import replay_prefix_bundle

    calls = install(monkeypatch)

    def stale(*_):
        raise ValueError('stale source')

    monkeypatch.setattr(production, '_current_source', stale)
    with pytest.raises(ValueError, match='stale'):
        replay_prefix_bundle(recorded(), '/root')
    assert calls == []


@pytest.mark.parametrize('seconds', [0, -1, 601, float('nan'), float('inf'), True])
def test_invalid_budget_stops_before_replay(monkeypatch, seconds):
    from ladon.real_bound_native_prefix_bundle import replay_prefix_bundle

    calls = install(monkeypatch)
    with pytest.raises(ValueError):
        replay_prefix_bundle(recorded(), '/root', timeout_seconds=seconds)
    assert calls == []


def test_oversized_bundle_stops_before_workers(monkeypatch):
    from ladon.real_bound_native_prefix_bundle import replay_prefix_bundle

    calls = install(monkeypatch)
    bundle = recorded()
    bundle['padding'] = 'x' * (32 * 1024**2)
    with pytest.raises(ValueError):
        replay_prefix_bundle(bundle, '/root')
    assert calls == []
