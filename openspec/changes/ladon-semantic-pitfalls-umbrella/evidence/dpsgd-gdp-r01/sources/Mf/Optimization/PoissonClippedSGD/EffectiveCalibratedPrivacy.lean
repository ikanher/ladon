import Mf.DP.PoissonGaussianEffectiveCalibration
import Mf.Optimization.PoissonClippedSGD.ExactProductOptimalPrivacy
/-!
# Actual adaptive privacy from represented-input calibration

The constructed rational finite search supplies its own privacy budget and
passing index. Every admissible run with the selected multiplier inherits both
adjacency directions through the actual common simulator. The primitive q,
epsilon and delta interval streams are inputs; accuracy and feasibility are
proved by the calibration, not supplied by the caller.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.PoissonGaussianHistogram
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The represented-input calibration certifies every actual run at its selected multiplier. -/
theorem optionalTranscript_effectiveCalibrated_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) (hT : 0 < T)
    {ε δ : ℝ} (hε : 0 ≤ ε) (hδ : 0 < δ)
    (hδτ : δ < 1-(1-(data.q : ℝ))^T)
    (aq : RationalScalarInput (data.q : ℝ))
    (aε : RationalScalarInput ε) (aδ : RationalScalarInput δ)
    (hmult : data.multiplier = Real.sqrt (effectiveCalibratedVariance T data.q data.q_le_one aq aε aδ hT data.q_pos hε hδ hδτ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hs := effectiveCalibratedVariance_spec T data.q data.q_le_one aq aε aδ hT data.q_pos hε hδ hδτ
  apply data.optionalTranscript_approxDP_of_optimalVariance_le hε hδ hδτ _ g hg
  change (PoissonGaussianProductProfile.optimalVariance T data.q data.q_le_one hε hδ hδτ : ℝ) ≤
    data.multiplier^2
  rw [hmult, Real.sq_sqrt hs.1.le]
  exact hs.2.2.1
end Mf.Optimization.PoissonClippedSGD.PrivacyData
