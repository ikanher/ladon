import Mf.Optimization.PoissonClippedSGD.MixtureTranscript
import Mf.DP.GaussianTestingTranscript

/-!
# Exact Gaussian privacy at full sampling

At `q = 1` the exceptional-record mixture is exactly Gaussian. The actual
adaptive transcript is therefore a common kernel image of a scalar Gaussian
product pair. This supplies both full randomized-testing GDP and its Gaussian
event profile, without the finite Poisson correction. It is the full-sampling
boundary of the extension to Appendix C.4.2 of Koloskova, Hendrikx and Stich,
*Revisiting Gradient Clipping* (ICML 2023).
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.GaussianTesting
namespace Mf.Optimization.PoissonClippedSGD

/-- The full-sampling multiplier variance `T / mu²` gives exact parameter `mu`. -/
theorem fullSamplingGDPParameter {T : ℕ} (hT : 0 < T) {mu : ℝ} (hmu : 0 < mu) :
    Real.sqrt T * (1 / Real.sqrt ((T : ℝ) / mu ^ 2)) = mu := by
  have hTr : (0 : ℝ) < T := by exact_mod_cast hT
  rw [Real.sqrt_div (Nat.cast_nonneg T), Real.sqrt_sq hmu.le]
  field_simp

namespace PrivacyData

/-- A single common kernel supplies both testing and event-profile directions. -/
theorem optionalTranscript_fullSampling_gaussianComparison_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) (hq : data.q = 1) {V : ℝ} (hV : 0 < V)
    (hmult : data.multiplier = Real.sqrt V)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') :
    let mu := Real.sqrt T * (1 / Real.sqrt V)
    GDPTestDominates mu (data.optionalTranscriptLaw g hg T D)
      (data.optionalTranscriptLaw g hg T D') ∧
    GDPTestDominates mu (data.optionalTranscriptLaw g hg T D')
      (data.optionalTranscriptLaw g hg T D) ∧
    EventProfileLE (gdpProfile mu) (data.optionalTranscriptLaw g hg T D)
      (data.optionalTranscriptLaw g hg T D') ∧
    EventProfileLE (gdpProfile mu) (data.optionalTranscriptLaw g hg T D')
      (data.optionalTranscriptLaw g hg T D) := by
  cases n with
  | zero => obtain ⟨i, _⟩ := hdel; exact Fin.elim0 i
  | succ n =>
      obtain ⟨K, hK, hP, hQ⟩ := ActualMixture.optionalTranscript_commonMixtureKernel_variance
        data V hV hmult g hg D D' hdel T
      letI : IsMarkovKernel K := hK
      have ha : 0 < 1 / Real.sqrt V := by positivity
      simp only [hq, GaussianMixtureSimulation.scalarMixture, tsub_self,
        ENNReal.coe_zero, ENNReal.coe_one, zero_smul, one_smul, zero_add] at hP
      have ht := gdpTestDominates_of_commonGaussianKernel hT ha K _ _ hQ hP
      have ep := iidGaussian_eventProfile hT (a := 1 / Real.sqrt V) (b := 0) ha.ne'
      have eq := iidGaussian_eventProfile hT (a := 0) (b := 1 / Real.sqrt V) ha.ne
      rw [sub_zero, abs_of_pos ha] at ep
      rw [zero_sub, abs_neg, abs_of_pos ha] at eq
      have hp := eventProfileLE_bind ep K
      have hq' := eventProfileLE_bind eq K
      rw [hP, hQ] at hp hq'
      exact ⟨ht.2, ht.1, hp, hq'⟩

/-- Exact GDP and its full nonnegative-epsilon event profile for either neighbor order. -/
theorem optionalTranscript_fullSampling_gaussianComparison
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) (hq : data.q = 1) {mu : ℝ} (hmu : 0 < mu)
    (hmult : data.multiplier = Real.sqrt ((T : ℝ) / mu ^ 2))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hadj : OptionalRecordAdjacent D D') :
    GDPTestDominates mu (data.optionalTranscriptLaw g hg T D)
      (data.optionalTranscriptLaw g hg T D') ∧
    EventProfileLE (gdpProfile mu) (data.optionalTranscriptLaw g hg T D)
      (data.optionalTranscriptLaw g hg T D') := by
  have hV : 0 < (T : ℝ) / mu ^ 2 := by positivity
  rcases hadj with hdel | hdel
  · have h := data.optionalTranscript_fullSampling_gaussianComparison_of_deletion
      hT hq hV hmult g hg D D' hdel
    dsimp only at h
    rw [fullSamplingGDPParameter hT hmu] at h
    exact ⟨h.1, h.2.2.1⟩
  · have h := data.optionalTranscript_fullSampling_gaussianComparison_of_deletion
      hT hq hV hmult g hg D' D hdel
    dsimp only at h
    rw [fullSamplingGDPParameter hT hmu] at h
    exact ⟨h.2.1, h.2.2.2⟩

/-- Full sampling yields approximate DP whenever the exact Gaussian profile fits the budget. -/
theorem optionalTranscript_fullSampling_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) (hq : data.q = 1) {mu ε δ : ℝ} (hmu : 0 < mu)
    (hε : 0 ≤ ε) (hδ : 0 ≤ δ) (hbudget : gdpProfile mu ε ≤ δ)
    (hmult : data.multiplier = Real.sqrt ((T : ℝ) / mu ^ 2))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  intro D D' hadj A hA
  haveI : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw; infer_instance
  haveI : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D') := by
    unfold optionalTranscriptLaw; infer_instance
  have hp := (data.optionalTranscript_fullSampling_gaussianComparison
    hT hq hmu hmult g hg D D' hadj).2 ε hε A hA
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A + δ := by linarith
  have h := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at h
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using h

end PrivacyData
end Mf.Optimization.PoissonClippedSGD
