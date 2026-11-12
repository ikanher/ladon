import Mf.DP.PoissonHighMomentCalibration
import Mf.Optimization.PoissonClippedSGD.HighMomentPrivacy

/-!
# Publicly calibrated Gaussian-reference privacy for Poisson clipped SGD

The higher-moment calibration in the reviewed rate-comparison extension of
Appendix C.4.2 of Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping*
(ICML 2023), certifies every admissible adaptive Poisson clipped-SGD transcript
on the repaired privacy domain. Its public multiplier variance is
`32 q² T log(1/δ) / ε²`; the fixed denominator remains `qN`.

Both optional-record adjacency directions follow from the actual common-mixture
simulator. The scalar budget is constructed by the imported calibration theorem;
no feasibility or privacy premise is required. The exact mathematical contract
is `openspec/changes/revisiting-gc-gdp-rate-comparison-umbrella/proof-contract.md`.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonHighMomentCalibration

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The public variance32 choice certifies the full adaptive transcript,
universally over measurable record queries and optional-record adjacency. -/
theorem optionalTranscript_highMoment_approxDP_of_calibratedVariance
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {ε δ : ℝ}
    (hε : 0 < ε) (hε1 : ε ≤ 1) (hεT : ε ≤ (data.q : ℝ) ^ 2 * T)
    (hδ0 : 0 < δ) (hδ1 : δ ≤ Real.exp (-1))
    (hmult : data.multiplier = Real.sqrt (calibratedVariance T data.q ε δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hell := one_le_log_reciprocal hδ0 hδ1
  obtain ⟨hp, _, _⟩ := publicOrder_bounds hell
  exact data.optionalTranscript_highMoment_approxDP_of_budget hT
    (calibratedVariance_pos hε hε1 hεT hδ0 hδ1)
    (show 0 < ε / 2 by linarith) hδ0.le _ hp hmult
    (poissonHighMomentBudget_calibratedVariance_le hT
      (by exact_mod_cast data.q_pos) data.q_le_one hε hε1 hεT hδ0 hδ1) g hg

end Mf.Optimization.PoissonClippedSGD.PrivacyData
