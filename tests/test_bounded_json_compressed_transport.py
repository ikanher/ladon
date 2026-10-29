"""Bounded compressed fallback for oversized connection DAGs."""

import base64
import hashlib
import json
import random
import zlib

import pytest

from ladon import bounded_json_transport as api


def _compressed(inner):
    return api._COMPRESSED_MAGIC + base64.b64encode(zlib.compress(inner))


def test_fallback_preserves_v1_wire_for_small_objects():
    value = {'opaque': '{"looks": "like json"}', 'x': [True, 7]}
    wire = api.pack_json_with_compression_fallback(value)
    assert wire == api.pack_json(value)
    assert api.unpack_json_with_compression_fallback(wire) == value


def test_oversized_canonical_dag_roundtrips_through_ascii_compressed_envelope():
    rng = random.Random(4412)
    value = {'opaqueHistory': [rng.randbytes(250_000).hex() for _ in range(18)]}
    with pytest.raises(ValueError, match='wire exceeds byte limit'):
        api.pack_json(value)
    wire = api.pack_json_with_compression_fallback(value)
    assert wire.startswith(api._COMPRESSED_MAGIC)
    assert len(wire) <= api.TransportLimits().max_wire_bytes
    assert wire.isascii()
    assert api.unpack_json_with_compression_fallback(wire) == value


@pytest.mark.parametrize('wire', [
    api._COMPRESSED_MAGIC,
    api._COMPRESSED_MAGIC + b'not-base64!',
    api._COMPRESSED_MAGIC + base64.b64encode(zlib.compress(b'{}'))[:-4],
    _compressed(b'{}') + b'AAAA',
    api._COMPRESSED_MAGIC + base64.b64encode(zlib.compress(b'{}') + zlib.compress(b'{}')),
])
def test_malformed_incomplete_and_concatenated_streams_are_rejected(wire):
    with pytest.raises(ValueError):
        api.unpack_compressed_json(wire)


def test_compressed_wire_limit_is_enforced_before_decode():
    limits = api.TransportLimits(max_wire_bytes=128)
    with pytest.raises(ValueError, match='wire exceeds byte limit'):
        api.unpack_compressed_json(api._COMPRESSED_MAGIC + b'A'*256, limits=limits)


def test_decompression_bomb_is_bounded_before_json_parse():
    bomb = api._COMPRESSED_MAGIC + base64.b64encode(zlib.compress(b'x'*(40*1024**2+1)))
    with pytest.raises(ValueError, match='expansion'):
        api.unpack_compressed_json(bomb)


def test_inner_digest_is_still_checked_after_decompression():
    value = {'x': True}
    wire = api.pack_json(value)
    header = json.loads(wire)
    header['digest'] = 'sha256:' + '0'*64
    altered = json.dumps(header, sort_keys=True, separators=(',', ':')).encode('ascii')
    with pytest.raises(ValueError, match='digest mismatch'):
        api.unpack_compressed_json(_compressed(altered))


def test_fallback_only_compresses_wire_size_failures():
    with pytest.raises(TypeError, match='root must be an object'):
        api.pack_json_with_compression_fallback([])


def test_large_payload_envelope_has_no_non_ascii_transport_bytes():
    value = {'blob': hashlib.sha256(b'preserve opaque payload').hexdigest()}
    assert api.pack_compressed_json(value).isascii()
