"""Attachment validation keeps ordinary native inputs and authority boundaries."""
import copy
import hashlib

import pytest
from test_investigation_contract_findings import _contract_observation, _native_attachment
from test_investigation_findings import NOW, review_observation

from ladon.investigation import assess
from ladon.investigation_finalization import progress_receipt
from ladon.investigation_observations import record_observation
from ladon.proofir_v3 import validate_envelope_batch


@pytest.mark.parametrize('shape', ['separate-target', 'native-context-population'])
def test_attachment_accepts_the_ordinary_native_batch_contract(tmp_path, shape):
    attachment = _native_attachment()
    artifacts = attachment['context']['artifacts']
    if shape == 'separate-target':
        attachment['context']['artifacts'] = [
            value for value in artifacts
            if value['artifactId'] != attachment['artifact']['artifactId']]
    else:
        artifacts.extend(copy.deepcopy(artifacts[0]) for _ in range(257))
    # Establish that the fixture obeys the existing public native batch limits.
    validate_envelope_batch([*attachment['context']['artifacts'], attachment['artifact']])
    plan = _contract_observation(tmp_path, attachment)
    assert plan['observations'][0]['record']['contractAnalysis'] == attachment


def test_contract_status_does_not_deny_its_native_semantic_revalidation(tmp_path):
    plan = _contract_observation(tmp_path)
    reviewed, _, _ = review_observation(plan, tmp_path)
    # Exercise the legacy-plan status branch, whose old nonclaim denies all comparison.
    reviewed.update(version=1)
    for key in ('correspondenceBundles', 'responses', 'reconciliations'):
        reviewed.pop(key, None)
    status = assess(reviewed, tmp_path, now=NOW)
    assert 'bounded native' in status['authority'].lower()
    assert not any('no lean, network, model service or automatic semantic comparison' in value.lower()
                   for value in status['nonclaims'])
    assert any('source interpretation' in value.lower() for value in status['nonclaims'])


def test_contract_finding_and_receipt_keep_selected_formal_source_locations(tmp_path):
    plan = _contract_observation(tmp_path)
    record = copy.deepcopy(plan.pop('observations')[0]['record'])
    source = b'theorem example : True := True.intro\n'
    (tmp_path / 'Formal.lean').write_bytes(source)
    formal = {'path': 'Formal.lean', 'sha256': hashlib.sha256(source).hexdigest(),
              'startLine': 1, 'endLine': 1, 'statement': source.decode().strip()}
    record['formalSources'] = [formal]
    plan = record_observation(plan, record, tmp_path)
    reviewed, _, _ = review_observation(plan, tmp_path)
    finding = assess(reviewed, tmp_path, now=NOW)['findings'][0]
    assert finding['formalSources'] == [formal]
    receipt, saved = progress_receipt(reviewed, tmp_path, finalize=True, now=NOW)
    assert saved and receipt['findings'][0]['formalSources'] == [formal]
