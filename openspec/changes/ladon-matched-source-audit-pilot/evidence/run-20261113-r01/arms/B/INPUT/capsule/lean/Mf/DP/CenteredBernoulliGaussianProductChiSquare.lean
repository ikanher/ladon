import Mf.DP.CenteredBernoulliGaussianChiSquare
import Mf.DP.FiniteProductDensityMeasure
import Mathlib.MeasureTheory.Integral.Pi

/-!
# Finite-product chi-square for centered Bernoulli--Gaussian mixtures

This module lifts the one-step centered-mixture density ratio to `Fin T`
products and proves exact chi-square tensorization.  The statements include
the empty product, whose chi-square is zero.
-/

open MeasureTheory ProbabilityTheory
open scoped BigOperators

namespace Mf.DP

noncomputable section

/-- Product of the one-step centered-mixture density ratios. -/
def centeredBernoulliGaussianProductDensityRatio
    (horizon : Nat) (samplingRate standardizedShift : Real)
    (sample : Fin horizon → Real) : Real :=
  ∏ i, centeredBernoulliGaussianDensityRatio samplingRate standardizedShift (sample i)

/-- Finite product of the centered Bernoulli--Gaussian mixture law. -/
def centeredBernoulliGaussianProductLaw
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) : ProbabilityMeasure (Fin horizon → Real) :=
  ProbabilityMeasure.pi (fun _ =>
    centeredBernoulliGaussianMixtureLaw samplingRate hRate standardizedShift)

/-- Finite product of standard one-dimensional Gaussian laws. -/
def standardGaussianProductLaw
    (horizon : Nat) : ProbabilityMeasure (Fin horizon → Real) :=
  ProbabilityMeasure.pi (fun _ => standardGaussianProbabilityMeasure)

/-- The finite product of centered mixtures has the product density ratio. -/
theorem centeredBernoulliGaussianProductLaw_eq_withDensity
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) :
    Measure.pi (fun _ : Fin horizon =>
        (centeredBernoulliGaussianMixtureLaw samplingRate hRate standardizedShift :
          Measure Real)) =
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)).withDensity
        (fun sample => ENNReal.ofReal
          (centeredBernoulliGaussianProductDensityRatio horizon samplingRate
            standardizedShift sample)) := by
  have hRatioMeas : Measurable
      (centeredBernoulliGaussianDensityRatio samplingRate standardizedShift) := by
    unfold centeredBernoulliGaussianDensityRatio
    fun_prop
  have hRatioNonneg : ∀ sample,
      0 ≤ centeredBernoulliGaussianDensityRatio samplingRate standardizedShift sample := by
    intro sample
    have hRateNonneg : 0 ≤ (samplingRate : Real) := NNReal.coe_nonneg samplingRate
    have hRateOne : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
    unfold centeredBernoulliGaussianDensityRatio
    positivity
  have hproduct := finiteProductDensityMeasure_eq
    (n := horizon) (gaussianReal 0 1)
    (fun _ : Fin horizon =>
      centeredBernoulliGaussianDensityRatio samplingRate standardizedShift)
    (fun _ => hRatioMeas) (fun _ => hRatioNonneg)
  symm
  change densityMeasure
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1))
      (fun sample => centeredBernoulliGaussianProductDensityRatio horizon samplingRate
        standardizedShift sample) = _
  simp only [centeredBernoulliGaussianProductDensityRatio]
  rw [hproduct]
  congr 1
  funext i
  exact (centeredBernoulliGaussianMixtureLaw_eq_withDensity
    samplingRate hRate standardizedShift).symm

/-- The square of the one-step density ratio is integrable. -/
theorem integrable_centeredBernoulliGaussianDensityRatio_sq
    (samplingRate standardizedShift : Real) :
    Integrable
      (fun sample => centeredBernoulliGaussianDensityRatio
        samplingRate standardizedShift sample ^ 2)
      (gaussianReal 0 1) := by
  let leftShift := -samplingRate * standardizedShift
  let rightShift := (1 - samplingRate) * standardizedShift
  have hiLeft := integrable_gaussianShiftLikelihoodRatio_mul leftShift leftShift
  have hiRight := integrable_gaussianShiftLikelihoodRatio_mul rightShift rightShift
  have hiCross := integrable_gaussianShiftLikelihoodRatio_mul leftShift rightShift
  have heq : (fun sample =>
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
  rw [heq]
  exact ((hiLeft.const_mul _).add (hiRight.const_mul _)).add (hiCross.const_mul _)

/-- Product density-ratio integrability. -/
theorem integrable_centeredBernoulliGaussianProductDensityRatio
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    Integrable
      (centeredBernoulliGaussianProductDensityRatio horizon samplingRate standardizedShift)
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) :=
  Integrable.fintype_prod (fun _ =>
    integrable_centeredBernoulliGaussianDensityRatio samplingRate standardizedShift)

