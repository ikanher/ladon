"""Build immutable native attributed records, preserving complete syntax history."""

from ladon.proofir_v3 import make_envelope, validate_envelope_batch
from ladon.real_prose_native_codec import encode_history
from ladon.real_prose_native_payload import LIMITATIONS, PROVENANCE, statement_subject
from ladon.real_prose_native_record import PROFILE_DIGEST, build_record, contract_id
from ladon.real_prose_recognition_history import validate_recognition


def external(artifact, kind, local_id):
    return {'artifactRef': artifact['artifactId'], 'kind': kind, 'localId': local_id}


def authored_artifacts(recognition, sources, *, alternative_id, author):
    validate_recognition(recognition)
    if recognition['status'] != 'recognized':
        return []
    source, reading = sources
    source_ref = external(source, 'source-map', source['payload']['sourceMapId'])
    reading_ref = external(reading, 'interpretation', reading['payload']['interpretationId'])
    record, expressions = build_record(recognition, reading_ref, source_ref,
                                       alternative_id=alternative_id, author=author)
    identity = contract_id(recognition, alternative_id, author)
    statement = statement_subject(recognition)
    statement_ref = {key: statement[key] for key in ('kind', 'localId')}
    subjects = [{'kind': 'contract', 'localId': identity}, statement, *expressions]
    payload = {'contractId': identity, 'profileDigest': PROFILE_DIGEST, 'record': record,
               'statementRef': statement_ref, 'conclusionRef': statement_ref, 'assumptionRefs': [],
               'sourceMapRefs': [source_ref], 'interpretationRef': reading_ref, 'checkRunRefs': [],
               'recognition': encode_history(recognition), 'provenance': PROVENANCE,
               'residuals': [{'code': r['code'], 'message': r['message'], 'feature': 'recognition'}
                             for r in recognition['check']['result']['features']['residuals']]}
    contract = make_envelope(artifact_kind='proofir.contract',
        producer={'name': 'ladon-authored-real', 'version': '1', 'implementation': 'python'},
        environment_ref=reading['environmentRef'], subject_refs=subjects, payload=payload,
        coverage={'status': 'partial', 'population': {'kind': 'artifact-subjects', 'selector': {}},
                  'universeKnown': True, 'expected': len(subjects), 'discovered': len(subjects),
                  'decoded': len(subjects), 'valid': len(subjects), 'projected': len(subjects),
                  'queryMatched': len(subjects), 'omitted': [], 'bounds': {'maxSubjects': 1000}},
        limitations=[{'id': key, 'message': message} for key, message in LIMITATIONS.items()]).to_dict()
    artifacts = [source, reading, contract]
    validate_envelope_batch(artifacts)
    return artifacts
