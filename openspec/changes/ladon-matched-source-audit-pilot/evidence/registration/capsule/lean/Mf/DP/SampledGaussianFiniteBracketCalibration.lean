import Mf.DP.SampledGaussianCalibrationThresholds
import Mf.DP.SampledGaussianProductFiniteProfileBounds

/-!
# Finite-bracket calibration adapters

This owner converts verified lower and upper profile certificates into bounds
on the existing calibrated standard-deviation infimum.  The lower endpoint
uses a strict profile violation.  Its infimum conclusion explicitly retains
feasible-set nonemptiness; the upper endpoint itself supplies that fact and
does not require attainment of the infimum.
-/

open Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- A strict lower profile certificate rules out a candidate noise level. -/
theorem sampledGaussian_candidate_infeasible_of_lower_profile_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (candidate : NNReal)
    (certificate : ENNReal)
    (hLower : ENNReal.ofReal delta < certificate)
    (hProfile : certificate ≤
      sampledGaussianProductProfileStddev horizon samplingRate hRate
        sensitivity candidate epsilon) :
    candidate ∉ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta := by
  intro hFeasible
  have hCandidate := (mem_sampledGaussianFeasibleStddevSet_iff horizon
    samplingRate hRate sensitivity epsilon delta candidate).1 hFeasible
  exact (not_lt_of_ge (hProfile.trans hCandidate)) hLower

/-- An upper profile certificate makes its candidate feasible and hence bounds
the calibrated infimum without an attainment premise. -/
theorem sampledGaussian_calibratedStddev_le_of_upper_profile_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (candidate : NNReal)
    (certificate : ENNReal)
    (hProfile : sampledGaussianProductProfileStddev horizon samplingRate hRate
        sensitivity candidate epsilon ≤ certificate)
    (hUpper : certificate ≤ ENNReal.ofReal delta) :
    sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
      candidate := by
  apply sampledGaussianCalibratedStddev_le_of_feasible horizon samplingRate hRate
    sensitivity epsilon delta candidate
  exact (mem_sampledGaussianFeasibleStddevSet_iff horizon samplingRate hRate
    sensitivity epsilon delta candidate).2 (hProfile.trans hUpper)

/-- An upper profile certificate also supplies the nonemptiness needed for a
lower bound on the totalized infimum. -/
theorem sampledGaussian_feasibleSet_nonempty_of_upper_profile_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (candidate : NNReal)
    (certificate : ENNReal)
    (hProfile : sampledGaussianProductProfileStddev horizon samplingRate hRate
        sensitivity candidate epsilon ≤ certificate)
    (hUpper : certificate ≤ ENNReal.ofReal delta) :
    (sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta).Nonempty := by
  refine ⟨candidate, ?_⟩
  exact (mem_sampledGaussianFeasibleStddevSet_iff horizon samplingRate hRate
    sensitivity epsilon delta candidate).2 (hProfile.trans hUpper)

/-- A strict lower certificate bounds the calibrated infimum when the feasible
set is known to be nonempty. -/
theorem sampledGaussian_lower_bound_of_lower_profile_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (candidate : NNReal)
    (certificate : ENNReal)
    (hLower : ENNReal.ofReal delta < certificate)
    (hProfile : certificate ≤
      sampledGaussianProductProfileStddev horizon samplingRate hRate
        sensitivity candidate epsilon)
    (hNonempty : (sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta).Nonempty) :
    candidate ≤ sampledGaussianCalibratedStddev horizon samplingRate hRate
      sensitivity epsilon delta := by
  exact le_sampledGaussianCalibratedStddev_of_not_feasible horizon samplingRate hRate
    sensitivity epsilon delta candidate hNonempty
    (sampledGaussian_candidate_infeasible_of_lower_profile_certificate horizon
      samplingRate hRate sensitivity epsilon delta candidate certificate hLower hProfile)

