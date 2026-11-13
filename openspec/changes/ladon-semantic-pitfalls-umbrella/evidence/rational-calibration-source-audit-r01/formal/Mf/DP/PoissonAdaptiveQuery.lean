import Mf.Optimization.SDE.DPAdamSampledGaussianSharpRDP
import Mf.Optimization.SDE.DPAdamEuclideanAveragedReleaseMechanism
import Mf.DP.AdaptiveTranscriptProjection
import Mf.DP.GaussianApproxDP

/-!
# Poisson sampled Gaussian queries depending on the full public history

Abadi et al., *Deep Learning with Differential Privacy* (CCS 2016), Theorem 1,
composes sampled Gaussian mechanisms adaptively. Here each record query may
be any measurable function of time and the entire preceding noisy-sum transcript.
Every step samples fresh independent Bernoulli masks, clips each query at the
public radius, adds isotropic Gaussian noise, and releases only the noisy sum.

The two directions of add/remove privacy use the exact finite-binomial bounds
from `DPAdamSampledGaussianSharpRDP`. Pair-local common masks are auxiliary:
the differing record's participation stays hidden, and both auxiliary laws
are projected to the actual transcript before the event-level conclusion.
The construction extends the state-query argument in
`PoissonClippedSGD.PrivacyTranscript` to arbitrary measurable history queries.
-/

namespace Mf.DP.PoissonAdaptiveQuery
open MeasureTheory ProbabilityTheory
open Mf.Optimization
open scoped BigOperators
noncomputable section

abbrev SumRelease (d : ℕ) := Fin d → ℝ
abbrev SumHistory (d : ℕ) := Mf.DP.AdaptiveRenyiHistory (SumRelease d)
abbrev AugmentedRelease (n d : ℕ) := (Fin n → Bool) × SumRelease d
abbrev AugmentedHistory (n d : ℕ) := Mf.DP.AdaptiveRenyiHistory (AugmentedRelease n d)

/-- Public parameters and measurable record queries; no privacy conclusion is a field. -/
structure Data (n d : ℕ) where
  q : NNReal
  q_pos : 0 < q
  q_le_one : q ≤ 1
  clipping : ℝ
  clipping_pos : 0 < clipping
  multiplier : ℝ
  multiplier_pos : 0 < multiplier
  query : (t : ℕ) → SumHistory d t → Fin n → SumRelease d
  query_measurable : ∀ t i, Measurable (fun h : SumHistory d t => query t h i)

namespace Data
variable {n d : ℕ}

def projectHistory : (t : ℕ) → AugmentedHistory n d t → SumHistory d t
  | 0, _ => PUnit.unit
  | t + 1, h => (projectHistory t h.1, h.2.2)

theorem projectHistory_measurable : ∀ t, Measurable (projectHistory (n := n) (d := d) t) := by
  intro t
  induction t with
  | zero => exact measurable_const
  | succ t ih => exact (ih.comp measurable_fst).prodMk (measurable_snd.comp measurable_snd)

def reference (data : Data n d) : Measure (AugmentedRelease n d) :=
  (SDE.poissonMaskLaw (Record := Fin n) data.q data.q_le_one).prod
    (volume : Measure (SumRelease d))

instance (data : Data n d) : SFinite data.reference := by
  unfold reference
  infer_instance

private theorem sum_measurable (data : Data n d) (A : Finset (Fin n))
    (t : ℕ) (mask : Fin n → Bool) :
    Measurable fun x : SumHistory d t => SDE.euclideanPoissonMaskedClippedSum
      data.clipping (data.query t x) A mask := by
  unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
  apply Finset.measurable_fun_sum
  intro i _
  exact (Mf.DP.measurable_l2VectorClip data.clipping).comp (data.query_measurable t i)

private theorem pdf_measurable {X : Type*} [MeasurableSpace X] (sigma : ℝ)
    {mean y : X → SumRelease d} (hm : Measurable mean) (hy : Measurable y) :
    Measurable fun x => Mf.DP.bsrGaussianPdfReal sigma (mean x) (y x) := by
  unfold Mf.DP.bsrGaussianPdfReal
  apply Finset.measurable_fun_prod
  intro i _
  exact ProbabilityTheory.measurable_uncurry_gaussianPDFReal.comp
    (((measurable_pi_apply i).comp hm).prodMk
      (measurable_const.prodMk ((measurable_pi_apply i).comp hy)))

