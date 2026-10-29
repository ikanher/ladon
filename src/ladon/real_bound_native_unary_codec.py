"""One-owner replay encoding, separate from the historical two-owner codec."""

from copy import deepcopy

from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_ARTIFACT_BYTES, canonical_bytes
from ladon.real_bound_native_analysis_codec import _map


def encode_unary(production, run):
    production = deepcopy(production)
    production['authority'] = 'none'
    encoded = _map({'production': production, 'ruleRun': run})
    encoded['production']['snapshotId'] = snapshot_identity(encoded['production'])
    canonical_bytes(encoded, max_bytes=MAX_ARTIFACT_BYTES)
    return encoded


def decode_unary(replay):
    canonical_bytes(replay, max_bytes=MAX_ARTIFACT_BYTES)
    closed(replay, {'production', 'ruleRun'}, 'Real unary replay')
    production = replay['production']
    if (not isinstance(production, dict) or production.get('authority') != 'none'
            or production.get('snapshotId') != snapshot_identity(production)):
        raise ValueError('invalid historical unary production identity or authority')
    decoded = _map(replay, decode=True)
    decoded['production']['snapshotId'] = snapshot_identity(decoded['production'])
    return decoded['production'], decoded['ruleRun']
