import Mf.Optimization.PoissonClippedSGD.Basic

/-!
# Clipping bias near an interior population mean

For the small-gradient case of the restricted Poisson argument in
`docs/poisson-clipped-sgd/TARGET.md`, clipping displacement is controlled by
raw squared deviations. No bounded-support or symmetry assumption is needed.
-/

namespace Mf.Optimization.PoissonClippedSGD

noncomputable section

open scoped BigOperators
open Mf.DP

/-- Displacement by radial clipping is bounded by squared distance to an
interior reference, divided by that reference's radius margin. -/
theorem norm_sub_clip_le_sq_div_margin {d : ℕ}
    (c : ℝ) (x v : EuclideanSpace ℝ (Fin d))
    (hmargin : 0 < c - ‖v‖) :
    ‖x - euclideanBallClip c x‖ ≤ ‖x - v‖ ^ 2 / (c - ‖v‖) := by
  by_cases hx : ‖x‖ ≤ c
  · simp only [euclideanBallClip, if_pos hx, sub_self, norm_zero]
    positivity
  · have hc_lt : c < ‖x‖ := lt_of_not_ge hx
    have hxpos : 0 < ‖x‖ := by
      have := norm_nonneg v
      linarith
    have hres : ‖x - euclideanBallClip c x‖ = ‖x‖ - c := by
      rw [euclideanBallClip, if_neg hx]
      rw [show x - (c / ‖x‖) • x = (1 - c / ‖x‖) • x by module,
        norm_smul, Real.norm_eq_abs]
      have hratio : c / ‖x‖ < 1 := (div_lt_one hxpos).2 hc_lt
      rw [abs_of_nonneg (by linarith : 0 ≤ 1 - c / ‖x‖)]
      field_simp [hxpos.ne']
    have htri : ‖x‖ ≤ ‖x - v‖ + ‖v‖ := by
      calc
        ‖x‖ = ‖(x - v) + v‖ := by congr 1; abel
        _ ≤ ‖x - v‖ + ‖v‖ := norm_add_le _ _
    have hdist : c - ‖v‖ ≤ ‖x - v‖ := by linarith
    have hres_le : ‖x - euclideanBallClip c x‖ ≤ ‖x - v‖ := by
      rw [hres]
      linarith
    have hsq : ‖x - v‖ ≤ ‖x - v‖ ^ 2 / (c - ‖v‖) := by
      rw [le_div_iff₀ hmargin]
      nlinarith [norm_nonneg (x - v)]
    exact hres_le.trans hsq

/-- Averaging the clipping displacements gives a bias estimate in terms of
the population centered second moment. -/
theorem norm_clippedMean_sub_mean_le {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (c : ℝ)
    (hmargin : 0 < c - ‖vectorMean g‖) :
    ‖clippedMean c g - vectorMean g‖ ≤
      meanSqDeviation g (vectorMean g) / (c - ‖vectorMean g‖) := by
  rw [norm_sub_rev]
  change ‖vectorMean g - vectorMean (fun i => euclideanBallClip c (g i))‖ ≤ _
  rw [← vectorMean_sub]
  calc
    _ ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i - euclideanBallClip c (g i)‖ :=
      norm_vectorMean_le _
    _ ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i - vectorMean g‖ ^ 2 / (c - ‖vectorMean g‖) := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      exact Finset.sum_le_sum fun i _ => norm_sub_clip_le_sq_div_margin c _ _ hmargin
    _ = meanSqDeviation g (vectorMean g) / (c - ‖vectorMean g‖) := by
      simp [meanSqDeviation, Finset.sum_div, mul_div_assoc]

/-- When the raw mean lies in the half-radius ball, the mean clipping bias is
at most twice the raw variance divided by the clipping radius. -/
theorem norm_clippedMean_sub_mean_le_of_small {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (c sigma : ℝ) (hc : 0 < c)
    (hsmall : ‖vectorMean g‖ < c / 2)
    (hvariance : meanSqDeviation g (vectorMean g) ≤ sigma ^ 2) :
    ‖clippedMean c g - vectorMean g‖ ≤ 2 * sigma ^ 2 / c := by
  have hm : 0 < c - ‖vectorMean g‖ := by linarith
  calc
    _ ≤ meanSqDeviation g (vectorMean g) / (c - ‖vectorMean g‖) :=
      norm_clippedMean_sub_mean_le g c hm
    _ ≤ sigma ^ 2 / (c / 2) := by
      gcongr
      linarith
    _ = 2 * sigma ^ 2 / c := by ring

end

end Mf.Optimization.PoissonClippedSGD
