"""Check generated route-local contract bridges in a parent-free Lean context.

This operation reconstructs its own subjects. It never accepts a caller-written
interpretation, object map, prepared plan or additional premise context.
"""
from __future__ import annotations

import copy
import math
import time

from ._proof_contract_planned_source_inputs import _planned_deadline, _planned_input_size
from .proof_contract_bridge_supervision import bridge_limits, run_bridge_job
from .proof_contract_planned_source import _PLANNED_REQUEST_KEYS
from .proof_contract_source_obligations import (
    MAX_INPUT_BYTES,
    _plain,
    instantiate_planned_source_leaf_requirement,
)

GOAL_IDS = ('source-requirement', 'domain', 'object-map', 'conclusion')


def check_planned_source_bridge(source_request, terms):
    """Freshly reconstruct and check one source leaf; missing terms stay open.

    Invalid requests return small structured rejections. Every Lean stage is
    supervised under the same absolute deadline, RSS and output bounds.
    """
    started = time.monotonic()
    result = _base_result()
    try:
        _run_bridge(result, source_request, terms)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, OSError) as error:
        _failure(result, 'rejected', 'invalid-bridge-request', str(error))
    result['elapsedSeconds'] = time.monotonic() - started
    return _bounded_bridge_result(result)


def _run_bridge(result, source_request, terms):
    request, terms, limits = _own_inputs(source_request, terms)
    deadline = request['deadlineMonotonic']
    if deadline <= time.monotonic():
        return _failure(result, 'incomplete', 'timeout', 'Shared bridge deadline expired.')
    from .proof_contract_obligation_planner import ContractObligationPlanRequest

    if isinstance(request['planRequest'], ContractObligationPlanRequest):
        deadline = _planned_deadline(deadline, request['planRequest'])
    if deadline <= time.monotonic():
        return _failure(result, 'incomplete', 'timeout', 'Inherited bridge deadline expired.')
    result['sourceRequest'] = _plain(request)
    construction = instantiate_planned_source_leaf_requirement(request)
    result['construction'] = construction
    stopped = _resource_stop(construction, limits)
    if stopped:
        return _failure(result, 'incomplete', stopped['code'], stopped['message'])
    if construction.get('status') != 'candidate-goal':
        return _failure(result, construction.get('status', 'incomplete'),
                        'source-construction-unavailable', 'Exact source construction unavailable.')
    _prepare_and_check(result, request, terms, construction, deadline, limits)


def _own_inputs(request, terms):
    if not isinstance(request, dict) or set(request) != _PLANNED_REQUEST_KEYS:
        raise ValueError('bridge source request must use the closed planned-source schema')
    _validate_terms(request, terms)
    deadline = request['deadlineMonotonic']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('bridge deadline must be finite')
    limits = bridge_limits(request['limits'])
    owned = copy.deepcopy(request)
    owned['limits'] = limits
    return owned, copy.deepcopy(terms), limits


def _validate_terms(request, terms):
    if not isinstance(terms, dict) or not set(terms).issubset(GOAL_IDS):
        raise ValueError('bridge terms must name supported obligation IDs')
    if _planned_input_size({'sourceRequest': request, 'terms': terms}) > MAX_INPUT_BYTES:
        raise ValueError('aggregate bridge input exceeds 8 MiB')
    if any(not isinstance(term, str) or not term.strip() for term in terms.values()):
        raise ValueError('each bridge proof term must be nonempty text')


def _prepare_and_check(result, request, terms, construction, deadline, limits):
    from ._proof_contract_bridge_preparation import prepare_bridge

    prepared = prepare_bridge(request, construction, deadline, limits)
    result['preparation'] = prepared
    stopped = _resource_stop(prepared, limits)
    if stopped:
        _failure(result, 'incomplete', stopped['code'], stopped['message'])
        return
    if not prepared['goals']:
        _failure(result, 'incomplete', 'provider-slice-unavailable',
                 'A complete actual provider application slice was not obtained.')
        return
    result['goals'] = prepared.pop('goals')
    for goal in result['goals']:
        goal['status'] = 'unresolved'
    for goal in result['goals']:
        if goal['id'] not in terms:
            continue
        if not _check_one_goal(result, goal, terms[goal['id']], prepared, deadline, limits):
            return
    result['status'] = 'checked-support' if _bridge_supported(result['goals']) else 'unresolved-bridge'
    result['diagnostic'] = {'code': result['status'],
        'message': 'Only this generated source-leaf bridge is covered; prose intent remains unreviewed.'}


