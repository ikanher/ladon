"""Routine updates discard derived cache observations without archiving."""
import sqlite3

from test_index_history_publication import evidence_index

from ladon.proof_search_history_store import history_directory
from ladon.proof_search_index import update_proof_search_index


def test_default_update_does_not_archive_derived_evidence(tmp_path):
    repo, index = evidence_index(tmp_path)
    result = update_proof_search_index(repo)
    assert result.payload['preservedSnapshots'] == []
    assert result.payload['derivedEvidence'] == 'invalidated'
    assert not history_directory(index).exists()
    with sqlite3.connect(index) as connection:
        assert connection.execute('SELECT COUNT(*) FROM binders').fetchone()[0] == 0
        assert connection.execute('SELECT name FROM declarations').fetchone()[0] == 'after'


def test_missing_old_archive_does_not_block_current_updates(tmp_path):
    repo, index = evidence_index(tmp_path)
    first = update_proof_search_index(repo, archive_history=True)
    entry = first.payload['preservedSnapshots'][0]
    (history_directory(index) / entry['path']).unlink()
    (repo / 'Main.lean').write_text('theorem latest : True := True.intro\n')
    result = update_proof_search_index(repo)
    assert result.payload['status'] == 'complete'
    assert result.payload['historyIntegrity'] == 'not-assessed'


def test_noop_keeps_observations_and_creates_no_archive(tmp_path):
    repo, index = evidence_index(tmp_path)
    (repo / 'Main.lean').write_text('theorem before : True := True.intro\n')
    original = index.read_bytes()
    result = update_proof_search_index(repo)
    assert result.payload['status'] == 'unchanged'
    assert result.payload['derivedEvidence'] == 'unchanged'
    assert index.read_bytes() == original
    assert not history_directory(index).exists()


def test_saved_output_is_not_owned_by_cache_update(tmp_path):
    repo, _index = evidence_index(tmp_path)
    output = repo / 'audit-result.json'
    output.write_text('{"reading":"explicitly saved"}\n')
    original = output.read_bytes()
    update_proof_search_index(repo)
    assert output.read_bytes() == original


def test_authored_idea_metadata_is_preserved(tmp_path):
    repo, index = evidence_index(tmp_path)
    with sqlite3.connect(index) as connection:
        connection.execute("INSERT INTO ideas VALUES ('authored','Title','Statement','Scope')")
    update_proof_search_index(repo)
    with sqlite3.connect(index) as connection:
        assert connection.execute('SELECT title FROM ideas WHERE id=?', ('authored',)).fetchone() == ('Title',)
