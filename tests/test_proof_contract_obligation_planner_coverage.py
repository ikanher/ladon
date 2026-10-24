"""A partial planner must disclose only work it actually explored."""
from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b


def test_partial_result_does_not_report_every_application_explored():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = route_a_route_b()
    result = plan_contract_obligations(ContractObligationPlanRequest(
        **request_kwargs(case, bounds={'maxEvaluatedSteps': 1})))
    work = result['coverage']['workBudget']
    explored = result['coverage']['exploredStepRefs']
    assert len(explored) <= work['totalSteps'] <= 1
    assert result['coverage']['unvisitedApplications']
