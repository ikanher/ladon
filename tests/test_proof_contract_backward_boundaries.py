"""Exact wire-byte and pre-copy bounds for conditional backward templates."""

import json

import pytest
from test_proof_contract_backward import contract, iface, request

from ladon.proof_contract_obligations import transform_backward_sufficient


def test_json_escapes_cannot_bypass_aggregate_input_budget():
    desired = contract()
    desired['telescope'] = [{'binderId': f'b{i}', 'typeId': '\x00' * 480,
                             'quantifier': 'forall'} for i in range(4096)]
    desired['features']['witnessDependencies'] = []
    desired['features']['constantDependencies']['allowedBinderIds'] = ['b0']
    assert len(json.dumps(desired, separators=(',', ':')).encode()) > 8 * 1024**2
    with pytest.raises(ValueError, match='input'):
        transform_backward_sufficient(request(desired, 'identity', [iface('in')]))


def test_premise_cap_precedes_copying_desired_record():
    class CopyGuard(dict):
        def __deepcopy__(self, memo):
            raise AssertionError('desired record copied before occurrence cap')

    with pytest.raises(ValueError, match='occurrence'):
        transform_backward_sufficient(request(
            CopyGuard(contract()), 'combine-estimates', [iface('a'), iface('b')],
            parameters={'leftEmbeddingRefs': ['a'], 'rightEmbeddingRefs': ['b'],
                        'nestednessRefs': ['n']}, bounds={'maxPremiseOccurrences': 1},
        ))


@pytest.mark.parametrize('cap', [1024, 4096, 16384])
def test_exact_output_byte_cap_always_holds_with_escaped_identifiers(cap):
    desired = contract()
    desired['telescope'][0]['typeId'] = '\x00' * 480
    result = transform_backward_sufficient(request(
        desired, 'identity', [iface('in')], bounds={'maxOutputBytes': cap},
    ))
    encoded = json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    assert len(encoded) <= cap
    assert result['status'] in {'generated', 'budget-exhausted'}
