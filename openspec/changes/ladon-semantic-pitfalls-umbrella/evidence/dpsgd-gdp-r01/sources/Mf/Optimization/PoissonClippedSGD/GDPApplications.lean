import Mf.Optimization.PoissonClippedSGD.GDPUtility
import Mf.Optimization.PoissonClippedSGD.GDPBudgetAnalysis

/-!
# Actual SGD consumers of the GDP budget analysis

The finite-sum process uses the admissible square-root step from `GDPStepsize`.
The optimum refers to the certified stationarity upper bound. Its expression
uses the initial gap, so a privacy application must provide public tuning inputs
or otherwise account for that selection. This owner supplies optimization
conclusions only.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
noncomputable section

/-- The actual finite SGD process at the bound-minimizing admissible step.
Every comparison uses the same specified Gaussian noise scale. -/
theorem finite_sum_gdp_formula_convergence_tuned
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (L c sigmaSG mu : ℝ) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hmu : 0 < mu) (hclip : 4 * sigmaSG ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (fi : Fin n → EuclideanSpace ℝ (Fin d) → ℝ)
    (hfi : ∀ i x, HasGradientAt (fi i) (g i x) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x - y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG ^ 2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ finiteMeanObjective fi x)
    (x0 : EuclideanSpace ℝ (Fin d))
    (hgap : 0 < finiteMeanObjective fi x0 - fLower) (T : ℕ) (hT : 0 < T) :
    let F := finiteMeanObjective fi x0 - fLower
    let Q := gdpTotalVariance n d q T c sigmaSG mu
    let cap := poissonStepCap L ((1 - (q : ℝ)) / ((q : ℝ) * n))
    let eta := optimalStep F T L Q cap
    let s := gdpFormulaNoise n d q T c mu
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => g i (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 s
    let D := gdpFormulaD eta L n d q sigmaSG F T c mu
    (T : ℝ)⁻¹ * ∑ t, values t ≤ stationarityUpper c D ∧
      (∃ t : Fin T, values t ≤ stationarityUpper c D) ∧
      ∀ e : ℝ, 0 < e → e ≤ cap →
        stationarityUpper c D ≤ stationarityUpper c (gdpFormulaD e L n d q sigmaSG F T c mu) := by
  dsimp only
  let F := finiteMeanObjective fi x0 - fLower
  let Q := gdpTotalVariance n d q T c sigmaSG mu
  let cap := poissonStepCap L ((1 - (q : ℝ)) / ((q : ℝ) * n))
  let eta := optimalStep F T L Q cap
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  have hq1R : (q : ℝ) ≤ 1 := by exact_mod_cast hq1
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hdR : (0 : ℝ) < d := by exact_mod_cast hd
  have hTR : (0 : ℝ) < T := by exact_mod_cast hT
  have hk : 0 ≤ (1 - (q : ℝ)) / ((q : ℝ) * n) :=
    div_nonneg (sub_nonneg.mpr hq1R) (by positivity)
  have hQ : 0 < Q := gdpTotalVariance_pos hnR hdR hq hq1R hTR hc hmu
  have hcap : 0 < cap := poissonStepCap_pos hL hk
  have heta : 0 < eta := optimalStep_pos hgap hTR hL hQ hcap
  have hstep : eta * L * (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) ≤ 1 :=
    (le_poissonStepCap_iff hL hk).mp (optimalStep_le_cap F T L Q cap)
  have hbase := finite_sum_gdp_formula_convergence hn hd q hq0 hq1
    eta L c sigmaSG mu heta hL hc hsg hmu hclip hstep
    g hg fi hfi hLip hvariance fLower hlower x0 T hT
  dsimp only at hbase
  refine ⟨hbase.1, hbase.2, ?_⟩
  intro e he hecap
  exact stepUpper_optimal hgap hTR hL hQ hcap he hecap hc.le

/-- The larger-batch actual process is bounded by the smaller-batch formula
at a common step satisfying the smaller-batch stability restriction. -/
theorem finite_sum_gdp_formula_batch_bound
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q q' : NNReal) (hq0 : 0 < q) (hqq : q ≤ q') (hq'1 : q' ≤ 1)
    (eta L c sigmaSG mu : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hmu : 0 < mu) (hclip : 4 * sigmaSG ≤ c)
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
    let s := gdpFormulaNoise n d q' T c mu
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => g i (gaussianIterate eta q' c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q' hq'1 s
    (T : ℝ)⁻¹ * ∑ t, values t ≤ stationarityUpper c
      (gdpFormulaD eta L n d q sigmaSG (finiteMeanObjective fi x0 - fLower) T c mu) := by
  dsimp only
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  have hqqR : (q : ℝ) ≤ q' := by exact_mod_cast hqq
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hdR : (0 : ℝ) ≤ d := by positivity
  have hTR : (0 : ℝ) < T := by exact_mod_cast hT
  have hk := poisson_kappa_antitone hnR hq hqqR
  have hm := mul_le_mul_of_nonneg_left (add_le_add_right hk 1)
    (show 0 ≤ eta * L by positivity)
  have hstep' : eta * L * (1 + (1 - (q' : ℝ)) / ((q' : ℝ) * n)) ≤ 1 :=
    hm.trans hstep
  have hbase := finite_sum_gdp_formula_convergence hn hd q' (hq0.trans_le hqq) hq'1
    eta L c sigmaSG mu heta hL hc hsg hmu hclip hstep'
    g hg fi hfi hLip hvariance fLower hlower x0 T hT
  exact hbase.1.trans (gdpUpper_antitone_batch heta.le hL.le hnR hdR hq hqqR hTR hc.le hmu)

end
end Mf.Optimization.PoissonClippedSGD
