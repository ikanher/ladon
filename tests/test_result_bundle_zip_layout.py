"""Integrity includes the physical archive layout, not only its directory."""
import io
import zipfile

import pytest
from test_result_bundles import _export

from ladon.result_bundles import verify_result_bundle
from ladon.result_manifest_io import ResultManifestError


def _orphan():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('hidden-secret.bin', b'UNLISTED-SECRET-PAYLOAD')
    return buffer.getvalue().split(b'PK\x01\x02')[0]


@pytest.mark.parametrize('placement', ['suffix', 'prefix'])
def test_unindexed_local_members_are_rejected_before_extraction_publication(tmp_path, placement):
    bundle = _export(tmp_path)
    original = bundle.read_bytes()
    raw = original + _orphan() if placement == 'suffix' else _orphan() + original
    bundle.write_bytes(raw)
    destination = tmp_path / 'unpublished'
    with pytest.raises(ResultManifestError):
        verify_result_bundle(bundle, extract_to=destination)
    assert not destination.exists()
