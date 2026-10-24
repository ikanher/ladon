"""Hard supervision of original-source provider observation and extraction."""
from __future__ import annotations

import math

from ._proof_contract_planned_source_inputs import _planned_input_size
from .proof_contract_bridge_supervision import bridge_limits
from .proof_contract_obligation_supervision import _execute_job, _report
from .resource_limits import DEFAULT_MAX_RSS_BYTES


def run_provider_job(request, *, deadline_monotonic, limits=None, runner=None):
    """One bounded worker; observations never discharge the generated demand."""
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    try:
        if not isinstance(request, dict):
            raise TypeError('provider worker request must be a mapping')
        if type(deadline_monotonic) not in (int, float) or not math.isfinite(deadline_monotonic):
            raise ValueError('provider deadline must be finite')
        job = {'version': 1, 'operation': 'observe-provider', 'request': request}
        if _planned_input_size(job) > 8*1024**2:
            raise ValueError('provider worker input exceeds 8 MiB')
        defaults = {'timeout_seconds': 30, 'max_output_bytes': 8*1024**2,
                    'max_rss_bytes': DEFAULT_MAX_RSS_BYTES}
        bounds = {**bridge_limits(defaults if limits is None else limits),
                  'deadlineMonotonic': float(deadline_monotonic)}
        return _execute_job(job, bounds, state, runner,
                            worker_module='ladon.proof_contract_provider_worker')
    except (ValueError, TypeError, KeyError, OSError, OverflowError) as error:
        return _report('rejected', 'invalid-provider-stage', str(error), state)
