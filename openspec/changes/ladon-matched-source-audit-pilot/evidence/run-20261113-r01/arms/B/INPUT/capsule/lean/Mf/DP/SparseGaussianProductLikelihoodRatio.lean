import Mf.DP.SparseGaussianLikelihoodRatio
import Mf.DP.FiniteProductDensityMeasure
import Mathlib.MeasureTheory.Integral.Pi

/-!
# Finite products of direct sparse Gaussian likelihood ratios

The finite product is taken against the product of the exact normalized
privacy references.  The statements include the empty horizon, where the
density is one and the log likelihood is zero.
-/

open MeasureTheory ProbabilityTheory
open scoped BigOperators

namespace Mf.DP

noncomputable section

/-- Coordinate product of the direct one-step sparse Gaussian likelihood ratio. -/
def sparseGaussianProductLikelihoodRatio
    (horizon : Nat) (samplingRate standardizedShift : Real)
    (sample : Fin horizon → Real) : Real :=
  ∏ i, sparseGaussianLikelihoodRatio samplingRate standardizedShift (sample i)

/-- The finite product inherits the unsampled-mass likelihood floor, including
the empty-horizon case. -/
theorem sparseGaussianProductLikelihoodRatio_ge_floor
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) (sample : Fin horizon → Real) :
    (1 - (samplingRate : Real)) ^ horizon ≤
      sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample := by
  unfold sparseGaussianProductLikelihoodRatio
  simpa [Fintype.card_fin] using (Finset.prod_le_prod
    (s := (Finset.univ : Finset (Fin horizon)))
    (f := fun _ : Fin horizon => (1 - (samplingRate : Real)))
    (g := fun coordinate : Fin horizon =>
      sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift
        (sample coordinate))
    (fun _ _ => sub_nonneg.mpr (by exact_mod_cast hRate))
    (fun coordinate _ => sparseGaussianLikelihoodRatio_ge_one_sub_rate samplingRate
      standardizedShift (sample coordinate)))

/-- Finite product of the direct standardized sparse Gaussian mixture. -/
def sparseGaussianProductLaw
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) : ProbabilityMeasure (Fin horizon → Real) :=
  ProbabilityMeasure.pi (fun _ =>
    sparseGaussianMixtureLaw samplingRate hRate standardizedShift)

theorem measurable_sparseGaussianProductLikelihoodRatio
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    Measurable
      (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift) := by
  unfold sparseGaussianProductLikelihoodRatio
  apply Finset.univ.measurable_fun_prod
  intro coordinate _
  exact (measurable_sparseGaussianLikelihoodRatio samplingRate standardizedShift).comp
    (measurable_pi_apply coordinate)

theorem sparseGaussianProductLikelihoodRatio_pos
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) (sample : Fin horizon → Real) :
    0 < sparseGaussianProductLikelihoodRatio horizon samplingRate
      standardizedShift sample := by
  unfold sparseGaussianProductLikelihoodRatio
  exact Finset.prod_pos fun coordinate _ =>
    sparseGaussianLikelihoodRatio_pos samplingRate hRate standardizedShift
      (sample coordinate)

/-- The product of direct sparse mixtures has the coordinate-product density. -/
theorem sparseGaussianProductLaw_eq_withDensity
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) :
    Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)) =
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)).withDensity
        (fun sample => ENNReal.ofReal
          (sparseGaussianProductLikelihoodRatio horizon samplingRate
            standardizedShift sample)) := by
  have hproduct := finiteProductDensityMeasure_eq
    (n := horizon) (gaussianReal 0 1)
    (fun _ : Fin horizon => sparseGaussianLikelihoodRatio samplingRate standardizedShift)
    (fun _ => measurable_sparseGaussianLikelihoodRatio samplingRate standardizedShift)
    (fun _ sample => (sparseGaussianLikelihoodRatio_pos samplingRate hRate
      standardizedShift sample).le)
  symm
  change densityMeasure
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1))
      (fun sample => sparseGaussianProductLikelihoodRatio horizon samplingRate
        standardizedShift sample) = _
  simp only [sparseGaussianProductLikelihoodRatio]
  rw [hproduct]
  congr 1
  funext coordinate
  exact (sparseGaussianMixtureLaw_eq_withDensity samplingRate hRate
    standardizedShift).symm

theorem integrable_sparseGaussianProductLikelihoodRatio
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    Integrable
      (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift)
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) :=
  Integrable.fintype_prod (fun _ =>
    integrable_sparseGaussianLikelihoodRatio samplingRate standardizedShift)

