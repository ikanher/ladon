"""Adversarial source identity and partial-plan authority controls."""
import copy
from dataclasses import replace

import pytest
import test_proof_contract_planned_source as controls
from test_proof_contract_planned_source import request_for

from ladon.proof_contract_obligation_planner import plan_contract_obligations
from ladon.proofir_v3 import detached_content_id


@pytest.fixture(scope="module")
def observed_plan(tmp_path_factory):
    return controls.observed_plan.__wrapped__(tmp_path_factory)


@pytest.fixture
def api():
    return controls.api.__wrapped__()


def test_equal_record_with_different_native_artifact_is_not_the_provider(api, observed_plan):
    request = request_for(observed_plan)
    plan = copy.deepcopy(request['planRequest'])
    original_id = request['selectedIdentity']['forwardContractRef']['artifactRef']
    contract = next(a for a in plan.contract_artifacts if a['artifactId'] == original_id)
    contract['producer']['name'] = 'different-attributed-producer'
    contract['artifactId'] = detached_content_id(contract)
    for collection in (plan.endpoint_interfaces, plan.scope_bindings):
        for row in collection:
            reference = row.get('contractRef', {})
            if reference.get('artifactRef') == original_id:
                reference['artifactRef'] = contract['artifactId']
    request['planRequest'] = plan
    request['planResult'] = plan_contract_obligations(plan)
    _retarget(request)
    assert contract['payload']['record'] == request['providerSnapshot']['contract']
    result = api(request)
    assert result['status'] == 'rejected', result
    assert result.get('capture') is None


def _retarget(request):
    route_index = next(i for i, r in enumerate(request['planResult']['routeComparisons'])
                       if r['describedRoute'])
    route = request['planResult']['routeComparisons'][route_index]
    index = next(i for i, r in enumerate(route['backwardRequirements'])
                 if r['statementRef']['localId'] == 'second')
    request['routeIndex'], request['requirementIndex'] = route_index, index
    row = route['backwardRequirements'][index]
    request['selectedIdentity'] = {'routeId': route['routeId']} | {
        k: copy.deepcopy(row[k]) for k in request['selectedIdentity'] if k != 'routeId'}


def test_retained_partial_requirement_cannot_hide_pending_work(api, observed_plan):
    request = request_for(observed_plan)
    plan = replace(request['planRequest'], bounds={'maxEvaluatedSteps': 8})
    request['planRequest'] = plan
    request['planResult'] = plan_contract_obligations(plan)
    _retarget(request)
    assert request['planResult']['status'] == 'partial'
    result = api(request)
    assert result['status'] == 'candidate-goal', result
    assert result['planStatus'] == 'partial'
    assert result['planCoverage'] == request['planResult']['coverage']
    assert result['routeComparisons'] == request['planResult']['routeComparisons']
    assert result['planCoverage']['pendingBranches']
    assert result['wholeMethodAuthority'] == 'none'
    assert result['mathematicalFalsity'] == 'not-established'


def test_inherited_expired_planner_budget_stages_nothing(api, observed_plan):
    request = request_for(observed_plan)
    request['planRequest'] = replace(request['planRequest'], bounds={
        'deadlineUtc': '2000-01-01T00:00:00Z'})
    directory = request['repoRoot'] / '.ladon/contract-obligations'
    before = set(directory.rglob('*')) if directory.exists() else set()
    result = api(request)
    assert result['status'] == 'incomplete', result
    assert result.get('capture') is None
    assert (set(directory.rglob('*')) if directory.exists() else set()) == before
