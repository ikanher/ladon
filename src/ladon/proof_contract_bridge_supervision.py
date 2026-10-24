"""Hard process-tree supervision for individual generated bridge Lean stages."""
from __future__ import annotations

import math

from ._proof_contract_planned_source_inputs import _planned_input_size
from .proof_contract_obligation_supervision import _execute_job, _report
from .proof_contract_source_obligations import MAX_INPUT_BYTES, _limits
from .resource_limits import DEFAULT_MAX_RSS_BYTES


def run_bridge_job(operation, request, *, deadline_monotonic, limits=None, runner=None):
    """Run exactly one stage, preserving the caller's absolute deadline."""
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    try:
        if operation not in ('extract-provider', 'check-goal') or not isinstance(request, dict):
            raise ValueError('unsupported bridge operation or request')
        if type(deadline_monotonic) not in (int, float) or not math.isfinite(deadline_monotonic):
            raise ValueError('bridge deadline must be finite')
        job = {'version': 1, 'operation': operation, 'request': request}
        if _planned_input_size(job) > MAX_INPUT_BYTES:
            raise ValueError('aggregate bridge stage input exceeds 8 MiB')
        configured = bridge_limits({'timeout_seconds': 30, 'max_output_bytes': MAX_INPUT_BYTES,
                             'max_rss_bytes': DEFAULT_MAX_RSS_BYTES} if limits is None else limits)
        bounds = {**configured, 'deadlineMonotonic': float(deadline_monotonic)}
        return _execute_job(job, bounds, state, runner,
                            worker_module='ladon.proof_contract_bridge_worker')
    except (ValueError, TypeError, KeyError, OSError, OverflowError) as error:
        return _report('rejected', 'invalid-bridge-stage', str(error), state)


def bridge_limits(limits):
    """Fixed bridge ceilings; stricter caller limits remain effective."""
    configured = _limits(limits)
    return {**configured, 'timeout_seconds': min(30.0, configured['timeout_seconds']),
            'max_rss_bytes': min(DEFAULT_MAX_RSS_BYTES, configured['max_rss_bytes'])}
