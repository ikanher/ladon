"""A byte-cap stop must identify its actual resource and preserve prior work."""

import json

from test_proof_contract_backward import contract, iface, request

from ladon.proof_contract_obligations import transform_backward_sufficient


def test_output_cap_reports_output_resource_with_completed_branches():
    desired = contract()
    desired['telescope'][0]['typeId'] = '\x00' * 480
    result = transform_backward_sufficient(request(
        desired, 'weaken-loss', [iface('in')],
        parameters={'targetOffset': 4, 'nestednessRefs': ['attributed:nested']},
        choices={'weakenLossOffsets': [0, 1, 2]}, bounds={'maxOutputBytes': 8192},
    ))
    assert result['status'] == 'budget-exhausted'
    assert 0 < len(result['branches']) < 3
    assert result['coverage']['pendingSplitCount'] == 3 - len(result['branches'])
    assert result['residuals'][0]['code'] == 'output-size-cap'
    assert len(json.dumps(result, separators=(',', ':'), ensure_ascii=False).encode()) <= 8192
