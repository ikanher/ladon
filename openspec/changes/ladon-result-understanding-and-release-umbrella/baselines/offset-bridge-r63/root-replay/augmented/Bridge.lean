import Mf.DP.PoissonFixedEpochAsymptotics

open Filter
open scoped Topology
namespace OffsetBridge
noncomputable section
set_option autoImplicit false

/-- Intended offset component only. A placeholder here is not completion. -/
theorem fixedEpochOffsetBridge
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
  let schedule := Mf.DP.cappedFixedParticipationSchedule
    (epoch : NNReal) (by exact_mod_cast epoch_pos)
  have hrate (extra : Nat) :
      schedule.samplingRate (epoch + extra) =
        (Mf.DP.PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate := by
    simp [schedule, Mf.DP.cappedFixedParticipationSchedule,
      Mf.DP.cappedParticipationRate,
      Mf.DP.PoissonFixedEpochPoint.samplingRate,
      Mf.DP.PoissonFixedEpochPoint.ofExtra]
    apply (div_le_one (by exact_mod_cast Nat.add_pos_left epoch_pos extra)).2
    exact_mod_cast Nat.le_add_right epoch extra
  have hstd (extra : Nat) :
      Mf.DP.fixedParticipationCalibratedStddev schedule sensitivity epsilon delta
          (epoch + extra) =
        Mf.DP.poissonFixedEpochCalibratedStddev
          (Mf.DP.PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          sensitivity epsilon delta := by
    simp [Mf.DP.fixedParticipationCalibratedStddev,
      Mf.DP.poissonFixedEpochCalibratedStddev, hrate]
  have hmain := Mf.DP.tendsto_fixedParticipationCalibratedStddev_offset
    schedule sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
    (by simpa [schedule, Mf.DP.cappedFixedParticipationSchedule] using delta_lt_boundary)
  have hshift : Tendsto (fun extra : Nat => epoch + extra) atTop atTop := by
    apply tendsto_atTop.2
    intro b
    filter_upwards [Filter.eventually_ge_atTop b] with n hn
    omega
  have hcompose := hmain.comp hshift
  have hfun :
      (fun extra : Nat =>
        sensitivity /
          (Mf.DP.poissonFixedEpochCalibratedStddev
            (Mf.DP.PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta : Real) -
          Real.sqrt (2 * Real.log ((epoch + extra : Nat) : Real))) =
      (fun extra : Nat =>
        sensitivity /
          (Mf.DP.fixedParticipationCalibratedStddev schedule sensitivity epsilon delta
            (epoch + extra) : Real) -
          Mf.DP.gaussianCriticalScale (epoch + extra)) := by
    funext extra
    simp [hstd, Mf.DP.gaussianCriticalScale]
  rw [hfun]
  convert hcompose using 1
  · rfl
  · simp [schedule, Mf.DP.cappedFixedParticipationSchedule,
      Mf.DP.fixedParticipationTargetOffset,
      Mf.DP.fixedParticipationTargetProbability]

#print axioms fixedEpochOffsetBridge
end
end OffsetBridge
