"""Closed conditional transfer analyses retaining both exact historical owners."""

from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _context, _contract_ref
from ladon.real_bound_native_analysis_artifacts import _relation_artifact, _unique
from ladon.real_bound_native_analysis_codec import decode_replay, encode_replay
from ladon.real_bound_native_artifacts import _envelope, external
from ladon.real_bound_native_payload import LIMITATIONS
from ladon.real_bound_native_production import _verify_production
from ladon.real_bound_native_profile import PROFILE_DIGEST
from ladon.real_bound_native_transfer_evidence import recorded_transfer_evidence

SCHEMA = 'ladon-real-bound-transfer-bundle-v1'
ANALYSIS_KIND = 'real-bound-transfer-v1'


def is_transfer(payload):
    return (payload.get('profileDigest') == PROFILE_DIGEST and payload.get('stage') == 'propagation'
            and payload.get('analysisKind') == ANALYSIS_KIND)


def _components(replay):
    try:
        productions, run = decode_replay(replay)
        for production in productions:
            _verify_production(production)
            if production['status'] != 'admitted':
                raise ValueError('transfer history requires admitted owners')
        evidence = recorded_transfer_evidence(productions, run)
        env = productions[0]['artifacts'][-1]['environmentRef']
        relation, typed = _relation_artifact(productions, run, evidence, env,
            operation='real-bound:conditional-transfer-composition',
            statement='Recorded conditional composition; both source-shaped transfer premises remain assumed.')
        payload = _payload(replay, productions, relation, typed, evidence)
        owners = [a for p in productions for a in p['artifacts']]
        return payload, _unique([*owners, relation]), env
    except (TypeError, KeyError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError('malformed transfer replay evidence') from error


def _payload(replay, productions, relation, typed, evidence):
    return {'analysisId': 'analysis:' + snapshot_identity(replay)[7:],
            'profileDigest': PROFILE_DIGEST, 'stage': 'propagation', 'analysisKind': ANALYSIS_KIND,
            'contractRefs': [_contract_ref(p) for p in productions],
            'checkRunRefs': [external(relation, 'check-run', relation['payload']['checkRunId'])],
            'derivationGoalRef': external(relation, 'statement', 'goal:' + typed[7:]),
            'replay': deepcopy(replay), 'residuals': [],
            'result': {'status': 'recorded-checked', 'authority': 'none',
                       'relation': 'conditional-transfer-composition', 'rule': 'transfer-compose-v1',
                       'scope': 'conditional-source-shaped-transfer-composition', 'transferPremises': 'assumed',
                       'coefficientUniformity': 'not-inferred', 'sourceTheoremProof': 'not-checked',
                       'paperNormBridge': 'unresolved', 'mathematicalFalsity': 'not-established',
                       'goalDigest': evidence['request']['goal']['sha256'], 'typedGoalDigest': typed,
                       'checkerIdentity': evidence['checkerIdentity'],
                       'contextDigest': snapshot_identity({'contexts': [_context(p) for p in productions]})}}


def validate_transfer_payload(p, value, subjects, env):
    closed(p, {'analysisId', 'profileDigest', 'stage', 'analysisKind', 'contractRefs', 'checkRunRefs',
               'derivationGoalRef', 'replay', 'result', 'residuals'}, 'Real transfer payload')
    expected, _owners, expected_env = _components(p['replay'])
    if p != expected or env != expected_env:
        raise ValueError('transfer payload differs from exact recorded evidence')
    if ('contract-analysis', p['analysisId']) not in subjects:
        raise ValueError('transfer payload must own its analysis subject')
    if (value['coverage']['status'] != 'partial'
            or not set(LIMITATIONS) <= {row['id'] for row in value['limitations']}):
        raise ValueError('transfer payload requires historical limitations and partial coverage')


def validate_transfer_owners(artifacts, payload):
    _expected, owners, _env = _components(payload['replay'])
    if any(artifacts.get(owner['artifactId']) != owner for owner in owners):
        raise ValueError('transfer payload requires every exact evidence owner')


def recorded_transfer(productions, run):
    if not isinstance(productions, list) or len(productions) != 2:
        raise ValueError('transfer requires two ordered productions')
    normalized = deepcopy(productions)
    for production in normalized:
        _verify_production(production)
        production['authority'] = 'none'
        production['snapshotId'] = snapshot_identity(production)
    payload, owners, env = _components(encode_replay(normalized, run))
    artifact = _envelope('contract-analysis', env,
                         [{'kind': 'contract-analysis', 'localId': payload['analysisId']}], payload)
    artifacts = [*owners, artifact]
    validate_envelope_batch(artifacts)
    bundle = {'schema': SCHEMA, 'status': 'recorded-checked', 'authority': 'none',
              'analysisRef': external(artifact, 'contract-analysis', payload['analysisId']), 'artifacts': artifacts}
    bundle['snapshotId'] = snapshot_identity(bundle)
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    return bundle
