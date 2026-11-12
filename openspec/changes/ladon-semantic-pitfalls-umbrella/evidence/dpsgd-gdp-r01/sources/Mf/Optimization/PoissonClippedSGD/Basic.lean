import Mf.DP.EuclideanVectorClippingRegularity

/-!
# Finite quantities for Poisson clipped SGD

The mathematical target is the restricted Poisson argument in
`docs/poisson-clipped-sgd/TARGET.md`. Vectors use the Euclidean norm; record
averages use the deterministic population size. These definitions contain no
stochastic-process or convergence assumptions.
-/

namespace Mf.Optimization.PoissonClippedSGD

noncomputable section

open scoped BigOperators

/-- Population mean of a finite family of Euclidean vectors. -/
def vectorMean {n d : ℕ} (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    EuclideanSpace ℝ (Fin d) :=
  (n : ℝ)⁻¹ • ∑ i, g i

/-- Mean squared Euclidean deviation from a supplied center. -/
def meanSqDeviation {n d : ℕ} (g : Fin n → EuclideanSpace ℝ (Fin d))
    (v : EuclideanSpace ℝ (Fin d)) : ℝ :=
  (n : ℝ)⁻¹ * ∑ i, ‖g i - v‖ ^ 2

/-- Mean of individually clipped records, before sampling or Gaussian noise. -/
def clippedMean {n d : ℕ} (c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d)) : EuclideanSpace ℝ (Fin d) :=
  vectorMean fun i => Mf.DP.euclideanBallClip c (g i)

/-- Progress quantity with quadratic and linear gradient regimes. -/
def clippedProgress (c r : ℝ) : ℝ := min (r ^ 2) (c * r)

theorem meanSqDeviation_nonneg {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (v : EuclideanSpace ℝ (Fin d)) :
    0 ≤ meanSqDeviation g v := by
  unfold meanSqDeviation
  positivity

theorem vectorMean_sub {n d : ℕ}
    (g h : Fin n → EuclideanSpace ℝ (Fin d)) :
    vectorMean (fun i => g i - h i) = vectorMean g - vectorMean h := by
  simp [vectorMean, Finset.sum_sub_distrib, smul_sub]

theorem norm_vectorMean_le {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    ‖vectorMean g‖ ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i‖ := by
  rw [vectorMean, norm_smul, Real.norm_eq_abs, abs_of_nonneg (by positivity)]
  exact mul_le_mul_of_nonneg_left (norm_sum_le _ _) (by positivity)

end

end Mf.Optimization.PoissonClippedSGD
