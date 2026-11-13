import Mf.DP.PoissonAdaptiveQuery
import Mf.DP.OptionalSlotAdjacency
import Mf.DP.PoissonSampledGaussianRenyiLogScale
import Mf.DP.Training.Common.Postprocessing

/-!
# Explicit privacy constants for full-history Poisson queries

Theorem 1 of `latex/natural-language/poisson_gaussian_lambert_w_constants.tex`
proves the Abadi et al. (CCS 2016) noise scaling with constants one and four on
`0 < ε ≤ min(log(1/δ), q² T)`. This owner connects that arithmetic to the actual
adaptive transcript on optional-record slots. Queries may depend measurably
on the complete public history. The sampler and Gaussian row law are defined
in `PoissonAdaptiveQuery`; the differing participation bit remains hidden.

An absent slot contributes zero. A deletion is reduced to removing that slot
from the sampled sum, with all public parameters held fixed. The final theorem
also covers every common measurable function of the transcript.
-/

namespace Mf.DP.PoissonAdaptiveQuery
open MeasureTheory ProbabilityTheory
open Mf.Optimization
noncomputable section

namespace Data
variable {n d : ℕ}

def withQueries (data : Data n d)
    (g : (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hg : ∀ t i, Measurable (fun h : SumHistory d t => g t h i)) : Data n d :=
  { data with query := g, query_measurable := hg }

/-- Query equivalence is checked for every history and every hidden mask. -/
theorem transcriptLaw_withQueries_eq (data : Data n d)
    (g₁ g₂ : (t : ℕ) → SumHistory d t → Fin n → SumRelease d)
    (hg₁ : ∀ t i, Measurable (fun h : SumHistory d t => g₁ t h i))
    (hg₂ : ∀ t i, Measurable (fun h : SumHistory d t => g₂ t h i))
    (A B : Finset (Fin n))
    (hsum : ∀ t (x : SumHistory d t) mask, SDE.euclideanPoissonMaskedClippedSum data.clipping
        (g₁ t x) A mask =
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (g₂ t x) B mask) :
    ∀ t, (data.withQueries g₁ hg₁).transcriptLaw A t =
      (data.withQueries g₂ hg₂).transcriptLaw B t := by
  have hrow (t : ℕ) (h : SumHistory d t) :
      (data.withQueries g₁ hg₁).canonicalStep A t h =
      (data.withQueries g₂ hg₂).canonicalStep B t h := by
    apply Mf.DP.CommonBaseProbabilityDensity.ext
    funext z
    simp only [canonicalStep_density]
    change ENNReal.ofReal (Mf.DP.bsrGaussianPdfReal _
      (SDE.euclideanPoissonMaskedClippedSum data.clipping
        (g₁ t h) A z.1) z.2) = _
    rw [hsum]
    rfl
  have hk (t : ℕ) : (data.withQueries g₁ hg₁).stepKernel A t =
      (data.withQueries g₂ hg₂).stepKernel B t := by
    ext h : 1
    rw [stepKernel, stepKernel, Kernel.map_apply _ measurable_snd,
      Kernel.map_apply _ measurable_snd]
    change ((data.withQueries g₁ hg₁).canonicalStep A t h).measure.map Prod.snd =
      ((data.withQueries g₂ hg₂).canonicalStep B t h).measure.map Prod.snd
    rw [hrow]
    rfl
  intro t
  induction t with
  | zero => rfl
  | succ t ih => change _ ⊗ₘ _ = _ ⊗ₘ _; rw [ih, hk]

def withSlots {Record : Type} (data : Data n d)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) (D : Fin n → Option Record) : Data n d :=
  data.withQueries (fun t h i => (D i).elim 0 (fun r => g r t h)) (fun t i => by
    cases h : D i with
    | none => simp only [Option.elim_none]; exact measurable_const
    | some r => simpa only [h, Option.elim_some] using hg r t)

def optionalTranscriptLaw {Record : Type} (data : Data n d)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) (t : ℕ) (D : Fin n → Option Record) :=
  (data.withSlots g hg D).transcriptLaw Finset.univ t

