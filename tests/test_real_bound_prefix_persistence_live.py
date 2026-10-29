"""Opt-in unmocked native prefix save, SQLite, inspect and explicit replay gate."""

import json
import os
import sqlite3
import time

import pytest
from test_real_bound_prefix_lean import FIXTURE, clean_root
from test_real_bound_prefix_live import admit

from ladon.proof_contract_cli import contract_main
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database


@pytest.mark.skipif(os.environ.get('LADON_REAL_BOUND_LIVE_PREFIX_PERSISTENCE') != '1',
                    reason='opt-in fresh native prefix production and replay')
def test_public_prefix_native_production_and_replay(tmp_path, capsys):
    started = time.monotonic()
    clean_root(tmp_path)
    source = tmp_path / 'PrefixExamples.lean'
    source.write_text(FIXTURE.read_text())
    paths = []
    for name in ('higher', 'lower'):
        value = admit(tmp_path, 'PrefixExamples.Alternative.' + name,
                      'PrefixExamples.Alternative.measure', ['b0'])
        path = tmp_path / (name + '.json')
        path.write_text(json.dumps(value))
        paths.append(path)
    admitted_at = time.monotonic()
    saved, replayed = tmp_path / 'prefix.json', tmp_path / 'replayed.json'
    assert contract_main(['check-real-bound-prefix-proofir', '--stronger', str(paths[0]),
                          '--weaker', str(paths[1]), '--root', str(tmp_path), '--output', str(saved)]) == 0
    produced_at = time.monotonic()
    _inspect_and_replay(tmp_path, capsys, saved, replayed)
    replayed_at = time.monotonic()
    source.write_text(FIXTURE.read_text() + '\n-- drift after saved success\n')
    capsys.readouterr()
    assert contract_main(['inspect-real-prefix', '--input', str(saved)]) == 0
    assert json.loads(capsys.readouterr().out)['authority'] == 'none'
    assert contract_main(['replay-real-prefix', '--input', str(saved), '--root', str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'
    with capsys.disabled():
        print(json.dumps({'admitSeconds': admitted_at - started,
                          'produceSeconds': produced_at - admitted_at,
                          'replayInspectSqliteSeconds': replayed_at - produced_at,
                          'totalSeconds': time.monotonic() - started,
                          'bundleBytes': saved.stat().st_size,
                          'runDirectory': str(tmp_path)}))


def _inspect_and_replay(tmp_path, capsys, saved, replayed):
    first = json.loads(saved.read_text())
    payload = first['artifacts'][-1]['payload']
    assert first['authority'] == 'fresh-source-predicate-scalar-and-prefix-checks'
    assert payload['result']['relation'] == 'input-prefix-implies'
    assert payload['contractRefs'][0] != payload['contractRefs'][1]
    db = sqlite3.connect(':memory:')
    project_envelopes(db, first['artifacts'])
    validate_v3_database(db)
    capsys.readouterr()
    assert contract_main(['inspect', '--input', str(saved)]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected['authority'] == 'none' and inspected['freshCheck'] is False
    assert contract_main(['replay-real-prefix', '--input', str(saved), '--root', str(tmp_path),
                          '--output', str(replayed)]) == 0
    _fresh_claims(first, replayed)


def _fresh_claims(first, replayed):
    fresh = json.loads(replayed.read_text())
    assert fresh['authority'] == 'fresh-source-predicate-scalar-and-prefix-checks'
    assert fresh['analysisRef'] != first['analysisRef']
    result = fresh['artifacts'][-1]['payload']['result']
    assert result['authority'] == 'none' and result['relation'] == 'input-prefix-implies'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['paperNormBridge'] == 'unresolved'
