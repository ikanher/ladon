import Mf.DP.PoissonAdaptiveQueryCalibration
import Mathlib.Probability.Kernel.Composition.Lemmas

/-!
# Public random initialization for full-history Poisson queries

Theorem 1 of `latex/natural-language/poisson_gaussian_lambert_w_constants.tex`
allows a data-independent initial random seed. Jointly measurable seed/history
queries produce a genuine conditional transcript kernel. Its value at each
seed is proved equal to the previously constructed Poisson transcript law.
Integrating the uniform privacy bound proves privacy even when the seed is
released with the transcript; common randomized postprocessing preserves it.
-/

section
-- Identify the custom finite-history measurable spaces with their recursive products.
set_option backward.isDefEq.respectTransparency false
set_option backward.isDefEq.respectTransparency.types false

open MeasureTheory ProbabilityTheory
namespace Mf.DP
/-- Releasing a data-independent random seed along with a uniformly private
conditional output preserves the same approximate-DP guarantee. -/
theorem approxDP_publicSeed
    {Dataset Seed Output : Type} [MeasurableSpace Seed] [MeasurableSpace Output]
    (adj : Dataset → Dataset → Prop) (μ : Measure Seed) [IsProbabilityMeasure μ]
    (κ : Dataset → Kernel Seed Output) [∀ D, IsSFiniteKernel (κ D)]
    {ε δ : ℝ}
    (hDP : ∀ seed, ApproxDP adj (fun D => κ D seed) ε δ) :
    ApproxDP adj (fun D => μ ⊗ₘ κ D) ε δ := by
  intro left right hadj s hs
  rw [Measure.compProd_apply hs, Measure.compProd_apply hs]
  calc
    _ ≤ ∫⁻ seed, ENNReal.ofReal (Real.exp ε) * κ right seed (Prod.mk seed ⁻¹' s) +
        ENNReal.ofReal δ ∂μ := by
      apply lintegral_mono
      intro seed
      exact hDP seed left right hadj _ (measurable_prodMk_left hs)
    _ = _ := by
      rw [lintegral_add_right _ measurable_const,
        lintegral_const_mul _ (Kernel.measurable_kernel_prodMk_left hs), lintegral_const]
      simp

end Mf.DP

/-! A public seed is drawn once, then held fixed throughout an adaptive transcript. -/
namespace Mf.DP.PoissonAdaptiveQuerySeed
open MeasureTheory ProbabilityTheory
open Mf.Optimization
open scoped BigOperators
noncomputable section

abbrev SumRelease (d : ℕ) := Fin d → ℝ
abbrev SumHistory (d : ℕ) := Mf.DP.AdaptiveRenyiHistory (SumRelease d)
abbrev AugmentedRelease (n d : ℕ) := (Fin n → Bool) × SumRelease d

namespace Data
variable {n d : ℕ} {Seed : Type*} [MeasurableSpace Seed]

def seededData (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (seed : Seed) : Mf.DP.PoissonAdaptiveQuery.Data n d :=
  data.withQueries (fun t h i => query seed t h i) (fun t i =>
    (hquery t i).comp (measurable_prodMk_left (x := seed)))

private theorem query_sum_measurable (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) (mask : Fin n → Bool) :
    Measurable fun p : Seed × SumHistory d t =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping (query p.1 t p.2) A mask := by
  unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
  apply Finset.measurable_fun_sum
  intro i _
  exact (Mf.DP.measurable_l2VectorClip data.clipping).comp (hquery t i)

private theorem pdf_measurable {X : Type*} [MeasurableSpace X] (sigma : ℝ)
    {mean y : X → SumRelease d} (hm : Measurable mean) (hy : Measurable y) :
    Measurable fun x => Mf.DP.bsrGaussianPdfReal sigma (mean x) (y x) := by
  unfold Mf.DP.bsrGaussianPdfReal
  apply Finset.measurable_fun_prod
  intro i _
  exact ProbabilityTheory.measurable_uncurry_gaussianPDFReal.comp
    (((measurable_pi_apply i).comp hm).prodMk
      (measurable_const.prodMk ((measurable_pi_apply i).comp hy)))

def jointCanonicalStep (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) (p : Seed × SumHistory d t) :
    Mf.DP.CommonBaseProbabilityDensity data.reference :=
  (seededData data query hquery p.1).canonicalStep A t p.2

theorem jointCanonicalStep_measurable (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) :
    Measurable fun z : (Seed × SumHistory d t) × AugmentedRelease n d =>
      (jointCanonicalStep data query hquery A t z.1).density z.2 := by
  have hm : Measurable fun p : (Seed × SumHistory d t) × (Fin n → Bool) =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (query p.1.1 t p.1.2) A p.2 := by
    apply measurable_from_prod_countable_left
    intro mask
    exact query_sum_measurable data query hquery A t mask
  have hmean : Measurable fun z : (Seed × SumHistory d t) × AugmentedRelease n d =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (query z.1.1 t z.1.2) A z.2.1 :=
    hm.comp (f := fun z : (Seed × SumHistory d t) × AugmentedRelease n d =>
      (z.1, z.2.1)) (measurable_fst.prodMk (measurable_fst.comp measurable_snd))
  have hp : Measurable fun z : (Seed × SumHistory d t) × AugmentedRelease n d =>
      ENNReal.ofReal (Mf.DP.bsrGaussianPdfReal (data.multiplier * data.clipping)
        (SDE.euclideanPoissonMaskedClippedSum data.clipping
          (query z.1.1 t z.1.2) A z.2.1) z.2.2) :=
    (pdf_measurable (d := d) (data.multiplier * data.clipping)
      hmean (measurable_snd.comp measurable_snd)).ennreal_ofReal
  simpa [jointCanonicalStep, seededData,
    Mf.DP.PoissonAdaptiveQuery.Data.withQueries,
    Mf.DP.PoissonAdaptiveQuery.Data.canonicalStep_density] using hp

def jointStepKernel (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) :
    Kernel (Seed × SumHistory d t) (SumRelease d) :=
  (Mf.DP.commonBaseDensityKernel data.reference (jointCanonicalStep data query hquery A t)
    (jointCanonicalStep_measurable data query hquery A t)).map Prod.snd

theorem jointStepKernel_eq_seedStep (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) (seed : Seed) (h : SumHistory d t) :
    jointStepKernel data query hquery A t (seed, h) =
      (seededData data query hquery seed).stepKernel A t h := by
  simp only [jointStepKernel, Mf.DP.PoissonAdaptiveQuery.Data.stepKernel,
    Kernel.map_apply _ measurable_snd,
    Mf.DP.commonBaseDensityKernel]
  rfl

instance jointStepKernel_isMarkov (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) :
    IsMarkovKernel (jointStepKernel data query hquery A t) := by
  unfold jointStepKernel
  exact Kernel.IsMarkovKernel.map _ measurable_snd

def transcriptKernel (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) : (t : ℕ) → Kernel Seed (SumHistory d t)
  | 0 => Kernel.const Seed (Measure.dirac PUnit.unit)
  | t + 1 => by
      change Kernel Seed (SumHistory d t × SumRelease d)
      exact transcriptKernel data query hquery A t ⊗ₖ jointStepKernel data query hquery A t

instance transcriptKernel_isMarkov (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) : ∀ t, IsMarkovKernel (transcriptKernel data query hquery A t) := by
  intro t
  induction t with
  | zero =>
    change IsMarkovKernel (Kernel.const Seed (Measure.dirac (PUnit.unit : SumHistory d 0)))
    infer_instance
  | succ t ih =>
    change IsMarkovKernel
      (transcriptKernel data query hquery A t ⊗ₖ jointStepKernel data query hquery A t)
    infer_instance

theorem transcriptKernel_apply (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (query : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hquery : ∀ t i, Measurable (fun p : Seed × SumHistory d t => query p.1 t p.2 i))
    (A : Finset (Fin n)) (t : ℕ) (seed : Seed) :
    transcriptKernel data query hquery A t seed =
      (seededData data query hquery seed).transcriptLaw A t := by
  induction t with
  | zero => rfl
  | succ t ih =>
      change (transcriptKernel data query hquery A t ⊗ₖ
        jointStepKernel data query hquery A t) seed =
        (seededData data query hquery seed).transcriptLaw A t ⊗ₘ
          (seededData data query hquery seed).stepKernel A t
      rw [Kernel.compProd_apply_eq_compProd_sectR, ih]
      apply Measure.compProd_congr
      exact Filter.Eventually.of_forall fun h =>
        jointStepKernel_eq_seedStep data query hquery A t seed h

variable {Record : Type}

def optionalQuery
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (D : Fin n → Option Record) : Seed → (t : ℕ) → SumHistory d t → Fin n → SumRelease d :=
  fun seed t h i => (D i).elim 0 (fun r => g seed r t h)

lemma optionalQuery_measurable
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (D : Fin n → Option Record) (t : ℕ) (i : Fin n) :
    Measurable (fun p : Seed × SumHistory d t => optionalQuery g D p.1 t p.2 i) := by
  cases hi : D i with
  | none => simp only [optionalQuery, hi, Option.elim_none]; exact measurable_const
  | some r => simpa only [optionalQuery, hi, Option.elim_some] using hg r t

def optionalTranscriptKernel (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (T : ℕ) (D : Fin n → Option Record) : Kernel Seed (SumHistory d T) :=
  transcriptKernel data (optionalQuery g D) (optionalQuery_measurable g hg D) Finset.univ T

instance (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (T : ℕ) (D : Fin n → Option Record) :
    IsMarkovKernel (optionalTranscriptKernel data g hg T D) := by
  unfold optionalTranscriptKernel
  infer_instance

lemma optionalTranscriptKernel_apply (data : Mf.DP.PoissonAdaptiveQuery.Data n d)
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (T : ℕ) (D : Fin n → Option Record) (seed : Seed) :
    optionalTranscriptKernel data g hg T D seed =
      data.optionalTranscriptLaw (g seed)
        (fun r t => (hg r t).comp measurable_prodMk_left) T D := by
  rw [optionalTranscriptKernel, transcriptKernel_apply]
  rfl

/-- The complete transcript, including a data-independent initial seed, satisfies
approximate DP with explicit constants one and four. Joint measurability of
seed-dependent record queries produces the conditional transcript kernel. -/
theorem publicSeedTranscript_approxDP_of_explicit_constants
    {Seed Record : Type} [MeasurableSpace Seed] {T : ℕ}
    (data : Mf.DP.PoissonAdaptiveQuery.Data n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (μ : Measure Seed) [IsProbabilityMeasure μ]
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2)) :
    ApproxDP OptionalRecordAdjacent
      (fun D => μ ⊗ₘ optionalTranscriptKernel data g hg T D) ε δ := by
  apply Mf.DP.approxDP_publicSeed
  intro seed
  simpa only [optionalTranscriptKernel_apply] using
    data.optionalTranscript_approxDP_of_explicit_constants
      hε hεlog hεT hδ hmult (g seed) (fun r t => (hg r t).comp measurable_prodMk_left)

/-- Common randomized postprocessing of the seed and transcript retains the guarantee. -/
theorem publicSeedPostprocess_approxDP_of_explicit_constants
    {Seed Record Output : Type} [MeasurableSpace Seed] [MeasurableSpace Output] {T : ℕ}
    (data : Mf.DP.PoissonAdaptiveQuery.Data n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (μ : Measure Seed) [IsProbabilityMeasure μ]
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (kernel : Seed × SumHistory d T → Measure Output)
    (hkernel : ∀ event, MeasurableSet event → Measurable (fun h => kernel h event))
    (hprob : ∀ h, kernel h Set.univ = 1) :
    ApproxDP OptionalRecordAdjacent
      (fun D => (μ ⊗ₘ optionalTranscriptKernel data g hg T D).bind kernel) ε δ := by
  exact Training.ApproxDP.bind_right
    (publicSeedTranscript_approxDP_of_explicit_constants data
      hε hεlog hεT hδ hmult μ g hg) kernel hkernel hprob

end Data
end
end Mf.DP.PoissonAdaptiveQuerySeed


end
