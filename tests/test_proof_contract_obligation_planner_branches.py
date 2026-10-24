"""Different AND branches carry their own premise requirement and interface."""
from copy import deepcopy

from support.proof_contract_obligation_planner import composition_case, request_kwargs, run_forward
from test_proof_contract_propagation import _binding, _derivation, _step


def _two_branch_case():
    case = composition_case()
    left = _step('left-identity', ['compose-left'], 'left-mid')
    right = _step('right-identity', ['compose-right'], 'right-mid')
    root = _step('compose-app', ['left-mid', 'right-mid'], 'goal')
    for source_id, output_id in [('compose-left-iface', 'left-output'),
                                  ('compose-right-iface', 'right-output')]:
        interface = deepcopy(next(row for row in case['interfaces'] if row['interfaceId'] == source_id))
        interface.pop('contractRef')
        interface['interfaceId'] = output_id
        case['interfaces'].append(interface)
    case['steps'] = [left, right, root]
    case['graph'] = _derivation(case['steps'])
    case['bindings'] = [_binding(left, output_interface='left-output'),
                        _binding(right, output_interface='right-output'), case['bindings'][0]]
    case['routeASteps'] = [step['stepRef'] for step in case['steps']]
    return case


def test_two_distinct_and_branches_receive_their_own_requirement():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = _two_branch_case()
    assert run_forward(case)['status'] == 'complete'
    choices = [{'stepRef': case['routeASteps'][-1], 'choices': {'lossSplits': [[1, 2]]}}]
    result = plan_contract_obligations(ContractObligationPlanRequest(
        **request_kwargs(case, backward_choices=choices)))
    route = next(row for row in result['routeComparisons'] if row['describedRoute'])
    requirements = route['backwardRequirements']
    losses = {row['stepRef']['localId']: row['contractRecord']['features']['regularity']['offset']
              for row in requirements if row['stepRef']['localId'] != 'step:compose-app'}
    assert losses == {'step:left-identity': 1, 'step:right-identity': 2}
    assert not result['residuals']
    assert route['endpoint']['status'] == 'conditional-profile-support'
