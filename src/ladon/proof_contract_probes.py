"""Local source-bound application probes with independent Lean replay and trust."""
from __future__ import annotations

import copy
import hashlib
import time

from ._proof_contract_context_goals import ContextOutputLimit
from ._proof_contract_probe_inputs import probe_inputs
from ._proof_contract_probe_pair import MAX_BYTES
from ._proof_contract_probe_reporting import (
    ApplicationProbeOutputLimit,
    base_result,
    bounded_result,
    fail,
    require_capacity,
)
from ._proof_contract_route_context_evidence import load_goal_evidence, store_goal_evidence
from .proof_contract_bridge import _accepted_check, _resource_stop
from .proof_contract_obligation_supervision import _execute_job

__all__ = [
    'ApplicationProbeOutputLimit',
    'application_probe_profile',
    'check_application_probe',
    'plan_application_probe',
]


def application_probe_profile():
    """Catalog registered templates; only the first family has a source consumer."""
    from ._proof_contract_probe_templates import application_probe_profile as profile

    return profile()


def plan_application_probe(request):
    """Plan exact original propositions without accepting caller-authored goals."""
    return _run(request)


def check_application_probe(request, plan_id, terms, *, cached_result=None):
    """Regenerate a saved subject, then check separately attributed proof terms.

    Cached results are trusted local Ladon outputs, not authenticated credentials;
    do not reuse cache data from an untrusted workspace or writer.
    """
    return _run(request, plan_id, terms, cached_result, checking=True)


def _run(request, plan_id=None, terms=None, cached_result=None, checking=False):
    started, result, cap = time.monotonic(), base_result(), MAX_BYTES
    try:
        owned = probe_inputs(request, plan_id, terms, cached_result, checking=checking)
        cap = owned['limits']['max_output_bytes']
        require_capacity(result, cap)
        if owned['deadlineMonotonic'] <= time.monotonic():
            fail(result, 'incomplete', 'timeout', 'Shared application-probe deadline expired before work began.')
        else:
            _prepare(result, owned, cap)
        if checking and result['status'] == 'planned':
            _check(result, owned, plan_id, terms, cached_result, cap)
    except ContextOutputLimit as error:
        fail(result, 'incomplete', 'output-limit', str(error))
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, RecursionError) as error:
        fail(result, 'rejected', 'invalid-application-probe', str(error))
    result['elapsedSeconds'] = time.monotonic() - started
    return bounded_result(result, cap)


def _stage(operation, request, owned):
    job = {'version': 1, 'operation': operation, 'request': request}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    bounds = {**owned['limits'], 'deadlineMonotonic': owned['deadlineMonotonic']}
    return _execute_job(job, bounds, state, None, worker_module='ladon.proof_contract_probe_worker')


def _stop(result, checked, owned):
    stopped = _resource_stop(checked, owned['limits'])
    if stopped:
        fail(result, 'incomplete', stopped['code'], stopped['message'])
    return stopped is not None


def _prepare(result, owned, cap):
    checked = _stage('prepare-probe', owned, owned)
    result['preparation'] = {k: v for k, v in checked.items() if k != 'result'}
    if _stop(result, checked, owned):
        result['partialPreparation'] = checked.get('result')
        return
    if checked['status'] != 'completed':
        fail(result, 'rejected', 'probe-preparation-rejected', checked['diagnostic'])
        return
    prepared = checked['result']
    status = prepared.get('status')
    if status == 'unsupported':
        result.update(status='unsupported', artifact=prepared['artifact'], residuals=prepared['residuals'])
    elif status == 'prepared':
        result.update({k: v for k, v in prepared.items() if k != 'status'})
        result.update(status='planned', goals=copy.deepcopy(prepared['goals']))
    else:
        result['partialPreparation'] = prepared
        fail(result, 'incomplete', 'probe-preparation-incomplete', 'A complete source context is required.')
    require_capacity(result, cap)


def _check(result, owned, plan_id, terms, cached_result, cap):
    if result['planId'] != plan_id:
        raise ValueError('saved probe differs from regenerated source, context, clock or limits')
    for goal in result['goals']:
        goal.update(status='unresolved', reused=False)
    for goal in result['goals']:
        if not _check_goal(result, owned, goal, terms, cached_result, cap):
            return
    result['cache'] = _result_cache(result)
    _finalize_check(result, owned)


def _check_goal(result, owned, goal, terms, cached_result, cap):
    cached = _cached_goal(cached_result, result, goal, owned)
    term = terms.get(goal['goalId'])
    if cached is not None and (term is None or term == cached['term']):
        goal.update(term=cached['term'], result=cached['result'],
                    status='checked-support', reused=True)
        return True
    return term is None or _check_one(result, owned, goal, term, cap)


def _finalize_check(result, owned):
    if all(g['status'] == 'checked-support' for g in result['goals']):
        kind = owned['template']['kind']
        result.update(status='checked-local-nonimplication' if kind == 'counterexample'
                      else 'checked-local-implication', checkerAuthority='checked-local-goals')
    else:
        fail(result, 'unresolved', 'unresolved-proof', 'Both exact goals require completion, replay and trust.')


