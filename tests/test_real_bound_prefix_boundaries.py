"""Prefix rule candidate filtering and resource boundaries are conservative."""

import copy

import pytest
from test_real_bound_prefix_rule import pair

from ladon.real_bound_native_prefix import check_prefix_implication, prefix_candidate


@pytest.mark.parametrize('side,field', [('input', 'functionRef'), ('input', 'setRef'),
                                      ('input', 'boundRef'), ('output', 'functionRef'),
                                      ('output', 'setRef'), ('output', 'orderRef'), ('output', 'boundRef')])
def test_only_the_input_order_can_change(side, field):
    high, low = pair()
    artifact = high['artifacts'][-1]
    record = artifact['payload']['record']
    ref = record['application'][side][field]
    original = next(row for row in artifact['subjectRefs'] if row['localId'] == ref['localId'])
    changed = copy.deepcopy(original)
    changed['localId'] = 'expr:' + 'c' * 64
    changed['fingerprint']['digest'] = 'sha256:' + 'c' * 64
    artifact['subjectRefs'].append(changed)
    record['application'][side][field] = {'kind': 'expression', 'localId': changed['localId']}
    assert prefix_candidate(high, low) == 'real-prefix-context-mismatch'


@pytest.mark.parametrize('seconds', [0, -1, 601, float('inf'), float('nan'), True])
def test_bad_deadline_is_rejected_before_reading_productions(seconds):
    with pytest.raises(ValueError):
        check_prefix_implication({}, {}, '/absent', timeout_seconds=seconds)


def test_bounded_inputs_before_source_or_worker_use():
    with pytest.raises(ValueError, match='32 MiB'):
        check_prefix_implication({'padding': 'x' * (32 * 1024**2)}, {}, '/absent')
