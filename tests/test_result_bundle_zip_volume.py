"""Split-volume metadata cannot masquerade as a self-contained archive."""
import struct

import pytest
from test_result_bundles import _export

from ladon.result_bundles import verify_result_bundle
from ladon.result_manifest_io import ResultManifestError


def test_nonzero_member_volume_is_rejected(tmp_path):
    bundle = _export(tmp_path)
    raw = bytearray(bundle.read_bytes())
    offset = raw.index(b'PK\x01\x02')
    struct.pack_into('<H', raw, offset + 34, 1)
    bundle.write_bytes(raw)
    with pytest.raises(ResultManifestError):
        verify_result_bundle(bundle)
