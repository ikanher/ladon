from __future__ import annotations

import sqlite3

from ladon.proof_search_index import build_proof_search_index


def test_bodyless_axiom_retains_supported_let_statement(tmp_path):
    (tmp_path / 'Main.lean').write_text('axiom a : let x := 1; FinalMarker x\n')
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        text, status = db.execute('SELECT type_text, type_status FROM declarations').fetchone()
    assert status == 'lexical-signature'
    assert 'FinalMarker x' in text
