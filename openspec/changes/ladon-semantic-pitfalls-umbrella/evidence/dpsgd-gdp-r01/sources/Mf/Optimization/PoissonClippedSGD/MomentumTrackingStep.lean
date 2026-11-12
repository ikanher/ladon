import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumTrackingExpectation

/-!
# Actual Poisson fresh step for corrected momentum tracking

The public expected-batch denominator and random total-count variance remain
inside the actual Bernoulli/Gaussian kernel, including empty masks.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open Mf.Optimization.FiniteMemoryAdam

/-- Fresh centering and total clipped-record energy produce the signed storage step. -/
theorem momentum_fresh_tracking_step_le {n d : ℕ}
    (hn : 0 < n) (hd : 0 < d) (π : NNReal) (hπ0 : 0 < π) (hπ1 : π ≤ 1)
    (c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (q γ L b : ℝ) (hγ : 0 < γ) (hL : 0 < L) (hb : 0 ≤ b)
    (hgate : γ * L * (1 + b) * ((1 + b)^2 + b^2) ≤ 1 + 2*b)
    (x y v : EuclideanSpace ℝ (Fin d))
    (hco : ‖clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)‖^2 ≤
      L * inner ℝ (x-y) (clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y))) :
    (∫ p, MomentumTracking.storage b
      (x-y + (q • v - γ • (sampledGradient π c g x p.1 + p.2 - clippedMean c (fun i => g i y))))
      (q • v - γ • (sampledGradient π c g x p.1 + p.2 - clippedMean c (fun i => g i y)))
      ∂gaussianStepLaw n d π hπ1 s) ≤
      MomentumTracking.storage (q*(1+b)) (x-y) v +
        γ^2*((1+b)^2+b^2)*(((1-(π:ℝ))/((π:ℝ)*n))*c^2+s^2) := by
  let μ := gaussianStepLaw n d π hπ1 s
  let Y := fun p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) =>
    sampledGradient π c g x p.1 + p.2
  let m := clippedMean c (fun i => g i x)
  let mref := clippedMean c (fun i => g i y)
  have hY : MemLp Y 2 μ := gaussian_direction_memLp π hπ1 c s g x
  have hmean : (∫ p, Y p ∂μ) = m := gaussian_direction_mean hn π hπ0 hπ1 c s g x
  have he := CenteredRelease.poisson_centered_energy_le hn hd π hπ0 hπ1 c s hc g x
  have h := MomentumTracking.integral_storage_step_le μ (fun p => Y p - m)
    (CenteredRelease.centered_memLp μ Y hY m)
    (CenteredRelease.centered_mean μ Y hY m hmean)
    (((1-(π:ℝ))/((π:ℝ)*n))*c^2+s^2) he q γ L b hγ hL hb hgate (x-y) v (m-mref) hco
  have hcancel (p) : m-mref+(Y p-m) = Y p-mref := by abel
  simpa only [hcancel, Y, μ, mref] using h

end Mf.Optimization.PoissonClippedSGD
