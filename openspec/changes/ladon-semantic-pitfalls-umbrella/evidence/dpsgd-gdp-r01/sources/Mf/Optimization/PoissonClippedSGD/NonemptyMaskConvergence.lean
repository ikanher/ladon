import Mf.Optimization.PoissonClippedSGD.NonemptyMaskPrivacy
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.PoissonUniformOutput

/-!
# Actual SGD utility and the weighted nonempty-mask privacy allowance

The finite weighted Gaussian comparison supplies the privacy allowance at
the actual positive multiplier. The same normalized noise and own public
step feed all six local-smooth utility terms, including both transients.

This is a forward privacy/utility theorem for the generic Revisiting
Gradient Clipping extension. It does not invert the allowance at a requested
delta, assert practical tightness against the reference/Bennett policy, prove
a PLD-optimality gap, or claim final-iterate utility.
-/

noncomputable section
open MeasureTheory
open Mf.DP
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Actual weighted-profile privacy and complete same-noise own-public-step utility. -/
theorem nonemptyMask_private_convergence
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε : ℝ} (hε : 0 ≤ ε)
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
    let δ := PoissonNonemptyMaskGaussianProfile.budget T data.q (1/data.multiplier) ε
    let s := normalizedSumNoise n d data.q data.clipping data.multiplier
    let rate := 32 * localRate data.eta (clippedCurvature L0 L1 data.clipping)
      (f data.initial - fLow) T sigma data.clipping (poissonVariance n data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ ∧
    s ^ 2 = data.clipping ^ 2 * d *
      data.multiplier ^ 2 /
        ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hq0 : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
  have hδ0 := PoissonNonemptyMaskGaussianProfile.budget_nonneg T hq0.le
    (by exact_mod_cast data.q_le_one) (one_div_pos.mpr data.multiplier_pos) ε
  have hs := data.normalizedSumNoise_pos hn hd
  have hgD := (data.withSlots g hg D).gradient_measurable
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos hs
  rw [← heta] at hstep
  have hpriv := data.optionalTranscript_nonemptyMask_approxDP hT hε g hg
  refine ⟨hpriv, data.optionalFinal_approxDP_of_transcript hd g hg hpriv,
    data.optionalUniform_approxDP_of_transcript hd hδ0 g hg hpriv, ?_, ?_, ?_⟩
  · have h := normalizedSumNoise_sqrt_sq n d data.q data.clipping
      (data.multiplier ^ 2) (sq_nonneg _)
    simpa only [Real.sqrt_sq data.multiplier_pos.le] using h
  · exact poisson_local_convergence hn hd hT data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial
  · exact poisson_local_uniform_output_convergence hn hd data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial


end Mf.Optimization.PoissonClippedSGD.PrivacyData
