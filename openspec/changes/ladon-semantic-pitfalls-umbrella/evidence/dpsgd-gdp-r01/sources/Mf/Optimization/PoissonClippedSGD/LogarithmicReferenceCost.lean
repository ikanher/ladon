import Mf.DP.PoissonLogarithmicReferenceCost
import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceCalibration
/-!
# Actual transcript privacy with the constant-15 variance bound

The calibrated run satisfies the unrestricted privacy theorem. On the enlarged
regime epsilon<=1 and Tq²>=epsilon², its same public variance also satisfies
Corollary 3.4's explicit cost. No restriction delta<=exp(-1) is imposed.
-/
noncomputable section
open MeasureTheory Mf.DP
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

theorem optionalTranscript_logarithmicReference_fifteen
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε δ : ℝ} (hε : 0 < ε) (hε1 : ε ≤ 1)
    (hscale : ε^2 ≤ (T : ℝ)*(data.q : ℝ)^2)
    (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hmult : data.multiplier =
      Real.sqrt (PoissonLogarithmicReferenceCalibration.calibratedVariance T data.q ε δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    PoissonLogarithmicReferenceCalibration.calibratedVariance T data.q ε δ ≤
      15*(Real.log (1/δ)+1)*((T : ℝ)*(data.q : ℝ)^2)/ε^2 := by
  refine ⟨data.optionalTranscript_logarithmicReference_approxDP hT hε hδ0 hδ1
    le_rfl hmult g hg,?_⟩
  exact PoissonLogarithmicReferenceCalibration.calibratedVariance_fifteen hT
    (by exact_mod_cast data.q_pos) data.q_le_one hε hε1 hscale hδ0 hδ1
end Mf.Optimization.PoissonClippedSGD.PrivacyData
