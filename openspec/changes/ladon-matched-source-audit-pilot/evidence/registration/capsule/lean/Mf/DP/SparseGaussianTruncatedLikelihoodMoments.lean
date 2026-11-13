import Mf.DP.SparseGaussianLikelihoodRatio
import Mf.DP.SparseGaussianProductLikelihoodRatio
import Mf.DP.FiniteMeasurePositivePartSecondMoment
import Mf.DP.SampledGaussianProductMaximumEvent
import Mf.DP.TruncatedGaussianExponentialMoments
import Mathlib.MeasureTheory.Function.L2Space

/-!
# Truncated sparse-Gaussian likelihood moments

These are the exact one-coordinate moment identities used by the finite
maximum-event bracket.  They are stated under the standard Gaussian
reference and retain the shifted CDF arguments explicitly.
-/

open MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- The standard product reference restricted to the below-threshold box. -/
def sparseGaussianProductBelowBoxReferenceMeasure
    (horizon : Nat) (threshold : Real) : Measure (Fin horizon → Real) :=
  (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)).restrict
    (sparseGaussianProductBelowBox horizon threshold)

theorem integrable_sparseGaussianLikelihoodRatio_sq
    (samplingRate standardizedShift : Real) :
    Integrable (fun sample =>
      (sparseGaussianLikelihoodRatio samplingRate standardizedShift sample) ^ 2)
      (gaussianReal 0 1) := by
  let tilt : Real → Real := gaussianShiftLikelihoodRatio standardizedShift
  have hconst : Integrable (fun _ : Real => (1 - samplingRate) ^ 2)
      (gaussianReal 0 1) := integrable_const _
  have htilt : Integrable (fun sample : Real =>
      2 * samplingRate * (1 - samplingRate) * tilt sample)
      (gaussianReal 0 1) :=
    (integrable_gaussianShiftLikelihoodRatio standardizedShift).const_mul _
  have htiltSquare : Integrable (fun sample : Real =>
      samplingRate ^ 2 * (tilt sample * tilt sample))
      (gaussianReal 0 1) :=
    (integrable_gaussianShiftLikelihoodRatio_mul standardizedShift
      standardizedShift).const_mul _
  apply ((hconst.add htilt).add htiltSquare).congr
  filter_upwards with sample
  dsimp [tilt]
  simp only [sparseGaussianLikelihoodRatio, gaussianShiftLikelihoodRatio,
    Pi.add_apply, Pi.pow_apply]
  ring

theorem integrable_sparseGaussianProductLikelihoodRatio_sq
    (horizon : Nat) (samplingRate standardizedShift : Real) :
    Integrable (fun sample =>
      (sparseGaussianProductLikelihoodRatio horizon samplingRate
        standardizedShift sample) ^ 2)
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) := by
  have h := Integrable.fintype_prod (ι := Fin horizon)
    (f := fun _ => fun sample =>
      (sparseGaussianLikelihoodRatio samplingRate standardizedShift sample) ^ 2)
    (μ := fun _ : Fin horizon => gaussianReal 0 1)
    (fun _ => integrable_sparseGaussianLikelihoodRatio_sq samplingRate standardizedShift)
  convert h using 1
  funext sample
  simp only [sparseGaussianProductLikelihoodRatio]
  rw [Finset.prod_pow]

theorem integrableOn_sparseGaussianProductLikelihoodRatio_belowBox
    (horizon : Nat) (samplingRate standardizedShift threshold : Real) :
    IntegrableOn
      (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift)
      (sparseGaussianProductBelowBox horizon threshold)
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) :=
  (integrable_sparseGaussianProductLikelihoodRatio horizon samplingRate
    standardizedShift).integrableOn

theorem integrableOn_sparseGaussianProductLikelihoodRatio_sq_belowBox
    (horizon : Nat) (samplingRate standardizedShift threshold : Real) :
    IntegrableOn (fun sample =>
      (sparseGaussianProductLikelihoodRatio horizon samplingRate
        standardizedShift sample) ^ 2)
      (sparseGaussianProductBelowBox horizon threshold)
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) :=
  (integrable_sparseGaussianProductLikelihoodRatio_sq horizon samplingRate
    standardizedShift).integrableOn

theorem memLp_two_sparseGaussianProductLikelihoodRatio_belowBox
    (horizon : Nat) (samplingRate standardizedShift threshold : Real) :
    MemLp (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift) 2
      (sparseGaussianProductBelowBoxReferenceMeasure horizon threshold) := by
  rw [memLp_two_iff_integrable_sq]
  · exact integrableOn_sparseGaussianProductLikelihoodRatio_sq_belowBox horizon
      samplingRate standardizedShift threshold
  · exact (measurable_sparseGaussianProductLikelihoodRatio horizon samplingRate
      standardizedShift).aestronglyMeasurable