def _cached_goal(cache, current, goal, owned):
    """Return only a hash-verified accepted receipt for this exact regenerated goal."""
    if not isinstance(cache, dict) or cache.get('planId') != current['planId']:
        return None
    full_result = cache.get('schema') == 'ladon-application-probe-v1'
    for entry in cache['goals']:
        if _same_cached_goal(entry, goal, full_result):
            return _restore_cached_goal(entry, current, goal, owned, full_result)
    return None


def _same_cached_goal(entry, goal, full_result):
    return (not (full_result and entry.get('status') != 'checked-support')
            and entry['goalId'] == goal['goalId']
            and entry['goalDigest'] == goal['goalDigest']
            and entry['goal'] == goal['goal'])


def _restore_cached_goal(entry, current, goal, owned, full_result):
    try:
        raw = load_goal_evidence(owned['repoRoot'], entry['result'])
    except (ValueError, TypeError, KeyError, OSError, RecursionError):
        return None
    if not _accepted_cache_receipt(entry, raw, current, goal, full_result):
        return None
    return {'term': entry['term'], 'result': copy.deepcopy(entry['result'])}


def _accepted_cache_receipt(entry, raw, current, goal, full_result):
    if entry['result'].get('status') != 'supported' or not _accepted_check(raw):
        return False
    completion = raw.get('completion')
    if not isinstance(completion, dict):
        return False
    digest = 'sha256:' + hashlib.sha256(entry['term'].encode('utf-8')).hexdigest()
    if not _digest_matches(completion.get('termDigest'), digest):
        return False
    if not full_result and entry['termDigest'] != digest:
        return False
    binding = raw.get('ladonApplicationProbeBinding')
    return binding == _goal_receipt_binding(current, goal, digest)


def _goal_receipt_binding(current, goal, term_digest):
    return {'planId': current['planId'], 'goalId': goal['goalId'],
            'goalDigest': goal['goalDigest'], 'goal': goal['goal'],
            'termDigest': term_digest}


def _digest_matches(actual, expected):
    if not isinstance(actual, str):
        return False
    return actual.removeprefix('sha256:') == expected.removeprefix('sha256:')


def _result_cache(result):
    rows = []
    for goal in result['goals']:
        if goal.get('status') != 'checked-support' or not isinstance(goal.get('result'), dict):
            continue
        term = goal.get('term')
        if not isinstance(term, str):
            continue
        rows.append({'goalId': goal['goalId'], 'goalDigest': goal['goalDigest'],
            'goal': goal['goal'], 'term': term,
            'termDigest': 'sha256:' + hashlib.sha256(term.encode('utf-8')).hexdigest(),
            'result': copy.deepcopy(goal['result'])})
    return {'schema': 'ladon-application-probe-cache-v1', 'planId': result['planId'],
            'goals': rows}


def _check_one(result, owned, goal, term, cap):
    require_capacity(result, cap)
    checked = _stage('check-probe-goal', {**result['adapter'], 'goal': goal['goal'],
        'term': term, 'symbols': result['symbols'], 'binding': result['binding']}, owned)
    goal.update(term=term, supervision={k: v for k, v in checked.items() if k != 'result'})
    stopped = _resource_stop(checked, owned['limits'])
    raw = checked.get('result')
    if stopped:
        fail(result, 'incomplete', stopped['code'], stopped['message'])
        _save_stopped_raw(result, owned, goal, raw, checked, cap)
        return False
    # Enforce the caller's aggregate response capacity before persisting any
    # proof evidence or copying the full worker result into another structure.
    require_capacity([result, checked], cap)
    if isinstance(raw, dict):
        if checked['status'] == 'completed' and _accepted_check(raw):
            raw = _bind_goal_receipt(raw, result, goal, term)
            checked['result'] = raw
        goal['result'] = store_goal_evidence(owned['repoRoot'], raw)
    require_capacity(result, cap)
    if checked['status'] == 'completed' and _accepted_check(raw):
        goal['status'] = 'checked-support'
    return True


def _bind_goal_receipt(raw, result, goal, term):
    bound = copy.deepcopy(raw)
    binding_key = 'ladonApplicationProbeBinding'
    if binding_key in bound:
        raise ValueError('checker result already contains application-probe receipt binding')
    term_digest = 'sha256:' + hashlib.sha256(term.encode('utf-8')).hexdigest()
    bound[binding_key] = _goal_receipt_binding(result, goal, term_digest)
    return bound


def _save_stopped_raw(result, owned, goal, raw, checked, cap):
    if not isinstance(raw, dict):
        return
    try:
        require_capacity([result, checked], cap)
        goal['result'] = store_goal_evidence(owned['repoRoot'], raw)
    except ContextOutputLimit:
        # Preserve the resource stop and its actual cap even when raw evidence
        # cannot fit the publication envelope. No proof work may follow it.
        return
