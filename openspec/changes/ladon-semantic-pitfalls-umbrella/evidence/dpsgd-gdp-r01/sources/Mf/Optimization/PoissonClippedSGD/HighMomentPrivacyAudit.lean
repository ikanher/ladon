import Mf.Probability.HighMomentTailBound
import Mf.DP.DensityTailEventBounds
import Mf.DP.HigherMomentDensityErrors
import Mf.DP.PoissonGaussianReferenceHighMomentErrors
import Mf.DP.PoissonHighMomentGaussianProfile
import Mf.DP.PoissonHighMomentCalibrationBounds
import Mf.Optimization.PoissonClippedSGD.HighMomentPrivacy

/-! Axiom audit of both high-moment privacy errors, actual transcript transport,
and the scalar variance32 prefix. Complete public calibration is not claimed. -/

#print axioms Mf.Probability.momentTailCoefficient_nonneg
#print axioms Mf.Probability.sub_one_le_momentTailCoefficient_mul_pow
#print axioms Mf.Probability.sub_le_momentTailCoefficient_abs_pow_div
#print axioms Mf.Probability.max_sub_le_momentTailCoefficient_abs_pow_div
#print axioms Mf.DP.withDensity_forward_eventError_of_tail
#print axioms Mf.DP.withDensity_reverse_eventError_of_tail
#print axioms Mf.DP.highMomentEventError_nonneg
#print axioms Mf.DP.highMomentEventError_mono
#print axioms Mf.DP.withDensity_forward_highMoment_eventError
#print axioms Mf.DP.withDensity_reverse_highMoment_eventError
#print axioms Mf.DP.poissonHighMomentEPlus_nonneg
#print axioms Mf.DP.centeredPoissonReference_highMoment_directedErrors
#print axioms Mf.DP.PoissonHighMomentGaussianProfile.sampledSource_directedErrors_of_centered_allowances
#print axioms Mf.DP.PoissonHighMomentGaussianProfile.sampledSource_highMoment_directedErrors
#print axioms Mf.DP.PoissonHighMomentGaussianProfile.poissonHighMoment_product_eventBounds
#print axioms Mf.DP.PoissonHighMomentGaussianProfile.poissonHighMoment_correction_nonneg
#print axioms Mf.DP.PoissonHighMomentGaussianProfile.poissonHighMoment_actual_eventBounds_of_commonKernel
#print axioms Mf.DP.PoissonHighMomentCalibration.variance32_pos
#print axioms Mf.DP.PoissonHighMomentCalibration.variance32_lower_log_over_eps
#print axioms Mf.DP.PoissonHighMomentCalibration.variance32_ge_32
#print axioms Mf.DP.PoissonHighMomentCalibration.variance32_displacement_le
#print axioms Mf.DP.PoissonHighMomentCalibration.variance32_mass_mul_displacement_le
#print axioms Mf.DP.PoissonHighMomentCalibration.poissonHighMomentExponent_variance32_le
#print axioms Mf.DP.PoissonHighMomentCalibration.sqrt_exp_sub_one_le_eps_div_eight
#print axioms Mf.DP.PoissonHighMomentCalibration.publicOrder_bounds
#print axioms Mf.DP.PoissonHighMomentCalibration.poissonHighMomentRadius_variance32_le
#print axioms Mf.Optimization.PoissonClippedSGD.PrivacyData.optionalTranscript_highMoment_eventBounds_of_deletion
#print axioms Mf.Optimization.PoissonClippedSGD.PrivacyData.optionalTranscript_highMoment_eventBound
#print axioms Mf.Optimization.PoissonClippedSGD.PrivacyData.optionalTranscript_highMoment_approxDP_of_budget

-- The quadratic endpoint retains the exact sharp coefficient.
example : Mf.Probability.momentTailCoefficient 2 = 1 / 4 := by
  norm_num [Mf.Probability.momentTailCoefficient]

-- Tangency at p=2: the scalar upper envelope is attained at v=2h.
example (h : ℝ) (hh : 0 < h) :
    2 * h - h = Mf.Probability.momentTailCoefficient 2 * |2 * h| ^ 2 / h := by
  rw [abs_of_pos (by positivity)]
  norm_num [Mf.Probability.momentTailCoefficient]
  field_simp
  <;> ring