/-- The squared residual of the product density ratio is integrable. -/
theorem integrable_centeredBernoulliGaussianProductDensityRatio_sub_one_sq
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    Integrable
      (fun sample =>
        (centeredBernoulliGaussianProductDensityRatio horizon samplingRate
          standardizedShift sample - 1) ^ 2)
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) := by
  let ratio : Real → Real :=
    centeredBernoulliGaussianDensityRatio samplingRate standardizedShift
  let productRatio : (Fin horizon → Real) → Real := fun sample => ∏ i, ratio (sample i)
  have hRatio :=
    integrable_centeredBernoulliGaussianDensityRatio samplingRate standardizedShift
  have hRatioSq :=
    integrable_centeredBernoulliGaussianDensityRatio_sq samplingRate standardizedShift
  have hProduct : Integrable productRatio
      (Measure.pi fun _ : Fin horizon => gaussianReal 0 1) :=
    Integrable.fintype_prod (fun _ => hRatio)
  have hProductSq : Integrable (fun sample => productRatio sample ^ 2)
      (Measure.pi fun _ : Fin horizon => gaussianReal 0 1) := by
    have h := Integrable.fintype_prod (ι := Fin horizon)
      (f := fun _ => fun sample => ratio sample ^ 2)
      (μ := fun _ : Fin horizon => gaussianReal 0 1) (fun _ => hRatioSq)
    convert h using 1
    funext sample
    dsimp [productRatio]
    rw [Finset.prod_pow]
  have hexpand : (fun sample => (productRatio sample - 1) ^ 2) =
      fun sample => productRatio sample ^ 2 - 2 * productRatio sample + 1 := by
    funext sample
    ring
  change Integrable (fun sample => (productRatio sample - 1) ^ 2) _
  rw [hexpand]
  exact (hProductSq.sub (hProduct.const_mul _)).add (integrable_const 1)

/-- Chi-square represented by the squared product density-ratio residual. -/
def centeredBernoulliGaussianProductChiSquare
    (horizon : Nat) (samplingRate standardizedShift : Real) : Real :=
  ∫ sample,
    (centeredBernoulliGaussianProductDensityRatio horizon samplingRate
      standardizedShift sample - 1) ^ 2
    ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)

/-- Exact chi-square tensorization, including the zero-horizon boundary. -/
theorem centeredBernoulliGaussianProductChiSquare_eq
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    centeredBernoulliGaussianProductChiSquare horizon samplingRate standardizedShift =
      (1 + centeredBernoulliGaussianChiSquare samplingRate standardizedShift) ^ horizon - 1 := by
  let base : Measure Real := gaussianReal 0 1
  let ratio : Real → Real :=
    centeredBernoulliGaussianDensityRatio samplingRate standardizedShift
  let productRatio : (Fin horizon → Real) → Real := fun sample => ∏ i, ratio (sample i)
  have hRatio : Integrable ratio base :=
    integrable_centeredBernoulliGaussianDensityRatio samplingRate standardizedShift
  have hRatioSq : Integrable (fun sample => ratio sample ^ 2) base :=
    integrable_centeredBernoulliGaussianDensityRatio_sq samplingRate standardizedShift
  have hProductRatio : Integrable productRatio
      (Measure.pi fun _ : Fin horizon => base) :=
    Integrable.fintype_prod (fun _ => hRatio)
  have hProductRatioSq : Integrable (fun sample => productRatio sample ^ 2)
      (Measure.pi fun _ : Fin horizon => base) := by
    have h := Integrable.fintype_prod (ι := Fin horizon)
      (f := fun _ => fun sample => ratio sample ^ 2) (μ := fun _ => base)
      (fun _ => hRatioSq)
    convert h using 1
    funext sample
    dsimp [productRatio]
    rw [Finset.prod_pow]
  have hIntegralRatio :
      (∫ sample, productRatio sample ∂Measure.pi fun _ : Fin horizon => base) = 1 := by
    rw [show (∫ sample, productRatio sample
          ∂Measure.pi fun _ : Fin horizon => base) =
        (∫ sample, ratio sample ∂base) ^ Fintype.card (Fin horizon) by
      exact integral_fintype_prod_eq_pow ratio]
    rw [show (∫ sample, ratio sample ∂base) = 1 by
      exact integral_centeredBernoulliGaussianDensityRatio
        samplingRate standardizedShift]
    simp
  have hIntegralSq :
      (∫ sample, productRatio sample ^ 2
          ∂Measure.pi fun _ : Fin horizon => base) =
        (1 + centeredBernoulliGaussianChiSquare
          samplingRate standardizedShift) ^ horizon := by
    rw [show (∫ sample, productRatio sample ^ 2
          ∂Measure.pi fun _ : Fin horizon => base) =
        (∫ sample, ratio sample ^ 2 ∂base) ^ Fintype.card (Fin horizon) by
      rw [show (fun sample => productRatio sample ^ 2) =
          fun sample => ∏ i : Fin horizon, ratio (sample i) ^ 2 by
        funext sample
        dsimp [productRatio]
        rw [Finset.prod_pow]]
      exact integral_fintype_prod_eq_pow (fun sample => ratio sample ^ 2)]
    simp only [Fintype.card_fin]
    have hsecond : (∫ sample, ratio sample ^ 2 ∂base) =
        1 + centeredBernoulliGaussianChiSquare
          samplingRate standardizedShift := by
      dsimp [ratio, base]
      have h := centeredBernoulliGaussianChiSquare_eq_secondMoment_sub_one
        samplingRate standardizedShift
      linarith
    rw [hsecond]
  change (∫ sample, (productRatio sample - 1) ^ 2
    ∂Measure.pi fun _ : Fin horizon => base) = _
  have hexpand : (fun sample => (productRatio sample - 1) ^ 2) =
      fun sample => productRatio sample ^ 2 - 2 * productRatio sample + 1 := by
    funext sample
    ring
  rw [hexpand]
  rw [integral_add, integral_sub, integral_const_mul, hIntegralSq,
    hIntegralRatio, integral_const]
  · simp [base]
    ring
  · exact hProductRatioSq
  · exact hProductRatio.const_mul _
  · exact hProductRatioSq.sub (hProductRatio.const_mul _)
  · fun_prop

@[simp] theorem centeredBernoulliGaussianProductChiSquare_zeroHorizon
    (samplingRate standardizedShift : Real) :
    centeredBernoulliGaussianProductChiSquare 0 samplingRate standardizedShift = 0 := by
  rw [centeredBernoulliGaussianProductChiSquare_eq]
  simp

end

end Mf.DP
