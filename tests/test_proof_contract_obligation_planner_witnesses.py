"""Witness dependency gaps are named independently of constant permissions."""
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


def _case():
    source = _contract('witness-source', offset=3, dependencies=())
    payload = deepcopy(source['payload'])
    record = payload['record']
    record['telescope'].append({'binderId':'w', 'typeId':'Nat', 'quantifier':'exists'})
    record['features']['witnessDependencies'] = [
        {'binderId':'w', 'state':'known', 'allowedBinderIds':['u'], 'reason':None}]
    source = envelope('proofir.contract', payload, source['subjectRefs'], environment=ENVIRONMENT)
    desired = deepcopy(record)
    desired['features']['witnessDependencies'][0]['allowedBinderIds'] = []
    scope = _scope(source, statement='witness-source')
    scope['binderMap'].append({'fromBinderId':'w', 'toBinderId':'w'})
    step = _step('witness-identity', ['witness-source'], 'goal')
    return {'graph':_derivation([step]), 'artifacts':[source], 'scopes':[scope],
            'interfaces':[_interface('out'), _interface('in', contract=source)],
            'steps':[step], 'bindings':[_binding(step)], 'desired':desired,
            'goalRef':ref('statement', 'goal'), 'routeASteps':[step['stepRef']]}


def test_witness_only_mismatch_has_the_witness_dependency_dimension():
    from ladon.proof_contract_obligation_planner import (
        ContractObligationPlanRequest,
        plan_contract_obligations,
    )

    result = plan_contract_obligations(ContractObligationPlanRequest(**request_kwargs(_case())))
    mismatches = [row for row in result['comparisons'] if row['status'] == 'candidate-contract-mismatch']
    assert mismatches
    assert all(row['mismatchDimensions'] == ['witnessDependencies'] for row in mismatches)
    assert result['endpoint']['status'] == 'unresolved'
