import Mf.Optimization.PoissonClippedSGD.Basic
import Mathlib.Analysis.Calculus.Gradient.Basic
import Mathlib.Tactic

/-!
# Gradient of the finite mean objective

The mean-oracle gradient identity used by the general convergence theorem
follows from the component gradient identities for a finite-sum objective.
This adapter requires differentiability but no smoothness of individual losses.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open scoped BigOperators

variable {n d : ℕ}

def finiteMeanObjective (fi : Fin n → EuclideanSpace ℝ (Fin d) → ℝ)
    (x : EuclideanSpace ℝ (Fin d)) : ℝ :=
  (n : ℝ)⁻¹ • (∑ i, fi i) x

theorem finiteMeanObjective_hasGradientAt
    (fi : Fin n → EuclideanSpace ℝ (Fin d) → ℝ)
    (gi : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hgi : ∀ i x, HasGradientAt (fi i) (gi i x) x)
    (x : EuclideanSpace ℝ (Fin d)) :
    HasGradientAt (finiteMeanObjective fi) (vectorMean (fun i => gi i x)) x := by
  rw [hasGradientAt_iff_hasFDerivAt]
  have hsum0 : HasFDerivAt (∑ i : Fin n, fi i)
      (∑ i : Fin n, InnerProductSpace.toDual ℝ (EuclideanSpace ℝ (Fin d)) (gi i x)) x :=
    HasFDerivAt.sum (u := Finset.univ) (fun i hi =>
      hasGradientAt_iff_hasFDerivAt.mp (hgi i x))
  have hsum : HasFDerivAt (fun y : EuclideanSpace ℝ (Fin d) => ∑ i : Fin n, fi i y)
      (∑ i : Fin n, InnerProductSpace.toDual ℝ (EuclideanSpace ℝ (Fin d)) (gi i x)) x := by
    convert hsum0 using 1
    funext y
    simp only [Finset.sum_apply]
  have hscaled := hsum.const_smul ((n:ℝ)⁻¹)
  have hderiv : InnerProductSpace.toDual ℝ (EuclideanSpace ℝ (Fin d))
        (vectorMean (fun i => gi i x)) =
      (n:ℝ)⁻¹ • ∑ i, InnerProductSpace.toDual ℝ (EuclideanSpace ℝ (Fin d)) (gi i x) := by
    ext v
    simp [InnerProductSpace.toDual_apply_apply, vectorMean]
  rw [hderiv]
  have hobj : finiteMeanObjective fi =
      ((n:ℝ)⁻¹ • fun y : EuclideanSpace ℝ (Fin d) => ∑ i : Fin n, fi i y) := by
    funext y
    simp [finiteMeanObjective, Finset.sum_apply]
  exact hscaled.congr_of_eventuallyEq (Filter.EventuallyEq.of_eq hobj)

end Mf.Optimization.PoissonClippedSGD
end
