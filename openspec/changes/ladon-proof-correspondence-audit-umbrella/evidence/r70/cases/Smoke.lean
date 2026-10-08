import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
namespace Audit
theorem smoke (x : ℝ) : (x + 1)^2 = x^2 + 2*x + 1 := by ring
#print axioms smoke
end Audit
