"""Byte stability excludes measured resource telemetry but retains its meaning."""
import copy

import pytest
from test_report_v2 import canonical_payload

from ladon.report_serialization import canonical_json_bytes


def _payload(peak):
    result = canonical_payload()
    result['phases']['module_dag']['data']['run_resources'] = {
        'observed': {'peakRssBytes': peak, 'observedWallSeconds': 1.0, 'moduleCount': 3},
        'limits': {'peakRssBytes': 1024, 'wallSeconds': 10.0}, 'status': 'accepted'}
    return result


def test_measured_rss_does_not_make_equivalent_reports_nondeterministic():
    first, second = _payload(128), _payload(256)
    original = copy.deepcopy(second)
    assert canonical_json_bytes(first) != canonical_json_bytes(second)
    assert canonical_json_bytes(first, normalize_timings=True) == canonical_json_bytes(
        second, normalize_timings=True)
    assert second == original


@pytest.mark.parametrize('section,key,value', [
    ('limits', 'peakRssBytes', 2048),
    ('observed', 'moduleCount', 4),
    ('observed', 'peakRssBytes', None),
])
def test_resource_meaning_remains_visible_in_normalized_bytes(section, key, value):
    first, second = _payload(128), _payload(256)
    second['phases']['module_dag']['data']['run_resources'][section][key] = value
    assert canonical_json_bytes(first, normalize_timings=True) != canonical_json_bytes(
        second, normalize_timings=True)


def test_resource_status_and_unregistered_peak_values_are_not_normalized():
    first, second = _payload(128), _payload(128)
    second['phases']['module_dag']['data']['run_resources']['status'] = 'rejected'
    assert canonical_json_bytes(first, normalize_timings=True) != canonical_json_bytes(
        second, normalize_timings=True)
    second = copy.deepcopy(first)
    first['phases']['module_dag']['data']['peakRssBytes'] = 128
    second['phases']['module_dag']['data']['peakRssBytes'] = 256
    assert canonical_json_bytes(first, normalize_timings=True) != canonical_json_bytes(
        second, normalize_timings=True)
