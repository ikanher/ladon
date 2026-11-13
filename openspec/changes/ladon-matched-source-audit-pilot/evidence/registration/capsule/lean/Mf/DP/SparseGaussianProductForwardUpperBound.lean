import Mf.DP.FiniteProfileRestrictedSecondMomentUpperBound
import Mf.DP.SparseGaussianTruncatedLikelihoodMoments

/-!
# Restricted second-moment upper bounds for sparse Gaussian products

The closed form retains the reference below-box mass in both the centered
square and the Cauchy--Schwarz factor.  It therefore avoids the artificial
outside-box penalty caused by zero-extending the truncated likelihood.
-/

open MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

def sparseGaussianProductBelowBoxReferenceMass
    (horizon : Nat) (threshold : Real) : Real :=
  (stdNormalCDFReal threshold) ^ horizon

def sparseGaussianProductBelowBoxFirstMoment
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift threshold : Real) : Real :=
  ((1 - (samplingRate : Real)) * stdNormalCDFReal threshold +
    (samplingRate : Real) *
      stdNormalCDFReal (threshold - standardizedShift)) ^ horizon

def sparseGaussianProductBelowBoxSecondMoment
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift threshold : Real) : Real :=
  ((1 - (samplingRate : Real)) ^ 2 * stdNormalCDFReal threshold +
    2 * (samplingRate : Real) * (1 - (samplingRate : Real)) *
      stdNormalCDFReal (threshold - standardizedShift) +
    (samplingRate : Real) ^ 2 * Real.exp (standardizedShift ^ 2) *
      stdNormalCDFReal (threshold - 2 * standardizedShift)) ^ horizon

def sparseGaussianProductBelowBoxCenteredSecondMoment
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift threshold coefficient : Real) : Real :=
  sparseGaussianProductBelowBoxSecondMoment horizon samplingRate standardizedShift threshold -
    2 * coefficient *
      sparseGaussianProductBelowBoxFirstMoment horizon samplingRate standardizedShift threshold +
    coefficient ^ 2 * sparseGaussianProductBelowBoxReferenceMass horizon threshold

def sparseGaussianProductRestrictedSecondMomentResidual
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift threshold coefficient : Real) : Real :=
  (Real.sqrt
      (sparseGaussianProductBelowBoxReferenceMass horizon threshold *
        sparseGaussianProductBelowBoxCenteredSecondMoment horizon samplingRate
          standardizedShift threshold coefficient) +
    sparseGaussianProductBelowBoxFirstMoment horizon samplingRate standardizedShift threshold -
      coefficient * sparseGaussianProductBelowBoxReferenceMass horizon threshold) / 2

/-- The real forward upper formula before the optional residual mass cap. -/
def sparseGaussianProductForwardRestrictedSecondMomentUpperBoundReal
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift epsilon threshold : Real) : Real :=
  1 - sparseGaussianProductBelowBoxFirstMoment horizon samplingRate
      standardizedShift threshold +
    sparseGaussianProductRestrictedSecondMomentResidual horizon samplingRate
      standardizedShift threshold (Real.exp epsilon)

def sparseGaussianProductForwardRestrictedSecondMomentUpperBound
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift epsilon threshold : Real) : ENNReal :=
  ENNReal.ofReal
    (sparseGaussianProductForwardRestrictedSecondMomentUpperBoundReal horizon
      samplingRate standardizedShift epsilon threshold)

/-- The selected numerical-facing upper formula caps the below-box residual by
the complete below-box source mass. -/
def sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBoundReal
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift epsilon threshold : Real) : Real :=
  1 - sparseGaussianProductBelowBoxFirstMoment horizon samplingRate
      standardizedShift threshold +
    min (sparseGaussianProductBelowBoxFirstMoment horizon samplingRate
      standardizedShift threshold)
      (sparseGaussianProductRestrictedSecondMomentResidual horizon samplingRate
        standardizedShift threshold (Real.exp epsilon))

def sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift epsilon threshold : Real) : ENNReal :=
  ENNReal.ofReal
    (sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBoundReal horizon
      samplingRate standardizedShift epsilon threshold)

theorem sparseGaussianProductBelowBoxCenteredSecondMoment_nonneg
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold coefficient : Real) :
    0 ≤ sparseGaussianProductBelowBoxCenteredSecondMoment horizon samplingRate
      standardizedShift threshold coefficient := by
  exact sparseGaussianProductLikelihoodRatio_closedCenteredSquare_nonneg
    horizon samplingRate hRate standardizedShift threshold coefficient

