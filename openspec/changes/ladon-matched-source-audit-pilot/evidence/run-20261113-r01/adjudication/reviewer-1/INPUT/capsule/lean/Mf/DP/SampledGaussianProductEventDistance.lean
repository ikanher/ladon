import Mf.DP.DensityRatioEventDistance
import Mf.DP.SampledGaussianProductOutputGrowth

/-!
# Product event-distance convergence for sampled Gaussian sources

This module turns the exact one-step chi-square estimate into an explicit
finite-product event-distance witness.  It works on the affinely normalized
exact source and matched Gaussian source; transport to the original laws is a
separate accounting-comparison layer.
-/

open Filter MeasureTheory
open scoped ENNReal NNReal Topology

namespace Mf.DP

noncomputable section

/-- The exact product chi-square is nonnegative. -/
theorem centeredBernoulliGaussianProductChiSquare_nonneg
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    0 ≤ centeredBernoulliGaussianProductChiSquare horizon samplingRate
      standardizedShift := by
  unfold centeredBernoulliGaussianProductChiSquare
  exact integral_nonneg_of_ae (Filter.Eventually.of_forall fun _ => sq_nonneg _)

/-- Tensorization and `1 + x ≤ exp x` give an exponential product bound. -/
theorem centeredBernoulliGaussianProductChiSquare_le_exp_sub_one
    (horizon : Nat) (samplingRate standardizedShift bound : Real)
    (hBound : centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤ bound) :
    centeredBernoulliGaussianProductChiSquare horizon samplingRate standardizedShift ≤
      Real.exp ((horizon : Real) * bound) - 1 := by
  rw [centeredBernoulliGaussianProductChiSquare_eq]
  have hChiZero : 0 ≤ centeredBernoulliGaussianChiSquare samplingRate
      standardizedShift := by
    unfold centeredBernoulliGaussianChiSquare
    exact integral_nonneg_of_ae (Filter.Eventually.of_forall fun _ => sq_nonneg _)
  have hbase : 1 + centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤
      Real.exp (centeredBernoulliGaussianChiSquare samplingRate standardizedShift) := by
    simpa [add_comm] using
      Real.add_one_le_exp
        (centeredBernoulliGaussianChiSquare samplingRate standardizedShift)
  have hpow := pow_le_pow_left₀ (by positivity : 0 ≤ 1 +
      centeredBernoulliGaussianChiSquare samplingRate standardizedShift) hbase horizon
  have hexpBound :
      Real.exp (centeredBernoulliGaussianChiSquare samplingRate standardizedShift) ^
          horizon ≤ Real.exp ((horizon : Real) * bound) := by
    rw [← Real.exp_nat_mul]
    exact Real.exp_le_exp.mpr
      (mul_le_mul_of_nonneg_left hBound (Nat.cast_nonneg _))
  linarith

