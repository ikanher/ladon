import Mf.Optimization.PoissonClippedSGD.FreshReleaseMoments
import Mf.Optimization.PoissonClippedSGD.NormalizedMoments

/-!
# Fresh release error about the clipped population gradient

The general DP-Adam learning-rate proof (2026-10-25), Lemma “Conditional
release error”, separates clipping bias, Poisson count fluctuation and
Gaussian variance. The sampling contribution uses the uncentered clipped
record second moment. No lower bound on the expected batch size is needed.
The noise scale here is the coordinate standard deviation after public
normalization, so its vector variance is `d * σ²`.
-/

noncomputable section
set_option autoImplicit false
open MeasureTheory
open scoped BigOperators

namespace Mf.Optimization.PoissonClippedSGD
open Mf.DP Mf.Optimization.FinitePoissonSign Mf.Probability.EuclideanGaussian

/-- The mask error has a bias term and the full clipped-record count variance. -/
theorem sampled_error_energy {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (C : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x a : EuclideanSpace ℝ (Fin d)) :
    (∫ m, ‖sampledGradient q C g x m - a‖ ^ 2 ∂maskLaw n q hq) =
      ((1 - (q : ℝ)) / ((q : ℝ) * n)) *
        meanSqDeviation (fun i => euclideanBallClip C (g i x)) 0 +
        ‖clippedMean C (fun i => g i x) - a‖ ^ 2 := by
  let Y := fun m => sampledGradient q C g x m
  let μ := maskLaw n q hq
  let : IsProbabilityMeasure μ := maskLaw_isProbability n q hq
  have hi : Integrable Y μ := Integrable.of_finite
  have hs : Integrable (fun m => ‖Y m‖ ^ 2) μ := Integrable.of_finite
  have hp := hi.const_inner (𝕜 := ℝ) a
  have heq : (fun m => ‖Y m - a‖ ^ 2) =
      (fun m => ‖Y m‖ ^ 2 - 2 * inner ℝ a (Y m) + ‖a‖ ^ 2) := by
    funext m
    rw [norm_sub_sq_real, real_inner_comm]
  change (∫ m, ‖Y m - a‖ ^ 2 ∂μ) = _
  rw [heq, integral_add (f := fun m => ‖Y m‖ ^ 2 - 2 * inner ℝ a (Y m))
    (g := fun _ => ‖a‖ ^ 2) (hs.sub (hp.const_mul 2)) (integrable_const _),
    integral_sub (f := fun m => ‖Y m‖ ^ 2) (g := fun m => 2 * inner ℝ a (Y m))
      hs (hp.const_mul 2), integral_const_mul, integral_inner hi]
  simp only [integral_const, probReal_univ, one_smul]
  change (∫ m, ‖sampledGradient q C g x m‖ ^ 2 ∂maskLaw n q hq) -
    2 * inner ℝ a (∫ m, sampledGradient q C g x m ∂maskLaw n q hq) + ‖a‖ ^ 2 = _
  rw [integral_norm_sq_sampledGradient q hq hq0 hn,
    integral_sampledGradient q hq hq0 hn]
  have hv := meanSqDeviation_decomposition hn
    (fun i => euclideanBallClip C (g i x)) 0
  change meanSqDeviation (fun i => euclideanBallClip C (g i x)) 0 =
    meanSqDeviation (fun i => euclideanBallClip C (g i x))
      (clippedMean C (fun i => g i x)) + ‖clippedMean C (fun i => g i x) - 0‖ ^ 2 at hv
  rw [hv, sub_zero, norm_sub_sq_real, real_inner_comm]
  ring

/-- Clipping bounds the count fluctuation by `C²`, without replacing it by
the centered record variance. -/
theorem clipped_record_energy_le {n d : ℕ} (hn : 0 < n) (C : ℝ) (hC : 0 ≤ C)
    (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    meanSqDeviation (fun i => euclideanBallClip C (g i)) 0 ≤ C ^ 2 := by
  unfold meanSqDeviation
  simp only [sub_zero]
  calc
    _ ≤ (n : ℝ)⁻¹ * ∑ _i : Fin n, C ^ 2 := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      exact Finset.sum_le_sum fun i _ => pow_le_pow_left₀ (norm_nonneg _)
        (euclideanBallClip_mem_closedBall C hC (g i)) 2
    _ = C ^ 2 := by
      have hnR : (n : ℝ) ≠ 0 := by exact_mod_cast hn.ne'
      simp only [Finset.sum_const, Finset.card_fin, nsmul_eq_mul]
      field_simp

/-- Full fresh error at a fixed state, including integrability and exact
coordinate-noise units. The empirical raw variance controls the bias. -/
theorem fresh_clipped_target_error {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (C σ v : ℝ) (hC : 0 ≤ C)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d))
    (hv : meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ v) :
    let a := euclideanBallClip C (vectorMean (fun i => g i x))
    let e := fun p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) =>
      sampledGradient q C g x p.1 + p.2 - a
    Integrable (fun p => ‖e p‖ ^ 2) (signStepLaw n d q hq σ) ∧
    (∫ p, ‖e p‖ ^ 2 ∂signStepLaw n d q hq σ) ≤
      v + ((1 - (q : ℝ)) / ((q : ℝ) * n)) * C ^ 2 + (d : ℝ) * σ ^ 2 := by
  intro a e
  let : IsProbabilityMeasure (maskLaw n q hq) := maskLaw_isProbability n q hq
  let H := fun m => sampledGradient q C g x m - a
  have he (p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d)) : e p = H p.1 + p.2 := by
    dsimp [e, H]
    abel
  simp_rw [he]
  refine ⟨finite_shift_integrable_sq (maskLaw n q hq) H σ, ?_⟩
  change (∫ p, ‖H p.1 + p.2‖ ^ 2 ∂(maskLaw n q hq).prod (law d σ)) ≤ _
  rw [integral_finite_shift_sq]
  change (∫ m, ‖sampledGradient q C g x m - a‖ ^ 2 ∂maskLaw n q hq) + _ ≤ _
  rw [sampled_error_energy hn q hq hq0 C g x a]
  have hb := (clippedMean_center_distance_sq_le hn C hC (fun i => g i x)).trans hv
  have hc := clipped_record_energy_le hn C hC (fun i => g i x)
  have hqnonneg : 0 ≤ (1 - (q : ℝ)) / ((q : ℝ) * n) :=
    div_nonneg (sub_nonneg.mpr (by exact_mod_cast hq)) (by positivity)
  have hm := mul_le_mul_of_nonneg_left hc hqnonneg
  dsimp only [a] at *
  linarith

end Mf.Optimization.PoissonClippedSGD
