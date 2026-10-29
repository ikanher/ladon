import Mathlib.Data.Real.Basic

namespace PrefixExamples

def measure (f : Real) (_p : Nat) (_y : Unit) (j : Nat) : Real := f + j

def envelope (f : Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measure f p y j ≤ C

def transport (f : Real) := f

theorem narrow (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    envelope f S n C → envelope (transport f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, transport] using h

theorem wide (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    envelope f S (n + 4) C → envelope (transport f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simp only [one_mul, transport]
  intro j hj p hp y
  exact h j (Nat.le_trans hj (Nat.le_add_right n 4)) p hp y

namespace Alternative

def measure (a : Real) (f : Nat → Real) (p : Nat) (_y : Unit) (j : Nat) : Real := a * f p + j

def bound (a : Real) (f : Nat → Real) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Unit, measure a f p y j ≤ C

def operator (f : Nat → Real) := f

theorem lower (a : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound a f S (n + 2) C → bound a (operator f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simp only [one_mul, operator]
  intro j hj p hp y
  exact h j (Nat.le_trans hj (Nat.le_add_right n 2)) p hp y

theorem higher (a : Real) (n : Nat) : ∃ K : Real, 0 ≤ K ∧ ∀ f S C, 0 ≤ C →
    bound a f S (n + 7) C → bound a (operator f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simp only [one_mul, operator]
  intro j hj p hp y
  exact h j (Nat.le_trans hj (Nat.le_add_right n 7)) p hp y

end Alternative
end PrefixExamples
