"""Internal evidence checks supplement the real public-API Lean qualification.

These constructed records test validation; they are not accepted external certificates.
"""
import copy
import hashlib
import json

import pytest

from ladon.proof_contract_lift_check import _validate_native_evidence

TERM = 'by trivial'
STRUCTURE = 'ladon-expr-dag-v1:{"nodes":[["const","`True","[]"]],"root":0}'
AXIOMS = ['propext', 'Classical.choice', 'Quot.sound']


def _digest(value):
    return 'sha256:' + hashlib.sha256(value).hexdigest()


def _seal(capture):
    capture.pop('captureId', None)
    capture['captureId'] = _digest(json.dumps(capture, sort_keys=True,
        separators=(',', ':'), ensure_ascii=False).encode())


def _native():
    goal = {'typeStructural': STRUCTURE, 'localContext': [], 'goalCount': 1}
    environment = {'executionContextRef': 'sha256:environment', 'executableDigest': 'sha256:lean',
                   'compiledInventory': {'snapshotDigest': 'sha256:inventory', 'modules': []}}
    capture = {'goal': goal, 'source': {'digest': 'sha256:source'}, 'environment': environment}
    _seal(capture)
    observation = {'captureId': capture['captureId'], 'termDigest': _digest(TERM.encode()),
                   'coverage': 'complete', 'observedAxioms': AXIOMS,
                   'sourceDigest': 'sha256:replay', 'sourceContextDigest': 'sha256:source'}
    completion = {'status': 'completed', 'captureId': capture['captureId'],
        'termDigest': _digest(TERM.encode()),
        'application': {'status': 'applied', 'originalGoal': copy.deepcopy(goal), 'residualGoals': []},
        'replay': {'status': 'accepted', 'coverage': 'complete', 'observation': observation,
                   'sourceDigest': 'sha256:generated-replay', 'declarationBodyDigest': 'sha256:replay', 'sourceContext': {'digest': 'sha256:source'}},
        'trust': {'policy': 'lean-standard-no-placeholders-v1', 'accepted': True,
                  'coverage': 'complete', 'allowedAxioms': AXIOMS, 'observedAxioms': AXIOMS}}
    return {'nativeEvidence': {'capture': capture, 'completion': completion,
        'canonicalTypedSubject': STRUCTURE, 'actualTypedSubject': STRUCTURE,
        'compiledInventory': environment['compiledInventory'],
        'environmentRef': environment['executionContextRef'],
        'executableIdentity': environment['executableDigest']}}


def _validate(native):
    return _validate_native_evidence(native, {'term': TERM})


def test_complete_internal_record_passes_local_validation_only():
    _validate(_native())


@pytest.mark.parametrize(('path', 'value'), [
    (('canonicalTypedSubject',), STRUCTURE + 'changed'),
    (('actualTypedSubject',), STRUCTURE + 'changed'),
    (('capture', 'captureId'), 'sha256:stale'),
    (('completion', 'captureId'), 'sha256:other'),
    (('completion', 'termDigest'), 'sha256:other'),
    (('completion', 'application', 'originalGoal', 'localContext'), [{'implementationDetail': False}]),
    (('completion', 'application', 'residualGoals'), [{'typeStructural': STRUCTURE}]),
    (('completion', 'replay', 'coverage'), 'partial'),
    (('completion', 'replay', 'observation', 'captureId'), 'sha256:other'),
    (('completion', 'replay', 'observation', 'termDigest'), 'sha256:other'),
    (('completion', 'replay', 'observation', 'sourceDigest'), 'sha256:other'),
    (('completion', 'replay', 'observation', 'sourceContextDigest'), 'sha256:other'),
    (('completion', 'trust', 'accepted'), False),
    (('completion', 'trust', 'policy'), 'relaxed'),
    (('completion', 'trust', 'coverage'), 'partial'),
    (('completion', 'trust', 'observedAxioms'), ['sorryAx']),
    (('environmentRef',), 'sha256:other'),
    (('executableIdentity',), 'sha256:other'),
    (('compiledInventory',), {}),
])
def test_mutated_evidence_cannot_be_promoted(path, value):
    native = _native()
    cursor = native['nativeEvidence']
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises((ValueError, TypeError)):
        _validate(native)


def test_visible_local_assumption_rejected_even_with_resealed_capture():
    native = _native()
    capture = native['nativeEvidence']['capture']
    capture['goal']['localContext'] = [{'implementationDetail': False}]
    _seal(capture)
    with pytest.raises((ValueError, TypeError)):
        _validate(native)
