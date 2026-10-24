"""Finite arithmetic oracle for conditional endpoint support of each method."""
import pytest
from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b
from support.proofir_v3_native import ref
from test_proof_contract_propagation import _contract, _interface, _scope

CASES = [(source, final, dependent) for source in (0, 2, 3, 4)
         for final in sorted({source, source + 1, 5}) for dependent in (False, True)]


def _case(source_loss, final_loss, dependent):
    case = route_a_route_b()
    dependencies = ('u',) if dependent else ()
    source = _contract('route-a-source', offset=source_loss, dependencies=dependencies)
    case['artifacts'][0] = source
    case['interfaces'][1] = _interface('in-a', contract=source)
    case['scopes'][0] = _scope(source, statement='route-a-source')
    binding = case['bindings'][2]
    binding['ruleId'] = 'weaken-loss'
    binding['parameters'] = {'targetOffset': final_loss,
                             'nestednessRefs': [ref('check-run', 'check:interface')]}
    return case


@pytest.mark.parametrize('source_loss,final_loss,dependent', CASES)
def test_method_endpoint_matches_arithmetic_and_dependency_oracle(source_loss, final_loss, dependent):
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = _case(source_loss, final_loss, dependent)
    result = plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(case)))
    described = next(row for row in result['routeComparisons'] if row['describedRoute'])
    expected = 'conditional-profile-support' if final_loss <= 3 and not dependent else 'unresolved'
    assert described['endpoint']['status'] == expected
    assert result['endpoint']['status'] == 'conditional-profile-support'
    assert result['mathematicalFalsity'] == 'not-established'
