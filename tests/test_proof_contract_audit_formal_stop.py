"""The statement producer's actual process observation remains a memory stop."""
import json
from types import SimpleNamespace

from test_proof_contract_audit_driver import _fixture_plan, _write_plan

from ladon.process_supervisor import ProcessResult
from ladon.proof_contract_production import _process_observation
from ladon.resource_limits import memory_limit_message


def test_statement_observation_memory_receipt_is_terminal_for_audit(tmp_path):
    from ladon.proof_contract_audit import run_contract_audit

    cap, peak = 1024**2, 2 * 1024**2
    stopped = ProcessResult(('lean',), -9, '', '', .01,
                            memory_limited=True, peak_rss_bytes=peak)
    captured = {'sourceHash': '0' * 64, 'helperHash': '1' * 64,
                'toolchain': SimpleNamespace(context_identity='fixture-environment')}
    observation = _process_observation(captured, stopped, 'Source.lean', 'Source',
                                      'test', 30, cap)

    def worker(command, **_kwargs):
        return ProcessResult(tuple(command), 0, json.dumps({
            'status': 'completed', 'result': observation, 'diagnostic': None}), '', .01)

    path = _write_plan(tmp_path / 'plan.json', _fixture_plan())
    report = run_contract_audit(path, tmp_path / 'run', runner=worker)
    assert report['status'] == 'stopped'
    assert report['code'] == 'memory-limit'
    assert memory_limit_message(cap, peak) in report['message']
    envelope = json.loads((tmp_path / 'run/stages/propagate.json').read_bytes())
    assert envelope['result'] == observation
