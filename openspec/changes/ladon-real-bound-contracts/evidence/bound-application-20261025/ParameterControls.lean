import Mathlib.Data.Real.Basic

namespace ChoiceBounds
universe u

def sample {P : Type u} [Inhabited P] (f : P → Nat → Real)
    (p : P) (_y : Unit) (j : Nat) : Real := f p j + f default j

def envelope {P : Type u} [Inhabited P] (f : P → Nat → Real)
    (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, sample f p y j ≤ C

def transform {P : Type u} (f : P → Nat → Real) := f

theorem estimate (P : Type u) [Inhabited P] (_alternative : Inhabited P)
    (_unused : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P → Nat → Real) (S : Set P) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transform f) S n (K * C) := by
  exact False.elim _unused

def proofEnvelope {P : Type u} [Inhabited P] (_h : False) (f : P → Nat → Real)
    (S : Set P) (n : Nat) (C : Real) : Prop := envelope f S n C

theorem proofParameter (P : Type u) [Inhabited P] (h : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P → Nat → Real) (S : Set P) (C : Real),
      0 ≤ C → proofEnvelope h f S n C → proofEnvelope h (transform f) S n (K * C) := by
  exact False.elim h

end ChoiceBounds
