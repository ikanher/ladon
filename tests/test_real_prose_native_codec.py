"""Native transport preserves exact observations without relaxing canonical bounds."""

import importlib
import json

import pytest

from ladon.proofir_v3 import canonical_bytes


def codec():
    return importlib.import_module('ladon.real_prose_native_codec')


def test_deep_timing_history_roundtrips_inside_existing_native_limits():
    value = {'elapsed': 1.25, 'unicode': 'λ'}
    for _ in range(100):
        value = {'body': value}
    encoded = codec().encode_history(value)
    canonical_bytes(encoded)
    assert codec().decode_history(encoded) == value
    assert len(encoded['chunks']) >= 1


@pytest.mark.parametrize('change', ['digest', 'truncated', 'extra', 'oversized', 'duplicate'])
def test_closed_transport_rejects_changed_or_ambiguous_history(change):
    encoded = codec().encode_history({'value': 'x' * 100_000})
    if change == 'digest':
        encoded['digest'] = 'sha256:' + '0' * 64
    elif change == 'truncated':
        encoded['chunks'].pop()
    elif change == 'extra':
        encoded['authority'] = 'checked'
    elif change == 'oversized':
        encoded['chunks'] = ['x' * (codec().CHUNK_BYTES + 1)]
    else:
        raw = '{"x":1,"x":2}'
        import hashlib
        encoded['chunks'] = [raw]
        encoded['byteLength'] = len(raw)
        encoded['digest'] = 'sha256:' + hashlib.sha256(raw.encode()).hexdigest()
    with pytest.raises(ValueError):
        codec().decode_history(encoded)


def test_codec_has_one_canonical_serialization():
    encoded = codec().encode_history({'a': 1})
    raw = json.dumps({'a': 1}, indent=2)
    import hashlib
    encoded['chunks'] = [raw]
    encoded['byteLength'] = len(raw)
    encoded['digest'] = 'sha256:' + hashlib.sha256(raw.encode()).hexdigest()
    with pytest.raises(ValueError):
        codec().decode_history(encoded)
