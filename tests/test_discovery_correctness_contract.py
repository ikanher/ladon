"""Regression contracts for attributable structural explanation and lexical search."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pytest
from test_authority_safe_discovery_regressions import _declaration_database

from ladon.proof_search_explain import dispatch_explain
from ladon.proof_search_type import TypeSearchRequest


def _args(**overrides):
    values = {'goal': 'True', 'candidate': 'Demo.proof', 'module': 'Demo', 'assumption': [],
              'suggestion_cap': 10, 'freshness': 'stored', 'raw_signature': False}
    return argparse.Namespace(**(values | overrides))


@pytest.mark.parametrize('text', [None, '', '   '])
def test_missing_rendered_type_is_unavailable(tmp_path: Path, text: str | None) -> None:
    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute('UPDATE declarations SET type_text=?', (text,))
    result = dispatch_explain(_args(), tmp_path, path)
    assert result['status'] == 'unavailable'
    assert 'empty' in result['reason'] or 'missing' in result['reason']
    assert 'unless' not in ' '.join(result['nonclaims'])


def test_exact_owner_disambiguates_candidate_and_retains_all_type_evidence(tmp_path: Path) -> None:
    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT INTO declarations SELECT 'other',name,candidate_name,type_text,"
                           "type_text_bytes,type_text_truncated,type_status,authority,'Other',"
                           "'Other.lean',2,namespace,package,rendered_type,conclusion_text FROM declarations")
    result = dispatch_explain(_args(), tmp_path, path)
    assert result['status'] == 'available'
    evidence = result['candidateEvidence']
    assert evidence['module'] == 'Demo'
    assert evidence['package'] == 'project'
    assert evidence['typeTextBytes'] == 4
    assert evidence['typeTextTruncated'] is False
    assert evidence['path'] == 'Demo.lean'
    assert result['routeCard']['accepted'] is False
    assert any('check' in claim for claim in result['nonclaims'])


def test_stored_candidate_carries_generation_without_live_verification(tmp_path: Path) -> None:
    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
        connection.executemany('INSERT INTO metadata VALUES(?,?)', [
            ('generationIdentity', 'stored-generation'), ('helperIdentity', 'stored-helper'),
            ('indexSchema', 'test-schema'), ('sourceFingerprint', 'stored-source'),
        ])
    result = dispatch_explain(_args(), tmp_path, path)
    evidence = result['candidateEvidence']['generationEvidence']
    assert evidence['freshness'] == 'stored'
    assert evidence['generationIdentity'] == 'stored-generation'
    assert evidence['helperIdentity'] == 'stored-helper'
    assert 'currentGenerationIdentity' not in evidence


@pytest.mark.parametrize('diagnostic_cap', [-1, 1001])
def test_api_diagnostic_cap_is_bounded(diagnostic_cap: int) -> None:
    with pytest.raises(ValueError, match='diagnostic'):
        TypeSearchRequest('True', diagnostic_limit=diagnostic_cap)


def test_field_contributions_use_the_same_case_rules_as_sqlite(tmp_path: Path) -> None:
    from ladon.proof_search_type import query_type_shortlist

    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE declarations SET rendered_type='ss',type_text='ß',conclusion_text='SS'")
        result = query_type_shortlist(connection, TypeSearchRequest('ss'))
    assert result['results'][0]['fieldContributions'] == {
        'renderedType': True, 'conclusionText': True, 'typeText': False,
    }


def test_type_text_result_has_explicit_lexical_schema_and_zero_diagnostic_cap(tmp_path: Path, capsys) -> None:
    from ladon.cli import main
    from ladon.proof_search_index import build_proof_search_index

    (tmp_path / 'Main.lean').write_text('theorem exampleFact : True := True.intro\n')
    build_proof_search_index(tmp_path)
    status = main(['proof-search', 'search', 'type-text', '--repo-root', str(tmp_path),
                   '--pattern', 'True', '--diagnostic-limit', '0', '--format', 'json'])
    output = capsys.readouterr()
    assert status == 0, output.err
    result = json.loads(output.out)
    assert result['schema'] == 'ladon-proof-search-type-text-result-v2'
    assert result['operation'] == 'search-type-text'
    assert result['schemaVersion'] == 2
    assert result['coverage']['diagnosticCap'] == 0


def test_packaged_schema_rejects_promoted_authority_and_unbounded_caps(tmp_path: Path) -> None:
    from copy import deepcopy
    from importlib.resources import files

    import jsonschema

    from ladon.proof_search_type import query_type_shortlist

    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection:
        result = query_type_shortlist(connection, TypeSearchRequest('True'))
    schema = json.loads(files('ladon').joinpath('schemas/ladon-proof-search-type-text-result-v2.schema.json').read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(result, schema)
    promoted = deepcopy(result)
    promoted['results'][0]['authority'] = 'lean_verified'
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(promoted, schema)
    unbounded = deepcopy(result)
    unbounded['coverage']['diagnosticCap'] = -1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(unbounded, schema)


def test_type_text_freshness_callback_cannot_promote_candidate_authority(tmp_path: Path) -> None:
    from ladon.proof_search_type import query_type_shortlist

    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection, pytest.raises(ValueError, match='candidate verification'):
        query_type_shortlist(
            connection, TypeSearchRequest('True', freshness='verify'),
            verifier=lambda _candidates, _pattern: {
                'Demo.proof': {'authority': 'lean_verified', 'verification': 'accepted'},
            },
        )


@pytest.mark.parametrize('selection', ['namespace-filter', 'namespace-root', 'multiple-roots'])
def test_namespace_population_is_literal_and_uses_every_root(tmp_path: Path, selection: str) -> None:
    from ladon.proof_search_type import query_type_shortlist

    path = tmp_path / 'index.sqlite'
    _declaration_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE declarations SET namespace='A_B',candidate_name='A_B.proof'")
        for name in ('AxB.Child', 'A_B.Child', 'Second'):
            connection.execute(
                "INSERT INTO declarations SELECT ?,name,?,type_text,type_text_bytes,"
                "type_text_truncated,type_status,authority,module,path,line,?,package,"
                "rendered_type,conclusion_text FROM declarations LIMIT 1",
                (name, name + '.proof', name),
            )
        options = {
            'namespace-filter': {'namespace': 'A_B'},
            'namespace-root': {'scope': 'namespace', 'roots': ('A_B',)},
            'multiple-roots': {'scope': 'namespace', 'roots': ('A_B', 'Second')},
        }[selection]
        result = query_type_shortlist(connection, TypeSearchRequest('True', **options))
    expected = {'A_B.proof', 'A_B.Child.proof'}
    if selection == 'multiple-roots':
        expected.add('Second.proof')
    assert {row['candidateName'] for row in result['results']} == expected


def test_name_search_namespace_with_underscore_remains_literal(tmp_path: Path, capsys) -> None:
    from ladon.cli import main
    from ladon.proof_search_index import build_proof_search_index

    (tmp_path / 'Main.lean').write_text(
        'namespace A_B\ntheorem proof : True := True.intro\nend A_B\n'
        'namespace A_B.Child\ntheorem proof : True := True.intro\nend A_B.Child\n'
        'namespace AxB.Child\ntheorem proof : True := True.intro\nend AxB.Child\n',
    )
    build_proof_search_index(tmp_path)
    status = main(['proof-search', 'search', 'name', '--repo-root', str(tmp_path),
                   '--text', 'proof', '--scope', 'namespace', '--root', 'A_B', '--format', 'json'])
    output = capsys.readouterr()
    assert status == 0, output.err
    assert {row['candidateName'] for row in json.loads(output.out)['results']} == {'A_B.proof', 'A_B.Child.proof'}
