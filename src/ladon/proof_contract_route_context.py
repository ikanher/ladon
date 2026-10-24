"""Checkpointed original-context checks for one native route-local demand."""
from __future__ import annotations

import time

from ._proof_contract_route_context_inputs import compose_requirement, own_inputs
from .proof_contract_bridge import _accepted_check, _resource_stop
from .proof_contract_obligation_supervision import _execute_job
from .proof_contract_provider_expansion import _initial_deadline

MAX_BYTES = 8 * 1024**2


def plan_route_context_bridge(request):
    """Derive separate original-context and route transfer obligations."""
    return _run(request, None, None, False)


def check_route_context_bridge(request, plan_id, terms):
    """Regenerate the exact native subject, then check supplied bridge terms."""
    return _run(request, plan_id, terms, True)


def _run(request, plan_id, terms, checking):
    started, result = time.monotonic(), _base()
    try:
        owned, plan_id, terms, _limits = own_inputs(request, plan_id, terms, checking)
        owned['originalDeadlineMonotonic'] = owned['deadlineMonotonic']
        owned['deadlineMonotonic'] = _initial_deadline(owned['analysisArtifact'], owned['deadlineMonotonic'])
        _prepare(result, owned)
        if checking and result['status'] == 'planned':
            _check(result, owned, plan_id, terms)
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, RecursionError) as error:
        _fail(result, 'rejected', 'invalid-route-context', str(error))
    result['elapsedSeconds'] = time.monotonic() - started
    return _bounded(result)


def _prepare(result, owned):
    if owned['deadlineMonotonic'] <= time.monotonic():
        _fail(result, 'incomplete', 'timeout', 'Shared route context deadline expired.')
        return
    checked = _stage('prepare-route-context', owned, owned)
    result['preparation'] = {key: value for key, value in checked.items() if key != 'result'}
    if _stop(result, checked, owned['limits']):
        return
    if checked['status'] != 'completed':
        _fail(result, 'rejected', 'route-context-preparation-rejected', checked['diagnostic'])
        return
    prepared = checked['result']
    if prepared.get('status') != 'prepared':
        result['partialPreparation'] = prepared
        _fail(result, 'incomplete', prepared.get('code', 'route-context-incomplete'),
              prepared.get('message', 'Complete original source and native route observations are required.'))
        return
    result.update({key: value for key, value in prepared.items() if key != 'status'})
    result['status'] = 'planned'


def _check(result, owned, plan_id, terms):
    if result['planId'] != plan_id:
        raise ValueError('saved route context plan differs from the regenerated original subject')
    if not set(terms) <= {row['id'] for row in result['goals']}:
        raise ValueError('term does not identify a generated route context obligation')
    for goal in result['goals']:
        goal['status'] = 'unresolved'
    for goal in result['goals']:
        if goal['id'] in terms and not _check_goal(result, owned, goal, terms[goal['id']]):
            return
    if not _check_composition(result, owned):
        return
    supported = _supported(result)
    result.update(status='checked-support' if supported else 'unresolved-bridge', demandDischarged=supported)


def _check_composition(result, owned):
    composition = compose_requirement(result['goals'])
    if composition is None:
        return True
    final = next(row for row in result['goals'] if row['id'] == 'source-requirement')
    final['termOrigin'] = 'composition-of-checked-reading-and-transfer'
    return _check_goal(result, owned, final, composition['term'])


def _check_goal(result, owned, goal, term):
    checked = _stage('check-route-context-goal', {**result['adapter'], 'goal': goal['goal'],
        'term': term, 'symbols': result['symbols'], 'binding': result['binding']}, owned)
    if not _admit_check(result, checked, term):
        return False
    goal.update(term=term, result=checked.get('result'),
                supervision={key: value for key, value in checked.items() if key != 'result'})
    if _stop(result, checked, owned['limits']):
        return False
    if checked['status'] == 'completed' and _accepted_check(checked['result']):
        goal['status'] = 'checked-support'
    return True


def _admit_check(result, checked, term):
    from ._proof_contract_source_obligations_inputs import bounded_json_size

    if _resource_stop(checked, result['binding']['limits']):
        # Resource guidance takes priority over a large evidence envelope.
        _stop(result, checked, result['binding']['limits'])
        return False
    if bounded_json_size([result, checked, term], MAX_BYTES) + 128 > MAX_BYTES:
        _fail(result, 'incomplete', 'output-limit', 'Route context evidence capacity exhausted; later goals were not attempted.')
        return False
    return True


def _supported(result):
    return (bool(result['goals']) and not result['residuals']
            and all(row['status'] == 'checked-support' and _accepted_check(row.get('result'))
                    for row in result['goals']))


def _stage(operation, request, owned):
    from ._proof_contract_planned_source_inputs import _planned_input_size

    job = {'version': 1, 'operation': operation, 'request': request}
    if _planned_input_size(job) > MAX_BYTES:
        raise ValueError('aggregate route context worker input exceeds 8 MiB')
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    bounds = {**owned['limits'], 'deadlineMonotonic': float(owned['deadlineMonotonic'])}
    return _execute_job(job, bounds, state, None,
                         worker_module='ladon.proof_contract_route_context_worker')


def _stop(result, checked, limits):
    stopped = _resource_stop(checked, limits)
    if stopped:
        _fail(result, 'incomplete', stopped['code'], stopped['message'])
    return stopped is not None


def _base():
    return {'schema': 'ladon-route-context-bridge-v1', 'status': 'incomplete',
        'goalOrigin': 'generated-route-context-obligation', 'planId': None,
        'sourceFidelity': 'attributed-unreviewed', 'wholeMethodAuthority': 'none',
        'methodCorrespondence': 'unreviewed', 'ruleAttribution': 'conditional-unreviewed',
        'mathematicalFalsity': 'not-established', 'demandDischarged': False,
        'goals': [], 'residuals': [], 'memoryReportBackRequired': False, 'diagnostic': None}


def _fail(result, status, code, message):
    result.update(status=status, diagnostic={'code': code, 'message': str(message)[:1000]},
                  demandDischarged=False, memoryReportBackRequired=code == 'memory-limit')


def _bounded(result):
    from ._proof_contract_source_obligations_inputs import bounded_json_size

    if bounded_json_size(result, MAX_BYTES) <= MAX_BYTES:
        return result
    small = _base()
    if result['memoryReportBackRequired']:
        _fail(small, 'incomplete', 'memory-limit', result['diagnostic']['message'])
    else:
        _fail(small, 'incomplete', 'result-output-limit', 'Route context evidence exceeds 8 MiB.')
    return small
