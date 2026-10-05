"""Lineage projection preserves uncertainty and does not relabel trust facts."""
from __future__ import annotations

import copy
import sqlite3

import pytest
from test_result_lineage import _inspect, _lineage_fixture

from ladon.result_manifest_io import ResultManifestError


def test_unsafe_trust_is_not_a_declared_mathematical_assumption(tmp_path):
    manifest, artifacts, companion, db, inserted = _lineage_fixture(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute('INSERT INTO lineage_trust VALUES (?,?,?,?)',
                     (inserted['closureId'], 'unsafe_reference', 'value', 'Demo.proof'))
        conn.execute('INSERT INTO lineage_trust VALUES (?,?,?,?)',
                     (inserted['closureId'], 'sorryAx', 'value', 'Demo.proof'))
    rows = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions')['rows']
    assert all(r['status'] == 'unavailable' for r in rows if r['kind'] == 'declared-external-assumptions')
    assert any(r['kind'] == 'placeholders' and r['observation']['kind'] == 'sorryAx'
               for r in rows if r['status'] == 'observed')
    lineage = _inspect(manifest, artifacts, companion, tmp_path, section='lineage')
    assert 'unsafe_reference' in str(lineage)


def test_historical_selection_never_claims_current_observations(tmp_path):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    companion['entries'][0]['targetRevision'] = 'sha256:' + '0' * 64
    row = _inspect(manifest, artifacts, companion, tmp_path, section='lineage')['rows'][0]
    assert row['status'] == 'historical'
    rows = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions')['rows']
    assert all(r['selectionCurrency'] == 'historical' for r in rows)
    assert all(r['status'] != 'observed' for r in rows)


def test_wrong_closure_cannot_use_active_same_name_capture(tmp_path):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    companion['entries'][0]['closureId'] = 'other-closure'
    row = _inspect(manifest, artifacts, companion, tmp_path, section='lineage')['rows'][0]
    assert row['status'] == 'mismatched'
    assert row['reason'] == 'closure-mismatch'


def test_malformed_store_is_validated_even_when_hidden_by_section(tmp_path):
    manifest, artifacts, companion, db, _inserted = _lineage_fixture(tmp_path)
    db.write_bytes(b'not a sqlite database')
    with pytest.raises(ResultManifestError, match='lineage'):
        _inspect(manifest, artifacts, companion, tmp_path, section='components')


def test_missing_store_does_not_make_a_current_selection_historical(tmp_path):
    manifest, artifacts, companion, db, _inserted = _lineage_fixture(tmp_path)
    db.unlink()
    row = _inspect(manifest, artifacts, companion, tmp_path, section='lineage')['rows'][0]
    assert row['selectionCurrency'] == 'current'


def test_clipped_trust_fields_keep_exact_store_drilldown(tmp_path):
    manifest, artifacts, companion, db, inserted = _lineage_fixture(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute('UPDATE lineage_nodes SET name=? WHERE closure_id=? AND name=?',
                     ('λ' * 5000, inserted['closureId'], 'Classical.choice'))
        conn.execute('UPDATE lineage_edges SET target=? WHERE closure_id=? AND target=?',
                     ('λ' * 5000, inserted['closureId'], 'Classical.choice'))
        conn.execute('UPDATE lineage_trust SET target=? WHERE closure_id=?',
                     ('λ' * 5000, inserted['closureId']))
        conn.execute('UPDATE lineage_scc_members SET member=? WHERE closure_id=? AND member=?',
                     ('λ' * 5000, inserted['closureId'], 'Classical.choice'))
    rows = _inspect(manifest, artifacts, companion, tmp_path, section='assumptions')['rows']
    row = next(r for r in rows if r['kind'] == 'observed-axioms')
    ref = next(o['reference'] for o in row['fieldOmissions'] if o['path'] == '/observation/target')
    assert ref['input'] == 'lineage-database'
    assert ref['closureId'] == inserted['closureId']
    assert ref['table'] == 'lineage_trust'
    assert ref['pointer'] == '/target'


def test_identity_drift_is_retained_independently_of_correspondence(tmp_path):
    manifest, artifacts, companion, _db, _inserted = _lineage_fixture(tmp_path)
    changed = copy.deepcopy(companion)
    changed['entries'][0]['identity']['toolchain_identity'] = 'another toolchain'
    result = _inspect(manifest, artifacts, changed, tmp_path, section='lineage')
    assert result['rows'][0]['reason'] == 'stale-toolchain'
    assert result['axes']['correspondence'] == 'attributed-reviews-only'
