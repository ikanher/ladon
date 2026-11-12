import Mf.DP.PoissonGaussianZeroEpsilonCalibration
import Mf.DP.PoissonCorrectedGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Actual adaptive Poisson SGD at epsilon zero

The public chi-square calibration supplies both directed product bounds.
The pair-specific common kernel constructs the actual adaptive transcript
laws, preserving optional-slot add/remove adjacency and the public qN
normalization. The resulting (0,δ)-DP theorem covers every 0<q≤1 and δ>0;
it assumes neither a privacy budget nor a simulator identity from the caller.
This is the epsilon-zero branch of the generic Revisiting Gradient Clipping
privacy extension, not an exact GDP or optimal-noise claim.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonGaussianZeroEpsilon
open Mf.Probability.SeedTranscript
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both zero-epsilon comparisons for an actual neighboring transcript pair. -/
theorem optionalTranscript_zeroEpsilon_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {δ : ℝ} (hδ : 0 < δ)
    (hmult : data.multiplier = Real.sqrt (calibratedVariance T data.q δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      (data.optionalTranscriptLaw g hg T D').real A + δ ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      (data.optionalTranscriptLaw g hg T D).real A + δ := by
  cases n with
  | zero => obtain ⟨i, _⟩ := hdel; exact Fin.elim0 i
  | succ n =>
      have hq0 : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
      have hV := calibratedVariance_pos hT hq0 hδ
      obtain ⟨K, hK, hP, hQ⟩ := ActualMixture.optionalTranscript_commonMixtureKernel_variance
        data _ hV hmult g hg D D' hdel T
      let : IsMarkovKernel K := hK
      let : IsProbabilityMeasure (GaussianMixtureSimulation.scalarMixture data.q
          (1/Real.sqrt (calibratedVariance T data.q δ))) :=
        GaussianMixtureSimulation.scalarMixture_isProbability data.q data.q_le_one _
      have hf : ∀ B, MeasurableSet B →
          (iidHistoryLaw (GaussianMixtureSimulation.scalarMixture data.q
            (1/Real.sqrt (calibratedVariance T data.q δ))) T).real B ≤
          Real.exp 0 * (iidHistoryLaw (gaussianReal 0 1) T).real B + δ := by
        intro B hB
        simpa only [iidHistoryLaw, Real.exp_zero, one_mul] using
          (calibrated_product_eventBounds hT data.q data.q_le_one hq0 hδ hB).1
      have hr : ∀ B, MeasurableSet B →
          (iidHistoryLaw (gaussianReal 0 1) T).real B ≤
          Real.exp 0 * (iidHistoryLaw (GaussianMixtureSimulation.scalarMixture data.q
            (1/Real.sqrt (calibratedVariance T data.q δ))) T).real B + δ := by
        intro B hB
        simpa only [iidHistoryLaw, Real.exp_zero, one_mul] using
          (calibrated_product_eventBounds hT data.q data.q_le_one hq0 hδ hB).2
      have hforward := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hf K hA
      have hreverse := PoissonCorrectedGaussianProfile.fixed_eventBound_bind hr K hA
      rw [hP, hQ] at hforward hreverse
      simpa only [Real.exp_zero, one_mul] using And.intro hforward hreverse

/-- Public positive noise certifies every adjacent pair at epsilon zero. -/
theorem optionalTranscript_zeroEpsilon_approxDP
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 0 < T) {δ : ℝ} (hδ : 0 < δ)
    (hmult : data.multiplier = Real.sqrt (calibratedVariance T data.q δ))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) 0 δ := by
  intro D D' hadj A hA
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw
    infer_instance
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D') := by
    unfold optionalTranscriptLaw
    infer_instance
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      (data.optionalTranscriptLaw g hg T D').real A + δ := by
    rcases hadj with hdel | hdel
    · exact (data.optionalTranscript_zeroEpsilon_eventBounds_of_deletion
        hT hδ hmult g hg D D' hdel hA).1
    · exact (data.optionalTranscript_zeroEpsilon_eventBounds_of_deletion
        hT hδ hmult g hg D' D hdel hA).2
  have hh := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add measureReal_nonneg hδ.le] at hh
  simpa only [measureReal_def, Real.exp_zero, ENNReal.ofReal_one, one_mul,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using hh

end Mf.Optimization.PoissonClippedSGD.PrivacyData
