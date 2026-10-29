"""Historical unary coefficient evidence must retain its checked goal and owner."""

import json
import sqlite3
from pathlib import Path

import pytest
from test_real_bound_comparison_persistence import analysis, rehash_artifact

from ladon.proof_contract_cli import contract_main
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import validate_envelope_batch

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/recorded-coefficient.json'


def recorded():
    from ladon.real_bound_native_coefficient_artifacts import recorded_coefficient

    data = json.loads(FIXTURE.read_text())
    return recorded_coefficient(data['production'], data['relationRun'])


def test_unary_coefficient_history_preserves_actual_goal():
    bundle = recorded()
    p = analysis(bundle)['payload']
    assert bundle['authority'] == p['result']['authority'] == 'none'
    assert len(p['contractRefs']) == len(p['checkRunRefs']) == 1
    assert p['stage'] == 'propagation'
    assert p['analysisKind'] == 'real-bound-coefficient-v1'
    assert p['result']['scope'] == 'pointwise-fixed-output-context'
    assert p['result']['coefficientUniformity'] == 'not-inferred'
    assert p['derivationGoalRef']['artifactRef'] == p['checkRunRefs'][0]['artifactRef']
    assert recorded() == bundle


def test_unary_coefficient_sqlite_roundtrip():
    bundle = recorded()
    artifact = analysis(bundle)
    validate_envelope_batch(bundle['artifacts'])
    db = sqlite3.connect(':memory:')
    project_envelopes(db, bundle['artifacts'])
    validate_v3_database(db)
    assert db.execute('SELECT COUNT(*) FROM proofir_v3_contract_analysis_inputs WHERE owner_artifact_id=?',
                      (artifact['artifactId'],)).fetchone() == (1,)
    assert db.execute('SELECT COUNT(*) FROM proofir_v3_contract_analysis_derivations WHERE owner_artifact_id=?',
                      (artifact['artifactId'],)).fetchone() == (1,)
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('field,value', [
    ('scope', 'uniform-estimate'), ('coefficientUniformity', 'proved'), ('authority', 'fresh-lean-check'),
    ('sourceTheoremProof', 'checked'), ('paperNormBridge', 'checked'), ('rule', 'identity-v1'),
])
def test_rehashed_claim_cannot_gain_authority(field, value):
    bundle = recorded()
    target = analysis(bundle)
    target['payload']['result'][field] = value
    rehash_artifact(target)
    with pytest.raises(ValueError):
        validate_envelope_batch(bundle['artifacts'])


@pytest.mark.parametrize('mutation', ['missing-check', 'goal', 'duplicate-owner', 'kind'])
def test_exact_unary_owners_and_rule_kind_required(mutation):
    bundle = recorded()
    target = analysis(bundle)
    p = target['payload']
    if mutation == 'missing-check':
        owner = p['checkRunRefs'][0]['artifactRef']
        bundle['artifacts'] = [r for r in bundle['artifacts'] if r['artifactId'] != owner]
    elif mutation == 'goal':
        p['derivationGoalRef'] = p['contractRefs'][0]
    elif mutation == 'duplicate-owner':
        p['contractRefs'].append(p['contractRefs'][0])
    else:
        p['analysisKind'] = 'real-bound-chain-v1'
    rehash_artifact(target)
    with pytest.raises(ValueError):
        validate_envelope_batch(bundle['artifacts'])


def test_history_survives_checker_drift_and_never_runs_workers(monkeypatch):
    from ladon import real_bound_native_coefficient as live
    from ladon import real_bound_native_coefficient_bundle as bundles
    from ladon import real_bound_native_coefficient_evidence as evidence

    def forbidden(*_args, **_kwargs):
        pytest.fail('historical inspection attempted fresh checking')

    monkeypatch.setattr(live, '_fresh', forbidden)
    monkeypatch.setattr(evidence, 'native_checker_identity', lambda: 'sha256:' + 'f' * 64)
    result = bundles.inspect_coefficient_bundle(recorded())
    assert result['authority'] == 'none'
    assert result['freshCheck'] is False
    assert result['evidenceAuthentication'] == 'not-established'


@pytest.mark.parametrize('operation', ['inspect-real-coefficient', 'inspect'])
def test_public_coefficient_history(tmp_path, capsys, operation):
    path = tmp_path / 'bundle.json'
    path.write_text(json.dumps(recorded()))
    assert contract_main([operation, '--input', str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'validated-historical'
    assert result['recordedResult']['scope'] == 'pointwise-fixed-output-context'
    assert result['authority'] == 'none'


def test_coefficient_cannot_be_misused_as_input_predicate_edge():
    from ladon.real_bound_native_chain_artifacts import recorded_chain

    with pytest.raises(ValueError, match='single-edge|unsupported|comparison'):
        recorded_chain([recorded()])
