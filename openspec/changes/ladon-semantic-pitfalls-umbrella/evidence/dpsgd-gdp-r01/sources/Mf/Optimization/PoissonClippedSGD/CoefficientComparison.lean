import Mathlib.Analysis.Real.Sqrt
import Mathlib.Tactic

/-!
# Converting clipped progress to gradient norm

These scalar inequalities implement the norm conversion and coefficient-four
comparison of Appendix A in `docs/poisson-clipped-sgd/TARGET.md`.
-/

noncomputable section

namespace Mf.Optimization.PoissonClippedSGD

theorem appendixA4_scalar_comparison
    (c a b u w : ℝ)
    (hc : 0 < c) (ha : 0 ≤ a) (hb : 0 ≤ b) (hu : 0 ≤ u) (hw : 0 ≤ w)
    (hbsmall : b / c ≤ 1 / 16) (husmall : u / c ≤ 1 / 4) :
    Real.sqrt (4*a^2 + 8*b^2 + 2*u^2 + 2*w^2) +
        (4*a^2 + 8*b^2 + 2*u^2 + 2*w^2) / c ≤
      4 * (a + a^2/c + b + u + w + w^2/c) := by
  let D : ℝ := 4*a^2 + 8*b^2 + 2*u^2 + 2*w^2
  let K : ℝ := 2*a + 3*b + 2*u + 2*w
  have hD : 0 ≤ D := by dsimp [D]; positivity
  have hK : 0 ≤ K := by dsimp [K]; positivity
  have hKsq : D ≤ K^2 := by
    dsimp [D, K]
    nlinarith [mul_nonneg ha hb, mul_nonneg ha hu, mul_nonneg ha hw,
      mul_nonneg hb hu, mul_nonneg hb hw, mul_nonneg hu hw]
  have hsqrt : Real.sqrt D ≤ K := by
    rw [Real.sqrt_le_iff]
    exact ⟨hK, hKsq⟩
  have hbquad : 8*b^2/c ≤ b/2 := by
    have hmul := mul_le_mul_of_nonneg_right hbsmall (mul_nonneg hb hc.le)
    have hdiv : (b/c) * (b*c) = b^2 := by field_simp [ne_of_gt hc]
    have hbc : 0 ≤ b*c := mul_nonneg hb hc.le
    rw [hdiv] at hmul
    have hc2 : c ≠ 0 := ne_of_gt hc
    field_simp [hc2]
    nlinarith
  have huquad : 2*u^2/c ≤ u/2 := by
    have hmul := mul_le_mul_of_nonneg_right husmall (mul_nonneg hu hc.le)
    have hdiv : (u/c) * (u*c) = u^2 := by field_simp [ne_of_gt hc]
    have huc : 0 ≤ u*c := mul_nonneg hu hc.le
    rw [hdiv] at hmul
    have hc2 : c ≠ 0 := ne_of_gt hc
    field_simp [hc2]
    nlinarith
  have hquad : D/c ≤ 4*a^2/c + b/2 + u/2 + 2*w^2/c := by
    dsimp [D]
    have hc2 : c ≠ 0 := ne_of_gt hc
    have hbq := hbquad
    have huq := huquad
    field_simp [hc2] at *
    nlinarith
  have hsum : K + (4*a^2/c + b/2 + u/2 + 2*w^2/c) ≤
      4 * (a + a^2/c + b + u + w + w^2/c) := by
    have ha' : 2*a ≤ 4*a := by nlinarith
    have hb' : (7/2)*b ≤ 4*b := by nlinarith
    have hu' : (5/2)*u ≤ 4*u := by nlinarith
    have hw' : 2*w ≤ 4*w := by nlinarith
    have hwq : 2*w^2/c ≤ 4*w^2/c := by
      have hnonneg : 0 ≤ w^2/c := div_nonneg (sq_nonneg w) hc.le
      calc
        2*w^2/c = 2*(w^2/c) := by ring
        _ ≤ 4*(w^2/c) := by nlinarith [hnonneg]
        _ = 4*w^2/c := by ring
    dsimp [K]
    calc
      2*a + 3*b + 2*u + 2*w + (4*a^2/c + b/2 + u/2 + 2*w^2/c)
          = 2*a + (7/2)*b + (5/2)*u + 2*w + 4*a^2/c + 2*w^2/c := by ring
      _ ≤ 4*a + 4*b + 4*u + 4*w + 4*a^2/c + 4*w^2/c := by linarith
      _ = 4 * (a + a^2/c + b + u + w + w^2/c) := by ring
  dsimp [D] at hsqrt hquad
  calc
    Real.sqrt (4*a^2 + 8*b^2 + 2*u^2 + 2*w^2) +
        (4*a^2 + 8*b^2 + 2*u^2 + 2*w^2)/c
      ≤ K + (4*a^2/c + b/2 + u/2 + 2*w^2/c) := by
        exact add_le_add hsqrt hquad
    _ ≤ 4 * (a + a^2/c + b + u + w + w^2/c) := hsum


theorem norm_le_sqrt_min_add_min_div
    (c r : ℝ) (hc : 0 < c) (hr : 0 ≤ r) :
    r ≤ Real.sqrt (min (r^2) (c*r)) + min (r^2) (c*r) / c := by
  by_cases hrc : r ≤ c
  · have hmin : min (r^2) (c*r) = r^2 := by
      apply min_eq_left
      nlinarith
    rw [hmin, Real.sqrt_sq_eq_abs, abs_of_nonneg hr]
    have hnonneg : 0 ≤ r^2/c := div_nonneg (sq_nonneg r) hc.le
    linarith
  · have hcr : c*r ≤ r^2 := by nlinarith
    have hmin : min (r^2) (c*r) = c*r := min_eq_right hcr
    rw [hmin]
    have hsqnonneg : 0 ≤ c*r := mul_nonneg hc.le hr
    have hsqrtnonneg := Real.sqrt_nonneg (c*r)
    have hdiv : (c*r)/c = r := by field_simp [ne_of_gt hc]
    rw [hdiv]
    linarith

end Mf.Optimization.PoissonClippedSGD
