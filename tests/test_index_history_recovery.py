"""Migration, overlap and archival publication failure boundaries."""
from __future__ import annotations

import sqlite3

import pytest
from test_index_history_publication import evidence_index
from test_proof_search_active_index import _all_table_rows

from ladon.proof_search_history import list_history, open_history_snapshot
from ladon.proof_search_history_store import history_directory
from ladon.proof_search_index import ProofSearchIndexError, update_proof_search_index
from ladon.proofir_sqlite_v3 import publish_v3_database
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


def test_changed_legacy_v5_layout_migrates_with_original_rows(tmp_path):
    repo, index = evidence_index(tmp_path)
    with sqlite3.connect(index) as connection:
        connection.execute('DROP TABLE index_history')
        connection.execute('PRAGMA user_version=5')
        for key, value in {'indexSchema': 'ladon-proof-search-index-v5',
                           'schemaGeneration': 'sqlite-v5-name2-fts2-lineage1-proofir1',
                           'schemaVersion': '5'}.items():
            connection.execute('UPDATE metadata SET value=? WHERE key=?', (value, key))
    with sqlite3.connect(index) as connection:
        original = _all_table_rows(connection)
    result = update_proof_search_index(repo)
    entry = result.payload['preservedSnapshots'][0]
    with open_history_snapshot(repo, index, entry['snapshotId']) as (connection, _entry, metadata):
        assert metadata['indexSchema'] == 'ladon-proof-search-index-v5'
        connection.row_factory = None
        assert _all_table_rows(connection) == original
    with sqlite3.connect(index) as connection:
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 6


def test_archive_directory_sync_failure_keeps_active_and_discloses_orphan(tmp_path, monkeypatch):
    from ladon import proof_search_history_store as owner
    repo, index = evidence_index(tmp_path)
    original = index.read_bytes()
    def fail_sync(_root):
        raise OSError('injected archive directory sync failure')
    monkeypatch.setattr(owner, '_sync_directory', fail_sync)
    with pytest.raises((OSError, ProofSearchIndexError), match='injected archive'):
        update_proof_search_index(repo)
    assert index.read_bytes() == original
    inventory = list_history(repo)
    assert inventory['total'] == 0
    assert inventory['unregisteredFiles']['total'] == 1
    assert inventory['unregisteredFiles']['rows'][0]['classification'] == 'protected'


def test_existing_publisher_prevents_archive_and_active_mutation(tmp_path):
    repo, index = evidence_index(tmp_path)
    original = index.read_bytes()
    lock = acquire_publication_lock(index)
    try:
        with pytest.raises(ProofSearchIndexError) as raised:
            update_proof_search_index(repo)
        assert 'active' in str(raised.value).lower() or 'progress' in str(raised.value).lower()
        assert index.read_bytes() == original
        assert not history_directory(index).exists()
    finally:
        release_publication_lock(lock)


def test_proofir_full_publication_cannot_overwrite_history_owner(tmp_path):
    repo, index = evidence_index(tmp_path)
    update_proof_search_index(repo)
    original = index.read_bytes()
    with pytest.raises(ProofSearchIndexError):
        publish_v3_database(index, [])
    assert index.read_bytes() == original


def test_joint_relocation_retains_history_selection(tmp_path):
    repo, index = evidence_index(tmp_path)
    result = update_proof_search_index(repo)
    selected = result.payload['preservedSnapshots'][0]['snapshotId']
    folder = tmp_path / 'moved'
    folder.mkdir()
    moved = folder / index.name
    index.rename(moved)
    history_directory(index).rename(history_directory(moved))
    with open_history_snapshot(repo, moved, selected) as (connection, _entry, _metadata):
        assert [tuple(row) for row in connection.execute('SELECT name FROM declarations')] == [('before',)]
