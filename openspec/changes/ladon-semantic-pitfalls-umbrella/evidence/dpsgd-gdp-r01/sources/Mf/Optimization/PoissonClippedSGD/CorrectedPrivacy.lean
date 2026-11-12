import Mf.DP.PoissonCorrectedGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Corrected finite privacy for every admissible Poisson clipped-SGD run

The concrete common-mixture simulator transfers the finite corrected profile
to the full adaptive transcript in both optional-record adjacency directions.
The public sufficient variance then supplies an event-level approximate-DP
certificate, with no assumed privacy or law-equality premise.

This implements the privacy portion of the extension to Appendix C.4.2 of
Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping* (ICML 2023).
The noise multiplier is `sqrt(V)`; the fixed public denominator remains `qN`.
The finite correction is part of the certificate: the raw asymptotic Gaussian
profile alone is not asserted to bound this mechanism.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonCorrectedGaussianProfile

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both ordered event comparisons for any single optional-record deletion. -/
theorem optionalTranscript_corrected_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ : ℝ} (hV : 0 < V) (hθ : 0 < θ)
    (hmult : data.multiplier = Real.sqrt V) (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        poissonCorrectedBudget T data.q V ε θ ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D).real A +
        poissonCorrectedBudget T data.q V ε θ := by
  cases n with
  | zero =>
      obtain ⟨i, _⟩ := hdel
      exact Fin.elim0 i
  | succ n =>
      obtain ⟨K, hK, hP, hQ⟩ := ActualMixture.optionalTranscript_commonMixtureKernel_variance
        data V hV hmult g hg D D' hdel T
      let : IsMarkovKernel K := hK
      exact poissonCorrected_actual_eventBounds_of_commonKernel hT data.q data.q_le_one
        (by exact_mod_cast data.q_pos) hV hθ ε K _ _ hP hQ hA

/-- Universal corrected event bound for symmetric optional-record adjacency. -/
theorem optionalTranscript_corrected_eventBound
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ : ℝ} (hV : 0 < V) (hθ : 0 < θ)
    (hmult : data.multiplier = Real.sqrt V) (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hadj : OptionalRecordAdjacent D D') {A : Set (SumHistory d T)}
    (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        poissonCorrectedBudget T data.q V ε θ := by
  rcases hadj with hdel | hdel
  · exact (data.optionalTranscript_corrected_eventBounds_of_deletion
      hT hV hθ hmult ε g hg D D' hdel hA).1
  · exact (data.optionalTranscript_corrected_eventBounds_of_deletion
      hT hV hθ hmult ε g hg D' D hdel hA).2

/-- A sufficient corrected-profile budget certifies actual transcript DP. -/
theorem optionalTranscript_corrected_approxDP_of_budget
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ ε δ : ℝ} (hV : 0 < V) (hθ : 0 < θ) (hδ : 0 ≤ δ)
    (hmult : data.multiplier = Real.sqrt V)
    (hbudget : poissonCorrectedBudget T data.q V ε θ ≤ δ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  intro D D' hadj A hA
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw
    infer_instance
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D') := by
    unfold optionalTranscriptLaw
    infer_instance
  have h := data.optionalTranscript_corrected_eventBound hT hV hθ hmult ε
    g hg D D' hadj hA
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A + δ := by
    linarith
  have hh := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at hh
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using hh

/-- Every variance above the explicit public threshold certifies the full
adaptive transcript, universally over all measurable record queries. -/
theorem optionalTranscript_corrected_approxDP_of_safeVariance
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) (hq1 : (data.q : ℝ) < 1)
    {V ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hV : poissonCorrectedSafeVariance T data.q ε δ ≤ V)
    (hmult : data.multiplier = Real.sqrt V)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  have hVp := lt_of_lt_of_le (poissonCorrectedSafeVariance_pos T data.q ε δ) hV
  exact data.optionalTranscript_corrected_approxDP_of_budget hT hVp
    (show 0 < ε / 2 by linarith) hδ0.le hmult
    (poissonCorrectedBudget_le_delta hT (by exact_mod_cast data.q_pos) hq1 hε hδ0 hδ1 hV)
    g hg

end Mf.Optimization.PoissonClippedSGD.PrivacyData
