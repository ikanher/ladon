from __future__ import annotations

import sqlite3

from ladon.proof_search_index import build_proof_search_index, update_proof_search_index


def test_unavailable_omission_is_replaced_with_its_module(tmp_path):
    source = tmp_path / 'Main.lean'
    source.write_text('theorem t (x : Nat : FinalMarker := by trivial\n')
    index = build_proof_search_index(tmp_path).index_path
    source.write_text('theorem t (x : Int : FinalMarker := by trivial\n')
    assert update_proof_search_index(tmp_path).payload['status'] == 'complete'
    with sqlite3.connect(index) as db:
        assert db.execute("SELECT reason FROM omissions WHERE kind='declaration'").fetchall() == [('lexical_signature_unavailable',)]
    source.write_text('theorem t : FinalMarker := by trivial\n')
    update_proof_search_index(tmp_path)
    with sqlite3.connect(index) as db:
        assert db.execute("SELECT reason FROM omissions WHERE kind='declaration'").fetchall() == []
