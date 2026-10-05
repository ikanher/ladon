import Mf.DP.FixedParticipationGaussianAccounting
import Mf.DP.SampledGaussianCalibrationThresholds

open Filter
open scoped Topology

namespace Mf.DP

noncomputable section

set_option autoImplicit false

private theorem tendsto_stdNormalCDFReal_atTop_one :
    Tendsto stdNormalCDFReal atTop (nhds 1) := by
  change Tendsto (fun x => ProbabilityTheory.cdf stdNormalMeasure x)
    atTop (nhds 1)
  exact ProbabilityTheory.tendsto_cdf_atTop stdNormalMeasure

private theorem tendsto_stdNormalCDFReal_atBot_zero :
    Tendsto stdNormalCDFReal atBot (nhds 0) := by
  change Tendsto (fun x => ProbabilityTheory.cdf stdNormalMeasure x)
    atBot (nhds 0)
  exact ProbabilityTheory.tendsto_cdf_atBot stdNormalMeasure

private theorem continuous_stdNormalCDFReal : Continuous stdNormalCDFReal := by
  rw [continuous_iff_continuousAt]
  intro offset
  exact (hasDerivAt_stdNormalCDFReal offset).continuousAt

private theorem exists_stdNormalCDFReal_eq
    {probability : Real} (hProbabilityPos : 0 < probability)
    (hProbabilityLtOne : probability < 1) :
    ∃ offset : Real, stdNormalCDFReal offset = probability := by
  rcases ((tendsto_order.1 tendsto_stdNormalCDFReal_atBot_zero).2
      probability hProbabilityPos).exists with ⟨lower, hLower⟩
  rcases ((tendsto_order.1 tendsto_stdNormalCDFReal_atTop_one).1
      probability hProbabilityLtOne).exists with ⟨upper, hUpper⟩
  exact Set.mem_range.mp
    (intermediate_value_univ lower upper continuous_stdNormalCDFReal
      ⟨hLower.le, hUpper.le⟩)

/-- Semantic inverse of the standard-normal CDF.  Its values outside `(0,1)`
are totalized and carry no calibration meaning. -/
noncomputable def standardNormalQuantile (probability : Real) : Real :=
  if h : 0 < probability ∧ probability < 1 then
    Classical.choose (exists_stdNormalCDFReal_eq h.1 h.2)
  else 0

theorem stdNormalCDFReal_standardNormalQuantile
    {probability : Real} (hProbabilityPos : 0 < probability)
    (hProbabilityLtOne : probability < 1) :
    stdNormalCDFReal (standardNormalQuantile probability) = probability := by
  rw [standardNormalQuantile, dif_pos ⟨hProbabilityPos, hProbabilityLtOne⟩]
  exact Classical.choose_spec
    (exists_stdNormalCDFReal_eq hProbabilityPos hProbabilityLtOne)

theorem standardNormalQuantile_eq_of_cdf_eq
    {probability offset : Real} (hProbabilityPos : 0 < probability)
    (hProbabilityLtOne : probability < 1)
    (hOffset : stdNormalCDFReal offset = probability) :
    standardNormalQuantile probability = offset := by
  apply strictMono_stdNormalCDFReal.injective
  rw [stdNormalCDFReal_standardNormalQuantile hProbabilityPos hProbabilityLtOne]
  exact hOffset.symm

/-- Probability level whose fixed-participation limiting accountant equals
`delta`.  Its calibration meaning is restricted to the open unit interval. -/
def fixedParticipationTargetProbability
    (participationBudget delta : Real) : Real :=
  -Real.log (1 - delta) / participationBudget

