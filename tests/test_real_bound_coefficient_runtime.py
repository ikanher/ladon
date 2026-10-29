"""Orchestration controls; mocked calls do not establish mathematical evidence."""

import copy

import pytest


def install(monkeypatch):
    from ladon import real_bound_native_coefficient as live

    value = {'request': {'plan': {'planId': 'plan'}, 'terms': {}}, 'owner': 'same'}
    calls = []
    monkeypatch.setattr(live.production_api, '_verify_production', lambda p: calls.append('verify'))
    monkeypatch.setattr(live.production_api, '_current_source', lambda p, _r: calls.append('source'))
    monkeypatch.setattr(live, '_semantic_owner', lambda p: p['owner'])
    monkeypatch.setattr(live, '_contract_ref', lambda p: {'owner': p['owner']})
    monkeypatch.setattr(live, '_fresh_check_evidence', lambda p: [])

    def fresh(p, root, seconds):
        calls.append(('admission', seconds))
        return copy.deepcopy(p)

    def rule(root, plan, terms, *, timeout_seconds):
        calls.append(('rule', timeout_seconds))
        return {'status': 'completed'}

    monkeypatch.setattr(live, '_fresh', fresh)
    monkeypatch.setattr(live, 'check_coefficient_relation', rule)
    monkeypatch.setattr(live, 'accepted_coefficient_run', lambda run, p: True)
    return live, value, calls


def _assert_result(result):
    assert result['status'] == 'resolved'
    assert result['relation'] == 'output-coefficient-implies'
    assert result['scope'] == 'pointwise-fixed-output-context'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['coefficientUniformity'] == 'not-inferred'
    assert result['paperNormBridge'] == 'unresolved'


def test_fresh_admission_and_rule_share_one_budget(monkeypatch):
    live, value, calls = install(monkeypatch)
    result = live.check_coefficient_implication(value, '/root', timeout_seconds=12)
    jobs = [row for row in calls if isinstance(row, tuple)]
    assert [row[0] for row in jobs] == ['admission', 'rule']
    assert 0 < jobs[1][1] < jobs[0][1] <= 12
    _assert_result(result)


@pytest.mark.parametrize('budget', [0, -1, 601, float('inf'), float('nan'), True])
def test_invalid_budget_stops_before_io(monkeypatch, budget):
    live, value, calls = install(monkeypatch)
    with pytest.raises(ValueError):
        live.check_coefficient_implication(value, '/root', timeout_seconds=budget)
    assert calls == []


def test_expired_preflight_stops_before_io(monkeypatch):
    live, value, calls = install(monkeypatch)

    def expired(_deadline):
        raise TimeoutError('expired')

    monkeypatch.setattr(live, '_remaining', expired)
    result = live.check_coefficient_implication(value, '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert calls == []


def test_fresh_owner_cannot_be_substituted(monkeypatch):
    live, value, calls = install(monkeypatch)
    monkeypatch.setattr(live, '_fresh', lambda *_: {**value, 'owner': 'different'})
    with pytest.raises(ValueError, match='owner'):
        live.check_coefficient_implication(value, '/root')
    assert not any(isinstance(row, tuple) and row[0] == 'rule' for row in calls)


def test_unaccepted_rule_stays_unresolved(monkeypatch):
    live, value, _calls = install(monkeypatch)
    monkeypatch.setattr(live, 'accepted_coefficient_run', lambda *_: False)
    result = live.check_coefficient_implication(value, '/root')
    assert result['status'] == 'unresolved'
    assert result['rule'] is None
    assert result['authority'] == 'none'
    assert result['relationCheckRun'] == {'status': 'completed'}


def test_final_deadline_retains_proof_without_promoting_result(monkeypatch):
    live, value, _calls = install(monkeypatch)

    def checked_then_expired(*_args):
        def expired(_deadline):
            raise TimeoutError('expired')
        monkeypatch.setattr(live, '_remaining', expired)
        return True

    monkeypatch.setattr(live, 'accepted_coefficient_run', checked_then_expired)
    result = live.check_coefficient_implication(value, '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert result['relationCheckRun'] == {'status': 'completed'}


def test_oversized_input_stops_before_io(monkeypatch):
    live, value, calls = install(monkeypatch)
    value['padding'] = 'x' * (32 * 1024**2)
    with pytest.raises(ValueError, match='32 MiB'):
        live.check_coefficient_implication(value, '/root')
    assert calls == []
