"""Pruned method support requires its actual endpoint, and every exit is bounded."""
import json

from support.proof_contract_obligation_planner import request_kwargs, route_a_route_b
from support.proofir_v3_native import ref
from test_proof_contract_propagation import _contract, _cyclic_derivation, _interface, _scope


def test_strong_intermediate_does_not_certify_a_weaker_pruned_endpoint():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = route_a_route_b()
    source = _contract('route-a-source', offset=3, dependencies=())
    case['artifacts'][0] = source
    case['interfaces'][1] = _interface('in-a', contract=source)
    case['scopes'][0] = _scope(source, statement='route-a-source')
    binding = case['bindings'][2]
    binding['ruleId'] = 'weaken-loss'
    binding['parameters'] = {'targetOffset': 5, 'nestednessRefs': [ref('check-run', 'check:interface')]}
    result = plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(case)))
    described = next(row for row in result['routeComparisons'] if row['describedRoute'])
    assert result['endpoint']['status'] == 'conditional-profile-support'
    assert described['endpoint']['status'] == 'unresolved'


def test_cycle_exit_enforces_output_cap_for_large_mandatory_metadata():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    case = route_a_route_b()
    case['graph'] = _cyclic_derivation()
    case['goalRef'] = ref('statement', 'A')
    case['routeASteps'] = [ref('derivation-step', 'step:cycle-a')]
    values = request_kwargs(case, bounds={'maxOutputBytes': 4096}, artifacts=[],
                            bindings=[], interfaces=[], scopes=[], backward_choices=[],
                            route_priorities=[])
    values['desired_contract']['assumptions'] = [
        {'predicateId': f'assumption:{index}:' + ('x' * 240)} for index in range(32)]
    try:
        result = plan_contract_obligations(ContractObligationPlanRequest(**values))
    except ValueError as error:
        assert 'metadata' in str(error) or 'maxOutputBytes' in str(error)
        assert len(str(error)) <= 512
    else:
        assert len(json.dumps(result, separators=(',', ':'), ensure_ascii=False).encode()) <= 4096
