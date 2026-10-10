from __future__ import annotations

import sqlite3

from ladon.proof_search_index import build_proof_search_index


def test_layout_lets_and_absolute_value_conclusion_survive(tmp_path):
    (tmp_path / 'Main.lean').write_text('''theorem fieldShape (x : Real) :
    let state := x
    let scale := (let inner := state; inner + 1)
    let value := fun t => scale * t
    |value x| ≤ FinalMarker x := by
  exact ProofBodyOnlySymbol
''')
    index = build_proof_search_index(tmp_path).index_path
    with sqlite3.connect(index) as db:
        text, truncated = db.execute('SELECT type_text, type_text_truncated FROM declarations').fetchone()
    assert 'let state := x' in text
    assert '|value x| ≤ FinalMarker x' in text
    assert 'ProofBodyOnlySymbol' not in text
    assert not truncated
