"""Public inspection boundaries beyond the independent initial red suite."""
from __future__ import annotations

import copy
import json
import socket
import subprocess

import pytest
from test_result_assessments import assessment, companion, manifest

from ladon.entrypoint import main
from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import ResultManifestError, canonical_json, content_revision


def test_companion_schema_parity():
    from importlib.resources import files

    import jsonschema

    from ladon.result_assessments import validate_result_assessments

    schema = json.loads(files('ladon.schemas').joinpath('ladon-result-assessments-v1.schema.json').read_text())
    value = manifest()
    data = companion(value, [assessment(value['claims'][0], 'unrestricted-domain', kind='conventional-only')])
    jsonschema.Draft202012Validator(schema).validate(data)
    assert validate_result_assessments(data, value) == data
    for mutation in [lambda d: d.update(schema='ladon-result-assessments-v9'),
                     lambda d: d['assessments'][0].update(scope='x' * 65537),
                     lambda d: d['assessments'][0]['author'].update(kind='authenticated-human')]:
        invalid = copy.deepcopy(data)
        mutation(invalid)
        assert not jsonschema.Draft202012Validator(schema).is_valid(invalid)
        with pytest.raises(ResultManifestError):
            validate_result_assessments(invalid, value)


def test_attributed_differences_survive_next_to_exact_component():
    value = manifest()
    row = assessment(value['claims'][0], 'implication', targets=['finite-map'],
                     kind='reported-implication-without-checked-adapter')
    row['author']['kind'] = 'model'
    row['differences'] = ['Formal bound is strict; article includes equality.', 'Transcript scope excludes average-only claim.']
    result = inspect_result_manifest(value, [], assessments=companion(value, [row]))
    card = result['rows'][0]
    assert card['assessments'][0]['differences'] == row['differences']
    assert card['assessments'][0]['author']['kind'] == 'model'
    assert card['assessments'][0]['currency'] == 'current'
    assert result['coverage']['proofCoverage'] == 'unknown'


@pytest.mark.parametrize('limit', [0, 101, True, 1.5])
def test_limits_reject_invalid_page_requests(limit):
    with pytest.raises(ResultManifestError):
        inspect_result_manifest(manifest(), [], limit=limit)


def test_cursor_binds_companion_and_target_selection():
    value = manifest()
    page = inspect_result_manifest(value, [], limit=1)
    cursor = page['pagination']['nextCursor']
    for kwargs in ({'assessments': companion(value, [])}, {'target_id': 'finite-map'}, {'limit': 2}):
        with pytest.raises(ResultManifestError):
            inspect_result_manifest(value, [], **{'limit': 1, 'cursor': cursor, **kwargs})
    with pytest.raises(ResultManifestError):
        inspect_result_manifest(value, [], limit=1, cursor=cursor[:-1] + ('0' if cursor[-1] != '0' else '1'))


def test_large_unicode_cli_page_is_offline_and_json_text_equivalent(tmp_path, monkeypatch, capsys):
    value = manifest()
    value['claims'][0]['statement'] = 'λ' * 32768
    value['claims'][0]['revision'] = content_revision('claim', value['claims'][0])
    value['revision'] = content_revision('manifest', value)
    path = tmp_path / 'manifest.json'
    path.write_bytes(canonical_json(value))
    def forbidden(*_args, **_kwargs):
        raise AssertionError('offline inspect attempted external activity')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    outputs = []
    for fmt in ('json', 'text'):
        assert main(['result', 'inspect', str(path), '--format', fmt]) == 0
        captured = capsys.readouterr()
        assert captured.err == ''
        assert len(captured.out.encode()) <= 32768
        outputs.append(captured.out)
    decoded = {k: json.loads(v) for k, v in (line.split(': ', 1) for line in outputs[1].splitlines())}
    assert decoded == json.loads(outputs[0])
    assert '/claims/0/statement' in outputs[0]


def test_inspection_errors_use_existing_stderr_contract(tmp_path, capsys):
    assert main(['result', 'inspect', str(tmp_path / 'missing')]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)['operation'] == 'inspect'
    assert main(['result', 'inspect', str(tmp_path / 'missing'), '--limit', 'oops']) == 2
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)['operation'] == 'inspect'


def test_every_component_reachable_without_repeating_rows():
    value = manifest()
    value['claims'][0]['components'] = [f'part-{i}' for i in range(150)]
    value['claims'][0]['revision'] = content_revision('claim', value['claims'][0])
    value['links'] = []
    value['reviews'] = []
    value['revision'] = content_revision('manifest', value)
    cursor = None
    seen = []
    while True:
        page = inspect_result_manifest(value, [], limit=100, cursor=cursor)
        assert len(canonical_json(page)) + 1 <= 32768
        assert page['pagination']['total'] == 150
        seen.extend(row['componentId'] for row in page['rows'])
        cursor = page['pagination']['nextCursor']
        if cursor is None:
            break
    assert seen == value['claims'][0]['components']
