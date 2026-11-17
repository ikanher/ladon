"""Routine freshness checks bind current rows without auditing old snapshots."""
import json

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index


def test_freshness_avoids_history_and_detects_edits(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_history_store as history
    (tmp_path / 'Main.lean').write_text('theorem first : Nat := 1\n')
    build_proof_search_index(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError('routine freshness must not hash historical databases')

    monkeypatch.setattr(history, 'validate_history', forbidden)
    args = ['proof-search', 'index', 'freshness', '--repo-root', str(tmp_path), '--format', 'json']
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first['freshness'] == 'fresh'
    assert first['historyIntegrity'] == 'not-assessed'
    assert set(first['phaseSeconds']) == {'storedIdentity', 'sourceValidation'}
    generation = first['generationIdentity']
    (tmp_path / 'Main.lean').write_text('theorem changed : Nat := 2\n')
    assert main(args + ['--expected-generation', generation]) == 0
    edited = json.loads(capsys.readouterr().out)
    assert edited['freshness'] == 'stale-source'
    assert edited['unchangedSinceExpectedGeneration'] is False


def test_stored_type_search_binds_generation(tmp_path, capsys):
    (tmp_path / 'Main.lean').write_text('theorem first : Nat := 1\n')
    build_proof_search_index(tmp_path)
    args = ['proof-search', 'search', 'type-text', '--repo-root', str(tmp_path),
            '--pattern', 'Nat', '--freshness', 'stored', '--format', 'json']
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['generationIdentity']
    assert result['indexPath'].endswith('proof-search.sqlite')
    assert result['freshnessStatus'] == 'unchecked'
