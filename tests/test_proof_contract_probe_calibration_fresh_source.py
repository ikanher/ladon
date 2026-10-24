"""Staging must preserve the environment identity on the first request."""
import shutil
import subprocess
import time
from pathlib import Path

from ladon._proof_contract_probe_calibration_checks import prepare_calibration, verify_calibration
from ladon.proof_contract_probe_calibration import probe_calibration_profile


def test_first_staging_in_git_repository_keeps_original_environment(tmp_path):
    subprocess.run(['git', 'init', '--quiet', str(tmp_path)], check=True)
    shutil.copyfile(Path('tests/fixtures/proof_contract_planned_source/lean-toolchain'), tmp_path / 'lean-toolchain')
    owned = {'repoRoot': str(tmp_path), 'deadlineMonotonic': time.monotonic() + 30}
    adapter, environment = prepare_calibration(owned, probe_calibration_profile())
    verify_calibration(owned, adapter, environment)
    assert adapter['sourcePath'].endswith('/Probe.lean')
