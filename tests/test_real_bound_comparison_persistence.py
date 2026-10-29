"""Behavioral history/owner gates for native Real comparison bundles."""

import copy
import json
import sqlite3
from pathlib import Path

import pytest

from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/recorded-comparison.json'


def recorded():
    from ladon.real_bound_native_analysis_artifacts import recorded_comparison

    data = json.loads(FIXTURE.read_text())
    return recorded_comparison(data['productions'], data['relationRun'])


def analysis(bundle):
    return next(row for row in bundle['artifacts']
                if row['artifactId'] == bundle['analysisRef']['artifactRef'])


def rehash_artifact(row):
    row['artifactId'] = detached_content_id(row)
    return row


def test_genuine_recorded_relation_roundtrips_through_native_batch_and_sqlite():
    bundle = recorded()
    artifact = analysis(bundle)
    validate_envelope_batch(bundle['artifacts'])
    p = artifact['payload']
    assert bundle['authority'] == 'none'
    assert p['stage'] == 'comparison'
    assert p['result']['authority'] == 'none'
    assert p['result']['status'] == 'recorded-checked'
    assert p['result']['relation'] == 'equivalent'
    assert p['result']['sourceTheoremProof'] == 'not-checked'
    assert p['result']['paperNormBridge'] == 'unresolved'
    assert p['contractRefs'][0] != p['contractRefs'][1]
    assert len(p['checkRunRefs']) == 1
    assert all(row['authority'] == 'none' for row in p['replay']['productions'])
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, bundle['artifacts'])
    validate_v3_database(connection)
    rows = connection.execute(
        'SELECT contract_owner,contract_local_id FROM proofir_v3_contract_analysis_inputs '
        'WHERE owner_artifact_id=? ORDER BY ordinal', (artifact['artifactId'],)
    ).fetchall()
    assert rows == [(r['artifactRef'], r['localId']) for r in p['contractRefs']]
    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    assert recorded() == bundle


@pytest.mark.parametrize('mutation', ['swap-inputs', 'wrong-check', 'wrong-goal',
                                     'fresh-authority', 'source-proof', 'missing-replay',
                                     'embedded-freshness', 'wrong-environment'])
def test_rehashed_artifact_cannot_substitute_owners_or_upgrade_history(mutation):
    bundle = recorded()
    target = analysis(bundle)
    p = target['payload']
    if mutation == 'swap-inputs':
        p['contractRefs'].reverse()
    elif mutation == 'wrong-check':
        p['checkRunRefs'] = [p['replay']['productions'][0]['artifacts'][-1]['payload']['checkRunRefs'][0]]
    elif mutation == 'wrong-goal':
        p['result']['goalDigest'] = 'sha256:' + 'e' * 64
    elif mutation == 'fresh-authority':
        p['result']['authority'] = 'fresh-lean-check'
    elif mutation == 'source-proof':
        p['result']['sourceTheoremProof'] = 'checked'
    elif mutation == 'missing-replay':
        p.pop('replay')
    elif mutation == 'embedded-freshness':
        row = p['replay']['productions'][0]
        row['authority'] = 'fresh-lean-check'
        row['snapshotId'] = snapshot_identity(row)
    else:
        target['environmentRef'] = 'sha256:' + 'd' * 64
    rehash_artifact(target)
    with pytest.raises(ValueError):
        validate_envelope_batch(bundle['artifacts'])


@pytest.mark.parametrize('mutation', ['goal', 'pair', 'term', 'capture', 'memory',
                                     'output', 'missing-check', 'unresolved'])
def test_recording_rejects_unbound_or_unaccepted_relation_receipts(mutation):
    from ladon.real_bound_native_analysis_artifacts import recorded_comparison

    data = json.loads(FIXTURE.read_text())
    run = data['relationRun']
    inner = run['result']
    if mutation == 'goal':
        inner['goal']['proposition'] = 'True'
    elif mutation == 'pair':
        inner['leftPlanId'] = inner['rightPlanId']
    elif mutation == 'term':
        inner['term'] = 'by trivial'
    elif mutation == 'capture':
        inner['check']['capture']['capture']['source']['digest'] = 'sha256:' + 'c' * 64
    elif mutation in ('memory', 'output'):
        run['processReceipt'][mutation + 'Limited'] = True
    elif mutation == 'missing-check':
        inner['check'] = {}
    else:
        inner['status'] = 'unresolved'
    with pytest.raises(ValueError):
        recorded_comparison(data['productions'], run)


