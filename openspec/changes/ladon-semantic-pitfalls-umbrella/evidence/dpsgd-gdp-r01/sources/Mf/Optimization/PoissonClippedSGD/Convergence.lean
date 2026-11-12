import Mf.Optimization.PoissonClippedSGD.GaussianStep
import Mf.Optimization.PoissonClippedSGD.Telescoping
import Mf.Optimization.PoissonClippedSGD.ExpectedProgress
import Mf.Optimization.PoissonClippedSGD.FiniteAveraging
import Mf.Optimization.PoissonClippedSGD.Rates

/-!
# Finite-horizon convergence of Gaussian Poisson-clipped SGD

This theorem proves Appendix A of `docs/poisson-clipped-sgd/TARGET.md` for the
actual finite-product recursion. It derives the required integrability and
one-step descent, telescopes them, and bounds the average expected true gradient
norm. Its hypotheses contain neither an assumed descent inequality nor a
supplied stationarity certificate.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
noncomputable section

theorem gaussian_convergence
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta L c sigmaSG sigmaDP : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hs : 0 ≤ sigmaDP)
    (hclip : 4 * sigmaSG ≤ c)
    (hstep : eta * L * (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => g i x)) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x-y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG^2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ f x)
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) (hT : 0 < T) :
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => g i
        (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 sigmaDP) ≤
      Real.sqrt (poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG sigmaDP
        (f x0-fLower) T c) +
      poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG sigmaDP
        (f x0-fLower) T c / c := by
  let grad : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d) :=
    fun x => vectorMean (fun i => g i x)
  let phi : EuclideanSpace ℝ (Fin d) → ℝ := fun x => clippedProgress c ‖grad x‖
  let kappa : ℝ := (1-(q:ℝ))/((q:ℝ)*n)
  let err : ℝ := 2*eta*sigmaSG^4/c^2 + L*eta^2/2*(kappa*sigmaSG^2+sigmaDP^2)
  let D : ℝ := poissonRateD eta L kappa sigmaSG sigmaDP (f x0-fLower) T c
  have hk : 0 ≤ kappa := by
    exact div_nonneg (sub_nonneg.mpr (by exact_mod_cast hq1)) (by positivity)
  have herr : 0 ≤ err := by dsimp [err]; positivity
  have hgradmeas : Measurable grad := by
    have hsum : Measurable (fun x => ∑ i, g i x) :=
      Finset.measurable_sum _ (fun i _ => hg i)
    exact hsum.const_smul ((n:ℝ)⁻¹)
  have hfint (t : ℕ) : Integrable
      (fun ω => f (gaussianRun eta q c g x0 t ω))
      (gaussianHistoryLaw n d t q hq1 sigmaDP) :=
    integrable_objective_comp_of_memLp_two _
      (gaussianRun_measurable eta q c hc.le g hg x0 t)
      (gaussianRun_memLp hn eta c sigmaDP q hq0 hq1 hc.le g hg x0 t)
      f grad L hL.le hf hLip x0
  have hpint (t : ℕ) : Integrable
      (fun ω => phi (gaussianRun eta q c g x0 t ω))
      (gaussianHistoryLaw n d t q hq1 sigmaDP) :=
    integrable_clipped_progress_comp_of_memLp_two _
      (gaussianRun_measurable eta q c hc.le g hg x0 t)
      (gaussianRun_memLp hn eta c sigmaDP q hq0 hq1 hc.le g hg x0 t)
      grad L c hL.le hc.le hLip
  have hdes (x : EuclideanSpace ℝ (Fin d)) :
      (∫ p, f (Trajectory.update eta (sampledGradient q c g) x p)
        ∂gaussianStepLaw n d q hq1 sigmaDP) ≤ f x - eta/4*phi x + err := by
    simpa [Trajectory.update, phi, err, kappa, add_assoc] using
      gaussian_actual_one_step hn hd q hq0 hq1 f grad g (fun _ => rfl) hg
        L eta c sigmaSG sigmaDP hL.le hf hLip hvariance hsg hc hclip heta.le hstep x
  have havg := Trajectory.commonHistory_fin_average_potential_le
    (gaussianStepLaw n d q hq1 sigmaDP) eta err fLower (sampledGradient q c g)
    x0 f phi T heta herr (fun _ _ => hlower _) hdes hfint hpint hT
  have heq : 4*(f x0-fLower)/(eta*T)+4*err/eta = D := by
    dsimp [err, D, poissonRateD]
    field_simp
    <;> ring
  rw [heq] at havg
  let P : Fin T → ℝ := fun t => ∫ ω,
    phi (gaussianIterate eta q c g x0 T t.val t.isLt.le ω)
      ∂gaussianHistoryLaw n d T q hq1 sigmaDP
  let G : Fin T → ℝ := fun t => ∫ ω,
    ‖grad (gaussianIterate eta q c g x0 T t.val t.isLt.le ω)‖
      ∂gaussianHistoryLaw n d T q hq1 sigmaDP
  have hP : ∀ t, 0 ≤ P t := by
    intro t
    apply integral_nonneg
    intro ω
    exact le_min (sq_nonneg _) (mul_nonneg hc.le (norm_nonneg _))
  have hpoint : ∀ t, G t ≤ Real.sqrt (P t)+P t/c := by
    intro t
    let X := gaussianIterate eta (q:ℝ) c g x0 T t.val t.isLt.le
    have hXm := gaussianIterate_measurable eta q c hc.le g hg x0 T t.val t.isLt.le
    have hX := gaussianIterate_memLp hn eta c sigmaDP q hq0 hq1 hc.le g hg x0 T t.val t.isLt.le
    exact expected_norm_from_progress c hc (fun ω => ‖grad (X ω)‖)
      (hgradmeas.comp hXm).norm (fun _ => norm_nonneg _)
      (integrable_norm_gradient_comp_of_memLp_two X hXm hX grad L hL.le hLip x0)
      (integrable_clipped_progress_comp_of_memLp_two X hXm hX grad L c hL.le hc.le hLip)
  have havgP : (∑ t, P t)/(T:ℝ) ≤ D := by
    simpa only [P, gaussianIterate, gaussianHistoryLaw, one_div, div_eq_mul_inv, mul_comm, mul_one] using havg
  have hfinal := finite_average_sqrt_plus_linear_bound hT c D hc P G hP hpoint havgP
  simpa only [G, grad, D, kappa, div_eq_mul_inv, mul_comm] using hfinal

end
end Mf.Optimization.PoissonClippedSGD
