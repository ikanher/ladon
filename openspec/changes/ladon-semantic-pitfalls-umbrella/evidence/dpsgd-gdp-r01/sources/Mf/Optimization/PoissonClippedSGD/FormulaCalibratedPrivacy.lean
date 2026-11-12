import Mf.DP.PoissonGaussianFormulaCalibration
import Mf.Optimization.PoissonClippedSGD.ExactProductOptimalPrivacy
/-!
# Actual adaptive privacy from finite exact-CDF calibration

Every admissible Poisson clipped-SGD run at the public formula-selected noise
inherits both directed privacy inequalities through the existing actual common
simulator. The product calibration supplies its own budget and passing index.
The finite selector uses exact scalar CDF values; a certified numerical
implementation is a separate obligation, not claimed here.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.PoissonGaussianHistogram
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The finite formula calibration certifies every actual run at its selected multiplier. -/
theorem optionalTranscript_formulaCalibrated_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) (hT : 0 < T)
    {ε δ : ℝ} (hε : 0 ≤ ε) (hδ : 0 < δ)
    (hδτ : δ < 1-(1-(data.q : ℝ))^T)
    (hmult : data.multiplier = Real.sqrt (formulaCalibratedVariance T data.q ε δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hs := formulaCalibratedVariance_spec T hT data.q data.q_le_one data.q_pos hε hδ hδτ
  apply data.optionalTranscript_approxDP_of_optimalVariance_le hε hδ hδτ _ g hg
  change (PoissonGaussianProductProfile.optimalVariance T data.q data.q_le_one hε hδ hδτ : ℝ) ≤
    data.multiplier^2
  rw [hmult, Real.sq_sqrt hs.1.le]
  exact hs.2.2.1
end Mf.Optimization.PoissonClippedSGD.PrivacyData
