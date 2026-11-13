import Mf.DP.CenteredBernoulliGaussianDensity
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

/-!
# Fourth-order chi-square control for centered Bernoulli--Gaussian mixtures

The exact density-ratio second moment is computed from the standard Gaussian
moment-generating function. A scalar exponential remainder estimate then gives
the local fourth-order bound used by finite-product comparison.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

theorem integral_gaussianShiftLikelihoodRatio_mul
    (shift1 shift2 : Real) :
    ∫ sample, gaussianShiftLikelihoodRatio shift1 sample *
        gaussianShiftLikelihoodRatio shift2 sample ∂gaussianReal 0 1 =
      Real.exp (shift1 * shift2) := by
  have hmgf :
      ∫ sample, Real.exp ((shift1 + shift2) * sample) ∂gaussianReal 0 1 =
        Real.exp ((shift1 + shift2) ^ 2 / 2) := by
    simpa [mgf, mul_comm] using
      congrFun (mgf_id_gaussianReal (μ := (0 : Real)) (v := (1 : NNReal)))
        (shift1 + shift2)
  have hfun : (fun sample => gaussianShiftLikelihoodRatio shift1 sample *
        gaussianShiftLikelihoodRatio shift2 sample) =
      fun sample => Real.exp (-(shift1 ^ 2 + shift2 ^ 2) / 2) *
        Real.exp ((shift1 + shift2) * sample) := by
    funext sample
    simp only [gaussianShiftLikelihoodRatio, ← Real.exp_add]
    congr 1
    ring
  rw [hfun, integral_const_mul, hmgf, ← Real.exp_add]
  congr 1
  ring

theorem integrable_gaussianShiftLikelihoodRatio_mul
    (shift1 shift2 : Real) :
    Integrable (fun sample => gaussianShiftLikelihoodRatio shift1 sample *
      gaussianShiftLikelihoodRatio shift2 sample) (gaussianReal 0 1) := by
  have h := (integrable_exp_mul_gaussianReal (μ := (0 : Real))
    (v := (1 : NNReal)) (shift1 + shift2)).const_mul
      (Real.exp (-(shift1 ^ 2 + shift2 ^ 2) / 2))
  convert h using 1
  funext sample
  simp only [gaussianShiftLikelihoodRatio, ← Real.exp_add]
  congr 1
  ring

theorem integrable_gaussianShiftLikelihoodRatio (shift : Real) :
    Integrable (gaussianShiftLikelihoodRatio shift) (gaussianReal 0 1) := by
  unfold gaussianShiftLikelihoodRatio
  have h := (integrable_exp_mul_gaussianReal (μ := (0 : Real))
    (v := (1 : NNReal)) shift).const_mul (Real.exp (-shift ^ 2 / 2))
  convert h using 1
  funext sample
  rw [← Real.exp_add]
  congr 1
  ring

theorem integral_gaussianShiftLikelihoodRatio (shift : Real) :
    ∫ sample, gaussianShiftLikelihoodRatio shift sample ∂gaussianReal 0 1 = 1 := by
  unfold gaussianShiftLikelihoodRatio
  have hmgf : ∫ sample, Real.exp (shift * sample) ∂gaussianReal 0 1 =
      Real.exp (shift ^ 2 / 2) := by
    simpa [mgf, mul_comm] using
      congrFun (mgf_id_gaussianReal (μ := (0 : Real)) (v := (1 : NNReal))) shift
  have hfun : (fun sample => Real.exp (shift * sample - shift ^ 2 / 2)) =
      fun sample => Real.exp (-shift ^ 2 / 2) * Real.exp (shift * sample) := by
    funext sample
    rw [← Real.exp_add]
    congr 1
    ring
  rw [hfun, integral_const_mul, hmgf, ← Real.exp_add]
  ring_nf
  simp

theorem centeredBernoulliGaussianDensityRatio_eq_likelihoodRatios
    (samplingRate standardizedShift sample : Real) :
    centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample =
      (1 - samplingRate) *
          gaussianShiftLikelihoodRatio (-samplingRate * standardizedShift) sample +
        samplingRate * gaussianShiftLikelihoodRatio
          ((1 - samplingRate) * standardizedShift) sample := by
  simp [centeredBernoulliGaussianDensityRatio, gaussianShiftLikelihoodRatio]
  congr 1 <;> ring

