"""Native-demand-bound observation of an original provider proof application."""
from __future__ import annotations

import copy
import math
import time
from pathlib import Path

from ._proof_contract_obligation_check_inputs import (
    _requirements_for_demand,
    _validate_context,
    _validation_plan,
)
from ._proof_contract_planned_source_inputs import _planned_deadline, _planned_input_size
from .proof_contract_bridge import _resource_stop
from .proof_contract_bridge_supervision import bridge_limits
from .proof_contract_obligation_supervision import run_obligation_validation
from .proof_contract_provider_supervision import run_provider_job
from .proof_contract_source_obligations import _plain

_KEYS = {'repoRoot', 'analysisArtifact', 'context', 'providerSliceRequest',
         'application', 'occurrence', 'deadlineMonotonic', 'limits'}
MAX_BYTES = 8*1024**2


def make_provider_slice_request(analysis, context, route, demand, requirement, deadline, limits):
    """Build an unexecuted request from validated native owners, with no authority."""
    from ._proof_contract_provider_requests import make_provider_slice_request as build

    return build(analysis, context, route, demand, requirement, deadline, limits)


def expand_obligation_provider(request):
    """Revalidate exact native bindings and observe one original application.

    Application extraction retains the unresolved demand; it never supplies a
    missing premise or certifies a generated goal.
    """
    started = time.monotonic()
    result = _base_result()
    try:
        owned = _own_inputs(request)
        _expand(result, owned)
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError) as error:
        _fail(result, 'rejected', 'invalid-provider-expansion', str(error))
    result['elapsedSeconds'] = time.monotonic()-started
    return _bounded(result)


def _own_inputs(request):
    if not isinstance(request, dict) or set(request) != _KEYS:
        raise ValueError('provider expansion request must use the closed schema')
    if _planned_input_size(request) > MAX_BYTES:
        raise ValueError('aggregate provider expansion input exceeds 8 MiB')
    _finite_deadline(request['deadlineMonotonic'])
    _validate_context(request['context'])
    limits = bridge_limits(request['limits'])
    if not isinstance(request['providerSliceRequest'], dict):
        raise TypeError('providerSliceRequest must be a mapping')
    _validate_application(request['application'], request['occurrence'])
    owned = copy.deepcopy(request)
    owned['limits'] = limits
    return owned


def _validate_application(application, occurrence):
    from .proof_slice import _NAME

    if not isinstance(application, str) or not _NAME.fullmatch(application):
        raise ValueError('provider application must be an ordinary Lean name')
    if type(occurrence) is not int or not 0 <= occurrence < 4096:
        raise ValueError('provider application occurrence must be between 0 and 4095')


