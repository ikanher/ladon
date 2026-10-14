"""Stop attribution and receipt binding never turn incompleteness into proof."""
import copy
from datetime import UTC, datetime, timedelta

import pytest

from ladon.investigation import initialize
from ladon.investigation_finalization import progress_receipt, validate_progress_receipt
from ladon.proof_slice import digest


def test_attributed_user_stop_and_stale_bindings(tmp_path):
    source = tmp_path / 'source.txt'
    source.write_text('An assertion.\n')
    now = datetime.now(UTC)
    plan = initialize(source, tmp_path, now=now-timedelta(minutes=1), correspondence=True)
    stop = {'schema': 'ladon-investigation-user-stop-v1', 'actor': 'operator',
            'at': now.isoformat(), 'instructionRef': 'session:user:stop-1',
            'reason': 'Operator requested cancellation.', 'planId': digest(plan),
            'scopeId': digest(plan['scope'])}
    receipt, saved = progress_receipt(plan, tmp_path, finalize=True, stop_record=stop, now=now)
    assert saved and receipt['terminalReason'] == 'user-stop'
    assert receipt['mathematicalReview'] == 'incomplete-review'
    assert receipt['formalCorrespondence'] == 'incomplete-no-counterpart'
    assert receipt['next'] and receipt['status'] == 'incomplete-user-stop'
    assert validate_progress_receipt(receipt, plan, tmp_path) == receipt
    changed = copy.deepcopy(plan)
    changed['units'][0].update(inventory='done', note='Different inventory.')
    with pytest.raises(ValueError, match='different plan'):
        progress_receipt(changed, tmp_path, finalize=True, stop_record=stop, now=now)
    with pytest.raises(ValueError, match='stale'):
        validate_progress_receipt(receipt, changed, tmp_path)
    source.write_text('Changed assertion.\n')
    with pytest.raises(ValueError, match='stale source'):
        validate_progress_receipt(receipt, plan, tmp_path)


@pytest.mark.parametrize('version', [1, 2, 3])
def test_budget_receipts_retain_unfinished_queue_and_clock(tmp_path, version):
    source = tmp_path / 'source.txt'
    source.write_text('Still unreviewed.\n')
    now = datetime.now(UTC)
    plan = initialize(source, tmp_path, now=now-timedelta(minutes=90),
                      derivations=version == 2, correspondence=version == 3)
    receipt, saved = progress_receipt(plan, tmp_path, finalize=True, now=now)
    assert saved and receipt['terminalReason'] == 'elapsed-budget'
    assert receipt['next'] and receipt['remainingSeconds'] == 0
    assert receipt['startedAt'] == plan['startedAt']
    assert validate_progress_receipt(receipt, plan, tmp_path) == receipt
