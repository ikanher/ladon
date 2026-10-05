import Mathlib

/-!
# Sampling schedules with finite expected participation

This module defines a semantic interface for Poisson sampling schedules whose
expected participation count converges to a finite positive budget. It also
provides a total capped version of the exact quotient schedule `ρ / T`; the cap
only affects a finite prefix.

The schedule models independent Poisson inclusion. It does not model exact,
balanced, or shuffled participation.
-/

open Filter
open scoped Topology

namespace Mf.DP

noncomputable section

/-- A valid Poisson sampling schedule with a finite positive limiting expected
participation count. -/
structure FixedParticipationSchedule where
  samplingRate : Nat → NNReal
  rate_le_one : ∀ horizon, samplingRate horizon ≤ 1
  participationBudget : NNReal
  participationBudget_pos : 0 < participationBudget
  tendsto_expectedParticipation :
    Tendsto
      (fun horizon : Nat =>
        (horizon : Real) * (samplingRate horizon : Real))
      atTop (𝓝 (participationBudget : Real))

/-- Total capped exact-budget rate `min 1 (ρ / T)`. The zero-horizon value is
zero under the total division convention; asymptotic theorems use positive
horizons. -/
def cappedParticipationRate
    (participationBudget : NNReal) (horizon : Nat) : NNReal :=
  min 1 (participationBudget / (horizon : NNReal))

theorem cappedParticipationRate_le_one
    (participationBudget : NNReal) (horizon : Nat) :
    cappedParticipationRate participationBudget horizon ≤ 1 :=
  min_le_left _ _

/-- The probability cap is inactive at all sufficiently large horizons. -/
theorem eventually_cappedParticipationRate_eq_div
    (participationBudget : NNReal) :
    ∀ᶠ horizon : Nat in atTop,
      cappedParticipationRate participationBudget horizon =
        participationBudget / (horizon : NNReal) := by
  filter_upwards
    [eventually_ge_atTop (max 1 (Nat.ceil participationBudget))] with horizon hHorizon
  unfold cappedParticipationRate
  apply min_eq_right
  rw [div_le_one (by
    exact_mod_cast (show 0 < horizon from
      lt_of_lt_of_le Nat.zero_lt_one
        (le_trans (le_max_left _ _) hHorizon)))]
  exact (Nat.ceil_le).mp (le_trans (le_max_right _ _) hHorizon)

/-- The capped quotient schedule has limiting expected participation `ρ`. -/
theorem tendsto_horizon_mul_cappedParticipationRate
    (participationBudget : NNReal) :
    Tendsto
      (fun horizon : Nat =>
        (horizon : Real) *
          (cappedParticipationRate participationBudget horizon : Real))
      atTop (𝓝 (participationBudget : Real)) := by
  have hRate := eventually_cappedParticipationRate_eq_div participationBudget
  have hPositive : ∀ᶠ horizon : Nat in atTop, 0 < horizon := by
    filter_upwards
      [eventually_ge_atTop (max 1 (Nat.ceil participationBudget))] with horizon hHorizon
    exact lt_of_lt_of_le Nat.zero_lt_one
      (le_trans (le_max_left _ _) hHorizon)
  have hEventuallyConstant : ∀ᶠ horizon : Nat in atTop,
      (horizon : Real) *
          (cappedParticipationRate participationBudget horizon : Real) =
        (participationBudget : Real) := by
    filter_upwards [hRate, hPositive] with horizon hRateAt hHorizon
    rw [hRateAt, NNReal.coe_div]
    field_simp [ne_of_gt (by exact_mod_cast hHorizon)]
    norm_num
    ring
  exact tendsto_congr' hEventuallyConstant |>.mpr tendsto_const_nhds

/-- The capped exact-budget rate packaged as a valid finite-participation
schedule. -/
def cappedFixedParticipationSchedule
    (participationBudget : NNReal) (participationBudget_pos : 0 < participationBudget) :
    FixedParticipationSchedule where
  samplingRate := cappedParticipationRate participationBudget
  rate_le_one := cappedParticipationRate_le_one participationBudget
  participationBudget := participationBudget
  participationBudget_pos := participationBudget_pos
  tendsto_expectedParticipation :=
    tendsto_horizon_mul_cappedParticipationRate participationBudget

/-- A finite positive expected-participation budget forces the per-step
sampling rate to vanish. -/
theorem FixedParticipationSchedule.tendsto_samplingRate_zero
    (schedule : FixedParticipationSchedule) :
    Tendsto
      (fun horizon => (schedule.samplingRate horizon : Real))
      atTop (𝓝 0) := by
  have hHorizon : Tendsto (fun horizon : Nat => (horizon : Real)) atTop atTop :=
    tendsto_natCast_atTop_atTop
  have hRatio := schedule.tendsto_expectedParticipation.div_atTop hHorizon
  apply hRatio.congr'
  filter_upwards [eventually_gt_atTop (0 : Nat)] with horizon hHorizonPos
  field_simp [show (horizon : Real) ≠ 0 by exact_mod_cast ne_of_gt hHorizonPos]

/-- A positive limiting participation budget forces the sampling rate to be
strictly positive at all sufficiently large horizons. -/
theorem FixedParticipationSchedule.eventually_samplingRate_pos
    (schedule : FixedParticipationSchedule) :
    ∀ᶠ horizon : Nat in atTop, 0 < schedule.samplingRate horizon := by
  have hProduct : ∀ᶠ horizon : Nat in atTop,
      0 < (horizon : Real) * (schedule.samplingRate horizon : Real) :=
    (tendsto_order.1 schedule.tendsto_expectedParticipation).1 0
      (by exact_mod_cast schedule.participationBudget_pos)
  filter_upwards [hProduct] with horizon hProduct
  have hRateReal : 0 < (schedule.samplingRate horizon : Real) := by
    have hHorizon : 0 ≤ (horizon : Real) := by positivity
    nlinarith
  exact_mod_cast hRateReal

/-- The quadratic sampling-rate scale used by centered perturbation variances
vanishes under finite expected participation. -/
theorem FixedParticipationSchedule.tendsto_horizon_mul_samplingRate_sq_zero
    (schedule : FixedParticipationSchedule) :
    Tendsto
      (fun horizon : Nat =>
        (horizon : Real) * (schedule.samplingRate horizon : Real) ^ 2)
      atTop (𝓝 0) := by
  have hProduct := schedule.tendsto_expectedParticipation.mul
    schedule.tendsto_samplingRate_zero
  convert hProduct using 1 <;> ring

end

end Mf.DP
