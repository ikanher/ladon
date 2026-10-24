"""Supervised route preparation and original-source proof-term checking."""
import hashlib
import json
import sys
from pathlib import Path

from .proof_contract_context_worker import (
    MAX_BYTES,
    _quote_path,
    _response,
    _verify_original_inputs,
)
from .proof_contract_io import _decode
from .proof_contract_payloads import closed


def _compute(job):
    from ._proof_contract_context_goals import ContextOutputLimit
    from ._proof_contract_route_context_preparation import prepare_route_context
    from .proof_contract_source_obligations import SourceIncomplete, SourceResourceLimit

    closed(job, {'version', 'operation', 'request'}, 'route context worker job')
    if job['version'] != 1:
        raise ValueError('unknown route context protocol')
    try:
        if job['operation'] == 'prepare-route-context':
            return prepare_route_context(job['request'])
        if job['operation'] == 'check-route-context-goal':
            return _check_goal(job['request'])
    except ContextOutputLimit as error:
        return {'status': 'incomplete', 'code': 'output-limit', 'message': str(error)}
    except TimeoutError as error:
        return {'status': 'incomplete', 'code': 'timeout', 'message': str(error)}
    except SourceIncomplete as error:
        return {'status': 'unsupported', 'code': 'unsupported-source-fragment', 'message': str(error)}
    except SourceResourceLimit as error:
        return {'status': 'incomplete', 'code': 'resource-limit', 'message': str(error)}
    raise ValueError('unknown route context operation')


def _check_goal(request):
    from .correspondence_check import _check_goal as check
    from .proof_contract_bridge_worker import _verified_source
    from .proof_slice import pinned_toolchain

    closed(request, {'repoRoot', 'sourcePath', 'sourceDigest', 'goal', 'term',
                     'symbols', 'binding'}, 'route context goal stage')
    root = Path(request['repoRoot']).resolve(strict=True)
    _verify_route_inputs(root, request['binding'])
    source = _verified_source(root, request)
    result = check(request['goal'], request['term'], root, source,
                   request['symbols'], pinned_toolchain(root))
    _verify_route_inputs(root, request['binding'])
    if _verified_source(root, request) != source:
        raise ValueError('strict route prefix changed during goal checking')
    from ._proof_contract_route_context_evidence import store_goal_evidence

    return store_goal_evidence(root, result)


def _verify_route_inputs(root, binding):
    from .source_association_io import _read_regular, _source_path

    _verify_original_inputs(root, binding['contextBinding'])
    source = binding['parentSource']
    path = _source_path(root, source['path'], binding['parentSelection']['module'])
    if hashlib.sha256(_read_regular(path, MAX_BYTES)).hexdigest() != source['sha256']:
        raise ValueError('original endpoint source changed during checking')
    quote = binding['parentInterpretation']['source']
    if hashlib.sha256(_read_regular(_quote_path(root, quote['path']), MAX_BYTES)).hexdigest() != quote['sha256']:
        raise ValueError('original endpoint prose changed during checking')


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('route context worker input exceeds 8 MiB')
        sys.stdout.write(_response(_compute(_decode(raw))))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError,
            RecursionError, TimeoutError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                     'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
