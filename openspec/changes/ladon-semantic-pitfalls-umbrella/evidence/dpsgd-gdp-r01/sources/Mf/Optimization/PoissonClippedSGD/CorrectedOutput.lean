import Mf.Optimization.PoissonClippedSGD.CorrectedPrivacy
import Mf.Optimization.PoissonClippedSGD.ApproxDPOutput

/-!
# Finite corrected-profile privacy of the independent Poisson output

The finite Gaussian-reference certificate for the actual adaptive transcript
also protects the independently selected pre-update pair `(J, X_J)`. The public
reconstruction kernel and exact product-history law preserve the original
sampler, noise and step. This supplies output privacy for the extension of
Appendix C.4.2 of Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping*
(ICML 2023); the correction remains part of the privacy budget.
-/

noncomputable section
open MeasureTheory ProbabilityTheory Mf.Probability
open Mf.DP Mf.DP.PoissonCorrectedGaussianProfile
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- A proved complete corrected budget protects the independent index/iterate pair. -/
theorem optionalUniform_corrected_approxDP_of_budget
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d) (hd : 0 < d)
    {V θ ε δ : ℝ} (hV : 0 < V) (hθ : 0 < θ) (hδ : 0 ≤ δ)
    (hmult : data.multiplier = Real.sqrt V)
    (hbudget : poissonCorrectedBudget T data.q V ε θ ≤ δ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ := by
  exact data.optionalUniform_approxDP_of_transcript hd hδ g hg
    (data.optionalTranscript_corrected_approxDP_of_budget
      (Nat.pos_of_ne_zero (NeZero.ne T)) hV hθ hδ hmult hbudget g hg)

/-- The public sufficient variance protects the actual independent uniform output. -/
theorem optionalUniform_corrected_approxDP_of_safeVariance
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d) (hd : 0 < d)
    (hq1 : (data.q : ℝ) < 1)
    {V ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hV : poissonCorrectedSafeVariance T data.q ε δ ≤ V)
    (hmult : data.multiplier = Real.sqrt V)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ := by
  exact data.optionalUniform_corrected_approxDP_of_budget hd
    ((poissonCorrectedSafeVariance_pos T data.q ε δ).trans_le hV)
    (by positivity : 0 < ε / 2) hδ0.le hmult
    (poissonCorrectedBudget_le_delta (Nat.pos_of_ne_zero (NeZero.ne T))
      (by exact_mod_cast data.q_pos) hq1 hε hδ0 hδ1 hV) g hg

end Mf.Optimization.PoissonClippedSGD.PrivacyData
