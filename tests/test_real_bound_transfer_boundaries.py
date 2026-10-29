"""Additional kernel boundaries for exact middle applications and dependent data."""

import json

import pytest
from test_real_bound_prefix_lean import lean
from test_real_bound_transfer_lean import check, concrete_goal
from test_real_bound_transfer_lean import (
    transfer_project as transfer_project,  # noqa: PLC0414 -- pytest fixture
)


@pytest.mark.parametrize('old,new', [
    ('(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S (n+7) (K*C)',
     '(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound f S (n+7) (K*C)'),
    ('(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S (n+7) (K*C)',
     '(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) Set.univ (n+7) (K*C)'),
    ('(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S (n+7) (K*C)',
     '(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S n (K*C)'),
    ('(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S (n+7) (K*C)',
     '(0 ≤ L ∧ (0 ≤ K*C → TransferExamples.bound (TransferExamples.twice f) S (n+7) C'),
    ('(0 ≤ L ∧ (0 ≤ K*C →', '(0 ≤ L ∧ (True →'),
    ('TransferExamples.bound f S ((n+7)+4) C →',
     'TransferExamples.bound (TransferExamples.twice f) S ((n+7)+4) C →'),
])
def test_changed_middle_or_original_input_is_not_the_checked_goal(transfer_project, old, new):
    target = concrete_goal().replace(old, new)
    assert target != concrete_goal()
    run = check(transfer_project, expected=target)
    assert not run.succeeded


DEPENDENT = '''
namespace DependentTransfers
noncomputable def measureD (n : Nat) (g : Fin n → Real) (f : Real) (_p : Nat) (_y : Unit) (_j : Nat) : Real :=
  if ∃ i, 0 < g i then f else 0
def boundD (n : Nat) (g : Fin n → Real) (f : Real) (S : Set Nat) (r : Nat) (C : Real) : Prop :=
  ∀ j ≤ r, ∀ p ∈ S, ∀ y : Unit, measureD n g f p y j ≤ C
theorem dependentOrder (n : Nat) (g : Fin n → Real) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    boundD n g f S (n+4) C → boundD n g (TransferExamples.identity f) S n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h j hj p hp y
  simpa only [one_mul, TransferExamples.identity] using
    h j (Nat.le_trans hj (Nat.le_add_right n 4)) p hp y
def measureP (_h : True) (f : Real) (_p : Nat) (_y : Unit) (_j : Nat) : Real := f
def boundP (h : True) (f : Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measureP h f p y j ≤ C
theorem proofDependent (h : True) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    boundP h f S (n+4) C → boundP h (TransferExamples.identity f) S n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h j hj p hp y
  simpa only [one_mul, TransferExamples.identity] using
    h j (Nat.le_trans hj (Nat.le_add_right n 4)) p hp y
end DependentTransfers
'''


@pytest.mark.parametrize('name,roles,diagnostic', [
    ('dependentOrder', '[0,3,4,5,2,6]', 'dependent data type'),
    ('proofDependent', '[1,3,4,5,2,6]', 'proof'),
])
def test_unsupported_dependent_contexts_are_not_dropped(transfer_project, name, roles, diagnostic):
    root, prefix, _types = transfer_project
    query = (prefix + DEPENDENT + '\nopen Lean Elab Command\n'
             'run_elab do\n'
             f'  let value ← Ladon.RealBoundBinding.observedTypeJson ``DependentTransfers.{name}\n'
             '  logInfo m!"DEPENDENT_EXPR:{value.compress}"\n')
    (root / 'DependentQuery.lean').write_text(query)
    observed = lean(root, 'DependentQuery.lean')
    assert observed.succeeded, observed.stdout + observed.stderr
    values = [line.split('DEPENDENT_EXPR:', 1)[1] for line in observed.stdout.splitlines()
              if 'DEPENDENT_EXPR:' in line]
    assert len(values) == 1
    arg = json.dumps('DependentTransfers.' + name) + ' ' + json.dumps(values[0])
    source = prefix + DEPENDENT + f'\n#check (ladon_real_bound_compose% {arg} {arg} {roles} 4 4)\n'
    (root / 'DependentCheck.lean').write_text(source)
    result = lean(root, 'DependentCheck.lean')
    assert not result.succeeded
    assert diagnostic in result.stdout + result.stderr
