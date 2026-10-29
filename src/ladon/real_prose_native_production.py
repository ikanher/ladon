"""Fresh supervised authoring and authority-free inspection of native Real readings."""

import tempfile
import time
from pathlib import Path

from ladon.proof_contract_payloads import closed, identifier
from ladon.real_prose_inputs import (
    MAX_BYTES,
    implementation_identity,
    observation_identity,
    reading_request,
)
from ladon.real_prose_native_payload import recognition_history
from ladon.real_prose_recognition import inspect_recognition
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_candidate_limits import validate_semantic_bounds

SCHEMA = 'ladon-real-prose-production-v1'


def produce_real_prose_bound(root, interpretation, context, *, alternative_id, author='caller',
                             timeout_seconds=600, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
                             max_output_bytes=MAX_BYTES):
    return _produce(root, interpretation, context, alternative_id, author,
                    timeout_seconds, max_rss_bytes, max_output_bytes, time.monotonic())


def _produce(root, interpretation, context, alternative_id, author, timeout, rss, output, started,
             previous=None):
    from ladon.proof_contract_obligation_supervision import _execute_job

    validate_semantic_bounds(timeout, output, rss)
    if timeout > 600 or output > MAX_BYTES:
        raise ValueError('authored Real production exceeds the 600-second/8-MiB profile limits')
    identifier(alternative_id, 'alternative ID')
    identifier(author, 'author')
    request = {**reading_request(None, interpretation, context), 'alternativeId': alternative_id, 'author': author}
    identity = implementation_identity()
    bounds = {'timeout_seconds': timeout, 'deadlineMonotonic': started + timeout,
              'max_output_bytes': output, 'max_rss_bytes': rss, 'effectiveTimeoutSeconds': timeout}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    with tempfile.TemporaryDirectory(prefix='ladon-prose-native-') as workspace:
        job = {'version': 1, 'root': str(Path(root).resolve(strict=True)), 'workspace': workspace,
               'request': request, 'startedMonotonic': started, 'timeoutSeconds': timeout,
               'deadlineMonotonic': started + timeout, 'implementationDigest': identity,
               'maxRssBytes': rss, 'maxOutputBytes': output, 'previous': previous}
        check = _execute_job(job, bounds, state, None, worker_module='ladon.real_prose_native_worker')
    if implementation_identity() != identity:
        raise ValueError('authored Real implementation changed during production')
    inner = check.get('result') or {}
    status = inner.get('status', 'unavailable') if check['status'] == 'completed' else 'unavailable'
    result = {'schema': SCHEMA, 'status': status, 'channel': 'prose', 'authority': 'none',
              'fidelity': 'attributed-unreviewed', 'admission': 'unresolved', 'request': request, 'check': check}
    result['snapshotId'] = observation_identity(result)
    validate_production(result)
    return result


def _recognition(inner):
    return recognition_history(inner['artifacts'][-1]['payload']) if inner['artifacts'] else inner['recognition']


def validate_production(snapshot):
    from ladon.real_prose_native_artifacts import authored_artifacts
    from ladon.real_prose_recognition_history import validate_recognition

    closed(snapshot, {'schema', 'status', 'channel', 'authority', 'fidelity', 'admission',
                      'request', 'check', 'snapshotId'}, 'authored Real production')
    if (snapshot['schema'] != SCHEMA or snapshot['snapshotId'] != observation_identity(snapshot)
            or snapshot['channel'] != 'prose' or snapshot['authority'] != 'none'
            or snapshot['fidelity'] != 'attributed-unreviewed' or snapshot['admission'] != 'unresolved'):
        raise ValueError('invalid or promoted authored Real production')
    request = snapshot['request']
    closed(request, {'interpretation', 'context', 'alternativeId', 'author'}, 'authored Real request')
    reading_request(None, request['interpretation'], request['context'])
    identifier(request['alternativeId'], 'alternative ID')
    identifier(request['author'], 'author')
    _validate_check(snapshot, authored_artifacts, validate_recognition)


def _validate_check(snapshot, authored_artifacts, validate_recognition):
    from ladon.real_prose_history import _completed_receipt

    request = snapshot['request']
    check = snapshot['check']
    closed(check, {'schema', 'status', 'result', 'diagnostic', 'processReceipt', 'workerInputDigest', 'bounds'},
           'authored Real supervision')
    if check['schema'] != 'ladon-supervised-obligation-planner-v1':
        raise ValueError('authored Real requires its supervised operation')
    if check['status'] != 'completed':
        if (check['status'] not in {'rejected', 'incomplete'}
                or snapshot['status'] != 'unavailable' or check['result'] is not None):
            raise ValueError('stopped production cannot retain a native contract')
        return
    _completed_receipt(check)
    inner = check['result']
    closed(inner, {'status', 'recognition', 'artifacts'}, 'authored Real worker result')
    recognition = _recognition(inner)
    validate_recognition(recognition)
    if recognition['request'] != {k: request[k] for k in ('interpretation', 'context')}:
        raise ValueError('authored Real production changed its exact reading or context')
    _validate_outcome(snapshot, inner, recognition, authored_artifacts)


def _validate_outcome(snapshot, inner, recognition, authored_artifacts):
    if recognition['status'] == 'recognized':
        _validate_artifacts(snapshot, inner, recognition, authored_artifacts)
    elif (inner['artifacts'] != [] or snapshot['status'] != recognition['status']
          or inner['status'] != snapshot['status']):
        raise ValueError('unrecognized reading cannot emit an authored native contract')


def _validate_artifacts(snapshot, inner, recognition, builder):
    request = snapshot['request']
    sources = recognition['check']['result']['observation']['check']['result']['artifacts']
    expected = builder(recognition, sources, alternative_id=request['alternativeId'], author=request['author'])
    if (inner['artifacts'] != expected or inner['recognition'] is not None
            or inner['status'] != 'authored' or snapshot['status'] != 'authored'):
        raise ValueError('authored Real production differs from exact native reconstruction')


def inspect_real_prose_bound(snapshot, root=None):
    validate_production(snapshot)
    inner = snapshot['check']['result']
    recognition = _recognition(inner) if inner else None
    if recognition is not None:
        inspected = inspect_recognition(recognition, root)
    else:
        inspected = {'sourceFreshness': 'not-checked'}
    return {'schema': 'ladon-real-prose-production-inspection-v1', 'status': 'validated-historical',
            'recordedStatus': snapshot['status'], 'authority': 'none', 'freshCheck': False,
            'evidenceAuthentication': 'not-established', 'sourceFreshness': inspected['sourceFreshness'],
            'fidelity': 'attributed-unreviewed', 'admission': 'unresolved',
            'mathematicalFalsity': 'not-established',
            'contract': inner['artifacts'][-1]['payload']['record'] if inner and inner['artifacts'] else None}


def replay_real_prose_bound(snapshot, root, **limits):
    started = time.monotonic()
    request = snapshot['request']
    configured = {'timeout_seconds': 600, 'max_rss_bytes': DEFAULT_MAX_RSS_BYTES,
                  'max_output_bytes': MAX_BYTES, **limits}
    return _produce(root, request['interpretation'], request['context'], request['alternativeId'],
                    request['author'], configured['timeout_seconds'], configured['max_rss_bytes'],
                    configured['max_output_bytes'], started, previous=snapshot)
