import Mf.Optimization.PoissonClippedSGD.BinomialCalibration

/-! Axiom and exact boundary audit for the finite-binomial variance16 baseline
and its actual adaptive transcript consumer. -/

namespace Mf.DP
#print axioms sampledGaussianRenyiMoment_succ
#print axioms shifted_energy_sum_ge
#print axioms sampledGaussianRenyiMoment_mono_order
#print axioms binomialWeight_factorial_shift
#print axioms sampledGaussianRenyiMoment_hasDerivAt_pair
#print axioms shiftedPairSum_le
#print axioms sampledGaussianLogMoment_deriv_le
#print axioms sampledGaussianLogMoment_le
#print axioms sampledGaussianLogMoment_le_smallSeparation
end Mf.DP

namespace Mf.DP.PoissonRenyiCalibration
#print axioms publicOrder_bounds
#print axioms variance16_pos
#print axioms publicOrder_div_variance16_le
#print axioms mass_mul_order_div_variance16_le
#print axioms totalCost_variance16_le
#print axioms tailBudget_variance16_le
#print axioms logScale_ge_one
#print axioms calibratedVariance_pos
#print axioms tailBudget_calibratedVariance_le
end Mf.DP.PoissonRenyiCalibration

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
#print axioms optionalTranscript_binomial_approxDP_of_calibratedVariance
end Mf.Optimization.PoissonClippedSGD.PrivacyData

open Mf.DP Mf.DP.PoissonRenyiCalibration

-- Zero sampling gives the exact unit moment, at arbitrary separation.
example (x : ℝ) : sampledGaussianRenyiMoment 2 0 x = 1 := by
  norm_num [sampledGaussianRenyiMoment, Finset.sum_range_succ]

-- Largest delta and eps=q²T retain the exact public baseline variance and order.
example : Real.exp ((3 - 1 : ℝ) *
    (4 * max 0 (sampledGaussianForwardRho 3 (1 / 2) (1 / 16)) - 1)) ≤
      Real.exp (-1) := by
  have h := tailBudget_variance16_le (T := 4) (q := 1 / 2) (ell := 1) (eps := 1)
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num)
  norm_num [variance16, publicOrder] at h ⊢
  exact h
