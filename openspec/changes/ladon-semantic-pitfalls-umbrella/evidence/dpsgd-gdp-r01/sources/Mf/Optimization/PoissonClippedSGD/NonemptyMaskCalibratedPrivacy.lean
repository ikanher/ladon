import Mf.DP.PoissonNonemptyMaskQuantileCalibration
import Mf.Optimization.PoissonClippedSGD.NonemptyMaskPrivacy

/-!
# Prescribed-delta adaptive Poisson privacy from the quantile fallback

On 0<delta<1-(1-q)^T, the public TV quantile variance pays the entire
weighted nonempty-mask budget at epsilon zero. The actual transcript theorem
then yields (epsilon,delta)-DP for every epsilon>=0 by monotonicity.
The caller supplies neither a quantile nor a budget-feasibility witness.

This coarse boundary fallback preserves the actual adaptive mechanism,
optional-slot adjacency and public qN normalization. It is not an optimized
weighted-profile inversion or a constant-gap comparison with exact PLD.
-/

noncomputable section
open MeasureTheory
open Mf.DP Mf.DP.PoissonNonemptyMaskGaussianProfile
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- A public positive multiplier certifies the prescribed budget on the below-tau branch. -/
theorem optionalTranscript_nonemptyMask_quantile_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε δ : ℝ} (hε : 0 ≤ ε) (hδ0 : 0 < δ)
    (hδτ : δ < 1 - emptyMass T data.q)
    (hmult : data.multiplier =
      Real.sqrt (PoissonNonemptyMaskQuantileCalibration.calibratedVariance T data.q δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hbase := data.optionalTranscript_nonemptyMask_approxDP hT (ε := 0) le_rfl g hg
  have hb : budget T data.q (1 / data.multiplier) 0 ≤ δ := by
    rw [hmult]
    exact PoissonNonemptyMaskQuantileCalibration.calibrated_budget_zero_le hT
      (by exact_mod_cast data.q_pos) (by exact_mod_cast data.q_le_one) hδ0 hδτ
  exact approxDP_mono_epsilon _ _ (approxDP_mono_delta _ _ hbase hb) hε

end Mf.Optimization.PoissonClippedSGD.PrivacyData
