"""Keep native authoring, exact owner validation and recognition under one cap."""

import json
import sys
from pathlib import Path

from ladon.proof_contract_payloads import closed
from ladon.real_prose_inputs import MAX_BYTES, implementation_identity, reading_request
from ladon.real_prose_native_artifacts import authored_artifacts
from ladon.real_prose_recognition import _recognize_bound, inspect_recognition


def compute(job):
    closed(job, {'version', 'root', 'workspace', 'request', 'startedMonotonic', 'timeoutSeconds',
                 'deadlineMonotonic', 'implementationDigest', 'maxRssBytes', 'maxOutputBytes', 'previous'},
           'authored Real job')
    if (job['version'] != 1 or implementation_identity() != job['implementationDigest']
            or job['deadlineMonotonic'] != job['startedMonotonic'] + job['timeoutSeconds']):
        raise ValueError('authored Real requires its current implementation and shared deadline')
    request = job['request']
    closed(request, {'interpretation', 'context', 'alternativeId', 'author'}, 'authored Real request')
    if job['previous'] is not None:
        from ladon.real_prose_native_production import inspect_real_prose_bound

        inspect_real_prose_bound(job['previous'], Path(job['root']))
        if job['previous']['request'] != request:
            raise ValueError('authored Real replay changed its original request')
    recognition = _recognize_bound(job['root'], request['interpretation'], request['context'],
        timeout_seconds=job['timeoutSeconds'], max_rss_bytes=job['maxRssBytes'],
        max_output_bytes=job['maxOutputBytes'], started=job['startedMonotonic'],
        workspace_parent=job['workspace'])
    artifacts = []
    if recognition['status'] == 'recognized':
        sources = recognition['check']['result']['observation']['check']['result']['artifacts']
        artifacts = authored_artifacts(recognition, sources,
                                       alternative_id=request['alternativeId'], author=request['author'])
    reading_request(Path(job['root']), request['interpretation'], request['context'])
    inspect_recognition(recognition, Path(job['root']))
    if implementation_identity() != job['implementationDigest']:
        raise ValueError('authored Real implementation changed during authoring')
    return {'status': 'authored' if artifacts else recognition['status'],
            'recognition': None if artifacts else recognition, 'artifacts': artifacts}


def main():
    from ladon.proof_contract_io import _decode

    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('authored Real input exceeds 8 MiB')
        result = compute(_decode(raw))
        encoded = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError('authored Real result exceeds 8 MiB')
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'result': None, 'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