theorem integrable_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox
    (horizon : Nat) (samplingRate standardizedShift threshold coefficient : Real) :
    Integrable (fun sample =>
      (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift sample -
        coefficient) ^ 2)
      (sparseGaussianProductBelowBoxReferenceMeasure horizon threshold) := by
  have hratio := integrableOn_sparseGaussianProductLikelihoodRatio_belowBox horizon
    samplingRate standardizedShift threshold
  have hratioSq := integrableOn_sparseGaussianProductLikelihoodRatio_sq_belowBox horizon
    samplingRate standardizedShift threshold
  rw [show (fun sample =>
      (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift sample -
        coefficient) ^ 2) = fun sample =>
      (sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift sample) ^ 2 -
        2 * coefficient *
          sparseGaussianProductLikelihoodRatio horizon samplingRate standardizedShift sample +
        coefficient ^ 2 by
    funext sample
    ring]
  exact (hratioSq.sub (hratio.const_mul _)).add (integrable_const _)

theorem integral_sparseGaussianLikelihoodRatio_Iic
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold : Real) :
    (∫ sample in Set.Iic threshold,
      sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift sample
      ∂gaussianReal 0 1) =
      (1 - (samplingRate : Real)) * stdNormalCDFReal threshold +
        (samplingRate : Real) * stdNormalCDFReal (threshold - standardizedShift) := by
  have hconst : IntegrableOn (fun _ : Real => 1 - (samplingRate : Real))
      (Set.Iic threshold) (gaussianReal 0 1) := (integrable_const _).integrableOn
  have htilt : IntegrableOn (fun sample : Real =>
      (samplingRate : Real) *
        Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2))
      (Set.Iic threshold) (gaussianReal 0 1) :=
    (integrable_gaussianLikelihoodTilt standardizedShift).integrableOn.const_mul _
  rw [show (fun sample : Real =>
      sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift sample) =
      fun sample => (1 - (samplingRate : Real)) +
        (samplingRate : Real) *
          Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2) by
    funext sample
    simp [sparseGaussianLikelihoodRatio]]
  rw [integral_add hconst htilt, integral_const, integral_const_mul,
    integral_gaussianLikelihoodTilt_Iic]
  have hzero := gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift 0 threshold
  have hzero' : gaussianReal 0 1 (Set.Iic threshold) =
      stdNormalMeasure (Set.Iic threshold) := by simpa using hzero
  simp [Measure.real, Measure.restrict_apply measurableSet_Iic, hzero',
    stdNormalCDFReal_eq_real_measure_Iic]
  ring

