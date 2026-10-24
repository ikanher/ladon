"""Closed original-context obligations from an exact native correspondence owner."""
from __future__ import annotations

import copy
import math
import re
import time

from ._proof_contract_planned_source_inputs import _planned_input_size
from .proof_contract_bridge import _accepted_check, _resource_stop
from .proof_contract_bridge_supervision import bridge_limits
from .proof_contract_obligation_supervision import _execute_job
from .proof_contract_source_obligations import _plain

MAX_BYTES = 8 * 1024**2
_KEYS = {'repoRoot', 'correspondenceRef', 'context', 'deadlineMonotonic', 'limits'}
_DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
_GOAL = re.compile(r'(?:interpretation|conditional|domain|object-map|conclusion|(?:premise|provider)-[0-9]{1,4})\Z')


def plan_context_bridge(request):
    """Regenerate closed obligations; no term or caller-written goal is accepted."""
    return _run(request, None, None)


def check_context_bridge(request, plan_id, terms):
    """Rebuild a saved subject before checking terms with independent replay."""
    return _run(request, plan_id, terms, checking=True)


def _run(request, plan_id, terms, checking=False):
    started = time.monotonic()
    result = _base()
    try:
        owned = _inputs(request, plan_id, terms, checking)
        _prepare(result, owned)
        if result['status'] == 'planned' and checking:
            _check(result, owned, plan_id, terms)
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError) as error:
        _fail(result, 'rejected', 'invalid-context-bridge', str(error))
    result['elapsedSeconds'] = time.monotonic() - started
    return _bounded(result)


def _inputs(request, plan_id, terms, checking):
    if not isinstance(request, dict) or set(request) != _KEYS:
        raise ValueError('context bridge request must use the closed schema')
    if _planned_input_size([request, plan_id, terms]) > MAX_BYTES:
        raise ValueError('aggregate context bridge input exceeds 8 MiB')
    deadline = request['deadlineMonotonic']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('context bridge deadline must be finite')
    _context(request['context'])
    _reference(request['correspondenceRef'])
    _check_inputs(plan_id, terms, checking)
    limits = bridge_limits(request['limits'])
    owned = copy.deepcopy(request)
    owned['limits'] = limits
    return owned


def _context(context):
    if (not isinstance(context, dict) or set(context) != {'artifacts'}
            or not isinstance(context['artifacts'], list) or len(context['artifacts']) > 4096):
        raise ValueError('context requires a bounded native artifact list')


def _check_inputs(plan_id, terms, checking):
    if checking:
        if not isinstance(plan_id, str) or not _DIGEST.fullmatch(plan_id):
            raise ValueError('check requires an exact saved plan identity')
        _terms(terms)


def _reference(reference):
    if (not isinstance(reference, dict)
            or set(reference) != {'artifactRef', 'kind', 'localId'}
            or reference['kind'] != 'correspondence'
            or not isinstance(reference['artifactRef'], str)
            or not _DIGEST.fullmatch(reference['artifactRef'])
            or not isinstance(reference['localId'], str)
            or not 1 <= len(reference['localId']) <= 512):
        raise ValueError('exact external correspondence reference required')


def _terms(terms):
    if not isinstance(terms, dict) or len(terms) > 4096:
        raise ValueError('terms must be a bounded goal-to-term mapping')
    for key, term in terms.items():
        if (not isinstance(key, str) or not _GOAL.fullmatch(key)
                or not isinstance(term, str) or not term.strip()
                or len(term.encode()) > 1024**2):
            raise ValueError('invalid context goal identity or bounded proof term')


def _prepare(result, owned):
    deadline, limits = owned['deadlineMonotonic'], owned['limits']
    if deadline <= time.monotonic():
        _fail(result, 'incomplete', 'timeout', 'Shared context bridge deadline expired.')
        return
    checked = _stage('prepare-context', owned, owned)
    result['preparation'] = {key: value for key, value in checked.items() if key != 'result'}
    if _stop(result, checked, limits):
        return
    if checked['status'] != 'completed':
        _fail(result, 'rejected', 'context-preparation-rejected', checked['diagnostic'])
        return
    prepared = checked['result']
    if prepared.get('status') != 'prepared':
        result['partialPreparation'] = prepared
        _fail(result, 'incomplete', 'context-preparation-incomplete',
              'A complete original application and checked strict prefix are required.')
        return
    result.update(status='planned', planId=prepared['planId'],
                  binding=prepared['binding'], goals=prepared['goals'],
                  residuals=prepared['residuals'], construction=prepared['construction'],
                  adapter=prepared['adapter'], symbols=prepared['symbols'])


def _check(result, owned, plan_id, terms):
    if result['planId'] != plan_id:
        raise ValueError('saved context plan differs from the exact regenerated subject')
    ids = {goal['id'] for goal in result['goals']}
    if not set(terms) <= ids:
        raise ValueError('supplied term does not identify a generated context obligation')
    for goal in result['goals']:
        goal['status'] = 'unresolved'
    for goal in result['goals']:
        if goal['id'] in terms and not _check_goal(result, owned, goal, terms[goal['id']]):
            return
    result['status'] = 'checked-support' if _supported(result) else 'unresolved-bridge'


def _supported(result):
    return (bool(result['goals']) and not result['residuals']
            and all(g['status'] == 'checked-support' and _accepted_check(g.get('result'))
                    for g in result['goals']))


def _check_goal(result, owned, goal, term):
    checked = _stage('check-context-goal', {**result['adapter'], 'goal': goal['goal'],
        'term': term, 'symbols': result['symbols'], 'binding': result['binding']}, owned)
    goal.update(term=term, result=checked.get('result'),
                supervision={key: value for key, value in checked.items() if key != 'result'})
    if _stop(result, checked, owned['limits']):
        return False
    if checked['status'] == 'completed' and _accepted_check(checked['result']):
        goal['status'] = 'checked-support'
    return True


def _stage(operation, request, owned):
    job = {'version': 1, 'operation': operation, 'request': _plain(request)}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    bounds = {**owned['limits'], 'deadlineMonotonic': float(owned['deadlineMonotonic'])}
    return _execute_job(job, bounds, state, None,
                         worker_module='ladon.proof_contract_context_worker')


def _stop(result, checked, limits):
    stopped = _resource_stop(checked, limits)
    if stopped:
        _fail(result, 'incomplete', stopped['code'], stopped['message'])
    return stopped is not None


def _base():
    return {'schema': 'ladon-source-context-bridge-v1', 'status': 'incomplete',
        'goalOrigin': 'generated-original-context-obligation', 'planId': None,
        'sourceFidelity': 'attributed-unreviewed', 'wholeMethodAuthority': 'none',
        'mathematicalFalsity': 'not-established', 'goals': [], 'residuals': [],
        'memoryReportBackRequired': False, 'diagnostic': None}


def _fail(result, status, code, message):
    result.update(status=status, diagnostic={'code': code, 'message': str(message)[:1000]},
                  memoryReportBackRequired=code == 'memory-limit')


def _bounded(result):
    from ._proof_contract_source_obligations_inputs import bounded_json_size

    if bounded_json_size(result, MAX_BYTES) <= MAX_BYTES:
        return result
    small = _base()
    if result['memoryReportBackRequired']:
        _fail(small, 'incomplete', 'memory-limit', result['diagnostic']['message'])
    else:
        _fail(small, 'incomplete', 'result-output-limit', 'Context bridge evidence exceeds 8 MiB.')
    return small
