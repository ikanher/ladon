"""Successful status cannot hide inconsistent outer relation provenance."""

import json

import pytest
from test_real_bound_comparison_persistence import FIXTURE

from ladon.real_bound_native_analysis_artifacts import recorded_comparison


@pytest.mark.parametrize('field,value', [
    ('inputDigest', 'sha256:' + 'f' * 64),
    ('requestedTimeoutSeconds', 601),
    ('configuredTimeoutSeconds', 601),
    ('requestedMaxRssBytes', 99 * 1024**3),
    ('requestedMaxOutputBytes', 100 * 1024**2),
])
def test_outer_receipt_must_match_worker_input_and_bounds(field, value):
    data = json.loads(FIXTURE.read_text())
    data['relationRun']['processReceipt'][field] = value
    with pytest.raises(ValueError):
        recorded_comparison(data['productions'], data['relationRun'])


@pytest.mark.parametrize('field,value', [('timeout_seconds', 601), ('max_rss_bytes', 99 * 1024**3),
                                       ('max_output_bytes', 100 * 1024**2)])
def test_saved_bounds_cannot_exceed_relation_policy(field, value):
    data = json.loads(FIXTURE.read_text())
    data['relationRun']['bounds'][field] = value
    with pytest.raises(ValueError):
        recorded_comparison(data['productions'], data['relationRun'])
