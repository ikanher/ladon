"""Bound authored blockers to exact current obligations, without reviewing them."""

import copy

from ladon.correspondence_interpretation import closed, text
from ladon.proof_slice import digest


def _blocker_evidence(blocker):
    keys = {'kind', 'evidence', 'nextAction', 'unblockCondition'}
    if isinstance(blocker, dict) and blocker.get('kind') == 'policy-limited':
        keys.add('unverifiedScope')
    closed(blocker, keys, 'work blocker evidence')
    for key in keys:
        text(blocker[key], key)
    return blocker


def separate_blocked_work(plan, queue):
    if 'workBlockers' not in plan:
        return queue, []
    value = plan['workBlockers']
    closed(value, {'profile', 'records'}, 'work blockers')
    if value['profile'] != 'work-blockers-v1':
        raise ValueError('unsupported work blocker profile')
    records = value['records']
    if not isinstance(records, list) or len(records) > 4096:
        raise ValueError('invalid bounded work blockers')
    return _partition_work(records, queue)


def _partition_work(records, queue):
    work = {digest(row): row for row in queue}
    seen, blocked = set(), []
    for row in records:
        closed(row, {'workId', 'blocker'}, 'work blocker record')
        identity = row['workId']
        if not isinstance(identity, str) or identity not in work or identity in seen:
            raise ValueError('unknown, duplicate or stale work blocker identity')
        blocker = _blocker_evidence(row['blocker'])
        seen.add(identity)
        blocked.append({'workId': identity, 'work': copy.deepcopy(work[identity]),
                        'blocker': copy.deepcopy(blocker)})
    return [row for row in queue if digest(row) not in seen], blocked