theorem integral_sparseGaussianLikelihoodRatio_sq_Iic
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold : Real) :
    (∫ sample in Set.Iic threshold,
      (sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift sample) ^ 2
      ∂gaussianReal 0 1) =
      (1 - (samplingRate : Real)) ^ 2 * stdNormalCDFReal threshold +
        2 * (samplingRate : Real) * (1 - (samplingRate : Real)) *
          stdNormalCDFReal (threshold - standardizedShift) +
        (samplingRate : Real) ^ 2 * Real.exp (standardizedShift ^ 2) *
          stdNormalCDFReal (threshold - 2 * standardizedShift) := by
  let q : Real := samplingRate
  let tilt : Real → Real := fun sample =>
    Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2)
  let tiltSquare : Real → Real := fun sample =>
    Real.exp (2 * standardizedShift * sample - standardizedShift ^ 2)
  have hconst : IntegrableOn (fun _ : Real => (1 - q) ^ 2)
      (Set.Iic threshold) (gaussianReal 0 1) := (integrable_const _).integrableOn
  have htilt : IntegrableOn (fun sample : Real =>
      2 * q * (1 - q) * tilt sample)
      (Set.Iic threshold) (gaussianReal 0 1) :=
    (integrable_gaussianLikelihoodTilt standardizedShift).integrableOn.const_mul _
  have htiltSquare : IntegrableOn (fun sample : Real => q ^ 2 * tiltSquare sample)
      (Set.Iic threshold) (gaussianReal 0 1) :=
    (integrable_gaussianLikelihoodTiltSquare standardizedShift).integrableOn.const_mul _
  have hdecomp :
      (fun sample : Real =>
        (sparseGaussianLikelihoodRatio q standardizedShift sample) ^ 2) =
      fun sample => (1 - q) ^ 2 + 2 * q * (1 - q) * tilt sample +
        q ^ 2 * tiltSquare sample := by
    funext sample
    dsimp [sparseGaussianLikelihoodRatio, tilt, tiltSquare]
    rw [show Real.exp (2 * standardizedShift * sample - standardizedShift ^ 2) =
        (Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2)) ^ 2 by
      calc
        Real.exp (2 * standardizedShift * sample - standardizedShift ^ 2) =
            Real.exp ((standardizedShift * sample - standardizedShift ^ 2 / 2) +
              (standardizedShift * sample - standardizedShift ^ 2 / 2)) := by
                congr 1
                ring
        _ = Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2) *
              Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2) := by
                rw [Real.exp_add]
        _ = (Real.exp (standardizedShift * sample - standardizedShift ^ 2 / 2)) ^ 2 := by
                ring]
    ring
  rw [hdecomp]
  change (∫ sample,
      ((1 - q) ^ 2 + 2 * q * (1 - q) * tilt sample) +
        q ^ 2 * tiltSquare sample ∂(gaussianReal 0 1).restrict (Set.Iic threshold)) = _
  have hsplit :
      (∫ sample in Set.Iic threshold,
        ((1 - q) ^ 2 + 2 * q * (1 - q) * tilt sample) +
          q ^ 2 * tiltSquare sample ∂gaussianReal 0 1) =
        (∫ sample in Set.Iic threshold,
          (1 - q) ^ 2 + 2 * q * (1 - q) * tilt sample ∂gaussianReal 0 1) +
          (∫ sample in Set.Iic threshold,
            q ^ 2 * tiltSquare sample ∂gaussianReal 0 1) := by
    simpa [add_assoc] using
      (integral_add (μ := (gaussianReal 0 1).restrict (Set.Iic threshold))
        (hconst.add htilt) htiltSquare)
  rw [hsplit, integral_add hconst htilt, integral_const, integral_const_mul,
    integral_const_mul]
  rw [integral_gaussianLikelihoodTilt_Iic,
    integral_gaussianLikelihoodTiltSquare_Iic]
  have hzero := gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift 0 threshold
  have hzero' : gaussianReal 0 1 (Set.Iic threshold) =
      stdNormalMeasure (Set.Iic threshold) := by simpa using hzero
  simp [q, Measure.real, Measure.restrict_apply measurableSet_Iic, hzero',
    stdNormalCDFReal_eq_real_measure_Iic]
  ring

theorem integral_sparseGaussianProductLikelihoodRatio_belowBox
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold : Real) :
    (∫ sample in sparseGaussianProductBelowBox horizon threshold,
      sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample
      ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) =
      ((1 - (samplingRate : Real)) * stdNormalCDFReal threshold +
        (samplingRate : Real) *
          stdNormalCDFReal (threshold - standardizedShift)) ^ horizon := by
  change (∫ sample in Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold),
      sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample
      ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) = _
  rw [Measure.restrict_pi_pi]
  change (∫ sample,
      ∏ coordinate,
        sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift
          (sample coordinate)
      ∂Measure.pi (fun _ : Fin horizon =>
        (gaussianReal 0 1).restrict (Set.Iic threshold))) = _
  rw [integral_fintype_prod_eq_prod]
  simp_rw [integral_sparseGaussianLikelihoodRatio_Iic samplingRate hRate
    standardizedShift threshold]
  simp [Finset.prod_const]

theorem integral_sparseGaussianProductLikelihoodRatio_sq_belowBox
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold : Real) :
    (∫ sample in sparseGaussianProductBelowBox horizon threshold,
      (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample) ^ 2
      ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) =
      ((1 - (samplingRate : Real)) ^ 2 * stdNormalCDFReal threshold +
        2 * (samplingRate : Real) * (1 - (samplingRate : Real)) *
          stdNormalCDFReal (threshold - standardizedShift) +
        (samplingRate : Real) ^ 2 * Real.exp (standardizedShift ^ 2) *
          stdNormalCDFReal (threshold - 2 * standardizedShift)) ^ horizon := by
  change (∫ sample in Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold),
      (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample) ^ 2
      ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) = _
  rw [Measure.restrict_pi_pi]
  change (∫ sample,
      (∏ coordinate,
        sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift
          (sample coordinate)) ^ 2
      ∂Measure.pi (fun _ : Fin horizon =>
        (gaussianReal 0 1).restrict (Set.Iic threshold))) = _
  rw [show (fun sample : Fin horizon → Real =>
      (∏ coordinate,
        sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift
          (sample coordinate)) ^ 2) =
      fun sample => ∏ coordinate,
        (sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift
          (sample coordinate)) ^ 2 by
    funext sample
    rw [← Finset.prod_pow]]
  rw [integral_fintype_prod_eq_prod
    (f := fun _ (x : Real) =>
      (sparseGaussianLikelihoodRatio (samplingRate : Real) standardizedShift x) ^ 2)]
  simp_rw [integral_sparseGaussianLikelihoodRatio_sq_Iic samplingRate hRate
    standardizedShift threshold]
  simp [Finset.prod_const]

