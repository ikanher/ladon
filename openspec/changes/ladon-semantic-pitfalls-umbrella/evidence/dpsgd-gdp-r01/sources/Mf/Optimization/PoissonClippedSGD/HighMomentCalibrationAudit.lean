import Mf.Optimization.PoissonClippedSGD.HighMomentCalibration

/-! Axiom and boundary audit for the public variance32 privacy calibration
and its actual adaptive Poisson clipped-SGD transcript consumer. -/

#print axioms Mf.DP.PoissonHighMomentCalibration.tailThreshold_sq_exp_neg
#print axioms Mf.DP.PoissonHighMomentCalibration.gaussianBudgetParameter_sq_ge
#print axioms Mf.DP.PoissonHighMomentCalibration.variance32_ge_gaussianPremise
#print axioms Mf.DP.PoissonHighMomentCalibration.exp_half_div_four_le_exp_neg
#print axioms Mf.DP.PoissonHighMomentCalibration.momentTailCoefficient_le_one
#print axioms Mf.DP.PoissonHighMomentCalibration.residual_branch_le_half_exp_neg
#print axioms Mf.DP.PoissonHighMomentCalibration.poissonHighMomentBudget_variance32_le
#print axioms Mf.DP.PoissonHighMomentCalibration.one_le_log_reciprocal
#print axioms Mf.DP.PoissonHighMomentCalibration.exp_neg_log_reciprocal
#print axioms Mf.DP.PoissonHighMomentCalibration.calibratedVariance_pos
#print axioms Mf.DP.PoissonHighMomentCalibration.poissonHighMomentBudget_calibratedVariance_le
#print axioms
  Mf.Optimization.PoissonClippedSGD.PrivacyData.optionalTranscript_highMoment_approxDP_of_calibratedVariance

open Mf.DP Mf.DP.PoissonHighMomentCalibration

-- At the largest allowed delta the public order is exactly the quadratic endpoint.
example : 2 * Nat.ceil (Real.log (1 / Real.exp (-1))) = 2 := by
  rw [one_div, ← Real.exp_neg, neg_neg, Real.log_exp]
  norm_num

-- An exact boundary witness retains eps=q²T, ell=1 and the public order p=2.
example : poissonHighMomentBudget 4 (1 / 2) 32 1 (1 / 2) 2 ≤ Real.exp (-1) := by
  have h := poissonHighMomentBudget_variance32_le (T := 4) (q := 1 / 2)
    (eps := 1) (ell := 1) (by norm_num) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) (by norm_num)
  norm_num [variance32] at h ⊢
  exact h