/-- Exact standard-Gaussian second moment of the centered-mixture density ratio. -/
theorem centeredBernoulliGaussianDensityRatio_secondMoment
    (samplingRate standardizedShift : Real) :
    ∫ sample,
        centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample ^ 2
        ∂gaussianReal 0 1 =
      (1 - samplingRate) ^ 2 *
          Real.exp (samplingRate ^ 2 * standardizedShift ^ 2) +
        samplingRate ^ 2 *
          Real.exp ((1 - samplingRate) ^ 2 * standardizedShift ^ 2) +
        2 * samplingRate * (1 - samplingRate) *
          Real.exp (-samplingRate * (1 - samplingRate) * standardizedShift ^ 2) := by
  let leftShift : Real := -samplingRate * standardizedShift
  let rightShift : Real := (1 - samplingRate) * standardizedShift
  have hleft := integral_gaussianShiftLikelihoodRatio_mul leftShift leftShift
  have hright := integral_gaussianShiftLikelihoodRatio_mul rightShift rightShift
  have hcross := integral_gaussianShiftLikelihoodRatio_mul leftShift rightShift
  have hiLeft := integrable_gaussianShiftLikelihoodRatio_mul leftShift leftShift
  have hiRight := integrable_gaussianShiftLikelihoodRatio_mul rightShift rightShift
  have hiCross := integrable_gaussianShiftLikelihoodRatio_mul leftShift rightShift
  have hsquare : (fun sample =>
      centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample ^ 2) =
      fun sample =>
        (1 - samplingRate) ^ 2 *
            (gaussianShiftLikelihoodRatio leftShift sample *
              gaussianShiftLikelihoodRatio leftShift sample) +
          samplingRate ^ 2 *
            (gaussianShiftLikelihoodRatio rightShift sample *
              gaussianShiftLikelihoodRatio rightShift sample) +
          (2 * samplingRate * (1 - samplingRate)) *
            (gaussianShiftLikelihoodRatio leftShift sample *
              gaussianShiftLikelihoodRatio rightShift sample) := by
    funext sample
    rw [centeredBernoulliGaussianDensityRatio_eq_likelihoodRatios]
    change ((1 - samplingRate) * gaussianShiftLikelihoodRatio leftShift sample +
      samplingRate * gaussianShiftLikelihoodRatio rightShift sample) ^ 2 = _
    ring
  rw [hsquare, integral_add, integral_add, integral_const_mul,
    integral_const_mul, integral_const_mul, hleft, hright, hcross]
  · dsimp [leftShift, rightShift]
    congr 1 <;> ring
  · exact hiLeft.const_mul _
  · exact hiRight.const_mul _
  · exact (hiLeft.const_mul _).add (hiRight.const_mul _)
  · exact hiCross.const_mul _

theorem integrable_centeredBernoulliGaussianDensityRatio
    (samplingRate standardizedShift : Real) :
    Integrable (centeredBernoulliGaussianDensityRatio samplingRate standardizedShift)
      (gaussianReal 0 1) := by
  rw [show centeredBernoulliGaussianDensityRatio samplingRate standardizedShift =
    fun sample => (1 - samplingRate) *
        gaussianShiftLikelihoodRatio (-samplingRate * standardizedShift) sample +
      samplingRate * gaussianShiftLikelihoodRatio
        ((1 - samplingRate) * standardizedShift) sample by
    funext sample
    exact centeredBernoulliGaussianDensityRatio_eq_likelihoodRatios _ _ _]
  exact ((integrable_gaussianShiftLikelihoodRatio _).const_mul _).add
    ((integrable_gaussianShiftLikelihoodRatio _).const_mul _)

