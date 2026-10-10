from __future__ import annotations

import sqlite3

import pytest

from ladon.proof_search_index import build_proof_search_index


@pytest.mark.parametrize('binding', ['←', '<-'])
def test_unsupported_do_binding_never_captures_proof(tmp_path, binding):
    (tmp_path / 'Main.lean').write_text(
        f'theorem t : do let x {binding} action; pure (FinalMarker x) := by exact ProofLeakMarker\n'
    )
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        assert db.execute('SELECT type_text, type_status FROM declarations').fetchone() == (None, 'unavailable')
        assert db.execute("SELECT reason FROM omissions WHERE kind='declaration'").fetchall() == [('lexical_signature_unavailable',)]
