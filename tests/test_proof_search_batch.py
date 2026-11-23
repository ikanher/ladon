"""One bounded batch shares a read generation and source validation window."""
import json

import pytest

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index


def fixture(tmp_path):
    (tmp_path / 'Main.lean').write_text('theorem first : Nat := 1\n')
    build_proof_search_index(tmp_path)
    path = tmp_path / 'queries.json'
    path.write_text(json.dumps([['name', '--text', 'first'], ['type-text', '--pattern', 'Nat']]))
    return path


def test_batch_shares_validation_and_generation(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_index as index

    path = fixture(tmp_path)
    original = index.capture_repository_snapshot
    captures = []

    def capture(root):
        captures.append(root)
        return original(root)

    monkeypatch.setattr(index, 'capture_repository_snapshot', capture)
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['freshness'] == 'verified-fresh'
    assert result['validation']['captureCount'] == len(captures) == 2
    assert result['returnedQueries'] == 2
    assert all(r['generationIdentity'] == result['generationIdentity'] for r in result['queries'])
    assert result['queries'][0]['results'][0]['candidateName'] == 'first'
    assert result['queries'][1]['results'][0]['candidateName'] == 'first'
    assert result['validation']['authority'] == 'observed-source-window'


def test_source_edit_during_batch_withholds_results(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_batch as batch

    path = fixture(tmp_path)
    original = batch._query

    def query(*args, **kwargs):
        result = original(*args, **kwargs)
        (tmp_path / 'Main.lean').write_text('theorem second : Nat := 2\n')
        return result

    monkeypatch.setattr(batch, '_query', query)
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) != 0
    result = json.loads(capsys.readouterr().out)
    assert result['freshness'] == 'unstable-source'
    assert result['queries'] == []
    assert result['sourceChanges']['changed'][0]['path'] == 'Main.lean'


def test_stale_index_is_rejected_before_queries(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_batch as batch

    path = fixture(tmp_path)
    (tmp_path / 'Main.lean').write_text('theorem stale : Nat := 2\n')

    def forbidden(*args):
        raise AssertionError('query ran on stale inputs')

    monkeypatch.setattr(batch, '_query', forbidden)
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) != 0
    result = json.loads(capsys.readouterr().out)
    assert result['freshness'] == 'stale-source'
    assert result['queries'] == []


def test_generation_publication_during_batch_is_reported(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_batch as batch
    from ladon.proof_search_index import update_proof_search_index

    path = fixture(tmp_path)
    original = batch._query
    observed = []

    def query(connection, args):
        result = original(connection, args)
        observed.append(result['results'][0]['candidateName'])
        if len(observed) == 1:
            (tmp_path / 'Main.lean').write_text('theorem replacement : Nat := 2\n')
            update_proof_search_index(tmp_path)
        return result

    monkeypatch.setattr(batch, '_query', query)
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) != 0
    result = json.loads(capsys.readouterr().out)
    assert observed == ['first', 'first']
    assert result['freshness'] == 'unstable-source'
    assert result['queries'] == []


def test_queries_have_standalone_result_parity(tmp_path, capsys):
    path = fixture(tmp_path)
    for mode, args in [('name', ['--text', 'first']), ('type-text', ['--pattern', 'Nat'])]:
        assert main(['proof-search', 'search', mode, *args, '--repo-root', str(tmp_path),
                     '--freshness', 'stored', '--format', 'json']) == 0
        expected = json.loads(capsys.readouterr().out)['results']
        path.write_text(json.dumps([[mode, *args]]))
        assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                     '--queries', str(path), '--format', 'json']) == 0
        actual = json.loads(capsys.readouterr().out)['queries'][0]['results']
        assert actual == expected


def test_configuration_edit_during_batch_is_identified(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_batch as batch

    path = fixture(tmp_path)
    original = batch._query

    def query(*args):
        result = original(*args)
        (tmp_path / 'lean-toolchain').write_text('leanprover/lean4:v4.33.0\n')
        return result

    monkeypatch.setattr(batch, '_query', query)
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) != 0
    result = json.loads(capsys.readouterr().out)
    assert result['freshness'] == 'unstable-source'
    assert 'toolchain_identity' in result['identityChanges']
    assert result['queries'] == []


