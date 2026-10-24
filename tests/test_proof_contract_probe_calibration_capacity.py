"""A too-small output budget must not turn into an oversized error payload."""
from __future__ import annotations

import json
import time

import pytest

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_probe_calibration import run_probe_calibration


def tiny_request(root):
    return {'repoRoot': str(root), 'left': [False] * 5, 'right': [False] * 5,
            'family': [0], 'certificateRef': None, 'deadlineMonotonic': time.monotonic() + 30,
            'limits': {'timeout_seconds': 1, 'max_rss_bytes': 1024**2, 'max_output_bytes': 1}}


def test_api_raises_typed_capacity_stop_when_even_error_envelope_cannot_fit(tmp_path):
    with pytest.raises(ValueError, match='output capacity'):
        run_probe_calibration(tiny_request(tmp_path))
    assert not (tmp_path / '.ladon').exists()


def test_cli_has_empty_stdout_and_no_publication_if_error_cannot_fit(tmp_path, capsys):
    input_path, output_path = tmp_path / 'input.json', tmp_path / 'result.json'
    input_path.write_text(json.dumps(tiny_request(tmp_path)))
    assert contract_main(['probe-calibration', '--input', str(input_path), '--output', str(output_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'output capacity' in captured.err
    assert not output_path.exists()
