import Mf.Optimization.PoissonClippedSGD.Convergence
import Mf.Optimization.PoissonClippedSGD.FiniteSumGradient

/-!
# Public consequences and finite-sum specialization

The full chain bounds average expected true gradient norm by the unsplit proof
bound and both six-term expressions with coefficient four. The finite-sum
specialization derives the population gradient from component gradients.
The selected best iterate minimizes expectation, not each realized trajectory.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
noncomputable section

theorem gaussian_convergence_with_rates
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
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => g i (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 sigmaDP
    let avg := (T:ℝ)⁻¹ * ∑ t, values t
    let kappa := (1-(q:ℝ))/((q:ℝ)*n)
    let D := poissonRateD eta L kappa sigmaSG sigmaDP (f x0-fLower) T c
    avg ≤ Real.sqrt D + D/c ∧
      Real.sqrt D + D/c ≤ 4*poissonRate eta L kappa sigmaSG sigmaDP (f x0-fLower) T c ∧
      4*poissonRate eta L kappa sigmaSG sigmaDP (f x0-fLower) T c ≤
        4*oldRate eta L n q sigmaSG sigmaDP (f x0-fLower) T c ∧
      ∃ t : Fin T, values t ≤ avg := by
  dsimp only
  have havg := gaussian_convergence hn hd q hq0 hq1 eta L c sigmaSG sigmaDP heta hL hc hsg hs hclip hstep g hg f hf hLip hvariance fLower hlower x0 T hT
  have hrates := poisson_rates_comparison eta L c sigmaSG sigmaDP (f x0-fLower)
    T n q ((1-(q:ℝ))/((q:ℝ)*n)) heta hL hc hsg hs (sub_nonneg.mpr (hlower x0))
    (by exact_mod_cast hT) (by exact_mod_cast hn) (by exact_mod_cast hq0)
    (by exact_mod_cast hq1) hclip rfl hstep
  refine ⟨havg, hrates.1, hrates.2, ?_⟩
  obtain ⟨t, ht⟩ := exists_term_le_finite_average hT (fun t : Fin T => ∫ ω,
    ‖vectorMean (fun i => g i (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
      ∂gaussianHistoryLaw n d T q hq1 sigmaDP)
  exact ⟨t, by simpa only [div_eq_mul_inv, mul_comm] using ht⟩

theorem finite_sum_gaussian_convergence
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta L c sigmaSG sigmaDP : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hs : 0 ≤ sigmaDP)
    (hclip : 4 * sigmaSG ≤ c)
    (hstep : eta * L * (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (fi : Fin n → EuclideanSpace ℝ (Fin d) → ℝ)
    (hfi : ∀ i x, HasGradientAt (fi i) (g i x) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x-y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG^2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ finiteMeanObjective fi x)
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) (hT : 0 < T) :
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => g i (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 sigmaDP
    let avg := (T:ℝ)⁻¹ * ∑ t, values t
    let kappa := (1-(q:ℝ))/((q:ℝ)*n)
    let D := poissonRateD eta L kappa sigmaSG sigmaDP (finiteMeanObjective fi x0-fLower) T c
    avg ≤ Real.sqrt D + D/c ∧
      Real.sqrt D + D/c ≤ 4*poissonRate eta L kappa sigmaSG sigmaDP (finiteMeanObjective fi x0-fLower) T c ∧
      4*poissonRate eta L kappa sigmaSG sigmaDP (finiteMeanObjective fi x0-fLower) T c ≤
        4*oldRate eta L n q sigmaSG sigmaDP (finiteMeanObjective fi x0-fLower) T c ∧
      ∃ t : Fin T, values t ≤ avg := by
  exact gaussian_convergence_with_rates hn hd q hq0 hq1 eta L c sigmaSG sigmaDP heta hL hc hsg hs hclip hstep g hg (finiteMeanObjective fi) (finiteMeanObjective_hasGradientAt fi g hfi) hLip hvariance fLower hlower x0 T hT

end
end Mf.Optimization.PoissonClippedSGD
