import Mf.DP.PoissonLogarithmicReferenceFixedEpoch
import Mf.DP.PoissonFixedEpochVariance
import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceTunedConvergence
import Mf.Optimization.ReciprocalLinearHorizon

/-!
# Fixed expected passes in the finite-private SGD bound

The existing fixed-epoch extension of Räisä, Jälkö and Honkela,
*Subsampling is not Magic* (ICML 2024), normalizes a frozen-average privacy
variance by `Tq²`; see `PoissonFixedEpochVariance`. We reuse its exact
normalization identity for the coefficient W/T in the adaptive-SGD descent
bound, at the supplied finite Gaussian-reference variance.

At equal exact expected passes, W/T decreases with batch size. The optimized
convergence bound therefore decreases when both square-root minimizers are
admissible. The horizon-scaled stability cap shrinks with batch size for N>1,
so the cap hypothesis is not discarded. These statements concern the explicit
sufficient variance, not the earlier infimal exact-accountant calibration.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.LogarithmicReference
open Mf.DP Mf.DP.PoissonLogarithmicReferenceCalibration

/-- The older frozen-average normalization is exactly the variance coefficient
per update in the adaptive-SGD bound, at this supplied finite calibration. -/
theorem totalVariance_eq_fixedEpoch (point : PoissonFixedEpochPoint)
    (n d c sigma eps δ : ℝ) (hd : 0 ≤ d) (he : 0 < eps) :
    totalVariance n d point.horizon point.samplingRate c sigma eps δ /
        (point.horizon : ℝ) =
      poissonFixedEpochTotalAverageVarianceOfStddev point (sigma ^ 2 / n)
        (c * Real.sqrt (d * calibratedVariance point.horizon point.samplingRate eps δ) / n) := by
  have hq : (0 : ℝ) < point.samplingRate := by exact_mod_cast point.samplingRate_pos
  have hv := calibratedVariance_pos (δ := δ) point.horizon_pos hq he
  rw [← poissonFixedEpoch_averageVariance_eq]
  unfold totalVariance noiseVariance
  simp only [div_pow, mul_pow, Real.sq_sqrt (mul_nonneg hd hv.le)]
  ring

/-- Exact expected participation separates the normalized sampling and privacy costs. -/
theorem totalVariance_div_horizon_eq {T : ℕ} {E q : ℝ}
    (hpasses : (T : ℝ) * q = E) (n d c sigma eps δ : ℝ) :
    totalVariance n d T q c sigma eps δ / (T : ℝ) =
      (1 - q) / (E * n) * sigma ^ 2 +
      c ^ 2 * d / n ^ 2 * (calibratedVariance T q eps δ / ((T : ℝ) * q ^ 2)) := by
  rw [← hpasses]
  unfold totalVariance noiseVariance
  ring

