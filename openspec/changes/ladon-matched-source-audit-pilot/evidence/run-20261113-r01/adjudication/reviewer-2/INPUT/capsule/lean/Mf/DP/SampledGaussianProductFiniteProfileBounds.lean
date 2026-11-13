import Mf.DP.SparseGaussianProductForwardUpperBound
import Mf.DP.SparseGaussianProductMaximumEventLowerBound
import Mf.DP.SparseGaussianProductReverseBounds

/-!
# Finite sampled-Gaussian forward profile bounds

Positive coordinatewise scaling transports the normalized sparse-mixture
bounds to the public sensitivity and noise-standard-deviation parameters.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- Public standard-deviation form of the maximum-event lower witness. -/
theorem sampledGaussianProductForwardProfile_maxEvent_lowerBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        (sensitivity / (noiseStddev : Real)) epsilon threshold ≤
      eventHockeyStickProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
          Measure (Fin horizon → Real)) epsilon := by
  let scaleEquiv := positiveGaussianProductScaleEquiv horizon noiseStddev hStddev
  have hinvariant := eventHockeyStickProfile_map_measurableEquiv scaleEquiv
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
      (noiseStddev ^ 2) : Measure (Fin horizon → Real))
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
      Measure (Fin horizon → Real)) epsilon
  rw [sampledGaussianSourceProductLaw_map_positiveGaussianScale horizon samplingRate hRate
    sensitivity noiseStddev hStddev,
    sampledGaussianReferenceProductLaw_map_positiveGaussianScale horizon noiseStddev hStddev]
      at hinvariant
  exact (sparseGaussianProductMaximumEventForwardLowerBound_le_profile horizon
    samplingRate hRate (sensitivity / (noiseStddev : Real)) epsilon threshold).trans_eq
      hinvariant

/-- Public standard-deviation form of the selected capped restricted
second-moment forward upper bound. -/
theorem sampledGaussianProductForwardProfile_le_cappedRestrictedSecondMomentUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    eventHockeyStickProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
          Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound horizon
        samplingRate (sensitivity / (noiseStddev : Real)) epsilon threshold := by
  let scaleEquiv := positiveGaussianProductScaleEquiv horizon noiseStddev hStddev
  have hinvariant := eventHockeyStickProfile_map_measurableEquiv scaleEquiv
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
      (noiseStddev ^ 2) : Measure (Fin horizon → Real))
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
      Measure (Fin horizon → Real)) epsilon
  rw [sampledGaussianSourceProductLaw_map_positiveGaussianScale horizon samplingRate hRate
    sensitivity noiseStddev hStddev,
    sampledGaussianReferenceProductLaw_map_positiveGaussianScale horizon noiseStddev hStddev]
      at hinvariant
  rw [← hinvariant]
  exact sparseGaussianProductForwardProfile_le_cappedRestrictedSecondMomentUpperBound
    horizon samplingRate hRate (sensitivity / (noiseStddev : Real)) epsilon threshold

/-- Public standard-deviation form of the reverse likelihood-floor bound. -/
theorem sampledGaussianProductReverseProfile_le_likelihoodFloorUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    eventHockeyStickProfile
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
          Measure (Fin horizon → Real))
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductReverseLikelihoodFloorUpperBound horizon samplingRate epsilon := by
  let scaleEquiv := positiveGaussianProductScaleEquiv horizon noiseStddev hStddev
  have hinvariant := eventHockeyStickProfile_map_measurableEquiv scaleEquiv
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
      Measure (Fin horizon → Real))
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
      (noiseStddev ^ 2) : Measure (Fin horizon → Real)) epsilon
  rw [sampledGaussianReferenceProductLaw_map_positiveGaussianScale horizon noiseStddev hStddev,
    sampledGaussianSourceProductLaw_map_positiveGaussianScale horizon samplingRate hRate
      sensitivity noiseStddev hStddev] at hinvariant
  rw [← hinvariant]
  exact sparseGaussianProductReverseProfile_le_likelihoodFloorUpperBound horizon
    samplingRate hRate (sensitivity / (noiseStddev : Real)) epsilon

