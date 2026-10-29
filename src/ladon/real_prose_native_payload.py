"""Native authored Real dispatch binds history and exact external reading owners."""

from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import _require_ref
from ladon.real_prose_inputs import observation_identity
from ladon.real_prose_native_codec import decode_history
from ladon.real_prose_native_record import PROFILE_DIGEST, build_record, contract_id
from ladon.real_prose_recognition_history import validate_recognition

LIMITATIONS = {
    'authored-real-not-admitted': 'Typed syntax and arithmetic aliases do not admit the bound predicate.',
    'authored-real-history': 'Saved execution history is unauthenticated; fresh use requires new checks.',
    'attributed-interpretation': 'Interpretation fidelity is unreviewed; no truth or falsity is established.',
}
PROVENANCE = {'mode': 'authored', 'fidelity': 'attributed-unreviewed', 'completeness': 'partial',
              'checkerAuthority': 'none', 'mathematicalFalsity': 'not-established'}


def recognition_history(payload):
    history = decode_history(payload['recognition'])
    validate_recognition(history)
    if history['status'] != 'recognized':
        raise ValueError('authored Real native records require recognized syntax')
    return history


def validate_payload(payload, value, subjects, env):
    closed(payload, {'contractId', 'profileDigest', 'record', 'statementRef', 'conclusionRef',
                     'assumptionRefs', 'sourceMapRefs', 'checkRunRefs', 'provenance', 'residuals',
                     'interpretationRef', 'recognition'}, 'authored Real payload')
    if payload['profileDigest'] != PROFILE_DIGEST or payload['provenance'] != PROVENANCE:
        raise ValueError('authored Real profile cannot promote authority or fidelity')
    if payload['checkRunRefs'] != [] or payload['assumptionRefs'] != []:
        raise ValueError('authored Real premises remain in its telescope; no admission checks are claimed')
    if not set(LIMITATIONS) <= {row['id'] for row in value['limitations']}:
        raise ValueError('authored Real history requires its authority limitations')
    _record_payload(payload, value, subjects, env)


def _record_payload(payload, value, subjects, env):
    history = recognition_history(payload)
    record, descriptors = expected_record(payload, history)
    if record != payload['record']:
        raise ValueError('authored Real record differs from exact recognition features and owners')
    expected_id = contract_id(history, record['alternativeId'], record['author'])
    if payload['contractId'] != expected_id or ('contract', expected_id) not in subjects:
        raise ValueError('authored Real alternative has the wrong exact contract owner')
    _local_owners(payload, value, subjects, env, history, descriptors)
    expected_residuals = [{'code': row['code'], 'message': row['message'], 'feature': 'recognition'}
                          for row in history['check']['result']['features']['residuals']]
    if payload['residuals'] != expected_residuals:
        raise ValueError('authored Real residual obligations changed')


def expected_record(payload, history):
    refs = payload['sourceMapRefs']
    if not isinstance(refs, list) or len(refs) != 1:
        raise ValueError('authored Real requires one exact source map')
    attribution = payload['record']
    closed(attribution, {'schema', 'profileId', 'alternativeId', 'author', 'source', 'scope',
                         'telescope', 'roles', 'application', 'loss', 'constant', 'guards',
                         'origins', 'admission'}, 'authored Real record')
    for ref in (payload['interpretationRef'], refs[0]):
        closed(ref, {'artifactRef', 'kind', 'localId'}, 'authored Real external owner')
    return build_record(history, payload['interpretationRef'], refs[0],
                        alternative_id=attribution['alternativeId'], author=attribution['author'])


def statement_subject(history):
    expression = history['check']['result']['observation']['check']['result']['observation']['propositionExpr']
    digest = observation_identity({'propositionExpr': expression})
    return {'kind': 'statement', 'localId': 'proposition:' + digest[7:],
            'fingerprint': {'scheme': {'name': 'lean-proposition-value', 'version': '1'}, 'digest': digest}}


def _local_owners(payload, value, subjects, env, history, descriptors):
    statement = statement_subject(history)
    ref = {key: statement[key] for key in ('kind', 'localId')}
    if payload['statementRef'] != ref or payload['conclusionRef'] != ref:
        raise ValueError('authored Real proposition owner changed')
    _require_ref(ref, '/payload/statementRef', subjects, env, value, 'statement')
    expected = [{'kind': 'contract', 'localId': payload['contractId']}, statement, *descriptors]
    if value['subjectRefs'] != expected:
        raise ValueError('authored Real typed expression subjects differ from recognition')
    _require_ref(payload['interpretationRef'], '/payload/interpretationRef', subjects, env, value, 'interpretation')
    _require_ref(payload['sourceMapRefs'][0], '/payload/sourceMapRefs/0', subjects, env, value, 'source-map')


def validate_owners(artifact, artifacts):
    payload = artifact['payload']
    history = recognition_history(payload)
    ref = payload['interpretationRef']
    reading = artifacts[ref['artifactRef']]
    source_ref = payload['sourceMapRefs'][0]
    source = artifacts[source_ref['artifactRef']]
    actual = reading['payload']
    if (reading['artifactKind'] != 'proofir.interpretation' or actual['interpretationId'] != ref['localId']
            or actual['record'] != history['request']['interpretation'] or actual['sourceRef'] != source_ref):
        raise ValueError('authored Real interpretation/recognition owner mismatch')
    observed = history['check']['result']['observation']['check']['result']
    if artifact['environmentRef'] != observed['environment']:
        raise ValueError('authored Real environment differs from its exact observation')
    if [source, reading] != observed['artifacts']:
        raise ValueError('authored Real source/interpretation differ from exact observation owners')
