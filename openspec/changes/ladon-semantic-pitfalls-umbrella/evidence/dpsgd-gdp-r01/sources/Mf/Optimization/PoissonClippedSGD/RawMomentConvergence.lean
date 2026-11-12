import Mf.DP.PoissonRawMomentCalibration
import Mf.Optimization.PoissonClippedSGD.RawMomentPrivacy
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.PoissonUniformOutput

/-!
# Public candidate selection, actual privacy and same-noise SGD utility

A finite public list proposes variances, reference margins and moment orders.
The selector tests the complete raw/centered Gaussian-reference budget with
reciprocal and Bennett reverse alternatives, and
retains an explicit fallback on every positive privacy domain. This owner
consumes the selected candidate's proved feasibility to protect the adaptive
Poisson transcript and its outputs. The accepted local-smooth clipped-SGD
utility theorem uses the same selected multiplier and its own public step.

No caller-supplied privacy or budget conclusion is required. Selection uses
exact real comparisons; a floating-point search needs separate certification.
Utility concerns average pre-update or independent uniform gradient norm,
not the final iterate or an ordering of actual errors between algorithms.
-/

noncomputable section
open MeasureTheory
open Mf.DP Mf.DP.PoissonRawMomentCalibration
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- A publicly selected candidate protects every admissible actual transcript. -/
theorem optionalTranscript_rawMoment_approxDP_of_selection
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (p : ℕ) (hp : 2 ≤ p) (cs : List Candidate)
    (hmult : data.multiplier = Real.sqrt (select T data.q ε δ p cs).variance)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have h := select_valid hT (by exact_mod_cast data.q_pos) data.q_le_one hε hδ0 hδ1 p hp cs
  exact data.optionalTranscript_rawMoment_approxDP_of_budget hT h.1 h.2.1 hδ0.le
    _ h.2.2.1 _ h.2.2.2.1 hmult h.2.2.2.2 g hg

/-- A run at the selected variance has privacy and the complete utility envelope,
with the step evaluated at that actual noise. All calibration premises are public. -/
theorem rawMoment_private_convergence_of_selection
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (p : ℕ) (hp : 2 ≤ p) (cs : List Candidate)
    (hmult : data.multiplier = Real.sqrt (select T data.q ε δ p cs).variance)
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
    s ^ 2 = data.clipping ^ 2 * d * (select T data.q ε δ p cs).variance / ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hvalid := select_valid hT (by exact_mod_cast data.q_pos) data.q_le_one hε hδ0 hδ1 p hp cs
  have hVp := hvalid.1
  have hs := data.normalizedSumNoise_pos hn hd
  have hgD := (data.withSlots g hg D).gradient_measurable
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos hs
  rw [← heta] at hstep
  have hpriv := data.optionalTranscript_rawMoment_approxDP_of_selection
    hT hε hδ0 hδ1 p hp cs hmult g hg
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