theorem sampledGaussianProductReverseProfile_le_reciprocalUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    eventHockeyStickProfile
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
          Measure (Fin horizon → Real))
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductReverseReciprocalUpperBound horizon samplingRate
        (sensitivity / (noiseStddev : Real)) epsilon threshold := by
  let scaleEquiv := positiveGaussianProductScaleEquiv horizon noiseStddev hStddev
  have hinvariant := eventHockeyStickProfile_map_measurableEquiv scaleEquiv
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
      Measure (Fin horizon → Real))
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
      (noiseStddev ^ 2) : Measure (Fin horizon → Real)) epsilon
  rw [sampledGaussianReferenceProductLaw_map_positiveGaussianScale horizon noiseStddev hStddev,
    sampledGaussianSourceProductLaw_map_positiveGaussianScale horizon samplingRate hRate
      sensitivity noiseStddev hStddev] at hinvariant
  rw [← hinvariant]
  exact sparseGaussianProductReverseProfile_le_reciprocalUpperBound horizon samplingRate
    hRate (sensitivity / (noiseStddev : Real)) epsilon threshold

theorem sampledGaussianProductReverseProfile_le_bestUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    eventHockeyStickProfile
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
          Measure (Fin horizon → Real))
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductReverseBestUpperBound horizon samplingRate
        (sensitivity / (noiseStddev : Real)) epsilon threshold := by
  apply le_min
  · exact sampledGaussianProductReverseProfile_le_reciprocalUpperBound horizon samplingRate
      hRate sensitivity epsilon threshold noiseStddev hStddev
  · exact sampledGaussianProductReverseProfile_le_likelihoodFloorUpperBound horizon samplingRate
      hRate sensitivity epsilon noiseStddev hStddev

def sampledGaussianProductFiniteProfileUpperBoundWithThresholds
    (horizon : Nat) (samplingRate : NNReal)
    (sensitivity epsilon forwardThreshold reverseThreshold : Real)
    (noiseStddev : NNReal) : ENNReal :=
  max
    (sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound horizon
      samplingRate (sensitivity / (noiseStddev : Real)) epsilon forwardThreshold)
    (sparseGaussianProductReverseBestUpperBound horizon samplingRate
      (sensitivity / (noiseStddev : Real)) epsilon reverseThreshold)

/-- Compatibility form using one threshold for both ordered profile bounds. -/
def sampledGaussianProductFiniteProfileUpperBound
    (horizon : Nat) (samplingRate : NNReal)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal) : ENNReal :=
  sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
    sensitivity epsilon threshold threshold noiseStddev

/-- The maximum-event forward witness is also a lower bound for the two-sided
binary profile. -/
theorem sampledGaussianProductMaximumEventLowerBound_le_binaryProfile
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        (sensitivity / (noiseStddev : Real)) epsilon threshold ≤
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon := by
  exact (sampledGaussianProductForwardProfile_maxEvent_lowerBound horizon samplingRate hRate
    sensitivity epsilon threshold noiseStddev hStddev).trans
      (le_max_left _ _)

/-- Exact finite two-sided sampled-Gaussian profile upper bound with separately
chosen thresholds for the forward and reciprocal-reverse estimates. -/
theorem sampledGaussianProductBinaryProfile_le_finiteProfileUpperBoundWithThresholds
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon forwardThreshold reverseThreshold : Real)
    (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon ≤
      sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
        sensitivity epsilon forwardThreshold reverseThreshold noiseStddev := by
  unfold binaryAccountingProfile
  unfold sampledGaussianProductFiniteProfileUpperBoundWithThresholds
  apply max_le
  · exact
      (sampledGaussianProductForwardProfile_le_cappedRestrictedSecondMomentUpperBound
        horizon samplingRate hRate sensitivity epsilon forwardThreshold noiseStddev
          hStddev).trans
        (le_max_left _ _)
  · exact
      (sampledGaussianProductReverseProfile_le_bestUpperBound horizon samplingRate hRate
        sensitivity epsilon reverseThreshold noiseStddev hStddev).trans
        (le_max_right _ _)

/-- Compatibility form of the exact finite upper bound using one threshold in
both ordered directions. -/
theorem sampledGaussianProductBinaryProfile_le_finiteProfileUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon ≤
      sampledGaussianProductFiniteProfileUpperBound horizon samplingRate
        sensitivity epsilon threshold noiseStddev := by
  exact sampledGaussianProductBinaryProfile_le_finiteProfileUpperBoundWithThresholds
    horizon samplingRate hRate sensitivity epsilon threshold threshold noiseStddev hStddev

end

end Mf.DP