/-- A one-step chi-square upper bound yields an explicit product event distance. -/
theorem centeredBernoulliGaussianProduct_uniformEventDistance_expBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift bound : Real)
    (hBound : centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤ bound) :
    UniformEventDistance
      (centeredBernoulliGaussianProductLaw horizon samplingRate hRate
        standardizedShift : Measure (Fin horizon → Real))
      (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
      (ENNReal.ofReal
        (Real.sqrt (Real.exp ((horizon : Real) * bound) - 1))) := by
  apply (centeredBernoulliGaussianProduct_uniformEventDistance horizon samplingRate hRate
    standardizedShift).mono
  apply ENNReal.ofReal_le_ofReal
  exact Real.sqrt_le_sqrt
    (centeredBernoulliGaussianProductChiSquare_le_exp_sub_one
      horizon samplingRate standardizedShift bound hBound)

private theorem centeredBernoulliGaussianProductChiSquare_le_expRatio
    {samplingRate sensitivity growthCoefficient noiseStddev : Real}
    {horizon : Nat}
    (hRateZero : 0 ≤ samplingRate) (hRateOne : samplingRate ≤ 1)
    (hCoefficient : 0 < growthCoefficient) (hSensitivity : 0 < sensitivity)
    (hHorizon : 0 < horizon) (hNoise : 0 < noiseStddev)
    (hGrowth : growthCoefficient * (horizon : Real) ≤ noiseStddev ^ 2)
    (hLarge : sensitivity ^ 2 ≤ growthCoefficient * (horizon : Real)) :
    centeredBernoulliGaussianProductChiSquare horizon samplingRate
        (sensitivity / noiseStddev) ≤
      Real.exp ((samplingRate ^ 2 * (1 - samplingRate) ^ 2 * sensitivity ^ 4 /
        growthCoefficient ^ 2) / (horizon : Real)) - 1 := by
  have hHorizonReal : 0 < (horizon : Real) := by exact_mod_cast hHorizon
  have hShift : |sensitivity / noiseStddev| ≤ 1 := by
    rw [abs_of_pos (div_pos hSensitivity hNoise)]
    apply (div_le_one hNoise).2
    nlinarith [hLarge, hGrowth]
  have hOneStep := centeredBernoulliGaussianChiSquare_le_fourthOrder_strong
    hRateZero hRateOne hShift
  have hOneStepBound :
      centeredBernoulliGaussianChiSquare samplingRate (sensitivity / noiseStddev) ≤
        samplingRate ^ 2 * (1 - samplingRate) ^ 2 * sensitivity ^ 4 /
          (growthCoefficient ^ 2 * (horizon : Real) ^ 2) := by
    have hDenominator : 0 < growthCoefficient ^ 2 * (horizon : Real) ^ 2 :=
      mul_pos (sq_pos_of_pos hCoefficient) (sq_pos_of_pos hHorizonReal)
    have hNoiseFourth :
        growthCoefficient ^ 2 * (horizon : Real) ^ 2 ≤ noiseStddev ^ 4 := by
      nlinarith [sq_nonneg (noiseStddev ^ 2 -
        growthCoefficient * (horizon : Real))]
    calc
      centeredBernoulliGaussianChiSquare samplingRate (sensitivity / noiseStddev) ≤
          samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
            (sensitivity / noiseStddev) ^ 4 := hOneStep
      _ = (samplingRate ^ 2 * (1 - samplingRate) ^ 2 * sensitivity ^ 4) /
          noiseStddev ^ 4 := by field_simp
      _ ≤ (samplingRate ^ 2 * (1 - samplingRate) ^ 2 * sensitivity ^ 4) /
          (growthCoefficient ^ 2 * (horizon : Real) ^ 2) := by
        apply (div_le_div_iff₀ (pow_pos hNoise 4) hDenominator).2
        exact mul_le_mul_of_nonneg_left hNoiseFourth (by positivity)
  rw [centeredBernoulliGaussianProductChiSquare_eq]
  have hChiZero :
      0 ≤ centeredBernoulliGaussianChiSquare samplingRate
        (sensitivity / noiseStddev) := by
    unfold centeredBernoulliGaussianChiSquare
    exact integral_nonneg_of_ae (Filter.Eventually.of_forall fun _ => sq_nonneg _)
  have hbase :
      1 + centeredBernoulliGaussianChiSquare samplingRate
          (sensitivity / noiseStddev) ≤
        Real.exp (centeredBernoulliGaussianChiSquare samplingRate
          (sensitivity / noiseStddev)) := by
    simpa [add_comm] using Real.add_one_le_exp
      (centeredBernoulliGaussianChiSquare samplingRate
        (sensitivity / noiseStddev))
  have hpow := pow_le_pow_left₀ (by positivity : 0 ≤ 1 +
      centeredBernoulliGaussianChiSquare samplingRate
        (sensitivity / noiseStddev)) hbase horizon
  have hExponent :
      (horizon : Real) * centeredBernoulliGaussianChiSquare samplingRate
          (sensitivity / noiseStddev) ≤
        (samplingRate ^ 2 * (1 - samplingRate) ^ 2 * sensitivity ^ 4 /
          growthCoefficient ^ 2) / (horizon : Real) := by
    have hDenominator : 0 < growthCoefficient ^ 2 * (horizon : Real) ^ 2 :=
      mul_pos (sq_pos_of_pos hCoefficient) (sq_pos_of_pos hHorizonReal)
    have hscaled := (le_div_iff₀ hDenominator).mp hOneStepBound
    apply (le_div_iff₀ hHorizonReal).2
    apply (le_div_iff₀ (sq_pos_of_pos hCoefficient)).2
    nlinarith [hscaled]
  have hExpPow :
      Real.exp (centeredBernoulliGaussianChiSquare samplingRate
        (sensitivity / noiseStddev)) ^ horizon ≤
      Real.exp ((samplingRate ^ 2 * (1 - samplingRate) ^ 2 * sensitivity ^ 4 /
        growthCoefficient ^ 2) / (horizon : Real)) := by
    rw [← Real.exp_nat_mul]
    exact Real.exp_le_exp.mpr hExponent
  linarith

/-- Linear noise-variance growth gives the explicit centered-product witness eventually. -/
theorem centeredBernoulliGaussianProduct_eventually_expBound
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : Nat → NNReal)
    {growthCoefficient : Real} (hCoefficient : 0 < growthCoefficient)
    (hSensitivity : 0 < sensitivity)
    (hGrowth : ∀ᶠ horizon : Nat in atTop,
      growthCoefficient * (horizon : Real) ≤ (noiseStddev horizon : Real) ^ 2) :
    ∃ constant : Real, 0 ≤ constant ∧ ∀ᶠ horizon : Nat in atTop,
      UniformEventDistance
        (centeredBernoulliGaussianProductLaw horizon samplingRate hRate
          (sensitivity / (noiseStddev horizon : Real)) :
          Measure (Fin horizon → Real))
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
        (ENNReal.ofReal
          (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1))) := by
  let q : Real := samplingRate
  let constant : Real :=
    q ^ 2 * (1 - q) ^ 2 * sensitivity ^ 4 / growthCoefficient ^ 2
  have hRateZero : 0 ≤ q := by dsimp [q]; positivity
  have hRateOne : q ≤ 1 := by dsimp [q]; exact_mod_cast hRate
  have hConstant : 0 ≤ constant := by dsimp [constant]; positivity
  refine ⟨constant, hConstant, ?_⟩
  obtain ⟨threshold, hthreshold⟩ :=
    exists_nat_ge (max (1 : Real) (sensitivity ^ 2 / growthCoefficient))
  filter_upwards [hGrowth, eventually_ge_atTop threshold] with horizon hG hT
  have hThresholdPos : 0 < threshold := by
    have hOne : (1 : Real) ≤ (threshold : Real) :=
      (le_max_left _ _).trans (by exact_mod_cast hthreshold)
    exact_mod_cast (lt_of_lt_of_le (zero_lt_one : (0 : Real) < 1) hOne)
  have hHorizon : 0 < horizon := lt_of_lt_of_le hThresholdPos hT
  have hHorizonReal : 0 < (horizon : Real) := by exact_mod_cast hHorizon
  have hNoise : 0 < (noiseStddev horizon : Real) := by
    have hLower : 0 < growthCoefficient * (horizon : Real) :=
      mul_pos hCoefficient hHorizonReal
    have hSquare : 0 < (noiseStddev horizon : Real) ^ 2 := hLower.trans_le hG
    nlinarith
  have hLarge : sensitivity ^ 2 ≤ growthCoefficient * (horizon : Real) := by
    have hThresholdReal :
        max (1 : Real) (sensitivity ^ 2 / growthCoefficient) ≤
          (threshold : Real) := by exact_mod_cast hthreshold
    have hRatio : sensitivity ^ 2 / growthCoefficient ≤ (horizon : Real) :=
      (le_max_right _ _).trans (hThresholdReal.trans (by exact_mod_cast hT))
    simpa [mul_comm] using (div_le_iff₀ hCoefficient).mp hRatio
  have hProduct := centeredBernoulliGaussianProductChiSquare_le_expRatio
    hRateZero hRateOne hCoefficient hSensitivity hHorizon hNoise hG hLarge
  apply (centeredBernoulliGaussianProduct_uniformEventDistance horizon
    samplingRate hRate (sensitivity / (noiseStddev horizon : Real))).mono
  apply ENNReal.ofReal_le_ofReal
  apply Real.sqrt_le_sqrt
  simpa [constant, q] using hProduct

