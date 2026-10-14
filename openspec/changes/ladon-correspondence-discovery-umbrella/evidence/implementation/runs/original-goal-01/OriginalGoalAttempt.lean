import Mathlib.Data.Real.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith

-- This attempt keeps the original unrestricted claim.
-- It is expected to fail; the conditional repair lives in Controls.lean.
example : ∀ x : ℝ, 0 ≤ x := by
  intro x
  linarith
