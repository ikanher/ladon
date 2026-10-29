"""One resource-contained observation and alias-normalization operation."""

import json
import sys
from pathlib import Path

from ladon.proof_contract_io import _decode
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_worker import _process_failure_code, _process_failure_message
from ladon.real_prose_inputs import MAX_BYTES, implementation_identity, reading_request
from ladon.real_prose_normalization import normalize_aliases
from ladon.real_prose_observation import _observe
from ladon.real_prose_shape import recognize_shape
from ladon.real_prose_shape_certificates import apply_certificates


def _compute(job):
    closed(job, {'version', 'root', 'workspace', 'request', 'startedMonotonic',
                 'deadlineMonotonic', 'timeoutSeconds', 'implementationDigest',
                 'maxRssBytes', 'maxOutputBytes'}, 'prose recognition job')
    if job['version'] != 1 or implementation_identity() != job['implementationDigest']:
        raise ValueError('stale recognition implementation')
    request = reading_request(Path(job['root']), **job['request'])
    if job['deadlineMonotonic'] != job['startedMonotonic'] + job['timeoutSeconds']:
        raise ValueError('recognition stages must share the exact original deadline')
    limits = {'timeout_seconds': job['timeoutSeconds'], 'max_rss_bytes': job['maxRssBytes'],
              'max_output_bytes': job['maxOutputBytes']}
    observation = _observe(job['root'], request['interpretation'], request['context'],
                           limits, None, job['startedMonotonic'], workspace_parent=job['workspace'])
    result = {'status': 'unavailable', 'observation': observation, 'shape': None,
              'normalization': None, 'features': None, 'diagnostic': None}
    if observation['status'] == 'observed':
        _recognize(job, observation, result)
    if implementation_identity() != job['implementationDigest']:
        raise ValueError('recognition implementation changed during execution')
    reading_request(Path(job['root']), **request)
    return result


def _recognize(job, observation, result):
    proposition = observation['check']['result']['observation']['propositionExpr']
    shape = recognize_shape(proposition)
    result['shape'] = shape
    if shape['candidate'] is None:
        result['status'] = 'unresolved'
        return
    normal = normalize_aliases(job, observation, shape)
    result['normalization'] = normal
    receipt = normal['processReceipt']
    stopped = any(receipt[k] for k in ('timed_out', 'memory_limited', 'output_limited'))
    if receipt['returncode'] != 0 or stopped:
        from ladon.process_supervisor import ProcessResult

        process = ProcessResult(**receipt)
        result['diagnostic'] = {'code': _process_failure_code(process),
                               'message': _process_failure_message(process, job['maxRssBytes'])}
        return
    if normal['worker'] is None or normal['worker']['status'] == 'unavailable':
        return
    features = apply_certificates(shape, proposition, normal['worker']['results'])
    result['features'] = features
    result['status'] = 'recognized' if features['normalizationState'] == 'checked' else 'unresolved'


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('prose recognition request exceeds 8 MiB')
        result = _compute(_decode(raw))
        encoded = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError('prose recognition result exceeds 8 MiB')
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'result': None, 'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
