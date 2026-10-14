"""Read original semantic profiles without granting current checker authority."""

from ladon.correspondence_interpretation import LEGACY_PROFILE
from ladon.proof_slice import digest, slice_identity
from ladon.proof_slice_validation import validate_slice_shape
from ladon.proofir_correspondence import _correspondence_payload
from ladon.proofir_correspondence_payloads import validate_native_interpretation_batch


def interpretation_profile(bundle):
    artifacts = [row for row in bundle['artifacts']
                 if row['artifactKind'] == 'proofir.interpretation']
    if len(artifacts) != 1:
        raise ValueError('structured subject requires one exact native interpretation')
    return artifacts[0]['payload'].get('loweringProfile', LEGACY_PROFILE)


def _historical_identity(plan):
    validate_slice_shape(plan['slice'])
    if plan['slice']['sliceId'] != slice_identity(plan['slice']):
        raise ValueError('altered historical source slice')
    if plan['planId'] != digest({k: v for k, v in plan.items() if k != 'planId'}):
        raise ValueError('altered historical plan identity')


def _historical_native_binding(bundle, root, checked):
    plan = bundle['plan']
    ref = validate_native_interpretation_batch(plan['interpretation'], bundle['artifacts'],
                                               plan['slice']['environment'], source_root=root)
    if ref != plan['interpretationRef'] or (checked and bundle['planId'] != plan['planId']):
        raise ValueError('historical interpretation or check plan binding changed')
    native = [row for row in bundle['artifacts'] if row['artifactKind'] == 'proofir.correspondence']
    if not native or native[-1]['payload'] != _correspondence_payload(
            plan, bundle if checked else None):
        raise ValueError('historical native correspondence projection changed')


def historical_formal_subject(bundle, root, checked):
    """Validate immutable historical projections, retaining their original goals."""
    plan = bundle['plan']
    required = {'schema', 'interpretation', 'slice', 'objectMap', 'obligations',
                'residuals', 'planId', 'interpretationRef'}
    if set(plan) != required or plan['schema'] != 'ladon-correspondence-plan-v1':
        raise ValueError('unsupported historical correspondence plan')
    if interpretation_profile(bundle) != LEGACY_PROFILE:
        raise ValueError('historical plan cannot acquire a current typed lowering profile')
    _historical_identity(plan)
    _historical_native_binding(bundle, root, checked)
    return 'formal-correspondence', plan['planId']
