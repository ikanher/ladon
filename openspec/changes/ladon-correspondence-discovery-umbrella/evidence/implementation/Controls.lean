import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace CorrespondenceControls

theorem renamed_bound (x : ℝ) (hx : x ≤ 2) : x ≤ 2 := hx

def shiftedSize (n : ℕ) := n + 1
theorem definition_expansion (n : ℕ) : shiftedSize n = n + 1 := rfl

theorem max_norm_le_sum (a b : ℝ) : max |a| |b| ≤ |a| + |b| := by
  apply max_le
  · linarith [abs_nonneg b]
  · linarith [abs_nonneg a]

theorem sum_norm_le_twice_max (a b : ℝ) : |a| + |b| ≤ 2 * max |a| |b| := by
  linarith [le_max_left |a| |b|, le_max_right |a| |b|]

theorem stronger_suffices (x : ℝ) (hx : x ≤ 2) : x ≤ 3 := by linarith

theorem harmless_constant (x y : ℝ) (hy : 0 ≤ y) (h : x ≤ y) : x ≤ 2*y := by
  linarith

theorem pointwise_constant (x : ℝ) : ∃ C : ℝ, x ≤ C := ⟨x, le_refl x⟩

theorem no_uniform_constant : ¬ ∃ C : ℝ, ∀ x : ℝ, x ≤ C := by
  rintro ⟨C, h⟩
  have := h (C + 1)
  linarith

-- B ≤ A is compatible with an arbitrarily looser A-based flux bound.
-- This finite witness refutes a general inference, not either research estimate.
theorem reversed_comparison_witness :
    (0 : ℝ) ≤ 1 ∧ (1 : ℝ) ≤ 1 ∧ ¬ (1 : ℝ) ≤ 0 := by norm_num

theorem narrowed_goal (x : ℝ) (hx : 0 ≤ x) : 0 ≤ x := hx
theorem unrestricted_goal_false : ¬ ∀ x : ℝ, 0 ≤ x := by
  intro h
  have := h (-1)
  norm_num at this

def polynomial (x : ℝ) := (x+1)*(x-1)^2
theorem wrong_step_at_zero : polynomial 0 ≠ (0-1)*(0+1)^2 := by
  norm_num [polynomial]
theorem true_endpoint (x : ℝ) (hx : -1 ≤ x) : 0 ≤ polynomial x := by
  exact mul_nonneg (by linarith) (sq_nonneg (x-1))

theorem direct_method (a b : ℝ) : a^2 + b^2 ≥ 0 := by
  exact add_nonneg (sq_nonneg a) (sq_nonneg b)
theorem expanded_method (a b : ℝ) : a^2 + b^2 ≥ 0 := by
  have hid : a^2+b^2 = ((a+b)^2+(a-b)^2)/2 := by ring
  rw [hid]
  positivity

structure PremiseData (x : ℝ) where
  nonnegative : 0 ≤ x
theorem generic_consumer (x : ℝ) (h : PremiseData x) : 0 ≤ x := h.nonnegative
def actual_producer (x : ℝ) : PremiseData (x^2) := ⟨sq_nonneg x⟩
theorem actual_consumer (x : ℝ) : 0 ≤ x^2 := generic_consumer _ (actual_producer x)

end CorrespondenceControls

#print axioms CorrespondenceControls.max_norm_le_sum
#print axioms CorrespondenceControls.sum_norm_le_twice_max
#print axioms CorrespondenceControls.no_uniform_constant
#print axioms CorrespondenceControls.reversed_comparison_witness
#print axioms CorrespondenceControls.unrestricted_goal_false
#print axioms CorrespondenceControls.wrong_step_at_zero
#print axioms CorrespondenceControls.true_endpoint
#print axioms CorrespondenceControls.direct_method
#print axioms CorrespondenceControls.expanded_method
#print axioms CorrespondenceControls.actual_consumer
