"""Failure paths preserve finite execution and measured resource observations."""
from __future__ import annotations

from pathlib import Path

import pytest
from test_source_association import (
    _api,
    _context,
    _ilean,
    _request,
    _runner,
    _stored_checked_artifacts,
)


@pytest.mark.parametrize('bounds', [
    {'timeout_seconds': float('nan')}, {'timeout_seconds': float('inf')},
    {'timeout_seconds': 601}, {'max_output_bytes': 64 * 1024**2 + 1},
    {'max_rss_bytes': 64 * 1024**3 + 1},
])
def test_invalid_bounds_rejected_when_request_is_constructed(tmp_path, bounds):
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    with pytest.raises((ValueError, TypeError)):
        _request(tmp_path, context, artifacts, **bounds)


@pytest.mark.parametrize('raw', [b'{"nested":' + b'[' * 1100 + b'0' + b']' * 1100 + b'}',
                               _ilean().replace(b'"directImports": []', b'"directImports": [NaN]')])
def test_malformed_fresh_metadata_is_a_bounded_failure(tmp_path, raw):
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    result = capture(_request(tmp_path, context, artifacts), artifacts,
                     process_runner=_runner(ilean=raw))
    assert result['status'] != 'associated'
    assert result['artifacts'] == []
    assert result['resources']['peakRssBytes'] == 1024


def test_missing_compiler_output_preserves_measured_peak(tmp_path: Path):
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    result = capture(_request(tmp_path, context, artifacts), artifacts,
                     process_runner=_runner(ilean=None))
    assert result['status'] != 'associated'
    assert result['artifacts'] == []
    assert result['resources']['peakRssBytes'] == 1024
