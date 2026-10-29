"""Native coefficient replay and publication deadline controls, with mocked workers."""

import copy
import json

import pytest
from test_real_bound_coefficient_persistence import FIXTURE, recorded


def install(monkeypatch, *, limited=False):
    from ladon import real_bound_native_coefficient as live
    from ladon import real_bound_native_coefficient_evidence as evidence

    data = json.loads(FIXTURE.read_text())
    calls = []
    monkeypatch.setattr(live.production_api, '_current_source', lambda *_: None)
    monkeypatch.setattr(evidence, 'native_checker_identity', lambda: data['relationRun']['result']['checkerIdentity'])

    def fresh(value, _root, seconds):
        calls.append(('admission', seconds))
        return copy.deepcopy(value)

    def rule(*args, timeout_seconds):
        calls.append(('rule', timeout_seconds))
        run = copy.deepcopy(data['relationRun'])
        if limited:
            run['processReceipt']['memoryLimited'] = True
        return run

    monkeypatch.setattr(live, '_fresh', fresh)
    monkeypatch.setattr(live, 'check_coefficient_relation', rule)
    return calls


def test_replay_checks_one_owner_and_rule_with_one_budget(monkeypatch):
    from ladon.real_bound_native_coefficient_bundle import replay_coefficient_bundle

    calls = install(monkeypatch)
    result = replay_coefficient_bundle(recorded(), '/root', timeout_seconds=60)
    assert result['authority'] == 'fresh-source-predicate-scalar-and-coefficient-checks'
    assert [row[0] for row in calls] == ['admission', 'rule']
    assert 60 >= calls[0][1] >= calls[1][1] > 0


def test_failed_replay_does_not_reuse_saved_success(monkeypatch):
    from ladon.real_bound_native_coefficient_bundle import replay_coefficient_bundle

    install(monkeypatch, limited=True)
    result = replay_coefficient_bundle(recorded(), '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert 'artifacts' not in result


def test_expired_publication_keeps_evidence_without_native_bundle(monkeypatch):
    from ladon import real_bound_native_coefficient_bundle as bundles

    install(monkeypatch)
    original = bundles.recorded_coefficient

    def record_then_expire(*args):
        bundle = original(*args)

        def expired(_deadline):
            raise TimeoutError('expired during publication')
        monkeypatch.setattr(bundles, '_remaining', expired)
        return bundle

    monkeypatch.setattr(bundles, 'recorded_coefficient', record_then_expire)
    data = json.loads(FIXTURE.read_text())
    result = bundles.produce_coefficient_bundle(data['production'], '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert result['relationCheckRun'] is not None
    assert 'artifacts' not in result


@pytest.mark.parametrize('seconds', [0, -1, 601, float('inf'), float('nan'), True])
def test_invalid_deadline_precedes_history_and_workers(monkeypatch, seconds):
    from ladon.real_bound_native_coefficient_bundle import replay_coefficient_bundle

    calls = install(monkeypatch)
    with pytest.raises(ValueError):
        replay_coefficient_bundle({}, '/root', timeout_seconds=seconds)
    assert calls == []
