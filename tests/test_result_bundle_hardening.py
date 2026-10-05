"""Adversarial transport lengths, history, authority and snapshot regressions."""
from __future__ import annotations

import json
import struct
import zipfile

import pytest
from test_result_bundle_views import _fixture, _view, _write
from test_result_bundles import MANIFEST, _export, _index, _selection

from ladon.result_bundle_archive import extract_bundle_archive
from ladon.result_bundles import export_result_bundle, verify_result_bundle
from ladon.result_manifest_io import ResultManifestError, content_revision


@pytest.mark.parametrize('compression', [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_archive_cannot_hide_expansion_behind_a_false_zero_length(tmp_path, compression):
    path = tmp_path / 'bad.zip'
    with zipfile.ZipFile(path, 'w', compression=compression) as archive:
        archive.writestr('hidden', b'x' * 50000)
    raw = bytearray(path.read_bytes())
    local = raw.index(b'PK\x03\x04')
    central = raw.index(b'PK\x01\x02')
    for offset in (local + 14, local + 22, central + 16, central + 24):
        struct.pack_into('<I', raw, offset, 0)
    path.write_bytes(raw)
    stage = tmp_path / 'stage'
    stage.mkdir()
    with pytest.raises(ResultManifestError):
        extract_bundle_archive(path, stage, max_bytes=100000, max_members=10)


def test_archive_rejects_aliasing_directory_components(tmp_path):
    path = tmp_path / 'case.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('A/one', b'one')
        archive.writestr('a/two', b'two')
    stage = tmp_path / 'stage'
    stage.mkdir()
    with pytest.raises(ResultManifestError):
        extract_bundle_archive(path, stage, max_bytes=10000, max_members=10)


def test_bundled_predecessor_and_historical_review_keep_their_exact_bytes(tmp_path, capsys):
    old = json.loads(MANIFEST.read_text())
    current = json.loads(MANIFEST.read_text())
    current['previousRevision'] = old['revision']
    claim = current['claims'][0]
    claim['statement'] += ' Revised statement.'
    claim['revision'] = content_revision('claim', claim)
    current['revision'] = content_revision('manifest', current)
    manifest = _write(tmp_path / 'new.json', current)
    selected = _selection(tmp_path / 'selection.json', entries=[{
        'id': 'previous', 'role': 'predecessor', 'path': str(MANIFEST),
        'disclosure': 'supplied', 'permission': 'include'}])
    bundle = tmp_path / 'result.zip'
    export_result_bundle(manifest, selected, bundle)
    verified = verify_result_bundle(bundle)
    assert verified['missingPredecessors']['count'] == 0
    index = _index(bundle)
    row = next(r for r in index['inventory'] if r['role'] == 'predecessor')
    with zipfile.ZipFile(bundle) as archive:
        assert archive.read(row['path']) == MANIFEST.read_bytes()
    result = _view(capsys, 'inspect', bundle, '--section', 'reviews')
    assert result['rows'][0]['currency'] == 'historical'


def test_missing_previous_revision_and_external_replay_dependencies_are_explicit(tmp_path):
    manifest = json.loads(MANIFEST.read_text())
    previous = 'sha256:' + 'a' * 64
    manifest['previousRevision'] = previous
    manifest['revision'] = content_revision('manifest', manifest)
    path = _write(tmp_path / 'new.json', manifest)
    selection_path = _selection(tmp_path / 'selection.json', entries=[])
    selection = json.loads(selection_path.read_text())
    selection['identifiers'] = [{'scheme': 'doi', 'value': '10.example/producer-supplied'}]
    selection['externalDependencies'] = [{'id': 'lean', 'kind': 'replay-environment',
                                           'reason': 'not bundled', 'locator': 'https://example.invalid/lean'}]
    _write(selection_path, selection)
    bundle = tmp_path / 'result.zip'
    export_result_bundle(path, selection_path, bundle)
    result = verify_result_bundle(bundle)
    assert result['missingPredecessors']['rows'] == [previous]
    assert result['externalDependencies']['rows'] == selection['externalDependencies']
    assert result['identifiers']['rows'] == selection['identifiers']
    assert result['replay'] == 'not-run'


def test_changed_bundle_attachment_invalidates_an_existing_cursor(tmp_path, capsys):
    manifest, selection_path, _, _ = _fixture(tmp_path)
    selected = json.loads(selection_path.read_text())
    attachment = tmp_path / 'note.txt'
    attachment.write_text('first')
    selected['entries'].append({'id': 'note', 'role': 'attachment', 'path': str(attachment),
                                'disclosure': 'supplied', 'permission': 'include'})
    _write(selection_path, selected)
    bundle = tmp_path / 'result.zip'
    export_result_bundle(manifest, selection_path, bundle)
    first = _view(capsys, 'guide', bundle, '--section', 'assumptions', '--limit', '1')
    attachment.write_text('second')
    export_result_bundle(manifest, selection_path, bundle)
    from ladon.entrypoint import main
    assert main(['result', 'guide', str(bundle), '--section', 'assumptions', '--limit', '1',
                 '--cursor', first['pagination']['nextCursor']]) == 2
    assert 'cursor' in capsys.readouterr().err


def test_failure_before_extraction_publication_preserves_existing_directory(tmp_path):
    bundle = _export(tmp_path)
    destination = tmp_path / 'existing'
    destination.mkdir()
    (destination / 'old').write_text('preserve')
    with pytest.raises(ResultManifestError):
        verify_result_bundle(bundle, extract_to=destination)
    assert (destination / 'old').read_text() == 'preserve'


def test_bundle_with_extra_file_is_rejected_even_for_unused_attachment(tmp_path):
    bundle = _export(tmp_path)
    with zipfile.ZipFile(bundle, 'a') as archive:
        archive.writestr('unlisted', b'private payload')
    destination = tmp_path / 'unpublished'
    with pytest.raises(ResultManifestError):
        verify_result_bundle(bundle, extract_to=destination)
    assert not destination.exists()
