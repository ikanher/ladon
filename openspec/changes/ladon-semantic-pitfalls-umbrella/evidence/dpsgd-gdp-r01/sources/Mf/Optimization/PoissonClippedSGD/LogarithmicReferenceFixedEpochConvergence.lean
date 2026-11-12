import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceFixedEpoch

/-!
# Same-run privacy and utility at fixed expected passes

The adaptive Poisson clipped-SGD run uses the public finite Gaussian-reference
calibration and its optimal admissible constant step. Equal exact expected
participation and inactive caps compare its certified upper bound with the
bound at a smaller batch and a longer integer horizon. Privacy protects the
same transcript and its final output; the utility claim remains an average
expected pre-update gradient norm.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
open Mf.DP.PoissonLogarithmicReferenceCalibration LogarithmicReference
namespace PrivacyData
variable {n d : ℕ}

/-- Finite privacy, expected-gradient convergence and the exact-pass comparison
for the same publicly tuned run, provided both stability caps are inactive. -/
theorem logarithmicReference_fixed_passes_comparison {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) {T : ℕ} (hT : 0 < T)
    {eps δ q : ℝ} (he : 0 < eps) (hδ : 0 < δ) (hδ1 : δ < 1)
    (hq : 0 < q) (hqq : q ≤ (data.q : ℝ))
    (Tref : ℕ) (hTref : 0 < Tref) {E : ℝ} (hE : 0 < E)
    (hpasses : (Tref : ℝ) * q = E) (hpasses' : (T : ℝ) * (data.q : ℝ) = E)
    (hnoise : data.multiplier = Real.sqrt (calibratedVariance T data.q eps δ))
    {F L sigma : ℝ} (hF : 0 < F) (hL : 0 < L) (hsg : 0 ≤ sigma)
    (hclip : 4 * sigma ≤ data.clipping)
    (heta : data.eta = learningRate n d T data.q data.clipping sigma eps δ F L)
    (hcap : Real.sqrt (2 * F / ((Tref : ℝ) * L *
      totalVariance n d Tref q data.clipping sigma eps δ)) ≤
      poissonStepCap L ((1 - q) / (q * n)))
    (hcap' : Real.sqrt (2 * F / ((T : ℝ) * L *
      totalVariance n d T data.q data.clipping sigma eps δ)) ≤
      poissonStepCap L ((1 - (data.q : ℝ)) / ((data.q : ℝ) * n)))
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
        upperBound n d Tref q data.clipping sigma eps δ F L := by
  have h := data.logarithmicReference_tuned_batch_comparison hn hd hT he hδ hδ1
    (by exact_mod_cast data.q_pos) le_rfl hnoise hF hL hsg hclip heta
    g hg D f hf hLip hvariance fLower hlower hgap
  exact ⟨h.1, h.2.1, h.2.2.1,
    upperBound_exact_passes hTref hT hE (by exact_mod_cast hn) (by exact_mod_cast hd)
      hq hqq (by exact_mod_cast data.q_le_one) hpasses hpasses'
      data.clipping_pos he hF hL hcap hcap'⟩

end PrivacyData
end Mf.Optimization.PoissonClippedSGD
