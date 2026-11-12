import Mf.Optimization.PoissonClippedSGD.FinalLaw
import Mf.Optimization.PoissonClippedSGD.UniformOutput
import Mf.Probability.FiniteAdaptivePrefix

/-!
# Independent pre-update output from the raw Poisson transcript

The public transcript reconstructs every pre-update state. Adjoining an
independent index and applying this reconstruction gives exactly the original
Gaussian product-history index/iterate law, including the newest-first seed
convention. These identities do not depend on a privacy accountant.
-/

noncomputable section
open MeasureTheory Mf.Probability.SeedTranscript
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
variable {n d : ℕ}

/-- Retain the independent index together with its publicly reconstructed state. -/
def selectedOutput (data : PrivacyData n d) {T : ℕ}
    (p : Fin T × SumHistory d T) : Fin T × EuclideanSpace ℝ (Fin d) :=
  (p.1, data.state p.1.val (prefixHistory p.1.val p.1.isLt.le p.2))

theorem selectedOutput_measurable (data : PrivacyData n d) (T : ℕ) :
    Measurable (data.selectedOutput (T := T)) := by
  apply measurable_fst.prodMk
  apply measurable_from_prod_countable_right
  intro j
  exact (data.state_measurable j.val).comp (prefixHistory_measurable j.isLt.le)

theorem selectedOutput_seedTranscript (data : PrivacyData n d) (A : Finset (Fin n))
    {T : ℕ} (j : Fin T) (ω : Fin T → AugmentedRelease n d) :
    data.selectedOutput (j, data.seedTranscript A T ω) =
      (j, gaussianIterate data.eta data.q data.clipping (restrictedGradient data.gradient A)
        data.initial T j.val j.isLt.le (fun i => data.normalizedSeed (ω i))) := by
  apply Prod.ext
  · rfl
  change data.state j.val
    (prefixHistory j.val j.isLt.le (encode (data.seedRelease A) T ω)) = _
  rw [prefixHistory_encode]
  change data.state j.val (data.seedTranscript A j.val (seedPrefix j.isLt.le ω)) = _
  rw [data.state_seedTranscript A]
  rfl

/-- The raw transcript and normalized Gaussian history give the same selected pair. -/
theorem selectedOutput_law (data : PrivacyData n d) (A : Finset (Fin n))
    (hd : 0 < d) {T : ℕ} (ν : Measure (Fin T)) [IsProbabilityMeasure ν] :
    (ν.prod (data.transcriptLaw A T)).map data.selectedOutput =
      (ν.prod (gaussianHistoryLaw n d T data.q data.q_le_one
        (normalizedSumNoise n d data.q data.clipping data.multiplier))).map
        (fun p => (p.1, gaussianIterate data.eta data.q data.clipping
          (restrictedGradient data.gradient A) data.initial T p.1.val p.1.isLt.le p.2)) := by
  have hpi : (Measure.pi fun _ : Fin T => data.seedLaw).map
      (fun ω i => data.normalizedSeed (ω i)) =
      gaussianHistoryLaw n d T data.q data.q_le_one
        (normalizedSumNoise n d data.q data.clipping data.multiplier) := by
    rw [Measure.pi_map_pi (f := fun _ : Fin T => data.normalizedSeed)
      (fun _ => data.normalizedSeed_measurable.aemeasurable)]
    simp only [data.normalizedSeed_law hd]
    rfl
  have hn : Measurable (fun (ω : Fin T → AugmentedRelease n d) i =>
      data.normalizedSeed (ω i)) :=
    measurable_pi_lambda _ (fun i => data.normalizedSeed_measurable.comp (measurable_pi_apply i))
  have hg : ∀ i, Measurable (restrictedGradient data.gradient A i) := by
    intro i
    classical
    by_cases hi : i ∈ A
    · unfold restrictedGradient
      simp only [if_pos hi]
      exact data.gradient_measurable i
    · unfold restrictedGradient
      simp only [if_neg hi]
      exact measurable_const
  have ho : Measurable (fun p : Fin T ×
      (Fin T → (Fin n → Bool) × EuclideanSpace ℝ (Fin d)) =>
      (p.1, gaussianIterate data.eta data.q data.clipping
        (restrictedGradient data.gradient A) data.initial T p.1.val p.1.isLt.le p.2)) := by
    apply measurable_fst.prodMk
    apply measurable_from_prod_countable_right
    intro j
    exact gaussianIterate_measurable data.eta data.q data.clipping data.clipping_pos.le
      (restrictedGradient data.gradient A) hg data.initial T j.val j.isLt.le
  have he := data.seedTranscript_measurable A T
  have hp := Measure.map_prod_map ν (Measure.pi fun _ : Fin T => data.seedLaw)
    measurable_id he
  rw [Measure.map_id, data.seedTranscript_law A T] at hp
  have hp' := Measure.map_prod_map ν (Measure.pi fun _ : Fin T => data.seedLaw)
    measurable_id hn
  rw [Measure.map_id, hpi] at hp'
  rw [hp, hp', Measure.map_map (data.selectedOutput_measurable T) (measurable_id.prodMap he),
    Measure.map_map ho (measurable_id.prodMap hn)]
  congr 1
  funext p
  exact data.selectedOutput_seedTranscript A p.1 p.2

/-- Actual independent uniform index and pre-update iterate, retaining the index. -/
def optionalUniformLaw {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (T : ℕ) [NeZero T] (D : Fin n → Option Record) :
    Measure (Fin T × EuclideanSpace ℝ (Fin d)) :=
  (outputLaw n d T data.q data.q_le_one
    (normalizedSumNoise n d data.q data.clipping data.multiplier)).map
    (fun p => (p.1, output data.eta data.q data.clipping (slotGradient g D) data.initial p))

theorem optionalUniformLaw_eq_map {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (hd : 0 < d) (T : ℕ) [NeZero T]
    (D : Fin n → Option Record) :
    data.optionalUniformLaw g T D =
      ((PMF.uniformOfFintype (Fin T)).toMeasure.prod
        (data.optionalTranscriptLaw g hg T D)).map data.selectedOutput := by
  have hstate : (data.withSlots g hg D).selectedOutput (T := T) = data.selectedOutput := by
    funext p
    apply Prod.ext
    · rfl
    exact data.state_withQueries _ _ _ _
  have hgrad : restrictedGradient (slotGradient g D) Finset.univ = slotGradient g D := by
    funext i x
    simp only [restrictedGradient, Finset.mem_univ, if_true]
  have h := (data.withSlots g hg D).selectedOutput_law Finset.univ hd
    (PMF.uniformOfFintype (Fin T)).toMeasure
  rw [hstate] at h
  change ((PMF.uniformOfFintype (Fin T)).toMeasure.prod
    (data.optionalTranscriptLaw g hg T D)).map data.selectedOutput =
    (outputLaw n d T data.q data.q_le_one
      (normalizedSumNoise n d data.q data.clipping data.multiplier)).map
      (fun p => (p.1, output data.eta data.q data.clipping
        (restrictedGradient (slotGradient g D) Finset.univ) data.initial p)) at h
  rw [hgrad] at h
  exact h.symm

end Mf.Optimization.PoissonClippedSGD.PrivacyData
