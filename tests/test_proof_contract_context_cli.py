"""Ordinary context CLI boundaries, with expired requests and no Lean work."""
import json
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize('command', ['context-obligations', 'check-context-bridge'])
def test_ordinary_contract_cli_exposes_context_operations(command):
    result = subprocess.run([sys.executable, '-m', 'ladon.entrypoint', 'investigation',
        'contract', command, '--help'], capture_output=True, text=True, check=False,
        env={**os.environ, 'PYTHONPATH': 'src'})
    assert result.returncode == 0
    assert '--input' in result.stdout
    if command == 'check-context-bridge':
        assert '--plan-id' in result.stdout and '--terms' in result.stdout


def test_expired_cli_input_stops_before_worker(tmp_path):
    request = {'repoRoot': str(tmp_path), 'context': {'artifacts': []},
        'correspondenceRef': {'artifactRef': 'sha256:' + 'a' * 64,
                              'kind': 'correspondence', 'localId': 'old'},
        'deadlineMonotonic': 0, 'limits': {'timeout_seconds': 30,
            'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}}
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(request))
    result = subprocess.run([sys.executable, '-m', 'ladon.entrypoint', 'investigation',
        'contract', 'context-obligations', '--input', str(path)],
        capture_output=True, text=True, check=False,
        env={**os.environ, 'PYTHONPATH': 'src'})
    body = json.loads(result.stdout)
    assert result.returncode == 2
    assert body['status'] == 'incomplete' and body['diagnostic']['code'] == 'timeout'
    assert body['wholeMethodAuthority'] == 'none' and 'preparation' not in body
