from __future__ import annotations

import sqlite3

from ladon.proof_search_index import build_proof_search_index


def test_incomplete_binding_cannot_consume_body_assignment(tmp_path):
    (tmp_path / 'Main.lean').write_text('theorem t : let x ← action; FinalMarker x := by exact ProofLeakMarker\n')
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        assert db.execute('SELECT type_text, type_status FROM declarations').fetchone() == (None, 'unavailable')
