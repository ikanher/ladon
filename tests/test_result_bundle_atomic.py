"""Cancellation and failed publication preserve existing local artifacts."""
import io
import zipfile

import pytest
from test_result_bundles import MANIFEST, _selection

from ladon.result_bundle_archive import extract_bundle_archive
from ladon.result_bundles import export_result_bundle


def test_interrupted_archive_write_preserves_previous_output(tmp_path, monkeypatch):
    import ladon.result_bundle_archive as owner
    selection = _selection(tmp_path / 'selection.json')
    output = tmp_path / 'previous.zip'
    output.write_bytes(b'keep previous bytes')
    before = set(tmp_path.iterdir())
    original = owner._write_member

    def interrupt_after_member(*args, **kwargs):
        original(*args, **kwargs)
        raise KeyboardInterrupt

    monkeypatch.setattr(owner, '_write_member', interrupt_after_member)
    with pytest.raises(KeyboardInterrupt):
        export_result_bundle(MANIFEST, selection, output)
    assert output.read_bytes() == b'keep previous bytes'
    assert set(tmp_path.iterdir()) == before


class _Unseekable(io.BytesIO):
    def seek(self, *args):
        raise OSError('nonseekable output')


def test_regular_streamed_zip_data_descriptor_is_supported(tmp_path):
    buffer = _Unseekable()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('record', b'payload')
    path = tmp_path / 'streamed.zip'
    path.write_bytes(buffer.getvalue())
    destination = tmp_path / 'stage'
    destination.mkdir()
    extract_bundle_archive(path, destination, max_bytes=10000, max_members=10)
    assert (destination / 'record').read_bytes() == b'payload'
