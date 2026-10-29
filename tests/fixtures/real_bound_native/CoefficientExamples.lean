import Mathlib.Data.Real.Basic

namespace CoefficientExamples
noncomputable section

def measure (f : Real) (_p : Nat) (_y : Unit) (_j : Nat) : Real := f
def bound (f : Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measure f p y j ≤ C
def operator (f : Real) := f

theorem ordinary (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound f S n C → bound (operator f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, operator] using h

-- The actual product is propositionally, but not definitionally, K*C.
theorem commuted (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound f S n C → bound (operator f) S n (C * K) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [mul_one, operator] using h

theorem pointwise (f : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ S C, 0 ≤ C →
    bound f S n C → bound (operator f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro S C _ h
  simpa only [one_mul, operator] using h

namespace Parameterized
def measure (a : Real) (f : Nat → Real) (p : Nat) (_y : Unit) (_j : Nat) : Real := a * f p
def bound (a : Real) (f : Nat → Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measure a f p y j ≤ C
def operator (a : Real) (f : Nat → Real) := fun p => a * f p

-- Both the predicate parameter and output object depend on the ORIGINAL K.
theorem estimate (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound K f S n C → bound K (operator K f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  intro j hj p hp y
  simpa only [measure, Parameterized.operator, one_mul] using h j hj p hp y
end Parameterized

def proofMeasure (h : Nonempty Real) (f : Real) (_p : Nat) (_y : Unit) (_j : Nat) : Real :=
  Classical.choice h * f
def proofBound (h : Nonempty Real) (f : Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, proofMeasure h f p y j ≤ C
theorem conditional (h : Nonempty Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C,
    0 ≤ C → proofBound h f S n C → proofBound h (operator f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ hC
  simpa only [one_mul, operator] using hC

end
end CoefficientExamples