theorem integral_centeredBernoulliGaussianDensityRatio
    (samplingRate standardizedShift : Real) :
    ∫ sample, centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample
      ∂gaussianReal 0 1 = 1 := by
  rw [integral_congr_ae (ae_of_all _ fun sample =>
    centeredBernoulliGaussianDensityRatio_eq_likelihoodRatios _ _ _),
    integral_add, integral_const_mul, integral_const_mul,
    integral_gaussianShiftLikelihoodRatio, integral_gaussianShiftLikelihoodRatio]
  · ring
  · exact (integrable_gaussianShiftLikelihoodRatio _).const_mul _
  · exact (integrable_gaussianShiftLikelihoodRatio _).const_mul _

/-- Chi-square divergence represented by the squared density-ratio residual. -/
def centeredBernoulliGaussianChiSquare
    (samplingRate standardizedShift : Real) : Real :=
  ∫ sample,
    (centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample - 1) ^ 2
    ∂gaussianReal 0 1

theorem centeredBernoulliGaussianChiSquare_eq_secondMoment_sub_one
    (samplingRate standardizedShift : Real) :
    centeredBernoulliGaussianChiSquare samplingRate standardizedShift =
      (∫ sample,
        centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample ^ 2
        ∂gaussianReal 0 1) - 1 := by
  let ratio := centeredBernoulliGaussianDensityRatio samplingRate standardizedShift
  have hRatio : Integrable ratio (gaussianReal 0 1) :=
    integrable_centeredBernoulliGaussianDensityRatio _ _
  have hRatioSq : Integrable (fun sample => ratio sample ^ 2) (gaussianReal 0 1) := by
    let leftShift := -samplingRate * standardizedShift
    let rightShift := (1 - samplingRate) * standardizedShift
    have hiLeft := integrable_gaussianShiftLikelihoodRatio_mul leftShift leftShift
    have hiRight := integrable_gaussianShiftLikelihoodRatio_mul rightShift rightShift
    have hiCross := integrable_gaussianShiftLikelihoodRatio_mul leftShift rightShift
    have heq : (fun sample => ratio sample ^ 2) = fun sample =>
        (1 - samplingRate) ^ 2 *
            (gaussianShiftLikelihoodRatio leftShift sample *
              gaussianShiftLikelihoodRatio leftShift sample) +
          samplingRate ^ 2 *
            (gaussianShiftLikelihoodRatio rightShift sample *
              gaussianShiftLikelihoodRatio rightShift sample) +
          (2 * samplingRate * (1 - samplingRate)) *
            (gaussianShiftLikelihoodRatio leftShift sample *
              gaussianShiftLikelihoodRatio rightShift sample) := by
      funext sample
      dsimp [ratio]
      rw [centeredBernoulliGaussianDensityRatio_eq_likelihoodRatios]
      change ((1 - samplingRate) * gaussianShiftLikelihoodRatio leftShift sample +
        samplingRate * gaussianShiftLikelihoodRatio rightShift sample) ^ 2 = _
      ring
    rw [heq]
    exact ((hiLeft.const_mul _).add (hiRight.const_mul _)).add (hiCross.const_mul _)
  unfold centeredBernoulliGaussianChiSquare
  have heq : (fun sample => (ratio sample - 1) ^ 2) =
      fun sample => ratio sample ^ 2 - 2 * ratio sample + 1 := by
    funext sample
    ring
  rw [show (fun sample =>
      (centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample - 1) ^ 2) =
      (fun sample => (ratio sample - 1) ^ 2) by rfl, heq]
  rw [integral_add, integral_sub, integral_const_mul,
    show (∫ sample, ratio sample ∂gaussianReal 0 1) = 1 by
      exact integral_centeredBernoulliGaussianDensityRatio _ _, integral_const]
  · simp [ratio]
    ring
  · exact hRatioSq
  · exact hRatio.const_mul _
  · exact (hRatioSq.sub (hRatio.const_mul _))
  · fun_prop

/-- The scalar chi-square formula in `t = u²`. -/
def centeredBernoulliGaussianChiSquareScalar
    (samplingRate t : Real) : Real :=
  (1 - samplingRate) ^ 2 * Real.exp (samplingRate ^ 2 * t) +
    samplingRate ^ 2 * Real.exp ((1 - samplingRate) ^ 2 * t) +
    2 * samplingRate * (1 - samplingRate) *
      Real.exp (-samplingRate * (1 - samplingRate) * t) - 1

