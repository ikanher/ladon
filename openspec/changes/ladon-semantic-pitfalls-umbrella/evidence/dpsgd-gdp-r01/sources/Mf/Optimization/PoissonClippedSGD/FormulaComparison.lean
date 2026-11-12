import Mf.Optimization.PoissonClippedSGD.FormulaConvergence
import Mf.Optimization.PoissonClippedSGD.FormulaEnvelopeComparison
/-!
# Actual-run factor-two comparison for finite exact-CDF calibration

For every admissible adaptive Poisson SGD run at the public formula-selected
noise and its own public step, combine transcript/final/uniform privacy, exact
normalized-noise identity, both pre-update utility outputs, the factor-two
variance cap and the complete feasible-envelope infimum comparison.

The selector is a finite exact-real scalar-CDF construction. This endpoint does
not claim the stronger represented-input interval algorithm or its effective
operation counts. Above the sampling-exposure threshold, the separate accepted
rare-event endpoint permits any prescribed positive noise; no multiplicative
comparison to its zero variance infimum is made.

This is the mathematical formula tier of the returned generic-bound proof
response r01, Theorems 5.5 and 7.1, for Revisiting Gradient Clipping DP-SGD
(Koloskova, Hendrikx and Stich, ICML 2023, Appendix C.4.2).
-/

noncomputable section
open MeasureTheory Mf.DP Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
/-- Complete actual-run and own-public-envelope comparison for the finite formula calibration. -/
theorem formula_private_convergence_comparison
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε δ : ℝ} (hε : 0 ≤ ε) (hδ0 : 0 < δ)
    (hδτ : δ < 1 - (1-(data.q : ℝ))^T)
    (hmult : data.multiplier =
      Real.sqrt (PoissonGaussianHistogram.formulaCalibratedVariance T data.q ε δ))
    {sigma L0 L1 : ℝ}
    (hsigma : 0 ≤ sigma) (hL0 : 0 < L0) (hL1 : 0 ≤ L1)
    (heta : data.eta = publicStepsize L0 L1 (1 + poissonVariance n data.q)
      (poissonVariance n data.q) (data.clipping / data.q) data.clipping
      (normalizedSumNoise n d data.q data.clipping data.multiplier))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin n → Option Record)
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => slotGradient g D i x)) x)
    (hloc : LocalSmoothGradient (fun x => vectorMean (fun i => slotGradient g D i x)) L0 L1)
    (hvariance : ∀ x, meanSqDeviation (fun i => slotGradient g D i x)
      (vectorMean (fun i => slotGradient g D i x)) ≤ sigma ^ 2)
    (fLow : ℝ) (hlower : ∀ x, fLow ≤ f x) :
    let s := normalizedSumNoise n d data.q data.clipping data.multiplier
    let rate := 32 * localRate data.eta (clippedCurvature L0 L1 data.clipping)
      (f data.initial - fLow) T sigma data.clipping (poissonVariance n data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ ∧
    s ^ 2 = data.clipping ^ 2 * d *
      PoissonGaussianHistogram.formulaCalibratedVariance T data.q ε δ /
        ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate ∧
    let V := PoissonGaussianHistogram.formulaCalibratedVariance T data.q ε δ
    0 < V ∧
    (PoissonGaussianProductProfile.optimalVariance T data.q data.q_le_one hε hδ0 hδτ : ℝ) ≤ V ∧
    V < 2*(PoissonGaussianProductProfile.optimalVariance T data.q data.q_le_one hε hδ0 hδτ : ℝ) ∧
    (∀ W : NNReal, PoissonGaussianProductProfile.profile T data.q data.q_le_one W ε ≤ δ →
      rate ≤ 2*data.publicVarianceEnvelope T L0 L1 (f data.initial-fLow) sigma W) ∧
    rate ≤ 2*sInf (data.feasibleEnvelopeValues T ε δ L0 L1 (f data.initial-fLow) sigma) := by
  dsimp only
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hb := data.formula_private_convergence hn hd hε hδ0 hδτ hmult hsigma hL0 hL1
    heta g hg D f hf hloc hvariance fLow hlower
  have hv := PoissonGaussianHistogram.formulaCalibratedVariance_spec T hT data.q
    data.q_le_one data.q_pos hε hδ0 hδτ
  have hF : 0 ≤ f data.initial-fLow := sub_nonneg.mpr (hlower data.initial)
  have hrate : 32*localRate data.eta (clippedCurvature L0 L1 data.clipping)
      (f data.initial-fLow) T sigma data.clipping (poissonVariance n data.q)
      (normalizedSumNoise n d data.q data.clipping data.multiplier) =
      data.publicVarianceEnvelope T L0 L1 (f data.initial-fLow) sigma
        (PoissonGaussianHistogram.formulaCalibratedVariance T data.q ε δ) := by
    rw [heta,hmult]
    rfl
  refine ⟨hb.1,hb.2.1,hb.2.2.1,hb.2.2.2.1,hb.2.2.2.2.1,hb.2.2.2.2.2,
    hv.1,hv.2.2.1,hv.2.2.2.1,?_,?_⟩
  · intro W hW
    rw [hrate]
    exact data.formula_envelope_le_twice_feasible hn hd hT hε hδ0 hδτ hL0 hL1 hF hsigma W hW
  · rw [hrate]
    exact data.formula_envelope_le_twice_infimum hn hd hT hε hδ0 hδτ hL0 hL1 hF hsigma

end Mf.Optimization.PoissonClippedSGD.PrivacyData
