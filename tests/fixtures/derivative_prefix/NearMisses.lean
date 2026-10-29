import Mathlib.Analysis.Calculus.ContDiff.FTaylorSeries
import Mathlib.Data.Real.Basic

namespace DerivativeNearMisses
universe u v w
variable {P : Type u} {Y : Type v} {Z : Type w}
variable [NormedAddCommGroup P] [NormedSpace Real P]
variable [NormedAddCommGroup Y] [NormedSpace Real Y]
variable [NormedAddCommGroup Z] [NormedSpace Real Z]

def parametersOnly (f : P × Y → Z) (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Y,
    ‖iteratedFDeriv Real j (fun q : P => f (q, y)) p‖ ≤ C

def atZero (f : P × Y → Z) (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ‖iteratedFDeriv Real j f (p, (0 : Y))‖ ≤ C

def squaredNorm (f : P × Y → Z) (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Y, ‖iteratedFDeriv Real j f (p, y)‖ ^ 2 ≤ C

def echo (f : P × Y → Z) := f

theorem parameterEstimate (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → parametersOnly f S n C → parametersOnly (echo f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, echo] using h

theorem pointEstimate (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → atZero f S n C → atZero (echo f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, echo] using h

theorem normEstimate (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → squaredNorm f S n C → squaredNorm (echo f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, echo] using h

end DerivativeNearMisses

namespace WithoutInstances
universe u v w
def bound {P : Type u} {Y : Type v} {Z : Type w}
    (_f : P × Y → Z) (_S : Set P) (_n : Nat) (_C : Real) : Prop := True
def identityMap {P : Type u} {Y : Type v} {Z : Type w} (f : P × Y → Z) := f

theorem estimate {P : Type u} {Y : Type v} {Z : Type w} (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → bound f S n C → bound (identityMap f) S n (K * C) := by
  exact ⟨1, zero_le_one, fun _ _ _ _ _ => True.intro⟩
end WithoutInstances
