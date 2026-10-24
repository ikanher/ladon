"""Bound Python planner execution without changing immutable semantic requests."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from ._proof_contract_goal_scratch import ENV_AUDIT_DELEGATION, ENV_KEYS
from ._proof_contract_goal_scratch import environment as _scratch_environment
from ._proof_contract_goal_scratch import finish as _finish_goal_workspace
from ._proof_contract_goal_scratch import provision as _create_goal_workspace
from ._proof_contract_obligations_validation import _parse_deadline
from ._proof_contract_planned_source_inputs import _planned_input_size
from .proof_contract_obligation_planner import ContractObligationPlanRequest
from .proof_contract_source_obligations import MAX_INPUT_BYTES, _limits, _plain
from .resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message

OPERATIONS = frozenset({'plan-v1', 'plan-v2', 'replay-v2', 'artifact-v2'})

def run_obligation_planner(request, *, deadline_monotonic, limits=None, operation='plan-v2',
                           analysis_id=None, deadline_observation=None, runner=None):
    """Run one bounded worker; historical replay enforces the outer deadline."""
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    try:
        job, bounds = _prepare_job(request, deadline_monotonic, limits, operation,
                                   analysis_id, deadline_observation)
        return _execute_job(job, bounds, state, runner)
    except (ValueError, TypeError, KeyError, OverflowError, OSError) as error:
        return _report('rejected', 'invalid-worker-request', str(error), state)

def run_obligation_validation(artifact, context, *, deadline_monotonic, limits=None, runner=None):
    """Validate historical native inputs in a bounded worker process."""
    from .proof_contract_payloads import closed

    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    try:
        closed(context, {'artifacts'}, 'native context')
        if not isinstance(context['artifacts'], list) or len(context['artifacts']) > 4096:
            raise ValueError('native context requires a bounded artifact list')
        if not isinstance(deadline_monotonic, (int, float)) or not math.isfinite(deadline_monotonic):
            raise ValueError('deadline must be finite')
        defaults = {'timeout_seconds': 30, 'max_output_bytes': MAX_INPUT_BYTES,
                    'max_rss_bytes': DEFAULT_MAX_RSS_BYTES}
        configured = _limits(defaults if limits is None else limits)
        job = {'version': 1, 'operation': 'validate-native',
               'request': {'artifact': artifact, 'context': context},
               'analysisId': None, 'deadlineObservation': None}
        if _planned_input_size(job) > MAX_INPUT_BYTES:
            raise ValueError('aggregate native validation input exceeds 8 MiB')
        bounds = {**configured, 'deadlineMonotonic': float(deadline_monotonic)}
        return _execute_job(job, bounds, state, runner)
    except (ValueError, TypeError, KeyError, OverflowError, OSError) as error:
        return _report('rejected', 'invalid-worker-request', str(error), state)

def _execute_job(job, bounds, state, runner, *, worker_module=None):
    try:
        state['bounds'] = bounds
        if bounds['deadlineMonotonic'] <= time.monotonic():
            return _report('incomplete', 'timeout', 'Shared planner deadline expired.', state)
        data = json.dumps(job, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError('worker input exceeds 8 MiB')
        state['inputDigest'] = 'sha256:' + hashlib.sha256(data).hexdigest()
        return _execute_worker(job, data, bounds, state, runner, worker_module)
    except (ValueError, TypeError, KeyError, OverflowError, OSError) as error:
        return _report('rejected', 'invalid-worker-request', str(error), state)

def _execute_worker(job, data, bounds, state, runner, worker_module):
    workspace = _create_goal_workspace(job, worker_module)
    try:
        run_options = {} if worker_module is None else {'worker_module': worker_module}
        process = _run(data, bounds, runner, scratch_workspace=workspace, **run_options)
    except BaseException:
        _finish_goal_workspace(workspace)
        raise
    state['receipt'] = _receipt(process, state['inputDigest'], bounds)
    try:
        cleanup = _finish_goal_workspace(workspace)
        cleanup_error = None
    except OSError as error:
        cleanup = None
        cleanup_error = str(error)
    result = _decode_process(process, state)
    return _with_cleanup_status(result, cleanup, cleanup_error, state)

def _with_cleanup_status(result, cleanup, cleanup_error, state):
    if cleanup_error is not None:
        detail = 'owned goal scratch cleanup could not be verified: ' + cleanup_error
    elif cleanup is not None:
        detail = 'owned goal scratch quarantined at ' + cleanup
    else:
        return result
    if result['status'] == 'completed':
        return _report('incomplete', 'goal-scratch-cleanup-required', detail, state,
                       result.get('result'))
    result['diagnostic']['message'] = (result['diagnostic']['message'] + '; ' + detail)[:1000]
    return result

def _prepare_job(request, deadline, limits, operation, analysis_id, observation):
    if not isinstance(request, ContractObligationPlanRequest) or operation not in OPERATIONS:
        raise TypeError('unsupported planner request or operation')
    if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
        raise ValueError('deadline must be finite')
    if _planned_input_size(request) > MAX_INPUT_BYTES:
        raise ValueError('planner request exceeds 8 MiB')
    defaults = {'timeout_seconds': 30, 'max_output_bytes': MAX_INPUT_BYTES,
                'max_rss_bytes': DEFAULT_MAX_RSS_BYTES}
    limits = _limits(defaults if limits is None else limits)
    bounds = {**limits, 'deadlineMonotonic': _deadline(request, deadline, operation)}
    job = {'version': 1, 'operation': operation, 'request': _plain(request),
           'analysisId': analysis_id, 'deadlineObservation': observation}
    if _planned_input_size(job) > MAX_INPUT_BYTES:
        raise ValueError('aggregate worker request exceeds 8 MiB')
    return job, bounds

def _deadline(request, outer, operation):
    if operation == 'replay-v2':
        return float(outer)
    bounds = request.bounds or {}
    if not isinstance(bounds, dict):
        raise TypeError('planner bounds must be a mapping')
    parsed = _parse_deadline(bounds.get('deadlineUtc'))
    if parsed is None:
        return float(outer)
    remaining = (parsed - datetime.now(UTC)).total_seconds()
    # Publishing an expired artifact records a historical partial plan. It
    # performs no source checking and remains bounded by the outer supervisor.
    if operation == 'artifact-v2' and remaining <= 0:
        return float(outer)
    return min(float(outer), time.monotonic() + remaining)

def _run(data, bounds, runner, *, worker_module='ladon.proof_contract_obligation_worker',
         scratch_workspace=None):
    from .process_supervisor import ProcessResult, run_bounded_target_process

    remaining = min(bounds['timeout_seconds'], bounds['deadlineMonotonic'] - time.monotonic())
    bounds['effectiveTimeoutSeconds'] = max(0.0, remaining)
    if remaining <= 0:
        return ProcessResult((), -1, '', '', 0, timed_out=True)
    root = Path(__file__).resolve().parents[2]
    command = [sys.executable, '-m', worker_module]
    environment = {key: value for key, value in os.environ.items()
                   if key not in (*ENV_KEYS, ENV_AUDIT_DELEGATION)}
    environment['PYTHONPATH'] = str(root / 'src')
    environment.update(_scratch_environment(scratch_workspace))
    return (run_bounded_target_process if runner is None else runner)(command,
        cwd=root, timeout_seconds=remaining, max_output_bytes=bounds['max_output_bytes'],
        max_rss_bytes=bounds['max_rss_bytes'], input_bytes=data, env=environment)

def _receipt(process, digest, bounds):
    return {'command': list(process.command), 'returnCode': process.returncode,
        'elapsedSeconds': process.elapsed_seconds, 'timedOut': process.timed_out,
        'memoryLimited': process.memory_limited, 'outputLimited': process.output_limited,
        'peakRssBytes': process.peak_rss_bytes, 'inputDigest': digest,
        'requestedMaxRssBytes': bounds['max_rss_bytes'],
        'requestedMaxOutputBytes': bounds['max_output_bytes'],
        'requestedTimeoutSeconds': bounds['effectiveTimeoutSeconds'],
        'configuredTimeoutSeconds': bounds['timeout_seconds'],
        'stdoutDigest': 'sha256:' + hashlib.sha256(process.stdout.encode()).hexdigest(),
        'stderrDigest': 'sha256:' + hashlib.sha256(process.stderr.encode()).hexdigest()}

def _decode_process(process, state):
    stopped = _resource_stop(process, state)
    if stopped is not None:
        return stopped
    from .proof_contract_io import _decode
    from .proof_contract_payloads import closed

    body = _decode(process.stdout)
    closed(body, {'status', 'result', 'diagnostic'}, 'worker result')
    if process.returncode != 0 or body['status'] != 'completed':
        return _report('rejected', 'worker-rejected', body['diagnostic'], state)
    if not isinstance(body['result'], dict):
        raise TypeError('worker did not return a structured result')
    return _report('completed', 'completed', 'Bounded planner work completed.', state, body['result'])

def _resource_stop(process, state):
    if process.memory_limited:
        message = memory_limit_message(state['bounds']['max_rss_bytes'], process.peak_rss_bytes)
        return _report('incomplete', 'memory-limit', message, state)
    if process.output_limited:
        return _report('incomplete', 'output-limit', 'Planner output limit reached.', state)
    if process.timed_out:
        return _report('incomplete', 'timeout', 'Shared planner deadline expired.', state)
    return None

def _report(status, code, message, state, result=None):
    return {'schema': 'ladon-supervised-obligation-planner-v1', 'status': status,
            'result': result, 'diagnostic': {'code': code, 'message': str(message)[:1000]},
            'processReceipt': state['receipt'], 'workerInputDigest': state['inputDigest'],
            'bounds': state['bounds']}
