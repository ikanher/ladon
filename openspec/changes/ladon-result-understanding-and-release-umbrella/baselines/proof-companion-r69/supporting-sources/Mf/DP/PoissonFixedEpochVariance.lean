import Mf.DP.PoissonFixedEpochRate
import Mf.DP.SampledGaussianCalibrationRatio
import Mf.DP.FixedParticipationGradientVariance
import Mf.DP.FixedParticipationGradientUtility

/-!
# Frozen-coordinate variance on the Poisson fixed-epoch path

This module packages the exact calibrated sampled-Gaussian standard deviation
and the frozen-coordinate horizon-average variance at an admissible point
`T ≥ E`, `q = E/T`.  It is an algebraic utility surface for independent frozen
gradient estimates, not an adaptive optimizer or final-iterate theorem.
-/

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- Exact sampled-Gaussian calibrated raw standard deviation at one discrete
fixed-epoch point. -/
def poissonFixedEpochCalibratedStddev
    (point : PoissonFixedEpochPoint)
    (sensitivity epsilon delta : Real) : NNReal :=
  sampledGaussianCalibratedStddev point.horizon point.samplingRate
    point.samplingRate_le_one sensitivity epsilon delta

/-- Epoch-normalized privacy-noise component with a supplied raw standard
deviation. -/
def poissonFixedEpochPrivacyVarianceOfStddev
    (point : PoissonFixedEpochPoint) (noiseStddev : Real) : Real :=
  (point.horizon : Real) / (point.epoch : Real) ^ 2 * noiseStddev ^ 2

/-- Frozen-gradient sampling component of the horizon average. -/
def poissonFixedEpochSamplingVariance
    (point : PoissonFixedEpochPoint) (energy : Real) : Real :=
  ((point.horizon : Real) - (point.epoch : Real)) /
      ((point.epoch : Real) * (point.horizon : Real)) * energy

/-- Fixed-epoch total horizon-average variance with a supplied raw standard
deviation. -/
def poissonFixedEpochTotalAverageVarianceOfStddev
    (point : PoissonFixedEpochPoint) (energy noiseStddev : Real) : Real :=
  poissonFixedEpochSamplingVariance point energy +
    poissonFixedEpochPrivacyVarianceOfStddev point noiseStddev

/-- Exact calibrated fixed-epoch total horizon-average variance. -/
def poissonFixedEpochTotalAverageVariance
    (point : PoissonFixedEpochPoint)
    (sensitivity epsilon delta energy : Real) : Real :=
  poissonFixedEpochTotalAverageVarianceOfStddev point energy
    (poissonFixedEpochCalibratedStddev point sensitivity epsilon delta : Real)

theorem poissonFixedEpochSamplingVariance_nonneg
    (point : PoissonFixedEpochPoint) (energy : Real) (energy_nonneg : 0 ≤ energy) :
    0 ≤ poissonFixedEpochSamplingVariance point energy := by
  unfold poissonFixedEpochSamplingVariance
  have epoch_nonneg : 0 ≤ (point.epoch : Real) := by positivity
  have horizon_nonneg : 0 ≤ (point.horizon : Real) := by positivity
  have epoch_le_horizon : (point.epoch : Real) ≤ point.horizon := by
    exact_mod_cast point.epoch_le_horizon
  positivity

/-- The privacy component is the existing fixed-participation component after
using the exact identity `T q = E`. -/
theorem poissonFixedEpochPrivacyVarianceOfStddev_eq_fixedParticipation
    (point : PoissonFixedEpochPoint) (noiseStddev : Real) :
    poissonFixedEpochPrivacyVarianceOfStddev point noiseStddev =
      fixedParticipationPrivacyVarianceComponent (point.epoch : Real)
        point.samplingRate noiseStddev := by
  unfold poissonFixedEpochPrivacyVarianceOfStddev
    fixedParticipationPrivacyVarianceComponent
  have epoch_ne : (point.epoch : Real) ≠ 0 := by
    exact_mod_cast point.epoch_pos.ne'
  have horizon_ne : (point.horizon : Real) ≠ 0 := by
    exact_mod_cast point.horizon_pos.ne'
  have rate_ne : (point.samplingRate : Real) ≠ 0 := by
    exact_mod_cast point.samplingRate_pos.ne'
  have budget := point.horizon_mul_samplingRate
  field_simp
  nlinarith

