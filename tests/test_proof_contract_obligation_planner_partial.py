"""Byte-limited analysis retains a completed backward requirement."""
from copy import deepcopy

from support.proof_contract_obligation_planner import request_kwargs
from support.proofir_v3_native import ENVIRONMENT, envelope, ref
from test_proof_contract_propagation import (
    _binding,
    _contract,
    _derivation,
    _interface,
    _scope,
    _step,
)


def _large_requirement_case():
    artifact = _contract('partial-source', offset=3, dependencies=())
    payload = deepcopy(artifact['payload'])
    source = payload['record']
    universals = [f'u{index}:' + ('x' * 55) for index in range(64)]
    existentials = [f'w{index}' for index in range(32)]
    source['telescope'] = [
        {'binderId':name, 'typeId':'Nat', 'quantifier':'forall'} for name in universals] + [
        {'binderId':name, 'typeId':'Nat', 'quantifier':'exists'} for name in existentials]
    source['features']['witnessDependencies'] = [
        {'binderId':name, 'state':'known', 'allowedBinderIds':[], 'reason':None}
        for name in existentials]
    artifact = envelope('proofir.contract', payload, artifact['subjectRefs'], environment=ENVIRONMENT)
    desired = deepcopy(source)
    for row in desired['features']['witnessDependencies']:
        row['allowedBinderIds'] = list(universals)
    scope = _scope(artifact, statement='partial-source')
    scope['binderMap'] = [{'fromBinderId':name, 'toBinderId':name}
                         for name in universals + existentials]
    return _chain_case(artifact, desired, scope)


def _chain_case(artifact, desired, scope):
    steps = [_step(f'partial:{index}', ['partial-source' if index == 0 else f'mid:{index-1}'],
                   'goal' if index == 9 else f'mid:{index}') for index in range(10)]
    return {'graph':_derivation(steps), 'artifacts':[artifact], 'scopes':[scope],
            'interfaces':[_interface('out'), _interface('in', contract=artifact)],
            'steps':steps, 'bindings':[_binding(step) for step in steps],
            'desired':desired, 'goalRef':ref('statement', 'goal'),
            'routeASteps':[step['stepRef'] for step in steps]}


def test_output_stop_retains_completed_requirement_that_fits_with_metadata():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    result = plan_contract_obligations(ContractObligationPlanRequest(
        **request_kwargs(_large_requirement_case(), bounds={'maxOutputBytes':512 * 1024})))
    assert result['status'] == 'partial'
    assert result['backwardRequirements']
    assert 'contractRecord' in result['backwardRequirements'][0]
    assert result['coverage']['pendingBranches']