/-- The complete coefficient W/T decreases along the exact fixed-pass path. -/
theorem totalVariance_exact_passes {T T' : ℕ} (hT : 0 < T) (hT' : 0 < T')
    {E n d q q' c sigma eps δ : ℝ} (hE : 0 < E) (hn : 0 < n) (hd : 0 ≤ d)
    (hq : 0 < q) (hqq : q ≤ q') (hq'1 : q' ≤ 1)
    (hpasses : (T : ℝ) * q = E) (hpasses' : (T' : ℝ) * q' = E) (he : 0 < eps) :
    totalVariance n d T' q' c sigma eps δ / (T' : ℝ) ≤
      totalVariance n d T q c sigma eps δ / (T : ℝ) := by
  rw [totalVariance_div_horizon_eq hpasses, totalVariance_div_horizon_eq hpasses']
  apply add_le_add
  · exact mul_le_mul_of_nonneg_right
      (div_le_div_of_nonneg_right (sub_le_sub_left hqq 1) (mul_pos hE hn).le) (sq_nonneg _)
  · exact mul_le_mul_of_nonneg_left
      (calibratedVariance_exact_passes hT hT' hE hq hqq hq'1 hpasses hpasses' he)
      (by positivity)

private theorem stepRateD_free_value {F T L Q bias : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hQ : 0 < Q) :
    stepRateD (Real.sqrt (2 * F / (T * L * Q))) F T L Q bias =
      bias + 2 * Real.sqrt (8 * F * L * (Q / T)) := by
  have h := ReciprocalLinearCost.cost_optimal_eq
    (show 0 < 4 * F / T by positivity) (show 0 < 2 * L * Q by positivity) bias
  have ha : (4 * F / T) / (2 * L * Q) = 2 * F / (T * L * Q) := by ring
  have hab : (4 * F / T) * (2 * L * Q) = 8 * F * L * (Q / T) := by ring
  unfold ReciprocalLinearCost.cost ReciprocalLinearCost.optimalRate at h
  rw [ha, hab] at h
  unfold stepRateD
  convert h using 1
  ring

/-- The retuned bound when the public stability cap does not truncate the root. -/
theorem upperBound_eq_of_inactive_cap {T : ℕ} {n d q c sigma eps δ F L : ℝ}
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T) (hq : 0 < q) (hq1 : q ≤ 1)
    (hc : 0 < c) (he : 0 < eps) (hF : 0 < F) (hL : 0 < L)
    (hcap : Real.sqrt (2 * F / ((T : ℝ) * L * totalVariance n d T q c sigma eps δ)) ≤
      poissonStepCap L ((1 - q) / (q * n))) :
    upperBound n d T q c sigma eps δ F L =
      stationarityUpper c (8 * sigma ^ 4 / c ^ 2 +
        2 * Real.sqrt (8 * F * L * (totalVariance n d T q c sigma eps δ / (T : ℝ)))) := by
  unfold upperBound learningRate optimalStep
  rw [min_eq_right hcap, stepRateD_free_value hF (by exact_mod_cast hT) hL
    (totalVariance_pos hn hd hT hq hq1 hc he)]

/-- Adaptive-SGD upper bounds at equal exact expected passes, with inactive caps.
This compares the finite sufficient calibration, not the exact optimal accountant. -/
theorem upperBound_exact_passes {T T' : ℕ} (hT : 0 < T) (hT' : 0 < T')
    {E n d q q' c sigma eps δ F L : ℝ} (hE : 0 < E) (hn : 0 < n) (hd : 0 < d)
    (hq : 0 < q) (hqq : q ≤ q') (hq'1 : q' ≤ 1)
    (hpasses : (T : ℝ) * q = E) (hpasses' : (T' : ℝ) * q' = E)
    (hc : 0 < c) (he : 0 < eps) (hF : 0 < F) (hL : 0 < L)
    (hcap : Real.sqrt (2 * F / ((T : ℝ) * L * totalVariance n d T q c sigma eps δ)) ≤
      poissonStepCap L ((1 - q) / (q * n)))
    (hcap' : Real.sqrt (2 * F / ((T' : ℝ) * L * totalVariance n d T' q' c sigma eps δ)) ≤
      poissonStepCap L ((1 - q') / (q' * n))) :
    upperBound n d T' q' c sigma eps δ F L ≤ upperBound n d T q c sigma eps δ F L := by
  rw [upperBound_eq_of_inactive_cap hn hd hT hq (hqq.trans hq'1) hc he hF hL hcap,
    upperBound_eq_of_inactive_cap hn hd hT' (hq.trans_le hqq) hq'1 hc he hF hL hcap']
  apply stationarityUpper_mono hc.le
  apply add_le_add le_rfl
  apply mul_le_mul_of_nonneg_left _ (by norm_num)
  apply Real.sqrt_le_sqrt
  exact mul_le_mul_of_nonneg_left
    (totalVariance_exact_passes hT hT' hE hn hd.le hq hqq hq'1 hpasses hpasses' he)
    (by positivity)

/-- Horizon-scaled admissible steps shrink with q at fixed expected passes.
This identity explains why the cap cannot be ignored in that comparison. -/
theorem scaled_cap_exact_passes {T : ℕ} {E q : ℝ}
    (hq : 0 < q) (hpasses : (T : ℝ) * q = E) (n L : ℝ) (hn : 0 < n) :
    (T : ℝ) * poissonStepCap L ((1 - q) / (q * n)) =
      E * n / (L * (1 + (n - 1) * q)) := by
  rw [← hpasses]
  unfold poissonStepCap
  field_simp
  ring

end Mf.Optimization.PoissonClippedSGD.LogarithmicReference
