import Mf.DP.PoissonGaussianRareEvent
import Mf.DP.PoissonCorrectedGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Actual adaptive Poisson SGD privacy from rare participation

Every positive multiplier is sufficient when delta >= 1-(1-q)^T.
The proof constructs the actual common simulator and transports the product
likelihood-floor bound in both directions. Epsilon may be any nonnegative
real, including zero. No calibration equation or privacy-budget witness is
supplied by the caller. Public normalization qN and optional-slot add/remove
adjacency are unchanged.

This is the rare-event branch of the generic Revisiting Gradient Clipping
extension. It gives sufficient privacy for arbitrary positive noise, not
an exact-profile endpoint or optimality theorem.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonGaussianRareEvent
open Mf.Probability.SeedTranscript
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both rare-event comparisons for an actual neighboring transcript pair. -/
theorem optionalTranscript_rareEvent_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      (data.optionalTranscriptLaw g hg T D').real A + samplingExposure T data.q ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      (data.optionalTranscriptLaw g hg T D).real A + samplingExposure T data.q := by
  cases n with
  | zero => obtain ⟨i, _⟩ := hdel; exact Fin.elim0 i
  | succ n =>
      obtain ⟨K, hK, hP, hQ⟩ := ActualMixture.optionalTranscript_commonMixtureKernel
        data g hg D D' hdel T
      let : IsMarkovKernel K := hK
      let : IsProbabilityMeasure (GaussianMixtureSimulation.scalarMixture data.q
          (1/data.multiplier)) :=
        GaussianMixtureSimulation.scalarMixture_isProbability data.q data.q_le_one _
      have hf : ∀ B, MeasurableSet B →
          (iidHistoryLaw (GaussianMixtureSimulation.scalarMixture data.q
            (1/data.multiplier)) T).real B ≤
          Real.exp 0 * (iidHistoryLaw (gaussianReal 0 1) T).real B + samplingExposure T data.q := by
        intro B hB
        simpa only [iidHistoryLaw, Real.exp_zero, one_mul] using
          (PoissonGaussianRareEvent.product_eventBounds T data.q data.q_le_one
            (1/data.multiplier) hB).1
      have hr : ∀ B, MeasurableSet B →
          (iidHistoryLaw (gaussianReal 0 1) T).real B ≤
          Real.exp 0 * (iidHistoryLaw (GaussianMixtureSimulation.scalarMixture data.q
            (1/data.multiplier)) T).real B + samplingExposure T data.q := by
        intro B hB
        simpa only [iidHistoryLaw, Real.exp_zero, one_mul] using
          (PoissonGaussianRareEvent.product_eventBounds T data.q data.q_le_one
            (1/data.multiplier) hB).2
      have hforward := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hf K hA
      have hreverse := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hr K hA
      rw [hP, hQ] at hforward hreverse
      simpa only [Real.exp_zero, one_mul] using And.intro hforward hreverse

/-- Every positive multiplier gives (epsilon,delta)-DP above the rare-event threshold. -/
theorem optionalTranscript_rareEvent_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    {ε δ : ℝ} (hε : 0 ≤ ε) (hδ : samplingExposure T data.q ≤ δ)
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
  have hδ0 : 0 ≤ δ :=
    (samplingExposure_nonneg T data.q.coe_nonneg (by exact_mod_cast data.q_le_one)).trans hδ
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      (data.optionalTranscriptLaw g hg T D').real A + samplingExposure T data.q := by
    rcases hadj with hdel | hdel
    · exact (data.optionalTranscript_rareEvent_eventBounds_of_deletion g hg D D' hdel hA).1
    · exact (data.optionalTranscript_rareEvent_eventBounds_of_deletion g hg D' D hdel hA).2
  have hexp : 1 ≤ Real.exp ε := Real.one_le_exp_iff.mpr hε
  have hevent : (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A + δ := by
    have hm := mul_le_mul_of_nonneg_right hexp
      (show 0 ≤ (data.optionalTranscriptLaw g hg T D').real A from measureReal_nonneg)
    linarith
  have hh := ENNReal.ofReal_le_ofReal hevent
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ0,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at hh
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using hh

end Mf.Optimization.PoissonClippedSGD.PrivacyData
