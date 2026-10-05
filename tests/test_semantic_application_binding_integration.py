"""An assigned argument must survive subsequent premise discharge and replay."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SOURCE = '''namespace BindingFixture
opaque measure (scale point : Nat) : Nat := scale + point
-- Synthetic signature only: this axiom tests argument ownership, not mathematics.
axiom propagate (h boundary query : Nat) (hh : 0 < h)
  (hb : 0 ≤ boundary) (hbq : boundary < query)
  (hg : 0 ≤ measure h boundary) : 0 < measure h query
end BindingFixture
'''
LOCALS = ['h:Nat', 'boundary:Nat', 'query:Nat', 'hh:0 < h',
          'hb:0 ≤ boundary', 'hbq:boundary < query',
          'hg:0 ≤ BindingFixture.measure h boundary']


def _project(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    project.joinpath('lean-toolchain').write_text('leanprover/lean4:v4.32.1\n')
    project.joinpath('lakefile.toml').write_text(
        'name = "binding_fixture"\ndefaultTargets = ["BindingFixture"]\n'
        '[[lean_lib]]\nname = "BindingFixture"\n')
    project.joinpath('BindingFixture.lean').write_text(SOURCE)
    built = subprocess.run(['lake', 'build'], cwd=project, capture_output=True,
                           text=True, check=False, timeout=60)
    assert built.returncode == 0, built.stdout + built.stderr
    return project


def _command(project, locals_):
    lean = subprocess.check_output(['elan', 'which', 'lean'], cwd=project, text=True).strip()
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    argv = [console, 'proof-search', 'discover', '--repo-root', str(project),
            '--module', 'BindingFixture', '--goal', '0 < BindingFixture.measure h query',
            '--candidate', 'BindingFixture.propagate', '--toolchain-mode', 'explicit',
            '--lean-path', lean, '--lake-path', str(Path(lean).with_name('lake')),
            '--scratch-mode', 'advisory', '--projection', 'audit', '--format', 'json',
            '--evidence-store', str(project.parent / 'evidence.sqlite')]
    for local in locals_:
        argv.extend(['--local', local])
    return argv


@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean unavailable')
@pytest.mark.parametrize('complete', [True, False])
def test_assigned_argument_is_not_replaced_by_another_local_of_the_same_type(tmp_path, complete):
    project = _project(tmp_path)
    locals_ = LOCALS if complete else LOCALS[:-1]
    result = subprocess.run(_command(project, locals_), cwd=tmp_path, text=True,
                            capture_output=True, check=False, timeout=90)
    payload = json.loads(result.stdout)
    checked = payload['candidates'][0]['check']
    assert result.returncode == 0, checked.get('scratch')
    _assert_application(checked, complete)


def _assert_application(checked, complete):
    if complete:
        assert checked['status'] == 'accepted'
        assert checked['scratch']['status'] == 'compiled', checked['scratch']
    else:
        assert checked['status'] == 'applicable-with-residuals', checked
        assert [row['typeDisplay'] for row in checked['residualPremises']] == [
            '0 ≤ BindingFixture.measure h boundary']