/-- Exact identification of the integral chi-square with the scalar formula at `u²`. -/
theorem centeredBernoulliGaussianChiSquare_eq_scalar
    (samplingRate standardizedShift : Real) :
    centeredBernoulliGaussianChiSquare samplingRate standardizedShift =
      centeredBernoulliGaussianChiSquareScalar samplingRate (standardizedShift ^ 2) := by
  rw [centeredBernoulliGaussianChiSquare_eq_secondMoment_sub_one,
    centeredBernoulliGaussianDensityRatio_secondMoment]
  rfl

theorem centeredBernoulliGaussianChiSquareScalar_zero (samplingRate : Real) :
    centeredBernoulliGaussianChiSquareScalar samplingRate 0 = 0 := by
  simp [centeredBernoulliGaussianChiSquareScalar]
  ring

theorem hasDerivAt_centeredBernoulliGaussianChiSquareScalar
    (samplingRate t : Real) :
    HasDerivAt (centeredBernoulliGaussianChiSquareScalar samplingRate)
      ((1 - samplingRate) ^ 2 * samplingRate ^ 2 *
          Real.exp (samplingRate ^ 2 * t) +
        samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
          Real.exp ((1 - samplingRate) ^ 2 * t) -
        2 * samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
          Real.exp (-samplingRate * (1 - samplingRate) * t)) t := by
  unfold centeredBernoulliGaussianChiSquareScalar
  let derivativeSource : Real → Real := fun y =>
    (1 - samplingRate) ^ 2 * Real.exp (samplingRate ^ 2 * y) +
      samplingRate ^ 2 * Real.exp ((1 - samplingRate) ^ 2 * y) +
      2 * samplingRate * (1 - samplingRate) *
        Real.exp (-samplingRate * (1 - samplingRate) * y) - 1
  let derivativeValue : Real :=
    (1 - samplingRate) ^ 2 * (Real.exp (samplingRate ^ 2 * t) * samplingRate ^ 2) +
      samplingRate ^ 2 *
        (Real.exp ((1 - samplingRate) ^ 2 * t) * (1 - samplingRate) ^ 2) +
      2 * samplingRate * (1 - samplingRate) *
        (Real.exp (-samplingRate * (1 - samplingRate) * t) *
          (-samplingRate * (1 - samplingRate)))
  have hleft := ((hasDerivAt_const_mul (x := t) (samplingRate ^ 2)).exp).const_mul
    ((1 - samplingRate) ^ 2)
  have hright := ((hasDerivAt_const_mul (x := t)
    ((1 - samplingRate) ^ 2)).exp).const_mul (samplingRate ^ 2)
  have hcross := ((hasDerivAt_const_mul (x := t)
    (-samplingRate * (1 - samplingRate))).exp).const_mul
      (2 * samplingRate * (1 - samplingRate))
  have hDerivative : HasDerivAt derivativeSource derivativeValue t := by
    simpa only [derivativeSource, derivativeValue, Pi.add_apply, Pi.sub_apply] using
      ((hleft.add hright).add hcross).sub_const 1
  have hSource :
      (fun y =>
        (1 - samplingRate) ^ 2 * Real.exp (samplingRate ^ 2 * y) +
          samplingRate ^ 2 * Real.exp ((1 - samplingRate) ^ 2 * y) +
          2 * samplingRate * (1 - samplingRate) *
            Real.exp (-samplingRate * (1 - samplingRate) * y) - 1) =
        derivativeSource := rfl
  have hValue :
      (1 - samplingRate) ^ 2 * samplingRate ^ 2 *
            Real.exp (samplingRate ^ 2 * t) +
          samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
            Real.exp ((1 - samplingRate) ^ 2 * t) -
          2 * samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
            Real.exp (-samplingRate * (1 - samplingRate) * t) = derivativeValue := by
    dsimp [derivativeValue]
    ring
  rw [hSource, hValue]
  exact hDerivative

