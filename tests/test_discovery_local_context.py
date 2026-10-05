"""Caller context must survive installed discovery and fail before target execution."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.proof_search_cli import build_proof_search_parser
from ladon.proof_search_discovery_cli import dispatch_discover
from ladon.proof_search_index import ProofSearchIndexError

FIXTURE = Path(__file__).parent / 'fixtures/lean_integration'


@pytest.mark.parametrize('locals_', [[':Nat'], ['x:'], ['x:Nat', 'x:Nat'],
                                     ['x:Nat\n'], ['x:Nat := 0'], ['x:Nat); theorem injected : True := by trivial']])
def test_invalid_local_context_is_rejected_before_toolchain_probe(monkeypatch, locals_):
    from ladon import proof_search_discovery_cli as owner

    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid local context reached target toolchain execution')

    monkeypatch.setattr(owner, 'resolve_toolchain_context', forbidden)
    argv = ['discover', '--module', 'Main', '--goal', 'True', '--candidate', 'id']
    for row in locals_:
        argv.extend(['--local', row])
    args = build_proof_search_parser().parse_args(argv)
    with pytest.raises(ProofSearchIndexError):
        dispatch_discover(args, Path('/missing-repository'))


@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean fixture unavailable')
@pytest.mark.parametrize(('locals_', 'goal', 'candidate', 'status', 'residuals'), [
    (['value:Nat', 'h:value = value'], 'value = value', 'LadonFixture.fixtureIdentity', 'accepted', []),
    (['P:Prop', 'h:P'], 'P', 'id', 'accepted', []),
    (['P:Prop', 'Q:Prop', 'h:P'], 'P ∧ Q', 'And.intro', 'applicable-with-residuals', ['Q']),
])
def test_installed_discovery_preserves_context_and_exact_application(tmp_path, locals_, goal, candidate, status, residuals):
    argv = _context_command(tmp_path, locals_, goal, candidate)
    completed = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, timeout=90, check=False)
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    expected = [dict(zip(('name', 'type'), row.split(':', 1), strict=True)) for row in locals_]
    assert payload['request']['localContext'] == expected
    checked = payload['candidates'][0]['check']
    assert checked['status'] == status, checked
    assert [row['typeDisplay'] for row in checked['residualPremises']] == residuals
    assert checked['evidenceReceipt']['executionBinding'] == 'explicit-pinned'
    assert checked['evidenceReceipt']['subject']['localContext'] == expected
    _assert_scratch(checked, status)


def _context_command(tmp_path, locals_, goal, candidate):
    lean = Path(subprocess.check_output(['elan', 'which', 'lean'], cwd=FIXTURE, text=True).strip())
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    argv = [console, 'proof-search', 'discover', '--repo-root', str(FIXTURE),
            '--module', 'LadonFixture', '--goal', goal, '--candidate', candidate,
            '--toolchain-mode', 'explicit', '--lean-path', str(lean), '--lake-path', str(lean.with_name('lake')),
            '--scratch-mode', 'advisory', '--projection', 'audit', '--format', 'json',
            '--evidence-store', str(tmp_path / 'evidence.sqlite')]
    for row in locals_:
        argv.extend(['--local', row])
    return argv


def _assert_scratch(checked, status):
    if status == 'accepted':
        assert checked['scratch']['status'] == 'compiled', checked['scratch']
        assert checked['scratch']['source'].startswith('import LadonFixture\n')


@pytest.mark.parametrize(('constant', 'notation'), [('Real', 'ℝ'), ('Nat', 'ℕ'), ('Int', 'ℤ')])
def test_printed_notation_does_not_reject_an_exact_structural_constant_type(constant, notation):
    from ladon.semantic_local_context import validate_observed_local_context

    row = {'localId': 'local:0', 'userName': 'epsilon', 'binderInfo': 'default',
           'typeDisplay': notation, 'typeStructural': f'Lean.Expr.const `{constant} []',
           'valueDisplay': '', 'valueStructural': '', 'dependencies': [], 'origin': 'goal-introduced'}
    request = [{'name': 'epsilon', 'type': constant}]
    validate_observed_local_context([row], request)
    row['typeStructural'] = 'Lean.Expr.const `Bool []'
    with pytest.raises(ValueError, match='mismatched type'):
        validate_observed_local_context([row], request)
    row.update(typeStructural=f'Lean.Expr.const `{constant} []', typeDisplay='Bool')
    with pytest.raises(ValueError, match='mismatched type'):
        validate_observed_local_context([row], request)


def test_unicode_type_spelling_cannot_hide_a_wrong_structural_constant():
    from ladon.semantic_local_context import validate_observed_local_context

    row = {'localId': 'local:0', 'userName': 'epsilon', 'binderInfo': 'default',
           'typeDisplay': 'ℝ', 'typeStructural': 'Lean.Expr.const `Bool []',
           'valueDisplay': '', 'valueStructural': '', 'dependencies': [], 'origin': 'goal-introduced'}
    with pytest.raises(ValueError, match='structurally mismatched'):
        validate_observed_local_context([row], [{'name': 'epsilon', 'type': 'ℝ'}])


def test_real_projected_local_type_requires_its_exact_dependency():
    from ladon.semantic_local_context import validate_observed_local_context

    # Lean serialization copied from the diagnostic-only installed failure
    # (hNonFull); this is a field projection over the earlier `point` fvar.
    point = {'localId': 'local:0', 'userName': 'point', 'binderInfo': 'Lean.BinderInfo.default',
             'typeDisplay': 'Mf.DP.PoissonFixedEpochPoint',
             'typeStructural': 'Lean.Expr.const `Mf.DP.PoissonFixedEpochPoint []',
             'valueDisplay': '', 'valueStructural': '', 'dependencies': [],
             'origin': 'goal-introduced'}
    projected = {
        'localId': 'local:4', 'userName': 'hNonFull',
        'binderInfo': 'Lean.BinderInfo.default',
        'typeDisplay': 'point.epoch < point.horizon',
        'typeStructural': (
            'Lean.Expr.app (Lean.Expr.app (Lean.Expr.app (Lean.Expr.app '
            '(Lean.Expr.const `LT.lt [Lean.Level.zero]) (Lean.Expr.const `Nat [])) '
            '(Lean.Expr.const `instLTNat [])) (Lean.Expr.app '
            '(Lean.Expr.const `Mf.DP.PoissonFixedEpochPoint.epoch []) '
            '(Lean.Expr.fvar (Lean.Name.mkNum `_uniq 2)))) (Lean.Expr.app '
            '(Lean.Expr.const `Mf.DP.PoissonFixedEpochPoint.horizon []) '
            '(Lean.Expr.fvar (Lean.Name.mkNum `_uniq 2)))'
        ),
        'valueDisplay': '', 'valueStructural': '', 'dependencies': ['local:0'],
        'origin': 'goal-introduced'}
    requested = [
        {'name': 'point', 'type': 'Mf.DP.PoissonFixedEpochPoint'},
        {'name': 'hNonFull', 'type': 'point.epoch < point.horizon'},
    ]

    validate_observed_local_context([point, projected], requested)

    # Keep the structural expression while claiming an unrelated dependency.
    projected['dependencies'] = ['local:1']
    with pytest.raises(ValueError):
        validate_observed_local_context([point, projected], requested)



@pytest.mark.skipif(shutil.which('lake') is None, reason='pinned Lean fixture unavailable')
def test_installed_discovery_accepts_a_real_record_projection_hypothesis(tmp_path):
    locals_ = [
        'point:LadonFixture.ProjectionPoint',
        'hNonFull:point.epoch < point.horizon',
    ]
    argv = _context_command(tmp_path, locals_, 'point.epoch < point.horizon', 'id')
    completed = subprocess.run(
        argv, cwd=tmp_path, capture_output=True, text=True, timeout=90, check=False
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    expected = [
        {'name': 'point', 'type': 'LadonFixture.ProjectionPoint'},
        {'name': 'hNonFull', 'type': 'point.epoch < point.horizon'},
    ]
    assert payload['request']['localContext'] == expected
    checked = payload['candidates'][0]['check']
    assert checked['status'] == 'accepted', checked
    assert checked['evidenceReceipt']['subject']['localContext'] == expected
    _assert_scratch(checked, 'accepted')

