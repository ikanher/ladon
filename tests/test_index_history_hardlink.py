"""In-place publishers cannot mutate an archive through a hardlink alias."""
from __future__ import annotations

import os
import sqlite3

import pytest
from test_index_history_publication import evidence_index

from ladon.proof_search_history_store import history_directory
from ladon.proof_search_index import update_proof_search_index
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


def test_hardlink_alias_is_rejected_before_in_place_mutation(tmp_path):
    repo, index = evidence_index(tmp_path)
    result = update_proof_search_index(repo)
    snapshot = history_directory(index) / result.payload['preservedSnapshots'][0]['path']
    alias = tmp_path / 'looks-active.sqlite'
    os.link(snapshot, alias)
    original = snapshot.read_bytes()
    with pytest.raises((RuntimeError, ValueError), match='hardlink'):
        lock = acquire_publication_lock(alias)
        try:
            with sqlite3.connect(alias) as connection:
                connection.execute("UPDATE metadata SET value='changed' WHERE key='generationIdentity'")
        finally:
            release_publication_lock(lock)
    assert snapshot.read_bytes() == original
    assert not alias.with_name(alias.name + '.lock').exists()
