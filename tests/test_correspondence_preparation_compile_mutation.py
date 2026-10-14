"""A real compiler interval cannot hide creation/restoration of an import sidecar."""
import shutil
from pathlib import Path

import pytest

from ladon import correspondence_preparation as preparation
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import extract_proof_slice, pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution


def test_transient_sidecar_during_actual_preparation_is_rejected(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    shutil.copytree(Path(__file__).parent / 'fixtures/correspondence_m1', repo,
                    ignore=shutil.ignore_patterns('.ladon', '.lake', '*.olean'))
    compiled = repo / '.lake/build/lib/lean'
    compiled.mkdir(parents=True)
    dependency = repo / 'Dep.lean'
    dependency.write_text('import Lean\ndef importedNumber : Nat := 1\n')
    source = repo / 'Proof.lean'
    source.write_text('import Dep\nimport Lean\nnamespace CompileMutation\n'
        'theorem bridge (n : Nat) : n = n := rfl\n'
        'theorem selected (n : Nat) : n = n := bridge n\nend CompileMutation\n')
    toolchain = pinned_toolchain(repo)
    execution = prepare_direct_lean_execution(repo, None, toolchain, require_compiled_module=False)
    result = run_bounded_target_process([*execution.command, '-R', str(repo), '-o',
                str(compiled / 'Dep.olean'), str(dependency)], cwd=repo,
                env=execution.environment, timeout_seconds=60, max_output_bytes=8*1024**2,
                max_rss_bytes=32*1024**3)
    assert result.succeeded, result.stdout + result.stderr
    fresh = extract_proof_slice(repo, 'Proof.lean', 'Proof', 'CompileMutation.selected',
                                'CompileMutation.bridge')
    assert fresh['complete'], fresh
    sidecar = compiled / 'Dep.ir.sig'
    assert not sidecar.exists(), 'Lean4.32 fixture requires the recorded absent-sidecar profile'
    original_run = preparation.run_bounded_target_process
    def transient(*args, **kwargs):
        sidecar.write_bytes(b'transient sidecar mutation probe')
        try:
            observed = original_run(*args, **kwargs)
            assert observed.succeeded, observed.stdout + observed.stderr
            return observed
        finally:
            sidecar.unlink()
    monkeypatch.setattr(preparation, 'run_bounded_target_process', transient)
    with (pytest.raises(ValueError, match='(?i)(stale|changed|mutation)'),
          preparation.prepare_source_context(repo, fresh, source.read_bytes(), toolchain)):
        pytest.fail('during-compile sidecar mutation acquired prepared authority')
    assert not sidecar.exists()
    assert not list(compiled.glob('LadonPrepared*'))
