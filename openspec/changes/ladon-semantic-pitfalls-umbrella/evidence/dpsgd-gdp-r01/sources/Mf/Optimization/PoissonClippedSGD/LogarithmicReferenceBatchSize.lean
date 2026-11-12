import Mf.DP.PoissonLogarithmicReferenceBatchSize
import Mf.Optimization.PoissonClippedSGD.GDPBudgetAnalysis
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration

/-!
# Batch comparison with finite Gaussian-reference privacy

At fixed update count, the calibrated normalized noise and Poisson sampling
variance decrease with the sampling probability. The admissible learning-rate
interval expands, so minimizing the convergence bound separately at each
sampling probability preserves this order, including an active stability cap.

The calibration is the finite sufficient variance from
`PoissonLogarithmicReferenceCalibration`; the comparison does not substitute
the asymptotic GDP formula. Generic learning-rate and Poisson-cap lemmas are
reused from `GDPBudgetAnalysis`. The noise identity connects the scalar
coefficient to the Gaussian history law of the actual clipped-SGD algorithm.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.LogarithmicReference
open Mf.DP.PoissonLogarithmicReferenceCalibration

/-- Total second moment of the normalized Gaussian noise at the finite calibration. -/
def noiseVariance (n d : ℝ) (T : ℕ) (q c eps δ : ℝ) : ℝ :=
  c ^ 2 * d / n ^ 2 * (calibratedVariance T q eps δ / q ^ 2)

/-- Sampling variance and calibrated privacy variance in the descent coefficient. -/
def totalVariance (n d : ℝ) (T : ℕ) (q c sigma eps δ : ℝ) : ℝ :=
  (1 - q) / (q * n) * sigma ^ 2 + noiseVariance n d T q c eps δ

/-- Best admissible constant learning rate for this finite privacy calibration. -/
def learningRate (n d : ℝ) (T : ℕ) (q c sigma eps δ F L : ℝ) : ℝ :=
  optimalStep F T L (totalVariance n d T q c sigma eps δ)
    (poissonStepCap L ((1 - q) / (q * n)))

/-- Retuned expected-gradient upper bound at the finite privacy calibration. -/
def upperBound (n d : ℝ) (T : ℕ) (q c sigma eps δ F L : ℝ) : ℝ :=
  stationarityUpper c (stepRateD (learningRate n d T q c sigma eps δ F L) F T L
    (totalVariance n d T q c sigma eps δ) (8 * sigma ^ 4 / c ^ 2))

/-- The normalization agrees with the actual Gaussian history law. -/
theorem noiseVariance_eq_normalized (n d T : ℕ) {q c eps δ : ℝ}
    (hT : 0 < T) (hq : 0 < q) (he : 0 < eps) :
    noiseVariance n d T q c eps δ =
      (normalizedSumNoise n d q c (Real.sqrt (calibratedVariance T q eps δ))) ^ 2 := by
  rw [normalizedSumNoise_sqrt_sq _ _ _ _ _ (calibratedVariance_pos hT hq he).le]
  unfold noiseVariance
  ring

