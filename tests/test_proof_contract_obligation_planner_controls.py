"""A stronger alternative must not make a valid described method look deficient."""

from copy import deepcopy

from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b
from test_proof_contract_propagation import _contract, _interface, _scope


def _matching_described_route():
    case = route_a_route_b()
    source = _contract('route-a-source', offset=3, dependencies=())
    case['artifacts'][0] = source
    case['interfaces'][1] = _interface('in-a', contract=source)
    case['scopes'][0] = _scope(source, statement='route-a-source')
    return case


def _plan(case):
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )
    return plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(case)))


def test_valid_described_route_is_compared_to_original_goal_not_stronger_alternative():
    case = _matching_described_route()
    result = _plan(case)
    described = next(row for row in result['routeComparisons'] if row['describedRoute'])
    assert described['endpoint']['status'] == 'conditional-profile-support'
    assert described['comparisons']
    assert not any(row['status'] == 'candidate-contract-mismatch'
                   for row in described['comparisons'])
    assert result['desired']['contractRecord'] == case['desired']


def test_result_owns_request_metadata_and_original_reading():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )
    values = request_kwargs(_matching_described_route())
    result = plan_contract_obligations(ContractObligationPlanRequest(**values))
    expected = deepcopy(result)
    values['desired_contract']['telescope'][0]['binderId'] = 'mutated'
    values['desired_reading_identity']['readingId'] = 'mutated'
    values['route_priorities'][0]['sourceId'] = 'mutated'
    values['bounds']['maxEvaluatedSteps'] = 1
    assert result == expected