/-- The explicit `sqrt (exp (K/T) - 1)` witness tends to zero. -/
theorem tendsto_expProductEventDistance_zero (constant : Real) :
    Tendsto (fun horizon : Nat => ENNReal.ofReal
      (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1)))
      atTop (nhds 0) := by
  have hinv : Tendsto (fun horizon : Nat => (1 : Real) / (horizon : Real))
      atTop (nhds 0) := tendsto_one_div_atTop_nhds_zero_nat
  have hscaled : Tendsto (fun horizon : Nat =>
      constant * ((1 : Real) / (horizon : Real))) atTop (nhds 0) := by
    simpa using hinv.const_mul constant
  have hexp : Tendsto (fun horizon : Nat =>
      Real.exp (constant * ((1 : Real) / (horizon : Real)))) atTop
      (nhds (Real.exp 0)) :=
    Real.continuous_exp.continuousAt.tendsto.comp hscaled
  have hsub : Tendsto (fun horizon : Nat =>
      Real.exp (constant * ((1 : Real) / (horizon : Real))) - 1) atTop
      (nhds (Real.exp 0 - 1)) := hexp.sub_const 1
  have hsqrt := hsub.sqrt
  have hof := ENNReal.tendsto_ofReal hsqrt
  simpa [div_eq_mul_inv] using hof

