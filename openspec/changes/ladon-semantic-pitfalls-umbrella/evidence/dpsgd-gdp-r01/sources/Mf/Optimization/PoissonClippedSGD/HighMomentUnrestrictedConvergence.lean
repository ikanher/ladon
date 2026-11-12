import Mf.DP.PoissonHighMomentUnrestrictedCalibration
import Mf.Optimization.PoissonClippedSGD.RawMomentPrivacy
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.PoissonUniformOutput

/-!
# All-parameter higher-moment privacy and same-noise clipped-SGD utility

For every positive epsilon, delta in `(0,1)` and public integer moment order
at least two, the sufficient higher-moment variance certifies the actual
adaptive Poisson transcript in both optional-slot adjacency directions.
The raw-moment forward alternative and optional zero reverse error preserve
this fallback guarantee. Its final iterate and independent uniform pre-update
output inherit privacy.
The accepted local-smooth extension of Appendix C.4.2 of Koloskova, Hendrikx
and Stich, *Revisiting Gradient Clipping* (ICML 2023), supplies the full
six-term utility envelope at exactly that run's noise and public stepsize.

This is a conservative domain-coverage fallback. The sharper asymmetric
reference policy and a comparison to PLD noise levels require separate
producers; neither follows from this sufficient calibration. No final-iterate
utility or exact amplified GDP is asserted.
-/

noncomputable section
open MeasureTheory
open Mf.DP Mf.DP.PoissonHighMomentCalibration
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The public higher-moment fallback protects every admissible adaptive
transcript, without an upper bound on epsilon or a budget-feasibility premise. -/
theorem optionalTranscript_highMoment_approxDP_of_unrestrictedVariance
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (p : ℕ) (hp : 2 ≤ p)
    (hV : unrestrictedVariance T data.q ε δ p ≤ V)
    (hmult : data.multiplier = Real.sqrt V)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  exact data.optionalTranscript_rawMoment_approxDP_of_budget hT
    ((unrestrictedVariance_pos T data.q ε δ p hp).trans_le hV)
    (by linarith : 0 < ε / 2) hδ0.le p hp 1 (by decide) hmult
    ((PoissonRawMomentGaussianProfile.budget_le_floorBudget T data.q V ε (ε / 2) p 1).trans
      ((PoissonHighMomentFloor.budget_le_highMomentBudget hT
      (by exact_mod_cast data.q_pos)
      ((unrestrictedVariance_pos T data.q ε δ p hp).trans_le hV)
      (by linarith : 0 < ε / 2) p hp).trans
      (poissonHighMomentBudget_unrestrictedVariance_le hT
        (by exact_mod_cast data.q_pos) data.q_le_one hε hδ0 hδ1 p hp hV))) g hg

/-- Every run at or above the public variance threshold, with its own public
stepsize, has transcript/output privacy and the six-term local-smooth utility
bound. The only variance premise is the explicit public threshold. -/
theorem highMoment_private_convergence_of_unrestrictedVariance
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {V ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (p : ℕ) (hp : 2 ≤ p)
    (hV : unrestrictedVariance T data.q ε δ p ≤ V)
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
  have hVp := (unrestrictedVariance_pos T data.q ε δ p hp).trans_le hV
  have hs := data.normalizedSumNoise_pos hn hd
  have hgD := (data.withSlots g hg D).gradient_measurable
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos hs
  rw [← heta] at hstep
  have hpriv := data.optionalTranscript_highMoment_approxDP_of_unrestrictedVariance
    hT hε hδ0 hδ1 p hp hV hmult g hg
  refine ⟨hpriv, data.optionalFinal_approxDP_of_transcript hd g hg hpriv,
    data.optionalUniform_approxDP_of_transcript hd hδ0.le g hg hpriv, ?_, ?_, ?_⟩
  · rw [hmult]
    exact normalizedSumNoise_sqrt_sq n d data.q data.clipping V hVp.le
  · exact poisson_local_convergence hn hd hT data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial
  · exact poisson_local_uniform_output_convergence hn hd data.q data.q_pos data.q_le_one
      data.clipping_pos hs hstep.1 hsigma hL0 hL1 hstep.2 (slotGradient g D) hgD
      f hf hloc hvariance fLow hlower data.initial

end Mf.Optimization.PoissonClippedSGD.PrivacyData
