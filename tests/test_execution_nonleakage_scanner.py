"""Positive controls keep the nonleakage gate sensitive to contaminated evidence."""
from __future__ import annotations

import pytest
from support.execution_nonleakage import (
    FORBIDDEN_MARKERS,
    assert_clean_files,
    assert_no_discarded_input,
)


@pytest.mark.parametrize('carrier', ['diagnostic', 'metadata-key', 'binary-sidecar'])
def test_gate_rejects_each_marker_in_an_output_carrier(carrier: str) -> None:
    for marker in FORBIDDEN_MARKERS:
        value = {
            'diagnostic': f'worker failed: {marker}',
            'metadata-key': {marker: 'captured'},
            'binary-sidecar': b'\x00SQLite\x00' + marker.encode() + b'\xff',
        }[carrier]
        with pytest.raises(AssertionError, match='discarded caller'):
            assert_no_discarded_input(value)


def test_gate_scans_nonempty_sqlite_sidecars(tmp_path) -> None:
    sidecar = tmp_path / 'evidence.sqlite-wal'
    sidecar.write_bytes(b'\x00' + FORBIDDEN_MARKERS[0].encode())
    with pytest.raises(AssertionError, match='discarded caller'):
        assert_clean_files(tmp_path)
