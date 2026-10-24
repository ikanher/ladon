"""One bounded native-validation, original-observation and strict-prefix stage."""
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

from .proof_contract_io import _decode
from .proof_contract_payloads import closed

MAX_BYTES = 8 * 1024**2


def _compute(job):
    from ._proof_contract_context_preparation import prepare_context

    closed(job, {'version', 'operation', 'request'}, 'context worker job')
    if job['version'] != 1:
        raise ValueError('unknown context worker operation')
    if job['operation'] == 'prepare-context':
        return prepare_context(job['request'])
    if job['operation'] == 'check-context-goal':
        return _check_goal(job['request'])
    raise ValueError('unknown context worker operation')


def _check_goal(request):
    from .correspondence_check import _check_goal as check
    from .proof_contract_bridge_worker import _verified_source
    from .proof_slice import pinned_toolchain

    closed(request, {'repoRoot', 'sourcePath', 'sourceDigest', 'goal', 'term',
                     'symbols', 'binding'}, 'context goal stage')
    root = Path(request['repoRoot']).resolve(strict=True)
    _verify_original_inputs(root, request['binding'])
    source = _verified_source(root, request)
    result = check(request['goal'], request['term'], root, source,
                   request['symbols'], pinned_toolchain(root))
    _verify_original_inputs(root, request['binding'])
    if _verified_source(root, request) != source:
        raise ValueError('strict context prefix changed during goal checking')
    return result


def _environment(root):
    from .proof_slice import pinned_toolchain

    return pinned_toolchain(root).context_identity


def _verify_original_inputs(root, binding):
    from .source_association_io import _read_regular, _source_path

    if _environment(root) != binding['environment']:
        raise ValueError('original context environment changed during checking')
    source = binding['originalSource']
    path = _source_path(root, source['path'], binding['selection']['module'])
    if hashlib.sha256(_read_regular(path, MAX_BYTES)).hexdigest() != source['sha256']:
        raise ValueError('original context source changed during checking')
    quote = binding['originalInterpretation']['source']
    if hashlib.sha256(_read_regular(_quote_path(root, quote['path']), MAX_BYTES)).hexdigest() != quote['sha256']:
        raise ValueError('original context quote changed during checking')


def _quote_path(root, relative):
    if not isinstance(relative, str):
        raise TypeError('quote path must be a string')
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative:
        raise ValueError('quote path escapes source root')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('quote path contains a symlink')
    current.resolve(strict=True).relative_to(root)
    return current


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('context worker input exceeds 8 MiB')
        result = _compute(_decode(raw))
        sys.stdout.write(_response(result))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, RecursionError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                     'diagnostic': str(error)[:500]}))
        return 2


def _response(result):
    from ._proof_contract_source_obligations_inputs import bounded_json_size
    from .proof_contract_bridge import _resource_stop

    envelope = {'status': 'completed', 'result': result, 'diagnostic': None}
    if bounded_json_size(envelope, MAX_BYTES) > MAX_BYTES:
        stopped = _resource_stop(result, {'max_rss_bytes': 12 * 1024**3})
        code = 'memory-limit' if stopped and stopped['code'] == 'memory-limit' else 'output-limit'
        envelope['result'] = {'status': code, 'code': code}
    return json.dumps(envelope, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


if __name__ == '__main__':
    raise SystemExit(main())
