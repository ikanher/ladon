import Mf.Optimization.PoissonClippedSGD.UniformLaw
import Mf.DP.GaussianTestingTranscript

/-!
# Approximate-DP postprocessing of the Poisson transcript

Any proved event-level approximate-DP guarantee for the fixed transcript law
passes to its actual final iterate and independent index/iterate pair. The
accountant is not an input to the stochastic process: its theorem supplies the
privacy premise consumed by these postprocessing lemmas.
-/

noncomputable section
open MeasureTheory ProbabilityTheory Mf.Probability Mf.DP
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Final-iterate privacy follows from privacy of the actual transcript. -/
theorem optionalFinal_approxDP_of_transcript
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d) (hd : 0 < d)
    {ε δ : ℝ}
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r))
    (hpriv : ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ) :
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ := by
  have h := approxDP_postprocess_map (data.state T) (data.state_measurable T) hpriv
  have heq : data.optionalFinalLaw g T =
      fun D => (data.optionalTranscriptLaw g hg T D).map (data.state T) := by
    funext D
    exact data.optionalFinalLaw_eq_map g hg hd T D
  rw [heq]
  exact h

/-- Independent index/iterate privacy follows from the same transcript guarantee. -/
theorem optionalUniform_approxDP_of_transcript
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d) (hd : 0 < d)
    {ε δ : ℝ} (hδ : 0 ≤ δ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r))
    (hpriv : ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ) :
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ := by
  let ν := (PMF.uniformOfFintype (Fin T)).toMeasure
  let F := fun p : SumHistory d T × Fin T => data.selectedOutput (p.2, p.1)
  have hF : Measurable F := (data.selectedOutput_measurable T).comp measurable_swap
  let K : Kernel (SumHistory d T) (Fin T × EuclideanSpace ℝ (Fin d)) := seedKernel ν F
  haveI : IsProbabilityMeasure ν := by dsimp [ν]; infer_instance
  haveI : IsMarkovKernel K := seedKernel_isMarkov ν F hF
  have hprob (D : Fin n → Option Record) :
      IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw
    infer_instance
  have heq (D : Fin n → Option Record) :
      (data.optionalTranscriptLaw g hg T D).bind K = data.optionalUniformLaw g T D := by
    letI := hprob D
    rw [bind_seedKernel _ ν F hF, data.optionalUniformLaw_eq_map g hg hd T D]
    have hswap : ((data.optionalTranscriptLaw g hg T D).prod ν).map Prod.swap =
        ν.prod (data.optionalTranscriptLaw g hg T D) :=
      Measure.measurePreserving_swap.map_eq
    change ((data.optionalTranscriptLaw g hg T D).prod ν).map F =
      (ν.prod (data.optionalTranscriptLaw g hg T D)).map data.selectedOutput
    rw [← hswap, Measure.map_map (data.selectedOutput_measurable T) measurable_swap]
    rfl
  intro D D' hadj A hA
  letI := hprob D
  letI := hprob D'
  haveI : IsProbabilityMeasure (data.optionalUniformLaw g T D) := by
    rw [← heq D]
    infer_instance
  haveI : IsProbabilityMeasure (data.optionalUniformLaw g T D') := by
    rw [← heq D']
    infer_instance
  have hev (B : Set (SumHistory d T)) (hB : MeasurableSet B) :
      (data.optionalTranscriptLaw g hg T D).real B ≤
        Real.exp ε * (data.optionalTranscriptLaw g hg T D').real B + δ :=
    GaussianTesting.real_le_of_ennreal_eventBound hδ (hpriv D D' hadj B hB)
  have hb : ((data.optionalTranscriptLaw g hg T D).bind K).real A ≤
      Real.exp ε * ((data.optionalTranscriptLaw g hg T D').bind K).real A + δ := by
    rw [GaussianTesting.measureReal_bind K hA, GaussianTesting.measureReal_bind K hA]
    exact GaussianTesting.integral_le_of_eventBound hev (GaussianTesting.isTest_kernel_real K hA)
  rw [heq D, heq D'] at hb
  have h := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at h
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalUniformLaw g T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalUniformLaw g T D') A)] using h
end Mf.Optimization.PoissonClippedSGD.PrivacyData