def _check_one_goal(result, goal, term, prepared, deadline, limits):
    job = {**prepared['adapter'], 'goal': goal['goal'], 'term': term,
           'symbols': prepared['symbols']}
    checked = run_bridge_job('check-goal', job, deadline_monotonic=deadline, limits=limits)
    goal['supervision'] = {key: value for key, value in checked.items() if key != 'result'}
    goal['term'] = term
    goal['result'] = checked.get('result')
    stopped = _resource_stop(checked, limits)
    if stopped:
        _failure(result, 'incomplete', stopped['code'], stopped['message'])
        return False
    if checked['status'] == 'completed' and _accepted_check(checked['result']):
        goal['status'] = 'checked-support'
    return True


def _accepted_check(result):
    if not isinstance(result, dict) or result.get('status') != 'supported':
        return False
    completion = result.get('completion')
    if not isinstance(completion, dict):
        return False
    replay, trust = completion.get('replay'), completion.get('trust')
    return (completion.get('status') == 'completed' and isinstance(replay, dict)
            and replay.get('status') == 'accepted' and isinstance(trust, dict)
            and trust.get('accepted') is True)


def _bridge_supported(goals):
    if [row.get('id') for row in goals] != list(GOAL_IDS):
        return False
    return all(row.get('status') == 'checked-support' and _accepted_check(row.get('result'))
               for row in goals)


def _resource_stop(value, limits):
    flags = {'memory_limited': 'memory-limit', 'memoryLimited': 'memory-limit',
             'output_limited': 'output-limit', 'outputLimited': 'output-limit',
             'timed_out': 'timeout', 'timedOut': 'timeout'}
    todo = [value]
    while todo:
        row = todo.pop()
        if isinstance(row, list):
            todo.extend(row)
        elif isinstance(row, dict):
            code = _stop_code(row, flags)
            if code:
                return {'code': code, 'message': _stop_message(code, limits)}
            todo.extend(row.values())
    return None


def _stop_code(row, flags):
    for key, code in flags.items():
        if row.get(key) is True:
            return code
    for key in ('status', 'code'):
        value = row.get(key)
        if value in ('memory-limit', 'timeout', 'output-limit'):
            return value
    if row.get('code') in ('resource-limit', 'resource-limit-or-io'):
        message = str(row.get('message', '')).lower()
        return 'memory-limit' if 'memory' in message else 'resource-limit'
    return None


def _stop_message(code, limits):
    if code == 'memory-limit':
        from .resource_limits import memory_limit_message
        return memory_limit_message(limits['max_rss_bytes'])
    return f'Bridge work stopped after {code}; no later obligation was attempted.'


def _base_result():
    return {'schema': 'ladon-planned-source-bridge-v1', 'status': 'incomplete',
        'goalOrigin': 'generated-contract-obligation', 'sourceFidelity': 'attributed-unreviewed',
        'transportProfile': 'universal-nat-identity-v1', 'wholeMethodAuthority': 'none',
        'mathematicalFalsity': 'not-established', 'goals': [], 'diagnostic': None}


def _failure(result, status, code, message):
    result.update(status=status, diagnostic={'code': code, 'message': str(message)[:1000]},
                  memoryReportBackRequired=code == 'memory-limit')
    return result


def _bounded_bridge_result(result):
    from ._proof_contract_source_obligations_inputs import bounded_json_size

    if bounded_json_size(result, MAX_INPUT_BYTES) <= MAX_INPUT_BYTES:
        return result
    small = _base_result()
    diagnostic = result.get('diagnostic') or {}
    if result.get('memoryReportBackRequired'):
        return _failure(small, 'incomplete', 'memory-limit', diagnostic.get('message', ''))
    return _failure(small, 'incomplete', 'result-output-limit',
                    'Bridge evidence exceeds 8 MiB; no support is published.')
