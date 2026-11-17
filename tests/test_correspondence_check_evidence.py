"""Stored checker targets must stay visible beside their original obligations."""

import json

import pytest

from ladon.correspondence_evidence import _hash
from ladon.proofir_v3_queries import query_v3_correspondence
from tests.test_correspondence_context import context_database
from tests.test_correspondence_query_coverage import OWNER

REF = {'artifactRef': OWNER, 'kind': 'correspondence', 'localId': 'correspondence:p'}
CHECK_OWNER = 'sha256:' + 'e' * 64
NAMESPACE = 'ladon.correspondence-receipt/v1'


def evidence_database(mode='prove', status='supported'):
    db = context_database()
    db.execute('UPDATE proofir_v3_correspondences SET correspondence_id=?', (REF['localId'],))
    db.execute('INSERT INTO proofir_v3_correspondence_obligations VALUES(?,?,?,?,?,?,?)',
               (OWNER, 0, 'conclusion', 'conclusion-transfer', 'True', status, '/'))
    db.execute('INSERT INTO proofir_v3_correspondence_checks VALUES(?,?,?,?,?,?)',
               (OWNER, 0, CHECK_OWNER, 'check-run', 'check:1', '/'))
    receipt = {'planId': 'p', 'obligation': 'conclusion', 'mode': mode,
               'goalDigest': _hash('True'), 'checkedGoal': 'True' if mode == 'prove' else '¬ (True)',
               'status': status, 'receiptDigest': 'sha256:' + 'f' * 64}
    db.execute('INSERT INTO proofir_v3_extensions VALUES(?,?,?,?,?,?,?)',
               (CHECK_OWNER, NAMESPACE, json.dumps(receipt), _hash(receipt), 'full', 1, '/'))
    db.execute('INSERT INTO proofir_v3_check_runs VALUES(?,?,?,?,?,?,?,?,?,?)',
               (CHECK_OWNER, 'check:1', '{}', 'generated-correspondence-obligation-' + mode,
                '{}', '{}', '{}', 'none', 'process-observation', '/'))
    return db, receipt


def query(db, **options):
    return query_v3_correspondence(db, REF, limit=options.pop('limit', 10), **options)


@pytest.mark.parametrize(('mode', 'status'), [('prove', 'supported'), ('refute', 'refuted'),
                                            ('prove', 'unresolved')])
def test_exact_stored_target_is_visible_without_new_authority(mode, status):
    db, receipt = evidence_database(mode, status)
    result = query(db)
    row = result['checkEvidence']['rows'][0]
    assert row['receipt']['value'] == receipt
    assert row['binding']['status'] == 'matched-stored-records'
    assert row['checkRunRef']['artifactRef'] == CHECK_OWNER
    assert result['dimensions'] == {}
    assert result['authority'] == 'stored-evidence-only'
    assert result['coverage']['checkEvidenceComplete'] is True


@pytest.mark.parametrize(('field', 'value'), [('planId', 'other'), ('obligation', 'other'),
    ('goalDigest', _hash('False')), ('checkedGoal', 'False'), ('mode', 'refute'),
    ('status', 'refuted')])
def test_rewritten_receipt_cannot_match_original_obligation(field, value):
    db, receipt = evidence_database()
    receipt[field] = value
    db.execute('UPDATE proofir_v3_extensions SET payload_json=?,payload_digest=?',
               (json.dumps(receipt), _hash(receipt)))
    result = query(db)
    assert result['checkEvidence']['rows'][0]['binding']['status'] == 'mismatched'
    assert result['coverage']['complete'] is False


@pytest.mark.parametrize('missing', ['receipt', 'table', 'check', 'local-check', 'digest'])
def test_missing_evidence_never_resolves_through_another_owner(missing):
    db, _ = evidence_database()
    if missing == 'receipt':
        db.execute('UPDATE proofir_v3_extensions SET content_artifact_id=?', ('sha256:' + 'f' * 64,))
    elif missing == 'table':
        db.execute('DROP TABLE proofir_v3_extensions')
    elif missing == 'check':
        db.execute('DELETE FROM proofir_v3_check_runs')
    elif missing == 'local-check':
        db.execute("UPDATE proofir_v3_check_runs SET check_run_id='other'")
    else:
        db.execute("UPDATE proofir_v3_extensions SET storage_state='digest-sentinel'")
    result = query(db)
    assert result['checkEvidence']['rows'][0]['binding']['status'] == 'unavailable'
    assert result['coverage']['complete'] is False


def test_receipts_share_the_context_allowance():
    db, _ = evidence_database()
    db.execute('INSERT INTO proofir_v3_correspondence_checks VALUES(?,?,?,?,?,?)',
               (OWNER, 1, CHECK_OWNER, 'check-run', 'check:1', '/'))
    full = query(db)
    size = full['checkEvidence']['rows'][0]['receipt']['storedBytes']
    result = query(db, max_context_bytes=size)
    assert result['checkEvidence']['rows'][0]['receipt']['status'] == 'observed'
    assert result['checkEvidence']['rows'][1]['receipt']['status'] == 'omitted'
    assert result['coverage']['complete'] is False
    limited = query(db, limit=1)
    assert len(limited['checkEvidence']['rows']) == 1
    assert limited['checkEvidence']['omitted'] == 1


def test_nonopen_obligation_without_check_evidence_is_explicit():
    db, _ = evidence_database()
    db.execute('DELETE FROM proofir_v3_correspondence_checks')
    result = query(db)
    assert result['checkEvidence']['unboundObligations'] == ['conclusion']
    assert result['coverage']['checkEvidenceComplete'] is False


def test_inconsistent_refutation_status_is_not_a_matched_binding():
    db, _ = evidence_database(mode='refute', status='supported')
    result = query(db)
    assert 'outcomePolarity' in result['checkEvidence']['rows'][0]['binding']['fields']
