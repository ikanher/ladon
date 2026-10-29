"""Complete-owner, codec and transactional rejection controls beyond frozen red tests."""

import copy
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_real_prose_native_records import api, artifacts, rehash
from test_real_prose_native_records import captured as _captured_fixture
from test_real_prose_recognition import context, reading

from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import validate_envelope_batch
from ladon.real_prose_native_artifacts import authored_artifacts
from ladon.real_prose_native_codec import CHUNK_BYTES, decode_history, encode_history
from ladon.real_prose_native_payload import recognition_history


@pytest.fixture(scope='module')
def captured(tmp_path_factory):
    return _captured_fixture.__wrapped__(tmp_path_factory)


def test_coefficient_guard_origin_is_preserved_and_bound(captured):
    contract = copy.deepcopy(artifacts(captured[1])[-1])
    assert contract['payload']['record']['origins']['constantGuard'].startswith('/propositionExpr/')
    contract['payload']['record']['origins']['constantGuard'] = '/propositionExpr'
    with pytest.raises(ValueError):
        validate_envelope_batch([*artifacts(captured[1])[:-1], rehash(contract)])


def test_same_line_source_anchor_mutation_rejects_exact_owner_chain(captured):
    values = copy.deepcopy(artifacts(captured[1]))
    source, reading_, contract = values
    source['payload']['anchors'][0]['start']['byte'] += 1
    source['payload']['anchors'][0]['start']['column'] += 1
    rehash(source)
    reading_['payload']['sourceRef']['artifactRef'] = source['artifactId']
    rehash(reading_)
    payload = contract['payload']
    payload['sourceMapRefs'][0]['artifactRef'] = source['artifactId']
    payload['interpretationRef']['artifactRef'] = reading_['artifactId']
    payload['record']['source']['sourceMapRef'] = copy.deepcopy(payload['sourceMapRefs'][0])
    payload['record']['source']['interpretationRef'] = copy.deepcopy(payload['interpretationRef'])
    with pytest.raises(ValueError):
        validate_envelope_batch([source, reading_, rehash(contract)])


def test_distinct_attributed_alternatives_coexist_and_cannot_crosswire(captured):
    first = artifacts(captured[1])
    history = recognition_history(first[-1]['payload'])
    second = authored_artifacts(history, first[:2], alternative_id='reading:b', author='other')
    validate_envelope_batch([*first, second[-1]])
    assert first[-1]['artifactId'] != second[-1]['artifactId']
    second[-1]['payload']['record']['source']['recognitionId'] = 'sha256:' + 'a' * 64
    with pytest.raises(ValueError):
        validate_envelope_batch([*first, rehash(second[-1])])


def test_native_report_summary_has_no_admission_or_fresh_authority(captured, tmp_path, capsys):
    from ladon.proofir_v3_cli import proofir_v3_main

    path = tmp_path / 'native.json'
    path.write_text(json.dumps(artifacts(captured[1])[-1]))
    assert proofir_v3_main(['inspect', str(path)]) == 0
    report = json.loads(capsys.readouterr().out)['contract']
    assert report['profileId'] == 'real-bound-prose-v1'
    assert report['admission'] == 'unresolved' and report['authority'] == 'none'


def test_probe_and_planned_provider_reject_before_using_authored_features(captured):
    from ladon._proof_contract_planned_source_binding import _exact_provider_contract
    from ladon._proof_contract_probe_pair import _resolve_side

    values = artifacts(captured[1])
    contract = values[-1]
    ref = {'artifactRef': contract['artifactId'], 'kind': 'contract',
           'localId': contract['payload']['contractId']}
    with pytest.raises(ValueError, match='profile'):
        _resolve_side(values, {'contractRef': ref})
    provider = {'artifacts': values, 'contract': contract['payload']['record']}
    with pytest.raises(ValueError, match='profile'):
        _exact_provider_contract({'forwardContractRef': ref},
                                 SimpleNamespace(contract_artifacts=values), provider)


def test_sqlite_export_rebuild_indexes_and_rollback_are_lossless(captured, monkeypatch):
    import ladon.proofir_sqlite_v3 as module

    values = artifacts(captured[1])
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, values)
    before = connection.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall()
    exported = [json.loads(row[0]) for row in before]
    rebuilt = sqlite3.connect(':memory:')
    project_envelopes(rebuilt, exported)
    validate_v3_database(rebuilt)
    assert rebuilt.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall() == before
    assert connection.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_v3_contract_source'").fetchone()
    original = module._project_validated
    def fail_after_projection(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected after native projection')
    monkeypatch.setattr(module, '_project_validated', fail_after_projection)
    with pytest.raises(RuntimeError, match='injected'):
        project_envelopes(connection, values)
    assert connection.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall() == before
    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def test_opaque_history_preserves_large_naturals_and_fixed_partition():
    value = {'nat': 2**100, 'text': 'λ' * CHUNK_BYTES}
    encoded = encode_history(value)
    assert decode_history(encoded) == value
    assert all(len(chunk.encode()) == CHUNK_BYTES for chunk in encoded['chunks'][:-1])
    encoded['chunks'].reverse()
    with pytest.raises(ValueError):
        decode_history(encoded)


@pytest.mark.parametrize('value', [float('inf'), float('nan')])
def test_history_never_encodes_nonfinite_numbers(value):
    with pytest.raises(ValueError):
        encode_history({'value': value})


def test_missing_guard_produces_no_native_record(captured):
    root, _ = captured
    record = reading(root)
    body = record['formula']['body']['body']['items'][1]
    record['formula']['body']['body'] = body
    result = api().produce_real_prose_bound(root, record, context(), alternative_id='missing:guard', timeout_seconds=60)
    assert result['status'] == 'unresolved'
    assert artifacts(result) == []


def test_outer_timeout_cleans_native_and_nested_scratch(captured, monkeypatch, tmp_path):
    root, _ = captured
    source = root / 'Context.lean'
    before = source.read_bytes()
    temporary = tmp_path / 'scratch'
    temporary.mkdir()
    monkeypatch.setenv('TMPDIR', str(temporary))
    monkeypatch.setattr(tempfile, 'tempdir', None)
    try:
        source.write_bytes(before + b'\n#eval IO.sleep 10000\n')
        result = api().produce_real_prose_bound(root, reading(root), context(), alternative_id='timeout', timeout_seconds=2)
        assert result['status'] == 'unavailable'
        assert not list(Path(temporary).glob('ladon-prose-*'))
    finally:
        source.write_bytes(before)


def test_unknown_stopped_status_is_not_valid_history(tmp_path):
    from ladon.real_prose_inputs import observation_identity

    snapshot = {
        'schema': 'ladon-real-prose-production-v1', 'status': 'unavailable', 'channel': 'prose',
        'authority': 'none', 'fidelity': 'attributed-unreviewed', 'admission': 'unresolved',
        'request': {'interpretation': reading(tmp_path), 'context': context(),
                    'alternativeId': 'unknown:status', 'author': 'test'},
        'check': {'schema': 'ladon-supervised-obligation-planner-v1', 'status': 'bogus',
                  'result': None, 'diagnostic': None, 'processReceipt': None,
                  'workerInputDigest': None, 'bounds': None},
    }
    snapshot['snapshotId'] = observation_identity(snapshot)
    with pytest.raises(ValueError):
        api().validate_production(snapshot)