/-- Product-density normalization, including the empty horizon. -/
theorem integral_sparseGaussianProductLikelihoodRatio
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    (∫ sample,
      sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift sample
      ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) = 1 := by
  rw [show (∫ sample,
        sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift sample
        ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) =
      (∫ sample, sparseGaussianLikelihoodRatio samplingRate standardizedShift sample
        ∂gaussianReal 0 1) ^ Fintype.card (Fin horizon) by
    exact integral_fintype_prod_eq_pow
      (sparseGaussianLikelihoodRatio samplingRate standardizedShift)]
  rw [integral_sparseGaussianLikelihoodRatio]
  simp

/-- The product log likelihood is the sum of coordinate log likelihoods. -/
theorem log_sparseGaussianProductLikelihoodRatio_eq_sum
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) (sample : Fin horizon → Real) :
    Real.log (sparseGaussianProductLikelihoodRatio horizon samplingRate
      standardizedShift sample) =
      ∑ coordinate, Real.log (sparseGaussianLikelihoodRatio samplingRate
        standardizedShift (sample coordinate)) := by
  unfold sparseGaussianProductLikelihoodRatio
  rw [Real.log_prod]
  intro coordinate _
  exact (sparseGaussianLikelihoodRatio_pos samplingRate hRate standardizedShift
    (sample coordinate)).ne'

/-- Apply direct positive scaling independently in each product coordinate. -/
def positiveGaussianProductScaleEquiv
    (horizon : Nat) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    (Fin horizon → Real) ≃ᵐ (Fin horizon → Real) :=
  MeasurableEquiv.piCongrRight (fun _ =>
    positiveGaussianScaleEquiv noiseStddev hStddev)

/-- Coordinatewise scaling sends the reference product to the standard Gaussian product. -/
theorem sampledGaussianReferenceProductLaw_map_positiveGaussianScale
    (horizon : Nat) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianProductScaleEquiv horizon noiseStddev hStddev)
        (sampledGaussianReferenceProductLaw horizon
          (noiseStddev ^ 2) : Measure (Fin horizon → Real)) =
      Measure.pi (fun _ : Fin horizon => gaussianReal 0 1) := by
  change Measure.map
      (fun sample coordinate => positiveGaussianScaleEquiv noiseStddev hStddev
        (sample coordinate))
      (Measure.pi fun _ : Fin horizon =>
        (sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2) : Measure Real)) = _
  rw [Measure.pi_map_pi (hf := fun _ =>
    (positiveGaussianScaleEquiv noiseStddev hStddev).measurable.aemeasurable)]
  congr 1
  funext coordinate
  exact sampledGaussianOneStepReferenceLaw_map_positiveGaussianScale
    noiseStddev hStddev

/-- Coordinatewise scaling sends the sampled source product to the direct mixture product. -/
theorem sampledGaussianSourceProductLaw_map_positiveGaussianScale
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianProductScaleEquiv horizon noiseStddev hStddev)
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real)) =
      (sparseGaussianProductLaw horizon samplingRate hRate
        (sensitivity / (noiseStddev : Real)) : Measure (Fin horizon → Real)) := by
  change Measure.map
      (fun sample coordinate => positiveGaussianScaleEquiv noiseStddev hStddev
        (sample coordinate))
      (Measure.pi fun _ : Fin horizon =>
        (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure Real)) = _
  rw [Measure.pi_map_pi (hf := fun _ =>
    (positiveGaussianScaleEquiv noiseStddev hStddev).measurable.aemeasurable)]
  congr 1
  funext coordinate
  exact sampledGaussianOneStepSourceLaw_map_positiveGaussianScale samplingRate hRate
    sensitivity noiseStddev hStddev

/-- The normalized sampled source product has the direct product likelihood density. -/
theorem sampledGaussianSourceProductLaw_map_positiveGaussianScale_eq_withDensity
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (hStddev : 0 < noiseStddev) :
    Measure.map (positiveGaussianProductScaleEquiv horizon noiseStddev hStddev)
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real)) =
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)).withDensity
        (fun sample => ENNReal.ofReal
          (sparseGaussianProductLikelihoodRatio horizon samplingRate
            (sensitivity / (noiseStddev : Real)) sample)) := by
  rw [sampledGaussianSourceProductLaw_map_positiveGaussianScale]
  exact sparseGaussianProductLaw_eq_withDensity horizon samplingRate hRate _

end

end Mf.DP
