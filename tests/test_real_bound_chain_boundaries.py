"""Shared deadline and rule-sequence boundaries preserve incomplete outcomes."""

import pytest
from test_real_bound_chain_persistence import recorded
from test_real_bound_chain_replay import install


def test_deadline_between_edges_keeps_prior_checked_edge(monkeypatch):
    from ladon import real_bound_native_chain as live
    from ladon.real_bound_native_chain_bundle import produce_chain_bundle

    data, calls = install(monkeypatch)
    original = live._check_edge

    def edge(pair, rule, root, deadline):
        if rule == 'identity-v1':
            raise TimeoutError('shared deadline expired')
        return original(pair, rule, root, deadline)

    monkeypatch.setattr(live, '_check_edge', edge)
    strong, weak = data['productions']
    result = produce_chain_bundle([strong, weak, weak], ['order-prefix-v1', 'identity-v1'], '/root')
    assert result['status'] == 'unresolved'
    assert result['failedEdge'] == 1
    assert result['checkedEdgeCount'] == 1
    assert result['edgeResults'][0]['status'] == 'resolved'
    assert 'artifacts' not in result
    assert [r[0] for r in calls] == ['admission'] * 3 + ['prefix']


@pytest.mark.parametrize('seconds', [0, -1, 601, float('nan'), float('inf'), True])
def test_invalid_deadline_stops_before_workers(monkeypatch, seconds):
    from ladon.real_bound_native_chain_bundle import produce_chain_bundle

    data, calls = install(monkeypatch)
    with pytest.raises(ValueError):
        produce_chain_bundle(data['productions'], ['order-prefix-v1'], '/root', timeout_seconds=seconds)
    assert calls == []


def test_oversized_input_stops_before_workers(monkeypatch):
    from ladon.real_bound_native_chain_bundle import produce_chain_bundle

    data, calls = install(monkeypatch)
    data['productions'][0]['padding'] = 'x' * (32 * 1024**2)
    with pytest.raises(ValueError):
        produce_chain_bundle(data['productions'], ['order-prefix-v1'], '/root')
    assert calls == []


def test_offline_chain_never_invokes_a_worker(monkeypatch):
    from ladon import real_bound_native_chain as live
    from ladon.real_bound_native_chain_bundle import inspect_chain_bundle

    def forbidden(*_args, **_kwargs):
        pytest.fail('history attempted fresh Lean checking')

    monkeypatch.setattr(live, '_fresh', forbidden)
    monkeypatch.setattr(live, '_check_edge', forbidden)
    result = inspect_chain_bundle(recorded())
    assert result['authority'] == 'none'
    assert result['freshCheck'] is False