theorem fixedParticipationTargetProbability_mem_Ioo_iff
    {participationBudget delta : Real} (hBudget : 0 < participationBudget)
    (hDeltaLtOne : delta < 1) :
    0 < fixedParticipationTargetProbability participationBudget delta ∧
        fixedParticipationTargetProbability participationBudget delta < 1 ↔
      0 < delta ∧ delta < 1 - Real.exp (-participationBudget) := by
  unfold fixedParticipationTargetProbability
  have hOneSubDeltaPos : 0 < 1 - delta := sub_pos.mpr hDeltaLtOne
  constructor
  · rintro ⟨hProbabilityPos, hProbabilityLtOne⟩
    have hNegLogPos : 0 < -Real.log (1 - delta) := by
      rcases (div_pos_iff.mp hProbabilityPos) with hPositive | hNegative
      · exact hPositive.1
      · linarith [hNegative.2]
    have hLogNeg : Real.log (1 - delta) < 0 := by linarith
    have hDeltaPos : 0 < delta := by
      have : 1 - delta < 1 := (Real.log_neg_iff hOneSubDeltaPos).mp hLogNeg
      linarith
    have hNegLogLt : -Real.log (1 - delta) < participationBudget :=
      (div_lt_one hBudget).mp hProbabilityLtOne
    have hExpLt : Real.exp (-participationBudget) < 1 - delta := by
      exact (Real.lt_log_iff_exp_lt hOneSubDeltaPos).mp (by linarith)
    exact ⟨hDeltaPos, by linarith⟩
  · rintro ⟨hDeltaPos, hDeltaLtBoundary⟩
    have hOneSubDeltaLtOne : 1 - delta < 1 := by linarith
    have hLogNeg : Real.log (1 - delta) < 0 :=
      (Real.log_neg_iff hOneSubDeltaPos).mpr hOneSubDeltaLtOne
    have hProbabilityPos : 0 < -Real.log (1 - delta) / participationBudget :=
      div_pos (by linarith) hBudget
    have hExpLt : Real.exp (-participationBudget) < 1 - delta := by linarith
    have hNegBudgetLtLog : -participationBudget < Real.log (1 - delta) :=
      (Real.lt_log_iff_exp_lt hOneSubDeltaPos).mpr hExpLt
    have hProbabilityLtOne : -Real.log (1 - delta) / participationBudget < 1 :=
      (div_lt_one hBudget).mpr (by linarith)
    exact ⟨hProbabilityPos, hProbabilityLtOne⟩

/-- The target offset is the standard-normal quantile of the privacy-budget
probability. -/
noncomputable def fixedParticipationTargetOffset
    (participationBudget delta : Real) : Real :=
  standardNormalQuantile
    (fixedParticipationTargetProbability participationBudget delta)

theorem stdNormalCDFReal_fixedParticipationTargetOffset
    {participationBudget delta : Real} (hBudget : 0 < participationBudget)
    (hDeltaPos : 0 < delta)
    (hDeltaLtBoundary : delta < 1 - Real.exp (-participationBudget)) :
    stdNormalCDFReal
        (fixedParticipationTargetOffset participationBudget delta) =
      fixedParticipationTargetProbability participationBudget delta := by
  have hDeltaLtOne : delta < 1 := by
    have hExpPos : 0 < Real.exp (-participationBudget) := Real.exp_pos _
    linarith
  have hProbability :=
    (fixedParticipationTargetProbability_mem_Ioo_iff hBudget hDeltaLtOne).2
      ⟨hDeltaPos, hDeltaLtBoundary⟩
  exact stdNormalCDFReal_standardNormalQuantile hProbability.1 hProbability.2

/-- Fixed-participation limiting accounting profile at a finite standardized
shift offset. -/
def fixedParticipationLimitProfile
    (participationBudget offset : Real) : Real :=
  1 - Real.exp
    (-participationBudget * stdNormalCDFReal offset)

/-- For positive participation budget, the finite-offset limiting accounting
profile is strictly increasing in the standardized shift. -/
theorem strictMono_fixedParticipationLimitProfile
    {participationBudget : Real} (hBudget : 0 < participationBudget) :
    StrictMono (fixedParticipationLimitProfile participationBudget) := by
  intro lower upper hLowerUpper
  have hCDF : stdNormalCDFReal lower < stdNormalCDFReal upper :=
    strictMono_stdNormalCDFReal hLowerUpper
  have hExponent :
      -participationBudget * stdNormalCDFReal upper <
        -participationBudget * stdNormalCDFReal lower := by
    nlinarith
  have hExp :
      Real.exp (-participationBudget * stdNormalCDFReal upper) <
        Real.exp (-participationBudget * stdNormalCDFReal lower) :=
    Real.exp_lt_exp.mpr hExponent
  unfold fixedParticipationLimitProfile
  linarith

