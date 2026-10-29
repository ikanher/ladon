"""Directional native history must preserve evidence without granting freshness."""

import json
import sqlite3
from pathlib import Path

import pytest
from test_real_bound_comparison_persistence import analysis, rehash_artifact

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import validate_envelope_batch

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/recorded-prefix.json'


def recorded():
    from ladon.real_bound_native_prefix_artifacts import recorded_prefix

    data = json.loads(FIXTURE.read_text())
    return recorded_prefix(data['productions'], data['relationRun'])


def test_directional_history_and_sqlite_roundtrip():
    bundle = recorded()
    payload = analysis(bundle)['payload']
    assert bundle['schema'] == 'ladon-real-bound-prefix-bundle-v1'
    assert bundle['authority'] == 'none'
    assert payload['analysisKind'] == 'real-bound-prefix-v1'
    _history_claims(bundle, payload)
    validate_envelope_batch(bundle['artifacts'])
    db = sqlite3.connect(':memory:')
    project_envelopes(db, bundle['artifacts'])
    validate_v3_database(db)
    rows = db.execute('SELECT contract_owner,contract_local_id FROM proofir_v3_contract_analysis_inputs '
                      'WHERE owner_artifact_id=? ORDER BY ordinal',
                      (analysis(bundle)['artifactId'],)).fetchall()
    assert rows == [(r['artifactRef'], r['localId']) for r in payload['contractRefs']]
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def _history_claims(bundle, payload):
    assert payload['result']['relation'] == 'input-prefix-implies'
    assert payload['result']['rule'] == 'order-prefix-v1'
    assert payload['result']['authority'] == 'none'
    assert payload['result']['sourceTheoremProof'] == 'not-checked'
    assert payload['result']['paperNormBridge'] == 'unresolved'
    assert payload['contractRefs'][0] != payload['contractRefs'][1]
    assert len(payload['checkRunRefs']) == 1
    assert recorded() == bundle


@pytest.mark.parametrize('mutation', ['direction', 'equivalence', 'rule', 'fresh', 'kind', 'goal', 'missing-check'])
def test_native_rehashed_claim_mutations_reject(mutation):
    bundle = recorded()
    target = analysis(bundle)
    payload = target['payload']
    if mutation == 'direction':
        payload['contractRefs'].reverse()
    elif mutation == 'equivalence':
        payload['result']['relation'] = 'equivalent'
    elif mutation == 'rule':
        payload['result']['rule'] = 'coefficient-mono-v1'
    elif mutation == 'fresh':
        payload['result']['authority'] = 'fresh-lean-check'
    elif mutation == 'kind':
        payload.pop('analysisKind')
    elif mutation == 'goal':
        payload['result']['goalDigest'] = 'sha256:' + 'e' * 64
    else:
        owner = payload['checkRunRefs'][0]['artifactRef']
        bundle['artifacts'] = [r for r in bundle['artifacts'] if r['artifactId'] != owner]
    rehash_artifact(target)
    with pytest.raises(ValueError):
        validate_envelope_batch(bundle['artifacts'])


@pytest.mark.parametrize('mutation', ['pair', 'request', 'term', 'capture', 'memory', 'checker', 'admission'])
def test_recording_rejects_inconsistent_historical_proof(mutation):
    from ladon.real_bound_native_prefix_artifacts import recorded_prefix

    data = json.loads(FIXTURE.read_text())
    run = data['relationRun']
    result = run['result']
    if mutation == 'pair':
        data['productions'].reverse()
    elif mutation == 'request':
        result['request']['strongerPlanId'] = result['request']['weakerPlanId']
    elif mutation == 'term':
        result['request']['term'] = 'by trivial'
    elif mutation == 'capture':
        result['check']['capture']['capture']['source']['byteLength'] += 1
    elif mutation == 'memory':
        run['processReceipt']['memoryLimited'] = True
    elif mutation == 'checker':
        result['checkerIdentity'] = 'sha256:' + 'e' * 64
    else:
        result['request']['admissionTerm'] = 'by trivial'
    with pytest.raises(ValueError):
        recorded_prefix(data['productions'], run)


def test_history_survives_checker_drift_without_invoking_checkers(monkeypatch):
    from ladon import real_bound_native_check as checker
    from ladon import real_bound_native_prefix as live
    from ladon.real_bound_native_prefix_bundle import inspect_prefix_bundle

    def forbidden(*_args, **_kwargs):
        pytest.fail('offline history attempted a worker')

    monkeypatch.setattr(live, '_fresh', forbidden)
    monkeypatch.setattr(live, 'check_prefix_relation', forbidden)
    monkeypatch.setattr(checker, 'native_checker_identity', lambda: 'sha256:' + 'f' * 64)
    bundle = recorded()
    bundle['authority'] = 'fresh-source-predicate-scalar-and-prefix-checks'
    bundle['snapshotId'] = snapshot_identity(bundle)
    result = inspect_prefix_bundle(bundle)
    assert result['authority'] == 'none'
    assert result['freshCheck'] is False
    assert result['evidenceAuthentication'] == 'not-established'
    assert result['recordedResult']['relation'] == 'input-prefix-implies'


@pytest.mark.parametrize('operation', ['inspect-real-prefix', 'inspect'])
def test_public_history_inspection(tmp_path, capsys, operation):
    path = tmp_path / 'bundle.json'
    path.write_text(json.dumps(recorded()))
    assert contract_main([operation, '--input', str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'validated-historical'
    assert result['authority'] == 'none'


@pytest.mark.parametrize('operation', ['check-real-bound-prefix-proofir', 'replay-real-prefix'])
def test_public_fresh_dispatch_unresolved(tmp_path, monkeypatch, capsys, operation):
    from ladon import real_bound_native_prefix_bundle as bundles

    path = tmp_path / 'value.json'
    path.write_text('{}')
    calls = []

    def fresh(*args, timeout_seconds):
        calls.append((args, timeout_seconds))
        return {'schema': 'ladon-real-bound-prefix-analysis-v1', 'status': 'unresolved', 'relation': None}

    monkeypatch.setattr(bundles, 'produce_prefix_bundle', fresh)
    monkeypatch.setattr(bundles, 'replay_prefix_bundle', fresh)
    flags = (['--stronger', str(path), '--weaker', str(path)]
             if operation == 'check-real-bound-prefix-proofir' else ['--input', str(path)])
    assert contract_main([operation, *flags, '--root', str(tmp_path), '--timeout-seconds', '27']) == 2
    assert calls[0][0][-1] == tmp_path
    assert calls[0][1] == 27
    assert json.loads(capsys.readouterr().out)['relation'] is None