/-- Paired profile certificates give a calibration interval without assuming
that the calibrated infimum is attained. -/
theorem sampledGaussian_calibration_interval_of_paired_profile_certificates
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real)
    (lowerCandidate upperCandidate : NNReal)
    (lowerCertificate upperCertificate : ENNReal)
    (hLower : ENNReal.ofReal delta < lowerCertificate)
    (hLowerProfile : lowerCertificate ≤
      sampledGaussianProductProfileStddev horizon samplingRate hRate
        sensitivity lowerCandidate epsilon)
    (hUpperProfile : sampledGaussianProductProfileStddev horizon samplingRate hRate
        sensitivity upperCandidate epsilon ≤ upperCertificate)
    (hUpper : upperCertificate ≤ ENNReal.ofReal delta) :
    lowerCandidate ≤ sampledGaussianCalibratedStddev horizon samplingRate hRate
        sensitivity epsilon delta ∧
      sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
        upperCandidate := by
  have hNonempty := sampledGaussian_feasibleSet_nonempty_of_upper_profile_certificate
    horizon samplingRate hRate sensitivity epsilon delta upperCandidate upperCertificate
    hUpperProfile hUpper
  constructor
  · exact sampledGaussian_lower_bound_of_lower_profile_certificate horizon samplingRate hRate
      sensitivity epsilon delta lowerCandidate lowerCertificate hLower hLowerProfile hNonempty
  · exact sampledGaussian_calibratedStddev_le_of_upper_profile_certificate horizon samplingRate
      hRate sensitivity epsilon delta upperCandidate upperCertificate hUpperProfile hUpper

/-- A supplied maximum-event threshold whose lower expression exceeds the
privacy target certifies that a positive candidate is infeasible. -/
theorem sampledGaussian_candidate_infeasible_of_maximumEvent_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta threshold : Real) (candidate : NNReal)
    (hCandidate : 0 < candidate)
    (hLower : ENNReal.ofReal delta <
      sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        (sensitivity / (candidate : Real)) epsilon threshold) :
    candidate ∉ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta := by
  apply sampledGaussian_candidate_infeasible_of_lower_profile_certificate horizon
    samplingRate hRate sensitivity epsilon delta candidate
    (sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
      (sensitivity / (candidate : Real)) epsilon threshold) hLower
  simpa [sampledGaussianProductProfileStddev] using
    sampledGaussianProductMaximumEventLowerBound_le_binaryProfile horizon samplingRate hRate
      sensitivity epsilon threshold candidate hCandidate

/-- Supplied forward and reciprocal-reverse thresholds whose finite binary
upper expression meets the target certify feasibility and an upper bound on
calibrated noise. -/
theorem sampledGaussian_calibratedStddev_le_of_finiteBracketWithThresholds_upper_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta forwardThreshold reverseThreshold : Real)
    (candidate : NNReal)
    (hCandidate : 0 < candidate)
    (hUpper : sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
      sensitivity epsilon forwardThreshold reverseThreshold candidate ≤ ENNReal.ofReal delta) :
    sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
      candidate := by
  apply sampledGaussian_calibratedStddev_le_of_upper_profile_certificate horizon samplingRate
    hRate sensitivity epsilon delta candidate
    (sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
      sensitivity epsilon forwardThreshold reverseThreshold candidate)
  · simpa [sampledGaussianProductProfileStddev] using
      sampledGaussianProductBinaryProfile_le_finiteProfileUpperBoundWithThresholds horizon
        samplingRate hRate sensitivity epsilon forwardThreshold reverseThreshold candidate
        hCandidate
  · exact hUpper

/-- Compatibility form using one threshold for both ordered upper bounds. -/
theorem sampledGaussian_calibratedStddev_le_of_finiteBracket_upper_certificate
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta threshold : Real) (candidate : NNReal)
    (hCandidate : 0 < candidate)
    (hUpper : sampledGaussianProductFiniteProfileUpperBound horizon samplingRate
      sensitivity epsilon threshold candidate ≤ ENNReal.ofReal delta) :
    sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
      candidate := by
  exact sampledGaussian_calibratedStddev_le_of_finiteBracketWithThresholds_upper_certificate
    horizon samplingRate hRate sensitivity epsilon delta threshold threshold candidate
      hCandidate hUpper

