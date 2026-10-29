"""Public live qualification helpers; no mocked admission or relation evidence."""

import copy
import json
import sqlite3
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from test_real_bound_comparison_persistence import analysis, rehash_artifact

from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import validate_envelope_batch
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_production import produce_real_bound
from ladon.real_bound_observation import observe_bound_snapshot

FIXTURES = Path(__file__).parent / 'fixtures/real_bound_native'
TERMS = {'predicate-admission': 'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
         'scalar-semantics': 'by intros; exact ⟨rfl, rfl, rfl⟩'}


def phase(root, label, started):
    row = {'phase': label, 'elapsedSeconds': time.monotonic() - started}
    with (root / 'phases.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')


def admit(root, name, measure='TransferExamples.measure', arguments=()):
    started = time.monotonic()
    snapshot = produce_formal_snapshot(root, 'TaskExamples.lean', 'TaskExamples', name)
    observed = observe_bound_snapshot(snapshot, root)
    plan = plan_real_bound(plan_bound_prefix(observed, {'declaration': measure, 'arguments': list(arguments)}))
    result = produce_real_bound(root, plan, TERMS, timeout_seconds=180)
    path = root / (name + '.json')
    path.write_text(json.dumps(result))
    phase(root, 'admit:' + name, started)
    assert result['status'] == 'admitted', result.get('check')
    return path


def cli(root, label, args, expected=0):
    started = time.monotonic()
    output = root / (label + '.json')
    captured = StringIO()
    with redirect_stdout(captured):
        code = contract_main([*args, '--output', str(output)])
    phase(root, label, started)
    report = output.read_text() if output.exists() else captured.getvalue()
    assert code == expected, report[:4000]
    return json.loads(report)


def assert_stored(bundle, owners):
    payload = analysis(bundle)['payload']
    validate_envelope_batch(bundle['artifacts'])
    db = sqlite3.connect(':memory:')
    project_envelopes(db, bundle['artifacts'])
    validate_v3_database(db)
    key = (analysis(bundle)['artifactId'],)
    assert db.execute('SELECT COUNT(*) FROM proofir_v3_contract_analysis_inputs WHERE owner_artifact_id=?',
                      key).fetchone() == (owners,)
    assert db.execute('SELECT COUNT(*) FROM proofir_v3_contract_analysis_derivations WHERE owner_artifact_id=?',
                      key).fetchone() == (1,)
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    assert payload['derivationGoalRef']['artifactRef'] == payload['checkRunRefs'][0]['artifactRef']
    assert payload['result']['authority'] == 'none'
    assert payload['result']['paperNormBridge'] == 'unresolved'


def assert_mutations_rejected(bundle):
    changes = [('scope', 'uniform-estimate'), ('transferPremises', 'proved'),
               ('coefficientUniformity', 'proved'), ('authority', 'fresh-lean-check'),
               ('sourceTheoremProof', 'checked'), ('paperNormBridge', 'checked')]
    for field, value in changes:
        changed = copy.deepcopy(bundle)
        target = analysis(changed)
        target['payload']['result'][field] = value
        rehash_artifact(target)
        with pytest.raises(ValueError):
            validate_envelope_batch(changed['artifacts'])
    for mutation in ('missing-check', 'goal', 'duplicate', 'reverse'):
        changed = copy.deepcopy(bundle)
        target = analysis(changed)
        _mutate_owner(changed, target['payload'], mutation)
        rehash_artifact(target)
        with pytest.raises(ValueError):
            validate_envelope_batch(changed['artifacts'])


def _mutate_owner(bundle, payload, mutation):
    if mutation == 'missing-check':
        owner = payload['checkRunRefs'][0]['artifactRef']
        bundle['artifacts'] = [a for a in bundle['artifacts'] if a['artifactId'] != owner]
    elif mutation == 'goal':
        payload['derivationGoalRef'] = payload['contractRefs'][0]
    elif mutation == 'duplicate':
        payload['contractRefs'].append(payload['contractRefs'][0])
    else:
        payload['contractRefs'].reverse()


def assert_historical(root, name, capsys):
    assert contract_main(['inspect', '--input', str(root / (name + '.json'))]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'validated-historical'
    assert result['authority'] == 'none' and result['freshCheck'] is False
    assert result['evidenceAuthentication'] == 'not-established'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['coefficientUniformity'] == 'not-inferred'


def check_replay(root, name, bundle, owners, capsys):
    capsys.readouterr()
    assert_historical(root, name, capsys)
    replay = cli(root, name + '-replay', ['replay-real-' + name, '--input', str(root / (name + '.json')),
                                         '--root', str(root), '--timeout-seconds', '600'])
    assert_stored(replay, owners)
    assert replay['authority'] == bundle['authority']
    assert replay['analysisRef'] != bundle['analysisRef']
    assert analysis(replay)['payload']['checkRunRefs'] != analysis(bundle)['payload']['checkRunRefs']
    return replay


def compare(root, label, left, right, resolved):
    result = cli(root, 'compare-' + label, ['compare-real-bounds', '--left', str(left), '--right', str(right),
                                         '--root', str(root), '--timeout-seconds', '600'], 0 if resolved else 2)
    assert result['status'] == ('resolved' if resolved else 'unresolved')
    assert result['contextMatch'] is resolved
    assert result['relation'] == ('equivalent' if resolved else None)
    assert result['paperNormBridge'] == 'unresolved'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['mathematicalFalsity'] == 'not-established'


def stale_checks(root, source, capsys):
    source.write_text(source.read_text() + '\n-- qualification source drift\n')
    for name in ('transfer', 'coefficient'):
        capsys.readouterr()
        assert_historical(root, name, capsys)
        result = cli(root, name + '-stale', ['replay-real-' + name, '--input', str(root / (name + '.json')),
                                            '--root', str(root)], 2)
        assert result['status'] == 'invalid'


def assert_not_chain_edge(bundle):
    from ladon.real_bound_native_chain_artifacts import recorded_chain

    with pytest.raises(ValueError, match='single-edge|unsupported|comparison'):
        recorded_chain([bundle])
