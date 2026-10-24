"""Bridge policy ceilings preserve stricter requests and clamp larger values."""
from time import monotonic

from test_proof_contract_planned_source_preflight import _invalid_request

from ladon import proof_contract_bridge as bridge
from ladon.process_supervisor import ProcessResult
from ladon.proof_contract_bridge_supervision import run_bridge_job


def test_worker_cannot_expand_stage_and_memory_ceiling():
    calls = []

    def runner(command, **kwargs):
        calls.append(kwargs)
        return ProcessResult(tuple(command), -1, '', '', 0, timed_out=True)

    result = run_bridge_job('check-goal', {}, deadline_monotonic=monotonic()+1000,
        limits={'timeout_seconds': 600, 'max_output_bytes': 8388608,
                'max_rss_bytes': 64*1024**3}, runner=runner)
    assert result['status'] == 'incomplete'
    assert calls[0]['timeout_seconds'] <= 30
    assert calls[0]['max_rss_bytes'] == 12*1024**3


def test_source_constructor_receives_effective_caps_without_mutating_input(monkeypatch):
    calls = []

    def constructor(request):
        calls.append(request['limits'])
        return {'status': 'incomplete'}

    monkeypatch.setattr(bridge, 'instantiate_planned_source_leaf_requirement', constructor)
    request = _invalid_request()
    request['limits'] = {'timeout_seconds': 600, 'max_output_bytes': 1024**2,
                         'max_rss_bytes': 64*1024**3}
    bridge.check_planned_source_bridge(request, {})
    assert calls == [{'timeout_seconds': 30, 'max_output_bytes': 1024**2,
                      'max_rss_bytes': 12*1024**3}]
    assert request['limits']['max_rss_bytes'] == 64*1024**3
