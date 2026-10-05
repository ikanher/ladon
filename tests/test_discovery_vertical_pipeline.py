"""The ordinary installed index/discover/explain loop retains rejected candidates."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / 'fixtures/lean_integration'


def _run(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120, check=False)
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean fixture unavailable')
def test_installed_pipeline_finds_explains_compiles_and_rejects(tmp_path):
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    common = ['--repo-root', str(FIXTURE), '--index', str(tmp_path / 'index.sqlite'), '--format', 'json']
    _run([console, 'proof-search', 'index', 'build', *common], tmp_path)
    lean = Path(subprocess.check_output(['elan', 'which', 'lean'], cwd=FIXTURE, text=True).strip())
    store = tmp_path / 'evidence.sqlite'
    goal = '∀ value : Nat, value = value'
    payload = _run([console, 'proof-search', 'discover', *common, '--module', 'LadonFixture',
                    '--goal', goal, '--pattern', '=', '--freshness', 'verify', '--max-candidates', '10',
                    '--toolchain-mode', 'explicit', '--lean-path', str(lean), '--lake-path', str(lean.with_name('lake')),
                    '--scratch-mode', 'advisory', '--evidence-store', str(store)], tmp_path)
    rows = {row['name']: row['check'] for row in payload['candidates']}
    _assert_pipeline_outcomes(rows)
    reference = rows['LadonFixture.fixtureIdentity']['checkRunRef']
    explained = _run([console, 'proof-search', 'explain', '--repo-root', str(FIXTURE),
                      '--candidate', 'LadonFixture.fixtureIdentity', '--goal', goal,
                      '--check-artifact', reference['artifactRef'], '--check-local-id', reference['localId'],
                      '--evidence-store', str(store), '--format', 'json'], tmp_path)
    assert explained['status'] == 'available', explained
    assert explained['candidateEvidence']['typeStatus'] == 'lean-rendered'
    assert explained['candidateEvidence']['evidenceReceipt']['observationState'] == 'stored'
    assert explained['routeCard']['accepted'] is False


def _assert_pipeline_outcomes(rows):
    assert rows['LadonFixture.fixtureIdentity']['status'] == 'accepted'
    assert rows['LadonFixture.fixtureUsesCore']['status'] == 'rejected'
    assert rows['LadonFixture.fixtureUsesCore']['failure']['stage'] == 'application-rejected'
    assert any(row.get('scratch', {}).get('status') == 'compiled' for row in rows.values())
