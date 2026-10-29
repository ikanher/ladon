"""Resource-contained source preparation and proposition observation."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

from ladon.correspondence_interpretation import UnsupportedInterpretation
from ladon.lean_toolchain import verify_toolchain_identities
from ladon.proof_contract_io import _decode
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_worker import _process_failure_code, _process_failure_message
from ladon.proof_slice import pinned_toolchain
from ladon.proofir_correspondence import interpretation_artifacts
from ladon.real_prose_execution import observe_stable
from ladon.real_prose_expression import parse_worker
from ladon.real_prose_inputs import (
    MAX_BYTES,
    context_source,
    implementation_identity,
    reading_request,
    sha,
)
from ladon.semantic_lean_execution import prepare_direct_lean_execution


def _prepare(job):
    closed(job, {'version', 'root', 'workspace', 'request', 'deadlineMonotonic',
                 'implementationDigest', 'maxRssBytes', 'maxOutputBytes', 'previous'}, 'prose worker job')
    if job['version'] != 1 or implementation_identity() != job['implementationDigest']:
        raise ValueError('stale prose observer implementation')
    root = Path(job['root']).resolve(strict=True)
    request = reading_request(root, **job['request'])
    if job['previous'] is not None:
        from ladon.real_prose_history import check_current, validate_prose_snapshot

        validate_prose_snapshot(job['previous'])
        if job['previous']['request'] != request:
            raise ValueError('prose replay request differs from its original reading')
        check_current(job['previous'], root)
    source = context_source(root, request['context'])
    context = pinned_toolchain(root)
    execution = prepare_direct_lean_execution(root, None, context, require_compiled_module=False)
    return root, request, source, context, execution


def _result(job, request, source, context):
    return {'status': 'unavailable', 'contextSource': {**request['context'],
                'sha256': sha(source), 'text': source.decode()},
            'environment': context.context_identity, 'leanVersion': context.lean_release,
            'implementationDigest': job['implementationDigest'], 'generated': None,
            'artifacts': list(interpretation_artifacts(request['interpretation'],
                                                      context.context_identity,
                                                      source_root=Path(job['root']))),
            'compiledInventory': None, 'observation': None, 'workerJson': None, 'processReceipts': [], 'residuals': []}


def _observe(job, request, source, context, execution, result):
    try:
        processes, encoded, generated, inventory = observe_stable(job, request, source, context, execution)
    except UnsupportedInterpretation as error:
        result['status'] = 'unsupported'
        result['residuals'] = [{'code': 'unsupported-interpretation', 'message': str(error)}]
        return
    result['generated'] = generated
    result['processReceipts'] = [asdict(process) for process in processes]
    result['compiledInventory'] = inventory
    process = processes[-1]
    if not process.succeeded:
        result['residuals'] = [{'code': _process_failure_code(process),
                              'message': _process_failure_message(process, job['maxRssBytes'])}]
        return
    if encoded is None:
        raise ValueError('prose helper returned no completed observation')
    result['workerJson'] = encoded
    result['observation'] = parse_worker(encoded)
    result['status'] = 'observed' if result['observation']['status'] == 'observed' else 'unavailable'


def _compute(job):
    root, request, source, context, execution = _prepare(job)
    result = _result(job, request, source, context)
    _observe(job, request, source, context, execution, result)
    if context_source(root, request['context']) != source:
        raise ValueError('prose context source changed during observation')
    reading_request(root, **request)
    verify_toolchain_identities(context)
    if implementation_identity() != job['implementationDigest']:
        raise ValueError('prose implementation changed during observation')
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('prose observation request exceeds 8 MiB')
        result = _compute(_decode(raw))
        encoded = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError('prose observation result exceeds 8 MiB')
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'result': None, 'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
