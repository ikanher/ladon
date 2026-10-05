"""Portable views preserve authority and continuations across bundle moves."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from test_result_lineage import _lineage_fixture

from ladon.entrypoint import main
from ladon.result_manifest_io import ResultManifestError


def _write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')
    return path


def _fixture(tmp_path):
    manifest, artifacts, lineage, database, _ = _lineage_fixture(tmp_path)
    entries = []
    for index, artifact in enumerate(artifacts):
        path = _write(tmp_path / f'artifact-{index}.json', artifact)
        entries.append(_entry(f'canonical-{index}', 'artifact', path))
    manifest_path = _write(tmp_path / 'manifest.json', manifest)
    entries.extend([_entry('lineage-input', 'lineage', _write(tmp_path / 'lineage.json', lineage)),
                    _entry('lineage-store', 'lineage-database', database)])
    selection = {'schema': 'ladon-result-bundle-selection-v1',
                 'supplier': {'identity': 'test-supplier', 'kind': 'tool'},
                 'entries': entries,
                 'lineageBindings': [{'entryId': lineage['entries'][0]['id'],
                                      'databaseId': 'lineage-store'}],
                 'identifiers': [], 'externalDependencies': []}
    return manifest_path, _write(tmp_path / 'selection.json', selection), manifest, lineage


def _entry(identifier, role, path):
    return {'id': identifier, 'role': role, 'path': str(path),
            'disclosure': 'supplied', 'permission': 'include'}


def _view(capsys, operation, bundle, *options):
    code = main(['result', operation, str(bundle), *options])
    output = capsys.readouterr()
    assert code == 0, output.err
    return json.loads(output.out)


def test_bundle_views_detach_lineage_and_preserve_cursor_across_relocation(tmp_path, capsys):
    from ladon.result_bundles import export_result_bundle
    origin = tmp_path / 'origin'
    origin.mkdir()
    manifest, selection, original, _ = _fixture(origin)
    bundle = tmp_path / 'result.zip'
    export_result_bundle(manifest, selection, bundle)
    shutil.rmtree(origin)
    first = _view(capsys, 'inspect', bundle, '--section', 'assumptions', '--limit', '1')
    cursor = first['pagination']['nextCursor']
    assert cursor
    moved = tmp_path / 'moved.zip'
    bundle.rename(moved)
    second = _view(capsys, 'inspect', moved, '--section', 'assumptions', '--limit', '1', '--cursor', cursor)
    assert second['inputBinding'] == first['inputBinding']
    assert second['rows'] != first['rows']
    lineage = _view(capsys, 'guide', moved, '--section', 'lineage')
    assert lineage['revision'] == original['revision']
    assert lineage['rows'][0]['status'] == 'available'
    assert lineage['rows'][0]['environmentBinding'] == 'not-established'
    reference = lineage['rows'][0]['references']['/ownerSummary']
    assert reference['database'].startswith('bundle:')
    assert str(origin) not in reference['database']


def test_unbound_lineage_never_opens_the_original_database(tmp_path, capsys):
    from ladon.result_bundles import export_result_bundle
    manifest, selection_path, _, _ = _fixture(tmp_path)
    selection = json.loads(selection_path.read_text())
    selection['lineageBindings'] = []
    selection['entries'] = [e for e in selection['entries'] if e['role'] != 'lineage-database']
    _write(selection_path, selection)
    bundle = tmp_path / 'result.zip'
    export_result_bundle(manifest, selection_path, bundle)
    result = _view(capsys, 'inspect', bundle, '--section', 'lineage')
    assert result['rows'][0]['status'] == 'unavailable'
    assert result['rows'][0]['reason'] == 'database-unavailable'


def test_lineage_binding_cannot_substitute_a_different_store(tmp_path):
    from ladon.result_bundles import export_result_bundle
    manifest, selection_path, _, _ = _fixture(tmp_path)
    selection = json.loads(selection_path.read_text())
    replacement = tmp_path / 'replacement.sqlite3'
    replacement.write_bytes(b'not the selected database')
    next(e for e in selection['entries'] if e['role'] == 'lineage-database')['path'] = str(replacement)
    _write(selection_path, selection)
    with pytest.raises(ResultManifestError):
        export_result_bundle(manifest, selection_path, tmp_path / 'result.zip')


def test_bundle_external_view_flags_are_rejected(tmp_path, capsys):
    from ladon.result_bundles import export_result_bundle
    manifest, selection, _, _ = _fixture(tmp_path)
    bundle = tmp_path / 'result.zip'
    export_result_bundle(manifest, selection, bundle)
    code = main(['result', 'inspect', str(bundle), '--artifact', str(manifest)])
    output = capsys.readouterr()
    assert code == 2
    assert not output.out
    assert json.loads(output.err)['exitClass'] == 'invocation'


def test_existing_store_with_pending_wal_is_not_silently_copied(tmp_path):
    from ladon.result_bundles import export_result_bundle
    manifest, selection, _, lineage = _fixture(tmp_path)
    database = tmp_path / lineage['entries'][0]['database']
    Path(str(database) + '-wal').write_bytes(b'pending journal contents')
    with pytest.raises(ResultManifestError):
        export_result_bundle(manifest, selection, tmp_path / 'result.zip')
