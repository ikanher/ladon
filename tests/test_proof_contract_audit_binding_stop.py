"""Source admission obeys the same stop-and-report contract as algorithm stages."""
import json

import pytest
from test_proof_contract_audit_driver import _fixture_plan, _write_plan
from test_proof_contract_worker_scratch import _repo

from ladon.process_supervisor import ProcessResult
from ladon.resource_limits import memory_limit_message


def test_source_binding_memory_stop_keeps_receipt_and_never_dispatches(tmp_path):
    from ladon.proof_contract_audit import run_contract_audit

    root, *_rest = _repo(tmp_path / 'repo')
    (root / 'quote.txt').write_text('Selected source')
    plan = _fixture_plan()
    plan.update(repoRoot=str(root), sourceFiles=['quote.txt'])
    path = _write_plan(tmp_path / 'plan.json', plan)
    calls = []
    cap = 12 * 1024**3
    peak = cap + 1024

    def memory_worker(command, **kwargs):
        job = json.loads(kwargs['input_bytes'])
        calls.append(job['operation'])
        assert job['operation'] == 'audit-source-binding'
        return ProcessResult(tuple(command), -9, '', '', .01,
                             memory_limited=True, peak_rss_bytes=peak)

    report = run_contract_audit(path, tmp_path / 'stopped', runner=memory_worker)
    assert report['status'] == 'stopped'
    assert report['code'] == 'memory-limit'
    assert memory_limit_message(cap, peak) in report['message']
    assert calls == ['audit-source-binding']
    assert report['stages'] == []
    saved = json.loads((tmp_path / 'stopped/run.json').read_bytes())
    assert saved == report
    assert 'memoryLimited' in json.dumps(saved)
    assert str(peak) in json.dumps(saved)

    def forbidden(*_args, **_kwargs):
        pytest.fail('memory-stopped admission launched a retry')

    with pytest.raises((ValueError, OSError)):
        run_contract_audit(path, tmp_path / 'retry', resume=tmp_path / 'stopped',
                           runner=forbidden)
    assert not (tmp_path / 'retry').exists()
