"""Native mismatch records preserve diagnostics without inventing proof attempts."""
from __future__ import annotations

import sys

from ladon.correspondence_evidence import completion_artifacts
from ladon.proofir_v3 import validate_envelope_batch


def test_prepared_subject_mismatch_projects_unknown_without_completed_proof():
    plan = {'planId': 'control', 'slice': {'environment': 'sha256:' + '1' * 64,
                                        'selection': {'declaration': 'selected'}}}
    diagnostic = {'code': 'prepared-goal-subject-mismatch',
                  'message': 'Original-source proposition differs from prepared captured goal.'}
    row = {'obligation': 'interpretation', 'mode': 'prove', 'goal': 'True',
           'status': 'unresolved', 'diagnostic': diagnostic,
           'typecheck': {'command': [sys.executable], 'stdout': '', 'stderr': ''}}
    result = {'checks': [row], 'implementationDigest': 'sha256:' + '2' * 64}
    artifacts, refs = completion_artifacts(plan, result)
    validate_envelope_batch(artifacts)
    check, attempt = artifacts
    assert check['payload']['results'][0]['result'] == 'unknown'
    assert check['payload']['guarantee']['scope'] == 'none'
    native = check['payload']['results'][0]['diagnostics']
    assert len(native) == 1
    assert native[0]['code'] == diagnostic['code']
    assert native[0]['message'] == diagnostic['message']
    assert attempt['payload']['attempts'][0]['outcome'] == 'proposed'
    assert attempt['payload']['attempts'][0]['diagnostics'] == native
    assert attempt['payload']['summary']['outcome'] == 'unknown'
    assert refs[0]['artifactRef'] == check['artifactId']
