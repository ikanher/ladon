import Mf.Probability.FiniteShiftGaussianMoments
import Mf.Optimization.PoissonClippedSGD.CountMoments
import Mf.Optimization.FinitePoissonSign.Mechanism

/-!
# Exact count-based costs for fresh clipped Poisson releases

At each fixed state, integrate the independent isotropic Gaussian first, then
average the actual finite mask. The second/fourth ceilings are the M2/M4 costs
in the GDP-informed Adam learning-rate response r01, Part U1–U2, recorded in
`openspec/changes/dpadam-batch-size-accounting-umbrella/gdp-learning-rate-r01-intake.md`.
The standard deviation is per coordinate, after division by the public `q*n`.
The query coordinates share a mask; no independence between them is assumed.
-/

set_option autoImplicit false
noncomputable section
open MeasureTheory
namespace Mf.Optimization.PoissonClippedSGD
open Mf.Probability.EuclideanGaussian Mf.Optimization.FinitePoissonSign

/-- Second release cost at coordinate noise scale `σ`. -/
def releaseSecondMoment (n d : ℕ) (q C σ : ℝ) : ℝ :=
  C^2*normalizedCountMoment n 2 q+(d : ℝ)*σ^2

/-- Fourth release cost, with the exact Gaussian cross term. -/
def releaseFourthMoment (n d : ℕ) (q C σ : ℝ) : ℝ :=
  C^4*normalizedCountMoment n 4 q+
    2*((d : ℝ)+2)*σ^2*(C^2*normalizedCountMoment n 2 q)+
    (d : ℝ)*((d : ℝ)+2)*σ^4

/-- Every fixed state has the sharp count/Gaussian release-moment ceilings. -/
theorem fresh_release_moments {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (C σ : ℝ) (hC : 0 ≤ C)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    let Y := fun p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) =>
      sampledGradient q C g x p.1 + p.2
    Integrable (fun p => ‖Y p‖^2) (signStepLaw n d q hq σ) ∧
    Integrable (fun p => ‖Y p‖^4) (signStepLaw n d q hq σ) ∧
    (∫ p, ‖Y p‖^2 ∂signStepLaw n d q hq σ) ≤ releaseSecondMoment n d q C σ ∧
    (∫ p, ‖Y p‖^4 ∂signStepLaw n d q hq σ) ≤ releaseFourthMoment n d q C σ := by
  let μ := SDE.poissonMaskLaw (Record := Fin n) q hq
  let H := sampledGradient q C g x
  have h2 := integral_sampledGradient_norm_pow_le hn q hq hq0 C hC g x 2
  have h4 := integral_sampledGradient_norm_pow_le hn q hq hq0 C hC g x 4
  refine ⟨finite_shift_integrable_sq μ H σ, finite_shift_integrable_four μ H σ, ?_, ?_⟩
  · change (∫ p, ‖H p.1+p.2‖^2 ∂μ.prod (law d σ)) ≤ _
    rw [integral_finite_shift_sq]
    simpa only [releaseSecondMoment, H, μ] using add_le_add h2 (le_refl ((d : ℝ)*σ^2))
  · change (∫ p, ‖H p.1+p.2‖^4 ∂μ.prod (law d σ)) ≤ _
    rw [integral_finite_shift_four]
    have ha : 0 ≤ 2*((d : ℝ)+2)*σ^2 := by positivity
    simpa only [releaseFourthMoment, H, μ] using add_le_add
      (add_le_add h4 (mul_le_mul_of_nonneg_left h2 ha))
      (le_refl ((d : ℝ)*((d : ℝ)+2)*σ^4))
end Mf.Optimization.PoissonClippedSGD
