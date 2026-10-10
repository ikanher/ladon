from __future__ import annotations

import sqlite3

from ladon.proof_search_index import build_proof_search_index


def signature(tmp_path, source):
    (tmp_path / 'Main.lean').write_text(source)
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        return db.execute('SELECT type_text FROM declarations').fetchone()[0]


def test_multiline_binding_assignment_keeps_conclusion(tmp_path):
    text = signature(tmp_path, 'theorem t : let x\n    := 1; FinalMarker x := by trivial\n')
    assert 'FinalMarker x' in text


def test_unfinished_proof_does_not_invalidate_statement(tmp_path):
    text = signature(tmp_path, 'theorem t : let x := 1; FinalMarker x := by\n  exact (\n')
    assert 'FinalMarker x' in text
    assert 'exact' not in text


def test_unsupported_recursive_let_is_unavailable(tmp_path):
    text = signature(tmp_path, 'theorem t : let rec f (n : Nat) := n; FinalMarker f := by trivial\n')
    assert text is None


def test_nested_match_does_not_cut_off_conclusion(tmp_path):
    text = signature(tmp_path, '''theorem t :
    let x := (match 1 with
      | 0 => 1
      | n => n)
    FinalMarker x := by trivial
''')
    assert 'FinalMarker x' in text
    assert 'by trivial' not in text
