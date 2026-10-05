import Mf.DP.PoissonFixedEpochAsymptotics

open Filter
open scoped Topology
namespace Mf.DP
noncomputable section
set_option autoImplicit false

/-- Fixed-epoch specialization of the calibrated standard-deviation offset limit.
The horizons `epoch + extra` cover the admissible integer tail. -/
theorem tendsto_poissonFixedEpochCalibratedStddev_offset
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra : Nat =>
        sensitivity /
          (Mf.DP.poissonFixedEpochCalibratedStddev
            (Mf.DP.PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta : Real) -
          Real.sqrt (2 * Real.log ((epoch + extra : Nat) : Real)))
      atTop
      (nhds (Mf.DP.standardNormalQuantile
        (-Real.log (1 - delta) / (epoch : Real)))) := by
  let schedule := Mf.DP.cappedFixedParticipationSchedule (epoch : NNReal)
    (by exact_mod_cast epoch_pos)
  have h := Mf.DP.tendsto_fixedParticipationCalibratedStddev_offset
    schedule sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_boundary
  have hShift := h.comp (tendsto_add_atTop_nat epoch)
  apply hShift.congr'
  filter_upwards with extra
  simp only [Function.comp_apply, schedule,
    Mf.DP.poissonFixedEpochCalibratedStddev,
    Mf.DP.fixedParticipationCalibratedStddev,
    Mf.DP.cappedFixedParticipationSchedule,
    Mf.DP.PoissonFixedEpochPoint.horizon_ofExtra,
    Mf.DP.PoissonFixedEpochPoint.ofExtra_samplingRate_eq_cappedParticipationRate,
    Mf.DP.gaussianCriticalScale,
    Nat.add_comm]

end
end Mf.DP
