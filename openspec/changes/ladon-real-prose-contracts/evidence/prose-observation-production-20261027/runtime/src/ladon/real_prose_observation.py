"""Supervised typed prose observation; an elaborated proposition is not a proof."""

import tempfile
import time
from pathlib import Path

from ladon.real_prose_inputs import (
    MAX_BYTES,
    SCHEMA,
    implementation_identity,
    observation_identity,
    reading_request,
)
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_candidate_limits import validate_semantic_bounds


def observe_prose_bound(root, interpretation, context, *, timeout_seconds=600,
                        max_rss_bytes=DEFAULT_MAX_RSS_BYTES, max_output_bytes=MAX_BYTES):
    limits = {'timeout_seconds': timeout_seconds, 'max_rss_bytes': max_rss_bytes,
              'max_output_bytes': max_output_bytes}
    return _observe(root, interpretation, context, limits, None, time.monotonic())


def _observe(root, interpretation, context, limits, previous, started):
    from ladon.proof_contract_obligation_supervision import _execute_job
    from ladon.real_prose_history import validate_prose_snapshot

    timeout_seconds, max_rss_bytes, max_output_bytes = (
        limits[k] for k in ('timeout_seconds', 'max_rss_bytes', 'max_output_bytes'))
    validate_semantic_bounds(timeout_seconds, max_output_bytes, max_rss_bytes)
    if timeout_seconds > 600 or max_output_bytes > MAX_BYTES:
        raise ValueError('prose observation exceeds the 600-second/8-MiB profile limits')
    root = Path(root).resolve(strict=True)
    from ladon._proof_contract_planned_source_inputs import _planned_input_size

    _planned_input_size({'interpretation': interpretation, 'context': context})
    request = reading_request(None, interpretation, context)
    identity = implementation_identity()
    bounds = {'timeout_seconds': timeout_seconds, 'deadlineMonotonic': started + timeout_seconds,
              'max_output_bytes': max_output_bytes, 'max_rss_bytes': max_rss_bytes,
              'effectiveTimeoutSeconds': timeout_seconds}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    with tempfile.TemporaryDirectory(prefix='ladon-prose-observation-') as workspace:
        job = {'version': 1, 'root': str(root), 'workspace': workspace, 'request': request,
               'deadlineMonotonic': bounds['deadlineMonotonic'], 'implementationDigest': identity,
               'maxRssBytes': max_rss_bytes, 'maxOutputBytes': max_output_bytes, 'previous': previous}
        check = _execute_job(job, bounds, state, None,
                             worker_module='ladon.real_prose_worker')
    if implementation_identity() != identity:
        raise ValueError('prose implementation changed during observation')
    result = _snapshot(request, check)
    validate_prose_snapshot(result)
    return result


def _snapshot(request, check):
    inner = check.get('result') or {}
    status = inner.get('status', 'unavailable') if check['status'] == 'completed' else 'unavailable'
    result = {'schema': SCHEMA, 'channel': 'prose', 'status': status,
              'authority': 'syntax-only', 'fidelity': 'attributed-unreviewed',
              'admission': 'unresolved', 'contract': None, 'request': request, 'check': check}
    result['snapshotId'] = observation_identity(result)
    return result


def inspect_prose_observation(snapshot, root=None):
    from ladon.real_prose_history import check_current, validate_prose_snapshot

    validate_prose_snapshot(snapshot)
    if root is not None:
        check_current(snapshot, Path(root).resolve(strict=True))
    return {'schema': 'ladon-real-prose-inspection-v1', 'status': 'validated-historical',
            'snapshotId': snapshot['snapshotId'], 'recordedStatus': snapshot['status'],
            'authority': 'none', 'freshCheck': False, 'evidenceAuthentication': 'not-established',
            'sourceFreshness': 'current' if root is not None else 'not-checked',
            'contextFreshness': _context_freshness(snapshot, root),
            'fidelity': 'attributed-unreviewed', 'admission': 'unresolved',
            'mathematicalFalsity': 'not-established'}


def replay_prose_observation(snapshot, root, **limits):
    from ladon.real_prose_history import validate_prose_snapshot

    started = time.monotonic()
    validate_prose_snapshot(snapshot)
    configured = {'timeout_seconds': 600, 'max_rss_bytes': DEFAULT_MAX_RSS_BYTES,
                  'max_output_bytes': MAX_BYTES, **limits}
    request = snapshot['request']
    return _observe(root, request['interpretation'], request['context'], configured, snapshot, started)


def _context_freshness(snapshot, root):
    if snapshot['check']['result'] is None:
        return 'not-recorded'
    return 'current' if root is not None else 'not-checked'
