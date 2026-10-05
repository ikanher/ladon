"""Pretty-printed applications must replay as one Lean term across lines."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.scratch_replay import build_scratch_source


@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean unavailable')
@pytest.mark.parametrize('introduced', [False, True])
def test_multiline_application_compiles_in_its_original_context(tmp_path, introduced):
    context = [{'name': 'P', 'type': 'Prop'}, {'name': 'h', 'type': 'P'}]
    goal = '∀ (P : Prop), P → P' if introduced else 'P'
    source = build_scratch_source('LadonFixture', goal, 'id\n  h',
                                  [] if introduced else context,
                                  context if introduced else [])
    path = tmp_path / 'Replay.lean'
    path.write_text(source)
    fixture = Path(__file__).parent / 'fixtures/lean_integration'
    result = subprocess.run(['lake', 'env', 'lean', str(path)], cwd=fixture,
                            text=True, capture_output=True, check=False, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