theorem deriv_centeredBernoulliGaussianChiSquareScalar
    (samplingRate t : Real) :
    deriv (centeredBernoulliGaussianChiSquareScalar samplingRate) t =
      ((1 - samplingRate) ^ 2 * samplingRate ^ 2 *
          Real.exp (samplingRate ^ 2 * t) +
        samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
          Real.exp ((1 - samplingRate) ^ 2 * t) -
        2 * samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
          Real.exp (-samplingRate * (1 - samplingRate) * t)) :=
  (hasDerivAt_centeredBernoulliGaussianChiSquareScalar samplingRate t).deriv

theorem deriv_centeredBernoulliGaussianChiSquareScalar_zero (samplingRate : Real) :
    deriv (centeredBernoulliGaussianChiSquareScalar samplingRate) 0 = 0 := by
  rw [deriv_centeredBernoulliGaussianChiSquareScalar]
  simp
  ring

theorem second_deriv_centeredBernoulliGaussianChiSquareScalar
    (samplingRate t : Real) :
    deriv (deriv (centeredBernoulliGaussianChiSquareScalar samplingRate)) t =
      ((1 - samplingRate) ^ 2 * samplingRate ^ 4 *
          Real.exp (samplingRate ^ 2 * t) +
        samplingRate ^ 2 * (1 - samplingRate) ^ 4 *
          Real.exp ((1 - samplingRate) ^ 2 * t) +
        2 * samplingRate ^ 3 * (1 - samplingRate) ^ 3 *
          Real.exp (-samplingRate * (1 - samplingRate) * t)) := by
  let firstDerivative : Real → Real := fun s =>
      ((1 - samplingRate) ^ 2 * samplingRate ^ 2 *
          Real.exp (samplingRate ^ 2 * s) +
        samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
          Real.exp ((1 - samplingRate) ^ 2 * s) -
        2 * samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
          Real.exp (-samplingRate * (1 - samplingRate) * s))
  have hFirstDerivative :
      deriv (centeredBernoulliGaussianChiSquareScalar samplingRate) =
        firstDerivative := by
    funext s
    exact deriv_centeredBernoulliGaussianChiSquareScalar samplingRate s
  rw [hFirstDerivative]
  have hleft := ((hasDerivAt_const_mul (x := t) (samplingRate ^ 2)).exp).const_mul
    ((1 - samplingRate) ^ 2 * samplingRate ^ 2)
  have hright := ((hasDerivAt_const_mul (x := t)
    ((1 - samplingRate) ^ 2)).exp).const_mul
      (samplingRate ^ 2 * (1 - samplingRate) ^ 2)
  have hcross := ((hasDerivAt_const_mul (x := t)
    (-samplingRate * (1 - samplingRate))).exp).const_mul
      (2 * samplingRate ^ 2 * (1 - samplingRate) ^ 2)
  have hDerivative := ((hleft.add hright).sub hcross).deriv
  change deriv firstDerivative t = _
  convert hDerivative using 1
  · rfl
  · ring

