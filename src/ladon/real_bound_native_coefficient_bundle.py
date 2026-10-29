"""Persist exact coefficient evidence and replay it under a shared deadline."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_coefficient import _coefficient_run, _result
from ladon.real_bound_native_coefficient_artifacts import SCHEMA, recorded_coefficient
from ladon.real_bound_native_unary_codec import decode_unary

FRESH_AUTHORITY = 'fresh-source-predicate-scalar-and-coefficient-checks'


def _validated(bundle):
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    closed(bundle, {'schema', 'status', 'authority', 'analysisRef', 'artifacts', 'snapshotId'},
           'Real coefficient bundle')
    if (bundle['schema'] != SCHEMA or bundle['snapshotId'] != snapshot_identity(bundle)
            or bundle['authority'] not in {'none', FRESH_AUTHORITY}):
        raise ValueError('invalid coefficient bundle identity or authority')
    validate_envelope_batch(bundle['artifacts'])
    try:
        matches = [a for a in bundle['artifacts'] if a['artifactId'] == bundle['analysisRef']['artifactRef']]
        if len(matches) != 1:
            raise ValueError('coefficient bundle requires one exact analysis owner')
        production, run = decode_unary(matches[0]['payload']['replay'])
        expected = recorded_coefficient(production, run)
        expected['authority'] = bundle['authority']
        expected['snapshotId'] = snapshot_identity(expected)
        if bundle != expected:
            raise ValueError('coefficient bundle differs from reconstructed evidence')
        return production, matches[0]['payload']
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('malformed coefficient bundle') from error


def produce_coefficient_bundle(production, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    try:
        result, fresh = _coefficient_run(production, root, timeout_seconds=_remaining(deadline))
    except TimeoutError:
        return _result(None, None, 'real-coefficient-shared-deadline-expired', None)
    if result['status'] != 'resolved':
        return result
    try:
        _remaining(deadline)
        bundle = recorded_coefficient(fresh, result['relationCheckRun'])
        _remaining(deadline)
        production_api._current_source(fresh, root)
        _remaining(deadline)
        bundle['authority'] = FRESH_AUTHORITY
        bundle['snapshotId'] = snapshot_identity(bundle)
        _remaining(deadline)
        return bundle
    except TimeoutError:
        return _result(fresh, result['relationCheckRun'], 'real-coefficient-publication-deadline-expired',
                       result['admissionCheckRun'])


def inspect_coefficient_bundle(bundle, root=None):
    production, payload = _validated(bundle)
    if root is not None:
        production_api._current_source(production, root)
    return {'schema': 'ladon-real-bound-coefficient-inspection-v1', 'status': 'validated-historical',
            'authority': 'none', 'freshCheck': False, 'evidenceAuthentication': 'not-established',
            'sourceFreshness': 'current' if root is not None else 'not-checked',
            'analysisRef': deepcopy(bundle['analysisRef']), 'recordedResult': deepcopy(payload['result']),
            'sourceTheoremProof': 'not-checked', 'coefficientUniformity': 'not-inferred',
            'paperNormBridge': 'unresolved', 'mathematicalFalsity': 'not-established'}


def replay_coefficient_bundle(bundle, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    production, _payload = _validated(bundle)
    try:
        return produce_coefficient_bundle(production, root, timeout_seconds=_remaining(deadline))
    except TimeoutError:
        return _result(None, None, 'real-coefficient-shared-deadline-expired', None)
