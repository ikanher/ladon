import Mf.DP.FixedParticipationGaussianCalibrationBracketing

open Filter
open scoped Topology

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- Fixed positive windows shrinking around `target` characterize convergence
to `target`. -/
theorem tendsto_of_eventually_fixedWindow
    (value : Nat → Real) (target : Real)
    (hWindow : ∀ eta : NNReal, 0 < eta →
      ∀ᶠ horizon : Nat in atTop,
        target - (eta : Real) ≤ value horizon ∧
          value horizon ≤ target + (eta : Real)) :
    Tendsto value atTop (nhds target) := by
  rw [tendsto_order]
  constructor
  · intro lower hLower
    let eta : NNReal := Real.toNNReal ((target - lower) / 2)
    have hEtaReal : 0 < (eta : Real) := by
      dsimp [eta]
      rw [max_eq_left (by linarith)]
      linarith
    have hEta : 0 < eta := by exact_mod_cast hEtaReal
    filter_upwards [hWindow eta hEta] with horizon hBounds
    have hLowerWindow : lower < target - (eta : Real) := by
      dsimp [eta]
      rw [max_eq_left (by linarith)]
      linarith
    exact hLowerWindow.trans_le hBounds.1
  · intro upper hUpper
    let eta : NNReal := Real.toNNReal ((upper - target) / 2)
    have hEtaReal : 0 < (eta : Real) := by
      dsimp [eta]
      rw [max_eq_left (by linarith)]
      linarith
    have hEta : 0 < eta := by exact_mod_cast hEtaReal
    filter_upwards [hWindow eta hEta] with horizon hBounds
    have hUpperWindow : target + (eta : Real) < upper := by
      dsimp [eta]
      rw [max_eq_left (by linarith)]
      linarith
    exact hBounds.2.trans_lt hUpperWindow