/-- A lower witness threshold and separately optimized forward and reciprocal-
reverse upper thresholds give a certified calibration interval. -/
theorem sampledGaussian_calibration_interval_of_finiteBracketWithThresholds_certificates
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real)
    (lowerThreshold forwardUpperThreshold reverseUpperThreshold : Real)
    (lowerCandidate upperCandidate : NNReal)
    (hLowerCandidate : 0 < lowerCandidate)
    (hUpperCandidate : 0 < upperCandidate)
    (hLower : ENNReal.ofReal delta <
      sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        (sensitivity / (lowerCandidate : Real)) epsilon lowerThreshold)
    (hUpper : sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
      sensitivity epsilon forwardUpperThreshold reverseUpperThreshold upperCandidate ≤
        ENNReal.ofReal delta) :
    lowerCandidate ≤ sampledGaussianCalibratedStddev horizon samplingRate hRate
        sensitivity epsilon delta ∧
      sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
        upperCandidate := by
  have hUpperProfile : sampledGaussianProductProfileStddev horizon samplingRate hRate
      sensitivity upperCandidate epsilon ≤
      sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
        sensitivity epsilon forwardUpperThreshold reverseUpperThreshold upperCandidate := by
    simpa [sampledGaussianProductProfileStddev] using
      sampledGaussianProductBinaryProfile_le_finiteProfileUpperBoundWithThresholds horizon
        samplingRate hRate sensitivity epsilon forwardUpperThreshold reverseUpperThreshold
        upperCandidate hUpperCandidate
  have hNonempty := sampledGaussian_feasibleSet_nonempty_of_upper_profile_certificate horizon
    samplingRate hRate sensitivity epsilon delta upperCandidate
    (sampledGaussianProductFiniteProfileUpperBoundWithThresholds horizon samplingRate
      sensitivity epsilon forwardUpperThreshold reverseUpperThreshold upperCandidate)
      hUpperProfile hUpper
  constructor
  · exact le_sampledGaussianCalibratedStddev_of_not_feasible horizon samplingRate hRate
      sensitivity epsilon delta lowerCandidate hNonempty
      (sampledGaussian_candidate_infeasible_of_maximumEvent_certificate horizon samplingRate
        hRate sensitivity epsilon delta lowerThreshold lowerCandidate hLowerCandidate hLower)
  · exact
      sampledGaussian_calibratedStddev_le_of_finiteBracketWithThresholds_upper_certificate
        horizon samplingRate hRate sensitivity epsilon delta forwardUpperThreshold
          reverseUpperThreshold upperCandidate hUpperCandidate hUpper

/-- Compatibility form using one threshold for both ordered upper estimates. -/
theorem sampledGaussian_calibration_interval_of_finiteBracket_certificates
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real)
    (lowerThreshold upperThreshold : Real)
    (lowerCandidate upperCandidate : NNReal)
    (hLowerCandidate : 0 < lowerCandidate)
    (hUpperCandidate : 0 < upperCandidate)
    (hLower : ENNReal.ofReal delta <
      sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        (sensitivity / (lowerCandidate : Real)) epsilon lowerThreshold)
    (hUpper : sampledGaussianProductFiniteProfileUpperBound horizon samplingRate
      sensitivity epsilon upperThreshold upperCandidate ≤ ENNReal.ofReal delta) :
    lowerCandidate ≤ sampledGaussianCalibratedStddev horizon samplingRate hRate
        sensitivity epsilon delta ∧
      sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
        upperCandidate := by
  exact sampledGaussian_calibration_interval_of_finiteBracketWithThresholds_certificates
    horizon samplingRate hRate sensitivity epsilon delta lowerThreshold upperThreshold
      upperThreshold lowerCandidate upperCandidate hLowerCandidate hUpperCandidate hLower hUpper

end

end Mf.DP
