import Mf.DP.PoissonCombinedReferenceCalibration
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD at the combined Gaussian-reference calibration

The public policy combines previously proved candidates at the same privacy
parameters, checks any additional public candidates, and retains a proved
fallback. The actual run has transcript/final/uniform approximate privacy and
pre-update/uniform local-smooth utility at its selected noise and own public step.
Its variance is no larger than the pair-family cap, and on the original guarded
domain no larger than twice the explicit variance16 comparator.

The variance inequality is not an inequality between retuned utility envelopes
or actual errors. No privacy/budget conclusion is a premise. This is a consumer
for the finite Gaussian-reference extension of Appendix C.4.2 of Koloskova,
Hendrikx and Stich, *Revisiting Gradient Clipping* (ICML 2023).
-/

noncomputable section
open MeasureTheory
open Mf.DP Mf.DP.PoissonRawMomentCalibration
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The combined policy preserves both variance caps and actual privacy/utility
at the selected noise and its own public step. -/
theorem combinedReference_private_convergence
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hq1 : data.q < 1) (extra : List Candidate)
    (hmult : data.multiplier = Real.sqrt
      (PoissonCombinedReferenceCalibration.selected T data.q ε δ extra).variance)
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
    (PoissonCombinedReferenceCalibration.selected T data.q ε δ extra).variance ≤
      PoissonPairBennettCalibration.calibratedVariance T data.q ε δ ∧
    (PoissonCombinedReferenceCalibration.RestrictedDomain T data.q ε δ →
      (PoissonCombinedReferenceCalibration.selected T data.q ε δ extra).variance ≤
        2*(16*(data.q : ℝ)^2*T*Real.log (1/δ)/ε^2)) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ ∧
    s ^ 2 = data.clipping ^ 2 * d *
      (PoissonCombinedReferenceCalibration.selected T data.q ε δ extra).variance /
        ((data.q : ℝ) * n) ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 1 ≤ T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hq0 : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
  have hq1R : (data.q : ℝ) < 1 := by exact_mod_cast hq1
  refine ⟨PoissonCombinedReferenceCalibration.selected_variance_le_pair
    hT hq0 hq1R hε hδ0 hδ1 extra, ?_, ?_⟩
  · intro hdom
    exact PoissonCombinedReferenceCalibration.selected_variance_le_twice_baseline
      hT hq0 hq1R.le hε hδ0 hdom extra
  · exact data.rawMoment_private_convergence_of_selection hn hd hε hδ0 hδ1
      2 (by norm_num) (PoissonCombinedReferenceCalibration.candidates T data.q ε δ extra)
      hmult hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower

end Mf.Optimization.PoissonClippedSGD.PrivacyData
