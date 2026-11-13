import Mf.DP.CenteredBernoulliGaussianChiSquare
import Mf.DP.MatchedGaussianSourceNormalization

/-!
# Direct sparse Gaussian likelihood ratios

This module keeps the privacy reference, rather than the matched Gaussian
source, at the origin.  Dividing a sampled Gaussian step by a positive noise
standard deviation sends the reference to `N(0,1)` and gives the sampled
source the density

`1 - q + q * exp (mu * z - mu^2 / 2)`

with respect to that standard Gaussian, where `mu` is the standardized shift.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

/-- Likelihood ratio of `(1-q) N(0,1) + q N(mu,1)` against `N(0,1)`. -/
def sparseGaussianLikelihoodRatio
    (samplingRate standardizedShift sample : Real) : Real :=
  1 - samplingRate + samplingRate *
    Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2)

/-- The unsampled mixture mass is a pointwise likelihood-ratio floor. -/
theorem sparseGaussianLikelihoodRatio_ge_one_sub_rate
    (samplingRate : NNReal) (standardizedShift sample : Real) :
    1 - (samplingRate : Real) ≤
      sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift sample := by
  unfold sparseGaussianLikelihoodRatio
  exact le_add_of_nonneg_right
    (mul_nonneg (NNReal.coe_nonneg samplingRate) (Real.exp_pos _).le)

/-- The direct, uncentered standardized Bernoulli--Gaussian mixture. -/
def sparseGaussianMixtureLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) : ProbabilityMeasure Real := by
  let mixture : Measure Real :=
    ((1 - samplingRate : NNReal) : ENNReal) • gaussianReal 0 1 +
      (samplingRate : ENNReal) • gaussianReal standardizedShift 1
  refine ⟨mixture, ?_⟩
  constructor
  simp [mixture, ENNReal.coe_sub]
  exact tsub_add_cancel_of_le (by exact_mod_cast hRate)

theorem measurable_sparseGaussianLikelihoodRatio
    (samplingRate standardizedShift : Real) :
    Measurable (sparseGaussianLikelihoodRatio samplingRate standardizedShift) := by
  unfold sparseGaussianLikelihoodRatio
  fun_prop

theorem sparseGaussianLikelihoodRatio_pos
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift sample : Real) :
    0 < sparseGaussianLikelihoodRatio samplingRate standardizedShift sample := by
  unfold sparseGaussianLikelihoodRatio
  have hRateNonneg : 0 ≤ (samplingRate : Real) := NNReal.coe_nonneg samplingRate
  have hRateOne : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
  by_cases hZero : (samplingRate : Real) = 0
  · simp [hZero]
  · exact add_pos_of_nonneg_of_pos (sub_nonneg.mpr hRateOne)
      (mul_pos (lt_of_le_of_ne hRateNonneg (Ne.symm hZero)) (Real.exp_pos _))

theorem integrable_sparseGaussianLikelihoodRatio
    (samplingRate standardizedShift : Real) :
    Integrable (sparseGaussianLikelihoodRatio samplingRate standardizedShift)
      (gaussianReal 0 1) := by
  have hconst : Integrable (fun _ : Real => 1 - samplingRate) (gaussianReal 0 1) :=
    integrable_const _
  have hshift : Integrable
      (fun sample : Real => samplingRate *
        gaussianShiftLikelihoodRatio standardizedShift sample)
    (gaussianReal 0 1) :=
    (integrable_gaussianShiftLikelihoodRatio standardizedShift).const_mul samplingRate
  exact (hconst.add hshift).congr
    (Filter.Eventually.of_forall fun sample => by
      unfold sparseGaussianLikelihoodRatio gaussianShiftLikelihoodRatio
      change 1 - samplingRate + samplingRate *
        Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2) = _
      rfl)

/-- The direct one-step likelihood ratio has unit mass under `N(0,1)`. -/
theorem integral_sparseGaussianLikelihoodRatio
    (samplingRate standardizedShift : Real) :
    (∫ sample, sparseGaussianLikelihoodRatio samplingRate standardizedShift sample
      ∂gaussianReal 0 1) = 1 := by
  have hconst : Integrable (fun _ : Real => 1 - samplingRate) (gaussianReal 0 1) :=
    integrable_const _
  have hshift : Integrable
      (fun sample : Real => samplingRate *
        gaussianShiftLikelihoodRatio standardizedShift sample)
      (gaussianReal 0 1) :=
    (integrable_gaussianShiftLikelihoodRatio standardizedShift).const_mul samplingRate
  rw [show (fun sample => sparseGaussianLikelihoodRatio samplingRate standardizedShift sample) =
      fun sample => (1 - samplingRate) + samplingRate *
        gaussianShiftLikelihoodRatio standardizedShift sample by
    funext sample
    simp [sparseGaussianLikelihoodRatio, gaussianShiftLikelihoodRatio]]
  rw [integral_add hconst hshift, integral_const, integral_const_mul,
    integral_gaussianShiftLikelihoodRatio]
  simp

private theorem gaussianReal_shift_eq_withDensity_likelihood_direct (shift : Real) :
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
    change gaussianPDF shift 1 sample =
      gaussianPDF 0 1 sample * ENNReal.ofReal
        (gaussianShiftLikelihoodRatio shift sample)
    change ENNReal.ofReal (gaussianPDFReal shift 1 sample) =
      ENNReal.ofReal (gaussianPDFReal 0 1 sample) * _
    rw [← ENNReal.ofReal_mul (gaussianPDFReal_nonneg 0 1 sample)]
    congr 1
    rw [gaussianPDFReal, gaussianPDFReal]
    simp only [gaussianShiftLikelihoodRatio]
    conv_rhs => rw [mul_assoc, ← Real.exp_add]
    congr 1
    norm_num
    ring)

