import Mf.Optimization.PoissonClippedSGD.GDPFormula
import Mf.Optimization.PoissonClippedSGD.Conclusions

/-!
# Finite-sum SGD at the GDP-formula noise scale

The corrected Appendix A convergence theorem is instantiated at the total
Gaussian scale derived in `GDPFormula`. The conclusion concerns the actual
finite product history, including its integrability and fresh Poisson draws.
The logarithmic scale is an exact choice of optimization noise; a finite
privacy interpretation requires a separate accountant theorem for this law.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
noncomputable section

/-- Actual finite-sum recursion at the raw GDP-formula noise, with an explicit
unsplit expected-gradient bound and a best-expected-index consequence. -/
theorem finite_sum_gdp_formula_convergence
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta L c sigmaSG mu : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hmu : 0 < mu)
    (hclip : 4 * sigmaSG ≤ c)
    (hstep : eta * L * (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (fi : Fin n → EuclideanSpace ℝ (Fin d) → ℝ)
    (hfi : ∀ i x, HasGradientAt (fi i) (g i x) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x - y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG ^ 2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ finiteMeanObjective fi x)
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) (hT : 0 < T) :
    let s := gdpFormulaNoise n d q T c mu
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => g i (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 s
    let D := gdpFormulaD eta L n d q sigmaSG
      (finiteMeanObjective fi x0 - fLower) T c mu
    (T : ℝ)⁻¹ * ∑ t, values t ≤ stationarityUpper c D ∧
      ∃ t : Fin T, values t ≤ stationarityUpper c D := by
  dsimp only
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  have hTR : (0 : ℝ) < T := by exact_mod_cast hT
  have h := finite_sum_gaussian_convergence hn hd q hq0 hq1 eta L c sigmaSG
    (gdpFormulaNoise n d q T c mu) heta hL hc hsg
    (gdpFormulaNoise_nonneg hq hTR hc.le hmu) hclip hstep
    g hg fi hfi hLip hvariance fLower hlower x0 T hT
  dsimp only at h
  rw [poissonRateD_eq_gdpFormulaD eta L sigmaSG
    (finiteMeanObjective fi x0 - fLower) c hq hTR hmu] at h
  obtain ⟨t, ht⟩ := h.2.2.2
  exact ⟨h.1, t, ht.trans h.1⟩

end
end Mf.Optimization.PoissonClippedSGD