theorem fixedParticipationAccountantLimit_targetOffset
    {participationBudget delta : Real} (hBudget : 0 < participationBudget)
    (hDeltaPos : 0 < delta)
    (hDeltaLtBoundary : delta < 1 - Real.exp (-participationBudget)) :
    fixedParticipationLimitProfile participationBudget
        (fixedParticipationTargetOffset participationBudget delta) = delta := by
  rw [fixedParticipationLimitProfile,
    stdNormalCDFReal_fixedParticipationTargetOffset hBudget hDeltaPos hDeltaLtBoundary]
  unfold fixedParticipationTargetProbability
  have hDeltaLtOne : delta < 1 := by
    have hExpPos : 0 < Real.exp (-participationBudget) := Real.exp_pos _
    linarith
  have hOneSubDeltaPos : 0 < 1 - delta := sub_pos.mpr hDeltaLtOne
  rw [show -participationBudget *
        (-Real.log (1 - delta) / participationBudget) = Real.log (1 - delta) by
      field_simp]
  rw [Real.exp_log hOneSubDeltaPos]
  ring


/-- Standard-deviation candidate with fixed standardized-shift offset.  The
`toNNReal` wrapper totalizes the finitely many horizons at which the analytic
denominator need not yet be positive. -/
def fixedParticipationStddevCandidate
    (sensitivity offset : Real) (horizon : Nat) : NNReal :=
  Real.toNNReal
    (sensitivity / (gaussianCriticalScale horizon + offset))

/-- Every fixed-offset candidate eventually exposes its intended positive real
standard deviation. -/
theorem eventually_coe_fixedParticipationStddevCandidate
    {sensitivity offset : Real} (hSensitivity : 0 < sensitivity) :
    ∀ᶠ horizon : Nat in atTop,
      0 < fixedParticipationStddevCandidate sensitivity offset horizon ∧
      (fixedParticipationStddevCandidate sensitivity offset horizon : Real) =
        sensitivity / (gaussianCriticalScale horizon + offset) := by
  have hDenominator : ∀ᶠ horizon : Nat in atTop,
      0 < gaussianCriticalScale horizon + offset := by
    simpa using (eventually_fixedOffset_denominators_pos offset 0).2
  filter_upwards [hDenominator] with horizon hDenominator
  have hQuotient :
      0 < sensitivity / (gaussianCriticalScale horizon + offset) :=
    div_pos hSensitivity hDenominator
  constructor
  · exact Real.toNNReal_pos.mpr hQuotient
  · exact Real.coe_toNNReal _ hQuotient.le

