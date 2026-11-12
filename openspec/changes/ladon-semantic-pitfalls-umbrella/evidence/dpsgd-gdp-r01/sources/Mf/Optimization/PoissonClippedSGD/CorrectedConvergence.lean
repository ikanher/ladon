import Mf.Optimization.PoissonClippedSGD.CorrectedOutput
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.PoissonUniformOutput

/-!
# Corrected-profile privacy and local-smooth utility at the same noise

This extends Appendix C.4.2 of Koloskova, Hendrikx and Stich, *Revisiting
Gradient Clipping* (ICML 2023). The finite Poisson Gaussian-reference budget
certifies the adaptive transcript and its final iterate. The utility theorem
uses precisely that run's multiplier, public normalization and stepsize, for
every positive clipping threshold. Its gradient bound concerns the average
pre-update iterate and the independent uniform output, not the final iterate.

The sufficient variance is a finite corrected-profile certificate; it does
not assert that the asymptotic Gaussian parameter is an exact GDP guarantee.
-/

noncomputable section
open MeasureTheory
open Mf.DP Mf.DP.PoissonCorrectedGaussianProfile
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD

namespace PrivacyData
variable {n d : ℕ}

/-- A complete finite budget also protects the actual final iterate. -/
theorem optionalFinal_corrected_approxDP_of_budget
    {T : ℕ} {Record : Type} (data : PrivacyData n d) (hd : 0 < d)
    (hT : 1 ≤ T) {V θ ε δ : ℝ} (hV : 0 < V) (hθ : 0 < θ) (hδ : 0 ≤ δ)
    (hmult : data.multiplier = Real.sqrt V)
    (hbudget : poissonCorrectedBudget T data.q V ε θ ≤ δ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ := by
  exact data.optionalFinal_approxDP_of_transcript hd g hg
    (data.optionalTranscript_corrected_approxDP_of_budget hT hV hθ hδ hmult hbudget g hg)

/-- Public sufficient calibration protects the actual final iterate for every larger variance. -/
theorem optionalFinal_corrected_approxDP_of_safeVariance
    {T : ℕ} {Record : Type} (data : PrivacyData n d) (hd : 0 < d)
    (hT : 1 ≤ T) (hq1 : (data.q : ℝ) < 1)
    {V ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hV : poissonCorrectedSafeVariance T data.q ε δ ≤ V)
    (hmult : data.multiplier = Real.sqrt V)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ := by
  exact data.optionalFinal_corrected_approxDP_of_budget hd hT
    ((poissonCorrectedSafeVariance_pos T data.q ε δ).trans_le hV)
    (by positivity : 0 < ε / 2) hδ0.le hmult
    (poissonCorrectedBudget_le_delta hT (by exact_mod_cast data.q_pos) hq1 hε hδ0 hδ1 hV)
    g hg

/-- Every admissible public run has finite corrected privacy and arbitrary-clipping
local-smooth utility at its very same noise and step. Smoothness is required only
for the utility dataset; the privacy assertion quantifies over all neighbors. -/
theorem corrected_private_convergence_of_budget
    {T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {V θ ε δ : ℝ} (hV : 0 < V) (hθ : 0 < θ) (hδ : 0 ≤ δ)
    (hmult : data.multiplier = Real.sqrt V)
    (hbudget : poissonCorrectedBudget T data.q V ε θ ≤ δ)
    {sigma L0 L1 : ℝ} (heta : 0 < data.eta)
    (hsigma : 0 ≤ sigma) (hL0 : 0 < L0) (hL1 : 0 ≤ L1)
    (hsteps : StepConditions data.eta L0 L1 (1 + poissonVariance n data.q)
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
    s ^ 2 = data.clipping ^ 2 * d * V / ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hs := data.normalizedSumNoise_pos hn hd
  have hgD := (data.withSlots g hg D).gradient_measurable
  refine ⟨data.optionalTranscript_corrected_approxDP_of_budget hT hV hθ hδ hmult hbudget g hg,
    data.optionalFinal_corrected_approxDP_of_budget hd hT hV hθ hδ hmult hbudget g hg,
    data.optionalUniform_corrected_approxDP_of_budget hd hV hθ hδ hmult hbudget g hg,
    ?_, ?_, ?_⟩
  · rw [hmult]
    exact normalizedSumNoise_sqrt_sq n d data.q data.clipping V hV.le
  · exact poisson_local_convergence hn hd hT data.q data.q_pos data.q_le_one
      data.clipping_pos hs heta hsigma hL0 hL1 hsteps (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial
  · exact poisson_local_uniform_output_convergence hn hd data.q data.q_pos data.q_le_one
      data.clipping_pos hs heta hsigma hL0 hL1 hsteps (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial

/-- Every variance at least the public sufficient threshold, with the public
stepsize evaluated at that actual variance, supplies the complete finite privacy
budget and the local-smooth utility bound. No noise-to-utility monotonicity or
proportional improvement after retuning the step is asserted. -/
theorem corrected_private_convergence_of_safeVariance
    {T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    (hq1 : (data.q : ℝ) < 1)
    {V ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hV : poissonCorrectedSafeVariance T data.q ε δ ≤ V)
    (hmult : data.multiplier = Real.sqrt V)
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
    s ^ 2 = data.clipping ^ 2 * d * V / ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 0 < T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hVp := (poissonCorrectedSafeVariance_pos T data.q ε δ).trans_le hV
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos (data.normalizedSumNoise_pos hn hd)
  rw [← heta] at hstep
  exact data.corrected_private_convergence_of_budget hn hd hVp
    (by positivity : 0 < ε / 2) hδ0.le hmult
    (poissonCorrectedBudget_le_delta hT (by exact_mod_cast data.q_pos) hq1 hε hδ0 hδ1 hV)
    hstep.1 hsigma hL0 hL1 hstep.2 g hg D f hf hloc hvariance fLow hlower

end PrivacyData
end Mf.Optimization.PoissonClippedSGD
