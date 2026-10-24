"""Distinct native witness alternatives need distinct route identities."""
from support.proof_contract_obligation_planner import (
    multi_frontier_case,
    request_kwargs,
    run_forward,
)


def test_same_step_sequence_with_different_provider_witnesses_has_distinct_route_ids():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = multi_frontier_case()
    forward = run_forward(case)
    goal = next(row for row in forward['frontiers'] if row['statementRef'] == case['goalRef'])
    assert len(goal['contracts']) == 2
    result = plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(case)))
    routes = result['routeComparisons']
    assert len(routes) == 2
    assert len({row['routeId'] for row in routes}) == 2
    assert len({tuple(row['forwardRouteWitnessRefs']) for row in routes}) == 2
