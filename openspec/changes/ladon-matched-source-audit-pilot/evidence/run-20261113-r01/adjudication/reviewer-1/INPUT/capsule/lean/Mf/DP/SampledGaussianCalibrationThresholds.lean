import Mf.DP.FullBatchGaussianAccounting
import Mf.DP.SampledGaussianProductNoiseMonotonicity

/-!
# Threshold lemmas for sampled Gaussian calibration

This module supplies the order-theoretic API for the calibrated standard-deviation
infimum and the fixed-factor Gaussian comparison points used by the asymptotic
bracketing argument.  It makes no sampled-profile continuity or attainment claim.
-/

open Set

namespace Mf.DP

noncomputable section

/-- Exact profile of the matched Gaussian source against the unchanged reference. -/
def matchedGaussianProductProfileStddev
    (horizon : Nat) (samplingRate : NNReal) (sensitivity : Real)
    (noiseStddev : NNReal) (epsilon : Real) : ENNReal :=
  binaryAccountingProfile
    (matchedGaussianSourceProductLaw horizon samplingRate sensitivity (noiseStddev ^ 2))
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon

/-- The matched product profile is the scalar Gaussian profile with signal `q Δ √T`. -/
theorem matchedGaussianProductProfileStddev_eq_scalar
    (horizon : Nat) (samplingRate : NNReal) (sensitivity : Real)
    (noiseStddev : NNReal) (epsilon : Real)
    (horizon_pos : 0 < horizon) (rate_pos : 0 < samplingRate)
    (sensitivity_pos : 0 < sensitivity) (noise_pos : 0 < noiseStddev) :
    matchedGaussianProductProfileStddev horizon samplingRate sensitivity
        noiseStddev epsilon =
      ENNReal.ofReal (Training.scalarGaussianSigmaProfile
        ((samplingRate : Real) * fullBatchGaussianSignal horizon sensitivity)
        epsilon noiseStddev) := by
  unfold matchedGaussianProductProfileStddev matchedGaussianSourceProductLaw
    matchedGaussianOneStepSourceLaw sampledGaussianReferenceProductLaw
  change binaryAccountingProfile
      ⟨bsrGaussianMeasure (noiseStddev : Real)
        (fun _ : Fin horizon => (samplingRate : Real) * sensitivity), by infer_instance⟩
      ⟨bsrGaussianMeasure (noiseStddev : Real)
        (fun _ : Fin horizon => 0), by infer_instance⟩ epsilon = _
  rw [bsrConstantGaussianBinaryProfile_eq_scalar horizon
    ((samplingRate : Real) * sensitivity) noiseStddev epsilon horizon_pos
    (mul_pos (by exact_mod_cast rate_pos) sensitivity_pos) (by exact_mod_cast noise_pos)]
  simp only [fullBatchGaussianSignal]
  ring_nf

/-- Feasible standard deviations remain feasible when the noise is increased. -/
theorem sampledGaussianFeasibleStddevSet_upward_closed
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) {small large : NNReal}
    (hsmall : small ∈ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta) (hStddev : small ≤ large) :
    large ∈ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta := by
  exact (sampledGaussianProductProfileStddev_antitone horizon samplingRate hRate
    sensitivity epsilon hStddev).trans hsmall

/-- Every feasible candidate is an upper bound on the calibrated infimum. -/
theorem sampledGaussianCalibratedStddev_le_of_feasible
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (candidate : NNReal)
    (hCandidate : candidate ∈ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta) :
    sampledGaussianCalibratedStddev horizon samplingRate hRate sensitivity epsilon delta ≤
      candidate := by
  apply csInf_le
  · exact ⟨0, fun _ _ => bot_le⟩
  · exact hCandidate

/-- An infeasible candidate lies below the calibrated infimum once feasibility is nonempty. -/
theorem le_sampledGaussianCalibratedStddev_of_not_feasible
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (candidate : NNReal)
    (hNonempty : (sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta).Nonempty)
    (hCandidate : candidate ∉ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
      sensitivity epsilon delta) :
    candidate ≤ sampledGaussianCalibratedStddev horizon samplingRate hRate
      sensitivity epsilon delta := by
  unfold sampledGaussianCalibratedStddev
  apply le_csInf hNonempty
  intro feasible hFeasible
  by_contra hnot
  have hlt : feasible < candidate := lt_of_not_ge hnot
  exact hCandidate (sampledGaussianFeasibleStddevSet_upward_closed horizon samplingRate hRate
    sensitivity epsilon delta hFeasible hlt.le)

/-- Lower fixed-factor candidate `(1-η) q g_T`, in standard-deviation units. -/
def sampledGaussianLowerCalibrationCandidate
    (horizon : Nat) (samplingRate eta : NNReal)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) : NNReal :=
  (1 - eta) * samplingRate *
    fullBatchGaussianCalibratedStddev horizon sensitivity epsilon delta
      sensitivity_pos epsilon_nonneg delta_pos delta_lt_one