/-- A fixed-offset lower/upper standard-deviation bracket squeezes the
standardized shift to the target offset. -/
theorem tendsto_standardizedOffset_of_candidateBracket
    (calibratedStddev : Nat → NNReal)
    (sensitivity targetOffset : Real)
    (hSensitivity : 0 < sensitivity)
    (hBracket : ∀ eta : NNReal, 0 < eta →
      ∀ᶠ horizon : Nat in atTop,
        fixedParticipationLowerStddevCandidate
            sensitivity targetOffset eta horizon ≤ calibratedStddev horizon ∧
          calibratedStddev horizon ≤
            fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon) :
    Tendsto
      (fun horizon =>
        sensitivity / (calibratedStddev horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds targetOffset) := by
  apply tendsto_of_eventually_fixedWindow
  intro eta hEta
  have hDenominators :=
    eventually_fixedOffset_denominators_pos targetOffset eta
  filter_upwards
    [hBracket eta hEta,
      eventually_coe_fixedParticipationLowerStddevCandidate eta hSensitivity,
      eventually_coe_fixedParticipationUpperStddevCandidate eta hSensitivity,
      hDenominators.1, hDenominators.2]
      with horizon hBracketAt hLower hUpper hUpperDenominator hLowerDenominator
  have hCalibratedPos : 0 < calibratedStddev horizon :=
    hLower.1.trans_le hBracketAt.1
  have hCalibratedPosReal : 0 < (calibratedStddev horizon : Real) := by
    exact_mod_cast hCalibratedPos
  have hLowerLeReal :
      (fixedParticipationLowerStddevCandidate
        sensitivity targetOffset eta horizon : Real) ≤
          (calibratedStddev horizon : Real) := by
    exact_mod_cast hBracketAt.1
  have hCalibratedLeUpperReal :
      (calibratedStddev horizon : Real) ≤
        (fixedParticipationUpperStddevCandidate
          sensitivity targetOffset eta horizon : Real) := by
    exact_mod_cast hBracketAt.2
  have hUpperOffset :
      sensitivity /
            (fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon : Real) -
          gaussianCriticalScale horizon = targetOffset - (eta : Real) := by
    rw [hUpper.2]
    field_simp [ne_of_gt hSensitivity, ne_of_gt hUpperDenominator]
    ring
  have hLowerOffset :
      sensitivity /
            (fixedParticipationLowerStddevCandidate
              sensitivity targetOffset eta horizon : Real) -
          gaussianCriticalScale horizon = targetOffset + (eta : Real) := by
    rw [hLower.2]
    field_simp [ne_of_gt hSensitivity, ne_of_gt hLowerDenominator]
    ring
  constructor
  · rw [← hUpperOffset]
    apply sub_le_sub_right
    exact (div_le_div_iff_of_pos_left hSensitivity
      (by exact_mod_cast hUpper.1) hCalibratedPosReal).2
        hCalibratedLeUpperReal
  · rw [← hLowerOffset]
    apply sub_le_sub_right
    exact (div_le_div_iff_of_pos_left hSensitivity
      hCalibratedPosReal (by exact_mod_cast hLower.1)).2 hLowerLeReal

/-- A finite standardized-shift offset forces the first-order calibrated-noise
scale `2 σ_T² log T / Δ²` to converge to one. -/
theorem tendsto_stddev_sq_mul_two_log_div_sensitivity_sq_one
    (noiseStddev : Nat → NNReal) (sensitivity offset : Real)
    (hSensitivity : 0 < sensitivity)
    (hStddev : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon)
    (hOffset : Tendsto
      (fun horizon =>
        sensitivity / (noiseStddev horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds offset)) :
    Tendsto
      (fun horizon =>
        2 * (noiseStddev horizon : Real) ^ 2 *
            Real.log (horizon : Real) /
          sensitivity ^ 2)
      atTop (nhds 1) := by
  let standardizedShift : Nat → Real := fun horizon =>
    sensitivity / (noiseStddev horizon : Real)
  have hShiftTop : Tendsto standardizedShift atTop atTop :=
    tendsto_standardizedShift_atTop_of_sub_critical_tendsto
      standardizedShift offset hOffset
  have hErrorDivShift : Tendsto
      (fun horizon =>
        (standardizedShift horizon - gaussianCriticalScale horizon) /
          standardizedShift horizon)
      atTop (nhds 0) :=
    hOffset.div_atTop hShiftTop
  have hShiftPos : ∀ᶠ horizon : Nat in atTop,
      0 < standardizedShift horizon :=
    hShiftTop.eventually (eventually_gt_atTop 0)
  have hCriticalDivShift : Tendsto
      (fun horizon =>
        gaussianCriticalScale horizon / standardizedShift horizon)
      atTop (nhds 1) := by
    have hOne : Tendsto (fun _ : Nat => (1 : Real)) atTop (nhds 1) :=
      tendsto_const_nhds
    have hOneSub := hOne.sub hErrorDivShift
    have hEq :
        (fun horizon =>
          1 - (standardizedShift horizon - gaussianCriticalScale horizon) /
            standardizedShift horizon) =ᶠ[atTop]
          (fun horizon =>
            gaussianCriticalScale horizon / standardizedShift horizon) := by
      filter_upwards [hShiftPos] with horizon hPositive
      field_simp [ne_of_gt hPositive]
      ring
    simpa using hOneSub.congr' hEq
  have hSquared : Tendsto
      (fun horizon =>
        (gaussianCriticalScale horizon / standardizedShift horizon) ^ 2)
      atTop (nhds 1) := by
    simpa using hCriticalDivShift.pow 2
  apply hSquared.congr'
  filter_upwards
    [hStddev, eventually_gaussianCriticalScale_sq]
      with horizon hNoise hCriticalSq
  dsimp [standardizedShift]
  rw [div_pow, hCriticalSq]
  have hNoiseReal : 0 < (noiseStddev horizon : Real) := by
    exact_mod_cast hNoise
  field_simp [ne_of_gt hSensitivity, ne_of_gt hNoiseReal]

/-- Finite standardized-shift offset is equivalently the first-order ratio
`σ_T b_T / Δ → 1`. -/
theorem tendsto_stddev_mul_critical_div_sensitivity_one
    (noiseStddev : Nat → NNReal) (sensitivity offset : Real)
    (hSensitivity : 0 < sensitivity)
    (hStddev : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon)
    (hOffset : Tendsto
      (fun horizon =>
        sensitivity / (noiseStddev horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds offset)) :
    Tendsto
      (fun horizon =>
        (noiseStddev horizon : Real) * gaussianCriticalScale horizon /
          sensitivity)
      atTop (nhds 1) := by
  let standardizedShift : Nat → Real := fun horizon =>
    sensitivity / (noiseStddev horizon : Real)
  have hShiftTop : Tendsto standardizedShift atTop atTop :=
    tendsto_standardizedShift_atTop_of_sub_critical_tendsto
      standardizedShift offset hOffset
  have hErrorDivShift : Tendsto
      (fun horizon =>
        (standardizedShift horizon - gaussianCriticalScale horizon) /
          standardizedShift horizon)
      atTop (nhds 0) :=
    hOffset.div_atTop hShiftTop
  have hShiftPos : ∀ᶠ horizon : Nat in atTop,
      0 < standardizedShift horizon :=
    hShiftTop.eventually (eventually_gt_atTop 0)
  have hCriticalDivShift : Tendsto
      (fun horizon =>
        gaussianCriticalScale horizon / standardizedShift horizon)
      atTop (nhds 1) := by
    have hOne : Tendsto (fun _ : Nat => (1 : Real)) atTop (nhds 1) :=
      tendsto_const_nhds
    have hOneSub := hOne.sub hErrorDivShift
    have hEq :
        (fun horizon =>
          1 - (standardizedShift horizon - gaussianCriticalScale horizon) /
            standardizedShift horizon) =ᶠ[atTop]
          (fun horizon =>
            gaussianCriticalScale horizon / standardizedShift horizon) := by
      filter_upwards [hShiftPos] with horizon hPositive
      field_simp [ne_of_gt hPositive]
      ring
    simpa using hOneSub.congr' hEq
  apply hCriticalDivShift.congr'
  filter_upwards [hStddev] with horizon hNoise
  dsimp [standardizedShift]
  have hNoiseReal : 0 < (noiseStddev horizon : Real) := by
    exact_mod_cast hNoise
  field_simp [ne_of_gt hSensitivity, ne_of_gt hNoiseReal]

/-- For the capped exact-budget schedule, replacing `log T` by
`log (1 / q_T)` preserves the first-order standard-deviation ratio. -/
theorem tendsto_cappedRate_stddev_mul_sqrt_two_log_inv_div_sensitivity_one
    (participationBudget : NNReal) (hBudget : 0 < participationBudget)
    (noiseStddev : Nat → NNReal) (sensitivity offset : Real)
    (hSensitivity : 0 < sensitivity)
    (hStddev : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon)
    (hOffset : Tendsto
      (fun horizon =>
        sensitivity / (noiseStddev horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds offset)) :
    Tendsto
      (fun horizon =>
        (noiseStddev horizon : Real) *
            Real.sqrt (2 * Real.log
              (1 / (cappedParticipationRate participationBudget horizon : Real))) /
          sensitivity)
      atTop (nhds 1) := by
  have hLogHorizon : Tendsto
      (fun horizon : Nat => Real.log (horizon : Real)) atTop atTop :=
    Real.tendsto_log_atTop.comp tendsto_natCast_atTop_atTop
  have hBudgetReal : 0 < (participationBudget : Real) := by
    exact_mod_cast hBudget
  have hLogBudgetDiv : Tendsto
      (fun horizon : Nat =>
        Real.log (participationBudget : Real) /
          Real.log (horizon : Real))
      atTop (nhds 0) :=
    tendsto_const_nhds.div_atTop hLogHorizon
  have hReferenceLogRatio : Tendsto
      (fun horizon : Nat =>
        (Real.log (horizon : Real) -
            Real.log (participationBudget : Real)) /
          Real.log (horizon : Real))
      atTop (nhds 1) := by
    have hOne : Tendsto (fun _ : Nat => (1 : Real)) atTop (nhds 1) :=
      tendsto_const_nhds
    have hOneSub := hOne.sub hLogBudgetDiv
    have hEq :
        (fun horizon : Nat =>
          1 - Real.log (participationBudget : Real) /
            Real.log (horizon : Real)) =ᶠ[atTop]
          (fun horizon : Nat =>
            (Real.log (horizon : Real) -
                Real.log (participationBudget : Real)) /
              Real.log (horizon : Real)) := by
      filter_upwards
        [hLogHorizon.eventually (eventually_gt_atTop 0)]
        with horizon hLogPositive
      field_simp [ne_of_gt hLogPositive]
    simpa using hOneSub.congr' hEq
  have hRateLogRatio : Tendsto
      (fun horizon : Nat =>
        Real.log
              (1 / (cappedParticipationRate participationBudget horizon : Real)) /
          Real.log (horizon : Real))
      atTop (nhds 1) := by
    apply hReferenceLogRatio.congr'
    filter_upwards
      [eventually_cappedParticipationRate_eq_div participationBudget,
        eventually_gt_atTop (0 : Nat)]
      with horizon hRate hHorizon
    have hRateReal := congrArg (fun rate : NNReal => (rate : Real)) hRate
    norm_num at hRateReal
    rw [hRateReal]
    have hHorizonReal : 0 < (horizon : Real) := by exact_mod_cast hHorizon
    have hRatioIdentity :
        1 / ((participationBudget : Real) / (horizon : Real)) =
          (horizon : Real) / (participationBudget : Real) := by
      field_simp [ne_of_gt hBudgetReal, ne_of_gt hHorizonReal]
    rw [hRatioIdentity,
      Real.log_div (ne_of_gt hHorizonReal) (ne_of_gt hBudgetReal)]
  have hSqrtRateLogRatio : Tendsto
      (fun horizon : Nat =>
        Real.sqrt (2 * Real.log
              (1 / (cappedParticipationRate participationBudget horizon : Real))) /
          gaussianCriticalScale horizon)
      atTop (nhds 1) := by
    have hSqrt := hRateLogRatio.sqrt
    have hRateLtOne : ∀ᶠ horizon : Nat in atTop,
        (cappedParticipationRate participationBudget horizon : Real) < 1 :=
      (tendsto_order.1
        (FixedParticipationSchedule.tendsto_samplingRate_zero
          (cappedFixedParticipationSchedule participationBudget hBudget))).2
            1 zero_lt_one
    have hEq :
        (fun horizon : Nat =>
          Real.sqrt
            (Real.log
                (1 / (cappedParticipationRate participationBudget horizon : Real)) /
              Real.log (horizon : Real))) =ᶠ[atTop]
          (fun horizon : Nat =>
            Real.sqrt (2 * Real.log
                (1 / (cappedParticipationRate participationBudget horizon : Real))) /
              gaussianCriticalScale horizon) := by
      filter_upwards
        [hLogHorizon.eventually (eventually_gt_atTop 0),
          (cappedFixedParticipationSchedule participationBudget hBudget).eventually_samplingRate_pos,
          hRateLtOne]
        with horizon hLogPositive hRatePositive hRateLtOneAt
      have hRatePositiveReal :
          0 < (cappedParticipationRate participationBudget horizon : Real) := by
        exact_mod_cast hRatePositive
      have hInvRateGtOne :
          1 < 1 / (cappedParticipationRate participationBudget horizon : Real) := by
        simpa using one_div_lt_one_div_of_lt hRatePositiveReal hRateLtOneAt
      have hLogInvRateNonneg :
          0 ≤ Real.log
            (1 / (cappedParticipationRate participationBudget horizon : Real)) :=
        (Real.log_nonneg hInvRateGtOne.le)
      rw [gaussianCriticalScale,
        ← Real.sqrt_div (mul_nonneg (by positivity) hLogInvRateNonneg)]
      congr 1
      field_simp [ne_of_gt hLogPositive]
    simpa using hSqrt.congr' hEq
  have hCriticalRatio :=
    tendsto_stddev_mul_critical_div_sensitivity_one
      noiseStddev sensitivity offset hSensitivity hStddev hOffset
  have hProduct := hCriticalRatio.mul hSqrtRateLogRatio
  have hEq :
      (fun horizon =>
        (noiseStddev horizon : Real) * gaussianCriticalScale horizon /
            sensitivity *
          (Real.sqrt (2 * Real.log
              (1 / (cappedParticipationRate participationBudget horizon : Real))) /
            gaussianCriticalScale horizon)) =ᶠ[atTop]
        (fun horizon =>
          (noiseStddev horizon : Real) *
              Real.sqrt (2 * Real.log
                (1 / (cappedParticipationRate participationBudget horizon : Real))) /
            sensitivity) := by
    filter_upwards
      [eventually_gaussianCriticalScale_pos]
        with horizon hCritical
    field_simp [ne_of_gt hSensitivity, ne_of_gt hCritical]
  simpa using hProduct.congr' hEq

/-- Calibrated standard deviation along a fixed-participation schedule. -/
def fixedParticipationCalibratedStddev
    (schedule : FixedParticipationSchedule)
    (sensitivity epsilon delta : Real) (horizon : Nat) : NNReal :=
  sampledGaussianCalibratedStddev horizon
    (schedule.samplingRate horizon) (schedule.rate_le_one horizon)
    sensitivity epsilon delta

/-- A lower/upper candidate bracket makes the calibrated standard deviation
eventually positive. -/
theorem eventually_fixedParticipationCalibratedStddev_pos_of_candidateBracket
    (schedule : FixedParticipationSchedule)
    (sensitivity epsilon delta targetOffset : Real)
    (hSensitivity : 0 < sensitivity)
    (hBracket : ∀ eta : NNReal, 0 < eta →
      ∀ᶠ horizon : Nat in atTop,
        fixedParticipationLowerStddevCandidate
            sensitivity targetOffset eta horizon ≤
              fixedParticipationCalibratedStddev
                schedule sensitivity epsilon delta horizon ∧
          fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon ≤
            fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon) :
    ∀ᶠ horizon : Nat in atTop,
      0 < fixedParticipationCalibratedStddev
        schedule sensitivity epsilon delta horizon := by
  let eta : NNReal := 1
  have hEta : 0 < eta := by simp [eta]
  filter_upwards
    [hBracket eta hEta,
      eventually_coe_fixedParticipationLowerStddevCandidate eta hSensitivity]
      with horizon hBracketAt hLower
  exact hLower.1.trans_le hBracketAt.1

/-- Task 8.9 seam: the calibrated standardized shift converges to the target
offset once the fixed-window candidate bracket is available. -/
theorem tendsto_fixedParticipationCalibratedStddev_offset_of_candidateBracket
    (schedule : FixedParticipationSchedule)
    (sensitivity epsilon delta targetOffset : Real)
    (hSensitivity : 0 < sensitivity)
    (hBracket : ∀ eta : NNReal, 0 < eta →
      ∀ᶠ horizon : Nat in atTop,
        fixedParticipationLowerStddevCandidate
            sensitivity targetOffset eta horizon ≤
              fixedParticipationCalibratedStddev
                schedule sensitivity epsilon delta horizon ∧
          fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon ≤
            fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon) :
    Tendsto
      (fun horizon =>
        sensitivity /
            (fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds targetOffset) := by
  exact tendsto_standardizedOffset_of_candidateBracket
    (fixedParticipationCalibratedStddev schedule sensitivity epsilon delta)
      sensitivity targetOffset hSensitivity hBracket

/-- Task 8.10 seam: the exact calibrated `sInf` has first-order variance scale
one once the candidate bracket is connected. -/
theorem tendsto_fixedParticipationCalibratedStddev_sq_mul_two_log_div_sensitivity_sq_one_of_candidateBracket
    (schedule : FixedParticipationSchedule)
    (sensitivity epsilon delta targetOffset : Real)
    (hSensitivity : 0 < sensitivity)
    (hBracket : ∀ eta : NNReal, 0 < eta →
      ∀ᶠ horizon : Nat in atTop,
        fixedParticipationLowerStddevCandidate
            sensitivity targetOffset eta horizon ≤
              fixedParticipationCalibratedStddev
                schedule sensitivity epsilon delta horizon ∧
          fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon ≤
            fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon) :
    Tendsto
      (fun horizon =>
        2 * (fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon : Real) ^ 2 *
            Real.log (horizon : Real) /
          sensitivity ^ 2)
      atTop (nhds 1) := by
  apply tendsto_stddev_sq_mul_two_log_div_sensitivity_sq_one
    (fixedParticipationCalibratedStddev schedule sensitivity epsilon delta)
      sensitivity targetOffset hSensitivity
  · exact eventually_fixedParticipationCalibratedStddev_pos_of_candidateBracket
      schedule sensitivity epsilon delta targetOffset hSensitivity hBracket
  · exact tendsto_fixedParticipationCalibratedStddev_offset_of_candidateBracket
      schedule sensitivity epsilon delta targetOffset hSensitivity hBracket

/-- Task 8.11 seam: for the capped exact-budget schedule, the exact calibrated
standard deviation is asymptotic to `Δ / sqrt (2 log (1/q_T))`. -/
theorem tendsto_cappedFixedParticipationCalibratedStddev_smallRate_ratio_one_of_candidateBracket
    (participationBudget : NNReal) (hBudget : 0 < participationBudget)
    (sensitivity epsilon delta targetOffset : Real)
    (hSensitivity : 0 < sensitivity)
    (hBracket : ∀ eta : NNReal, 0 < eta →
      ∀ᶠ horizon : Nat in atTop,
        fixedParticipationLowerStddevCandidate
            sensitivity targetOffset eta horizon ≤
              fixedParticipationCalibratedStddev
                (cappedFixedParticipationSchedule participationBudget hBudget)
                sensitivity epsilon delta horizon ∧
          fixedParticipationCalibratedStddev
              (cappedFixedParticipationSchedule participationBudget hBudget)
              sensitivity epsilon delta horizon ≤
            fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon) :
    Tendsto
      (fun horizon =>
        (fixedParticipationCalibratedStddev
            (cappedFixedParticipationSchedule participationBudget hBudget)
            sensitivity epsilon delta horizon : Real) *
          Real.sqrt (2 * Real.log
            (1 / (cappedParticipationRate participationBudget horizon : Real))) /
          sensitivity)
      atTop (nhds 1) := by
  apply tendsto_cappedRate_stddev_mul_sqrt_two_log_inv_div_sensitivity_one
    participationBudget hBudget
    (fixedParticipationCalibratedStddev
      (cappedFixedParticipationSchedule participationBudget hBudget)
      sensitivity epsilon delta)
    sensitivity targetOffset hSensitivity
  · exact eventually_fixedParticipationCalibratedStddev_pos_of_candidateBracket
      (cappedFixedParticipationSchedule participationBudget hBudget)
      sensitivity epsilon delta targetOffset hSensitivity hBracket
  · exact tendsto_fixedParticipationCalibratedStddev_offset_of_candidateBracket
      (cappedFixedParticipationSchedule participationBudget hBudget)
      sensitivity epsilon delta targetOffset hSensitivity hBracket

/-- Task 8.9: under the interior privacy domain, the calibrated standardized
shift converges to the target normal-quantile offset. -/
theorem tendsto_fixedParticipationCalibratedStddev_offset
    (schedule : FixedParticipationSchedule)
    (sensitivity epsilon delta : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon)
    (hDeltaPos : 0 < delta)
    (hDeltaLtBoundary :
      delta < 1 - Real.exp (-(schedule.participationBudget : Real))) :
    Tendsto
      (fun horizon =>
        sensitivity /
            (fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds (fixedParticipationTargetOffset
        (schedule.participationBudget : Real) delta)) := by
  let targetOffset := fixedParticipationTargetOffset
    (schedule.participationBudget : Real) delta
  apply tendsto_fixedParticipationCalibratedStddev_offset_of_candidateBracket
    schedule sensitivity epsilon delta targetOffset hSensitivity
  intro eta hEta
  simpa [fixedParticipationCalibratedStddev, targetOffset] using
    eventually_fixedParticipationCalibratedStddev_bracketed schedule
      sensitivity epsilon delta eta hSensitivity hEpsilon hDeltaPos
      hDeltaLtBoundary hEta

/-- Task 8.10: under the interior privacy domain, the exact calibrated
standard deviation has first-order variance scale one. -/
theorem tendsto_fixedParticipationCalibratedStddev_sq_mul_two_log_div_sensitivity_sq_one
    (schedule : FixedParticipationSchedule)
    (sensitivity epsilon delta : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon)
    (hDeltaPos : 0 < delta)
    (hDeltaLtBoundary :
      delta < 1 - Real.exp (-(schedule.participationBudget : Real))) :
    Tendsto
      (fun horizon =>
        2 * (fixedParticipationCalibratedStddev
              schedule sensitivity epsilon delta horizon : Real) ^ 2 *
            Real.log (horizon : Real) /
          sensitivity ^ 2)
      atTop (nhds 1) := by
  let targetOffset := fixedParticipationTargetOffset
    (schedule.participationBudget : Real) delta
  apply
    tendsto_fixedParticipationCalibratedStddev_sq_mul_two_log_div_sensitivity_sq_one_of_candidateBracket
      schedule sensitivity epsilon delta targetOffset hSensitivity
  intro eta hEta
  simpa [fixedParticipationCalibratedStddev, targetOffset] using
    eventually_fixedParticipationCalibratedStddev_bracketed schedule
      sensitivity epsilon delta eta hSensitivity hEpsilon hDeltaPos
      hDeltaLtBoundary hEta

/-- Task 8.11: for the capped exact-budget schedule, calibrated noise is
asymptotic to `Δ / sqrt (2 log (1/q_T))`. -/
theorem tendsto_cappedFixedParticipationCalibratedStddev_smallRate_ratio_one
    (participationBudget : NNReal) (hBudget : 0 < participationBudget)
    (sensitivity epsilon delta : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon)
    (hDeltaPos : 0 < delta)
    (hDeltaLtBoundary :
      delta < 1 - Real.exp (-(participationBudget : Real))) :
    Tendsto
      (fun horizon =>
        (fixedParticipationCalibratedStddev
            (cappedFixedParticipationSchedule participationBudget hBudget)
            sensitivity epsilon delta horizon : Real) *
          Real.sqrt (2 * Real.log
            (1 / (cappedParticipationRate participationBudget horizon : Real))) /
          sensitivity)
      atTop (nhds 1) := by
  let schedule := cappedFixedParticipationSchedule participationBudget hBudget
  let targetOffset := fixedParticipationTargetOffset
    (participationBudget : Real) delta
  apply
    tendsto_cappedFixedParticipationCalibratedStddev_smallRate_ratio_one_of_candidateBracket
      participationBudget hBudget sensitivity epsilon delta targetOffset
        hSensitivity
  intro eta hEta
  simpa [fixedParticipationCalibratedStddev, schedule, targetOffset,
    cappedFixedParticipationSchedule] using
    eventually_fixedParticipationCalibratedStddev_bracketed schedule
      sensitivity epsilon delta eta hSensitivity hEpsilon hDeltaPos
      hDeltaLtBoundary hEta

end

end Mf.DP