def _finite_deadline(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('provider deadline must be finite')
    return float(value)


def _expand(result, owned):
    candidate = owned['providerSliceRequest']
    deadline = min(owned['deadlineMonotonic'],
                   _finite_deadline(candidate['deadlineMonotonic']))
    deadline = _initial_deadline(owned['analysisArtifact'], deadline)
    if deadline <= time.monotonic():
        _fail(result, 'incomplete', 'timeout', 'Shared provider deadline expired.')
        return
    limits = _effective_limits(owned['limits'], candidate['bounds'])
    checked = run_obligation_validation(owned['analysisArtifact'], owned['context'],
                                        deadline_monotonic=deadline, limits=limits)
    result['nativeValidation'] = {key: value for key, value in checked.items() if key != 'result'}
    if _stop(result, checked, limits):
        return
    if checked['status'] != 'completed':
        _fail(result, 'rejected', 'native-validation-failed', 'Exact native validation failed.')
        return
    plan_request, plan_result = _validation_plan(checked, owned['context'])
    deadline = _planned_deadline(deadline, plan_request)
    expected = _rebuild_request(owned, plan_result)
    if candidate != expected:
        raise ValueError('provider request differs from the exact native route/source binding')
    result.update(request=_plain(owned), unresolvedDemand=copy.deepcopy(expected['binding']['demand']))
    if deadline <= time.monotonic():
        _fail(result, 'incomplete', 'timeout', 'Inherited provider deadline expired.')
        return
    if expected['sourceSelection'] is None:
        _fail(result, 'unavailable', 'source-anchor-unavailable',
              'No unique source declaration anchor is available for this native provider.')
        return
    _observe_provider(result, owned, expected, deadline, limits)


def _initial_deadline(artifact, outer):
    from datetime import UTC, datetime

    from ._proof_contract_obligations_validation import _parse_deadline

    if not isinstance(artifact, dict):
        raise TypeError('native analysis must be a mapping')
    payload = artifact.get('payload', {})
    request = payload.get('request', {}) if isinstance(payload, dict) else {}
    bounds = request.get('bounds') if isinstance(request, dict) else None
    if bounds is None:
        return outer
    if not isinstance(bounds, dict):
        raise TypeError('native planner bounds must be a mapping')
    parsed = _parse_deadline(bounds.get('deadlineUtc'))
    if parsed is None:
        return outer
    return min(outer, time.monotonic()+(parsed-datetime.now(UTC)).total_seconds())


def _effective_limits(outer, original):
    original = bridge_limits(original)
    return {key: min(outer[key], original[key]) for key in outer}


def _rebuild_request(owned, plan_result):
    candidate = owned['providerSliceRequest']
    routes = [r for r in plan_result['routeComparisons'] if r['routeId'] == candidate['routeId']]
    if len(routes) != 1:
        raise ValueError('provider route is not uniquely retained')
    route = routes[0]
    demands = [d for d in route['obligationBundle']['demands']
               if d['demandId'] == candidate['obligation'] and d['status'] == 'requires-source-check']
    if len(demands) != 1:
        raise ValueError('provider demand is not uniquely retained')
    demand = demands[0]
    requirements = _requirements_for_demand(route['backwardRequirements'], demand)
    if not requirements:
        raise ValueError('provider demand has no matching source requirement')
    return make_provider_slice_request(owned['analysisArtifact'], owned['context'], route,
        demand, requirements[0][1], candidate['deadlineMonotonic'], candidate['bounds'])


def _observe_provider(result, owned, expected, deadline, limits):
    target = expected['sourceSelection']
    from .proof_slice import _validate_selection

    _validate_selection(target['module'], target['declaration'],
                        owned['application'], owned['occurrence'])
    by_id = {row['artifactId']: row for row in owned['context']['artifacts']}
    contract = by_id[expected['contractRef']['artifactRef']]
    maps = [by_id[ref['artifactRef']] for ref in contract['payload']['sourceMapRefs']]
    job = {'repoRoot': str(Path(owned['repoRoot']).resolve()), 'sourceSelection': target,
           'contractArtifact': contract, 'sourceMapArtifacts': maps,
           'application': owned['application'], 'occurrence': owned['occurrence'],
           'obligationId': expected['obligation'], 'limits': limits}
    observed = run_provider_job(job, deadline_monotonic=deadline, limits=limits)
    result['worker'] = {key: value for key, value in observed.items() if key != 'result'}
    if _stop(result, observed, limits):
        return
    if observed['status'] != 'completed':
        _fail(result, 'rejected', 'source-observation-rejected', 'Original source observation was rejected.')
        return
    body = observed['result']
    result.update(providerSnapshot=body['providerSnapshot'], slice=body['slice'], coverage=body['coverage'])
    complete = isinstance(body['slice'], dict) and body['slice'].get('complete') is True
    _fail(result, 'observed' if complete else 'incomplete',
          'original-provider-application' if complete else 'application-slice-unavailable',
          'Observation covers the selected original application; its generated demand remains unresolved.')


def _stop(result, value, limits):
    stopped = _resource_stop(value, limits)
    if not stopped:
        return False
    _fail(result, 'incomplete', stopped['code'], stopped['message'])
    return True


def _base_result():
    return {'schema': 'ladon-obligation-provider-expansion-v1', 'status': 'incomplete',
        'goalOrigin': 'original-provider-source', 'authority': 'observation-only',
        'wholeMethodAuthority': 'none', 'mathematicalFalsity': 'not-established',
        'sourceFidelity': 'attributed-unreviewed', 'demandDischarged': False,
        'unresolvedDemand': None, 'providerSnapshot': None, 'slice': None,
        'coverage': {'providers': 'incomplete', 'proofBody': 'incomplete'}, 'diagnostic': None}


def _fail(result, status, code, message):
    result.update(status=status, diagnostic={'code': code, 'message': str(message)[:1000]},
                  memoryReportBackRequired=code == 'memory-limit')


def _bounded(result):
    if _planned_input_size(result)+1 <= MAX_BYTES:
        return result
    small = _base_result()
    if result.get('memoryReportBackRequired'):
        _fail(small, 'incomplete', 'memory-limit', result['diagnostic']['message'])
    else:
        _fail(small, 'incomplete', 'result-output-limit', 'Provider evidence exceeds 8 MiB.')
    return small