/-- Complete-product privacy supplies a vanishing centered-product event-distance witness. -/
theorem sampledGaussianProduct_eventually_expBound_of_profile
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : Nat → NNReal) (epsilon delta : Real)
    (hRatePos : 0 < samplingRate) (hSensitivity : 0 < sensitivity)
    (hDelta : 0 ≤ delta) (hDeltaOne : delta < 1)
    (hPrivate : ∀ horizon : Nat, 0 < horizon →
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev horizon ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
        epsilon ≤ ENNReal.ofReal delta) :
    ∃ constant : Real, 0 ≤ constant ∧
      Tendsto (fun horizon : Nat => ENNReal.ofReal
        (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1)))
        atTop (nhds 0) ∧
      ∀ᶠ horizon : Nat in atTop,
        UniformEventDistance
          (centeredBernoulliGaussianProductLaw horizon samplingRate hRate
            (sensitivity / (noiseStddev horizon : Real)) :
            Measure (Fin horizon → Real))
          (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
          (ENNReal.ofReal
            (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1))) := by
  obtain ⟨growthCoefficient, hCoefficient, hGrowth⟩ :=
    sampledGaussian_noiseStddev_sq_eventually_linear_of_productProfile
      samplingRate hRate sensitivity noiseStddev epsilon delta hRatePos
      hSensitivity hDelta hDeltaOne hPrivate
  obtain ⟨constant, hConstant, hDistance⟩ :=
    centeredBernoulliGaussianProduct_eventually_expBound samplingRate hRate
      sensitivity noiseStddev hCoefficient hSensitivity hGrowth
  exact ⟨constant, hConstant, tendsto_expProductEventDistance_zero constant, hDistance⟩

end

end Mf.DP
