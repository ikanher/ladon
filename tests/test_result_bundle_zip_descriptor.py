"""Descriptor extent disambiguates a CRC equal to the optional signature."""
import struct
import zipfile

from test_result_bundle_atomic import _Unseekable

from ladon.result_bundle_archive import extract_bundle_archive


def test_unsigned_descriptor_crc_can_equal_signature(tmp_path):
    payload = bytes.fromhex('ac0a7ad5')
    buffer = _Unseekable()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('item', payload)
    raw = bytearray(buffer.getvalue())
    descriptor = raw.index(b'PK\x07\x08')
    assert raw[descriptor:descriptor + 8] == b'PK\x07\x08PK\x07\x08'
    del raw[descriptor:descriptor + 4]
    end = raw.index(b'PK\x05\x06')
    central = struct.unpack_from('<I', raw, end + 16)[0]
    struct.pack_into('<I', raw, end + 16, central - 4)
    path = tmp_path / 'legal.zip'
    path.write_bytes(raw)
    with zipfile.ZipFile(path) as archive:
        assert archive.read('item') == payload
    destination = tmp_path / 'stage'
    destination.mkdir()
    extract_bundle_archive(path, destination, max_bytes=10000, max_members=10)
    assert (destination / 'item').read_bytes() == payload
