import Mathlib.MeasureTheory.Integral.Pi
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.MeasureTheory.Measure.FiniteMeasurePi
import Mathlib.Probability.Distributions.Gaussian.Real

/-!
# Finite Product Gaussian Laws

This module owns the finite noncentered product Gaussian law used by generic
finite-dimensional probability constructions. It has no optimizer, privacy,
or convergence semantics.
-/

namespace Mf
namespace Probability
namespace FiniteProductGaussian

open MeasureTheory

noncomputable section

variable {ι : Type*} [Fintype ι]

/-- Nonnegative coordinate variance induced by a real scale. -/
def variance (scale : ι → ℝ) : ι → NNReal :=
  fun i => ⟨scale i ^ 2, sq_nonneg (scale i)⟩

/-- Finite noncentered product Gaussian law with coordinate-dependent means and
scales. -/
def law (mu scale : ι → ℝ) : Measure (ι → ℝ) :=
  Measure.pi fun i : ι =>
    ProbabilityTheory.gaussianReal (mu i) (variance scale i)

/-- Coordinatewise negation on a finite Gaussian product space. -/
def neg (y : ι → ℝ) : ι → ℝ :=
  fun i => -y i

/-- Coordinatewise negation is measurable. -/
theorem neg_measurable : Measurable (neg (ι := ι)) := by
  classical
  exact measurable_pi_lambda _ fun i => (measurable_pi_apply i).neg

/-- A finite product Gaussian is closed under coordinatewise negation. -/
theorem law_map_neg (mu scale : ι → ℝ) :
    (law mu scale).map (neg (ι := ι)) =
      law (fun i => -mu i) scale := by
  unfold law neg
  rw [Measure.pi_map_pi
      (μ := fun i : ι =>
        ProbabilityTheory.gaussianReal (mu i) (variance scale i))
      (f := fun _i : ι => fun x : ℝ => -x)
      (hf := fun _ => measurable_neg.aemeasurable)]
  refine Measure.pi_eq ?_
  intro s hs
  simp [ProbabilityTheory.gaussianReal_map_neg]

/-- A finite product of scalar Gaussian probability measures is a probability
measure. -/
instance law_isProbabilityMeasure (mu scale : ι → ℝ) :
    IsProbabilityMeasure (law mu scale) := by
  let v := variance scale
  have hv : ∀ i, IsProbabilityMeasure
      (ProbabilityTheory.gaussianReal (mu i) (v i)) := fun i => inferInstance
  change IsProbabilityMeasure
    (Measure.pi (fun i : ι => ProbabilityTheory.gaussianReal (mu i) (v i)))
  exact Measure.pi.instIsProbabilityMeasure _

/-- Coordinate projection under the finite product Gaussian law has the
corresponding scalar Gaussian law. -/
theorem law_map_eval (mu scale : ι → ℝ) (i : ι) :
    (law mu scale).map (Function.eval i) =
      ProbabilityTheory.gaussianReal (mu i) (variance scale i) := by
  let v := variance scale
  have hv : ∀ j, IsProbabilityMeasure
      (ProbabilityTheory.gaussianReal (mu j) (v j)) := fun j => inferInstance
  simpa [law] using
    (MeasureTheory.measurePreserving_eval
      (μ := fun j : ι =>
        ProbabilityTheory.gaussianReal (mu j) (v j)) i).map_eq

end

end FiniteProductGaussian
end Probability
end Mf
