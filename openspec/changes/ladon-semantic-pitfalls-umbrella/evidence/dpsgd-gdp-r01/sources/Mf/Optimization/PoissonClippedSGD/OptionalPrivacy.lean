import Mf.Optimization.PoissonClippedSGD.RecordAdjacency
import Mf.Optimization.PoissonClippedSGD.PrivacyTranscript

/-!
# Padded optional-record privacy

Every optional slot contributes either its record query or zero. A single
record deletion is reduced pairwise to deleting one element from the public
slot set. The reduction allows other slots to be absent and preserves the
fixed public population denominator qN.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory ProbabilityTheory
noncomputable section

namespace PrivacyData
variable {n d : ℕ}

def withQueries (data : PrivacyData n d)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) : PrivacyData n d :=
  { data with gradient := g, gradient_measurable := hg }

@[simp] theorem state_withQueries (data : PrivacyData n d)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) :
    ∀ t h, (data.withQueries g hg).state t h = data.state t h := by
  intro t
  induction t with
  | zero => intro h; rfl
  | succ t ih => intro h; change _ - _ = _ - _; rw [ih]; rfl

/-- Query equivalence is checked for every state and every hidden mask. -/
theorem transcriptLaw_withQueries_eq (data : PrivacyData n d)
    (g₁ g₂ : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg₁ : ∀ i, Measurable (g₁ i)) (hg₂ : ∀ i, Measurable (g₂ i))
    (A B : Finset (Fin n))
    (hsum : ∀ x mask, SDE.euclideanPoissonMaskedClippedSum data.clipping
        (fun i k => g₁ i x k) A mask =
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (fun i k => g₂ i x k) B mask) :
    ∀ t, (data.withQueries g₁ hg₁).transcriptLaw A t =
      (data.withQueries g₂ hg₂).transcriptLaw B t := by
  have hrow (t : ℕ) (h : SumHistory d t) :
      (data.withQueries g₁ hg₁).canonicalStep A t h =
      (data.withQueries g₂ hg₂).canonicalStep B t h := by
    apply Mf.DP.CommonBaseProbabilityDensity.ext
    funext z
    simp only [canonicalStep_density, state_withQueries]
    change ENNReal.ofReal (Mf.DP.bsrGaussianPdfReal _
      (SDE.euclideanPoissonMaskedClippedSum data.clipping
        (fun i k => g₁ i (data.state t h) k) A z.1) z.2) = _
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

def withSlots {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin n → Option Record) : PrivacyData n d :=
  data.withQueries (slotGradient g D) (fun i => by
    cases h : D i with
    | none => simp only [slotGradient, h, Option.elim_none]; exact measurable_const
    | some r => simpa only [slotGradient, h, Option.elim_some] using hg r)

def optionalTranscriptLaw {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (t : ℕ) (D : Fin n → Option Record) :=
  (data.withSlots g hg D).transcriptLaw Finset.univ t

private theorem deletion_law {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (i : Fin n) (hi' : D' i = none) (hrest : ∀ j, j ≠ i → D j = D' j) (t : ℕ) :
    (data.withSlots g hg D).transcriptLaw (Finset.univ.erase i) t =
      data.optionalTranscriptLaw g hg t D' := by
  classical
  apply data.transcriptLaw_withQueries_eq
  intro x mask
  unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
  rw [Finset.sum_filter, Finset.sum_filter]
  calc
    _ = ∑ j ∈ Finset.univ.erase i, if mask j then
        Mf.DP.l2VectorClip data.clipping (fun k => slotGradient g D' j x k) else 0 := by
      apply Finset.sum_congr rfl
      intro j hj
      have hji : j ≠ i := (Finset.mem_erase.mp hj).1
      simp only [slotGradient, hrest j hji]
    _ = _ := Finset.sum_subset (Finset.erase_subset i Finset.univ) (by
      intro j _ hj
      have hji : j = i := by simpa using hj
      subst j
      simp only [slotGradient, hi', Option.elim_none]
      change (if mask i then Mf.DP.l2VectorClip data.clipping (0 : Fin d → ℝ) else 0) = 0
      have hz : Mf.DP.l2VectorClip data.clipping (0 : Fin d → ℝ) = 0 := by
        simp [Mf.DP.l2VectorClip, data.clipping_pos.le]
      simp only [hz, ite_self])

/-- Padded optional-record domain, with the public qN denominator unchanged. -/
theorem optionalTranscript_approxDP {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (order : ℕ) (horder : 2 ≤ order)
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

end PrivacyData
end
end Mf.Optimization.PoissonClippedSGD
