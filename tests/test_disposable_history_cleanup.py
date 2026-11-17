"""Cleanup is explicit, catalog-aware and recoverable after partial unlink."""
import sqlite3

import pytest
from test_index_history_publication import evidence_index

from ladon.proof_search_history_cleanup import apply_history_cleanup, preview_history_cleanup
from ladon.proof_search_history_store import history_directory
from ladon.proof_search_index import ProofSearchIndexError, update_proof_search_index


def archived(tmp_path):
    repo, index = evidence_index(tmp_path)
    result = update_proof_search_index(repo, archive_history=True)
    entry = result.payload['preservedSnapshots'][0]
    return repo, index, history_directory(index) / entry['path']


def test_preview_then_apply_preserves_active_and_unknown_files(tmp_path):
    repo, index, archive = archived(tmp_path)
    unknown = archive.parent / 'keep.txt'
    unknown.write_text('unregistered')
    original_names = sqlite3.connect(index).execute('SELECT name FROM declarations').fetchall()
    preview = preview_history_cleanup(repo, all_registered=True)
    assert preview['selectedBytes'] == archive.stat().st_size
    assert archive.exists()
    result = apply_history_cleanup(repo, preview)
    assert result['removedBytes'] == preview['selectedBytes']
    assert not archive.exists()
    assert unknown.read_text() == 'unregistered'
    with sqlite3.connect(index) as connection:
        assert connection.execute('SELECT name FROM declarations').fetchall() == original_names
        assert connection.execute('SELECT COUNT(*) FROM index_history').fetchone()[0] == 0
    assert apply_history_cleanup(repo, preview)['removedBytes'] == 0


def test_changed_file_blocks_catalog_mutation(tmp_path):
    repo, index, archive = archived(tmp_path)
    preview = preview_history_cleanup(repo, all_registered=True)
    archive.write_bytes(b'changed')
    with pytest.raises(ProofSearchIndexError, match='changed since preview'):
        apply_history_cleanup(repo, preview)
    with sqlite3.connect(index) as connection:
        assert connection.execute('SELECT COUNT(*) FROM index_history').fetchone()[0] == 1


def test_symlink_is_rejected(tmp_path):
    repo, index, archive = archived(tmp_path)
    archive.unlink()
    archive.symlink_to(index)
    with pytest.raises(ProofSearchIndexError, match='refuses'):
        preview_history_cleanup(repo, all_registered=True)


def test_interrupted_unlink_can_be_resumed(tmp_path, monkeypatch):
    from pathlib import Path

    repo, _index, archive = archived(tmp_path)
    preview = preview_history_cleanup(repo, all_registered=True)
    original = Path.unlink

    def interrupt(path, *args, **kwargs):
        if path == archive:
            raise OSError('interrupted unlink')
        return original(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, 'unlink', interrupt)
        with pytest.raises(OSError, match='interrupted unlink'):
            apply_history_cleanup(repo, preview)
    assert archive.exists()
    assert apply_history_cleanup(repo, preview)['removedBytes'] > 0
    assert not archive.exists()


def test_public_cleanup_cli_requires_saved_preview(tmp_path, capsys):
    import json

    from ladon.cli import main

    repo, _index, archive = archived(tmp_path)
    base = ['proof-search', 'index', 'history-cleanup', '--repo-root', str(repo), '--format', 'json']
    assert main(base + ['--all-registered']) == 0
    preview = json.loads(capsys.readouterr().out)
    saved = tmp_path / 'preview.json'
    saved.write_text(json.dumps(preview))
    assert archive.exists()
    assert main(base + ['--apply', '--preview-file', str(saved)]) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'complete'
    assert not archive.exists()


def test_missing_files_can_be_removed_from_catalog(tmp_path):
    repo, index, archive = archived(tmp_path)
    archive.unlink()
    preview = preview_history_cleanup(repo, all_registered=True)
    assert preview['selectedBytes'] == 0
    assert apply_history_cleanup(repo, preview)['removedBytes'] == 0
    with sqlite3.connect(index) as connection:
        assert connection.execute('SELECT COUNT(*) FROM index_history').fetchone()[0] == 0


def test_cleanup_respects_publication_lock(tmp_path):
    from ladon.sqlite_publication import (
        PublicationLockBusy,
        acquire_publication_lock,
        release_publication_lock,
    )

    repo, index, archive = archived(tmp_path)
    preview = preview_history_cleanup(repo, all_registered=True)
    lock = acquire_publication_lock(index)
    try:
        with pytest.raises(PublicationLockBusy):
            apply_history_cleanup(repo, preview)
        assert archive.exists()
    finally:
        release_publication_lock(lock)


def test_modified_preview_is_rejected(tmp_path):
    repo, _index, archive = archived(tmp_path)
    preview = preview_history_cleanup(repo, all_registered=True)
    preview['selected'][0]['path'] = str(archive.parent / 'other-file')
    with pytest.raises(ProofSearchIndexError, match='identity or owner mismatch'):
        apply_history_cleanup(repo, preview)
    assert archive.exists()
