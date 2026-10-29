"""Native unary coefficient proofs with exact historical owner reconstruction."""

from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _context, _contract_ref
from ladon.real_bound_native_analysis_artifacts import _relation_artifact, _unique
from ladon.real_bound_native_artifacts import _envelope, external
from ladon.real_bound_native_coefficient_evidence import recorded_coefficient_evidence
from ladon.real_bound_native_payload import LIMITATIONS
from ladon.real_bound_native_production import _verify_production
from ladon.real_bound_native_profile import PROFILE_DIGEST
from ladon.real_bound_native_unary_codec import decode_unary, encode_unary

SCHEMA = 'ladon-real-bound-coefficient-bundle-v1'
ANALYSIS_KIND = 'real-bound-coefficient-v1'


def is_coefficient(payload):
    return (payload.get('profileDigest') == PROFILE_DIGEST and payload.get('stage') == 'propagation'
            and payload.get('analysisKind') == ANALYSIS_KIND)


def _components(replay):
    try:
        production, run = decode_unary(replay)
        _verify_production(production)
        if production['status'] != 'admitted':
            raise ValueError('coefficient history requires an admitted owner')
        evidence = recorded_coefficient_evidence(production, run)
        env = production['artifacts'][-1]['environmentRef']
        relation, typed = _relation_artifact([production], run, evidence, env,
            operation='real-bound:coefficient-mono',
            statement='Recorded conditional output-bound implication; no uniformity or source-theorem claim.')
        payload = _payload(replay, production, relation, typed, evidence)
        return payload, _unique([*production['artifacts'], relation]), env
    except (TypeError, KeyError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError('malformed coefficient replay evidence') from error


def _payload(replay, production, relation, typed, evidence):
    return {'analysisId': 'analysis:' + snapshot_identity(replay)[7:],
            'profileDigest': PROFILE_DIGEST, 'stage': 'propagation', 'analysisKind': ANALYSIS_KIND,
            'contractRefs': [_contract_ref(production)],
            'checkRunRefs': [external(relation, 'check-run', relation['payload']['checkRunId'])],
            'derivationGoalRef': external(relation, 'statement', 'goal:' + typed[7:]),
            'replay': deepcopy(replay), 'residuals': [],
            'result': {'status': 'recorded-checked', 'authority': 'none',
                       'relation': 'output-coefficient-implies', 'rule': 'coefficient-mono-v1',
                       'scope': 'pointwise-fixed-output-context', 'coefficientUniformity': 'not-inferred',
                       'sourceTheoremProof': 'not-checked', 'paperNormBridge': 'unresolved',
                       'mathematicalFalsity': 'not-established',
                       'goalDigest': evidence['request']['goal']['sha256'], 'typedGoalDigest': typed,
                       'checkerIdentity': evidence['checkerIdentity'],
                       'contextDigest': snapshot_identity(_context(production))}}


def validate_coefficient_payload(p, value, subjects, env):
    closed(p, {'analysisId', 'profileDigest', 'stage', 'analysisKind', 'contractRefs', 'checkRunRefs',
               'derivationGoalRef', 'replay', 'result', 'residuals'}, 'Real coefficient payload')
    expected, _owners, expected_env = _components(p['replay'])
    if p != expected or env != expected_env:
        raise ValueError('coefficient payload differs from exact recorded evidence')
    if ('contract-analysis', p['analysisId']) not in subjects:
        raise ValueError('coefficient payload must own its analysis subject')
    if (value['coverage']['status'] != 'partial'
            or not set(LIMITATIONS) <= {row['id'] for row in value['limitations']}):
        raise ValueError('coefficient payload requires historical limitations and partial coverage')


def validate_coefficient_owners(artifacts, payload):
    _expected, owners, _env = _components(payload['replay'])
    if any(artifacts.get(owner['artifactId']) != owner for owner in owners):
        raise ValueError('coefficient payload requires every exact evidence owner')


def recorded_coefficient(production, run):
    _verify_production(production)
    replay = encode_unary(production, run)
    payload, owners, env = _components(replay)
    artifact = _envelope('contract-analysis', env,
                         [{'kind': 'contract-analysis', 'localId': payload['analysisId']}], payload)
    artifacts = [*owners, artifact]
    validate_envelope_batch(artifacts)
    bundle = {'schema': SCHEMA, 'status': 'recorded-checked', 'authority': 'none',
              'analysisRef': external(artifact, 'contract-analysis', payload['analysisId']), 'artifacts': artifacts}
    bundle['snapshotId'] = snapshot_identity(bundle)
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    return bundle
