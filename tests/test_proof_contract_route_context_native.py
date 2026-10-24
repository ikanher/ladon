"""Pure identity checks over actual source-observed route fixtures."""
import copy
import json
from pathlib import Path

import pytest

from ladon._proof_contract_route_context_preparation import (
    _indices,
    _match_context_provider,
    _parent_reading,
)
from ladon.proof_contract_obligation_artifacts import request_from_payload

FIXTURE = Path(__file__).parent / 'fixtures/proof_contract_route_context'


def _subjects():
    request = json.loads((FIXTURE / 'observed-request.json').read_text())
    result = json.loads((FIXTURE / 'observed-plan.json').read_text())
    payload = request['analysisArtifact']['payload']
    by_id = {a['artifactId']: a for a in request['context']['artifacts']}
    plan = request_from_payload(by_id[payload['derivationGoalRef']['artifactRef']],
        [by_id[r['artifactRef']] for r in payload['contractRefs']], payload['request'])
    return request, result, plan


def test_original_parent_reading_has_exact_native_owner_and_source():
    request, _result, plan = _subjects()
    owner = _parent_reading(request, FIXTURE.resolve(), plan)
    assert owner['artifactId'] == plan.desired_reading_identity['interpretationDigest']
    assert owner['payload']['record']['formula']['body']['binder']['domain'] == 'Fin 5'


@pytest.mark.parametrize('field', ['readingId', 'interpretationDigest'])
def test_changed_original_reading_is_rejected(field):
    request, _result, plan = _subjects()
    plan.desired_reading_identity[field] += '-changed'
    with pytest.raises(ValueError, match='original desired reading'):
        _parent_reading(request, FIXTURE.resolve(), plan)


def test_exact_selected_occurrence_and_provider_match_observed_context():
    request, result, _plan = _subjects()
    historical = request['analysisArtifact']['payload']['result']
    ri, qi = _indices(historical, request['selectedIdentity'])
    assert historical['routeComparisons'][ri]['backwardRequirements'][qi] == result['binding']['selectedRequirement']
    _match_context_provider({'binding': result['binding']['contextBinding']},
                            request['sourceBindings']['providerSnapshot'])


@pytest.mark.parametrize('key', ['routeId', 'premiseOrdinal', 'interfaceId'])
def test_changed_occurrence_cannot_select_another_goal(key):
    request, _result, _plan = _subjects()
    identity = copy.deepcopy(request['selectedIdentity'])
    identity[key] = 'changed'
    with pytest.raises(ValueError, match='absent or ambiguous'):
        _indices(request['analysisArtifact']['payload']['result'], identity)


def test_wrong_provider_is_rejected_even_in_same_module():
    request, result, _plan = _subjects()
    provider = request['sourceBindings']['providerSnapshot']
    provider['selection']['declaration'] = 'ThreeSteps.secondBound'
    with pytest.raises(ValueError, match='selected native provider'):
        _match_context_provider({'binding': result['binding']['contextBinding']}, provider)


def test_closed_goal_channels_retain_originals_and_route_binding():
    _request, result, _plan = _subjects()
    goals = result['goals']
    assert [g['id'] for g in goals][-4:] == ['source-reading', 'contract-transfer', 'endpoint-transfer', 'source-requirement']
    assert [g['occurrence'] for g in goals if g['kind'] == 'premise-supply'] == [4, 5]
    assert all('routeBindingDigest' in g for g in goals)
    assert all('binding' not in g for g in goals[-4:])
    assert goals[-3]['antecedentGoal'] == goals[-4]['goal']
    assert goals[-3]['consequentGoal'] == goals[-1]['goal']
    assert 'Fin 5' in goals[-4]['goal'] and 'Fin 5' not in goals[-1]['goal']
    assert 'ThreeSteps.endpoint' not in goals[-1]['goal']
