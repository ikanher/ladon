"""The first unresolved comparison is explicit and local to its explored route."""
from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b


def _assert_local_explanation(case, described):
    explanation = described['earliestUnresolved']
    assert explanation['ordering'] == 'route-dependency-order'
    assert explanation['scope'] == 'this-explored-route'
    comparison = described['comparisons'][explanation['comparisonIndex']]
    assert comparison['stepRef'] == case['routeASteps'][0]
    assert comparison['status'] in {'candidate-contract-mismatch', 'unresolved-bridge'}


def test_each_route_explains_its_first_unresolved_comparison_in_dependency_order():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = route_a_route_b()
    result = plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(case)))
    described = next(row for row in result['routeComparisons'] if row['describedRoute'])
    _assert_local_explanation(case, described)
    alternative = next(row for row in result['routeComparisons'] if not row['describedRoute'])
    assert alternative['earliestUnresolved'] is None
    assert result['minimalityClaim'] == 'none'
