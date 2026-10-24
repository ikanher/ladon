"""Qualification cannot count an infrastructure failure as a rejected proof."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'scripts/check_public_nat_rational_lift.py'
SPEC = importlib.util.spec_from_file_location('public_lift_gate', PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize('code', ['proof-rejected', 'trust-rejected'])
def test_negative_proof_requires_substantive_rejection(code):
    assert runner.case_passed('proof-rejected', {'status': 'rejected', 'diagnostic': {'code': code}})


@pytest.mark.parametrize('status', ['incomplete', 'unsupported', 'unresolved', 'stale-input'])
def test_other_stops_never_pass_mathematical_negative(status):
    assert not runner.case_passed('proof-rejected', {'status': status, 'diagnostic': {'code': 'timeout'}})


def test_override_requires_canonical_mismatch_not_merely_failure():
    assert runner.case_passed('semantic-goal-mismatch', {
        'status': 'unsupported', 'diagnostic': {'code': 'semantic-goal-mismatch'}})
    assert not runner.case_passed('semantic-goal-mismatch', {
        'status': 'unsupported', 'diagnostic': {'code': 'unsupported-canonical-goal'}})
    assert not runner.case_passed('semantic-goal-mismatch', {
        'status': 'spurious-countermodel', 'diagnostic': {'code': 'semantic-goal-mismatch'}})


def test_positive_controls_require_bound_positive_evidence():
    positive = {'status': 'lifted-counterexample', 'checkId': 'sha256:owned',
                'sourceVerified': True, 'sourceFormulaFidelity': 'unverified',
                'originalClaimRefuted': False, 'formalClaimRefuted': True,
                'realizationEvidence': {'checked': True}, 'spuriousnessEvidence': None,
                'openObligation': None}
    assert runner.case_passed('lifted-counterexample', positive)
    assert not runner.case_passed('lifted-counterexample', {**positive, 'checkId': None})
    assert not runner.case_passed('lifted-counterexample', {**positive, 'originalClaimRefuted': True})
    assert not runner.case_passed('lifted-counterexample', {**positive, 'formalClaimRefuted': False})
