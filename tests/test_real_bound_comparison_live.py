"""Opt-in public CLI qualification with two distinct current Mathlib-backed owners."""

import json
import os
import sqlite3
import time
from pathlib import Path

import pytest
from test_real_bound_relation_macro import source_with_alias

from ladon.derivative_prefix import plan_derivative_prefix
from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_slice import pinned_toolchain
from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.real_bound_native_analysis_codec import decode_replay
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_production import produce_real_bound
from ladon.real_bound_observation import observe_bound_snapshot


def _admit_distinct(root):
    terms = {'predicate-admission':
             'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
             'scalar-semantics': 'by intros; exact ⟨rfl, rfl, rfl⟩'}
    paths = []
    for name in ('ordinary', 'ordinaryCopy'):
        snapshot = produce_formal_snapshot(root, 'ScalarExamples.lean', 'ScalarExamples',
                                           'ScalarExamples.' + name)
        plan = plan_real_bound(plan_derivative_prefix(observe_bound_snapshot(snapshot, root)))
        production = produce_real_bound(root, plan, terms, timeout_seconds=180)
        assert production['status'] == 'admitted'
        path = root / (name + '.json')
        path.write_text(json.dumps(production))
        paths.append(path)
    return paths


@pytest.mark.skipif(os.environ.get('LADON_REAL_BOUND_LIVE_PERSISTENCE') != '1',
                    reason='opt-in multi-minute fresh Lean persistence/replay gate')
def test_live_cli_comparison_history_sqlite_and_explicit_replay(tmp_path, capsys):
    started = time.monotonic()
    library_root = Path(os.environ['LADON_MATHLIB_TEST_ROOT']).resolve()
    context = pinned_toolchain(library_root)
    (tmp_path / 'lean-toolchain').write_text((library_root / 'lean-toolchain').read_text())
    (tmp_path / '.lake/build/lib/lean').mkdir(parents=True)
    for index, library in enumerate(context.library_roots):
        target = tmp_path / f'.lake/packages/import{index}/.lake/build/lib/lean'
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    (tmp_path / 'ScalarExamples.lean').write_text(source_with_alias())
    left, right = _admit_distinct(tmp_path)
    admitted_at = time.monotonic()
    saved, replayed = tmp_path / 'comparison.json', tmp_path / 'replayed.json'
    assert contract_main(['compare-real-bounds-proofir', '--left', str(left), '--right', str(right),
                          '--root', str(tmp_path), '--output', str(saved)]) == 0
    produced_at = time.monotonic()
    first = json.loads(saved.read_text())
    artifact = first['artifacts'][-1]
    assert artifact['payload']['contractRefs'][0] != artifact['payload']['contractRefs'][1]
    assert first['authority'] == 'fresh-source-predicate-scalar-and-relation-checks'
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, first['artifacts'])
    validate_v3_database(connection)
    capsys.readouterr()
    assert contract_main(['inspect', '--input', str(saved)]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected['authority'] == 'none' and inspected['freshCheck'] is False
    assert contract_main(['replay-real-comparison', '--input', str(saved),
                          '--root', str(tmp_path), '--output', str(replayed)]) == 0
    fresh = json.loads(replayed.read_text())
    assert fresh['authority'] == 'fresh-source-predicate-scalar-and-relation-checks'
    assert fresh['artifacts'][-1]['payload']['result']['authority'] == 'none'
    assert fresh['analysisRef'] != first['analysisRef']
    productions, run = decode_replay(fresh['artifacts'][-1]['payload']['replay'])
    peaks = [run['processReceipt']['peakRssBytes']]
    peaks += [row['check']['processReceipt']['peakRssBytes'] for row in productions]
    capsys.readouterr()
    with capsys.disabled():
        print(json.dumps({'admitSeconds': admitted_at - started,
                          'compareSeconds': produced_at - admitted_at,
                          'replayAndInspectSeconds': time.monotonic() - produced_at,
                          'totalSeconds': time.monotonic() - started,
                          'maxWorkerPeakRssBytes': max(peaks),
                          'bundleBytes': saved.stat().st_size}))