/-- The direct standardized mixture has the displayed density ratio. -/
theorem sparseGaussianMixtureLaw_eq_withDensity
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) :
    (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real) =
      (standardGaussianProbabilityMeasure : Measure Real).withDensity
        (fun sample => ENNReal.ofReal
          (sparseGaussianLikelihoodRatio samplingRate standardizedShift sample)) := by
  let leftLR : Real → ENNReal := fun sample =>
    ENNReal.ofReal (gaussianShiftLikelihoodRatio 0 sample)
  let rightLR : Real → ENNReal := fun sample =>
    ENNReal.ofReal (gaussianShiftLikelihoodRatio standardizedShift sample)
  have hleft : Measurable leftLR := by dsimp [leftLR, gaussianShiftLikelihoodRatio]; fun_prop
  have hright : Measurable rightLR := by dsimp [rightLR, gaussianShiftLikelihoodRatio]; fun_prop
  have hRateNonneg : 0 ≤ (samplingRate : Real) := NNReal.coe_nonneg samplingRate
  have hRateOne : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
  have hOneSub : 0 ≤ 1 - (samplingRate : Real) := sub_nonneg.mpr hRateOne
  change ((1 - samplingRate : NNReal) : ENNReal) • gaussianReal 0 1 +
      (samplingRate : ENNReal) • gaussianReal standardizedShift 1 = _
  nth_rewrite 1 [gaussianReal_shift_eq_withDensity_likelihood_direct]
  nth_rewrite 2 [gaussianReal_shift_eq_withDensity_likelihood_direct]
  change ((1 - samplingRate : NNReal) : ENNReal) •
        (gaussianReal 0 1).withDensity leftLR +
      (samplingRate : ENNReal) • (gaussianReal 0 1).withDensity rightLR = _
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
    rw [ENNReal.coe_nnreal_eq samplingRate,
      ← ENNReal.ofReal_mul hRateNonneg]
    rw [← ENNReal.ofReal_add hOneSub
      (mul_nonneg hRateNonneg (Real.exp_pos _).le)]
    congr 1)

/-- Divide a real output by a positive Gaussian noise standard deviation. -/
def positiveGaussianScaleEquiv
    (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) : Real ≃ᵐ Real :=
  (Homeomorph.mulLeft₀ (noiseStddev : Real)⁻¹
    (inv_ne_zero (by exact_mod_cast ne_of_gt hStddev))).toMeasurableEquiv

@[simp] theorem positiveGaussianScaleEquiv_apply
    (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) (sample : Real) :
    positiveGaussianScaleEquiv noiseStddev hStddev sample =
      sample / (noiseStddev : Real) := by
  simp [positiveGaussianScaleEquiv, div_eq_mul_inv, mul_comm]

theorem gaussianReal_map_positiveGaussianScaleEquiv
    (mean : Real) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianScaleEquiv noiseStddev hStddev)
        (gaussianReal mean (noiseStddev ^ 2)) =
      gaussianReal (mean / (noiseStddev : Real)) 1 := by
  rw [Measure.map_congr (ae_of_all _ fun sample =>
    positiveGaussianScaleEquiv_apply noiseStddev hStddev sample)]
  rw [gaussianReal_map_div_const]
  congr 2
  ext
  simp [hStddev.ne']

/-- Direct scaling sends the privacy reference to the standard Gaussian. -/
theorem sampledGaussianOneStepReferenceLaw_map_positiveGaussianScale
    (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianScaleEquiv noiseStddev hStddev)
        (sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2) : Measure Real) =
      gaussianReal 0 1 := by
  change Measure.map (positiveGaussianScaleEquiv noiseStddev hStddev)
      (gaussianReal 0 (noiseStddev ^ 2)) = _
  rw [gaussianReal_map_positiveGaussianScaleEquiv]
  simp

/-- Direct scaling sends the sampled source to the uncentered standardized mixture. -/
theorem sampledGaussianOneStepSourceLaw_map_positiveGaussianScale
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianScaleEquiv noiseStddev hStddev)
        (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure Real) =
      (sparseGaussianMixtureLaw samplingRate hRate
        (sensitivity / (noiseStddev : Real)) : Measure Real) := by
  rw [sampledGaussianOneStepSourceLaw_eq_gaussianMixture]
  rw [Measure.map_add _ _ (positiveGaussianScaleEquiv noiseStddev hStddev).measurable,
    Measure.map_smul, Measure.map_smul]
  rw [gaussianReal_map_positiveGaussianScaleEquiv,
    gaussianReal_map_positiveGaussianScaleEquiv]
  simp [sparseGaussianMixtureLaw]

/-- Directly normalized sampled source, expressed against its normalized reference. -/
theorem sampledGaussianOneStepSourceLaw_map_positiveGaussianScale_eq_withDensity
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianScaleEquiv noiseStddev hStddev)
        (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure Real) =
      (gaussianReal 0 1).withDensity (fun sample => ENNReal.ofReal
        (sparseGaussianLikelihoodRatio samplingRate
          (sensitivity / (noiseStddev : Real)) sample)) := by
  rw [sampledGaussianOneStepSourceLaw_map_positiveGaussianScale]
  exact sparseGaussianMixtureLaw_eq_withDensity samplingRate hRate _

end

end Mf.DP
