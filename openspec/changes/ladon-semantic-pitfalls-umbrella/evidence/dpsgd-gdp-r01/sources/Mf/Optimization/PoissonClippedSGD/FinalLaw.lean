import Mf.Optimization.PoissonClippedSGD.PrivacyLaw
import Mf.Optimization.PoissonClippedSGD.OptionalPrivacy

/-!
# Final iterate as postprocessing of the actual Poisson transcript

The independent Gaussian product-history recursion has the same final-state
law as the measurable state map of the hidden-sampling transcript. This law
identity is independent of the choice of privacy accountant.
-/

noncomputable section
open MeasureTheory
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
variable {n d : ℕ}

/-- Final iterate of the actual Gaussian product-history recursion. -/
def optionalFinalLaw {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (T : ℕ) (D : Fin n → Option Record) : Measure (EuclideanSpace ℝ (Fin d)) :=
  (gaussianHistoryLaw n d T data.q data.q_le_one
    (normalizedSumNoise n d data.q data.clipping data.multiplier)).map
      (gaussianRun data.eta data.q data.clipping (slotGradient g D) data.initial T)

theorem optionalFinalLaw_eq_map {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (hd : 0 < d) (T : ℕ) (D : Fin n → Option Record) :
    data.optionalFinalLaw g T D =
      (data.optionalTranscriptLaw g hg T D).map (data.state T) := by
  have hstate : (data.withSlots g hg D).state T = data.state T := by
    funext h
    exact data.state_withQueries _ _ T h
  have hgrad : restrictedGradient (slotGradient g D) Finset.univ = slotGradient g D := by
    funext i x
    simp only [restrictedGradient, Finset.mem_univ, if_true]
  have h := (data.withSlots g hg D).finalState_law Finset.univ hd T
  rw [hstate] at h
  change (data.optionalTranscriptLaw g hg T D).map (data.state T) =
    (gaussianHistoryLaw n d T data.q data.q_le_one
      (normalizedSumNoise n d data.q data.clipping data.multiplier)).map
      (gaussianRun data.eta data.q data.clipping
        (restrictedGradient (slotGradient g D) Finset.univ) data.initial T) at h
  rw [hgrad] at h
  exact h.symm

end Mf.Optimization.PoissonClippedSGD.PrivacyData
