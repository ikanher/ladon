import Mf.DP.PoissonHighMomentCalibration
import Mf.DP.PoissonSampledGaussianRenyiCalibration
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.SamplerStepsize

/-!
# Public parameters for the matched Poisson privacy comparison

The reviewed extension of Appendix C.4.2 of Koloskova, Hendrikx and Stich,
*Revisiting Gradient Clipping* (ICML 2023), compares multiplier variances
`16 q² T log(1/δ) / ε²` and `32 q² T log(1/δ) / ε²`. The repaired comparison
domain is fixed in
`openspec/changes/revisiting-gc-gdp-rate-comparison-umbrella/proof-contract.md`.

This owner records only public parameter assumptions and derives the exact
normalized RMS noises of those calibrations. The sampling factor cancels from
their squared normalized noises. Each noise is positive, and its own public
selector satisfies all four sufficient stepsize restrictions. Privacy and
utility conclusions are produced by separate actual-run consumers.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD

/-- The repaired comparison domain, with no privacy or utility conclusion as a field. -/
structure MatchedPrivacyDomain (n d T : ℕ) (q C ε δ : ℝ) : Prop where
  population_pos : 0 < n
  dimension_pos : 0 < d
  horizon_pos : 0 < T
  sampling_pos : 0 < q
  sampling_lt_one : q < 1
  clipping_pos : 0 < C
  epsilon_pos : 0 < ε
  epsilon_le_one : ε ≤ 1
  epsilon_le_mass : ε ≤ q ^ 2 * T
  delta_pos : 0 < δ
  delta_le_exp_neg_one : δ ≤ Real.exp (-1)

namespace MatchedParameters
open Mf.Optimization.ClippedSGD

/-- Total RMS noise of the independent finite-binomial baseline calibration. -/
def baselineNoise (n d T : ℕ) (q C ε δ : ℝ) : ℝ :=
  normalizedSumNoise n d q C
    (Real.sqrt (Mf.DP.PoissonRenyiCalibration.calibratedVariance T q ε δ))

/-- Total RMS noise of the higher-moment Gaussian-reference calibration. -/
def gaussianReferenceNoise (n d T : ℕ) (q C ε δ : ℝ) : ℝ :=
  normalizedSumNoise n d q C
    (Real.sqrt (Mf.DP.PoissonHighMomentCalibration.calibratedVariance T q ε δ))

/-- The two public multiplier variances differ by exactly a factor of two. -/
theorem calibratedVariance_eq_two_mul (T : ℕ) (q ε δ : ℝ) :
    Mf.DP.PoissonHighMomentCalibration.calibratedVariance T q ε δ =
      2 * Mf.DP.PoissonRenyiCalibration.calibratedVariance T q ε δ := by
  unfold Mf.DP.PoissonHighMomentCalibration.calibratedVariance
    Mf.DP.PoissonRenyiCalibration.calibratedVariance
    Mf.DP.PoissonHighMomentCalibration.variance32
    Mf.DP.PoissonRenyiCalibration.variance16
  ring

/-- The exact ratio is in RMS units, before any utility or stepsize comparison. -/
theorem gaussianReferenceNoise_eq (n d T : ℕ) (q C ε δ : ℝ) :
    gaussianReferenceNoise n d T q C ε δ =
      Real.sqrt 2 * baselineNoise n d T q C ε δ := by
  unfold gaussianReferenceNoise baselineNoise
  rw [calibratedVariance_eq_two_mul, Real.sqrt_mul (by norm_num : (0 : ℝ) ≤ 2)]
  unfold normalizedSumNoise
  ring

variable {n d T : ℕ} {q C ε δ : ℝ}

/-- Positivity follows from the public domain, including singleton populations. -/
theorem baselineNoise_pos (h : MatchedPrivacyDomain n d T q C ε δ) :
    0 < baselineNoise n d T q C ε δ := by
  have hV := Mf.DP.PoissonRenyiCalibration.calibratedVariance_pos
    h.epsilon_pos h.epsilon_le_mass h.delta_pos h.delta_le_exp_neg_one
  have hn : (0 : ℝ) < n := by exact_mod_cast h.population_pos
  have hd : (0 : ℝ) < d := by exact_mod_cast h.dimension_pos
  unfold baselineNoise normalizedSumNoise
  exact mul_pos
    (div_pos (mul_pos h.clipping_pos (Real.sqrt_pos.2 hd)) (mul_pos h.sampling_pos hn))
    (Real.sqrt_pos.2 hV)

