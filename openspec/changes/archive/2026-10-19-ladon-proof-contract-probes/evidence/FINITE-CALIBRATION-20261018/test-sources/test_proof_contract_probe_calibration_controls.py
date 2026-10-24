"""Finite calibration consumer controls without synthetic proof receipts."""
from __future__ import annotations

import json
import time

import pytest

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_probe_calibration import probe_calibration_profile, run_probe_calibration


def request(root):
    return {'repoRoot': str(root), 'left': [False] * 5, 'right': [False] * 4 + [True],
            'family': [0, 1, 2, 3], 'certificateRef': None,
            'deadlineMonotonic': time.monotonic() + 30,
            'limits': {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3,
                       'max_output_bytes': 8 * 1024**2}}


def test_unequal_objects_agree_on_incomplete_family_without_promotion(tmp_path):
    req = request(tmp_path)
    result = run_probe_calibration(req)
    assert result['status'] == 'scoped-agreement'
    assert result['agreement'] is True
    assert result['objectEquivalence'] is result['certificateVerified'] is False
    assert result['goals'] == []
    assert result['wholeMethodAuthority'] == 'none'
    assert result['mathematicalFalsity'] == 'not-established'
    assert result['sourceFidelity'] == 'not-assessed'
    assert not (tmp_path / '.ladon').exists()


def test_visible_coordinate_difference_keeps_exact_selected_scope(tmp_path):
    req = request(tmp_path)
    req['family'] = [4]
    result = run_probe_calibration(req)
    assert result['status'] == 'observed-response-difference'
    assert result['observations'] == [{'index': 4, 'left': False, 'right': True}]
    assert result['objectDistinction'] is False


def test_certificate_rejects_boolean_family_even_when_python_equality_matches(tmp_path):
    req = request(tmp_path)
    req['family'] = list(range(5))
    req['certificateRef'] = probe_calibration_profile()
    req['certificateRef']['family'] = [False, True, 2, 3, 4]
    assert run_probe_calibration(req)['status'] == 'rejected'
    assert not (tmp_path / '.ladon').exists()


def test_stricter_limits_are_preserved_for_finite_observation(tmp_path):
    req = request(tmp_path)
    req['limits'] = {'timeout_seconds': 1, 'max_rss_bytes': 1024**2, 'max_output_bytes': 4096}
    result = run_probe_calibration(req)
    assert result['status'] == 'scoped-agreement'
    assert result['limits'] == req['limits']


@pytest.mark.parametrize('field,value', [('timeout_seconds', True), ('max_rss_bytes', 0),
                                        ('max_output_bytes', 8 * 1024**2 + 1)])
def test_invalid_limits_reject_without_starting_proofs(tmp_path, field, value):
    req = request(tmp_path)
    req['limits'][field] = value
    assert run_probe_calibration(req)['status'] == 'rejected'
    assert not (tmp_path / '.ladon').exists()


def test_cli_profile_and_incomplete_agreement_publish_immutable_results(tmp_path, capsys):
    profile_path = tmp_path / 'profile.json'
    assert contract_main(['probe-calibration-profile', '--output', str(profile_path)]) == 0
    assert json.loads(profile_path.read_text()) == probe_calibration_profile()
    input_path, output_path = tmp_path / 'input.json', tmp_path / 'result.json'
    input_path.write_text(json.dumps(request(tmp_path)))
    args = ['probe-calibration', '--input', str(input_path), '--output', str(output_path)]
    assert contract_main(args) == 0
    saved = output_path.read_bytes()
    assert json.loads(saved)['status'] == 'scoped-agreement'
    assert contract_main(args) == 2
    assert output_path.read_bytes() == saved
    assert 'invalid' in capsys.readouterr().out


def test_cli_expired_deadline_is_incomplete_and_nonzero(tmp_path):
    req = request(tmp_path)
    req['deadlineMonotonic'] = time.monotonic() - 1
    input_path, output_path = tmp_path / 'input.json', tmp_path / 'result.json'
    input_path.write_text(json.dumps(req))
    assert contract_main(['probe-calibration', '--input', str(input_path), '--output', str(output_path)]) == 2
    result = json.loads(output_path.read_text())
    assert result['diagnostic']['code'] == 'timeout'
    assert result['objectEquivalence'] is False
    assert not (tmp_path / '.ladon').exists()
