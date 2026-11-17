"""Batch transport bounds reject invalid inputs before query execution."""
import json

import pytest

from ladon.cli import main


@pytest.mark.parametrize('queries', [[], [[]], [['batch']], [['name', '--text']],
    [['name', '--repo-root', '/elsewhere']], [['name', '--limit', '101', '--text', 'x']],
    [['type-text', '--pattern', 2]], [[[]]], [['name', [], 'x']],
    [['name', '--text', 'x']] * 33])
def test_invalid_queries_are_diagnostics(tmp_path, capsys, queries):
    path = tmp_path / 'queries.json'
    path.write_text(json.dumps(queries))
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) != 0
    captured = capsys.readouterr()
    assert not captured.out
    assert json.loads(captured.err)['status'] == 'failed'
    assert not (tmp_path / '.ladon').exists()


def test_output_limit_is_enforced_before_publication(tmp_path, capsys, monkeypatch):
    from ladon import proof_search_batch as batch
    from ladon.proof_search_index import build_proof_search_index

    (tmp_path / 'Main.lean').write_text('def first : Nat := 1\n')
    build_proof_search_index(tmp_path)
    path = tmp_path / 'queries.json'
    path.write_text(json.dumps([['name', '--text', 'first']]))
    monkeypatch.setattr(batch, '_query', lambda *args: {'large': 'x' * 1024**2})
    output = tmp_path / 'result.json'
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json', '--output', str(output)]) != 0
    assert not output.exists()
    assert 'byte allowance' in capsys.readouterr().err


def test_foreign_worktree_index_is_rejected(tmp_path, capsys):
    from ladon.proof_search_index import build_proof_search_index

    first, second = tmp_path / 'first', tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    (first / 'Main.lean').write_text('def first : Nat := 1\n')
    index = build_proof_search_index(first).index_path
    query = tmp_path / 'query.json'
    query.write_text(json.dumps([['name', '--text', 'first']]))
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(second),
                 '--index', str(index), '--queries', str(query), '--format', 'json']) != 0
    assert 'another repository' in capsys.readouterr().err


def test_missing_index_is_an_operational_diagnostic(tmp_path, capsys):
    query = tmp_path / 'query.json'
    query.write_text(json.dumps([['name', '--text', 'first']]))
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(query), '--format', 'json']) != 0
    captured = capsys.readouterr()
    assert not captured.out
    assert json.loads(captured.err)['exitClass'] == 'operational'
    assert not (tmp_path / '.ladon').exists()