theorem sparseGaussianProductBelowBoxReferenceMeasure_real_univ
    (horizon : Nat) (threshold : Real) :
    (sparseGaussianProductBelowBoxReferenceMeasure horizon threshold).real Set.univ =
      (stdNormalCDFReal threshold) ^ horizon := by
  unfold sparseGaussianProductBelowBoxReferenceMeasure
  rw [measureReal_def, Measure.restrict_apply MeasurableSet.univ]
  simp only [Set.univ_inter]
  change ((Measure.pi (fun _ : Fin horizon => gaussianReal 0 1))
    (Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold))).toReal = _
  rw [Measure.pi_pi]
  have hcoordinate : gaussianReal 0 1 (Set.Iic threshold) =
      ENNReal.ofReal (stdNormalCDFReal threshold) := by
    rw [show gaussianReal 0 1 (Set.Iic threshold) =
        stdNormalMeasure (Set.Iic threshold) by
      simpa using gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift 0 threshold]
    rw [stdNormalCDFReal_eq_real_measure_Iic]
    exact (ofReal_measureReal (μ := stdNormalMeasure) (s := Set.Iic threshold)
      (by finiteness)).symm
  simp [hcoordinate, ENNReal.toReal_ofReal (stdNormalCDFReal_nonneg threshold)]

theorem integral_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox_eq
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold coefficient : Real) :
    (∫ sample,
      (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample - coefficient) ^ 2
      ∂sparseGaussianProductBelowBoxReferenceMeasure horizon threshold) =
      ((1 - (samplingRate : Real)) ^ 2 * stdNormalCDFReal threshold +
          2 * (samplingRate : Real) * (1 - (samplingRate : Real)) *
            stdNormalCDFReal (threshold - standardizedShift) +
          (samplingRate : Real) ^ 2 * Real.exp (standardizedShift ^ 2) *
            stdNormalCDFReal (threshold - 2 * standardizedShift)) ^ horizon -
        2 * coefficient *
          (((1 - (samplingRate : Real)) * stdNormalCDFReal threshold +
            (samplingRate : Real) *
              stdNormalCDFReal (threshold - standardizedShift)) ^ horizon) +
        coefficient ^ 2 * (stdNormalCDFReal threshold) ^ horizon := by
  letI : IsFiniteMeasure
      (sparseGaussianProductBelowBoxReferenceMeasure horizon threshold) := by
    unfold sparseGaussianProductBelowBoxReferenceMeasure
    infer_instance
  rw [integral_sub_const_sq_eq]
  · have hsecond := integral_sparseGaussianProductLikelihoodRatio_sq_belowBox
      horizon samplingRate hRate standardizedShift threshold
    have hfirst := integral_sparseGaussianProductLikelihoodRatio_belowBox
      horizon samplingRate hRate standardizedShift threshold
    have hmass := sparseGaussianProductBelowBoxReferenceMeasure_real_univ
      horizon threshold
    change (∫ sample,
      (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample) ^ 2
      ∂sparseGaussianProductBelowBoxReferenceMeasure horizon threshold) = _ at hsecond
    change (∫ sample,
      sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift sample
      ∂sparseGaussianProductBelowBoxReferenceMeasure horizon threshold) = _ at hfirst
    rw [hsecond, hfirst, hmass]
  · exact integrableOn_sparseGaussianProductLikelihoodRatio_belowBox horizon
      samplingRate standardizedShift threshold
  · exact integrableOn_sparseGaussianProductLikelihoodRatio_sq_belowBox horizon
      samplingRate standardizedShift threshold

theorem sparseGaussianProductLikelihoodRatio_closedCenteredSquare_nonneg
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold coefficient : Real) :
    0 ≤
      ((1 - (samplingRate : Real)) ^ 2 * stdNormalCDFReal threshold +
          2 * (samplingRate : Real) * (1 - (samplingRate : Real)) *
            stdNormalCDFReal (threshold - standardizedShift) +
          (samplingRate : Real) ^ 2 * Real.exp (standardizedShift ^ 2) *
            stdNormalCDFReal (threshold - 2 * standardizedShift)) ^ horizon -
        2 * coefficient *
          (((1 - (samplingRate : Real)) * stdNormalCDFReal threshold +
            (samplingRate : Real) *
              stdNormalCDFReal (threshold - standardizedShift)) ^ horizon) +
        coefficient ^ 2 * (stdNormalCDFReal threshold) ^ horizon := by
  rw [← integral_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox_eq
    horizon samplingRate hRate standardizedShift threshold coefficient]
  exact integral_sub_const_sq_nonneg _ _ _

end

end Mf.DP
