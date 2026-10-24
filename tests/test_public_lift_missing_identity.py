"""Paired missing identities are not evidence of an exact binding."""
import pytest
from test_public_lift_native_evidence import TERM, _native, _seal

from ladon.proof_contract_lift_check import _validate_native_evidence


@pytest.mark.parametrize(('observed', 'declared'), [
    ('sourceDigest', 'declarationBodyDigest'),
    ('sourceContextDigest', None),
])
def test_missing_both_replay_digests_never_matches(observed, declared):
    native = _native()
    replay = native['nativeEvidence']['completion']['replay']
    replay['observation'].pop(observed)
    if declared is None:
        replay['sourceContext'].pop('digest')
    else:
        replay.pop(declared)
    with pytest.raises((ValueError, TypeError)):
        _validate_native_evidence(native, {'term': TERM})


@pytest.mark.parametrize(('projected', 'captured'), [
    ('environmentRef', 'executionContextRef'), ('executableIdentity', 'executableDigest'),
])
def test_missing_both_environment_identities_never_matches(projected, captured):
    native = _native()
    evidence = native['nativeEvidence']
    evidence.pop(projected)
    capture = evidence['capture']
    capture['environment'].pop(captured)
    _seal(capture)
    completion = evidence['completion']
    completion['captureId'] = capture['captureId']
    completion['replay']['observation']['captureId'] = capture['captureId']
    with pytest.raises((ValueError, TypeError)):
        _validate_native_evidence(native, {'term': TERM})
