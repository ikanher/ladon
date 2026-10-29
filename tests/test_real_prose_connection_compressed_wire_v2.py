"""Connection supervisor and history checks accept bounded ASCII envelopes."""

import hashlib
import random
import sys

import pytest

from ladon.bounded_json_transport import (
    _COMPRESSED_MAGIC,
    pack_json,
    pack_json_with_compression_fallback,
    unpack_json_with_compression_fallback,
)
from ladon.process_supervisor import run_bounded_target_process
from ladon.real_prose_connection_history import _supervision


def _large_result():
    rng = random.Random(1123)
    return {'opaque': [rng.randbytes(250_000).hex() for _ in range(18)]}


def test_compressed_wire_survives_text_captured_process_boundary(tmp_path):
    value = {'result': _large_result()}
    wire = pack_json_with_compression_fallback(value)
    assert wire.startswith(_COMPRESSED_MAGIC)
    process = run_bounded_target_process(
        [sys.executable, '-c', 'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
        cwd=tmp_path,
        timeout_seconds=30,
        max_output_bytes=8 * 1024**2,
        input_bytes=wire,
    )
    assert process.succeeded
    assert process.stdout.isascii()
    assert process.stdout.encode('ascii') == wire
    assert unpack_json_with_compression_fallback(process.stdout.encode('ascii')) == value


def test_history_recomputes_compressed_output_digest_and_rejects_substitution():
    result = _large_result()
    body = {'status': 'completed', 'result': result, 'diagnostic': None}
    wire = pack_json_with_compression_fallback(body)
    assert wire.startswith(_COMPRESSED_MAGIC)
    receipt = {
        'command': ['python', '-m', 'ladon.real_prose_connection_worker'],
        'peak_rss_bytes': 1024,
        'elapsed_seconds': 1.0,
        'stdoutDigest': 'sha256:' + hashlib.sha256(wire).hexdigest(),
    }
    check = {
        'bounds': {
            'timeout_seconds': 600,
            'max_rss_bytes': 12 * 1024**3,
            'max_output_bytes': 8 * 1024**2,
            'deadlineMonotonic': 1.0,
        },
        'workerInputDigest': 'sha256:' + '1' * 64,
        'implementationDigest': 'sha256:' + '2' * 64,
        'processReceipt': receipt,
        'result': result,
    }
    _supervision(check)
    receipt['stdoutDigest'] = 'sha256:' + '0' * 64
    with pytest.raises(ValueError, match='output digest/length'):
        _supervision(check)


def test_legacy_output_digest_remains_byte_compatible():
    result = {'status': 'unresolved', 'detail': 'small result'}
    body = {'status': 'completed', 'result': result, 'diagnostic': None}
    assert pack_json_with_compression_fallback(body) == pack_json(body)
