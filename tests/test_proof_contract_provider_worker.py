"""Provider expansion hard-bounds the worker process tree without retries."""
import importlib
from time import monotonic

import pytest

from ladon.process_supervisor import ProcessResult


def _run(*args, **kwargs):
    return importlib.import_module('ladon.proof_contract_provider_supervision').run_provider_job(
        *args, **kwargs)


@pytest.mark.parametrize('flag,code', [('timed_out','timeout'),
    ('memory_limited','memory-limit'), ('output_limited','output-limit')])
def test_provider_resource_stop_is_single_and_bounded(flag, code):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return ProcessResult(tuple(command), -9, '', '', .01, **{flag: True})

    result = _run({}, deadline_monotonic=monotonic()+10, runner=runner)
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == code
    assert len(calls) == 1
    command, bounds = calls[0]
    assert command[-1] == 'ladon.proof_contract_provider_worker'
    assert 0 < bounds['timeout_seconds'] <= 10
    assert bounds['max_rss_bytes'] == 12*1024**3
    assert bounds['max_output_bytes'] == 8*1024**2
    if flag == 'memory_limited':
        assert 'Stop progress and report back to user' in result['diagnostic']['message']


def test_provider_expiry_launches_no_worker():
    result = _run({}, deadline_monotonic=monotonic()-1,
        runner=lambda *args, **_kwargs: pytest.fail('expired provider launched'))
    assert result['status'] == 'incomplete'
    assert result['processReceipt'] is None


def test_provider_caps_cannot_be_expanded():
    calls = []

    def runner(command, **kwargs):
        calls.append(kwargs)
        return ProcessResult(tuple(command), -9, '', '', 0, timed_out=True)

    _run({},deadline_monotonic=monotonic()+1000,
         limits={'timeout_seconds':600,'max_rss_bytes':64*1024**3,'max_output_bytes':8388608},
         runner=runner)
    assert calls[0]['timeout_seconds'] <= 30
    assert calls[0]['max_rss_bytes'] == 12*1024**3


def test_provider_cycle_is_rejected_before_serialization():
    value = {}; value['cycle'] = value
    result = _run(value, deadline_monotonic=monotonic()+30,
        runner=lambda *args, **_kwargs: pytest.fail('invalid provider launched'))
    assert result['status'] == 'rejected'
