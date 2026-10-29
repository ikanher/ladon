"""Resource and partial-result boundaries for compressed v3 histories."""

import pytest

from ladon.real_prose_connection_history import _check_status, _retained_wire


def test_retained_wire_total_is_bounded_before_joining_chunks():
    with pytest.raises(ValueError, match='wire limit'):
        _retained_wire(['ab', 'cd'], max_wire_bytes=3)


def test_empty_retained_chunks_are_rejected():
    with pytest.raises(ValueError, match='output chunks'):
        _retained_wire([''], max_wire_bytes=3)


def test_incomplete_v3_receipt_cannot_retain_completed_worker_output():
    check = {'status': 'incomplete', 'result': None, 'stdoutWireChunks': ['AQ==']}
    with pytest.raises(ValueError, match='stopped connection'):
        _check_status(check, compressed_wire=True)
