import Mf.DP.PoissonSampledGaussianRenyiLogScale
import Mf.Optimization.PoissonClippedSGD.BinomialCalibration
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput

/-!
# Explicit constants for the actual Poisson DP-SGD law

Theorem 1 in `latex/natural-language/poisson_gaussian_lambert_w_constants.tex`
gives constants `c₁ = 1`, `c₂ = 4` for the scaling of Abadi et al.,
*Deep Learning with Differential Privacy* (CCS 2016), on the explicit domain
`0 < ε ≤ min(log(1/δ), q² T)`. These theorems consume the exact conditional
sampled-Gaussian bound and the actual adaptive optional-record transcript,
including every larger multiplier and the actual final-iterate law.

No fixed-size sampling or random reshuffling is substituted for Poisson
sampling, and the public denominator remains `qN` on both neighboring inputs.
-/

noncomputable section
open MeasureTheory ProbabilityTheory Mf.DP Mf.DP.PoissonRenyiCalibration
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

private theorem constant_budget (rho : ℝ) (T : ℕ) :
    adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ) * rho := by
  induction T with
  | zero => simp
  | succ T ih => simp [adaptiveRenyiBudget_succ, ih, Nat.cast_add, add_mul]

/-- Both adjacency directions for the actual transcript at variance16 or above,
assuming only the logarithmic epsilon restriction. -/
theorem optionalTranscript_binomial_approxDP_of_variance_ge_logScale
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : calibratedVariance T data.q ε δ ≤ data.multiplier ^ 2)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  let m := publicOrder (Real.log (1 / δ)) ε
  have hm : 2 ≤ m := (publicOrder_bounds_of_le_logScale hε hεlog).1
  have hdelta := tailBudget_le_of_le_logScale (T := T)
    (by exact_mod_cast data.q_pos.le) data.q_le_one hε hεlog hεT hδ hmult
  apply approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T ε)
  simp only [constant_budget, SDE.euclideanSampledGaussianSharpStepRho, m]
  convert hdelta using 1
  rfl

/-- The natural-language multiplier formula with explicit constants one and four
certifies the full adaptive optional-record transcript. -/
theorem optionalTranscript_approxDP_of_explicit_constants
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  apply data.optionalTranscript_binomial_approxDP_of_variance_ge_logScale
    hε hεlog hεT hδ
    (calibratedVariance_le_sq_of_multiplier_ge data.q.coe_nonneg hε
      (hε.le.trans hεlog) hmult) g hg

/-- The same explicit constants certify the actual final iterate. -/
theorem optionalFinal_approxDP_of_explicit_constants
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) (hd : 0 < d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ :=
  data.optionalFinal_approxDP_of_transcript hd g hg
    (data.optionalTranscript_approxDP_of_explicit_constants hε hεlog hεT hδ hmult g hg)

end Mf.Optimization.PoissonClippedSGD.PrivacyData