/-- Exact connection to the one-step normalized variance divided by the
positive horizon. -/
theorem poissonFixedEpoch_averageVariance_eq
    (point : PoissonFixedEpochPoint) (energy noiseStddev : Real) :
    ((((1 - (point.samplingRate : Real)) / point.samplingRate) * energy +
          (noiseStddev / point.samplingRate) ^ 2) /
        point.horizon) =
      poissonFixedEpochTotalAverageVarianceOfStddev point energy noiseStddev := by
  unfold poissonFixedEpochTotalAverageVarianceOfStddev
  rw [poissonFixedEpochPrivacyVarianceOfStddev_eq_fixedParticipation]
  rw [fixedParticipation_averageVariance_eq point.horizon_pos
    (by exact_mod_cast point.samplingRate_pos)
    point.horizon_mul_samplingRate]
  congr 1
  unfold poissonFixedEpochSamplingVariance
  have epoch_ne : (point.epoch : Real) ≠ 0 := by
    exact_mod_cast point.epoch_pos.ne'
  have horizon_ne : (point.horizon : Real) ≠ 0 := by
    exact_mod_cast point.horizon_pos.ne'
  field_simp
  calc
    (1 - (point.samplingRate : Real)) * energy * point.horizon =
        energy * ((point.horizon : Real) -
          point.horizon * point.samplingRate) := by ring
    _ = energy * ((point.horizon : Real) - point.epoch) := by
      rw [point.horizon_mul_samplingRate]

/-- At the endpoint the public sampled calibration is exactly the explicit
full-batch square-root calibration. -/
theorem poissonFixedEpochCalibratedStddev_fullBatch
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    poissonFixedEpochCalibratedStddev
        (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
        sensitivity epsilon delta =
      fullBatchGaussianCalibratedStddev epoch sensitivity epsilon delta
        sensitivity_pos epsilon_nonneg delta_pos delta_lt_one := by
  unfold poissonFixedEpochCalibratedStddev
  simpa only [PoissonFixedEpochPoint.horizon_fullBatch,
    PoissonFixedEpochPoint.samplingRate_fullBatch] using
    sampledGaussianCalibratedStddev_one_eq_fullBatch epoch sensitivity epsilon delta
      epoch_pos sensitivity_pos epsilon_nonneg delta_pos delta_lt_one

@[simp] theorem poissonFixedEpochSamplingVariance_fullBatch
    (epoch : Nat) (epoch_pos : 0 < epoch) (energy : Real) :
    poissonFixedEpochSamplingVariance
        (PoissonFixedEpochPoint.fullBatch epoch epoch_pos) energy = 0 := by
  simp [poissonFixedEpochSamplingVariance, PoissonFixedEpochPoint.fullBatch]

/-- The full-batch endpoint privacy component is the square of the one-step
Gaussian base calibration. -/
theorem poissonFixedEpochPrivacyVariance_fullBatch_eq_base_sq
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    poissonFixedEpochPrivacyVarianceOfStddev
        (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
        (poissonFixedEpochCalibratedStddev
          (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
          sensitivity epsilon delta) =
      (fullBatchGaussianBaseStddev sensitivity epsilon delta
        sensitivity_pos epsilon_nonneg delta_pos delta_lt_one) ^ 2 := by
  rw [poissonFixedEpochCalibratedStddev_fullBatch epoch epoch_pos sensitivity epsilon
    delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one]
  unfold poissonFixedEpochPrivacyVarianceOfStddev
  rw [fullBatchGaussianCalibratedStddev_coe]
  simp only [PoissonFixedEpochPoint.fullBatch]
  have epoch_real_pos : 0 < (epoch : Real) := by exact_mod_cast epoch_pos
  rw [mul_pow, Real.sq_sqrt (le_of_lt epoch_real_pos)]
  field_simp [ne_of_gt epoch_real_pos]

/-- The exact total frozen-coordinate variance at full batch. -/
theorem poissonFixedEpochTotalAverageVariance_fullBatch_eq_base_sq
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta energy : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    poissonFixedEpochTotalAverageVariance
        (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
        sensitivity epsilon delta energy =
      (fullBatchGaussianBaseStddev sensitivity epsilon delta
        sensitivity_pos epsilon_nonneg delta_pos delta_lt_one) ^ 2 := by
  unfold poissonFixedEpochTotalAverageVariance
    poissonFixedEpochTotalAverageVarianceOfStddev
  rw [poissonFixedEpochSamplingVariance_fullBatch]
  simp only [zero_add]
  exact poissonFixedEpochPrivacyVariance_fullBatch_eq_base_sq epoch epoch_pos
    sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos delta_lt_one

end

end Mf.DP