/-- The candidate has exactly the requested standardized-shift offset
eventually, hence in the limit. -/
theorem tendsto_fixedParticipationStddevCandidate_offset
    {sensitivity offset : Real} (hSensitivity : 0 < sensitivity) :
    Tendsto
      (fun horizon : Nat =>
        sensitivity /
            (fixedParticipationStddevCandidate sensitivity offset horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds offset) := by
  have hDenominator : ∀ᶠ horizon : Nat in atTop,
      0 < gaussianCriticalScale horizon + offset := by
    simpa using (eventually_fixedOffset_denominators_pos offset 0).2
  apply tendsto_const_nhds.congr'
  filter_upwards
    [eventually_coe_fixedParticipationStddevCandidate hSensitivity,
      hDenominator]
      with horizon hCandidate hDenominatorPos
  rw [hCandidate.2]
  have hSensitivityNe : sensitivity ≠ 0 := ne_of_gt hSensitivity
  field_simp [hSensitivityNe, ne_of_gt hDenominatorPos]
  ring

/-- For nonnegative tolerance `eta`, the lower-noise calibration candidate
uses the larger standardized-shift offset `targetOffset + eta`.  Strict gap
theorems use the stronger premise `0 < eta`. -/
def fixedParticipationLowerStddevCandidate
    (sensitivity targetOffset : Real) (eta : NNReal) (horizon : Nat) : NNReal :=
  fixedParticipationStddevCandidate sensitivity (targetOffset + eta) horizon

/-- For nonnegative tolerance `eta`, the higher-noise calibration candidate
uses the smaller standardized-shift offset `targetOffset - eta`.  Strict gap
theorems use the stronger premise `0 < eta`. -/
def fixedParticipationUpperStddevCandidate
    (sensitivity targetOffset : Real) (eta : NNReal) (horizon : Nat) : NNReal :=
  fixedParticipationStddevCandidate sensitivity (targetOffset - eta) horizon

theorem eventually_coe_fixedParticipationLowerStddevCandidate
    {sensitivity targetOffset : Real} (eta : NNReal)
    (hSensitivity : 0 < sensitivity) :
    ∀ᶠ horizon : Nat in atTop,
      0 < fixedParticipationLowerStddevCandidate
          sensitivity targetOffset eta horizon ∧
      (fixedParticipationLowerStddevCandidate
          sensitivity targetOffset eta horizon : Real) =
        sensitivity /
          (gaussianCriticalScale horizon + (targetOffset + eta)) := by
  simpa [fixedParticipationLowerStddevCandidate] using
    eventually_coe_fixedParticipationStddevCandidate
      (offset := targetOffset + eta) hSensitivity

theorem eventually_coe_fixedParticipationUpperStddevCandidate
    {sensitivity targetOffset : Real} (eta : NNReal)
    (hSensitivity : 0 < sensitivity) :
    ∀ᶠ horizon : Nat in atTop,
      0 < fixedParticipationUpperStddevCandidate
          sensitivity targetOffset eta horizon ∧
      (fixedParticipationUpperStddevCandidate
          sensitivity targetOffset eta horizon : Real) =
        sensitivity /
          (gaussianCriticalScale horizon + (targetOffset - eta)) := by
  simpa [fixedParticipationUpperStddevCandidate] using
    eventually_coe_fixedParticipationStddevCandidate
      (offset := targetOffset - eta) hSensitivity

theorem tendsto_fixedParticipationLowerStddevCandidate_offset
    {sensitivity targetOffset : Real} (eta : NNReal)
    (hSensitivity : 0 < sensitivity) :
    Tendsto
      (fun horizon : Nat =>
        sensitivity /
            (fixedParticipationLowerStddevCandidate
              sensitivity targetOffset eta horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds (targetOffset + eta)) := by
  simpa [fixedParticipationLowerStddevCandidate] using
    tendsto_fixedParticipationStddevCandidate_offset
      (offset := targetOffset + eta) hSensitivity

theorem tendsto_fixedParticipationUpperStddevCandidate_offset
    {sensitivity targetOffset : Real} (eta : NNReal)
    (hSensitivity : 0 < sensitivity) :
    Tendsto
      (fun horizon : Nat =>
        sensitivity /
            (fixedParticipationUpperStddevCandidate
              sensitivity targetOffset eta horizon : Real) -
          gaussianCriticalScale horizon)
      atTop (nhds (targetOffset - eta)) := by
  simpa [fixedParticipationUpperStddevCandidate] using
    tendsto_fixedParticipationStddevCandidate_offset
      (offset := targetOffset - eta) hSensitivity

/-- A strictly positive tolerance makes the named lower-noise candidate
strictly smaller than the named higher-noise candidate eventually. -/
theorem eventually_fixedParticipationLowerStddevCandidate_lt_upper
    {sensitivity targetOffset : Real} (eta : NNReal)
    (hSensitivity : 0 < sensitivity) (hEta : 0 < eta) :
    ∀ᶠ horizon : Nat in atTop,
      fixedParticipationLowerStddevCandidate
          sensitivity targetOffset eta horizon <
        fixedParticipationUpperStddevCandidate
          sensitivity targetOffset eta horizon := by
  have hDenominators :=
    eventually_fixedOffset_denominators_pos targetOffset eta
  filter_upwards
    [eventually_coe_fixedParticipationLowerStddevCandidate eta hSensitivity,
      eventually_coe_fixedParticipationUpperStddevCandidate eta hSensitivity,
      hDenominators.1, hDenominators.2]
      with horizon hLower hUpper hUpperDenominator hLowerDenominator
  apply NNReal.coe_lt_coe.mp
  rw [hLower.2, hUpper.2]
  have hEtaReal : 0 < (eta : Real) := by exact_mod_cast hEta
  have hDenominatorOrder :
      gaussianCriticalScale horizon + targetOffset - (eta : Real) <
        gaussianCriticalScale horizon + targetOffset + (eta : Real) := by
    linarith
  have hQuotientOrder :=
    (div_lt_div_iff_of_pos_left hSensitivity
      hLowerDenominator hUpperDenominator).2 hDenominatorOrder
  simpa [add_assoc, sub_eq_add_neg] using hQuotientOrder

/-- The semantic finite-offset accountant theorem specialized to the explicit
fixed-offset candidate. -/
theorem tendsto_fixedParticipationStddevCandidate_profile
    (schedule : FixedParticipationSchedule)
    (sensitivity offset epsilon : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon) :
    Tendsto
      (fun horizon => sampledGaussianProductProfileStddev horizon
        (schedule.samplingRate horizon) (schedule.rate_le_one horizon)
        sensitivity
        (fixedParticipationStddevCandidate sensitivity offset horizon)
        epsilon)
      atTop (nhds (ENNReal.ofReal
        (1 - Real.exp (-(schedule.participationBudget : Real) *
          stdNormalCDFReal offset)))) := by
  apply tendsto_sampledGaussianProductProfileStddev_finiteOffset
    schedule sensitivity
      (fixedParticipationStddevCandidate sensitivity offset)
      offset epsilon hSensitivity hEpsilon
  · filter_upwards
      [eventually_coe_fixedParticipationStddevCandidate hSensitivity]
      with horizon hCandidate
    exact hCandidate.1
  · exact tendsto_fixedParticipationStddevCandidate_offset hSensitivity

theorem tendsto_fixedParticipationLowerStddevCandidate_profile
    (schedule : FixedParticipationSchedule)
    (sensitivity targetOffset : Real) (eta : NNReal) (epsilon : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon) :
    Tendsto
      (fun horizon => sampledGaussianProductProfileStddev horizon
        (schedule.samplingRate horizon) (schedule.rate_le_one horizon)
        sensitivity
        (fixedParticipationLowerStddevCandidate
          sensitivity targetOffset eta horizon)
        epsilon)
      atTop (nhds (ENNReal.ofReal
        (1 - Real.exp (-(schedule.participationBudget : Real) *
          stdNormalCDFReal (targetOffset + eta))))) := by
  simpa [fixedParticipationLowerStddevCandidate] using
    tendsto_fixedParticipationStddevCandidate_profile
      schedule sensitivity (targetOffset + eta) epsilon
      hSensitivity hEpsilon

theorem tendsto_fixedParticipationUpperStddevCandidate_profile
    (schedule : FixedParticipationSchedule)
    (sensitivity targetOffset : Real) (eta : NNReal) (epsilon : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon) :
    Tendsto
      (fun horizon => sampledGaussianProductProfileStddev horizon
        (schedule.samplingRate horizon) (schedule.rate_le_one horizon)
        sensitivity
        (fixedParticipationUpperStddevCandidate
          sensitivity targetOffset eta horizon)
        epsilon)
      atTop (nhds (ENNReal.ofReal
        (1 - Real.exp (-(schedule.participationBudget : Real) *
          stdNormalCDFReal (targetOffset - eta))))) := by
  simpa [fixedParticipationUpperStddevCandidate] using
    tendsto_fixedParticipationStddevCandidate_profile
      schedule sensitivity (targetOffset - eta) epsilon
      hSensitivity hEpsilon

end

end Mf.DP
