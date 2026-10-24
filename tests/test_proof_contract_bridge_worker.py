"""Bridge Lean stages have independent hard bounds and no resource retries."""
import importlib
from time import monotonic

import pytest

from ladon.process_supervisor import ProcessResult


def _run(*args, **kwargs):
    return importlib.import_module('ladon.proof_contract_bridge_supervision').run_bridge_job(
        *args, **kwargs)


@pytest.mark.parametrize('flag,code', [('timed_out', 'timeout'),
                                       ('memory_limited', 'memory-limit'),
                                       ('output_limited', 'output-limit')])
def test_bridge_resource_stop_is_bounded_once(flag, code):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return ProcessResult(tuple(command), -9, '', '', .01, **{flag: True})

    result = _run('check-goal', {}, deadline_monotonic=monotonic()+5, runner=runner)
    assert result['status'] == 'incomplete'
    assert result['diagnostic']['code'] == code
    assert len(calls) == 1
    command, bounds = calls[0]
    assert command[-1] == 'ladon.proof_contract_bridge_worker'
    assert 0 < bounds['timeout_seconds'] <= 5
    assert bounds['max_rss_bytes'] == 12*1024**3
    assert bounds['max_output_bytes'] == 8*1024**2
    if flag == 'memory_limited':
        assert 'Stop progress and report back to user' in result['diagnostic']['message']


def test_expired_bridge_starts_nothing():
    result = _run('extract-provider', {}, deadline_monotonic=monotonic()-1,
                  runner=lambda *a, **_kwargs: pytest.fail('expired work launched'))
    assert result['status'] == 'incomplete'
    assert result['processReceipt'] is None


@pytest.mark.parametrize('operation', ['check-parent', None, '', 'plan-v2'])
def test_unknown_bridge_operation_rejected(operation):
    result = _run(operation, {}, deadline_monotonic=monotonic()+5,
                  runner=lambda *a, **_kwargs: pytest.fail('invalid work launched'))
    assert result['status'] == 'rejected'


def test_cycle_is_rejected_before_worker_launch():
    payload = {}; payload['cycle'] = payload
    result = _run('check-goal', payload, deadline_monotonic=monotonic()+5,
                  runner=lambda *a, **_kwargs: pytest.fail('cyclic work launched'))
    assert result['status'] == 'rejected'
