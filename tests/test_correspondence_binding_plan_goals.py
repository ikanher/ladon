"""Self-consistent row receipts cannot replace their planned obligation."""
import copy

import pytest

from ladon.correspondence_evidence import _hash
from ladon.investigation_correspondence_inputs import validate_check_receipt_bindings


def test_changed_goal_with_rehashed_receipt_still_rejects_plan_mismatch():
    row = {'obligation': 'interpretation', 'mode': 'prove', 'goal': 'False → False',
           'status': 'supported'}
    evidence = {'planId': 'plan-id', 'obligation': 'interpretation', 'mode': 'prove',
                'goalDigest': _hash(row['goal']), 'receiptDigest': _hash(row)}
    bundle = {'planId': 'plan-id', 'plan': {'obligations': [
        {'id': 'interpretation', 'goal': 'True → True'}]}, 'checks': [row],
        'artifacts': [{'artifactKind': 'proofir.check-run', 'artifactId': 'check-id',
                       'payload': {'checkRunId': 'check-local'}, 'extensions': {
                           'ladon.correspondence-receipt/v1': evidence}}],
        'checkRunRefs': [{'artifactRef': 'check-id', 'kind': 'check-run',
                          'localId': 'check-local'}]}
    positive = copy.deepcopy(bundle)
    positive['plan']['obligations'][0]['goal'] = row['goal']
    validate_check_receipt_bindings(positive)
    with pytest.raises(ValueError, match='(?i)(goal|obligation|plan)'):
        validate_check_receipt_bindings(bundle)
