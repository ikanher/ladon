"""Unmocked mixed-edge, three-owner native chain qualification."""

import json
import os
import sqlite3
import time

import pytest
from test_real_bound_prefix_lean import FIXTURE, clean_root
from test_real_bound_prefix_live import admit

from ladon.proof_contract_cli import contract_main
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database

ALIAS = '''
namespace PrefixExamples
theorem narrowCopy (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    envelope f S n C → envelope (transport f) S n (K * C) := narrow n
end PrefixExamples
'''


def _admit_chain(root):
    paths = []
    for name in ('wide', 'narrow', 'narrowCopy'):
        value = admit(root, 'PrefixExamples.' + name, 'PrefixExamples.measure', [])
        path = root / (name + '.json')
        path.write_text(json.dumps(value))
        paths.append(path)
    return paths


def _check_chain(bundle):
    p = bundle['artifacts'][-1]['payload']
    assert p['rules'] == ['order-prefix-v1', 'identity-v1']
    assert p['result']['edgeCount'] == 2
    assert p['result']['authority'] == 'none'
    assert p['result']['endpointTheorem'] == 'not-checked'
    assert len({r['artifactRef'] for r in p['contractRefs']}) == 3
    artifacts = {a['artifactId']: a for a in bundle['artifacts']}
    edges = [artifacts[r['artifactRef']]['payload'] for r in p['edgeAnalysisRefs']]
    assert edges[0]['contractRefs'][1] == edges[1]['contractRefs'][0] == p['contractRefs'][1]
    assert len(p['checkRunRefs']) == 2
    return p


def _inspect_replay(root, saved, replayed, capsys):
    first = json.loads(saved.read_text())
    _check_chain(first)
    db = sqlite3.connect(':memory:')
    project_envelopes(db, first['artifacts'])
    validate_v3_database(db)
    capsys.readouterr()
    assert contract_main(['inspect-real-chain', '--input', str(saved)]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected['authority'] == 'none' and inspected['freshCheck'] is False
    assert contract_main(['replay-real-chain', '--input', str(saved), '--root', str(root),
                          '--output', str(replayed)]) == 0
    fresh = json.loads(replayed.read_text())
    _check_chain(fresh)
    assert fresh['authority'] == 'fresh-source-predicate-scalar-and-edge-checks'
    assert fresh['analysisRef'] != first['analysisRef']


@pytest.mark.skipif(os.environ.get('LADON_REAL_BOUND_LIVE_CHAIN') != '1',
                    reason='opt-in three-owner admission and two-edge native replay')
def test_public_mixed_chain_production_storage_and_replay(tmp_path, capsys):
    started = time.monotonic()
    clean_root(tmp_path)
    source = tmp_path / 'PrefixExamples.lean'
    source.write_text(FIXTURE.read_text() + ALIAS)
    paths = _admit_chain(tmp_path)
    admitted_at = time.monotonic()
    saved, replayed = tmp_path / 'chain.json', tmp_path / 'replayed.json'
    flags = [item for path in paths for item in ('--production', str(path))]
    assert contract_main(['propagate-real-bounds-proofir', *flags, '--rule', 'order-prefix-v1',
                          '--rule', 'identity-v1', '--root', str(tmp_path), '--output', str(saved)]) == 0
    produced_at = time.monotonic()
    _inspect_replay(tmp_path, saved, replayed, capsys)
    replayed_at = time.monotonic()
    source.write_text(FIXTURE.read_text() + ALIAS + '\n-- drift after complete chain\n')
    capsys.readouterr()
    assert contract_main(['replay-real-chain', '--input', str(saved), '--root', str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'
    with capsys.disabled():
        print(json.dumps({'admitSeconds': admitted_at - started,
                          'produceSeconds': produced_at - admitted_at,
                          'inspectSqliteReplaySeconds': replayed_at - produced_at,
                          'totalSeconds': time.monotonic() - started,
                          'bundleBytes': saved.stat().st_size, 'runDirectory': str(tmp_path)}))
