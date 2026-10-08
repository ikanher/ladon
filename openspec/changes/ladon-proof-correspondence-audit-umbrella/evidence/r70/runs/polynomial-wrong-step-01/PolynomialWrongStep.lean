import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
-- Intentionally unsuccessful reproduction of the supplied wrong factorization.
example (x : ℝ) : x^3 - x^2 - x + 1 = (x-1)*(x+1)^2 := by ring
