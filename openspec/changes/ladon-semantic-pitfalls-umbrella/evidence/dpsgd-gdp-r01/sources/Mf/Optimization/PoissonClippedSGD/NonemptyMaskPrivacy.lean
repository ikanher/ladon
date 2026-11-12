import Mf.DP.PoissonNonemptyMaskBinomialProfile
import Mf.DP.PoissonCorrectedGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Actual adaptive Poisson privacy from the weighted nonempty-mask profile

The actual common simulator transports both directions of the weighted
Gaussian mixture comparison. Each mask retains its own cardinality and
Bernoulli weight. The allowance has an exact binomial-sum representation.
It is produced internally at the run's multiplier, for every epsilon>=0
and 0<q<=1; no assumed mixture identity or accountant budget is required.

This is a finite approximate-DP profile, not exact amplified GDP or a
calibration at a prescribed delta. Public inversion remains a separate
producer in the generic Revisiting Gradient Clipping extension.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonNonemptyMaskGaussianProfile
open Mf.Probability.SeedTranscript
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both weighted Gaussian-mixture comparisons for an actual neighboring transcript pair. -/
theorem optionalTranscript_nonemptyMask_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε : ℝ} (hε : 0 ≤ ε)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        budget T data.q (1/data.multiplier) ε ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D).real A +
        budget T data.q (1/data.multiplier) ε := by
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
        budget T data.q (1/data.multiplier) ε := by
        intro B hB
        simpa only [iidHistoryLaw] using
          (PoissonNonemptyMaskGaussianProfile.product_eventBounds hT data.q data.q_le_one
            (by exact_mod_cast data.q_pos) (one_div_pos.mpr data.multiplier_pos) hε hB).1
      have hr : ∀ B, MeasurableSet B →
          (iidHistoryLaw (gaussianReal 0 1) T).real B ≤
          Real.exp ε * (iidHistoryLaw (GaussianMixtureSimulation.scalarMixture data.q
            (1/data.multiplier)) T).real B +
        budget T data.q (1/data.multiplier) ε := by
        intro B hB
        simpa only [iidHistoryLaw] using
          (PoissonNonemptyMaskGaussianProfile.product_eventBounds hT data.q data.q_le_one
            (by exact_mod_cast data.q_pos) (one_div_pos.mpr data.multiplier_pos) hε hB).2
      have hforward := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hf K hA
      have hreverse := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hr K hA
      rw [hP, hQ] at hforward hreverse
      exact And.intro hforward hreverse

/-- The actual transcript is private at the internally proved weighted allowance. -/
theorem optionalTranscript_nonemptyMask_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {ε : ℝ} (hε : 0 ≤ ε)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε
      (budget T data.q (1/data.multiplier) ε) := by
  intro D D' hadj A hA
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw
    infer_instance
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D') := by
    unfold optionalTranscriptLaw
    infer_instance
  have hδ0 := budget_nonneg T data.q.coe_nonneg
    (by exact_mod_cast data.q_le_one) (one_div_pos.mpr data.multiplier_pos) ε
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        budget T data.q (1/data.multiplier) ε := by
    rcases hadj with hdel | hdel
    · exact (data.optionalTranscript_nonemptyMask_eventBounds_of_deletion hT hε g hg D D' hdel hA).1
    · exact (data.optionalTranscript_nonemptyMask_eventBounds_of_deletion hT hε g hg D' D hdel hA).2
  have hh := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ0,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at hh
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using hh

end Mf.Optimization.PoissonClippedSGD.PrivacyData
