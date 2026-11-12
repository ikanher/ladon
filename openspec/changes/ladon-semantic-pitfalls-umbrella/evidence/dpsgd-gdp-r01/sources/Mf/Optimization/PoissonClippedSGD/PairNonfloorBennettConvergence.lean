import Mf.DP.PoissonPairNonfloorBennettCalibration
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD privacy and utility at the public pair/non-floor Bennett calibration

The symbolic pair-forward/non-floor-reverse calibration supplies the complete privacy budget
internally for every positive epsilon, delta in (0,1), 0<q<1 and positive horizon.
The same multiplier and its own public step feed the local-smooth clipped-SGD
utility theorem. Population, dimension, clipping, queries and objective remain
quantified, under the existing gradient and stochastic-variance hypotheses.

This extends the finite Gaussian-reference analysis of Appendix C.4.2 of
Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping* (ICML 2023).
It proves transcript/final/uniform approximate privacy and average pre-update
or independent uniform gradient-norm utility. It does not compare actual errors,
prove final-iterate utility, or assert a uniform noise gap to PLD. The separate
existing exact-Gaussian consumer covers q=1.
-/

noncomputable section
open MeasureTheory
open Mf.DP
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Every run at the public pair/non-floor Bennett variance has transcript/output privacy
and the full local-smooth utility envelope at its own noise and public step. -/
theorem pairNonfloorBennett_private_convergence
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hq1 : data.q < 1)
    (hmult : data.multiplier =
      Real.sqrt (PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ))
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
      PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ /
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
  have hq1R : (data.q : ℝ) < 1 := by exact_mod_cast hq1
  have hVp := PoissonPairNonfloorBennettCalibration.calibratedVariance_pos
    hT hq0 hq1R hε (delta := δ)
  have hbudget := PoissonPairNonfloorBennettCalibration.complete_budget_le
    hT hq0 hq1R hε hδ0 hδ1 le_rfl
  have hs := data.normalizedSumNoise_pos hn hd
  have hgD := (data.withSlots g hg D).gradient_measurable
  have hstep := poisson_publicStepsize_spec (N := n)
    (by exact_mod_cast data.q_pos : (0 : ℝ) < data.q)
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 hL1 data.clipping_pos hs
  rw [← heta] at hstep
  have hpriv := data.optionalTranscript_rawMoment_approxDP_of_budget hT hVp
    (by linarith : 0 < ε / 2) hδ0.le
    (PoissonPairBennettCalibration.publicOrder (ε / 2) δ)
    (PoissonPairBennettCalibration.publicOrder_ge_two _ _) 1 (by norm_num)
    hmult hbudget g hg
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