/-- Upper fixed-factor candidate `(1+η) q g_T`, in standard-deviation units. -/
def sampledGaussianUpperCalibrationCandidate
    (horizon : Nat) (samplingRate eta : NNReal)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) : NNReal :=
  (1 + eta) * samplingRate *
    fullBatchGaussianCalibratedStddev horizon sensitivity epsilon delta
      sensitivity_pos epsilon_nonneg delta_pos delta_lt_one

/-- Reducing a positive calibrated Gaussian scale by a factor `1-η` creates a fixed gap
above the target profile. -/
theorem scalarGaussianProfile_lowerCandidate_strictGap
    {signal epsilon delta eta kappa : Real}
    (signal_pos : 0 < signal) (eta_pos : 0 < eta) (eta_lt_one : eta < 1)
    (kappa_pos : 0 < kappa)
    (kappa_spec : Training.scalarGaussianSigmaProfile signal epsilon kappa = delta) :
    delta < Training.scalarGaussianSigmaProfile signal epsilon ((1 - eta) * kappa) := by
  have hScaled : 0 < (1 - eta) * kappa := mul_pos (sub_pos.mpr eta_lt_one) kappa_pos
  have hLess : (1 - eta) * kappa < kappa := by nlinarith
  have hStrict := Training.strictAntiOn_scalarGaussianSigmaProfile_pos
    signal_pos epsilon hScaled kappa_pos hLess
  simpa [kappa_spec] using hStrict

/-- Increasing a positive calibrated Gaussian scale by a factor `1+η` creates a fixed gap
below the target profile. -/
theorem scalarGaussianProfile_upperCandidate_strictGap
    {signal epsilon delta eta kappa : Real}
    (signal_pos : 0 < signal) (eta_pos : 0 < eta) (kappa_pos : 0 < kappa)
    (kappa_spec : Training.scalarGaussianSigmaProfile signal epsilon kappa = delta) :
    Training.scalarGaussianSigmaProfile signal epsilon ((1 + eta) * kappa) < delta := by
  have hScaled : 0 < (1 + eta) * kappa := mul_pos (by linarith) kappa_pos
  have hLess : kappa < (1 + eta) * kappa := by nlinarith
  have hStrict := Training.strictAntiOn_scalarGaussianSigmaProfile_pos
    signal_pos epsilon kappa_pos hScaled hLess
  simpa [kappa_spec] using hStrict

/-- The lower matched-Gaussian candidate has a horizon-independent scalar profile. -/
theorem matchedGaussianProductProfile_lowerCandidate_eq_fixed
    (horizon : Nat) (samplingRate eta : NNReal)
    (sensitivity epsilon delta : Real)
    (horizon_pos : 0 < horizon) (rate_pos : 0 < samplingRate)
    (eta_lt_one : eta < 1) (sensitivity_pos : 0 < sensitivity)
    (epsilon_nonneg : 0 ≤ epsilon) (delta_pos : 0 < delta)
    (delta_lt_one : delta < 1) :
    matchedGaussianProductProfileStddev horizon samplingRate sensitivity
        (sampledGaussianLowerCalibrationCandidate horizon samplingRate eta
          sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one)
        epsilon =
      ENNReal.ofReal (Training.scalarGaussianSigmaProfile sensitivity epsilon
        ((1 - (eta : Real)) * fullBatchGaussianBaseStddev sensitivity epsilon delta
          sensitivity_pos epsilon_nonneg delta_pos delta_lt_one)) := by
  let base := fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
    epsilon_nonneg delta_pos delta_lt_one
  have hbase : 0 < base :=
    (Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
      delta_pos delta_lt_one).1
  have hsqrt : 0 < Real.sqrt (horizon : Real) :=
    Real.sqrt_pos.2 (by exact_mod_cast horizon_pos)
  have hetaReal : (eta : Real) < 1 := by exact_mod_cast eta_lt_one
  have hnoise : 0 < sampledGaussianLowerCalibrationCandidate horizon samplingRate eta
      sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one := by
    apply mul_pos
    · exact mul_pos (tsub_pos_iff_lt.mpr eta_lt_one) rate_pos
    · exact_mod_cast mul_pos hbase hsqrt
  rw [matchedGaussianProductProfileStddev_eq_scalar horizon samplingRate sensitivity _
    epsilon horizon_pos rate_pos sensitivity_pos hnoise]
  apply congrArg ENNReal.ofReal
  unfold Training.scalarGaussianSigmaProfile
  apply congrArg (fun ratio => gdpProfile ratio epsilon)
  simp only [sampledGaussianLowerCalibrationCandidate,
    fullBatchGaussianCalibratedStddev_coe, NNReal.coe_mul,
    NNReal.coe_sub eta_lt_one.le]
  simp only [fullBatchGaussianSignal]
  field_simp [ne_of_gt (by exact_mod_cast rate_pos : (0 : Real) < samplingRate),
    ne_of_gt hsqrt, ne_of_gt hbase, ne_of_gt (sub_pos.mpr hetaReal)]
  <;> norm_num <;> ring

