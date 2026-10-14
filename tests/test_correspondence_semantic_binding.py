"""Historical untyped bytes cannot inherit typed or altered-subject guarantees."""

import copy

import pytest
from test_correspondence_investigation_v3 import input_bundle

from ladon.correspondence_interpretation import LEGACY_PROFILE, lower_formula
from ladon.proofir_correspondence import bind_native_interpretation
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch


def test_legacy_native_interpretation_readable_but_not_bound_to_current_plan(tmp_path):
    _, bundle = input_bundle(tmp_path)
    artifacts = copy.deepcopy(list(bundle['artifacts']))
    native = artifacts[-1]
    native['payload'].pop('loweringProfile')
    native['payload']['loweredFormula'] = lower_formula(
        bundle['record']['formula'], bundle['record']['symbols'], _profile=LEGACY_PROFILE)
    native['artifactId'] = detached_content_id(native)
    validate_envelope_batch(artifacts)
    plan = {'interpretation': bundle['record'], 'slice': {'environment': native['environmentRef']}}
    with pytest.raises(ValueError, match='lowering profile'):
        bind_native_interpretation(plan, artifacts, source_root=tmp_path)


def test_mutated_typed_subject_cannot_inherit_check_run_binding():
    from ladon.correspondence_evidence import _hash
    from ladon.investigation_correspondence_inputs import validate_check_receipt_bindings

    row = {'obligation': 'interpretation', 'mode': 'prove', 'goal': 'True → True',
           'status': 'supported', 'typedSubject': {'subject': 'True → True'}}
    artifact = {'artifactKind': 'proofir.check-run', 'artifactId': 'check-id',
                'payload': {'checkRunId': 'check-local'}, 'extensions': {
                    'ladon.correspondence-receipt/v1': {
                        'planId': 'plan-id', 'obligation': 'interpretation', 'mode': 'prove',
                        'goalDigest': _hash(row['goal']), 'receiptDigest': _hash(row)}}}
    bundle = {'planId': 'plan-id', 'checks': [row], 'artifacts': [artifact],
              'checkRunRefs': [{'artifactRef': 'check-id', 'kind': 'check-run',
                                'localId': 'check-local'}]}
    validate_check_receipt_bindings(bundle)
    bundle['checks'][0]['typedSubject']['subject'] = 'False → False'
    with pytest.raises(ValueError, match='check receipt'):
        validate_check_receipt_bindings(bundle)
