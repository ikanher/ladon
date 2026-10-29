"""Authored Real records retain exact typed owners without semantic promotion."""

import copy
import importlib
import json
import shutil
import sqlite3

import pytest
from test_real_prose_recognition import ROOT, context, reading

from ladon.proofir_v3 import detached_content_id, validate_envelope, validate_envelope_batch


def api():
    return importlib.import_module('ladon.real_prose_native_production')


@pytest.fixture(scope='module')
def captured(tmp_path_factory):
    module = api()
    root = tmp_path_factory.mktemp('authored-real')
    for name in ['Context.lean', 'lean-toolchain']:
        shutil.copy2(ROOT / name, root / name)
    result = module.produce_real_prose_bound(root, reading(root), context(),
                                            alternative_id='reading:a', author='tester', timeout_seconds=60)
    return root, result


def rehash(artifact):
    artifact['artifactId'] = detached_content_id(artifact)
    return artifact


def artifacts(snapshot):
    return snapshot['check']['result']['artifacts']


def test_fresh_production_has_exact_attributed_record_and_historical_native_authority(captured):
    root, snapshot = captured
    assert snapshot['status'] == 'authored' and snapshot['admission'] == 'unresolved'
    native = artifacts(snapshot)
    validate_envelope_batch(native)
    contract = native[-1]
    record = contract['payload']['record']
    assert record['profileId'] == 'real-bound-prose-v1'
    assert record['scope'] == {'kind': 'global'} and record['loss'] == 5
    assert record['alternativeId'] == 'reading:a' and record['author'] == 'tester'
    assert record['admission'] == 'unresolved'
    assert record['guards']['boundNonnegativeBinderIds']
    assert contract['payload']['checkRunRefs'] == []
    inspected = api().inspect_real_prose_bound(snapshot, root)
    assert inspected['authority'] == 'none' and inspected['freshCheck'] is False
    assert inspected['sourceFreshness'] == 'current'
    assert inspected['evidenceAuthentication'] == 'not-established'


@pytest.mark.parametrize('field', ['admission', 'origin', 'scope', 'alternative', 'permissions', 'fidelity'])
def test_rehashed_native_promotions_and_feature_drift_reject(captured, field):
    contract = copy.deepcopy(artifacts(captured[1])[-1])
    record = contract['payload']['record']
    if field == 'admission':
        record['admission'] = 'admitted'
    elif field == 'origin':
        record['origins']['input'] = '/propositionExpr'
    elif field == 'scope':
        record['scope'] = {'kind': 'set-indexed'}
    elif field == 'alternative':
        record['alternativeId'] = 'reading:b'
    elif field == 'permissions':
        record['constant']['permittedBinderIds'].append(record['roles']['function'])
    else:
        contract['payload']['provenance']['fidelity'] = 'reviewed-qualified'
    with pytest.raises(ValueError):
        validate_envelope(rehash(contract))


def test_native_interpretation_owner_cannot_be_crosswired_or_omitted(captured):
    values = copy.deepcopy(artifacts(captured[1]))
    contract = values[-1]
    contract['payload']['interpretationRef']['artifactRef'] = values[0]['artifactId']
    with pytest.raises(ValueError):
        validate_envelope_batch([*values[:-1], rehash(contract)])
    with pytest.raises(ValueError):
        validate_envelope_batch([artifacts(captured[1])[-1]])


def test_saved_production_reconstructs_record_and_rejects_current_source_change(captured):
    from ladon.real_prose_inputs import observation_identity

    root, saved = captured
    changed = copy.deepcopy(saved)
    artifacts(changed)[-1]['payload']['record']['loss'] = 4
    changed['snapshotId'] = observation_identity(changed)
    with pytest.raises(ValueError):
        api().inspect_real_prose_bound(changed)
    source = root / 'claim.txt'
    before = source.read_bytes()
    try:
        source.write_bytes(before + b' changed')
        assert api().inspect_real_prose_bound(saved)['freshCheck'] is False
        with pytest.raises(ValueError):
            api().inspect_real_prose_bound(saved, root)
    finally:
        source.write_bytes(before)


def test_existing_sqlite_projection_preserves_full_authored_payload(captured):
    from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database

    native = artifacts(captured[1])
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, native)
    validate_v3_database(connection)
    record, provenance = connection.execute(
        'SELECT record_json,provenance_json FROM proofir_v3_contracts').fetchone()
    assert json.loads(record) == native[-1]['payload']['record']
    assert json.loads(provenance) == native[-1]['payload']['provenance']
    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def test_legacy_nat_and_extracted_real_consumers_reject_authored_profile(captured):
    from ladon._contract_propagation_inputs import read_contracts
    from ladon.proof_contract_artifacts import comparison_artifact
    from ladon.real_bound_native_record import validate_record

    contract = artifacts(captured[1])[-1]
    for consume in [
        lambda: read_contracts([contract], contract['environmentRef']),
        lambda: comparison_artifact(contract, contract, analysis_id='unsupported:authored'),
        lambda: validate_record(contract['payload']['record']),
    ]:
        with pytest.raises(ValueError):
            consume()