def canonicalStep (data : Data n d) (A : Finset (Fin n)) (t : ℕ)
    (h : SumHistory d t) : Mf.DP.CommonBaseProbabilityDensity data.reference :=
  SDE.euclideanCommonMaskAugmentedBaseDensity data.clipping data.multiplier
    (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne')
    (data.query t h) A data.q data.q_le_one

@[simp] theorem canonicalStep_density (data : Data n d) (A : Finset (Fin n))
    (t : ℕ) (h : SumHistory d t) (z : AugmentedRelease n d) :
    (data.canonicalStep A t h).density z =
      ENNReal.ofReal (Mf.DP.bsrGaussianPdfReal (data.multiplier * data.clipping)
        (SDE.euclideanPoissonMaskedClippedSum data.clipping
          (data.query t h) A z.1) z.2) := by
  change 1 * _ = _
  exact one_mul _

theorem canonicalStep_measurable (data : Data n d) (A : Finset (Fin n)) (t : ℕ) :
    Measurable fun z : SumHistory d t × AugmentedRelease n d =>
      (data.canonicalStep A t z.1).density z.2 := by
  have hm : Measurable fun p : SumHistory d t × (Fin n → Bool) =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping (data.query t p.1) A p.2 := by
    apply measurable_from_prod_countable_left
    intro mask
    exact data.sum_measurable A t mask
  have hm' : Measurable fun z : SumHistory d t × AugmentedRelease n d =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (data.query t z.1) A z.2.1 :=
    hm.comp (f := fun z : SumHistory d t × AugmentedRelease n d =>
      (z.1, z.2.1)) (measurable_fst.prodMk
      (measurable_fst.comp measurable_snd))
  have hp : Measurable fun z : SumHistory d t × AugmentedRelease n d =>
      ENNReal.ofReal (Mf.DP.bsrGaussianPdfReal (data.multiplier * data.clipping)
        (SDE.euclideanPoissonMaskedClippedSum data.clipping
          (data.query t z.1) A z.2.1) z.2.2) :=
    (pdf_measurable (d := d) (data.multiplier * data.clipping)
      hm' (measurable_snd.comp measurable_snd)).ennreal_ofReal
  simpa only [canonicalStep_density] using hp

/-- Canonical public next-sum kernel: the internal mask is dropped. -/
def stepKernel (data : Data n d) (A : Finset (Fin n)) (t : ℕ) :
    Kernel (SumHistory d t) (SumRelease d) :=
  (Mf.DP.commonBaseDensityKernel data.reference (data.canonicalStep A t)
    (data.canonicalStep_measurable A t)).map Prod.snd

instance (data : Data n d) (A : Finset (Fin n)) (t : ℕ) :
    IsMarkovKernel (data.stepKernel A t) := by
  unfold stepKernel
  exact Kernel.IsMarkovKernel.map _ measurable_snd

/-- Dataset-indexed law of the finite noisy-sum transcript. -/
def transcriptLaw (data : Data n d) (A : Finset (Fin n)) :
    (t : ℕ) → Measure (SumHistory d t)
  | 0 => Measure.dirac PUnit.unit
  | t + 1 => (data.transcriptLaw A t) ⊗ₘ (data.stepKernel A t)

instance (data : Data n d) (A : Finset (Fin n)) :
    ∀ t, IsProbabilityMeasure (data.transcriptLaw A t) := by
  intro t
  induction t with
  | zero =>
      refine ⟨?_⟩
      change (Measure.dirac (PUnit.unit : SumHistory d 0)) Set.univ = 1
      exact Measure.dirac_apply_of_mem (Set.mem_univ _)
  | succ t ih =>
      change IsProbabilityMeasure (data.transcriptLaw A t ⊗ₘ data.stepKernel A t)
      infer_instance

theorem stepKernel_eq_exact (data : Data n d) (A : Finset (Fin n))
    (t : ℕ) (h : SumHistory d t) :
    data.stepKernel A t h = SDE.euclideanExactSampledGaussianSumRelease
      data.clipping data.multiplier (data.query t h) A
      (data.q : ℝ) data.q.2 data.q_le_one := by
  rw [stepKernel, Kernel.map_apply _ measurable_snd]
  change (data.canonicalStep A t h).measure.snd = _
  exact SDE.euclideanCommonMaskAugmentedBaseDensity_snd_eq_exact _ _ _ _ _ _ _

/-- Differing participation stays hidden; only the common-mask auxiliary row is exposed. -/
def hiddenStep (data : Data n d) (A : Finset (Fin n)) (record : Fin n)
    (t : ℕ) (h : AugmentedHistory n d t) :=
  SDE.euclideanCommonMaskAugmentedHiddenDensity data.clipping data.multiplier
    (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne')
    (data.query t (projectHistory t h)) A record data.q data.q_le_one

theorem hiddenStep_measurable (data : Data n d) (A : Finset (Fin n))
    (record : Fin n) (t : ℕ) :
    Measurable fun z : AugmentedHistory n d t × AugmentedRelease n d =>
      (data.hiddenStep A record t z.1).density z.2 := by
  have hhistory : Measurable fun z : AugmentedHistory n d t × AugmentedRelease n d =>
      projectHistory t z.1 :=
    (projectHistory_measurable t).comp measurable_fst
  have hm : Measurable fun p : SumHistory d t × (Fin n → Bool) =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping (data.query t p.1) A p.2 := by
    apply measurable_from_prod_countable_left
    intro mask
    exact data.sum_measurable A t mask
  have hmean : Measurable fun z : AugmentedHistory n d t × AugmentedRelease n d =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (data.query t (projectHistory t z.1)) A z.2.1 :=
    hm.comp (f := fun z : AugmentedHistory n d t × AugmentedRelease n d =>
      (projectHistory t z.1, z.2.1))
      (hhistory.prodMk (measurable_fst.comp measurable_snd))
  have hclip := (Mf.DP.measurable_l2VectorClip data.clipping).comp
    ((data.query_measurable t record).comp hhistory)
  change Measurable fun z : AugmentedHistory n d t × AugmentedRelease n d =>
    1 * (ENNReal.ofReal (data.q : ℝ) * ENNReal.ofReal
      (Mf.DP.bsrGaussianPdfReal (data.multiplier * data.clipping)
        (SDE.euclideanPoissonMaskedClippedSum data.clipping
          (data.query t (projectHistory t z.1)) A z.2.1 +
          Mf.DP.l2VectorClip data.clipping
            (data.query t (projectHistory t z.1) record)) z.2.2) +
      ENNReal.ofReal (1 - (data.q : ℝ)) * ENNReal.ofReal
        (Mf.DP.bsrGaussianPdfReal (data.multiplier * data.clipping)
          (SDE.euclideanPoissonMaskedClippedSum data.clipping
            (data.query t (projectHistory t z.1)) A z.2.1) z.2.2))
  simp only [one_mul]
  exact (measurable_const.mul
    (pdf_measurable _ (hmean.add hclip) (measurable_snd.comp measurable_snd)).ennreal_ofReal).add
      (measurable_const.mul
        (pdf_measurable _ hmean (measurable_snd.comp measurable_snd)).ennreal_ofReal)

def baseHiddenFamily (data : Data n d) (A : Finset (Fin n)) (record : Fin n) :
    Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily (AugmentedRelease n d)
      (fun _ => data.reference) where
  leftStep := fun t h => data.canonicalStep A t (projectHistory t h)
  rightStep := data.hiddenStep A record
  measurable_leftStep := fun t =>
    (data.canonicalStep_measurable A t).comp
      (f := fun z : AugmentedHistory n d t × AugmentedRelease n d =>
        (projectHistory t z.1, z.2))
        (((projectHistory_measurable t).comp measurable_fst).prodMk measurable_snd)
  measurable_rightStep := data.hiddenStep_measurable A record

def hiddenBaseFamily (data : Data n d) (A : Finset (Fin n)) (record : Fin n) :
    Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily (AugmentedRelease n d)
      (fun _ => data.reference) where
  leftStep := data.hiddenStep A record
  rightStep := fun t h => data.canonicalStep A t (projectHistory t h)
  measurable_leftStep := data.hiddenStep_measurable A record
  measurable_rightStep := fun t =>
    (data.canonicalStep_measurable A t).comp
      (f := fun z : AugmentedHistory n d t × AugmentedRelease n d =>
        (projectHistory t z.1, z.2))
        (((projectHistory_measurable t).comp measurable_fst).prodMk measurable_snd)

/-- Conditional clipped-query sensitivity at every public noisy-sum history. -/
theorem masked_query_sensitivity (data : Data n d)
    {A B : Finset (Fin n)} (hadj : Mf.DP.FinsetAddRemoveAdjacent A B)
    (t : ℕ) (h : SumHistory d t) (mask : Fin n → Bool) :
    Mf.DP.l2Norm
      (SDE.euclideanPoissonMaskedClippedSum data.clipping
        (data.query t h) A mask -
       SDE.euclideanPoissonMaskedClippedSum data.clipping
        (data.query t h) B mask) ≤ data.clipping :=
  SDE.euclideanPoissonMaskedClippedSum_addRemove_sensitivity
    data.clipping data.clipping_pos.le _ hadj mask

/-- Sharp adaptive smaller-to-larger RDP, before dropping proof-only common masks. -/
theorem baseHidden_rdp (data : Data n d) (A : Finset (Fin n)) (record : Fin n)
    (order : ℕ) (horder : 2 ≤ order) (T : ℕ) :
    Mf.DP.RenyiDivergenceUpperAt (order : ℝ)
      (Mf.DP.adaptiveRenyiBudget (fun _ => SDE.euclideanSampledGaussianSharpStepRho
        order data.q data.multiplier) T)
      (Mf.DP.adaptiveRenyiHeterogeneousBaseMeasure (fun _ => data.reference) T)
      ((data.baseHiddenFamily A record).leftTranscriptDensity T)
      ((data.baseHiddenFamily A record).rightTranscriptDensity T) := by
  apply Mf.DP.renyiDivergenceUpperAt_adaptiveFinite_heterogeneous
    (order : ℝ) (fun _ => data.reference) (data.baseHiddenFamily A record)
    (fun _ => SDE.euclideanSampledGaussianSharpStepRho order data.q data.multiplier)
    (by exact_mod_cast horder)
  intro t h
  exact SDE.euclideanCommonMaskAugmented_forward_rdp_sharp order _ _ horder
    data.clipping_pos data.multiplier_pos _ A record data.q data.q_le_one

/-- Sharp adaptive larger-to-smaller RDP at the identical public cost. -/
theorem hiddenBase_rdp (data : Data n d) (A : Finset (Fin n)) (record : Fin n)
    (order : ℕ) (horder : 2 ≤ order) (T : ℕ) :
    Mf.DP.RenyiDivergenceUpperAt (order : ℝ)
      (Mf.DP.adaptiveRenyiBudget (fun _ => SDE.euclideanSampledGaussianSharpStepRho
        order data.q data.multiplier) T)
      (Mf.DP.adaptiveRenyiHeterogeneousBaseMeasure (fun _ => data.reference) T)
      ((data.hiddenBaseFamily A record).leftTranscriptDensity T)
      ((data.hiddenBaseFamily A record).rightTranscriptDensity T) := by
  apply Mf.DP.renyiDivergenceUpperAt_adaptiveFinite_heterogeneous
    (order : ℝ) (fun _ => data.reference) (data.hiddenBaseFamily A record)
    (fun _ => SDE.euclideanSampledGaussianSharpStepRho order data.q data.multiplier)
    (by exact_mod_cast horder)
  intro t h
  exact SDE.euclideanCommonMaskAugmented_reverse_rdp_sharp order _ _ horder
    data.clipping_pos data.multiplier_pos _ A record data.q data.q_le_one

/-- The same conditional rows have the same transcript density, regardless of side. -/
private theorem left_eq_right (data : Data n d)
    (family₁ family₂ : Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily
      (AugmentedRelease n d) (fun _ => data.reference))
    (hstep : ∀ t h, family₁.leftStep t h = family₂.rightStep t h) :
    ∀ t, family₁.leftTranscriptDensity t = family₂.rightTranscriptDensity t := by
  intro t
  induction t with
  | zero => rfl
  | succ t ih =>
      apply Mf.DP.CommonBaseProbabilityDensity.ext
      funext z
      change (family₁.leftTranscriptDensity t).density z.1 *
          (family₁.leftStep t z.1).density z.2 =
        (family₂.rightTranscriptDensity t).density z.1 *
          (family₂.rightStep t z.1).density z.2
      rw [ih, hstep t z.1]

set_option backward.isDefEq.respectTransparency false in
set_option backward.isDefEq.respectTransparency.types false in
/-- The row law identity is consumed at every adaptive history. The local
elaboration options identify the custom measurable spaces at empty history. -/
private theorem rightTranscript_project (data : Data n d)
    (family : Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily
      (AugmentedRelease n d) (fun _ => data.reference))
    (A : Finset (Fin n))
    (hrow : ∀ t h, ((family.rightStep t h).measure).map Prod.snd =
      data.stepKernel A t (projectHistory t h)) :
    ∀ t, ((family.rightTranscriptDensity t).measure).map (projectHistory t) =
      data.transcriptLaw A t := by
  intro t
  induction t with
  | zero =>
      simp only [Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily.rightTranscriptDensity,
        Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily.emptyDensity,
        Mf.DP.CommonBaseProbabilityDensity.measure]
      change Measure.map (projectHistory 0)
        ((Measure.dirac (PUnit.unit : AugmentedHistory n d 0)).withDensity 1) = _
      rw [MeasureTheory.withDensity_one, Measure.map_dirac' (projectHistory_measurable 0)]
      rfl
  | succ t ih =>
      rw [Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily.rightTranscriptMeasure_succ]
      change Measure.map (Prod.map (projectHistory t) Prod.snd)
        ((family.rightTranscriptDensity t).measure ⊗ₘ
          Mf.DP.commonBaseDensityKernel data.reference (family.rightStep t)
            (family.measurable_rightStep t)) = _
      rw [Mf.DP.compProd_map_prodMap _ _ (data.stepKernel A t)
        (projectHistory t) Prod.snd (projectHistory_measurable t) measurable_snd
        (hrow t), ih]
      rfl

theorem baseTranscript_project (data : Data n d) (A : Finset (Fin n))
    (record : Fin n) (t : ℕ) :
    (((data.hiddenBaseFamily A record).rightTranscriptDensity t).measure).map
      (projectHistory t) = data.transcriptLaw A t := by
  apply data.rightTranscript_project (data.hiddenBaseFamily A record) A
  intro t h
  change (data.canonicalStep A t (projectHistory t h)).measure.snd = _
  rw [data.stepKernel_eq_exact]
  exact SDE.euclideanCommonMaskAugmentedBaseDensity_snd_eq_exact _ _ _ _ _ _ _

theorem hiddenTranscript_project {n d : ℕ} (data : Data (n + 1) d)
    (A : Finset (Fin (n + 1))) (record : Fin (n + 1)) (hr : record ∉ A) (t : ℕ) :
    (((data.baseHiddenFamily A record).rightTranscriptDensity t).measure).map
      (projectHistory t) = data.transcriptLaw (insert record A) t := by
  apply data.rightTranscript_project (data.baseHiddenFamily A record) (insert record A)
  intro t h
  rw [data.stepKernel_eq_exact]
  exact SDE.euclideanCommonMaskAugmentedHiddenDensity_snd_eq_exact
    _ _ _ _ _ _ hr _ _

/-- Finite two-sided privacy for the canonical hidden-mask noisy-sum transcript. -/
theorem transcript_approxDP (data : Data n d) (order : ℕ) (horder : 2 ≤ order)
    (T : ℕ) (epsilon : ℝ) :
    Mf.DP.ApproxDP Mf.DP.FinsetAddRemoveAdjacent (fun A => data.transcriptLaw A T)
      epsilon (Real.exp (((order : ℝ) - 1) *
        (Mf.DP.adaptiveRenyiBudget
          (fun _ => SDE.euclideanSampledGaussianSharpStepRho
            order data.q data.multiplier) T - epsilon))) := by
  intro left right hadj s hs
  rcases hadj with ⟨record, hr, rfl⟩ | ⟨record, hr, rfl⟩
  · cases n with
    | zero => exact Fin.elim0 record
    | succ n =>
      have hpos := Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily.rightTranscriptDensity_ne_zero
        (fun _ => data.reference) (data.baseHiddenFamily left record)
        (fun t h z => SDE.euclideanCommonMaskAugmentedHiddenDensity_ne_zero _ _ _ _ _ _ _ _ z)
      have h := (data.baseHidden_rdp left record order horder T).map_event_le
        (hpos T) epsilon (projectHistory T) (projectHistory_measurable T) s hs
      rw [data.left_eq_right _ (data.hiddenBaseFamily left record)
        (by intro t h; rfl) T, data.baseTranscript_project left record T,
        data.hiddenTranscript_project left record hr T] at h
      exact h
  · cases n with
    | zero => exact Fin.elim0 record
    | succ n =>
      have hpos := Mf.DP.HeterogeneousAdaptiveRenyiDensityFamily.rightTranscriptDensity_ne_zero
        (fun _ => data.reference) (data.hiddenBaseFamily right record)
        (fun t h z => SDE.euclideanCommonMaskAugmentedBaseDensity_ne_zero _ _ _ _ _ _ _ z)
      have h := (data.hiddenBase_rdp right record order horder T).map_event_le
        (hpos T) epsilon (projectHistory T) (projectHistory_measurable T) s hs
      rw [data.left_eq_right _ (data.baseHiddenFamily right record)
        (by intro t h; rfl) T, data.hiddenTranscript_project right record hr T,
        data.baseTranscript_project right record T] at h
      exact h

end Data
end
end Mf.DP.PoissonAdaptiveQuery
