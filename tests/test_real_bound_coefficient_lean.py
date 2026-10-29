"""Kernel checks for source-derived, pointwise coefficient weakening."""

import json
import shutil
from pathlib import Path

import pytest
from test_real_bound_prefix_lean import SOURCES, clean_root, lean

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/CoefficientExamples.lean'
NAMES = ('ordinary', 'commuted', 'pointwise', 'Parameterized.estimate', 'conditional')
FULL_NAMES = ['CoefficientExamples.' + name for name in NAMES]


@pytest.fixture(scope='module')
def coefficient_project(tmp_path_factory):
    root = tmp_path_factory.mktemp('real-coefficient-rules')
    clean_root(root)
    modules = ['LadonRealBound', 'LadonRealBoundBinding', 'LadonRealBoundScalars']
    if (SOURCES / 'LadonRealBoundCoefficient.lean').exists():
        modules.append('LadonRealBoundCoefficient')
    for name in modules:
        shutil.copy2(SOURCES / (name + '.lean'), root / (name + '.lean'))
        run = lean(root, name + '.lean', output=f'.lake/build/lib/lean/{name}.olean')
        assert run.succeeded, run.stdout + run.stderr
    prefix = ''.join('import ' + name + '\n' for name in modules) + FIXTURE.read_text()
    query = (prefix + '\nopen Lean Elab Command\n'
             'elab "#coefficient_type " target:str : command => do\n'
             '  liftTermElabM do\n'
             '    let value ← Ladon.RealBoundBinding.observedTypeJson target.getString.toName\n'
             '    logInfo m!"COEFFICIENT_EXPR:{value.compress}"\n')
    query += '\n'.join('#coefficient_type ' + json.dumps(name) for name in FULL_NAMES)
    (root / 'Query.lean').write_text(query)
    run = lean(root, 'Query.lean')
    assert run.succeeded, run.stdout + run.stderr
    types = [line.split('COEFFICIENT_EXPR:', 1)[1] for line in run.stdout.splitlines()
             if 'COEFFICIENT_EXPR:' in line]
    assert len(types) == len(FULL_NAMES)
    return root, prefix, dict(zip(FULL_NAMES, types, strict=True))


def check(project, name, *, admission=None, scalar=None, stale=False, expected=None):
    root, prefix, types = project
    full = 'CoefficientExamples.' + name
    expression = types[full]
    if stale:
        expression = expression.replace('"const":"Nat"', '"const":"Int"', 1)
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    guard_index = 6 if name == 'conditional' else 5
    args = f'{quote(full)} {quote(expression)} {guard_index}'
    measure = 'CoefficientExamples.measure'
    indices = ''
    if name == 'Parameterized.estimate':
        measure, indices = 'CoefficientExamples.Parameterized.measure', '1'
    elif name == 'conditional':
        measure, indices = 'CoefficientExamples.proofMeasure', '0'
    predicate_law = f'ladon_bound_admission% {quote(full)} {quote(expression)} {quote(measure)} [{indices}]'
    admission = admission or 'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
    scalar = scalar or ('by intros; exact ⟨rfl, rfl, mul_comm _ _⟩' if name == 'commuted'
                        else 'by intros; exact ⟨rfl, rfl, rfl⟩')
    body = (f'by\n  have admitted : ({predicate_law}) := ({admission})\n'
            f'  have scalars : (ladon_scalar_admission% {args}) := ({scalar})\n'
            f'  exact ladon_real_bound_coefficient_proof% {args} admitted scalars\n')
    goal = expected or f'ladon_real_bound_coefficient% {args}'
    (root / 'Check.lean').write_text(prefix + '\nexample : (' + goal + ') := ' + body)
    return lean(root, 'Check.lean')


@pytest.mark.parametrize('name', NAMES[:4])
def test_source_coefficient_rule_checks_actual_products_and_scope(coefficient_project, name):
    run = check(coefficient_project, name)
    assert run.succeeded, run.stdout + run.stderr


def test_goal_retains_original_coefficient_dependent_predicate_and_object(coefficient_project):
    expected = ('∀ (n : Nat) (K : Real) (f : Nat → Real) (S : Set Nat) (C L : Real), '
                'K ≤ L → 0 ≤ C → '
                'CoefficientExamples.Parameterized.bound K (CoefficientExamples.Parameterized.operator K f) S n (K*C) → '
                'CoefficientExamples.Parameterized.bound K (CoefficientExamples.Parameterized.operator K f) S n (L*C)')
    run = check(coefficient_project, 'Parameterized.estimate', expected=expected)
    assert run.succeeded, run.stdout + run.stderr
    changed = expected.rsplit('CoefficientExamples.Parameterized.bound K', 1)
    wrong = 'CoefficientExamples.Parameterized.bound L'.join(changed)
    run = check(coefficient_project, 'Parameterized.estimate', expected=wrong)
    assert not run.succeeded


@pytest.mark.parametrize('change', ['stale', 'admission', 'scalar'])
def test_source_and_both_laws_are_required(coefficient_project, change):
    options = {'stale': True} if change == 'stale' else {change: 'by trivial'}
    run = check(coefficient_project, 'ordinary', **options)
    assert not run.succeeded


def test_propositional_product_equality_cannot_be_replaced_by_rfl(coefficient_project):
    run = check(coefficient_project, 'commuted', scalar='by intros; exact ⟨rfl, rfl, rfl⟩')
    assert not run.succeeded


def test_inherited_proof_dependencies_are_rejected(coefficient_project):
    run = check(coefficient_project, 'conditional')
    assert not run.succeeded
    assert 'proof' in run.stdout.lower()


@pytest.mark.parametrize('guards', ['K ≤ L →', '0 ≤ C →', 'L ≤ K → 0 ≤ C →'])
def test_neither_sign_nor_direction_can_be_dropped(coefficient_project, guards):
    expected = ('∀ (n : Nat) (K f : Real) (S : Set Nat) (C L : Real), ' + guards +
                ' CoefficientExamples.bound (CoefficientExamples.operator f) S n (K*C) → '
                'CoefficientExamples.bound (CoefficientExamples.operator f) S n (L*C)')
    run = check(coefficient_project, 'ordinary', expected=expected)
    assert not run.succeeded
