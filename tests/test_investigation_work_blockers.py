"""Every remaining obligation needs its own bound blocker to terminate early."""
import copy
from datetime import UTC, datetime, timedelta

import pytest

from ladon.investigation import assess, initialize
from ladon.investigation_finalization import progress_receipt
from ladon.proof_slice import digest


def test_one_blocker_does_not_hide_other_work_and_policy_scope_stays_unverified(tmp_path):
    source = tmp_path / 'source.txt'
    source.write_text('Source assertion awaiting review.\n')
    now = datetime.now(UTC)
    plan = initialize(source, tmp_path, correspondence=True, now=now-timedelta(minutes=1))
    queue = assess(plan, tmp_path, now=now)['next']
    blocker = {'kind': 'policy-limited', 'evidence': 'Harness forbids reading the relevant reference.',
               'nextAction': 'Review the reference when policy allows it.',
               'unblockCondition': 'Operator permits that reference review.',
               'unverifiedScope': 'Reference-dependent assertion remains unverified.'}
    partial = copy.deepcopy(plan)
    partial['workBlockers'] = {'profile': 'work-blockers-v1',
                              'records': [{'workId': digest(queue[0]), 'blocker': blocker}]}
    outcome, saved = progress_receipt(partial, tmp_path, finalize=True, now=now)
    assert not saved and outcome['status'] == 'continue'
    assert outcome['next'] and outcome['blocked']
    complete = copy.deepcopy(partial)
    complete['workBlockers']['records'] = [
        {'workId': digest(work), 'blocker': blocker} for work in queue]
    outcome, saved = progress_receipt(complete, tmp_path, finalize=True, now=now)
    assert saved and outcome['status'] == 'incomplete-blocked'
    assert outcome['terminalReason'] == 'no-actionable-work-blocker'
    assert outcome['mathematicalReview'] == 'incomplete-review'
    assert outcome['formalCorrespondence'] == 'incomplete-no-counterpart'
    assert all('unverifiedScope' in row['blocker'] for row in outcome['blocked'])
    complete['workBlockers']['records'][0]['workId'] = 'stale'
    with pytest.raises(ValueError, match='stale|unknown'):
        assess(complete, tmp_path, now=now)
