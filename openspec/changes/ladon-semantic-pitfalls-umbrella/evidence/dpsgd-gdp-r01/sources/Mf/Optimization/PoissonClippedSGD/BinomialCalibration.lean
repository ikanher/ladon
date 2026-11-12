import Mf.DP.PoissonSampledGaussianRenyiCalibration
import Mf.Optimization.PoissonClippedSGD.OptionalPrivacy

/-!
# Finite-binomial public baseline for adaptive Poisson clipped SGD

The independent variance16 baseline of Theorem 11 in the reviewed extension
of Appendix C.4.2 of Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping*
(ICML 2023), applies to every admissible adaptive Poisson transcript.
The multiplier variance is `16 q² T log(1/δ) / ε²`, with fixed denominator qN.

The existing two-sided adaptive Renyi theorem supplies the actual transcript
comparison. The new finite-binomial calibration constructs its full allowance;
no privacy or feasibility premise is required. The exact contract is in
`openspec/changes/revisiting-gc-gdp-rate-comparison-umbrella/proof-contract.md`.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonRenyiCalibration

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

private theorem constant_adaptiveRenyiBudget (rho : ℝ) (T : ℕ) :
    adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ) * rho := by
  induction T with
  | zero => simp
  | succ T ih => simp [adaptiveRenyiBudget_succ, ih, Nat.cast_add, add_mul]

/-- The public variance16 baseline certifies both optional-record adjacency
directions for every admissible adaptive transcript. -/
theorem optionalTranscript_binomial_approxDP_of_calibratedVariance
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) {ε δ : ℝ}
    (hε : 0 < ε) (hε1 : ε ≤ 1) (hεT : ε ≤ (data.q : ℝ) ^ 2 * T)
    (hδ0 : 0 < δ) (hδ1 : δ ≤ Real.exp (-1))
    (hmult : data.multiplier = Real.sqrt (calibratedVariance T data.q ε δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  let m := publicOrder (Real.log (1 / δ)) ε
  have hm : 2 ≤ m := (publicOrder_bounds (logScale_ge_one hδ0 hδ1) hε hε1).1
  have hV := calibratedVariance_pos hε hεT hδ0 hδ1
  have hdelta := tailBudget_calibratedVariance_le (T := T)
    (by exact_mod_cast data.q_pos.le) data.q_le_one hε hε1 hεT hδ0 hδ1
  apply approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T ε)
  simp only [constant_adaptiveRenyiBudget, SDE.euclideanSampledGaussianSharpStepRho,
    hmult, Real.sq_sqrt hV.le, m]
  convert hdelta using 1 <;> rfl

end Mf.Optimization.PoissonClippedSGD.PrivacyData
