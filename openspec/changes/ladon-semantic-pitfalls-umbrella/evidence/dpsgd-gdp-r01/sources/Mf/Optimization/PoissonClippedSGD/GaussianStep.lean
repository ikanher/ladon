import Mf.Optimization.PoissonClippedSGD.Algorithm
import Mf.Optimization.PoissonClippedSGD.Integrability
import Mf.Optimization.PoissonClippedSGD.OneStep

open MeasureTheory
/-!
# One-step descent for the concrete Gaussian mechanism

The actual sampled direction supplies every moment and integrability premise
of the intermediate descent result. The exported theorem assumes only the
problem, variance, clipping and stepsize restrictions, not expected descent.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD

theorem gaussian_actual_one_step
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (grad : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hgrad : ∀ x, grad x = vectorMean (fun i => g i x))
    (hg : ∀ i, Measurable (g i))
    (L eta c sigma s : ℝ) (hL0 : 0 ≤ L)
    (hf : ∀ x, HasGradientAt f (grad x) x)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (hvariance : ∀ x, meanSqDeviation (fun i => g i x)
       (vectorMean (fun i => g i x)) ≤ sigma ^ 2)
    (hsigma : 0 ≤ sigma) (hc : 0 < c) (hclip : 4*sigma ≤ c)
    (heta : 0 ≤ eta) (hstep : eta*L*(1+(1-(q:ℝ))/((q:ℝ)*(n:ℝ))) ≤ 1)
    (x : EuclideanSpace ℝ (Fin d)) :
    (∫ p, f (x - eta • (sampledGradient (q:ℝ) c g x p.1 + p.2))
      ∂gaussianStepLaw n d q hq1 s) ≤
      f x - eta/4 * clippedProgress c ‖grad x‖ +
        2*eta*sigma^4/c^2 + L*eta^2/2 *
          (((1-(q:ℝ))/((q:ℝ)*(n:ℝ)))*sigma^2 + s^2) := by
  let Y : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d) :=
    fun p => sampledGradient (q:ℝ) c g x p.1 + p.2
  have hinput : Measurable (fun p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) => (x, p.1)) :=
    measurable_const.prodMk measurable_fst
  have hsamp : Measurable (fun p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) =>
      sampledGradient (q:ℝ) c g x p.1) := by
    exact (measurable_sampledGradient (q:ℝ) c hc.le g hg).comp hinput
  have hYmeas : Measurable Y := by
    exact hsamp.add measurable_snd
  have hY : MemLp Y 2 (gaussianStepLaw n d q hq1 s) := by
    simpa [Y] using gaussian_direction_memLp q hq1 c s g x
  have hnextmeas : Measurable (fun p => x - eta • Y p) :=
    measurable_const.sub (hYmeas.const_smul eta)
  have hnextLp : MemLp (fun p => x - eta • Y p) 2
      (gaussianStepLaw n d q hq1 s) := by
    exact (memLp_const x).sub (hY.const_smul eta)
  have hnext : Integrable (fun p => f (x - eta • Y p))
      (gaussianStepLaw n d q hq1 s) :=
    integrable_objective_comp_of_memLp_two (fun p => x - eta • Y p) hnextmeas
      hnextLp f grad L hL0 hf hL x
  have hmean := gaussian_direction_mean hn q hq0 hq1 c s g x
  have henergy := gaussian_direction_energy hn hd q hq0 hq1 c s g x
  have hκ : (1-(q:ℝ))/((q:ℝ)*(n:ℝ)) = (1-(q:ℝ))/((q:ℝ)*(n:ℝ)) := rfl
  have hvar := hvariance x
  have hstep' : eta * L * (1 + (1-(q:ℝ))/((q:ℝ)*(n:ℝ))) ≤ 1 := hstep
  have hresult := expected_aligned_step_bound hn (gaussianStepLaw n d q hq1 s)
    f grad L eta hL0 hf hL x Y hY hnext (fun i => g i x) (hgrad x)
    sigma c (q:ℝ) hsigma hc hclip hvar (by exact_mod_cast hq0) (by exact_mod_cast hq1)
    ((1-(q:ℝ))/((q:ℝ)*(n:ℝ))) rfl heta hstep' (s^2) (sq_nonneg s) hmean ?_
  · simpa [Y, mul_div_assoc, mul_comm, mul_left_comm, mul_assoc] using hresult
  · simpa [Y] using henergy

end Mf.Optimization.PoissonClippedSGD
