import Mathlib.Data.Real.Basic
import Mathlib.Tactic.NormNum

namespace TransferExamples
def measure (f : Real) (_p : Nat) (_y : Unit) (_j : Nat) : Real := f
def bound (f : Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measure f p y j ≤ C
def twice (f : Real) := 2 * f
def thrice (f : Real) := 3 * f
theorem first (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound f S (n+4) C → bound (twice f) S n (K*C) := by
  refine ⟨2, by norm_num, ?_⟩
  intro f S C _ h j hj p hp y
  exact mul_le_mul_of_nonneg_left (h j (Nat.le_trans hj (Nat.le_add_right n 4)) p hp y) (by norm_num)
theorem second (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound f S (n+7) C → bound (thrice f) S n (K*C) := by
  refine ⟨3, by norm_num, ?_⟩
  intro f S C _ h j hj p hp y
  exact mul_le_mul_of_nonneg_left (h j (Nat.le_trans hj (Nat.le_add_right n 7)) p hp y) (by norm_num)
def otherMeasure (f : Real) (_p : Nat) (_y : Unit) (_j : Nat) : Real := f+1
def other (f : Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, otherMeasure f p y j ≤ C
def identity (f : Real) := f
theorem incompatible (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    other f S (n+7) C → other (identity f) S n (K*C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h j hj p hp y
  simpa only [one_mul, identity] using h j (Nat.le_trans hj (Nat.le_add_right n 7)) p hp y
namespace Functions
def measure (a : Real) (f : Nat → Real) (p : Nat) (_y : Unit) (_j : Nat) := a*f p
def bound (a : Real) (f : Nat → Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measure a f p y j ≤ C
def scale (f : Nat → Real) := fun p => 2*f p
theorem estimate (a : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound a f S (n+0) C → bound a (scale f) S n (K*C) := by
  refine ⟨2, by norm_num, ?_⟩
  intro f S C _ h j hj p hp y
  have hh := mul_le_mul_of_nonneg_left (h j hj p hp y) (show (0:Real) ≤ 2 by norm_num)
  simpa only [measure, scale, mul_left_comm] using hh
end Functions
end TransferExamples
