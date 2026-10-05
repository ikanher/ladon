"""Every acquired trust observation remains reachable through bounded pages."""
from __future__ import annotations

import json
import sqlite3

from test_result_lineage import _inspect, _lineage_fixture

from ladon.result_inspection_page import text_projection


def test_assumption_pages_recover_all_captured_rows_with_exact_text_parity(tmp_path):
    manifest, artifacts, companion, db, inserted = _lineage_fixture(tmp_path)
    expected = _populate(db, inserted)
    observed, offsets = _pages(manifest, artifacts, companion, tmp_path)
    assert set(observed) == expected
    assert len(observed) == len(expected)
    assert offsets == sorted(set(offsets))


def _populate(db, inserted):
    with sqlite3.connect(db) as conn:
        columns = [r[1] for r in conn.execute('PRAGMA table_info(lineage_nodes)')]
        original = list(conn.execute('SELECT * FROM lineage_nodes WHERE name=?', ('Classical.choice',)).fetchone())
        expected = {'Classical.choice'}
        for n in range(40):
            name = f'Test.axiom{n}'
            values = original.copy()
            values[columns.index('name')] = name
            conn.execute('INSERT INTO lineage_nodes VALUES (' + ','.join('?' for _ in values) + ')', values)
            conn.execute('INSERT INTO lineage_trust VALUES (?,?,?,?)',
                         (inserted['closureId'], 'axiom_reference', 'value', name))
            expected.add(name)
    return expected


def _pages(manifest, artifacts, companion, tmp_path):
    cursor, observed, offsets = None, [], []
    while True:
        result = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions', limit=5, cursor=cursor)
        _assert_rendering(result)
        offsets.append(result['pagination']['offset'])
        observed.extend(r['observation']['target'] for r in result['rows'] if r['kind'] == 'observed-axioms')
        cursor = result['pagination']['nextCursor']
        if cursor is None:
            break
    return observed, offsets


def _assert_rendering(result):
    rendered = text_projection(result)
    decoded = {k: json.loads(v) for k, v in (line.split(': ', 1) for line in rendered.splitlines())}
    assert decoded == result
    assert len(rendered.encode()) + 1 <= 32768
