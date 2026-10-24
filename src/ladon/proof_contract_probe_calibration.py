"""Checked finite separating-family calibration; no general equivalence claim."""
from __future__ import annotations

import time

from ._proof_contract_context_goals import ContextOutputLimit
from ._proof_contract_probe_calibration_checks import (
    MAX_BYTES,
    calibration_goals,
    prepare_calibration,
    separator_source,
    source_digest,
    verify_calibration,
)
from ._proof_contract_route_context_evidence import store_goal_evidence
from ._proof_contract_source_obligations_inputs import bounded_json_size
from .proof_contract_bridge import _accepted_check, _resource_stop
from .proof_contract_bridge_supervision import run_bridge_job


class ProbeCalibrationOutputLimit(ValueError):
    """No result can be published within the caller's output capacity."""

    def __init__(self, diagnostic):
        self.code = diagnostic['code']
        self.memory_report_back_required = self.code == 'memory-limit'
        super().__init__('Insufficient output capacity; no result published. ' + diagnostic['message'])


def probe_calibration_profile():
    """Describe the registered finite class; this descriptor is not proof evidence."""
    return {'objectClassId': 'fin5-bool-functions-v1', 'observationId': 'coordinate-evaluation-v1',
            'family': [0, 1, 2, 3, 4], 'theorem': 'LadonProbeCalibration.full_separates',
            'sourceDigest': source_digest(separator_source()), 'templateVersion': 'fin5-calibration-v1'}


def run_probe_calibration(request):
    """Compare finite responses, checking all three proof obligations when requested."""
    from ._proof_contract_probe_calibration_inputs import own_inputs

    started, result, cap = time.monotonic(), _base(), MAX_BYTES
    try:
        profile = probe_calibration_profile()
        owned = own_inputs(request, profile)
        cap = owned['limits']['max_output_bytes']
        result.update(profile=profile, family=owned['family'], limits=owned['limits'],
                      deadlineMonotonic=owned['deadlineMonotonic'])
        _compare(result, owned)
        if owned['deadlineMonotonic'] <= time.monotonic():
            _fail(result, 'incomplete', 'timeout', 'Shared calibration deadline expired.')
        elif owned['certificateRef'] is not None:
            _check(result, owned, profile, cap)
    except TimeoutError as error:
        _fail(result, 'incomplete', 'timeout', str(error))
    except ContextOutputLimit as error:
        _fail(result, 'incomplete', 'output-limit', str(error))
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, RecursionError) as error:
        _fail(result, 'rejected', 'invalid-calibration', str(error))
    result['elapsedSeconds'] = time.monotonic() - started
    return _bounded(result, cap)


def _compare(result, owned):
    rows = [{'index': i, 'left': owned['left'][i], 'right': owned['right'][i]} for i in owned['family']]
    agreement = all(row['left'] == row['right'] for row in rows)
    result.update(observations=rows, agreement=agreement,
                  status='scoped-agreement' if agreement else 'observed-response-difference')


def _check(result, owned, profile, cap):
    from ._proof_contract_probe_calibration_inputs import application_goal

    if bounded_json_size(result, cap) + 1 > cap:
        raise ContextOutputLimit('Calibration output capacity exhausted before proof checking.')
    adapter, environment = prepare_calibration(owned, profile)
    result.update(source=adapter, environment=environment)
    goals = calibration_goals(application_goal(owned['left'], owned['right']))
    for goal in goals:
        verify_calibration(owned, adapter, environment)
        if not _check_one(result, owned, adapter, goal, cap):
            return
        verify_calibration(owned, adapter, environment)
    equal = owned['left'] == owned['right']
    result.update(status='checked-object-equivalence' if equal else 'checked-object-distinction',
                  certificateVerified=True, objectEquivalence=equal, objectDistinction=not equal)


def _check_one(result, owned, adapter, goal, cap):
    checked = run_bridge_job('check-goal', {**adapter, 'goal': goal['goal'],
        'term': goal['term'], 'symbols': {}}, deadline_monotonic=owned['deadlineMonotonic'],
        limits=owned['limits'])
    stopped = _resource_stop(checked, owned['limits'])
    if bounded_json_size(checked, MAX_BYTES) > MAX_BYTES:
        stop = stopped or {'code': 'output-limit', 'message': 'Calibration stage evidence exceeds 8 MiB.'}
        result['goals'].append({'id': goal['id'], 'status': 'unresolved',
                                'resourceStop': stop['code'],
                                'processReceipt': checked.get('processReceipt')})
        _fail(result, 'incomplete', stop['code'], stop['message'])
        return False
    raw = checked.get('result')
    row = {**goal, 'goalDigest': source_digest(goal['goal'].encode()),
           'status': 'unresolved', 'supervision': {key: value for key, value in checked.items() if key != 'result'}}
    if isinstance(raw, dict):
        row['result'] = store_goal_evidence(owned['repoRoot'], raw)
    result['goals'].append(row)
    if stopped:
        _fail(result, 'incomplete', stopped['code'], stopped['message'])
        return False
    if bounded_json_size(result, cap) + 1 > cap:
        raise ContextOutputLimit('Calibration response capacity exhausted; later goals were not attempted.')
    if checked.get('status') != 'completed' or not _accepted_check(raw):
        _fail(result, 'incomplete', 'unresolved-proof', 'Exact proof completion, replay and trust are required.')
        return False
    row['status'] = 'checked-support'
    return True


def _base():
    return {'schema': 'ladon-probe-calibration-v1', 'status': 'incomplete',
            'scope': 'Fin 5 → Bool under coordinate evaluation only',
            'objectEquivalence': False, 'objectDistinction': False, 'certificateVerified': False,
            'sourceFidelity': 'not-assessed', 'wholeMethodAuthority': 'none',
            'mathematicalFalsity': 'not-established', 'memoryReportBackRequired': False,
            'goals': [], 'diagnostic': None}


def _fail(result, status, code, message):
    result.update(status=status, objectEquivalence=False, objectDistinction=False,
                  certificateVerified=False, memoryReportBackRequired=code == 'memory-limit',
                  diagnostic={'code': code, 'message': str(message)[:1000]})


def _bounded(result, cap):
    if bounded_json_size(result, cap) + 1 <= cap:
        return result
    small = _base()
    diagnostic = result['diagnostic']
    if result['memoryReportBackRequired']:
        _fail(small, 'incomplete', 'memory-limit', diagnostic['message'])
    else:
        _fail(small, 'incomplete', 'output-limit', 'Calibration response exceeds caller output capacity.')
    if bounded_json_size(small, cap) + 1 > cap:
        raise ProbeCalibrationOutputLimit(small['diagnostic'])
    return small
