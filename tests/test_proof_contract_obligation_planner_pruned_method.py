"""Pruning a method's intermediate witness cannot erase its review obligation."""
from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b
from support.proofir_v3_native import ref
from test_proof_contract_propagation import _derivation


def test_described_method_missing_after_intermediate_pruning_is_explicitly_pending():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = route_a_route_b()
    case['steps'][-1]['conclusionRef'] = ref('statement', 'route-a-mid1')
    case['graph'] = _derivation(case['steps'])
    result = plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(case)))
    assert result['endpoint']['status'] == 'conditional-profile-support'
    described = [row for row in result['routeComparisons'] if row['describedRoute']]
    if described:
        assert described[0]['stepRefs'] == case['routeASteps']
        assert described[0]['endpoint']['status'] == 'unresolved'
    else:
        assert result['status'] == 'partial'
        pending = result['coverage']['pendingBranches']
        assert any(row.get('stepRef') in case['routeASteps'] and row.get('reason') for row in pending)
