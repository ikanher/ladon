import Mf.DP.PoissonGaussianProductProfile
import Mf.DP.PoissonCorrectedGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Exact product-profile upper bound for adaptive Poisson SGD

The actual common simulator transports both directed event inequalities from
the exact sampled-Gaussian product benchmark. The raw scalar variance is the
square of the run's noise multiplier and the scalar sensitivity is one.
There is no assumed privacy allowance, mixture identity or calibration.

This theorem supplies the exact-product upper benchmark for the generic
extension of Appendix C.4.2 of Koloskova, Hendrikx and Stich,
*Revisiting Gradient Clipping* (ICML 2023). It does not identify the profile
of each individual optimization problem with the worst-case product profile,
construct an attaining query, or prove optimal calibrated variance.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonGaussianProductProfile
open Mf.Probability.SeedTranscript
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both exact product-profile comparisons for an actual neighboring transcript pair. -/
theorem optionalTranscript_exactProduct_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        profile T data.q data.q_le_one
        ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D).real A +
        profile T data.q data.q_le_one
        ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε := by
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
          Real.exp ε * (iidHistoryLaw (gaussianReal 0 1) T).real B +
        profile T data.q data.q_le_one
        ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε := by
        intro B hB
        -- Expose the real value of the positive multiplier inside the product law.
        convert
          (PoissonGaussianProductProfile.standardized_eventBounds T data.q data.q_le_one
            (⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal)
            (by exact_mod_cast data.multiplier_pos) ε hB).1 using 1 <;> rfl
      have hr : ∀ B, MeasurableSet B →
          (iidHistoryLaw (gaussianReal 0 1) T).real B ≤
          Real.exp ε * (iidHistoryLaw (GaussianMixtureSimulation.scalarMixture data.q
            (1/data.multiplier)) T).real B +
        profile T data.q data.q_le_one
        ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε := by
        intro B hB
        -- Expose the real value of the positive multiplier inside the product law.
        convert
          (PoissonGaussianProductProfile.standardized_eventBounds T data.q data.q_le_one
            (⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal)
            (by exact_mod_cast data.multiplier_pos) ε hB).2 using 1 <;> rfl
      have hforward := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hf K hA
      have hreverse := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hr K hA
      rw [hP, hQ] at hforward hreverse
      exact And.intro hforward hreverse

/-- The actual transcript is private at the exact raw product benchmark. -/
theorem optionalTranscript_exactProduct_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε
      (profile T data.q data.q_le_one
        ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε) := by
  intro D D' hadj A hA
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw
    infer_instance
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D') := by
    unfold optionalTranscriptLaw
    infer_instance
  have hδ0 := profile_nonneg T data.q data.q_le_one
    ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        profile T data.q data.q_le_one
        ((⟨data.multiplier, data.multiplier_pos.le⟩ : NNReal) ^ 2) ε := by
    rcases hadj with hdel | hdel
    · exact (data.optionalTranscript_exactProduct_eventBounds_of_deletion ε g hg D D' hdel hA).1
    · exact (data.optionalTranscript_exactProduct_eventBounds_of_deletion ε g hg D' D hdel hA).2
  have hh := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ0,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at hh
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using hh

end Mf.Optimization.PoissonClippedSGD.PrivacyData
