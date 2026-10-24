"""Application-probe trust and output boundaries before any Lean work."""
import copy
import time

import pytest
from test_proof_contract_application_probe_contract import TEMPLATE, api, fixture


def request():
    data = fixture()
    return {'repoRoot': '.', 'context': data['context'], 'left': data['sides'][0],
        'right': data['sides'][1], 'template': TEMPLATE,
        'deadlineMonotonic': time.monotonic() + 30, 'limits': {}}


def test_cycles_depth_and_unbounded_term_maps_are_rejected_before_worker(monkeypatch):
    _, _, planner, checker = api()
    import ladon.proof_contract_probes as probes

    def forbidden(*args):
        raise AssertionError('invalid inputs must not start a worker')

    monkeypatch.setattr(probes, '_stage', forbidden)
    cyclic = request()
    cyclic['context']['cycle'] = cyclic
    assert planner(cyclic)['status'] == 'rejected'
    deep = request()
    for _ in range(140):
        deep['context'] = {'artifacts': [deep['context']]}
    assert planner(deep)['status'] == 'rejected'
    valid = request()
    for terms in ({'forged-goal': 'by trivial'}, {'probe': 'x' * (1024**2 + 1)},
                  {'probe': ''}, {'probe': {'completion': 'accepted'}}):
        assert checker(valid, 'sha256:' + '0' * 64, terms)['status'] == 'rejected'


def test_tiny_output_capacity_stops_before_work_without_publication(monkeypatch):
    _, _, planner, _ = api()
    import ladon.proof_contract_probes as probes

    def forbidden(*args):
        raise AssertionError('exhausted output must not start a worker')

    monkeypatch.setattr(probes, '_stage', forbidden)
    inputs = request()
    inputs['limits'] = {'max_output_bytes': 1}
    with pytest.raises(probes.ApplicationProbeOutputLimit):
        planner(inputs)


def test_native_probe_cannot_smuggle_checked_authority_or_other_goal(monkeypatch):
    builder, _, _, _ = api()
    from ladon.proofir_v3 import detached_content_id, validate_envelope_batch

    data = fixture()
    artifact = builder(data['context'], *data['sides'], TEMPLATE, analysis_id='analysis:authority')
    assert artifact['payload']['result']['status'] == 'planned'
    for key, value in (('checkerAuthority', 'checked'), ('status', 'checked-local-nonimplication'),
                       ('mathematicalFalsity', 'established')):
        changed = copy.deepcopy(artifact)
        changed['payload']['result'][key] = value
        changed['artifactId'] = detached_content_id(changed)
        with pytest.raises(ValueError):
            validate_envelope_batch([*data['context']['artifacts'], changed])


def test_native_plan_direction_keeps_both_original_quantified_readings():
    builder, _, _, _ = api()
    data = fixture()
    forward = builder(data['context'], *data['sides'],
        {**TEMPLATE, 'direction': 'left-to-right', 'kind': 'implication'}, analysis_id='analysis:forward')
    backward = builder(data['context'], *data['sides'],
        {**TEMPLATE, 'direction': 'right-to-left', 'kind': 'implication'}, analysis_id='analysis:backward')
    a, b = [x['payload']['result']['goals'][1]['goal'] for x in (forward, backward)]
    assert a != b
    for goal in (a, b):
        assert goal.count('∀') == 4
        assert 'Nat.add' in goal and 'Nat.mul' in goal
    assert forward['payload']['result']['goals'][0] == backward['payload']['result']['goals'][0]
