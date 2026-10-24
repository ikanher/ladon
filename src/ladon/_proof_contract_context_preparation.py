"""Rebuild native subjects and exclude the original parent from proof contexts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .proof_contract_bridge import _resource_stop
from .source_association_io import _read_regular, _source_path

MAX_BYTES = 8 * 1024**2


def _digest(value):
    return 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _native_plan(request, root):
    from .correspondence_check import prepare_correspondence
    from .proofir_correspondence import bind_native_interpretation, correspondence_artifacts
    from .proofir_v3 import validate_envelope_batch

    artifacts = request['context']['artifacts']
    validate_envelope_batch(artifacts)
    reference = request['correspondenceRef']
    owner = _owner(artifacts, reference, 'proofir.correspondence')
    payload = owner['payload']
    reading = _owner(artifacts, payload['interpretationRef'], 'proofir.interpretation')
    plan = prepare_correspondence(reading['payload']['record'], payload['slice'], payload['objectMap'])
    plan = bind_native_interpretation(plan, artifacts, source_root=root)
    expected = correspondence_artifacts(plan)['payload']
    # Native receipts store floats as exact decimal strings. Rebuilding their
    # original binary-float plan ID is unnecessary; all semantic fields agree.
    for key in expected:
        if key != 'correspondenceId' and expected[key] != payload[key]:
            raise ValueError('native context differs from regenerated original obligations: ' + key)
    if owner['environmentRef'] != plan['slice']['environment']:
        raise ValueError('native context environment differs from the selected application')
    return plan, owner, reading


def _owner(artifacts, reference, kind):
    matches = [a for a in artifacts if a['artifactId'] == reference['artifactRef']
               and a['artifactKind'] == kind]
    if len(matches) != 1 or {'kind': reference['kind'], 'localId': reference['localId']} not in matches[0]['subjectRefs']:
        raise ValueError('native context reference has no unique exact owner')
    return matches[0]


def prepare_context(request):
    from ._proof_contract_context_goals import ContextOutputLimit, build_context_goals
    from .proof_contract_context_bridge import _inputs
    from .proof_slice import extract_proof_slice

    owned = _inputs(request, None, None, False)
    root = Path(owned['repoRoot']).resolve(strict=True)
    plan, owner, reading = _native_plan(owned, root)
    frozen = plan['slice']
    selection = frozen['selection']
    path = _source_path(root, selection['sourceFile'], selection['module'])
    source = _read_regular(path, MAX_BYTES)
    if hashlib.sha256(source).hexdigest() != frozen['source']['sha256']:
        raise ValueError('original context source changed after planning')
    actual = extract_proof_slice(root, selection['sourceFile'], selection['module'],
        selection['declaration'], selection['application'], selection['occurrence'], scoped=True)
    if _resource_stop(actual, owned['limits']) or not actual.get('complete'):
        return {'status': 'incomplete', 'extraction': actual}
    if actual['sliceId'] != frozen['sliceId']:
        raise ValueError('fresh original application differs from the native context')
    prefix = _prefix(root, owned, frozen, source)
    if _resource_stop(prefix, owned['limits']):
        return {'status': 'incomplete', 'prefix': prefix}
    binding = _binding(owned, plan, reading, prefix)
    try:
        goals = build_context_goals(plan, binding)
    except ContextOutputLimit:
        return {'status': 'output-limit', 'code': 'output-limit'}
    identity = _digest({'profile': 'source-context-bridge-v1', 'binding': binding,
                        'goals': goals, 'residuals': plan['residuals']})
    if _read_regular(path, MAX_BYTES) != source:
        raise ValueError('original context source changed during preparation')
    return {'status': 'prepared', 'planId': identity, 'binding': binding, 'goals': goals,
        'residuals': plan['residuals'], 'symbols': plan['interpretation']['symbols'],
        'adapter': {'repoRoot': str(root), 'sourcePath': prefix['subject']['path'],
                    'sourceDigest': prefix['subject']['digest']},
        'construction': {'freshSlice': actual, 'prefixCheck': prefix,
                         'correspondenceArtifactRef': owner['artifactId']}}


def _prefix(root, owned, frozen, source):
    from ._proof_contract_source_obligations_prefix import check_generated_prefix
    from ._proof_contract_source_obligations_staging import _stage_prefix_check
    from .proof_contract_production import produce_formal_contract
    from .proof_contract_source_obligations import _runner

    selected, limits = frozen['selection'], owned['limits']
    observed = produce_formal_contract(root, selected['sourceFile'], selected['module'],
        selected['declaration'], timeout_seconds=limits['timeout_seconds'],
        max_output_bytes=limits['max_output_bytes'], max_rss_bytes=limits['max_rss_bytes'])
    if _resource_stop(observed, limits):
        return observed
    expected_source = {key: frozen['source'][key] for key in ('path', 'sha256')}
    if observed['environment'] != frozen['environment'] or observed['source'] != expected_source:
        raise ValueError('parent declaration observation has changed context')
    location = observed['observation']['declarationRange']
    lines = source.decode().splitlines(keepends=True)
    prefix = (''.join(lines[:location['startLine'] - 1])
              + lines[location['startLine'] - 1][:location['startColumn']]).encode()
    key = _digest({'reference': owned['correspondenceRef'], 'sliceId': frozen['sliceId'],
                   'prefixDigest': hashlib.sha256(prefix).hexdigest()}).removeprefix('sha256:')
    relative = Path('.ladon/contract-obligations') / key / 'Context.lean'
    parent = {'selection': {'declaration': selected['declaration'], 'module': selected['module']}}
    subject = _stage_prefix_check(root, relative, prefix, parent, key,
                                  owned['deadlineMonotonic'], [])
    return check_generated_prefix(root, subject, frozen['environment'], limits,
                                  _runner(owned['deadlineMonotonic']))


def _binding(owned, plan, reading, prefix):
    frozen = plan['slice']
    return {'correspondenceRef': owned['correspondenceRef'],
        'interpretationRef': plan['interpretationRef'],
        'interpretationSourceRef': reading['payload']['sourceRef'],
        'originalInterpretation': plan['interpretation'], 'objectMap': plan['objectMap'],
        'originalSliceId': frozen['sliceId'], 'selection': frozen['selection'],
        'originalSource': frozen['source'], 'environment': frozen['environment'],
        'strictPrefixDigest': prefix['subject']['digest'],
        'premiseOccurrences': [{'occurrence': p['occurrence'],
            'proposition': p['proposition'], 'providerObservation': p['providerObservation']}
            for p in frozen['nodes'][0]['premises']],
        'transportProfile': 'original-context-domain-witness-v1'}
