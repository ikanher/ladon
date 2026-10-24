"""Intermediate comparisons use local requirements, not the endpoint bound."""
import pytest
from support.proof_contract_obligation_planner import request_kwargs
from test_proof_contract_obligation_planner_branches import _two_branch_case


@pytest.mark.parametrize('split,left_status', [([1, 2], 'profile-related'),
                                               ([0, 3], 'candidate-contract-mismatch')])
def test_intermediate_comparison_uses_its_own_backward_requirement(split, left_status):
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = _two_branch_case()
    choices = [{'stepRef': case['routeASteps'][-1], 'choices': {'lossSplits': [split]}}]
    result = plan_contract_obligations(ContractObligationPlanRequest(
        **request_kwargs(case, backward_choices=choices)))
    route = next(row for row in result['routeComparisons'] if row['describedRoute'])
    statuses = {row['statementRef']['localId']: row['status'] for row in route['comparisons']}
    assert statuses['left-mid'] == left_status
    assert statuses['right-mid'] == 'profile-related'
    assert route['endpoint']['status'] == 'conditional-profile-support'
