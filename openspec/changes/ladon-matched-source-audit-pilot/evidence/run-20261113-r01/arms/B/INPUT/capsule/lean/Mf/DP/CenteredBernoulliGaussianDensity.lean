import Mathlib.MeasureTheory.Measure.ProbabilityMeasure
import Mathlib.Probability.Distributions.Gaussian.Real

/-!
# Centered Bernoulli--Gaussian densities

This module defines the standardized centered two-component Gaussian mixture
and proves its explicit likelihood ratio with respect to the standard Gaussian.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

/-- The standard one-dimensional Gaussian as a probability measure. -/
def standardGaussianProbabilityMeasure : ProbabilityMeasure Real :=
  ⟨gaussianReal 0 1, by infer_instance⟩

/-- The centered standardized mixture `(1-q) N(-q u,1) + q N((1-q)u,1)`. -/
def centeredBernoulliGaussianMixtureLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) : ProbabilityMeasure Real := by
  let mixture : Measure Real :=
    ((1 - samplingRate : NNReal) : ENNReal) •
        gaussianReal (-(samplingRate : Real) * standardizedShift) 1 +
      (samplingRate : ENNReal) •
        gaussianReal ((1 - (samplingRate : Real)) * standardizedShift) 1
  refine ⟨mixture, ?_⟩
  constructor
  simp [mixture, ENNReal.coe_sub]
  exact tsub_add_cancel_of_le (by exact_mod_cast hRate)

/-- Explicit real-valued density ratio of the centered mixture to `N(0,1)`. -/
def centeredBernoulliGaussianDensityRatio
    (samplingRate standardizedShift sample : Real) : Real :=
  (1 - samplingRate) *
      Real.exp (-samplingRate * standardizedShift * sample -
        samplingRate ^ 2 * standardizedShift ^ 2 / 2) +
    samplingRate *
      Real.exp ((1 - samplingRate) * standardizedShift * sample -
        (1 - samplingRate) ^ 2 * standardizedShift ^ 2 / 2)

/-- Likelihood ratio of `N(shift,1)` to `N(0,1)`. -/
def gaussianShiftLikelihoodRatio (shift sample : Real) : Real :=
  Real.exp (shift * sample - shift ^ 2 / 2)

private theorem gaussianPDF_shift_eq_mul_likelihood (shift sample : Real) :
    gaussianPDF shift 1 sample =
      gaussianPDF 0 1 sample *
        ENNReal.ofReal (gaussianShiftLikelihoodRatio shift sample) := by
  change ENNReal.ofReal (gaussianPDFReal shift 1 sample) =
    ENNReal.ofReal (gaussianPDFReal 0 1 sample) * _
  rw [← ENNReal.ofReal_mul (gaussianPDFReal_nonneg 0 1 sample)]
  congr 1
  rw [gaussianPDFReal, gaussianPDFReal]
  simp only [gaussianShiftLikelihoodRatio]
  conv_rhs => rw [mul_assoc, ← Real.exp_add]
  congr 1
  norm_num
  ring

private theorem gaussianReal_shift_eq_withDensity_likelihood (shift : Real) :
    gaussianReal shift 1 =
      (gaussianReal 0 1).withDensity
        (fun sample => ENNReal.ofReal (gaussianShiftLikelihoodRatio shift sample)) := by
  let likelihood : Real → ENNReal := fun sample =>
    ENNReal.ofReal (gaussianShiftLikelihoodRatio shift sample)
  have hLikelihood : Measurable likelihood := by
    dsimp [likelihood, gaussianShiftLikelihoodRatio]
    fun_prop
  rw [gaussianReal_of_var_ne_zero shift one_ne_zero,
    gaussianReal_of_var_ne_zero 0 one_ne_zero]
  change volume.withDensity (gaussianPDF shift 1) =
    (volume.withDensity (gaussianPDF 0 1)).withDensity likelihood
  rw [← withDensity_mul volume (measurable_gaussianPDF 0 1) hLikelihood]
  apply withDensity_congr_ae
  exact ae_of_all _ (fun sample => by
    simpa [likelihood] using gaussianPDF_shift_eq_mul_likelihood shift sample)

/-- The displayed ratio is a density of the actual convex Gaussian mixture. -/
theorem centeredBernoulliGaussianMixtureLaw_eq_withDensity
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) :
    (centeredBernoulliGaussianMixtureLaw samplingRate hRate standardizedShift :
        Measure Real) =
      (standardGaussianProbabilityMeasure : Measure Real).withDensity
        (fun sample => ENNReal.ofReal
          (centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample)) := by
  let leftLR : Real → ENNReal := fun sample => ENNReal.ofReal
    (gaussianShiftLikelihoodRatio (-(samplingRate : Real) * standardizedShift) sample)
  let rightLR : Real → ENNReal := fun sample => ENNReal.ofReal
    (gaussianShiftLikelihoodRatio
      ((1 - (samplingRate : Real)) * standardizedShift) sample)
  have hleft : Measurable leftLR := by dsimp [leftLR, gaussianShiftLikelihoodRatio]; fun_prop
  have hright : Measurable rightLR := by dsimp [rightLR, gaussianShiftLikelihoodRatio]; fun_prop
  have hRateNonneg : 0 ≤ (samplingRate : Real) := NNReal.coe_nonneg samplingRate
  have hRateOne : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
  have hOneSub : 0 ≤ 1 - (samplingRate : Real) := sub_nonneg.mpr hRateOne
  change ((1 - samplingRate : NNReal) : ENNReal) •
        gaussianReal (-(samplingRate : Real) * standardizedShift) 1 +
      (samplingRate : ENNReal) •
        gaussianReal ((1 - (samplingRate : Real)) * standardizedShift) 1 = _
  nth_rewrite 1 [gaussianReal_shift_eq_withDensity_likelihood]
  nth_rewrite 2 [gaussianReal_shift_eq_withDensity_likelihood]
  change ((1 - samplingRate : NNReal) : ENNReal) •
        (gaussianReal 0 1).withDensity leftLR +
      (samplingRate : ENNReal) •
        (gaussianReal 0 1).withDensity rightLR = _
  rw [← withDensity_smul ((1 - samplingRate : NNReal) : ENNReal) hleft,
    ← withDensity_smul (samplingRate : ENNReal) hright,
    ← withDensity_add_left
      (hleft.const_smul ((1 - samplingRate : NNReal) : ENNReal))]
  apply withDensity_congr_ae
  exact ae_of_all _ (fun sample => by
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    rw [ENNReal.coe_nnreal_eq (1 - samplingRate), NNReal.coe_sub hRate,
      ENNReal.coe_nnreal_eq samplingRate]
    dsimp [leftLR, rightLR, gaussianShiftLikelihoodRatio]
    norm_num
    rw [← ENNReal.ofReal_mul hOneSub]
    rw [ENNReal.coe_nnreal_eq samplingRate,
      ← ENNReal.ofReal_mul hRateNonneg]
    rw [← ENNReal.ofReal_add
      (mul_nonneg hOneSub (Real.exp_pos _).le)
      (mul_nonneg hRateNonneg (Real.exp_pos _).le)]
    congr 1
    dsimp [centeredBernoulliGaussianDensityRatio]
    congr 1 <;> ring <;> positivity)

end

end Mf.DP
