import Mf.DP.PoissonGaussianProductProfileAttainment
import Mf.Optimization.PoissonClippedSGD.ExactProductPrivacy

/-!
# Adaptive privacy at the exact product benchmark's feasible variances

Below the sampling-exposure threshold, the exact product profile has an
attained least feasible variance. Every actual adaptive Poisson SGD run with
at least that multiplier variance satisfies the requested privacy budget.
At or above exposure, every positive multiplier satisfies it.

The profile inequalities are produced by the exact benchmark's feasible-set
theorems and transported through the constructed common simulator. The least
variance is an exact-real comparison object, not a certified numerical
calibration. No equality with an individual optimizer's privacy profile,
optimal utility, or finite-computation guarantee is asserted.
-/

noncomputable section
open MeasureTheory
open Mf.DP Mf.DP.PoissonGaussianProductProfile
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Variance above the attained exact product minimum certifies the actual transcript. -/
theorem optionalTranscript_approxDP_of_optimalVariance_le
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    {ε δ : ℝ} (hε : 0 ≤ ε) (hδ0 : 0 < δ)
    (hδτ : δ < 1 - (1 - (data.q : ℝ)) ^ T)
    (hvariance : optimalVariance T data.q data.q_le_one hε hδ0 hδτ ≤
      (⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hbudget := ((optimalVariance_spec T data.q data.q_le_one hε hδ0 hδτ).2.2
    ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2)).mpr hvariance
  exact approxDP_mono_delta _ _
    (data.optionalTranscript_exactProduct_approxDP ε g hg) hbudget

/-- At or above exposure, the exact profile certifies every actual positive-noise run. -/
theorem optionalTranscript_exactProduct_exposure_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    {ε δ : ℝ} (hε : 0 ≤ ε)
    (hτδ : 1 - (1 - (data.q : ℝ)) ^ T ≤ δ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hV : (0 : NNReal) < (⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2 :=
    pow_pos (by exact_mod_cast data.multiplier_pos) 2
  have hbudget := (profile_le_exposure T data.q data.q_le_one hε hV).trans hτδ
  exact approxDP_mono_delta _ _
    (data.optionalTranscript_exactProduct_approxDP ε g hg) hbudget

end Mf.Optimization.PoissonClippedSGD.PrivacyData
