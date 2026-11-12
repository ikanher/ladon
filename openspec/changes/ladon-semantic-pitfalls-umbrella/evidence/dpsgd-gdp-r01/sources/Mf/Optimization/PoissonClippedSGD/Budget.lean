import Mf.Optimization.PoissonClippedSGD.Rates

/-!
# Exact useful budget for the retuned Poisson quadratic instance

The step 3999 / 1000 satisfies the Poisson stability gate. These scalar facts
are consumed by the concrete model application; all square-root comparisons
are proved in Lean from rational inequalities.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD

def retunedBudget : ℝ :=
  poissonRateD (3999 / 1000) (1 / 4) ((1-8192 / 50000) / 8192)
    (Real.sqrt (99 / 10000))
    (Real.sqrt (100000 * (25415828733737 / 512000000000000000) ^ 2))
    (318572823102549 / 500000000000000) 49 (2 / 5)

theorem retunedBudget_exact : retunedBudget =
    6301562693057169050692609613189008427 / 342449192960000000000000000000000000000 := by
  unfold retunedBudget poissonRateD
  rw [show Real.sqrt (99 / 10000) ^ 4 = (Real.sqrt (99 / 10000) ^ 2) ^ 2 by ring,
    Real.sq_sqrt (by norm_num : (0:ℝ) ≤ 99 / 10000),
    Real.sq_sqrt (by positivity)]
  norm_num

theorem retunedBudget_ceiling : Real.sqrt retunedBudget + retunedBudget / (2 / 5) <
    (22707 / 125000:ℝ) := by
  have hr : Real.sqrt retunedBudget < (135652 / 1000000:ℝ) := by
    apply (Real.sqrt_lt' (by norm_num)).2
    rw [retunedBudget_exact]
    norm_num
  rw [retunedBudget_exact] at hr ⊢
  linarith

theorem retunedBudget_improves_initial :
    Real.sqrt retunedBudget + retunedBudget / (2 / 5) <
      Real.sqrt (2 * (1 / 4) * (318572823102549 / 500000000000000)) := by
  apply retunedBudget_ceiling.trans
  apply (Real.lt_sqrt (by norm_num)).2
  norm_num

end Mf.Optimization.PoissonClippedSGD
