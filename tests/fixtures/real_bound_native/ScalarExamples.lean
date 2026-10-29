import Mathlib.Analysis.Calculus.ContDiff.FTaylorSeries
import Mathlib.Data.Real.Basic

namespace ScalarExamples

def envelope (f : Real × Real → Real) (S : Set Real) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y : Real, ‖iteratedFDeriv Real j f (p, y)‖ ≤ C

def transport (f : Real × Real → Real) := f

theorem ordinary (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : Real × Real → Real) (S : Set Real) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transport f) S n (K * C) := by
  refine ⟨1, zero_le_one, ?_⟩
  intro f S C _ h
  simpa only [one_mul, transport] using h

namespace BadMultiplication
local instance nonstandardProduct : HMul Real Real Real := ⟨fun _ _ => (0 : Real)⟩

theorem estimate (unrelated : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : Real × Real → Real) (S : Set Real) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transport f) S n (K * C) := by
  exact False.elim unrelated
end BadMultiplication

namespace BadOrder
local instance nonstandardOrder : LE Real := ⟨fun _ _ => True⟩

theorem estimate (unrelated : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : Real × Real → Real) (S : Set Real) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transport f) S n (K * C) := by
  exact False.elim unrelated
end BadOrder

namespace BadZero
local instance nonstandardZero : OfNat Real 0 := ⟨(1 : Real)⟩

theorem estimate (unrelated : False) (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : Real × Real → Real) (S : Set Real) (C : Real),
      0 ≤ C → envelope f S n C → envelope (transport f) S n (K * C) := by
  exact False.elim unrelated
end BadZero

end ScalarExamples
