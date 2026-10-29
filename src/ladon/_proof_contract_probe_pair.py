"""Resolve the exact native owners of two application readings."""
from __future__ import annotations

from ._proof_contract_context_preparation import _owner
from ._proof_contract_planned_source_inputs import _planned_input_size
from .proof_contract_payloads import closed, identifier

MAX_BYTES = 8 * 1024**2


def probe_reference(reference, kind):
    closed(reference, {'artifactRef', 'kind', 'localId'}, 'probe reference')
    from .proof_contract_context_bridge import _DIGEST

    if (reference['kind'] != kind or not isinstance(reference['artifactRef'], str)
            or not _DIGEST.fullmatch(reference['artifactRef'])):
        raise ValueError('probe requires an exact external ' + kind + ' reference')
    identifier(reference['localId'], 'probe reference local ID')


def probe_side(side):
    closed(side, {'contractRef', 'correspondenceRef'}, 'probe side')
    probe_reference(side['contractRef'], 'contract')
    probe_reference(side['correspondenceRef'], 'correspondence')


def probe_context(context):
    closed(context, {'artifacts'}, 'probe context')
    if not isinstance(context['artifacts'], list) or not 1 <= len(context['artifacts']) <= 4096:
        raise ValueError('probe context requires a bounded nonempty native batch')
    if _planned_input_size(context) > MAX_BYTES:
        raise ValueError('probe context exceeds 8 MiB')
    for artifact in context['artifacts']:
        _lowering_budget(artifact)


def _lowering_budget(artifact):
    """Preflight symbol expansion before the generic native lowering validator."""
    if not isinstance(artifact, dict) or artifact.get('artifactKind') != 'proofir.interpretation':
        return
    payload = artifact.get('payload')
    if not isinstance(payload, dict) or not isinstance(payload.get('record'), dict):
        raise TypeError('probe interpretation requires a native record')
    record = payload['record']
    symbols = record.get('symbols', {})
    if not isinstance(symbols, dict):
        raise TypeError('interpretation symbols must be an object')
    widest = max((_planned_input_size(v) for v in symbols.values()), default=1)
    size = _planned_input_size(record.get('formula'))
    if size * (widest + 32) > MAX_BYTES:
        raise ValueError('probe interpretation expansion exceeds the bounded profile')


def resolve_pair(artifacts, left, right):
    """Inputs have already passed aggregate and native batch validation."""
    probe_side(left)
    probe_side(right)
    values = list(artifacts.values()) if isinstance(artifacts, dict) else artifacts
    pair = [_resolve_side(values, side) for side in (left, right)]
    environments = {a['environmentRef'] for side in pair for a in side.values()}
    if len(environments) != 1:
        raise ValueError('application probes cannot cross native environments')
    return pair


def _resolve_side(artifacts, side):
    contract = _owner(artifacts, side['contractRef'], 'proofir.contract')
    from .proof_contract_rules import PROFILE_DIGEST

    if contract['payload']['profileDigest'] != PROFILE_DIGEST:
        raise ValueError('application probes do not support this contract profile')
    correspondence = _owner(artifacts, side['correspondenceRef'], 'proofir.correspondence')
    p = correspondence['payload']
    reading = _owner(artifacts, p['interpretationRef'], 'proofir.interpretation')
    if contract['payload']['sourceMapRefs'] != [reading['payload']['sourceRef']]:
        raise ValueError('contract must bind exactly its own interpretation source map')
    _owner(artifacts, reading['payload']['sourceRef'], 'proofir.source-map')
    _regenerate(reading, correspondence)
    return {'contract': contract, 'correspondence': correspondence, 'reading': reading}


def _regenerate(reading, correspondence):
    from .correspondence_check import prepare_correspondence
    from .proofir_correspondence import correspondence_artifacts

    p = correspondence['payload']
    plan = prepare_correspondence(reading['payload']['record'], p['slice'], p['objectMap'])
    plan['interpretationRef'] = p['interpretationRef']
    expected = correspondence_artifacts(plan)['payload']
    for key in expected:
        if key != 'correspondenceId' and expected[key] != p[key]:
            raise ValueError('probe correspondence differs from regenerated original: ' + key)


def derive_probe_result(artifacts, left, right, template):
    from ._proof_contract_probe_templates import template_result

    a, b = resolve_pair(artifacts, left, right)
    ca, cb = a['correspondence']['payload'], b['correspondence']['payload']
    if ca['slice'] != cb['slice'] or ca['objectMap'] != cb['objectMap']:
        return unsupported_result(template, 'different-application-context',
                                  'The readings require identical full native application contexts.')
    if ca['objectMap'] != {}:
        return unsupported_result(template, 'unsupported-object-map',
                                  'The first closed probe profile requires an empty object map.')
    return template_result(a['reading']['payload']['record'], b['reading']['payload']['record'],
        a['contract']['payload']['record'], b['contract']['payload']['record'], ca['slice'], template)


def unsupported_result(template, code, message):
    scope = {
        'regularity-boundary-v1': 'closed-nat-regularity-v1',
        'constant-uniformity-v1': 'closed-nat-regularity-v1',
        'constant-uniformity-v2': 'closed-nat-constant-uniformity-v2',
        'witness-dependence-v1': 'closed-nat-regularity-v1',
        'witness-dependence-v2': 'closed-nat-witness-dependence-v2',
        'restricted-domain-v1': 'closed-nat-regularity-v1',
        'restricted-domain-v2': 'closed-nat-zero-restricted-domain-v2',
        'inequality-direction-v1': 'closed-nat-regularity-v1',
        'inequality-direction-v2': 'closed-nat-zero-inequality-direction-v2',
    }.get(template.get('version'), 'closed-nat-regularity-v1')
    return {'schema': 'ladon-application-probe-plan-v1', 'status': 'unsupported',
        'template': template, 'scope': scope, 'goals': [],
        'residuals': [{'code': code, 'message': message, 'feature': template['familyId']}],
        'checkerAuthority': 'none', 'wholeMethodAuthority': 'none',
        'sourceFidelity': 'attributed-unreviewed', 'mathematicalFalsity': 'not-established'}
