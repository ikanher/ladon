"""One finite bridge stage; its supervisor bounds Lean and all descendants."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from .proof_contract_io import _decode
from .proof_contract_payloads import closed
from .source_association_io import _read_regular

MAX_BYTES = 8 * 1024**2


def _compute(job):
    closed(job, {'version', 'operation', 'request'}, 'bridge job')
    if job['version'] != 1:
        raise ValueError('unknown bridge job version')
    request = job['request']
    keys = {'repoRoot', 'sourcePath', 'sourceDigest'}
    if job['operation'] == 'extract-provider':
        closed(request, keys | {'declaration', 'application'}, 'bridge extraction')
    elif job['operation'] == 'check-goal':
        closed(request, keys | {'goal', 'term', 'symbols'}, 'bridge goal check')
    else:
        raise ValueError('unknown bridge operation')
    root = Path(request['repoRoot']).resolve(strict=True)
    source = _verified_source(root, request)
    result = _operation(root, request, source, job['operation'])
    if _verified_source(root, request) != source:
        raise ValueError('bridge source changed during stage')
    return result


def _verified_source(root, request):
    path = (root / request['sourcePath']).resolve(strict=True)
    path.relative_to(root)
    source = _read_regular(path, MAX_BYTES)
    if 'sha256:' + hashlib.sha256(source).hexdigest() != request['sourceDigest']:
        raise ValueError('bridge source digest changed')
    return source


def _operation(root, request, source, operation):
    from .proof_slice import extract_proof_slice, pinned_toolchain

    if operation == 'extract-provider':
        return extract_proof_slice(root, request['sourcePath'], 'Bridge',
            request['declaration'], request['application'], scoped=True)
    from .correspondence_check import _check_goal

    return _check_goal(request['goal'], request['term'], root, source,
                       request['symbols'], pinned_toolchain(root))


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('bridge input exceeds 8 MiB')
        result = _compute(_decode(raw))
        body = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None},
                          sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        if len(body.encode()) > MAX_BYTES:
            raise ValueError('bridge output exceeds 8 MiB')
        sys.stdout.write(body)
        return 0
    except (ValueError, TypeError, KeyError, OSError, OverflowError, RecursionError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                     'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
