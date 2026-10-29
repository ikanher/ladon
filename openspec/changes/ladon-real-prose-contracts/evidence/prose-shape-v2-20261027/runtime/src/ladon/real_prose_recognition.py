"""Public versioned Real-bound recognition, distinct from semantic admission."""

import tempfile
import time
from pathlib import Path

from ladon.real_prose_inputs import (
    MAX_BYTES,
    implementation_identity,
    observation_identity,
    reading_request,
)
from ladon.real_prose_shape import PROFILE_ID
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_candidate_limits import validate_semantic_bounds

SCHEMA = 'ladon-real-prose-recognition-v1'


def recognize_prose_bound(root, interpretation, context, *, timeout_seconds=600,
                          max_rss_bytes=DEFAULT_MAX_RSS_BYTES, max_output_bytes=MAX_BYTES):
    from ladon._proof_contract_planned_source_inputs import _planned_input_size
    from ladon.proof_contract_obligation_supervision import _execute_job
    from ladon.real_prose_recognition_history import validate_recognition

    started = time.monotonic()
    validate_semantic_bounds(timeout_seconds, max_output_bytes, max_rss_bytes)
    if max_output_bytes > MAX_BYTES:
        raise ValueError('recognition worker output exceeds 8 MiB')
    _planned_input_size({'interpretation': interpretation, 'context': context})
    request = reading_request(None, interpretation, context)
    identity = implementation_identity()
    bounds = {'timeout_seconds': timeout_seconds, 'deadlineMonotonic': started + timeout_seconds,
              'max_output_bytes': max_output_bytes, 'max_rss_bytes': max_rss_bytes,
              'effectiveTimeoutSeconds': timeout_seconds}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    with tempfile.TemporaryDirectory(prefix='ladon-prose-recognition-') as workspace:
        job = {'version': 1, 'root': str(Path(root).resolve(strict=True)), 'workspace': workspace,
               'request': request, 'startedMonotonic': started, 'timeoutSeconds': timeout_seconds,
               'deadlineMonotonic': bounds['deadlineMonotonic'], 'implementationDigest': identity,
               'maxRssBytes': max_rss_bytes, 'maxOutputBytes': max_output_bytes}
        check = _execute_job(job, bounds, state, None,
                             worker_module='ladon.real_prose_recognition_worker')
    if implementation_identity() != identity:
        raise ValueError('recognition implementation changed during execution')
    result = _snapshot(request, check)
    validate_recognition(result)
    return result


def _snapshot(request, check):
    inner = check.get('result') or {}
    status = inner.get('status', 'unavailable') if check['status'] == 'completed' else 'unavailable'
    result = {'schema': SCHEMA, 'channel': 'prose', 'profileId': PROFILE_ID, 'status': status,
              'authority': 'syntax-only', 'fidelity': 'attributed-unreviewed',
              'admission': 'unresolved', 'contract': None, 'request': request, 'check': check}
    result['snapshotId'] = observation_identity(result)
    return result


def inspect_recognition(snapshot, root=None):
    from ladon.real_prose_history import check_current
    from ladon.real_prose_recognition_history import validate_recognition

    validate_recognition(snapshot)
    inner = snapshot['check']['result']
    if root is not None and inner is not None:
        check_current(inner['observation'], Path(root).resolve(strict=True))
    return {'schema': 'ladon-real-prose-recognition-inspection-v1', 'status': 'validated-historical',
            'recordedStatus': snapshot['status'], 'profileId': PROFILE_ID,
            'authority': 'none', 'freshCheck': False, 'evidenceAuthentication': 'not-established',
            'admission': 'unresolved', 'sourceFreshness': 'current' if root is not None and inner else 'not-checked',
            'mathematicalFalsity': 'not-established', 'features': inner['features'] if inner else None}
