"""Stored omission metadata is not an axiom; acquisition stops at its budget."""
from __future__ import annotations

import copy
import sqlite3

import pytest
from test_result_lineage import _inspect, _lineage_fixture

from ladon import result_lineage_store
from ladon.result_manifest_io import ResultManifestError


def test_truncated_omissions_are_retained_without_becoming_axioms(tmp_path, monkeypatch):
    manifest, artifacts, companion, db, inserted = _lineage_fixture(tmp_path)
    with sqlite3.connect(db) as conn:
        for n in range(3):
            conn.execute('INSERT INTO lineage_omissions VALUES (?,?,?,?,?)',
                         (inserted['closureId'], 'test-facet', str(n), 'unavailable', '{}'))
    monkeypatch.setattr(result_lineage_store, 'ROW_LIMIT', 1)
    assumptions = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions')
    assert not any(r.get('reason') == 'stored-acquisition-truncated' and
                   'lineage_omissions' in str(r.get('references')) for r in assumptions['rows'])
    lineage = _inspect(manifest, artifacts, companion, tmp_path, section='lineage')
    assert lineage['rows'][0]['ownerDetails']['tables']['lineage_omissions']['truncated'] is True


def test_oversized_stored_field_is_rejected_before_projection(tmp_path):
    manifest, artifacts, companion, db, inserted = _lineage_fixture(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute('INSERT INTO lineage_omissions VALUES (?,?,?,?,?)',
                     (inserted['closureId'], 'test-facet', 'large', 'unavailable', 'x' * 70000))
    with pytest.raises(ResultManifestError, match='lineage'):
        _inspect(manifest, artifacts, companion, tmp_path, section='components')


def test_many_selections_share_one_acquisition_byte_budget(tmp_path, monkeypatch):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    for n in range(12):
        entry = copy.deepcopy(companion['entries'][0])
        entry['id'] = f'capture-{n}'
        companion['entries'].append(entry)
    monkeypatch.setattr(result_lineage_store, 'MAX_ACQUIRED_BYTES', 12000, raising=False)
    with pytest.raises(ResultManifestError, match='lineage.*(byte|limit)'):
        _inspect(manifest, artifacts, companion, tmp_path, section='components')
