"""Direct paths and aliases cannot turn immutable snapshots into active indexes."""
from __future__ import annotations

import pytest
from test_index_history_publication import evidence_index

from ladon.proof_search_history_store import history_directory
from ladon.proof_search_index import build_proof_search_index, update_proof_search_index
from ladon.proofir_sqlite_v3 import publish_v3_database
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


@pytest.mark.parametrize('writer', ['update', 'build', 'proofir', 'lock'])
def test_mutation_rejects_direct_snapshot_destination(tmp_path, writer):
    repo, index = evidence_index(tmp_path)
    result = update_proof_search_index(repo)
    snapshot = history_directory(index) / result.payload['preservedSnapshots'][0]['path']
    original = snapshot.read_bytes()
    (repo / 'Main.lean').write_text('theorem furtherEdit : True := True.intro\n')
    with pytest.raises((RuntimeError, ValueError), match='histor'):
        if writer == 'update':
            update_proof_search_index(repo, index_path=snapshot)
        elif writer == 'build':
            build_proof_search_index(repo, index_path=snapshot)
        elif writer == 'proofir':
            publish_v3_database(snapshot, [])
        else:
            lock = acquire_publication_lock(snapshot)
            release_publication_lock(lock)
    assert snapshot.read_bytes() == original
    assert not snapshot.with_name(snapshot.name + '.lock').exists()


def test_snapshot_alias_does_not_bypass_mutation_guard(tmp_path):
    repo, index = evidence_index(tmp_path)
    result = update_proof_search_index(repo)
    snapshot = history_directory(index) / result.payload['preservedSnapshots'][0]['path']
    alias = tmp_path / 'looks-active.sqlite'
    alias.symlink_to(snapshot)
    original = snapshot.read_bytes()
    with pytest.raises((RuntimeError, ValueError), match='histor'):
        lock = acquire_publication_lock(alias)
        release_publication_lock(lock)
    assert snapshot.read_bytes() == original
    assert alias.is_symlink()
