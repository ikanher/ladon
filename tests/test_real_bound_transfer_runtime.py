"""Transfer orchestration controls; fake worker results carry no mathematical evidence."""

import copy

import pytest


def install(monkeypatch):
    from ladon import real_bound_native_transfer as live

    calls = []
    values = [{'owner': name, 'request': {'plan': {}, 'terms': {}}, 'check': {}} for name in ('a', 'b')]
    monkeypatch.setattr(live.production_api, '_verify_production', lambda _p: None)
    monkeypatch.setattr(live.production_api, '_current_source', lambda _p, _r: None)
    monkeypatch.setattr(live, '_semantic_owner', lambda p: p['owner'])
    monkeypatch.setattr(live, '_contract_ref', lambda p: {'owner': p['owner']})
    monkeypatch.setattr(live, '_fresh_check_evidence', lambda _p: [])
    monkeypatch.setattr(live, 'transfer_candidate', lambda *_: None)
    monkeypatch.setattr(live, 'accepted_transfer_run', lambda *_: True)

    def fresh(value, _root, seconds):
        calls.append(('admit', seconds))
        return copy.deepcopy(value)

    def rule(*_args, timeout_seconds):
        calls.append(('rule', timeout_seconds))
        return {'status': 'completed'}

    monkeypatch.setattr(live, '_fresh', fresh)
    monkeypatch.setattr(live, 'check_transfer_relation', rule)
    return live, values, calls


def test_two_admissions_and_rule_share_budget(monkeypatch):
    live, values, calls = install(monkeypatch)
    result = live.check_transfer_composition(*values, '/root', timeout_seconds=60)
    assert [c[0] for c in calls] == ['admit', 'admit', 'rule']
    assert 60 >= calls[0][1] >= calls[1][1] >= calls[2][1] > 0
    assert result['status'] == 'resolved'
    assert result['scope'] == 'conditional-source-shaped-transfer-composition'
    assert result['transferPremises'] == 'assumed'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['coefficientUniformity'] == 'not-inferred'


@pytest.mark.parametrize('budget', [0, -1, 601, float('inf'), float('nan'), True])
def test_invalid_budget_stops_before_workers(monkeypatch, budget):
    live, values, calls = install(monkeypatch)
    with pytest.raises(ValueError):
        live.check_transfer_composition(*values, '/root', timeout_seconds=budget)
    assert calls == []


def test_incompatible_layout_cannot_launch_rule(monkeypatch):
    live, values, calls = install(monkeypatch)
    monkeypatch.setattr(live, 'transfer_candidate', lambda *_: 'real-transfer-context-layout-mismatch')
    result = live.check_transfer_composition(*values, '/root')
    assert [c[0] for c in calls] == ['admit', 'admit']
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'


def test_unaccepted_rule_has_no_composition_authority(monkeypatch):
    live, values, _calls = install(monkeypatch)
    monkeypatch.setattr(live, 'accepted_transfer_run', lambda *_: False)
    result = live.check_transfer_composition(*values, '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert result['rule'] is None


def test_second_admission_failure_preserves_both_runs_and_stops_rule(monkeypatch):
    live, values, calls = install(monkeypatch)
    original = live._fresh
    failed = {'status': 'incomplete', 'diagnostic': {'message': 'memory limit'}}

    def fresh(value, root, seconds):
        if value['owner'] == 'b':
            raise live._AdmissionIncomplete(failed)
        return original(value, root, seconds)

    monkeypatch.setattr(live, '_fresh', fresh)
    result = live.check_transfer_composition(*values, '/root')
    assert result['status'] == 'unresolved'
    assert result['admissionCheckRuns'] == [{}, failed]
    assert result['diagnostic'] == {'message': 'memory limit'}
    assert result['relationCheckRun'] is None
    assert len(calls) == 1


def test_expired_preflight_starts_no_workers(monkeypatch):
    live, values, calls = install(monkeypatch)

    def expired(_deadline):
        raise TimeoutError('expired')

    monkeypatch.setattr(live, '_remaining', expired)
    result = live.check_transfer_composition(*values, '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert calls == []
