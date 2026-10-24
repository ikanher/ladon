"""Immutable raw goal evidence and a bounded projection for route responses."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ._proof_contract_bridge_goals import _canonical
from ._proof_contract_context_goals import ContextOutputLimit
from ._proof_contract_source_obligations_inputs import bounded_json_size
from ._proof_contract_source_obligations_staging import _safe_create_parent, _write_probe
from .proof_contract_bridge import _resource_stop
from .proof_contract_context_worker import _quote_path
from .source_association_io import _read_regular

MAX_BYTES = 8 * 1024**2


def store_goal_evidence(root, raw):
    """Persist proof evidence with integrity checking, not writer authentication."""
    if not isinstance(raw, dict):
        raise TypeError('raw goal evidence must be an object')
    if bounded_json_size(raw, MAX_BYTES) > MAX_BYTES:
        raise ContextOutputLimit('raw goal evidence exceeds 8 MiB')
    data = _canonical(raw)
    digest = hashlib.sha256(data).hexdigest()
    relative = Path('.ladon/contract-obligations') / digest / 'evidence' / 'goal.json'
    root = Path(root).resolve(strict=True)
    _safe_create_parent(root, (root / relative).parent)
    _write_probe(root / relative, data)
    return _projection(raw, {'path': relative.as_posix(), 'sha256': digest, 'bytes': len(data)})


def load_goal_evidence(root, compact):
    """Verify bytes and projection; callers must trust the local evidence store.

    Content addressing detects later changes but does not authenticate who wrote
    the original record.
    """
    reference = compact['evidenceRef']
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256', 'bytes'}:
        raise ValueError('invalid raw goal evidence reference')
    expected_path = f".ladon/contract-obligations/{reference['sha256']}/evidence/goal.json"
    if reference['path'] != expected_path:
        raise ValueError('raw evidence is outside its content-bound location')
    path = _quote_path(Path(root).resolve(strict=True), reference['path'])
    raw_bytes = _read_regular(path, MAX_BYTES)
    if len(raw_bytes) != reference['bytes'] or hashlib.sha256(raw_bytes).hexdigest() != reference['sha256']:
        raise ValueError('raw goal evidence has changed')
    raw = json.loads(raw_bytes)
    if _projection(raw, reference) != compact:
        raise ValueError('goal evidence projection differs from immutable raw result')
    return raw


def _projection(raw, reference):
    result = {'status': raw.get('status'), 'completion': raw.get('completion'),
              'goalOrigin': raw.get('goalOrigin'), 'evidenceRef': reference}
    stopped = _resource_stop(raw, {'max_rss_bytes': 12 * 1024**3})
    if stopped:
        result['resourceStop'] = {'code': stopped['code']}
    capture = raw.get('capture')
    if isinstance(capture, dict):
        subject = capture.get('capture') or {}
        result['captureSummary'] = {'status': capture.get('status'),
                                    'captureId': subject.get('captureId')}
    return result
