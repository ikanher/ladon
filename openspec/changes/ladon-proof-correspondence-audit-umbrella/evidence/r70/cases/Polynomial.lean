import Mathlib.Data.Real.Basic
import Mathlib.Tactic
namespace Audit.Polynomial

def p (x : ℝ) : ℝ := x^3 - x^2 - x + 1

-- Concrete witnesses refute the disputed steps; they do not refute the theorem.
theorem wrong_factorization_at_zero : p 0 ≠ (0 - 1) * (0 + 1)^2 := by
  norm_num [p]
theorem wrong_product_negative_at_zero : (0 - 1 : ℝ) * (0 + 1)^2 < 0 := by
  norm_num

theorem corrected_factorization (x : ℝ) : p x = (x + 1) * (x - 1)^2 := by
  unfold p
  ring

theorem original_conclusion (x : ℝ) (hx : -1 ≤ x) : 0 ≤ p x := by
  rw [corrected_factorization]
  exact mul_nonneg (by linarith) (sq_nonneg (x - 1))

#print axioms wrong_factorization_at_zero
#print axioms wrong_product_negative_at_zero
#print axioms corrected_factorization
#print axioms original_conclusion
end Audit.Polynomial
