import Mf.Optimization.PoissonClippedSGD.Basic

/-!
# Finite variance control under clipping

The mean minimizes average squared distance. Applied to nonexpansive Euclidean
clipping, this bounds both the clipped variance and the displacement between
the clipped mean and the clipped raw mean. These are the two finite-population
estimates in Appendix A.1 of the target recorded in
`docs/poisson-clipped-sgd/TARGET.md`.
-/

namespace Mf.Optimization.PoissonClippedSGD

noncomputable section

open scoped BigOperators
open Mf.DP

/-- Exact decomposition of the mean squared distance about an arbitrary center. -/
theorem meanSqDeviation_decomposition {n d : ℕ} (hn : 0 < n)
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (v : EuclideanSpace ℝ (Fin d)) :
    meanSqDeviation g v = meanSqDeviation g (vectorMean g) +
      ‖vectorMean g - v‖ ^ 2 := by
  let total : ℝ := (n : ℝ)
  let firstMoment : EuclideanSpace ℝ (Fin d) := ∑ i, g i
  let μ := (1 / total) • firstMoment
  have htotal : total ≠ 0 := by
    dsimp [total]
    exact_mod_cast (Nat.ne_of_gt hn)
  have hmean : vectorMean g = μ := by
    simp [vectorMean, μ, total, firstMoment]
  have hleft :
      ∑ i, ‖g i - v‖ ^ 2 = total * ‖v‖ ^ 2 -
        2 * inner ℝ v firstMoment + ∑ i, ‖g i‖ ^ 2 := by
    calc
      _ = ∑ i, (‖v‖ ^ 2 - 2 * inner ℝ v (g i) + ‖g i‖ ^ 2) := by
        apply Finset.sum_congr rfl
        intro i _
        rw [← real_inner_self_eq_norm_sq, real_inner_sub_sub_self,
          real_inner_self_eq_norm_sq, real_inner_self_eq_norm_sq,
          real_inner_comm (g i) v, real_inner_comm v (g i)]
        ring
      _ = _ := by
        simp [Finset.sum_add_distrib, Finset.sum_sub_distrib,
          inner_sum, Finset.mul_sum, total, firstMoment]
  have hvar :
      ∑ i, ‖g i - μ‖ ^ 2 =
        ∑ i, ‖g i‖ ^ 2 - 2 * inner ℝ μ firstMoment + total * ‖μ‖ ^ 2 := by
    calc
      _ = ∑ i, (‖g i‖ ^ 2 - 2 * inner ℝ μ (g i) + ‖μ‖ ^ 2) := by
        apply Finset.sum_congr rfl
        intro i _
        rw [← real_inner_self_eq_norm_sq, real_inner_sub_sub_self,
          real_inner_self_eq_norm_sq, real_inner_self_eq_norm_sq,
          real_inner_comm μ (g i)]
      _ = _ := by
        simp [Finset.sum_add_distrib, Finset.sum_sub_distrib,
          inner_sum, Finset.mul_sum, total, firstMoment]
  unfold meanSqDeviation
  rw [hmean]
  have hnR : (n : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
  field_simp [hnR]
  rw [hleft, hvar]
  have hfirst : firstMoment = total • μ := by
    dsimp [μ]
    rw [smul_smul]
    simp [htotal]
  rw [hfirst, real_inner_smul_right v μ total,
    real_inner_smul_right μ μ total, real_inner_self_eq_norm_sq]
  rw [← real_inner_self_eq_norm_sq (μ - v), real_inner_sub_sub_self,
    real_inner_self_eq_norm_sq, real_inner_self_eq_norm_sq, real_inner_comm μ v]
  ring

/-- Squared norm of a population mean is bounded by its mean squared norm. -/
theorem norm_vectorMean_sq_le {n d : ℕ} (hn : 0 < n)
    (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    ‖vectorMean g‖ ^ 2 ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i‖ ^ 2 := by
  have h := meanSqDeviation_decomposition hn g 0
  have hv := meanSqDeviation_nonneg g (vectorMean g)
  simp only [meanSqDeviation, sub_zero] at h hv
  linarith

/-- Nonexpansive clipping controls squared deviations about the clipped raw mean. -/
theorem clipped_deviation_le {n d : ℕ} (c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    meanSqDeviation (fun i => euclideanBallClip c (g i))
        (euclideanBallClip c (vectorMean g)) ≤ meanSqDeviation g (vectorMean g) := by
  unfold meanSqDeviation
  apply mul_le_mul_of_nonneg_left _ (by positivity)
  apply Finset.sum_le_sum
  intro i _
  exact pow_le_pow_left₀ (norm_nonneg _)
    (euclideanBallClip_nonexpansive c hc (g i) (vectorMean g)) 2

/-- Clipping cannot increase the finite population variance. -/
theorem clippedMean_variance_le {n d : ℕ} (hn : 0 < n)
    (c : ℝ) (hc : 0 ≤ c) (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    meanSqDeviation (fun i => euclideanBallClip c (g i)) (clippedMean c g) ≤
      meanSqDeviation g (vectorMean g) := by
  have h := clipped_deviation_le c hc g
  rw [meanSqDeviation_decomposition hn] at h
  exact (le_add_of_nonneg_right (sq_nonneg _)).trans h

/-- Mean clipping differs from clipping the mean by at most the raw second
moment of centered record errors, in squared norm. -/
theorem clippedMean_center_distance_sq_le {n d : ℕ} (hn : 0 < n)
    (c : ℝ) (hc : 0 ≤ c) (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    ‖clippedMean c g - euclideanBallClip c (vectorMean g)‖ ^ 2 ≤
      meanSqDeviation g (vectorMean g) := by
  have h := clipped_deviation_le c hc g
  rw [meanSqDeviation_decomposition hn] at h
  exact (le_add_of_nonneg_left (meanSqDeviation_nonneg _ _)).trans h

end

end Mf.Optimization.PoissonClippedSGD
