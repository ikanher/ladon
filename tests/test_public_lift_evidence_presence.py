"""Explicit empty observations differ from absent or mistyped evidence."""
import pytest
from test_public_lift_native_evidence import TERM, _native, _seal

from ladon.proof_contract_lift_check import _validate_native_evidence


@pytest.mark.parametrize('value', [None, '', {}, 0])
def test_replay_axiom_coverage_requires_an_explicit_list(value):
    native = _native()
    completion = native['nativeEvidence']['completion']
    completion['trust']['observedAxioms'] = []
    observation = completion['replay']['observation']
    if value is None:
        observation.pop('observedAxioms')
    else:
        observation['observedAxioms'] = value
    with pytest.raises((ValueError, TypeError)):
        _validate_native_evidence(native, {'term': TERM})


def test_declared_axiom_policy_requires_list_not_dictionary_keys():
    native = _native()
    trust = native['nativeEvidence']['completion']['trust']
    trust['allowedAxioms'] = dict.fromkeys(trust['allowedAxioms'])
    with pytest.raises((ValueError, TypeError)):
        _validate_native_evidence(native, {'term': TERM})


def test_absent_locals_cannot_be_mistaken_for_observed_empty_context():
    native = _native()
    evidence = native['nativeEvidence']
    capture, completion = evidence['capture'], evidence['completion']
    capture['goal'].pop('localContext')
    completion['application']['originalGoal'].pop('localContext')
    _seal(capture)
    completion['captureId'] = capture['captureId']
    completion['replay']['observation']['captureId'] = capture['captureId']
    with pytest.raises((ValueError, TypeError)):
        _validate_native_evidence(native, {'term': TERM})


def test_empty_subjects_cannot_match_as_complete_semantic_evidence():
    native = _native()
    evidence = native['nativeEvidence']
    evidence['canonicalTypedSubject'] = evidence['actualTypedSubject'] = ''
    evidence['capture']['goal']['typeStructural'] = ''
    completion = evidence['completion']
    completion['application']['originalGoal']['typeStructural'] = ''
    _seal(evidence['capture'])
    completion['captureId'] = evidence['capture']['captureId']
    completion['replay']['observation']['captureId'] = evidence['capture']['captureId']
    with pytest.raises((ValueError, TypeError)):
        _validate_native_evidence(native, {'term': TERM})


def test_explicit_empty_axiom_lists_are_valid():
    native = _native()
    completion = native['nativeEvidence']['completion']
    completion['trust']['observedAxioms'] = []
    completion['replay']['observation']['observedAxioms'] = []
    _validate_native_evidence(native, {'term': TERM})
