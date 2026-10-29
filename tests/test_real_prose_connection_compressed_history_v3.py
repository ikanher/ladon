"""Compressed output histories validate retained wire, not a local recompression."""

import hashlib

import pytest

from ladon import bounded_json_transport as transport
from ladon.real_prose_connection_history import _supervision


def _check(wire, result):
    chunks = [wire[offset:offset + 256 * 1024].decode('ascii')
              for offset in range(0, len(wire), 256 * 1024)]
    return {
        'bounds': {
            'timeout_seconds': 600,
            'max_rss_bytes': 12 * 1024**3,
            'max_output_bytes': 8 * 1024**2,
            'deadlineMonotonic': 1.0,
        },
        'workerInputDigest': 'sha256:' + '1' * 64,
        'implementationDigest': 'sha256:' + '2' * 64,
        'processReceipt': {
            'command': ['python', '-m', 'ladon.real_prose_connection_worker'],
            'peak_rss_bytes': 1024,
            'elapsed_seconds': 1.0,
            'stdoutDigest': 'sha256:' + hashlib.sha256(wire).hexdigest(),
        },
        'result': result,
        'stdoutWireChunks': chunks,
    }


def test_compressed_history_validates_exact_retained_wire_without_recompressing(monkeypatch):
    result = {'status': 'unresolved', 'detail': 'compressed result'}
    body = {'status': 'completed', 'result': result, 'diagnostic': None}
    wire = transport.pack_compressed_json(body)
    check = _check(wire, result)

    def forbidden_recompression(*_args, **_kwargs):
        raise AssertionError('saved wire must be validated without recompression')

    monkeypatch.setattr(transport, 'pack_compressed_json', forbidden_recompression)
    _supervision(check, compressed_wire=True)


def test_compressed_history_rejects_a_changed_retained_wire_chunk():
    result = {'status': 'unresolved', 'detail': 'compressed result'}
    body = {'status': 'completed', 'result': result, 'diagnostic': None}
    wire = transport.pack_compressed_json(body)
    check = _check(wire, result)
    check['stdoutWireChunks'][0] = 'X' + check['stdoutWireChunks'][0][1:]
    with pytest.raises(ValueError, match='output digest'):
        _supervision(check, compressed_wire=True)
