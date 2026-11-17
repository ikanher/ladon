import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowTunedFiniteRate
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowNamedNonlinearLimitLaw
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowExactCountSchedule

namespace LadonBatchPairAudit
open Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowGrowingClockMaps
open DPAdamFixedBetaFastSlowFamily
open DPAdamFixedBetaFastSlowHighNoiseResponse
open DPAdamFixedBetaFastSlowHorizonTuning
open DPAdamFixedBetaResponseCoefficientContinuity
noncomputable section

-- Equal scalar beta fields imply equality of the actual proof-carrying coefficient input.
theorem betaSeparation_eq
    (left right : DPAdamMomentRatioInvariant.BetaSeparation)
    (h1 : left.beta1 = right.beta1) (h2 : left.beta2 = right.beta2) :
    left = right := by
  cases left
  cases right
  simp_all

-- A comparison of two supplied actual families: no family-existence claim is hidden here.
theorem same_beta_input {m d : ℕ} (source target : GrowingClockData m d)
    (h1 : source.base.beta1 = target.base.beta1)
    (h2 : source.base.beta2 = target.base.beta2) :
    (source.base.firstPrinciplesAtMesh 0).betaSeparation =
      (target.base.firstPrinciplesAtMesh 0).betaSeparation := by
  apply betaSeparation_eq <;> assumption

theorem common_privacy_slope {m d : ℕ} (source target : GrowingClockData m d)
    (order : ℕ) (delta epsilon slack : ℝ)
    (hs : source.base.effectiveBatch = source.base.samplingRate * (source.base.dataset.card : ℝ))
    (ht : target.base.effectiveBatch = target.base.samplingRate * (target.base.dataset.card : ℝ))
    (hcard : source.base.dataset.card = target.base.dataset.card)
    (hgap : receiptConversion order delta < epsilon) :
    privacySlope source order delta epsilon slack =
      privacySlope target order delta epsilon slack := by
  rw [privacySlope_eq_card_formula source order delta epsilon slack hs hgap,
      privacySlope_eq_card_formula target order delta epsilon slack ht hgap, hcard]

theorem common_clipped_mean {m d : ℕ}
    (source target : FixedNoiseFastSlowFamily m d)
    (hC : source.clipping = target.clipping)
    (hD : source.dataset = target.dataset)
    (hg : source.gradientOracle = target.gradientOracle) :
    clippedGradientMean source = clippedGradientMean target := by
  funext theta
  simp only [clippedGradientMean, hC, hD, hg]

theorem common_limiting_drift {m d : ℕ} (source target : GrowingClockData m d)
    (h1 : source.base.beta1 = target.base.beta1)
    (h2 : source.base.beta2 = target.base.beta2)
    (hC : source.base.clipping = target.base.clipping)
    (mean : (Fin d → ℝ) → (Fin d → ℝ)) :
    source.calibratedSlowDrift mean = target.calibratedSlowDrift mean := by
  funext theta
  simp only [GrowingClockData.calibratedSlowDrift, same_beta_input source target h1 h2, hC]

theorem common_limiting_covariance {m d : ℕ} (source target : GrowingClockData m d)
    (h1 : source.base.beta1 = target.base.beta1)
    (h2 : source.base.beta2 = target.base.beta2) (lambda : ℝ) :
    lambda • DPAdamFixedBetaGaussianResampling.covariance (d := d)
        (source.base.firstPrinciplesAtMesh 0).betaSeparation =
      lambda • DPAdamFixedBetaGaussianResampling.covariance (d := d)
        (target.base.firstPrinciplesAtMesh 0).betaSeparation := by
  rw [same_beta_input source target h1 h2]

theorem common_tuned_coefficient {m d : ℕ} (source target : GrowingClockData m d)
    (h1 : source.base.beta1 = target.base.beta1)
    (h2 : source.base.beta2 = target.base.beta2) (G L : ℝ) :
    Real.sqrt (2 * G / (L * (d : ℝ) *
      DPAdamFixedBetaGaussianReferenceIsotropy.scalarVariance
        (source.base.firstPrinciplesAtMesh 0).betaSeparation)) =
    Real.sqrt (2 * G / (L * (d : ℝ) *
      DPAdamFixedBetaGaussianReferenceIsotropy.scalarVariance
        (target.base.firstPrinciplesAtMesh 0).betaSeparation)) := by
  rw [same_beta_input source target h1 h2]

-- k-fold batch increase, with source count k*t and target count t.
theorem paired_step_scaling (k t c : ℝ) (hk : 0 < k) (ht : 0 < t) :
    c / Real.sqrt t = Real.sqrt k * (c / Real.sqrt (k * t)) := by
  rw [Real.sqrt_mul hk.le]
  field_simp [(Real.sqrt_pos.mpr hk).ne', (Real.sqrt_pos.mpr ht).ne']

theorem paired_dp_multiplier_scaling (k t gamma B : ℝ)
    (hk : 0 < k) (ht : 0 < t) (hgamma : 0 < gamma) :
    (k * B) * Real.sqrt (gamma * t) =
      Real.sqrt k * (B * Real.sqrt (gamma * (k * t))) := by
  rw [show gamma * (k * t) = k * (gamma * t) by ring,
    Real.sqrt_mul hk.le]
  nlinarith [Real.sq_sqrt hk.le]

theorem matched_expected_epochs (k t q : ℝ) : (k * t) * q = t * (k * q) := by ring

#print axioms common_privacy_slope
#print axioms common_clipped_mean
#print axioms common_limiting_drift
#print axioms common_limiting_covariance
#print axioms common_tuned_coefficient
#print axioms paired_step_scaling
#print axioms paired_dp_multiplier_scaling
#print axioms matched_expected_epochs
#print axioms DPAdamFixedBetaFastSlowTunedFiniteRate.tuned_family_learningRate_limit
#print axioms GrowingClockData.calibratedLiteralSlowClockPathLaw_tendsto_namedCovariance
end
end LadonBatchPairAudit
