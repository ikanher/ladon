"""Observe and slice one actual provider declaration in original formal source."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from .proof_contract_io import _decode
from .proof_contract_payloads import closed
from .source_association_io import _read_regular, _source_path

MAX_BYTES = 8*1024**2


def _compute(job):
    closed(job, {'version', 'operation', 'request'}, 'provider worker job')
    if job['version'] != 1 or job['operation'] != 'observe-provider':
        raise ValueError('unknown provider worker operation')
    request = job['request']
    closed(request, {'repoRoot', 'sourceSelection', 'contractArtifact', 'sourceMapArtifacts',
                     'application', 'occurrence', 'obligationId', 'limits'}, 'provider observation')
    root = Path(request['repoRoot']).resolve(strict=True)
    source = _verified_source(root, request['sourceSelection'])
    result = _observe(root, request)
    if _verified_source(root, request['sourceSelection']) != source:
        raise ValueError('provider source changed during extraction')
    return result


def _verified_source(root, selected):
    path = _source_path(root, selected['sourcePath'], selected['module'])
    source = _read_regular(path, MAX_BYTES)
    if 'sha256:'+hashlib.sha256(source).hexdigest() != selected['contentDigest']:
        raise ValueError('original provider source digest changed')
    return source


def _observe(root, request):
    from .proof_contract_bridge import _resource_stop
    from .proof_contract_bridge_supervision import bridge_limits
    from .proof_contract_formal import expand_formal_snapshot, produce_formal_snapshot
    from .proof_slice import _validate_selection

    target = request['sourceSelection']
    _validate_selection(target['module'], target['declaration'],
                        request['application'], request['occurrence'])
    limits = bridge_limits(request['limits'])
    snapshot = produce_formal_snapshot(root, target['sourcePath'], target['module'],
        target['declaration'], timeout_seconds=limits['timeout_seconds'],
        max_rss_bytes=limits['max_rss_bytes'], max_output_bytes=limits['max_output_bytes'])
    result = {'providerSnapshot': snapshot, 'slice': None,
              'coverage': {'providers': 'incomplete', 'proofBody': 'incomplete'}}
    if _resource_stop(snapshot, limits) or snapshot.get('status') != 'extracted':
        return result
    _verify_attachments(root, request, snapshot)
    expanded = expand_formal_snapshot(snapshot, root, application=request['application'],
        obligation_id=request['obligationId'], occurrence=request['occurrence'])
    result.update(slice=expanded['slice'], coverage=expanded['coverage'])
    return result


def _verify_attachments(root, request, snapshot):
    from ._proof_contract_planned_source_binding import (
        _unique_contract_artifact,
        _verified_provider_source_maps,
        _verify_provider_anchors,
    )

    expected = request['contractArtifact']
    reference = {'artifactRef': expected['artifactId'], 'kind': 'contract',
                 'localId': expected['payload']['contractId']}
    actual = _unique_contract_artifact(snapshot['artifacts'], reference)
    if actual != expected or snapshot['contract'] != expected['payload']['record']:
        raise ValueError('fresh provider statement differs from native contract owner')
    maps = _verified_provider_source_maps(expected, {'artifacts': request['sourceMapArtifacts']})
    _verify_provider_anchors(maps, snapshot, root)


def _response(result):
    body = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None},
                      sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    if len(body.encode()) > MAX_BYTES:
        return json.dumps({'status': 'completed', 'diagnostic': None,
            'result': {'status': 'output-limit', 'diagnostic': {
                'code': 'output-limit', 'message': 'Provider evidence exceeds 8 MiB.'}}})
    return body


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES+1)
        if len(raw) > MAX_BYTES:
            raise ValueError('provider input exceeds 8 MiB')
        result = _compute(_decode(raw))
        body = _response(result)
        sys.stdout.write(body)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, RecursionError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                     'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
