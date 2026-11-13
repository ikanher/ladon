import Mf.DP.StandardGaussianCore

/-!
# Truncated Gaussian exponential moments

This module proves the two exact exponential-tilting identities used by sparse
Gaussian likelihood analysis.  The tilt and threshold are arbitrary real
numbers, and truncation is the closed event `sample ≤ threshold`.
-/

open MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

/-- Pointwise Gaussian completion of squares for exponential tilting. -/
theorem standardGaussianPDF_mul_likelihoodTilt
    (tilt sample : Real) :
    gaussianPDFReal 0 (1 : NNReal) sample *
        Real.exp (tilt * sample - tilt ^ 2 / 2) =
      gaussianPDFReal tilt (1 : NNReal) sample := by
  rw [gaussianPDFReal_def, gaussianPDFReal_def]
  rw [mul_assoc, ← Real.exp_add]
  congr 1
  congr 1
  norm_num
  field_simp
  ring

/-- A Gaussian likelihood tilt is integrable under the standard Gaussian. -/
theorem integrable_gaussianLikelihoodTilt (tilt : Real) :
    Integrable (fun sample : Real =>
      Real.exp (tilt * sample - tilt ^ 2 / 2))
      (gaussianReal 0 (1 : NNReal)) := by
  have h := ProbabilityTheory.integrable_exp_mul_gaussianReal
    (μ := (0 : Real)) (v := (1 : NNReal)) tilt
  convert h.const_mul (Real.exp (-(tilt ^ 2 / 2))) using 1
  funext sample
  rw [← Real.exp_add]
  congr 1
  ring

theorem integrableOn_gaussianLikelihoodTilt_Iic
    (tilt threshold : Real) :
    IntegrableOn (fun sample : Real =>
      Real.exp (tilt * sample - tilt ^ 2 / 2))
      (Iic threshold) (gaussianReal 0 (1 : NNReal)) :=
  (integrable_gaussianLikelihoodTilt tilt).integrableOn

private theorem integral_gaussianLikelihoodTilt_Iic_eq_shiftedGaussian
    (tilt threshold : Real) :
    (∫ sample in Iic threshold,
      Real.exp (tilt * sample - tilt ^ 2 / 2)
      ∂gaussianReal 0 (1 : NNReal)) =
      (gaussianReal tilt (1 : NNReal)).real (Iic threshold) := by
  let reference : Measure Real := gaussianReal 0 (1 : NNReal)
  let shifted : Measure Real := gaussianReal tilt (1 : NNReal)
  let density : Real → ENNReal := fun sample =>
    ENNReal.ofReal (Real.exp (tilt * sample - tilt ^ 2 / 2))
  let event : Set Real := Iic threshold
  have hEvent : MeasurableSet event := measurableSet_Iic
  have hDensity : Measurable density := Measurable.ennreal_ofReal (by fun_prop)
  have hMeasure : shifted = reference.withDensity density := by
    rw [show shifted = volume.withDensity (gaussianPDF tilt (1 : NNReal)) by
      simp [shifted, gaussianReal_of_var_ne_zero, one_ne_zero]]
    rw [show reference = volume.withDensity (gaussianPDF 0 (1 : NNReal)) by
      simp [reference, gaussianReal_of_var_ne_zero, one_ne_zero]]
    rw [← withDensity_mul volume (measurable_gaussianPDF 0 (1 : NNReal))]
    · congr 1
      funext sample
      unfold gaussianPDF
      rw [Pi.mul_apply, ← ENNReal.ofReal_mul (gaussianPDFReal_nonneg 0 1 sample)]
      congr 1
      exact (standardGaussianPDF_mul_likelihoodTilt tilt sample).symm
    · exact hDensity
  calc
    (∫ sample in event, Real.exp (tilt * sample - tilt ^ 2 / 2) ∂reference) =
        ∫ sample, event.indicator (fun value =>
          Real.exp (tilt * value - tilt ^ 2 / 2)) sample ∂reference := by
      rw [integral_indicator hEvent]
    _ = ∫ sample, event.indicator (fun _ => (1 : Real)) sample
          ∂(reference.withDensity density) := by
      rw [integral_withDensity_eq_integral_toReal_smul hDensity]
      · apply integral_congr_ae
        filter_upwards with sample
        by_cases hmem : sample ∈ event
        · simp only [Set.indicator_of_mem hmem]
          rw [ENNReal.toReal_ofReal (Real.exp_pos _).le]
          simp [smul_eq_mul]
        · simp [Set.indicator_of_notMem hmem]
      · exact Filter.Eventually.of_forall fun sample => by simp [density]
    _ = ∫ sample, event.indicator (fun _ => (1 : Real)) sample ∂shifted := by
      rw [← hMeasure]
    _ = shifted.real event := by
      rw [integral_indicator hEvent]
      simp [Measure.real]