/-- Uniform second-derivative bound on the scalar neighborhood `0 ≤ t ≤ 1`. -/
theorem second_deriv_centeredBernoulliGaussianChiSquareScalar_le
    {samplingRate t : Real}
    (hRateZero : 0 ≤ samplingRate) (hRateOne : samplingRate ≤ 1)
    (htZero : 0 ≤ t) (htOne : t ≤ 1) :
    deriv (deriv (centeredBernoulliGaussianChiSquareScalar samplingRate)) t ≤
      Real.exp 1 * samplingRate ^ 2 * (1 - samplingRate) ^ 2 := by
  rw [second_deriv_centeredBernoulliGaussianChiSquareScalar]
  have hOneSub : 0 ≤ 1 - samplingRate := sub_nonneg.mpr hRateOne
  have hRateSq : samplingRate ^ 2 ≤ 1 := by
    nlinarith [sq_nonneg (1 - samplingRate)]
  have hOneSubSq : (1 - samplingRate) ^ 2 ≤ 1 := by
    nlinarith [sq_nonneg samplingRate]
  have hleftArg : samplingRate ^ 2 * t ≤ 1 := by
    nlinarith [mul_nonneg (sq_nonneg samplingRate) htZero]
  have hrightArg : (1 - samplingRate) ^ 2 * t ≤ 1 := by
    nlinarith [mul_nonneg (sq_nonneg (1 - samplingRate)) htZero]
  have hcrossArg : -samplingRate * (1 - samplingRate) * t ≤ 1 := by
    have : 0 ≤ samplingRate * (1 - samplingRate) * t :=
      mul_nonneg (mul_nonneg hRateZero hOneSub) htZero
    linarith
  have hleftExp := Real.exp_le_exp.mpr hleftArg
  have hrightExp := Real.exp_le_exp.mpr hrightArg
  have hcrossExp := Real.exp_le_exp.mpr hcrossArg
  have hleft := mul_le_mul_of_nonneg_left hleftExp
    (mul_nonneg (sq_nonneg (1 - samplingRate))
      (mul_nonneg (sq_nonneg samplingRate) (sq_nonneg samplingRate)))
  have hright := mul_le_mul_of_nonneg_left hrightExp
    (mul_nonneg (sq_nonneg samplingRate)
      (mul_nonneg (sq_nonneg (1 - samplingRate)) (sq_nonneg (1 - samplingRate))))
  have hcross := mul_le_mul_of_nonneg_left hcrossExp
    (mul_nonneg (mul_nonneg (by positivity : 0 ≤ (2 : Real))
      (mul_nonneg (mul_nonneg hRateZero (sq_nonneg samplingRate))
        (mul_nonneg hOneSub (sq_nonneg (1 - samplingRate)))))
      (by positivity : 0 ≤ (1 : Real)))
  nlinarith [Real.exp_pos 1]

private theorem exp_sub_one_sub_self_le_sq {z : Real} (hz : |z| ≤ 1) :
    Real.exp z - 1 - z ≤ z ^ 2 := by
  have h := Real.norm_exp_sub_one_sub_id_le (by
    simpa [Real.norm_eq_abs] using hz)
  calc
    Real.exp z - 1 - z ≤ |Real.exp z - 1 - z| := le_abs_self _
    _ ≤ |z| ^ 2 := by simpa [Real.norm_eq_abs] using h
    _ = z ^ 2 := sq_abs z

private theorem centeredBernoulliGaussianChiSquareScalar_le_quadratic
    {samplingRate t : Real}
    (hRateZero : 0 ≤ samplingRate) (hRateOne : samplingRate ≤ 1)
    (htZero : 0 ≤ t) (htOne : t ≤ 1) :
    centeredBernoulliGaussianChiSquareScalar samplingRate t ≤
      samplingRate ^ 2 * (1 - samplingRate) ^ 2 * t ^ 2 := by
  have hOneSub : 0 ≤ 1 - samplingRate := sub_nonneg.mpr hRateOne
  have hRateSq : samplingRate ^ 2 ≤ 1 := by
    nlinarith [sq_nonneg (1 - samplingRate)]
  have hOneSubSq : (1 - samplingRate) ^ 2 ≤ 1 := by
    nlinarith [sq_nonneg samplingRate]
  have hz1Nonneg : 0 ≤ samplingRate ^ 2 * t :=
    mul_nonneg (sq_nonneg samplingRate) htZero
  have hz2Nonneg : 0 ≤ (1 - samplingRate) ^ 2 * t :=
    mul_nonneg (sq_nonneg (1 - samplingRate)) htZero
  have hz3Nonpos : -samplingRate * (1 - samplingRate) * t ≤ 0 := by
    have := mul_nonneg (mul_nonneg hRateZero hOneSub) htZero
    linarith
  have hz1 : |samplingRate ^ 2 * t| ≤ 1 := by
    rw [abs_of_nonneg hz1Nonneg]
    nlinarith
  have hz2 : |(1 - samplingRate) ^ 2 * t| ≤ 1 := by
    rw [abs_of_nonneg hz2Nonneg]
    nlinarith
  have hz3 : |-samplingRate * (1 - samplingRate) * t| ≤ 1 := by
    rw [abs_of_nonpos hz3Nonpos]
    have hproduct : samplingRate * (1 - samplingRate) ≤ 1 := by
      nlinarith [sq_nonneg samplingRate, sq_nonneg (1 - samplingRate)]
    nlinarith [mul_nonneg (mul_nonneg hRateZero hOneSub) htZero]
  have hleft := exp_sub_one_sub_self_le_sq hz1
  have hright := exp_sub_one_sub_self_le_sq hz2
  have hcross := exp_sub_one_sub_self_le_sq hz3
  have hleftWeighted := mul_le_mul_of_nonneg_left hleft
    (sq_nonneg (1 - samplingRate))
  have hrightWeighted := mul_le_mul_of_nonneg_left hright
    (sq_nonneg samplingRate)
  have hcrossWeighted := mul_le_mul_of_nonneg_left hcross
    (mul_nonneg (mul_nonneg (by positivity : 0 ≤ (2 : Real)) hRateZero) hOneSub)
  unfold centeredBernoulliGaussianChiSquareScalar
  nlinarith [sq_nonneg samplingRate, sq_nonneg (1 - samplingRate)]

