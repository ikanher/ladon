"""Existing producer and replay resource receipts remain terminal in an audit."""
import json

import pytest
from test_proof_contract_audit_driver import _fixture_plan, _write_plan

from ladon.process_supervisor import ProcessResult
from ladon.resource_limits import memory_limit_message


@pytest.mark.parametrize('shape', ['formal', 'replay'])
def test_existing_child_memory_shapes_stop_progress_and_preserve_evidence(tmp_path, shape):
    from ladon.proof_contract_audit import run_contract_audit

    cap, peak = 1024**2, 2 * 1024**2
    message = memory_limit_message(cap, peak)
    receipt = {'memoryLimited': True, 'requestedMaxRssBytes': cap, 'peakRssBytes': peak}
    child = {'schema': 'ladon-contract-production-v1', 'channel': 'formal',
             'status': 'unavailable', 'contract': None,
             'processReceipts': [receipt],
             'residuals': [{'code': 'memory-limit', 'message': message, 'feature': 'statement'}]}
    if shape == 'replay':
        child = {'status': 'incomplete', 'code': 'memory-limit', 'message': message,
                 'processReceipt': receipt, 'result': None}
    calls = []

    def memory_worker(command, **_kwargs):
        calls.append(True)
        return ProcessResult(tuple(command), 0, json.dumps({
            'status': 'completed', 'result': child, 'diagnostic': None}), '', .01)

    path = _write_plan(tmp_path / 'plan.json', _fixture_plan())
    report = run_contract_audit(path, tmp_path / 'run', runner=memory_worker)
    assert report['status'] == 'stopped'
    assert report['code'] == 'memory-limit'
    assert message in report['message']
    assert len(calls) == 1
    saved = json.loads((tmp_path / 'run/stages/propagate.json').read_bytes())
    assert saved['result'] == child

    def forbidden(*_args, **_kwargs):
        pytest.fail('child memory stop was retried')

    with pytest.raises((ValueError, OSError)):
        run_contract_audit(path, tmp_path / 'retry', resume=tmp_path / 'run', runner=forbidden)