/-- The normalized forward profile is bounded by the restricted below-box
second-moment formula for every threshold. -/
theorem sparseGaussianProductForwardProfile_le_restrictedSecondMomentUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) :
    eventHockeyStickProfile
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real))
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductForwardRestrictedSecondMomentUpperBound horizon samplingRate
        standardizedShift epsilon threshold := by
  change eventHockeyStickProfile
      (Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)))
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) epsilon ≤ _
  rw [sparseGaussianProductLaw_eq_withDensity horizon samplingRate hRate
    standardizedShift]
  let reference : ProbabilityMeasure (Fin horizon → Real) :=
    ⟨Measure.pi (fun _ : Fin horizon => gaussianReal 0 1), by infer_instance⟩
  have hbound := eventHockeyStickProfile_withDensity_forward_le_restrictedSecondMoment
    reference
    (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real) standardizedShift)
    (measurable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
    (fun sample => (sparseGaussianProductLikelihoodRatio_pos horizon samplingRate hRate
      standardizedShift sample).le)
    (integrable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
    (sparseGaussianProductBelowBox horizon threshold)
    (measurableSet_sparseGaussianProductBelowBox horizon threshold)
    epsilon
    (integrable_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox horizon
      samplingRate standardizedShift threshold (Real.exp epsilon))
  have hreference : (reference : Measure (Fin horizon → Real)) =
      Measure.pi (fun _ : Fin horizon => gaussianReal 0 1) := rfl
  rw [hreference] at hbound
  unfold sparseGaussianProductForwardRestrictedSecondMomentUpperBound
  unfold sparseGaussianProductForwardRestrictedSecondMomentUpperBoundReal
  unfold sparseGaussianProductRestrictedSecondMomentResidual
  have hcomplement := setIntegral_compl
    (measurableSet_sparseGaussianProductBelowBox horizon threshold)
    (integrable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
  rw [integral_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
    standardizedShift] at hcomplement
  rw [hcomplement] at hbound
  rw [integral_sparseGaussianProductLikelihoodRatio_belowBox horizon samplingRate hRate
    standardizedShift threshold] at hbound
  have hcentered :=
    integral_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox_eq horizon
      samplingRate hRate standardizedShift threshold (Real.exp epsilon)
  unfold sparseGaussianProductBelowBoxReferenceMeasure at hcentered
  rw [hcentered] at hbound
  have hmass := sparseGaussianProductBelowBoxReferenceMeasure_real_univ horizon threshold
  unfold sparseGaussianProductBelowBoxReferenceMeasure at hmass
  rw [hmass] at hbound
  simpa [sparseGaussianProductBelowBoxReferenceMass,
    sparseGaussianProductBelowBoxFirstMoment,
    sparseGaussianProductBelowBoxSecondMoment,
    sparseGaussianProductBelowBoxCenteredSecondMoment,
    standardGaussianProductLaw] using hbound

/-- The normalized forward profile obeys the selected mass-capped bound. -/
theorem sparseGaussianProductForwardProfile_le_cappedRestrictedSecondMomentUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) :
    eventHockeyStickProfile
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real))
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound horizon
        samplingRate standardizedShift epsilon threshold := by
  change eventHockeyStickProfile
      (Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)))
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) epsilon ≤ _
  rw [sparseGaussianProductLaw_eq_withDensity horizon samplingRate hRate
    standardizedShift]
  let reference : ProbabilityMeasure (Fin horizon → Real) :=
    ⟨Measure.pi (fun _ : Fin horizon => gaussianReal 0 1), by infer_instance⟩
  have hbound :=
    eventHockeyStickProfile_withDensity_forward_le_restrictedSecondMomentCapped
      reference
      (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift)
      (measurable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift)
      (fun sample => (sparseGaussianProductLikelihoodRatio_pos horizon samplingRate hRate
        standardizedShift sample).le)
      (integrable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
        standardizedShift)
      (sparseGaussianProductBelowBox horizon threshold)
      (measurableSet_sparseGaussianProductBelowBox horizon threshold)
      epsilon
      (integrable_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox horizon
        samplingRate standardizedShift threshold (Real.exp epsilon))
  have hreference : (reference : Measure (Fin horizon → Real)) =
      Measure.pi (fun _ : Fin horizon => gaussianReal 0 1) := rfl
  rw [hreference] at hbound
  unfold sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound
  unfold sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBoundReal
  unfold sparseGaussianProductRestrictedSecondMomentResidual
  have hcomplement := setIntegral_compl
    (measurableSet_sparseGaussianProductBelowBox horizon threshold)
    (integrable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
  rw [integral_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
    standardizedShift] at hcomplement
  rw [hcomplement] at hbound
  rw [integral_sparseGaussianProductLikelihoodRatio_belowBox horizon samplingRate hRate
    standardizedShift threshold] at hbound
  have hcentered :=
    integral_sparseGaussianProductLikelihoodRatio_sub_const_sq_belowBox_eq horizon
      samplingRate hRate standardizedShift threshold (Real.exp epsilon)
  unfold sparseGaussianProductBelowBoxReferenceMeasure at hcentered
  rw [hcentered] at hbound
  have hmass := sparseGaussianProductBelowBoxReferenceMeasure_real_univ horizon threshold
  unfold sparseGaussianProductBelowBoxReferenceMeasure at hmass
  rw [hmass] at hbound
  simpa [sparseGaussianProductBelowBoxReferenceMass,
    sparseGaussianProductBelowBoxFirstMoment,
    sparseGaussianProductBelowBoxSecondMoment,
    sparseGaussianProductBelowBoxCenteredSecondMoment,
    standardGaussianProductLaw] using hbound

end

end Mf.DP
