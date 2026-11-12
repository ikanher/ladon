import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceBatchSize
import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceCalibration
import Mf.Optimization.PoissonClippedSGD.Conclusions
import Mf.Optimization.PoissonClippedSGD.FinalLaw

/-!
# Publicly retuned finite-private SGD and batch comparison

This combines the logarithmic Gaussian-reference calibration, the Poisson
clipped-SGD convergence theorem and the fixed-update batch comparison. The
same actual run has transcript and final-output privacy and the expected-average
gradient guarantee. A public upper bound on the objective gap suffices.

The comparison orders the retuned upper bounds. It does not compare realized
trajectories or expected training errors of two runs. The learning-rate inputs
must be public and fixed across neighboring datasets, as in `PrivacyData`.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
open Mf.DP.PoissonLogarithmicReferenceCalibration
open LogarithmicReference

namespace PrivacyData
variable {n d : ℕ}

/-- Finite privacy and expected-gradient convergence at the public optimized learning rate,
with a certified comparison to the retuned upper bound for any smaller batch. -/
theorem logarithmicReference_tuned_batch_comparison {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) {T : ℕ} (hT : 0 < T)
    {eps δ q : ℝ} (he : 0 < eps) (hδ : 0 < δ) (hδ1 : δ < 1)
    (hq : 0 < q) (hqq : q ≤ (data.q : ℝ))
    (hnoise : data.multiplier = Real.sqrt (calibratedVariance T data.q eps δ))
    {F L sigma : ℝ} (hF : 0 < F) (hL : 0 < L) (hsg : 0 ≤ sigma)
    (hclip : 4 * sigma ≤ data.clipping)
    (heta : data.eta = learningRate n d T data.q data.clipping sigma eps δ F L)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin n → Option Record)
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => slotGradient g D i x)) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => slotGradient g D i x) -
        vectorMean (fun i => slotGradient g D i y)‖ ≤ L * ‖x - y‖)
    (hvariance : ∀ x, meanSqDeviation (fun i => slotGradient g D i x)
      (vectorMean (fun i => slotGradient g D i x)) ≤ sigma ^ 2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ f x)
    (hgap : f data.initial - fLower ≤ F) :
    let s := normalizedSumNoise n d data.q data.clipping data.multiplier
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T data.q data.q_le_one s
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) eps δ ∧
      Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) eps δ ∧
      (T : ℝ)⁻¹ * ∑ t, values t ≤ upperBound n d T data.q data.clipping sigma eps δ F L ∧
      upperBound n d T data.q data.clipping sigma eps δ F L ≤
        upperBound n d T q data.clipping sigma eps δ F L := by
  dsimp only
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hdR : (0 : ℝ) < d := by exact_mod_cast hd
  have hqR : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
  have hq1 : (data.q : ℝ) ≤ 1 := by exact_mod_cast data.q_le_one
  have hepos : 0 < data.eta := by
    rw [heta]
    exact learningRate_pos hnR hdR hT hqR hq1 data.clipping_pos he hF hL
  have hstep : data.eta * L * (1 + (1 - (data.q : ℝ)) / ((data.q : ℝ) * n)) ≤ 1 := by
    rw [heta]
    exact learningRate_admissible hnR hqR hq1 hL
  have hgrad : ∀ i, Measurable (slotGradient g D i) :=
    (data.withSlots g hg D).gradient_measurable
  have hconv := gaussian_convergence hn hd data.q data.q_pos data.q_le_one
    data.eta L data.clipping sigma
    (normalizedSumNoise n d data.q data.clipping data.multiplier)
    hepos hL data.clipping_pos hsg (data.normalizedSumNoise_pos hn hd).le hclip hstep
    (slotGradient g D) hgrad f hf hLip hvariance fLower hlower data.initial T hT
  have hbudget : poissonRateD data.eta L ((1 - (data.q : ℝ)) / ((data.q : ℝ) * n))
      sigma (normalizedSumNoise n d data.q data.clipping data.multiplier)
      (f data.initial - fLower) T data.clipping ≤
      stepRateD (learningRate n d T data.q data.clipping sigma eps δ F L) F T L
        (totalVariance n d T data.q data.clipping sigma eps δ)
        (8 * sigma ^ 4 / data.clipping ^ 2) := by
    rw [heta, hnoise]
    unfold poissonRateD stepRateD totalVariance
    rw [← noiseVariance_eq_normalized n d T hT hqR he]
    have hden : 0 ≤ learningRate n d T data.q data.clipping sigma eps δ F L * (T : ℝ) := by
      rw [← heta]
      positivity
    have hgap' := div_le_div_of_nonneg_right
      (mul_le_mul_of_nonneg_left hgap (by norm_num : (0 : ℝ) ≤ 4)) hden
    linarith
  have hpriv := data.optionalTranscript_logarithmicReference_approxDP hT he hδ hδ1
    le_rfl hnoise g hg
  have hfinal := Mf.DP.approxDP_postprocess_map (data.state T) (data.state_measurable T) hpriv
  have hlaw : data.optionalFinalLaw g T =
      fun D => (data.optionalTranscriptLaw g hg T D).map (data.state T) := by
    funext D
    exact data.optionalFinalLaw_eq_map g hg hd T D
  rw [← hlaw] at hfinal
  exact ⟨hpriv, hfinal, hconv.trans (stationarityUpper_mono data.clipping_pos.le hbudget),
    upperBound_antitone hnR hdR hT hq hqq hq1 data.clipping_pos he hF hL⟩

end PrivacyData
end Mf.Optimization.PoissonClippedSGD
