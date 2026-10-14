"""Non-exported elaboration state must not change request checking subjects."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ladon.correspondence_check import _check_goal
from ladon.correspondence_preparation import prepare_source_context
from ladon.proof_slice import extract_proof_slice, pinned_toolchain

SOURCE = '''import Lean
class ScopeProbe where
  value : Nat
instance : ScopeProbe := ⟨0⟩
{local_command}
theorem bridge (n : Nat) : n = n := rfl
theorem selected (n : Nat) : n = n := bridge n
'''


def _case(tmp_path, command):
    root = tmp_path / 'repo'
    shutil.copytree(Path(__file__).parent / 'fixtures/correspondence_m1', root,
                    ignore=shutil.ignore_patterns('.ladon', '.lake', '*.olean'))
    (root / '.lake/build/lib/lean').mkdir(parents=True)
    source = SOURCE.format(local_command=command).encode()
    (root / 'Proof.lean').write_bytes(source)
    toolchain = pinned_toolchain(root)
    fresh = extract_proof_slice(root, 'Proof.lean', 'Proof', 'selected', 'bridge')
    assert fresh['complete'], fresh
    return root, source, toolchain, fresh


@pytest.mark.parametrize('command', [
    'local instance : ScopeProbe := ⟨1⟩',
    'local notation "localOne" => (1 : Nat)',
    'attribute [local simp] ScopeProbe.value',
])
def test_nonexported_local_environment_declines_request_preparation(tmp_path, command):
    root, source, toolchain, fresh = _case(tmp_path, command)
    with prepare_source_context(root, fresh, source, toolchain) as prepared:
        assert prepared is None, 'local environment state is not exported through an ordinary import'
    goal = 'ScopeProbe.value = 1' if 'instance' in command else 'ScopeProbe.value = 0'
    checked = _check_goal(goal, 'by rfl', root, source, {}, toolchain)
    assert checked['status'] == 'supported', checked
    assert checked['completion']['replay']['status'] == 'accepted'
    assert checked['completion']['trust']['accepted'] is True
    assert checked['completion']['trust']['coverage'] == 'complete'
    assert (root / 'Proof.lean').read_bytes() == source
    assert not list((root / '.lake/build/lib/lean').glob('LadonPrepared*'))


def test_exported_global_instance_keeps_exact_subject_and_trust(tmp_path):
    root, source, toolchain, fresh = _case(tmp_path, '')
    ordinary = _check_goal('ScopeProbe.value = 0', 'by rfl', root, source, {}, toolchain)
    with prepare_source_context(root, fresh, source, toolchain) as prepared:
        assert prepared is not None
        request = _check_goal('ScopeProbe.value = 0', 'by rfl', root, source, {}, toolchain,
                              prepared=prepared)
    assert ordinary['status'] == request['status'] == 'supported'
    assert ordinary['typedSubject']['subject']['structural'] == request['typedSubject']['subject']['structural']
    for checked in (ordinary, request):
        assert checked['completion']['replay']['status'] == 'accepted'
        assert checked['completion']['trust']['accepted'] is True
        assert checked['completion']['trust']['coverage'] == 'complete'