/-- The Gaussian-reference run also has strictly positive RMS noise. -/
theorem gaussianReferenceNoise_pos (h : MatchedPrivacyDomain n d T q C ε δ) :
    0 < gaussianReferenceNoise n d T q C ε δ := by
  rw [gaussianReferenceNoise_eq]
  exact mul_pos (Real.sqrt_pos.2 (by norm_num)) (baselineNoise_pos h)

/-- Substitution of variance16 cancels the public sampling fraction exactly. -/
theorem baselineNoise_sq (h : MatchedPrivacyDomain n d T q C ε δ) :
    (baselineNoise n d T q C ε δ) ^ 2 =
      16 * d * C ^ 2 * T * Real.log (1 / δ) / ((n : ℝ) ^ 2 * ε ^ 2) := by
  have hV := Mf.DP.PoissonRenyiCalibration.calibratedVariance_pos
    h.epsilon_pos h.epsilon_le_mass h.delta_pos h.delta_le_exp_neg_one
  unfold baselineNoise
  rw [normalizedSumNoise_sqrt_sq _ _ _ _ _ hV.le]
  unfold Mf.DP.PoissonRenyiCalibration.calibratedVariance
    Mf.DP.PoissonRenyiCalibration.variance16
  have hn : (n : ℝ) ≠ 0 := by exact_mod_cast h.population_pos.ne'
  field_simp [h.sampling_pos.ne', h.epsilon_pos.ne', hn]

/-- Substitution of variance32 gives twice the baseline normalized noise energy. -/
theorem gaussianReferenceNoise_sq (h : MatchedPrivacyDomain n d T q C ε δ) :
    (gaussianReferenceNoise n d T q C ε δ) ^ 2 =
      32 * d * C ^ 2 * T * Real.log (1 / δ) / ((n : ℝ) ^ 2 * ε ^ 2) := by
  rw [gaussianReferenceNoise_eq, mul_pow, Real.sq_sqrt (by norm_num : (0 : ℝ) ≤ 2),
    baselineNoise_sq h]
  ring

/-- The baseline's own public selector is positive and satisfies all four restrictions. -/
theorem baseline_publicStepsize_spec (h : MatchedPrivacyDomain n d T q C ε δ)
    {L0 L1 : ℝ} (hL0 : 0 < L0) (hL1 : 0 ≤ L1) :
    let s := baselineNoise n d T q C ε δ
    let η := publicStepsize L0 L1 (1 + poissonVariance n q) (poissonVariance n q) (C / q) C s
    0 < η ∧ StepConditions η L0 L1
      (1 + poissonVariance n q) (poissonVariance n q) (C / q) C s :=
  poisson_publicStepsize_spec h.sampling_pos h.sampling_lt_one.le
    hL0 hL1 h.clipping_pos (baselineNoise_pos h)

/-- The Gaussian-reference selector uses its own noise and the same public geometry. -/
theorem gaussianReference_publicStepsize_spec (h : MatchedPrivacyDomain n d T q C ε δ)
    {L0 L1 : ℝ} (hL0 : 0 < L0) (hL1 : 0 ≤ L1) :
    let s := gaussianReferenceNoise n d T q C ε δ
    let η := publicStepsize L0 L1 (1 + poissonVariance n q) (poissonVariance n q) (C / q) C s
    0 < η ∧ StepConditions η L0 L1
      (1 + poissonVariance n q) (poissonVariance n q) (C / q) C s :=
  poisson_publicStepsize_spec h.sampling_pos h.sampling_lt_one.le
    hL0 hL1 h.clipping_pos (gaussianReferenceNoise_pos h)

end MatchedParameters
end Mf.Optimization.PoissonClippedSGD
