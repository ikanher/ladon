"""Scope, cancellation and altered-evidence controls for the new shape profile."""

import json
import tempfile

import pytest
from test_real_prose_recognition import api, context, quantified, reading, var
from test_real_prose_recognition import project as _project_fixture


@pytest.fixture
def project(tmp_path):
    return _project_fixture.__wrapped__(tmp_path)


def find(node, predicate):
    if isinstance(node, dict):
        if predicate(node):
            return node
        for value in node.values():
            result = find(value, predicate)
            if result is not None:
                return result
    elif isinstance(node, list):
        for value in node:
            result = find(value, predicate)
            if result is not None:
                return result
    return None


@pytest.mark.parametrize('change', ['scope', 'path', 'canonical', 'guard', 'product_instance'])
def test_rehashed_normalization_tampering_has_no_checked_features(project, change):
    from ladon.real_prose_inputs import observation_identity

    result = api().recognize_prose_bound(project, reading(project), context(), timeout_seconds=60)
    inner = result['check']['result']
    worker = inner['normalization']['worker']
    order, product = worker['results']
    if change == 'scope':
        order['scopeCount'] -= 1
    elif change == 'path':
        order['originPath'] = product['originPath']
    elif change == 'canonical':
        order['lossLiteral'] = 4
    elif change == 'guard':
        inner['shape']['candidate']['guards']['boundNonnegativeBinderIds'] = []
    else:
        term = product['canonical']
        while 'lam' in term:
            term = term['lam']['body']
        # Change the actual HMul instance without changing its equality goal.
        term['app'][0]['app'][0]['app'][1] = {'const': 'Wrong.instance', 'levels': []}
    inner['normalization']['workerJson'] = json.dumps(worker)
    result['snapshotId'] = observation_identity(result)
    with pytest.raises(ValueError):
        api().inspect_recognition(result)


def test_symbolic_loss_does_not_become_zero_or_a_guessed_literal(project):
    path = project / 'Context.lean'
    path.write_text(path.read_text() + '\ndef symbolicShift (n offset : Nat) := n + offset\n')
    record = reading(project)
    record['formula'] = quantified('forall', 'offset', 'Nat', record['formula'])
    record['symbols']['shift'] = {'leanName': 'symbolicShift', 'leanType': 'Nat → Nat → Nat'}
    shift = find(record['formula'], lambda n: n.get('tag') == 'app' and n.get('symbol') == 'shift')
    shift['args'].append(var('offset'))
    result = api().recognize_prose_bound(project, record, context(), timeout_seconds=60)
    assert result['status'] == 'unresolved'
    assert result['check']['result']['features']['candidate']['loss'] is None


def test_actual_local_instance_is_retained_in_the_certificate(project):
    path = project / 'Context.lean'
    path.write_text(path.read_text() + '\ndef selectedProduct (m : HMul Real Real Real) (K C : Real) : Real := @HMul.hMul Real Real Real m K C\n')
    record = reading(project)
    record['formula'] = quantified('forall', 'm', 'HMul Real Real Real', record['formula'])
    record['symbols']['product'] = {'leanName': 'selectedProduct',
                                  'leanType': 'HMul Real Real Real → Real → Real → Real'}
    product = find(record['formula'], lambda n: n.get('tag') == 'app' and n.get('symbol') == 'product')
    product['args'].insert(0, var('m'))
    result = api().recognize_prose_bound(project, record, context(), timeout_seconds=60)
    assert result['status'] == 'recognized'
    row = result['check']['result']['normalization']['worker']['results'][1]
    body = row['canonical']
    while 'lam' in body:
        body = body['lam']['body']
    from ladon.proof_contract_expressions import _app_parts

    _head, args = _app_parts(body)
    assert args[3] == {'bvar': row['scopeCount'] - 1}
    assert result['admission'] == 'unresolved'


def test_duplicate_bound_guards_are_both_retained(project):
    from copy import deepcopy

    record = reading(project)
    node = find(record['formula'], lambda n: n.get('tag') == 'implies' and n.get('premise', {}).get('tag') == 'le')
    old = deepcopy(node['conclusion'])
    node['conclusion'] = {'tag': 'implies', 'premise': deepcopy(node['premise']), 'conclusion': old}
    result = api().recognize_prose_bound(project, record, context(), timeout_seconds=60)
    assert result['status'] == 'recognized'
    guards = result['check']['result']['features']['candidate']['guards']
    assert len(guards['boundNonnegativeBinderIds']) == 2


def test_unsupported_conjunction_is_not_mined_for_a_convenient_estimate(project):
    record = reading(project)
    node = find(record['formula'], lambda n: n.get('tag') == 'and')
    node['items'].insert(1, {'tag': 'const', 'name': 'True'})
    result = api().recognize_prose_bound(project, record, context(), timeout_seconds=60)
    assert result['status'] == 'unresolved'
    assert result['check']['result']['shape']['candidate'] is None
    assert result['check']['result']['normalization'] is None


def test_timeout_cleans_up_nested_observation_scratch(project, tmp_path_factory, monkeypatch):
    scratch = tmp_path_factory.mktemp('recognition-process-scratch')
    monkeypatch.setenv('TMPDIR', str(scratch))
    monkeypatch.setattr(tempfile, 'tempdir', str(scratch))
    path = project / 'Context.lean'
    path.write_text(path.read_text() + '\n#eval IO.sleep 10000\n')
    result = api().recognize_prose_bound(project, reading(project), context(), timeout_seconds=2)
    assert result['status'] == 'unavailable'
    assert not list(scratch.glob('ladon-prose-*'))


def test_old_v1_shape_reader_keeps_its_global_unsupported_behavior(project):
    from ladon.real_bound_shape import observe_bound_shape
    from ladon.real_prose_observation import observe_prose_bound

    observation = observe_prose_bound(project, reading(project), context(), timeout_seconds=60)
    value = observation['check']['result']['observation']['propositionExpr']
    assert observe_bound_shape(value)['candidate'] is None
