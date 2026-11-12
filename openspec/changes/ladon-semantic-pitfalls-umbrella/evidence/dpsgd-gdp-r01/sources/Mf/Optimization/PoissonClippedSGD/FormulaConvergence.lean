import Mf.Optimization.PoissonClippedSGD.FormulaCalibratedPrivacy
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.PoissonUniformOutput

/-!
# Finite exact-CDF calibration and actual Poisson SGD utility

The finite formula selector supplies actual transcript, final and uniform
output privacy below the exposure threshold. The same selected noise and its
own public step feed all six local-smooth utility terms. The result retains
arbitrary clipping, epsilon zero, full sampling, positive L1 and zero objective
gap or stochastic variance. Utility concerns pre-update or independent-uniform
outputs, not the final iterate.

This exact-real formula endpoint does not implement certified numerical
argument evaluation or real comparisons. Those remain separate obligations.
-/

noncomputable section
open MeasureTheory
open Mf.DP
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Every run at the finite formula variance has privacy and its own-step six-term utility. -/
theorem formula_private_convergence
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
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hVp := (PoissonGaussianHistogram.formulaCalibratedVariance_spec T hT data.q
    data.q_le_one data.q_pos hε hδ0 hδτ).1
  have hs := data.normalizedSumNoise_pos hn hd
  have hgD := (data.withSlots g hg D).gradient_measurable
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos hs
  rw [← heta] at hstep
  have hpriv := data.optionalTranscript_formulaCalibrated_approxDP hT hε hδ0 hδτ hmult g hg
  refine ⟨hpriv, data.optionalFinal_approxDP_of_transcript hd g hg hpriv,
    data.optionalUniform_approxDP_of_transcript hd hδ0.le g hg hpriv, ?_, ?_, ?_⟩
  · rw [hmult]
    exact normalizedSumNoise_sqrt_sq n d data.q data.clipping _ hVp.le
  · exact poisson_local_convergence hn hd hT data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial
  · exact poisson_local_uniform_output_convergence hn hd data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial


end Mf.Optimization.PoissonClippedSGD.PrivacyData