/-- Strong local fourth-order chi-square estimate for `|u| ≤ 1`. -/
theorem centeredBernoulliGaussianChiSquare_le_fourthOrder_strong
    {samplingRate standardizedShift : Real}
    (hRateZero : 0 ≤ samplingRate) (hRateOne : samplingRate ≤ 1)
    (hShift : |standardizedShift| ≤ 1) :
    centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤
      samplingRate ^ 2 * (1 - samplingRate) ^ 2 * standardizedShift ^ 4 := by
  rw [centeredBernoulliGaussianChiSquare_eq_scalar]
  have hShiftSq : standardizedShift ^ 2 ≤ 1 := by
    rw [← sq_abs]
    simpa only [one_pow] using
      (sq_le_sq₀ (abs_nonneg standardizedShift) (by norm_num)).2 hShift
  have hstrong := centeredBernoulliGaussianChiSquareScalar_le_quadratic
    hRateZero hRateOne (sq_nonneg standardizedShift) hShiftSq
  convert hstrong using 1 <;> ring

/-- A slightly looser fourth-order estimate with the paper-facing exponential constant. -/
theorem centeredBernoulliGaussianChiSquare_le_fourthOrder
    {samplingRate standardizedShift : Real}
    (hRateZero : 0 ≤ samplingRate) (hRateOne : samplingRate ≤ 1)
    (hShift : |standardizedShift| ≤ 1) :
    centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤
      (Real.exp 1 / 2) * samplingRate ^ 2 * (1 - samplingRate) ^ 2 *
        standardizedShift ^ 4 := by
  have hCoefficient :
      0 ≤ samplingRate ^ 2 * (1 - samplingRate) ^ 2 * standardizedShift ^ 4 :=
    by positivity
  have hExp : 2 ≤ Real.exp 1 := by
    convert Real.add_one_le_exp (1 : Real) using 1 <;> norm_num
  calc
    centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤
        samplingRate ^ 2 * (1 - samplingRate) ^ 2 * standardizedShift ^ 4 := by
      exact centeredBernoulliGaussianChiSquare_le_fourthOrder_strong
        hRateZero hRateOne hShift
    _ ≤ (Real.exp 1 / 2) * samplingRate ^ 2 *
        (1 - samplingRate) ^ 2 * standardizedShift ^ 4 := by
      nlinarith

/-- Explicit radius and constant witnesses for the downstream horizon argument. -/
theorem centeredBernoulliGaussianChiSquare_localFourthOrderWitness
    {samplingRate : Real} (hRateZero : 0 ≤ samplingRate)
    (hRateOne : samplingRate ≤ 1) :
    ∃ radius constant : Real,
      0 < radius ∧ 0 ≤ constant ∧
      (∀ standardizedShift : Real, |standardizedShift| ≤ radius →
        centeredBernoulliGaussianChiSquare samplingRate standardizedShift ≤
          constant * standardizedShift ^ 4) := by
  refine ⟨1, (Real.exp 1 / 2) * samplingRate ^ 2 * (1 - samplingRate) ^ 2,
    zero_lt_one, ?_, ?_⟩
  · positivity
  · intro standardizedShift hShift
    simpa [mul_assoc] using centeredBernoulliGaussianChiSquare_le_fourthOrder
      hRateZero hRateOne hShift

end

end Mf.DP
