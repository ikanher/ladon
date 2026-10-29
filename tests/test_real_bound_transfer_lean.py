"""Actual source-derived composition with explicit, unproved transfer premises."""

import json
import shutil
from pathlib import Path

import pytest
from test_real_bound_prefix_lean import SOURCES, clean_root, lean

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/TransferExamples.lean'
NAMES = ['first', 'second', 'incompatible', 'Functions.estimate']


@pytest.fixture(scope='module')
def transfer_project(tmp_path_factory):
    root = tmp_path_factory.mktemp('real-transfer-rules')
    clean_root(root)
    modules = ['LadonRealBound', 'LadonRealBoundBinding', 'LadonRealBoundScalars', 'LadonRealBoundComposition']
    if (SOURCES / 'LadonRealBoundTransfer.lean').exists():
        modules.append('LadonRealBoundTransfer')
    for name in modules:
        shutil.copy2(SOURCES / (name + '.lean'), root / (name + '.lean'))
        run = lean(root, name + '.lean', output=f'.lake/build/lib/lean/{name}.olean')
        assert run.succeeded, run.stdout + run.stderr
    prefix = ''.join('import ' + name + '\n' for name in modules) + FIXTURE.read_text()
    query = (prefix + '\nopen Lean Elab Command\n'
             'elab "#transfer_type " target:str : command => do\n'
             '  liftTermElabM do\n'
             '    let value ← Ladon.RealBoundBinding.observedTypeJson target.getString.toName\n'
             '    logInfo m!"TRANSFER_EXPR:{value.compress}"\n')
    query += '\n'.join('#transfer_type ' + json.dumps('TransferExamples.' + name) for name in NAMES)
    (root / 'Query.lean').write_text(query)
    run = lean(root, 'Query.lean')
    assert run.succeeded, run.stdout + run.stderr
    types = [line.split('TRANSFER_EXPR:', 1)[1] for line in run.stdout.splitlines() if 'TRANSFER_EXPR:' in line]
    assert len(types) == len(NAMES)
    return root, prefix, dict(zip(NAMES, types, strict=True))


def check(project, first='first', second='second', *, stale=False, wrong_loss=False, scalar=None, expected=None):
    root, prefix, types = project
    q = lambda s: json.dumps(s, ensure_ascii=False)
    left = types[first].replace('"const":"Nat"', '"const":"Int"', 1) if stale else types[first]
    roles, guard = ('[1,3,4,5,2,6]', 6) if first.startswith('Functions.') else ('[0,2,3,4,1,5]', 5)
    loss_a, loss_b = (0, 0) if first.startswith('Functions.') else (4, 7)
    if wrong_loss:
        loss_b += 1
    a = f'{q("TransferExamples." + first)} {q(left)}'
    b = f'{q("TransferExamples." + second)} {q(types[second])}'
    args = f'{a} {b} {roles} {loss_a} {loss_b}'
    scalar = scalar or 'by intros; exact ⟨rfl, rfl, rfl⟩'
    body = (f'by\n  have sa : (ladon_scalar_admission% {a} {guard}) := ({scalar})\n'
            f'  have sb : (ladon_scalar_admission% {b} {guard}) := ({scalar})\n'
            f'  exact ladon_real_bound_compose_proof% {args} sa sb\n')
    goal = expected or f'ladon_real_bound_compose% {args}'
    (root / 'Check.lean').write_text(prefix + f'\nexample : ({goal}) := ' + body)
    return lean(root, 'Check.lean')


@pytest.mark.parametrize('first,second', [('first', 'second'), ('Functions.estimate', 'Functions.estimate')])
def test_source_composition_across_unrelated_objects(transfer_project, first, second):
    run = check(transfer_project, first, second)
    assert run.succeeded, run.stdout + run.stderr


def concrete_goal():
    return ('∀ (n : Nat) (K f : Real) (S : Set Nat) (C L : Real), '
            '(0 ≤ K ∧ (0 ≤ C → TransferExamples.bound f S ((n+7)+4) C → '
            'TransferExamples.bound (TransferExamples.twice f) S (n+7) (K*C))) → '
            '(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S (n+7) (K*C) → '
            'TransferExamples.bound (TransferExamples.thrice (TransferExamples.twice f)) S n (L*(K*C)))) → '
            'Ladon.RealBound.TransferAt TransferExamples.bound TransferExamples.bound f '
            '(TransferExamples.thrice (TransferExamples.twice f)) S ((n+7)+4) n C (L*K)')


def test_goal_names_both_premises_exact_middle_and_outer_composite(transfer_project):
    run = check(transfer_project, expected=concrete_goal())
    assert run.succeeded, run.stdout + run.stderr


@pytest.mark.parametrize('replacement', ['source', 'loss', 'scalar', 'predicate'])
def test_invalid_source_or_composition_is_rejected(transfer_project, replacement):
    kwargs = {'stale': True} if replacement == 'source' else {}
    if replacement == 'loss':
        kwargs['wrong_loss'] = True
    if replacement == 'scalar':
        kwargs['scalar'] = 'by trivial'
    if replacement == 'predicate':
        kwargs['second'] = 'incompatible'
    run = check(transfer_project, **kwargs)
    assert not run.succeeded


@pytest.mark.parametrize('old,new', [
    ('0 ≤ K ∧', 'True ∧'), ('0 ≤ L ∧', 'True ∧'), ('0 ≤ C →', 'True →'),
    ('(L*(K*C))', '(L*C)'), (' S ((n+7)+4) n C (L*K)', ' S ((n+7)+4) n C K'),
    ('(TransferExamples.thrice (TransferExamples.twice f)) S ((n+7)+4)', 'f S ((n+7)+4)'),
])
def test_changed_guards_scale_or_endpoint_cannot_match_checked_goal(transfer_project, old, new):
    expected = concrete_goal().replace(old, new)
    assert expected != concrete_goal()
    run = check(transfer_project, expected=expected)
    assert not run.succeeded
