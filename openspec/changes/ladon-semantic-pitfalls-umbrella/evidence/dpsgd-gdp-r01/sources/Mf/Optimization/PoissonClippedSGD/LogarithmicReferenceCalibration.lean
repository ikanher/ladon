import Mf.DP.PoissonLogarithmicReferenceCalibration
import Mf.Optimization.PoissonClippedSGD.HighMomentFloorPrivacy
/-!
# Unrestricted logarithmic Gaussian-reference privacy for adaptive SGD

The generic-bound response r01, Theorem 3.3, supplies a complete public
calibration for every positive epsilon, delta in (0,1), positive horizon
and sampling probability through one. Both ordinary reference errors have
already been paid; the existing optional reverse-floor adapter may only
improve the allowance. The common kernel still produces both actual adaptive
transcript laws. No budget, reference-error or small-sampling premise remains.
-/
noncomputable section
open MeasureTheory Mf.DP
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

theorem optionalTranscript_logarithmicReference_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε δ V : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hV : PoissonLogarithmicReferenceCalibration.calibratedVariance T data.q ε δ ≤ V)
    (hmult : data.multiplier = Real.sqrt V)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hq : 0 < (data.q : ℝ) := by exact_mod_cast data.q_pos
  have hv := (PoissonLogarithmicReferenceCalibration.calibratedVariance_pos hT hq hε).trans_le hV
  exact data.optionalTranscript_highMomentFloor_approxDP_of_budget hT hv
    (by linarith) hδ0.le (PoissonLogarithmicReferenceCalibration.order ε (Real.log (1/δ)))
    (PoissonLogarithmicReferenceCalibration.order_ge_two _ _) hmult
    (PoissonLogarithmicReferenceCalibration.calibratedVariance_budget_le hT hq
      data.q_le_one hε hδ0 hδ1 hV) g hg
end Mf.Optimization.PoissonClippedSGD.PrivacyData
