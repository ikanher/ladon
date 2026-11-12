import Mf.DP.PoissonSampledGaussianUnrestrictedCalibration
import Mf.Optimization.PoissonClippedSGD.OptionalPrivacy
/-!
# Unrestricted direct-binomial privacy for the actual adaptive transcript

The generic-bound response r01, Theorem 4.3, is applied to the sharp two-sided
adaptive Renyi theorem. Every positive epsilon, delta in (0,1), positive
horizon and sampling probability through one is covered. The sampler,
optional-slot adjacency, clipping and public qN normalization are unchanged.
-/
noncomputable section
open MeasureTheory ProbabilityTheory Mf.DP Mf.DP.PoissonRenyiCalibration
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
private theorem constant_adaptiveRenyiBudget (rho : ℝ) (T : ℕ) :
    adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ)*rho := by
  induction T with
  | zero => simp
  | succ T ih => simp [adaptiveRenyiBudget_succ,ih,Nat.cast_add,add_mul]

theorem optionalTranscript_unrestrictedBinomial_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hmult : data.multiplier = Real.sqrt (unrestrictedBinomialVariance T data.q ε δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  let m := publicOrder (Real.log (1/δ)) ε
  have hm : 2 ≤ m := (publicOrder_unrestricted_bounds (logScale_pos hδ0 hδ1) hε).1
  have hq : 0 < (data.q : ℝ) := by exact_mod_cast data.q_pos
  have hM : 0 < (data.q : ℝ)^2*T := mul_pos (sq_pos_of_pos hq) (by exact_mod_cast hT)
  have hV := unrestrictedBinomialVariance_pos hM hε hδ0 hδ1
  have hdelta := tailBudget_unrestrictedBinomialVariance_le hq.le data.q_le_one hM hε hδ0 hδ1
  apply approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T ε)
  simp only [constant_adaptiveRenyiBudget,SDE.euclideanSampledGaussianSharpStepRho,
    hmult,Real.sq_sqrt hV.le,m]
  convert hdelta using 1 <;> rfl

theorem optionalTranscript_unrestrictedBinomial_approxDP_of_variance_ge
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    {W : ℝ} (hW : unrestrictedBinomialVariance T data.q ε δ ≤ W)
    (hmult : data.multiplier = Real.sqrt W)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  let m := publicOrder (Real.log (1/δ)) ε
  have hm : 2 ≤ m := (publicOrder_unrestricted_bounds (logScale_pos hδ0 hδ1) hε).1
  have hq : 0 < (data.q : ℝ) := by exact_mod_cast data.q_pos
  have hM : 0 < (data.q : ℝ)^2*T := mul_pos (sq_pos_of_pos hq) (by exact_mod_cast hT)
  have hV := (unrestrictedBinomialVariance_pos hM hε hδ0 hδ1).trans_le hW
  have hdelta := tailBudget_unrestrictedBinomialVariance_le_of_ge hq.le data.q_le_one hM hε hδ0 hδ1 hW
  apply approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T ε)
  simp only [constant_adaptiveRenyiBudget,SDE.euclideanSampledGaussianSharpStepRho,
    hmult,Real.sq_sqrt hV.le,m]
  convert hdelta using 1 <;> rfl
end Mf.Optimization.PoissonClippedSGD.PrivacyData