def test_index_replacement_without_source_change_is_detected(tmp_path, monkeypatch, capsys):
    import sqlite3

    from ladon import proof_search_batch as batch
    from ladon.proof_search_index import default_proof_search_index_path

    path = fixture(tmp_path)
    original = batch._query
    replaced = []

    def query(*args):
        result = original(*args)
        if not replaced:
            index = default_proof_search_index_path(tmp_path)
            replacement = tmp_path / 'replacement.sqlite'
            with sqlite3.connect(index) as source, sqlite3.connect(replacement) as target:
                source.backup(target)
                target.execute("UPDATE metadata SET value='replacement' WHERE key='generationIdentity'")
            replacement.replace(index)
            replaced.append(True)
        return result

    monkeypatch.setattr(batch, '_query', query)
    assert main(['proof-search', 'search', 'batch', '--repo-root', str(tmp_path),
                 '--queries', str(path), '--format', 'json']) != 0
    result = json.loads(capsys.readouterr().out)
    assert result['freshness'] == 'index-generation-changed'
    assert result['activeGenerationAtEnd'] == 'replacement'
    assert result['queries'] == []


def test_stored_batch_uses_recorded_owner_without_source_capture(tmp_path, monkeypatch):
    from ladon import proof_search_batch as batch
    from ladon.proof_search_index import default_proof_search_index_path

    fixture(tmp_path)
    (tmp_path / 'Main.lean').write_text('theorem changed : Nat := 2\n')
    from ladon import proof_search_index as index
    monkeypatch.setattr(index, 'capture_repository_snapshot', lambda *_: pytest.fail('source capture'))
    result = batch.run_prepared_batch(None, batch._requests([['name', '--text', 'first']]),
        index_path=default_proof_search_index_path(tmp_path), freshness='stored')
    assert result['freshness'] == 'stored'
    assert result['validation']['captureCount'] == 0
    assert result['validation']['authority'] == 'stored-index-generation'
    assert result['origin'] == str(tmp_path.resolve())
    assert result['queries'][0]['freshnessStatus'] == 'unchecked'
    assert result['queries'][0]['generationIdentity'] == result['generationIdentity']


def test_stored_batch_pins_generation_across_replacement(tmp_path, monkeypatch):
    import sqlite3

    from ladon import proof_search_batch as batch
    from ladon.proof_search_index import default_proof_search_index_path

    fixture(tmp_path)
    index_path = default_proof_search_index_path(tmp_path)
    replacement = tmp_path / 'replacement.sqlite'
    with sqlite3.connect(index_path) as source, sqlite3.connect(replacement) as target:
        source.backup(target)
        target.execute("UPDATE metadata SET value='replacement' WHERE key='generationIdentity'")
        target.execute("UPDATE declarations SET type_text='ReplacementOnly'")
    original = batch._query

    def replace_after_query(connection, args):
        result = original(connection, args)
        if replacement.exists():
            replacement.replace(index_path)
        return result

    monkeypatch.setattr(batch, '_query', replace_after_query)
    queries = [['name', '--text', 'first'], ['type-text', '--fragment', 'ReplacementOnly']]
    result = batch.run_search_batch(None, queries, index_path=index_path, freshness='stored')
    assert result['generationIdentity'] != 'replacement'
    assert result['queries'][1]['results'] == []
    assert all(q['generationIdentity'] == result['generationIdentity'] for q in result['queries'])
    assert result['status'] == 'available'


def test_detached_cli_respects_explicit_owner_assertion(tmp_path, monkeypatch, capsys):
    import shutil

    owner = tmp_path / 'archive'
    owner.mkdir()
    queries = fixture(owner)
    queries = queries.rename(tmp_path / 'queries.json')
    detached = (owner / '.ladon/index/proof-search.sqlite').rename(tmp_path / 'detached.sqlite')
    shutil.rmtree(owner)
    monkeypatch.chdir(tmp_path)
    argv = ['proof-search', 'search', 'batch', '--freshness', 'stored', '--format', 'json',
            '--index', str(detached), '--queries', str(queries)]
    assert main(argv) == 0
    assert json.loads(capsys.readouterr().out)['origin'] == str(owner)
    assert main(argv + ['--repo-root', '.']) != 0
    assert 'another repository' in capsys.readouterr().err


def test_normalized_fragment_batch_uses_versioned_child_and_parent(tmp_path):
    from ladon import proof_search_batch as batch
    from ladon.proof_search_index import default_proof_search_index_path

    fixture(tmp_path)
    result = batch.run_prepared_batch(None,
        batch._requests([['type-text', '--fragment', 'Nat']]),
        index_path=default_proof_search_index_path(tmp_path), freshness='stored')
    assert result['schema'] == 'ladon-proof-search-batch-v2'
    assert result['freshnessStatus'] == 'unchecked'
    assert result['queries'][0]['schema'] == 'ladon-proof-search-type-fragment-result-v1'
    assert result['queries'][0]['generationIdentity'] == result['generationIdentity']
