import Mathlib.Data.Real.Basic

namespace DependentBounds
universe u

def sample {P : Type u} [Inhabited P] (f : P → Nat → Real)
    (p : P) (_y : Unit) (j : Nat) : Real := f p j + f default j

def wrongSample {P : Type u} [Inhabited P] (f : P → Nat → Real)
    (p : P) (y : Unit) (j : Nat) : Real := sample f p y j + 1

def envelope {P : Type u} [Inhabited P] (f : P → Nat → Real)
    (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, sample f p y j ≤ C

def transform {P : Type u} (f : P → Nat → Real) := f

theorem estimate (P : Type u) [Inhabited P] (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P → Nat → Real) (S : Set P) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transform f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, transform] using h

-- No prefix-order law exists for this predicate. False must not leak into its law goal.
def exactOrder {P : Type u} [Inhabited P] (f : P → Nat → Real)
    (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ p ∈ S, ∀ y : Unit, sample f p y n ≤ C

theorem misleading (P : Type u) [Inhabited P] (_unused : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P → Nat → Real) (S : Set P) (C : Real),
      0 ≤ C → exactOrder f S n C → exactOrder (transform f) S n (K * C) := by
  exact False.elim _unused

end DependentBounds
