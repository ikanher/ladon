"""Progress events never imply publication after a refused or failed build."""
import json

from ladon.proof_search_cli import proof_search_main
from ladon.proof_search_index import build_proof_search_index
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


def _events(capsys):
    streams = capsys.readouterr()
    assert streams.out == ''
    return [json.loads(line) for line in streams.err.splitlines()]


def test_busy_build_emits_refusal_without_extraction(tmp_path, capsys):
    (tmp_path / 'Owner.lean').write_text('def n := 0\n')
    database = build_proof_search_index(tmp_path).index_path
    original = database.read_bytes()
    lock = acquire_publication_lock(database)
    try:
        assert proof_search_main(['index', 'build', '--repo-root', str(tmp_path), '--progress']) == 2
    finally:
        release_publication_lock(lock)
    events = _events(capsys)
    assert events[0]['phase'] == 'dispatch'
    assert events[-1]['schema'] == 'ladon-proof-search-terminal-v1'
    assert events[-1]['status'] == 'failed'
    assert not any(row.get('phase') == 'extraction' for row in events)
    assert database.read_bytes() == original


def test_failed_publication_preserves_old_database_and_reports_failure(tmp_path, capsys, monkeypatch):
    import ladon.proof_search_index as owner

    (tmp_path / 'Owner.lean').write_text('def n := 0\n')
    database = build_proof_search_index(tmp_path).index_path
    original = database.read_bytes()

    def fail(_source, _destination):
        raise OSError('injected publication failure')

    monkeypatch.setattr(owner, 'durable_replace', fail)
    assert proof_search_main(['index', 'build', '--repo-root', str(tmp_path), '--progress']) == 1
    events = _events(capsys)
    assert events[-2]['phase'] == 'publication'
    assert events[-1]['status'] == 'failed'
    assert not any(row.get('status') == 'completed' for row in events)
    assert database.read_bytes() == original
    assert not list(database.parent.glob('.proof-search.sqlite.*.tmp'))
