"""Regeneration against native owners from a real two-premise observation.

These pure checks reuse frozen observations; they never claim fresh extraction
or fabricate a successful checker receipt.
"""
import copy
import json
from pathlib import Path

import pytest

from ladon._proof_contract_context_goals import build_context_goals
from ladon._proof_contract_context_preparation import _native_plan
from ladon.proofir_v3 import make_envelope

FIXTURE = Path(__file__).parent / 'fixtures/proof_contract_context_bridge'


def _request():
    return json.loads((FIXTURE / 'native-request.json').read_text())


def _replace_owner(request, change):
    reference = request['correspondenceRef']
    owner = next(a for a in request['context']['artifacts']
                 if a['artifactId'] == reference['artifactRef'])
    payload = copy.deepcopy(owner['payload'])
    change(payload)
    parameters = {k: owner[k] for k in ('producer', 'coverage', 'limitations')}
    forged = make_envelope(artifact_kind=owner['artifactKind'], payload=payload,
        environment_ref=owner['environmentRef'], subject_refs=owner['subjectRefs'],
        **parameters).to_dict()
    request['context']['artifacts'] = [forged if a is owner else a
                                     for a in request['context']['artifacts']]
    request['correspondenceRef']['artifactRef'] = forged['artifactId']


def test_real_native_owners_regenerate_all_ordered_premises():
    prepared, _owner, _reading = _native_plan(_request(), FIXTURE)
    goals = build_context_goals(prepared, {'native': 'owned-by-test-fixture'})
    assert [g['id'] for g in goals] == ['interpretation', 'conditional', 'domain',
        'object-map', 'premise-2', 'premise-3', 'conclusion', 'provider-2', 'provider-3']
    assert [g['occurrence'] for g in goals if g['kind'] == 'premise-supply'] == [2, 3]
    domain = next(g for g in goals if g['id'] == 'domain')
    assert '∃ (ladonDomainWitness : Nat)' in domain['goal']
    assert '→' not in domain['goal']
    assert 'Contexts.ordered' not in domain['goal']


@pytest.mark.parametrize('mutation', ['goal', 'order', 'assumption', 'status', 'drop'])
def test_rehashed_native_owner_cannot_change_original_obligations(mutation):
    request = _request()

    def change(payload):
        if mutation == 'goal':
            payload['obligations'][-1]['goal'] = 'True'
        elif mutation == 'order':
            payload['obligations'][3:5] = reversed(payload['obligations'][3:5])
        elif mutation == 'assumption':
            payload['obligations'][3]['goal'] = 'False → True'
        elif mutation == 'status':
            payload['obligations'][3]['status'] = 'supported'
        else:
            payload['obligations'].pop(3)

    _replace_owner(request, change)
    with pytest.raises(ValueError):
        _native_plan(request, FIXTURE)


def test_goals_own_their_context_and_keep_missing_premises_visible():
    prepared, _owner, _reading = _native_plan(_request(), FIXTURE)
    binding = {'reading': {'id': 'frozen-reading'}}
    goals = build_context_goals(prepared, binding)
    goals[0]['binding']['reading']['id'] = 'changed'
    assert goals[1]['binding']['reading']['id'] == 'frozen-reading'
    assert binding['reading']['id'] == 'frozen-reading'
    assert all(g['status'] == 'open' for g in goals)
    assert len({g['goalDigest'] for g in goals}) == 9
