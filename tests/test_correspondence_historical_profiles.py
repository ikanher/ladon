"""Historical untyped projections stay readable without acquiring typed support."""

import copy

from test_correspondence_investigation_v3 import input_bundle

from ladon.correspondence_interpretation import LEGACY_PROFILE, lower_formula
from ladon.proofir_correspondence import interpretation_artifacts
from ladon.proofir_v3 import detached_content_id


def test_historical_untyped_interpretation_retains_bytes_and_migration_queue(tmp_path):
    from ladon.investigation_correspondence import assess_v3, attach_bundle, initialize_v3

    source, bundle = input_bundle(tmp_path)
    record = bundle['record']
    record['formula'] = {'tag': 'eq', 'left': {'tag': 'const', 'name': '2'},
                         'right': {'tag': 'app', 'symbol': 'divide', 'args': [
                             {'tag': 'const', 'name': '41'}, {'tag': 'const', 'name': '20'}]}}
    record['symbols'] = {'divide': {'leanName': 'HDiv.hDiv', 'leanType': 'Rat → Rat → Rat'}}
    artifacts = list(interpretation_artifacts(record, 'sha256:'+'0'*64, source_root=tmp_path))
    artifact = artifacts[-1]
    artifact['payload'].pop('loweringProfile')
    artifact['payload']['loweredFormula'] = lower_formula(record['formula'], record['symbols'],
                                                         _profile=LEGACY_PROFILE)
    artifact['artifactId'] = detached_content_id(artifact)
    bundle.update(artifacts=artifacts, loweredFormula=artifact['payload']['loweredFormula'])
    original = copy.deepcopy(bundle)
    attached = attach_bundle(initialize_v3(source, tmp_path), bundle, tmp_path)
    status = assess_v3(attached, tmp_path)
    assert attached['correspondenceBundles'][0]['bundle'] == original
    assert bundle == original
    assert any(row['kind'] == 'refresh-semantic-profile' for row in status['next'])
    assert status['formalCorrespondence'] != 'recorded-links-complete-unreplayed'
