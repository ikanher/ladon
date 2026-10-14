"""Compiler transport of quoted/prime names, dependent types, lets and shadowing."""
import json
import shutil
from pathlib import Path

import pytest

from ladon.correspondence_check import _check_goal, prepare_correspondence
from ladon.proof_slice import extract_proof_slice, pinned_toolchain

SOURCE = '''import Lean
namespace ComplexTransport
theorem bridge (n x : Nat) (h : x < n + 1) : x < n + 2 := Nat.lt.step h
theorem selected (n₀ : Nat) («rate β» : Fin (n₀ + 1)) : «rate β».val < n₀ + 2 := by
  let x' := «rate β».val
  have h' : x' < n₀ + 1 := «rate β».isLt
  exact bridge n₀ x' h'
theorem reflBridge (x : Nat) : x = x := rfl
theorem shadow (x : Nat) : x = x := (fun (x : Nat) => reflBridge x) x
end ComplexTransport
'''


def root_for(tmp_path):
    root = tmp_path / 'repo'
    shutil.copytree(Path(__file__).parent / 'fixtures/correspondence_m1', root,
                    ignore=shutil.ignore_patterns('.ladon', '.lake', '*.olean'))
    (root / 'Complex.lean').write_text(SOURCE)
    return root


def test_dependent_types_and_local_let_values_are_rechecked_without_old_fvars(tmp_path):
    root = root_for(tmp_path)
    source = (root / 'Complex.lean').read_bytes()
    actual = extract_proof_slice(root, 'Complex.lean', 'Complex', 'ComplexTransport.selected',
                                 'ComplexTransport.bridge', scoped=True)
    assert actual['complete'], actual
    transport = _assert_transport(actual)
    checked = _check_goal(transport['closedType'], transport['closedProof'], root, source,
                          {}, pinned_toolchain(root))
    assert checked['status'] == 'supported', checked
    assert checked['completion']['replay']['status'] == 'accepted'
    assert checked['completion']['trust']['coverage'] == 'complete'
    assert checked['completion']['trust']['accepted']
    assert (root / 'Complex.lean').read_bytes() == source


def test_actual_shadowed_display_names_cannot_select_an_ambiguous_object(tmp_path):
    root = root_for(tmp_path)
    actual = extract_proof_slice(root, 'Complex.lean', 'Complex', 'ComplexTransport.shadow',
                                 'ComplexTransport.reflBridge', scoped=True)
    assert actual['complete'], actual
    x_rows = [r for r in actual['localContext'] if r['name'] == 'x']
    assert len(x_rows) == 2
    assert len({r['localId'] for r in x_rows}) == 2
    record = json.loads((root / 'positive.json').read_bytes())
    with pytest.raises(ValueError, match='ambiguous'):
        prepare_correspondence(record, actual, {'x': 'n'})


def _assert_transport(actual):
    original = actual['localContext']
    assert {'n₀', '«rate β»', "x'", "h'"} <= {r['name'] for r in original}
    selected = actual['observation']['applications'][actual['selection']['occurrence']]
    transport = selected['transport']
    assert [r['originalLocalId'] for r in transport['localContext']] == [r['localId'] for r in original]
    assert any(r['letValue'] is not None for r in transport['localContext'])
    _assert_fvars(original, transport)
    return transport


def _assert_fvars(original, transport):
    old_ids = {r['localId'] for r in original}
    new_ids = {r['localId'] for r in transport['localContext']}
    assert not old_ids & new_ids
    for row in transport['localContext']:
        graph = json.loads(row['type']['structural'].removeprefix('ladon-expr-dag-v1:'))
        observed = {node[1] for node in graph['nodes'] if node[0] == 'fvar'}
        assert not observed & old_ids
        assert observed <= new_ids