/-- First exact truncated exponential moment. -/
theorem integral_gaussianLikelihoodTilt_Iic
    (tilt threshold : Real) :
    (∫ sample in Iic threshold,
      Real.exp (tilt * sample - tilt ^ 2 / 2)
      ∂gaussianReal 0 (1 : NNReal)) =
      stdNormalCDFReal (threshold - tilt) := by
  rw [integral_gaussianLikelihoodTilt_Iic_eq_shiftedGaussian]
  have hMeasure := gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
    tilt 1 threshold (by norm_num)
  have hReal := congrArg ENNReal.toReal hMeasure
  have hv : (⟨(1 : Real) ^ 2, sq_nonneg 1⟩ : NNReal) = 1 := by
    exact Subtype.ext (by norm_num)
  rw [hv] at hReal
  norm_num at hReal
  rw [stdNormalCDFReal_eq_real_measure_Iic]
  change ((gaussianReal tilt (1 : NNReal)) (Iic threshold)).toReal =
    (stdNormalMeasure (Iic (threshold - tilt))).toReal
  exact hReal

theorem gaussianLikelihoodTiltSquare_reduction
    (tilt sample : Real) :
    Real.exp (2 * tilt * sample - tilt ^ 2) =
      Real.exp (tilt ^ 2) *
        Real.exp ((2 * tilt) * sample - (2 * tilt) ^ 2 / 2) := by
  rw [← Real.exp_add]
  congr 1
  ring

theorem integrable_gaussianLikelihoodTiltSquare (tilt : Real) :
    Integrable (fun sample : Real =>
      Real.exp (2 * tilt * sample - tilt ^ 2))
      (gaussianReal 0 (1 : NNReal)) := by
  rw [show (fun sample : Real => Real.exp (2 * tilt * sample - tilt ^ 2)) =
      fun sample => Real.exp (tilt ^ 2) *
        Real.exp ((2 * tilt) * sample - (2 * tilt) ^ 2 / 2) by
    funext sample
    exact gaussianLikelihoodTiltSquare_reduction tilt sample]
  exact (integrable_gaussianLikelihoodTilt (2 * tilt)).const_mul _

theorem integrableOn_gaussianLikelihoodTiltSquare_Iic
    (tilt threshold : Real) :
    IntegrableOn (fun sample : Real =>
      Real.exp (2 * tilt * sample - tilt ^ 2))
      (Iic threshold) (gaussianReal 0 (1 : NNReal)) :=
  (integrable_gaussianLikelihoodTiltSquare tilt).integrableOn

/-- Second exact truncated exponential moment. -/
theorem integral_gaussianLikelihoodTiltSquare_Iic
    (tilt threshold : Real) :
    (∫ sample in Iic threshold,
      Real.exp (2 * tilt * sample - tilt ^ 2)
      ∂gaussianReal 0 (1 : NNReal)) =
      Real.exp (tilt ^ 2) * stdNormalCDFReal (threshold - 2 * tilt) := by
  rw [show (fun sample : Real => Real.exp (2 * tilt * sample - tilt ^ 2)) =
      fun sample => Real.exp (tilt ^ 2) *
        Real.exp ((2 * tilt) * sample - (2 * tilt) ^ 2 / 2) by
    funext sample
    exact gaussianLikelihoodTiltSquare_reduction tilt sample]
  rw [integral_const_mul]
  rw [integral_gaussianLikelihoodTilt_Iic]

end

end Mf.DP