private theorem deletion_law {Record : Type} (data : Data n d)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) (D D' : Fin n → Option Record)
    (i : Fin n) (hi' : D' i = none) (hrest : ∀ j, j ≠ i → D j = D' j) (t : ℕ) :
    (data.withSlots g hg D).transcriptLaw (Finset.univ.erase i) t =
      data.optionalTranscriptLaw g hg t D' := by
  classical
  apply data.transcriptLaw_withQueries_eq
  intro t x mask
  unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
  rw [Finset.sum_filter, Finset.sum_filter]
  calc
    _ = ∑ j ∈ Finset.univ.erase i, if mask j then
        Mf.DP.l2VectorClip data.clipping ((D' j).elim 0 (fun r => g r t x)) else 0 := by
      apply Finset.sum_congr rfl
      intro j hj
      have hji : j ≠ i := (Finset.mem_erase.mp hj).1
      simp only [hrest j hji]
    _ = _ := Finset.sum_subset (Finset.erase_subset i Finset.univ) (by
      intro j _ hj
      have hji : j = i := by simpa using hj
      subst j
      simp only [hi', Option.elim_none]
      change (if mask i then Mf.DP.l2VectorClip data.clipping (0 : Fin d → ℝ) else 0) = 0
      have hz : Mf.DP.l2VectorClip data.clipping (0 : Fin d → ℝ) = 0 := by
        simp [Mf.DP.l2VectorClip, data.clipping_pos.le]
      simp only [hz, ite_self])

/-- Padded optional-record domain, with a fixed public slot count. -/
theorem optionalTranscript_approxDP {Record : Type} (data : Data n d)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) (order : ℕ) (horder : 2 ≤ order)
    (T : ℕ) (epsilon : ℝ) :
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T)
      epsilon (Real.exp (((order : ℝ) - 1) *
        (Mf.DP.adaptiveRenyiBudget
          (fun _ => SDE.euclideanSampledGaussianSharpStepRho
            order data.q data.multiplier) T - epsilon))) := by
  classical
  intro D D' hadj s hs
  rcases hadj with ⟨i, r, hi, hi', hrest⟩ | ⟨i, r, hi, hi', hrest⟩
  · have h := (data.withSlots g hg D).transcript_approxDP order horder T epsilon
      Finset.univ (Finset.univ.erase i)
      (Or.inr ⟨i, Finset.notMem_erase _ _, by simp⟩) s hs
    dsimp only at h
    rw [data.deletion_law g hg D D' i hi' hrest T] at h
    exact h
  · have h := (data.withSlots g hg D').transcript_approxDP order horder T epsilon
      (Finset.univ.erase i) Finset.univ
      (Or.inl ⟨i, Finset.notMem_erase _ _, by simp⟩) s hs
    dsimp only at h
    rw [data.deletion_law g hg D' D i hi' hrest T] at h
    exact h

open Mf.DP.PoissonRenyiCalibration

private theorem constant_budget (rho : ℝ) (T : ℕ) :
    adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ) * rho := by
  induction T with
  | zero => simp
  | succ T ih => simp [adaptiveRenyiBudget_succ, ih, Nat.cast_add, add_mul]

/-- Constants one and four for every measurable full-history record query. -/
theorem optionalTranscript_approxDP_of_explicit_constants
    {T : ℕ} {Record : Type} (data : Data n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  let m := publicOrder (Real.log (1 / δ)) ε
  have hm : 2 ≤ m := (publicOrder_bounds_of_le_logScale hε hεlog).1
  have hv := calibratedVariance_le_sq_of_multiplier_ge data.q.coe_nonneg hε
    (hε.le.trans hεlog) hmult
  have hdelta := tailBudget_le_of_le_logScale (T := T)
    (by exact_mod_cast data.q_pos.le) data.q_le_one hε hεlog hεT hδ hv
  apply approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T ε)
  simp only [constant_budget, SDE.euclideanSampledGaussianSharpStepRho, m]
  convert hdelta using 1
  rfl

/-- Every common measurable function of the released history preserves the guarantee. -/
theorem postprocess_approxDP_of_explicit_constants
    {T : ℕ} {Record Output : Type} [MeasurableSpace Output]
    (data : Data n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t))
    (f : SumHistory d T → Output) (hf : Measurable f) :
    ApproxDP OptionalRecordAdjacent
      (fun D => (data.optionalTranscriptLaw g hg T D).map f) ε δ := by
  intro D D' hadj s hs
  rw [Measure.map_apply hf hs, Measure.map_apply hf hs]
  exact data.optionalTranscript_approxDP_of_explicit_constants
    hε hεlog hεT hδ hmult g hg D D' hadj (f ⁻¹' s) (hf hs)

/-- Common randomized postprocessing also preserves the full-history guarantee. -/
theorem randomizedPostprocess_approxDP_of_explicit_constants
    {T : ℕ} {Record Output : Type} [MeasurableSpace Output]
    (data : Data n d) {ε δ : ℝ}
    (hε : 0 < ε) (hεlog : ε ≤ Real.log (1 / δ))
    (hεT : ε ≤ (data.q : ℝ) ^ 2 * T) (hδ : 0 < δ)
    (hmult : 4 * (data.q : ℝ) * Real.sqrt ((T : ℝ) * Real.log (1 / δ)) / ε ≤
      data.multiplier)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t))
    (kernel : SumHistory d T → Measure Output)
    (hkernel : ∀ event, MeasurableSet event → Measurable (fun h => kernel h event))
    (hprob : ∀ h, kernel h Set.univ = 1) :
    ApproxDP OptionalRecordAdjacent
      (fun D => (data.optionalTranscriptLaw g hg T D).bind kernel) ε δ :=
  Training.ApproxDP.bind_right
    (data.optionalTranscript_approxDP_of_explicit_constants
      hε hεlog hεT hδ hmult g hg) kernel hkernel hprob

end Data
end
end Mf.DP.PoissonAdaptiveQuery
