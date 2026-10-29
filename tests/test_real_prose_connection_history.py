"""Qualified recorded checks remain historical and bind exact original inputs."""

import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from ladon.bounded_json_transport import pack_json
from ladon.real_prose_connection import inspect_real_prose_connection, replay_real_prose_connection
from ladon.real_prose_inputs import observation_identity


@pytest.fixture(scope='module')
def qualified():
    selected = os.environ.get('LADON_CONNECTION_TEST_CASE')
    if selected is None:
        pytest.skip('set LADON_CONNECTION_TEST_CASE to a qualified live case directory')
    root = Path(selected)
    values = [json.loads((root/name).read_text()) for name in ['CONNECTION.json','FORMAL.json','AUTHORED.json']]
    return (*values,Path((root/'ROOT.txt').read_text().strip()))


def rehash(value):
    check = value['check']
    wire = pack_json({'status':'completed','result':check['result'],'diagnostic':None})
    check['processReceipt']['stdoutDigest'] = 'sha256:'+hashlib.sha256(wire).hexdigest()
    value['snapshotId'] = observation_identity(value)
    return value


def test_saved_fresh_claim_grants_no_inspection_authority(qualified):
    snapshot,*_ = qualified
    report = inspect_real_prose_connection(snapshot)
    assert report['recordedStatus'] == 'connected'
    assert report['authority'] == 'none' and report['freshCheck'] is False
    assert report['evidenceAuthentication'] == 'not-established'
    assert report['sourceTheoremProof'] == 'not-checked'
    assert report['admission'] == 'unresolved'


@pytest.mark.parametrize('path,bad', [
    (['bound','connection','term'],'by trivial'),
    (['bound','inputs','authored','digest'],'not-a-digest'),
    (['goal','request','authored','expression'],{'const':'False','levels':[]}),
    (['goal','completion','termDigest'],'sha256:'+'0'*64),
    (['goal','completion','captureId'],'sha256:'+'0'*64),
    (['goal','completion','trust','observedAxioms'],['sorryAx']),
    (['goal','completion','replay','status'],'rejected'),
    (['goal','capture','capture','source','module'],'Other'),
])
def test_consistently_rehashed_local_evidence_substitutions_reject(qualified,path,bad):
    snapshot,*_ = qualified
    value = copy.deepcopy(snapshot)
    row = value['check']['result']
    for field in path[:-1]:
        row = row[field]
    row[path[-1]] = bad
    with pytest.raises((ValueError,TypeError,KeyError)):
        inspect_real_prose_connection(rehash(value))


def test_qualifications_cannot_be_promoted_by_rehashing(qualified):
    snapshot,*_ = qualified
    value = copy.deepcopy(snapshot)
    value['sourceTheoremProof'] = 'checked'
    value['snapshotId'] = observation_identity(value)
    with pytest.raises(ValueError):
        inspect_real_prose_connection(value)


def test_newer_equivalent_formal_record_cannot_replace_the_original_on_replay(qualified):
    snapshot,formal,authored,root = qualified
    fresh = snapshot['check']['result']['formal']
    assert fresh['snapshotId'] != formal['snapshotId']
    result = replay_real_prose_connection(snapshot,fresh,authored,root,root,timeout_seconds=30)
    assert result['status'] == 'unavailable' and result['authority'] == 'none'
    assert 'exact original' in result['check']['diagnostic']


def test_completed_snapshot_cannot_lose_its_goal_evidence(qualified):
    snapshot,*_ = qualified
    value = copy.deepcopy(snapshot)
    value['check']['result']['goal'] = None
    with pytest.raises((ValueError,TypeError,KeyError)):
        inspect_real_prose_connection(rehash(value))


def test_changed_valid_external_reference_requires_original_records_on_replay(qualified):
    snapshot,formal,authored,root = qualified
    value = copy.deepcopy(snapshot)
    value['check']['result']['bound']['inputs']['authored']['digest'] = 'sha256:'+'0'*64
    rehash(value)
    report = inspect_real_prose_connection(value)
    assert report['authority'] == 'none'
    assert report['externalInputBinding'] == 'requires-original-inputs-for-replay'
    result = replay_real_prose_connection(value,formal,authored,root,root,timeout_seconds=30)
    assert result['status'] == 'unavailable'
    assert 'exact original' in result['check']['diagnostic']