/-- The upper matched-Gaussian candidate has a horizon-independent scalar profile. -/
theorem matchedGaussianProductProfile_upperCandidate_eq_fixed
    (horizon : Nat) (samplingRate eta : NNReal)
    (sensitivity epsilon delta : Real)
    (horizon_pos : 0 < horizon) (rate_pos : 0 < samplingRate)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    matchedGaussianProductProfileStddev horizon samplingRate sensitivity
        (sampledGaussianUpperCalibrationCandidate horizon samplingRate eta
          sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one)
        epsilon =
      ENNReal.ofReal (Training.scalarGaussianSigmaProfile sensitivity epsilon
        ((1 + (eta : Real)) * fullBatchGaussianBaseStddev sensitivity epsilon delta
          sensitivity_pos epsilon_nonneg delta_pos delta_lt_one)) := by
  let base := fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
    epsilon_nonneg delta_pos delta_lt_one
  have hbase : 0 < base :=
    (Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
      delta_pos delta_lt_one).1
  have hsqrt : 0 < Real.sqrt (horizon : Real) :=
    Real.sqrt_pos.2 (by exact_mod_cast horizon_pos)
  have hnoise : 0 < sampledGaussianUpperCalibrationCandidate horizon samplingRate eta
      sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one := by
    apply mul_pos
    · exact mul_pos (by positivity) rate_pos
    · exact_mod_cast mul_pos hbase hsqrt
  rw [matchedGaussianProductProfileStddev_eq_scalar horizon samplingRate sensitivity _
    epsilon horizon_pos rate_pos sensitivity_pos hnoise]
  apply congrArg ENNReal.ofReal
  unfold Training.scalarGaussianSigmaProfile
  apply congrArg (fun ratio => gdpProfile ratio epsilon)
  simp only [sampledGaussianUpperCalibrationCandidate,
    fullBatchGaussianCalibratedStddev_coe, NNReal.coe_mul, NNReal.coe_add]
  simp only [fullBatchGaussianSignal]
  field_simp [ne_of_gt (by exact_mod_cast rate_pos : (0 : Real) < samplingRate),
    ne_of_gt hsqrt, ne_of_gt hbase]
  <;> norm_num

/-- The lower matched candidate is separated from the target by a strict fixed gap. -/
theorem matchedGaussianProductProfile_lowerCandidate_gt_delta
    (horizon : Nat) (samplingRate eta : NNReal)
    (sensitivity epsilon delta : Real)
    (horizon_pos : 0 < horizon) (rate_pos : 0 < samplingRate)
    (eta_pos : 0 < eta) (eta_lt_one : eta < 1)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    ENNReal.ofReal delta <
      matchedGaussianProductProfileStddev horizon samplingRate sensitivity
        (sampledGaussianLowerCalibrationCandidate horizon samplingRate eta
          sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one)
        epsilon := by
  rw [matchedGaussianProductProfile_lowerCandidate_eq_fixed horizon samplingRate eta
    sensitivity epsilon delta horizon_pos rate_pos eta_lt_one sensitivity_pos
    epsilon_nonneg delta_pos delta_lt_one]
  let base := fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
    epsilon_nonneg delta_pos delta_lt_one
  have hspec := Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
    delta_pos delta_lt_one
  have hgap := scalarGaussianProfile_lowerCandidate_strictGap sensitivity_pos
    (by exact_mod_cast eta_pos) (by exact_mod_cast eta_lt_one) hspec.1 hspec.2
  exact (ENNReal.ofReal_lt_ofReal_iff (delta_pos.trans hgap)).2 hgap

/-- The upper matched candidate is separated from the target by a strict fixed gap. -/
theorem matchedGaussianProductProfile_upperCandidate_lt_delta
    (horizon : Nat) (samplingRate eta : NNReal)
    (sensitivity epsilon delta : Real)
    (horizon_pos : 0 < horizon) (rate_pos : 0 < samplingRate)
    (eta_pos : 0 < eta) (sensitivity_pos : 0 < sensitivity)
    (epsilon_nonneg : 0 ≤ epsilon) (delta_pos : 0 < delta)
    (delta_lt_one : delta < 1) :
    matchedGaussianProductProfileStddev horizon samplingRate sensitivity
        (sampledGaussianUpperCalibrationCandidate horizon samplingRate eta
          sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one)
        epsilon < ENNReal.ofReal delta := by
  rw [matchedGaussianProductProfile_upperCandidate_eq_fixed horizon samplingRate eta
    sensitivity epsilon delta horizon_pos rate_pos sensitivity_pos epsilon_nonneg
    delta_pos delta_lt_one]
  have hspec := Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
    delta_pos delta_lt_one
  have hgap := scalarGaussianProfile_upperCandidate_strictGap sensitivity_pos
    (by exact_mod_cast eta_pos) hspec.1 hspec.2
  exact (ENNReal.ofReal_lt_ofReal_iff delta_pos).2 hgap

end

end Mf.DP
