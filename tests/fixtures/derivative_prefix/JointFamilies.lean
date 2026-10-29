import Mathlib.Analysis.Calculus.ContDiff.FTaylorSeries
import Mathlib.Data.Real.Basic

namespace CloudBounds
universe u v w
variable {P : Type u} {Y : Type v} {Z : Type w}
variable [NormedAddCommGroup P] [NormedSpace Real P]
variable [NormedAddCommGroup Y] [NormedSpace Real Y]
variable [NormedAddCommGroup Z] [NormedSpace Real Z]

def envelope (f : P × Y → Z) (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Y, ‖iteratedFDeriv Real j f (p, y)‖ ≤ C

def drift (f : P × Y → Z) := f

theorem stationary (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → envelope f S n C → envelope (drift f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, drift] using h

def proofEnvelope (_hypothesis : False) (f : P × Y → Z)
    (S : Set P) (n : Nat) (C : Real) : Prop := envelope f S n C

theorem proofParameter (hypothesis : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → proofEnvelope hypothesis f S n C →
      proofEnvelope hypothesis (drift f) S n (K * C) := by
  exact False.elim hypothesis

end CloudBounds

namespace RiverBounds
universe u v w
variable {P : Type u} {Y : Type v} {Z : Type w}
variable [NormedAddCommGroup P] [NormedSpace Real P]
variable [NormedAddCommGroup Y] [NormedSpace Real Y]
variable [NormedAddCommGroup Z] [NormedSpace Real Z]

def prefixControl (f : P × Y → Z) (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Y, ‖iteratedFDeriv Real j f (p, y)‖ ≤ C

def carry (f : P × Y → Z) := f

theorem longerInput (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : P × Y → Z) (S : Set P) (C : Real),
      0 ≤ C → prefixControl f S (n + 7) C →
      prefixControl (carry f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h j hj p hp y
  simpa only [one_mul, carry] using h j (Nat.le_trans hj (Nat.le_add_right n 7)) p hp y

end RiverBounds
