import Mf.Optimization.PoissonClippedSGD.Basic
import Mf.Optimization.PoissonClippedSGD.FiniteMeans
import Mf.Optimization.PoissonClippedSGD.Mechanism
import Mf.Optimization.PoissonClippedSGD.BernoulliMoments

/-!
# Moments after expected-batch normalization

The independent Bernoulli calculation is scaled by qn. Its second moment
retains the contribution from the nonzero clipped mean as well as the centered
variance, as required in Appendix A of `docs/poisson-clipped-sgd/TARGET.md`.
-/

open MeasureTheory
open scoped BigOperators

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open Mf.DP

lemma integrable_sampledGradient {n d : ℕ} (q c : ℝ) (qN : NNReal) (hq1 : qN ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    Integrable (fun m => sampledGradient q c g x m) (maskLaw n qN hq1) := by
  letI : IsProbabilityMeasure (maskLaw n qN hq1) := maskLaw_isProbability n qN hq1
  exact Integrable.of_finite

lemma integrable_norm_sq_sampledGradient {n d : ℕ} (q c : ℝ) (qN : NNReal) (hq1 : qN ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    Integrable (fun m => ‖sampledGradient q c g x m‖ ^ 2) (maskLaw n qN hq1) := by
  letI : IsProbabilityMeasure (maskLaw n qN hq1) := maskLaw_isProbability n qN hq1
  exact Integrable.of_finite

theorem integral_sampledGradient {n d : ℕ} (qN : NNReal) (hq1 : qN ≤ 1)
    (hq0 : 0 < qN) (hn : 0 < n) (c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    (∫ m, sampledGradient (qN:ℝ) c g x m ∂maskLaw n qN hq1) =
      clippedMean c (fun i => g i x) := by
  let h : Fin n → EuclideanSpace ℝ (Fin d) := fun i => euclideanBallClip c (g i x)
  have hsample : (fun m => sampledGradient (qN:ℝ) c g x m) =
      fun m => ((qN:ℝ) * (n:ℝ))⁻¹ • rawSampledSum n d h m := by
    funext m
    simp [sampledGradient, rawSampledSum, indicator, h]
  rw [hsample, integral_smul, rawSampledSum_integral]
  have hq : (qN:ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hq0)
  have hnR : (n:ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
  unfold clippedMean vectorMean
  rw [smul_smul]
  have hscalar : ((qN:ℝ) * (n:ℝ))⁻¹ * (qN:ℝ) = (n:ℝ)⁻¹ := by
    field_simp
  rw [hscalar]

theorem integral_norm_sq_sampledGradient {n d : ℕ} (qN : NNReal) (hq1 : qN ≤ 1)
    (hq0 : 0 < qN) (hn : 0 < n) (c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    (∫ m, ‖sampledGradient (qN:ℝ) c g x m‖ ^ 2 ∂maskLaw n qN hq1) =
      (1 + (1-(qN:ℝ))/((qN:ℝ)*(n:ℝ))) *
        ‖clippedMean c (fun i => g i x)‖ ^ 2 +
      ((1-(qN:ℝ))/((qN:ℝ)*(n:ℝ))) *
        meanSqDeviation (fun i => euclideanBallClip c (g i x))
          (clippedMean c (fun i => g i x)) := by
  let h : Fin n → EuclideanSpace ℝ (Fin d) := fun i => euclideanBallClip c (g i x)
  let μ : EuclideanSpace ℝ (Fin d) := vectorMean h
  have hsample : (fun m => sampledGradient (qN:ℝ) c g x m) =
      fun m => ((qN:ℝ) * (n:ℝ))⁻¹ • rawSampledSum n d h m := by
    funext m
    simp [sampledGradient, rawSampledSum, indicator, h]
  have hsq : (fun m => ‖sampledGradient (qN:ℝ) c g x m‖ ^ 2) =
      fun m => (((qN:ℝ) * (n:ℝ))⁻¹)^2 * ‖rawSampledSum n d h m‖ ^ 2 := by
    funext m
    have hs := congrFun hsample m
    rw [hs]
    rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg (by positivity)]
    rw [mul_pow]
  rw [hsq, integral_const_mul, rawSampledSum_norm_sq_integral]
  have hq : (qN:ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hq0)
  have hnR : (n:ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
  have hmu : μ = clippedMean c (fun i => g i x) := rfl
  have hdecomp := meanSqDeviation_decomposition hn h (0 : EuclideanSpace ℝ (Fin d))
  simp only [clippedMean, vectorMean, h] at hdecomp ⊢
  unfold meanSqDeviation at hdecomp ⊢
  simp only [sub_zero] at hdecomp
  rw [show ((qN:ℝ)*(n:ℝ))⁻¹ ^ 2 *
      ((qN:ℝ)^2 * ‖∑ i, h i‖^2 + (qN:ℝ)*(1-(qN:ℝ))*∑ i, ‖h i‖^2) =
      (n:ℝ)⁻¹^2 * ‖∑ i, h i‖^2 +
        ((1-(qN:ℝ))/((qN:ℝ)*(n:ℝ))) * ((n:ℝ)⁻¹ * ∑ i, ‖h i‖^2) by
      field_simp [hq, hnR]
      <;> ring]
  simp only [h] at hdecomp ⊢
  rw [hdecomp]
  simp only [norm_smul, Real.norm_eq_abs]
  rw [abs_of_nonneg (inv_nonneg.mpr (by positivity : (0:ℝ) ≤ (n:ℝ)))]
  field_simp [hnR]
  <;> ring

end Mf.Optimization.PoissonClippedSGD
