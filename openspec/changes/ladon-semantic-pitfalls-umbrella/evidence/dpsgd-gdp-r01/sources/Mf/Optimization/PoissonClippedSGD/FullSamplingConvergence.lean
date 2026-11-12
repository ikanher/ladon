import Mf.Optimization.PoissonClippedSGD.FullSamplingGDP
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.PoissonUniformOutput

/-!
# Full-sampling exact GDP and local-smooth utility for the same run

This supplies the q=1 boundary of the extension to Revisiting Gradient
Clipping, Appendix C.4.2 (Koloskova, Hendrikx and Stich, ICML 2023).
Variance V=T/mu² gives exact GDP; an explicit Gaussian-profile budget gives
approximate DP of the transcript and both actual outputs. The public step
and arbitrary-clipping utility use precisely this calibrated noise.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.GaussianTesting Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Exact full-sampling GDP, its event budget, and same-noise public-step utility. -/
theorem fullSampling_private_convergence
    {T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    (hq : data.q = 1)
    {mu ε δ : ℝ} (hmu : 0 < mu) (hε : 0 ≤ ε) (hδ : 0 ≤ δ)
    (hbudget : gdpProfile mu ε ≤ δ)
    (hmult : data.multiplier = Real.sqrt ((T : ℝ) / mu ^ 2))
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
    (∀ D D', OptionalRecordAdjacent D D' →
      GDPTestDominates mu (data.optionalTranscriptLaw g hg T D)
        (data.optionalTranscriptLaw g hg T D')) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ ∧
    s ^ 2 = data.clipping ^ 2 * d * ((T : ℝ) / mu ^ 2) / ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hs := data.normalizedSumNoise_pos hn hd
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos hs
  rw [← heta] at hstep
  have hgD := (data.withSlots g hg D).gradient_measurable
  have hp := data.optionalTranscript_fullSampling_approxDP hT hq hmu hε hδ hbudget hmult g hg
  refine ⟨?_, hp, data.optionalFinal_approxDP_of_transcript hd g hg hp,
    data.optionalUniform_approxDP_of_transcript hd hδ g hg hp, ?_, ?_, ?_⟩
  · intro D D' hadj
    exact (data.optionalTranscript_fullSampling_gaussianComparison hT hq hmu hmult g hg
      D D' hadj).1
  · rw [hmult]
    exact normalizedSumNoise_sqrt_sq n d data.q data.clipping _ (by positivity)
  · exact poisson_local_convergence hn hd hT data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial
  · exact poisson_local_uniform_output_convergence hn hd data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial

end Mf.Optimization.PoissonClippedSGD.PrivacyData