theorem noiseVariance_antitone {n d : ℝ} {T : ℕ} {q q' c eps δ : ℝ}
    (hd : 0 ≤ d) (hT : 0 < T) (hq : 0 < q) (hqq : q ≤ q')
    (hq'1 : q' ≤ 1) (he : 0 < eps) :
    noiseVariance n d T q' c eps δ ≤ noiseVariance n d T q c eps δ :=
  mul_le_mul_of_nonneg_left (calibratedVariance_div_sq_antitone hT hq hqq hq'1 he)
    (div_nonneg (mul_nonneg (sq_nonneg c) hd) (sq_nonneg n))

theorem totalVariance_antitone {n d : ℝ} {T : ℕ} {q q' c sigma eps δ : ℝ}
    (hn : 0 < n) (hd : 0 ≤ d) (hT : 0 < T) (hq : 0 < q) (hqq : q ≤ q')
    (hq'1 : q' ≤ 1) (he : 0 < eps) :
    totalVariance n d T q' c sigma eps δ ≤ totalVariance n d T q c sigma eps δ :=
  add_le_add
    (mul_le_mul_of_nonneg_right (poisson_kappa_antitone hn hq hqq) (sq_nonneg sigma))
    (noiseVariance_antitone hd hT hq hqq hq'1 he)

theorem totalVariance_pos {n d : ℝ} {T : ℕ} {q c sigma eps δ : ℝ}
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T) (hq : 0 < q) (hq1 : q ≤ 1)
    (hc : 0 < c) (he : 0 < eps) :
    0 < totalVariance n d T q c sigma eps δ := by
  have hv := calibratedVariance_pos (δ := δ) hT hq he
  unfold totalVariance noiseVariance
  exact add_pos_of_nonneg_of_pos
    (mul_nonneg (div_nonneg (sub_nonneg.mpr hq1) (by positivity)) (sq_nonneg sigma))
    (by positivity)

theorem learningRate_pos {n d : ℝ} {T : ℕ} {q c sigma eps δ F L : ℝ}
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T) (hq : 0 < q) (hq1 : q ≤ 1)
    (hc : 0 < c) (he : 0 < eps) (hF : 0 < F) (hL : 0 < L) :
    0 < learningRate n d T q c sigma eps δ F L :=
  optimalStep_pos hF (by exact_mod_cast hT) hL
    (totalVariance_pos hn hd hT hq hq1 hc he)
    (poissonStepCap_pos hL (div_nonneg (sub_nonneg.mpr hq1) (by positivity)))

theorem learningRate_admissible {n d : ℝ} {T : ℕ} {q c sigma eps δ F L : ℝ}
    (hn : 0 < n) (hq : 0 < q) (hq1 : q ≤ 1) (hL : 0 < L) :
    learningRate n d T q c sigma eps δ F L * L * (1 + (1 - q) / (q * n)) ≤ 1 :=
  (le_poissonStepCap_iff hL (div_nonneg (sub_nonneg.mpr hq1) (by positivity))).mp
    (optimalStep_le_cap _ _ _ _ _)

/-- Increasing batch size cannot worsen the retuned bound at fixed update count,
including when the stability cap is active. -/
theorem upperBound_antitone {n d : ℝ} {T : ℕ} {q q' c sigma eps δ F L : ℝ}
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T) (hq : 0 < q) (hqq : q ≤ q')
    (hq'1 : q' ≤ 1) (hc : 0 < c) (he : 0 < eps) (hF : 0 < F) (hL : 0 < L) :
    upperBound n d T q' c sigma eps δ F L ≤ upperBound n d T q c sigma eps δ F L := by
  have hq' := hq.trans_le hqq
  have hq1 := hqq.trans hq'1
  have hQ' := totalVariance_pos (sigma := sigma) (δ := δ) hn hd hT hq' hq'1 hc he
  have hcap' := poissonStepCap_pos hL
    (div_nonneg (sub_nonneg.mpr hq'1) (show 0 ≤ q' * n by positivity))
  have heta := learningRate_pos (sigma := sigma) (δ := δ) hn hd hT hq hq1 hc he hF hL
  have hcap : learningRate n d T q c sigma eps δ F L ≤
      poissonStepCap L ((1 - q') / (q' * n)) :=
    (optimalStep_le_cap _ _ _ _ _).trans (poissonStepCap_mono_batch hL hn hq hqq hq'1)
  unfold upperBound
  calc
    _ ≤ stationarityUpper c (stepRateD (learningRate n d T q c sigma eps δ F L)
        F T L (totalVariance n d T q' c sigma eps δ) (8 * sigma ^ 4 / c ^ 2)) :=
      stepUpper_optimal hF (by exact_mod_cast hT) hL hQ' hcap' heta hcap hc.le
    _ ≤ _ := stationarityUpper_mono hc.le (stepRateD_mono_variance heta.le hL.le
      (totalVariance_antitone hn hd.le hT hq hqq hq'1 he))

end Mf.Optimization.PoissonClippedSGD.LogarithmicReference
