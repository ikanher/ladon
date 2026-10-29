import Mathlib.Analysis.Calculus.ContDiff.FTaylorSeries
import Mathlib.Analysis.Complex.Basic

namespace ComplexScalarBounds
def envelope (f : Complex × Complex → Complex) (S : Set Complex) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Complex, ‖iteratedFDeriv Complex j f (p, y)‖ ≤ C
def transport (f : Complex × Complex → Complex) := f

theorem estimate (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : Complex × Complex → Complex) (S : Set Complex) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transport f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, transport] using h
end ComplexScalarBounds
