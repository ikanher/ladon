"""Explicit extraction limits must survive replay without hidden escalation."""
import json
from pathlib import Path

import pytest

from ladon.proof_slice import extract_proof_slice
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES


@pytest.mark.parametrize('kwargs', [{'timeout_seconds': 0}, {'timeout_seconds': True},
                                    {'max_rss_bytes': -1}, {'max_rss_bytes': True}])
def test_invalid_limits_before_filesystem(kwargs):
    with pytest.raises(ValueError, match='slice resource'):
        extract_proof_slice('/nonexistent', 'X.lean', 'X', 'x', 'y', **kwargs)


def test_custom_limits_replay_requires_explicit_allowance():
    from ladon.correspondence_check import check_correspondence, prepare_correspondence

    root = Path(__file__).parent / 'fixtures/correspondence_m1'
    result = extract_proof_slice(root, 'Proof.lean', 'Proof', 'Correspondence.term',
                                 'bridge', scoped=True, timeout_seconds=90,
                                 max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
    assert result['complete']
    assert result['limits']['secondsPerProcess'] == 90
    record = json.loads((root / 'positive.json').read_text())
    plan = prepare_correspondence(record, result, {'n': 'n'})
    with pytest.raises(ValueError, match='explicit slice replay allowance'):
        check_correspondence(plan, [], root)
    replay = check_correspondence(plan, [], root, slice_timeout_seconds=90)
    assert replay['conditionalValidity'] == 'supported'
