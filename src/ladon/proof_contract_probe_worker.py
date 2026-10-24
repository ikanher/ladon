"""Supervised preparation and source-fresh checking of application probe goals."""
from pathlib import Path

from ._proof_contract_context_preparation import _digest, _native_plan, prepare_context
from ._proof_contract_probe_pair import resolve_pair
from .proof_contract_context_worker import _verify_original_inputs
from .proof_contract_payloads import closed

CHECKER_IDENTITY = {'name': 'ladon-application-probe-source-goal', 'version': 1}


def _compute(job):
    closed(job, {'version', 'operation', 'request'}, 'application probe worker job')
    if job['version'] != 1:
        raise ValueError('unknown application probe job version')
    if job['operation'] == 'prepare-probe':
        return _prepare(job['request'])
    if job['operation'] == 'check-probe-goal':
        return _check_goal(job['request'])
    if job['operation'] == 'inspect-probe':
        return _inspect(job['request'])
    raise ValueError('unknown application probe operation')


def _inspect(request):
    from ._proof_contract_probe_pair import probe_context
    from .proofir_v3 import validate_envelope_batch

    closed(request, {'artifact', 'context'}, 'probe inspection request')
    probe_context(request['context'])
    artifact = request['artifact']
    if (not isinstance(artifact, dict) or artifact.get('artifactKind') != 'proofir.contract-analysis'
            or artifact.get('payload', {}).get('stage') != 'probes'):
        raise ValueError('probe inspection requires a native probes-stage artifact')
    validate_envelope_batch([*request['context']['artifacts'], artifact])
    return artifact


def _prepare(request):
    from ._proof_contract_probe_inputs import probe_inputs
    from .proof_contract_probe_artifacts import application_probe_artifact

    owned = probe_inputs(request)
    artifact = application_probe_artifact(owned['context'], owned['left'], owned['right'],
        owned['template'], analysis_id='analysis:application-probe')
    planned = artifact['payload']['result']
    if planned['status'] != 'planned':
        return {'status': 'unsupported', 'artifact': artifact, 'residuals': planned['residuals']}
    root = Path(owned['repoRoot']).resolve(strict=True)
    pair = resolve_pair(owned['context']['artifacts'], owned['left'], owned['right'])
    if pair[0]['correspondence']['payload']['objectMap'] != {}:
        raise ValueError('closed application probe profile requires an empty object map')
    for side in ('left', 'right'):
        _native_plan(_context_request(owned, side), root)
    prepared = prepare_context(_context_request(owned, 'left'))
    if prepared['status'] != 'prepared':
        return prepared
    return _prepared_result(owned, artifact, prepared, pair)


def _context_request(owned, side):
    return {key: owned[key] for key in ('repoRoot', 'context', 'deadlineMonotonic', 'limits')} | {
        'correspondenceRef': owned[side]['correspondenceRef']}


def _prepared_result(owned, artifact, prepared, pair):
    right = pair[1]['reading']
    right_binding = {**prepared['binding'],
        'correspondenceRef': owned['right']['correspondenceRef'],
        'interpretationRef': pair[1]['correspondence']['payload']['interpretationRef'],
        'interpretationSourceRef': right['payload']['sourceRef'],
        'originalInterpretation': right['payload']['record']}
    binding = {'left': prepared['binding'], 'right': right_binding}
    _verify_pair(Path(owned['repoRoot']).resolve(strict=True), binding)
    identity = _digest({'artifactId': artifact['artifactId'], 'binding': binding,
        'adapter': prepared['adapter'], 'deadlineMonotonic': owned['deadlineMonotonic'],
        'limits': owned['limits'], 'checkerIdentity': CHECKER_IDENTITY})
    symbols = {f'{i}.{key}': value for i, p in enumerate(pair)
               for key, value in p['reading']['payload']['record']['symbols'].items()}
    return {'status': 'prepared', 'planId': identity, 'artifact': artifact,
        'goals': artifact['payload']['result']['goals'], 'binding': binding,
        'adapter': prepared['adapter'], 'symbols': symbols,
        'checkerIdentity': CHECKER_IDENTITY,
        'construction': prepared['construction'], 'residuals': artifact['payload']['residuals']}


def _check_goal(request):
    from .correspondence_check import _check_goal as check
    from .proof_contract_bridge_worker import _verified_source
    from .proof_slice import pinned_toolchain

    closed(request, {'repoRoot', 'sourcePath', 'sourceDigest', 'goal', 'term',
                     'symbols', 'binding'}, 'application probe goal stage')
    root = Path(request['repoRoot']).resolve(strict=True)
    _verify_pair(root, request['binding'])
    source = _verified_source(root, request)
    result = check(request['goal'], request['term'], root, source,
                   request['symbols'], pinned_toolchain(root))
    _verify_pair(root, request['binding'])
    if _verified_source(root, request) != source:
        raise ValueError('application probe strict prefix changed during checking')
    return result


def _verify_pair(root, binding):
    for side in ('left', 'right'):
        _verify_original_inputs(root, binding[side])


def main():
    import json
    import sys

    from .proof_contract_context_worker import MAX_BYTES, _response
    from .proof_contract_io import _decode

    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('application probe worker input exceeds 8 MiB')
        sys.stdout.write(_response(_compute(_decode(raw))))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError, RecursionError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                    'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
