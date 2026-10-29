"""Native conditional transfer storage, historical inspection and fresh replay."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_analysis_codec import decode_replay
from ladon.real_bound_native_transfer import _result, _transfer_run
from ladon.real_bound_native_transfer_artifacts import SCHEMA, recorded_transfer

FRESH_AUTHORITY = 'fresh-source-predicate-scalar-and-transfer-checks'


def _validated(bundle):
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    closed(bundle, {'schema', 'status', 'authority', 'analysisRef', 'artifacts', 'snapshotId'}, 'transfer bundle')
    if (bundle['schema'] != SCHEMA or bundle['snapshotId'] != snapshot_identity(bundle)
            or bundle['authority'] not in {'none', FRESH_AUTHORITY}):
        raise ValueError('invalid transfer bundle identity or authority')
    validate_envelope_batch(bundle['artifacts'])
    try:
        matches = [a for a in bundle['artifacts'] if a['artifactId'] == bundle['analysisRef']['artifactRef']]
        if len(matches) != 1:
            raise ValueError('transfer bundle requires one exact analysis owner')
        productions, run = decode_replay(matches[0]['payload']['replay'])
        expected = recorded_transfer(productions, run)
        expected['authority'] = bundle['authority']
        expected['snapshotId'] = snapshot_identity(expected)
        if bundle != expected:
            raise ValueError('transfer bundle differs from reconstructed evidence')
        return productions, matches[0]['payload']
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('malformed transfer bundle') from error


def produce_transfer_bundle(left, right, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    try:
        result, fresh = _transfer_run(left, right, root, timeout_seconds=_remaining(deadline))
    except TimeoutError:
        return _result([], [], None, 'real-transfer-shared-deadline-expired')
    if result['status'] != 'resolved':
        return result
    try:
        _remaining(deadline)
        bundle = recorded_transfer(fresh, result['relationCheckRun'])
        for production in fresh:
            _remaining(deadline)
            production_api._current_source(production, root)
        _remaining(deadline)
        bundle['authority'] = FRESH_AUTHORITY
        bundle['snapshotId'] = snapshot_identity(bundle)
        _remaining(deadline)
        return bundle
    except TimeoutError:
        return _result(fresh, result['admissionCheckRuns'], result['relationCheckRun'],
                       'real-transfer-publication-deadline-expired')


def inspect_transfer_bundle(bundle, root=None):
    productions, payload = _validated(bundle)
    if root is not None:
        for production in productions:
            production_api._current_source(production, root)
    return {'schema': 'ladon-real-bound-transfer-inspection-v1', 'status': 'validated-historical',
            'authority': 'none', 'freshCheck': False, 'evidenceAuthentication': 'not-established',
            'sourceFreshness': 'current' if root is not None else 'not-checked',
            'analysisRef': deepcopy(bundle['analysisRef']), 'recordedResult': deepcopy(payload['result']),
            'transferPremises': 'assumed', 'sourceTheoremProof': 'not-checked',
            'coefficientUniformity': 'not-inferred', 'paperNormBridge': 'unresolved',
            'mathematicalFalsity': 'not-established'}


def replay_transfer_bundle(bundle, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    productions, _payload = _validated(bundle)
    try:
        return produce_transfer_bundle(*productions, root, timeout_seconds=_remaining(deadline))
    except TimeoutError:
        return _result([], [], None, 'real-transfer-shared-deadline-expired')