def test_native_batch_rejects_missing_relation_owner():
    bundle = recorded()
    ref = analysis(bundle)['payload']['checkRunRefs'][0]['artifactRef']
    with pytest.raises(ValueError):
        validate_envelope_batch([a for a in bundle['artifacts'] if a['artifactId'] != ref])


def test_offline_inspection_never_runs_a_checker(monkeypatch):
    from ladon import real_bound_native_analysis as live
    from ladon import real_bound_native_analysis_bundle as bundles

    def forbidden(*_args, **_kwargs):
        pytest.fail('offline inspection attempted fresh checking')

    monkeypatch.setattr(live, 'replay_real_bound', forbidden)
    monkeypatch.setattr(live, 'check_real_bound_relation', forbidden)
    result = bundles.inspect_comparison_bundle(recorded())
    assert result['status'] == 'validated-historical'
    assert result['authority'] == 'none'
    assert result['freshCheck'] is False
    assert result['evidenceAuthentication'] == 'not-established'


def install_replay(monkeypatch, *, unresolved=False, foreign=False):
    from ladon import real_bound_native_analysis as live
    from ladon import real_bound_native_production as production

    data = json.loads(FIXTURE.read_text())
    calls = []
    monkeypatch.setattr(production, '_current_source', lambda *_: None)

    def replay(value, root, *, timeout_seconds):
        calls.append(('admission', timeout_seconds))
        result = copy.deepcopy(data['productions'][1] if foreign else value)
        result['authority'] = 'fresh-lean-check'
        result['snapshotId'] = snapshot_identity(result)
        return result

    def relation(root, left, right, *, timeout_seconds):
        calls.append(('relation', timeout_seconds))
        result = copy.deepcopy(data['relationRun'])
        if unresolved:
            result['processReceipt']['memoryLimited'] = True
        return result

    monkeypatch.setattr(live, 'replay_real_bound', replay)
    monkeypatch.setattr(live, 'check_real_bound_relation', relation)
    return calls


def test_replay_runs_both_admissions_and_relation_with_one_budget(monkeypatch):
    from ladon.real_bound_native_analysis_bundle import replay_comparison_bundle

    calls = install_replay(monkeypatch)
    fresh = replay_comparison_bundle(recorded(), '/source', timeout_seconds=30)
    assert fresh['authority'] == 'fresh-source-predicate-scalar-and-relation-checks'
    assert [row[0] for row in calls] == ['admission', 'admission', 'relation']
    budgets = [row[1] for row in calls]
    assert 30 >= budgets[0] >= budgets[1] >= budgets[2] > 0
    assert analysis(fresh)['payload']['result']['authority'] == 'none'


def test_saved_success_cannot_override_a_resource_limited_fresh_replay(monkeypatch):
    from ladon.real_bound_native_analysis_bundle import replay_comparison_bundle

    install_replay(monkeypatch, unresolved=True)
    result = replay_comparison_bundle(recorded(), '/source')
    assert result['status'] == 'unresolved'
    assert result['relation'] is None
    assert 'artifacts' not in result


def test_fresh_replay_rejects_a_different_admitted_owner(monkeypatch):
    from ladon.real_bound_native_analysis_bundle import replay_comparison_bundle

    install_replay(monkeypatch, foreign=True)
    with pytest.raises(ValueError, match='owner|request|replay'):
        replay_comparison_bundle(recorded(), '/source')


def test_stale_source_stops_replay_before_a_worker(monkeypatch):
    from ladon import real_bound_native_analysis_bundle as bundles
    from ladon import real_bound_native_production as production

    calls = install_replay(monkeypatch)

    def stale(*_):
        raise ValueError('stale Real production source')

    monkeypatch.setattr(production, '_current_source', stale)
    with pytest.raises(ValueError, match='stale'):
        bundles.replay_comparison_bundle(recorded(), '/source')
    assert calls == []


def test_oversized_bundle_stops_before_any_replay(monkeypatch):
    from ladon.real_bound_native_analysis_bundle import replay_comparison_bundle

    calls = install_replay(monkeypatch)
    bundle = recorded()
    bundle['padding'] = 'x' * (32 * 1024**2)
    with pytest.raises(ValueError):
        replay_comparison_bundle(bundle, '/source')
    assert calls == []
