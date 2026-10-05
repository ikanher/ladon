import Mathlib

/-!
# Gaussian critical and null-truncation scales

This module owns the deterministic scales used for sparse Gaussian products at
finite expected participation. Definitions are total at horizons zero and one;
the displayed analytic formulas and inequalities are stated eventually, where
all logarithms and denominators have their intended positive domain.
-/

open Filter
open scoped Topology

namespace Mf.DP

noncomputable section

/-- Critical maximum scale `sqrt (2 log T)`, total at every natural horizon. -/
def gaussianCriticalScale (horizon : Nat) : Real :=
  Real.sqrt (2 * Real.log (horizon : Real))

/-- Null truncation scale, totalized to zero before horizon two. -/
def gaussianNullTruncationScale (horizon : Nat) : Real :=
  if 2 ≤ horizon then
    let critical := gaussianCriticalScale horizon
    critical - Real.log critical / (2 * critical)
  else 0

theorem tendsto_gaussianCriticalScale_atTop :
    Tendsto gaussianCriticalScale atTop atTop := by
  unfold gaussianCriticalScale
  have hCast : Tendsto (fun horizon : Nat => (horizon : Real)) atTop atTop :=
    tendsto_natCast_atTop_atTop
  have hLog : Tendsto (fun horizon : Nat => Real.log (horizon : Real)) atTop atTop :=
    Real.tendsto_log_atTop.comp hCast
  have hScaled : Tendsto
      (fun horizon : Nat => (2 : Real) * Real.log (horizon : Real)) atTop atTop := by
    simpa [mul_comm] using hLog.atTop_mul_const (by norm_num : (0 : Real) < 2)
  exact Real.tendsto_sqrt_atTop.comp hScaled

theorem eventually_gaussianCriticalScale_pos :
    ∀ᶠ horizon : Nat in atTop, 0 < gaussianCriticalScale horizon := by
  filter_upwards [eventually_ge_atTop 2] with horizon hHorizon
  unfold gaussianCriticalScale
  apply Real.sqrt_pos.2
  apply mul_pos (by norm_num)
  apply Real.log_pos
  exact_mod_cast (show (1 : Nat) < horizon by omega)

theorem eventually_gaussianCriticalScale_sq :
    ∀ᶠ horizon : Nat in atTop,
      gaussianCriticalScale horizon ^ 2 =
        2 * Real.log (horizon : Real) := by
  filter_upwards [eventually_gaussianCriticalScale_pos] with horizon hCritical
  unfold gaussianCriticalScale
  rw [Real.sq_sqrt]
  positivity

/-- The total truncation wrapper agrees eventually with its analytic formula. -/
theorem eventually_gaussianNullTruncationScale_eq :
    ∀ᶠ horizon : Nat in atTop,
      gaussianNullTruncationScale horizon =
        gaussianCriticalScale horizon -
          Real.log (gaussianCriticalScale horizon) /
            (2 * gaussianCriticalScale horizon) := by
  filter_upwards [eventually_ge_atTop 2] with horizon hHorizon
  simp [gaussianNullTruncationScale, hHorizon]

theorem tendsto_gaussianCriticalScale_log_div_self_zero :
    Tendsto
      (fun horizon : Nat =>
        Real.log (gaussianCriticalScale horizon) /
          (2 * gaussianCriticalScale horizon))
      atTop (𝓝 0) := by
  have hRatio : Tendsto
      (fun horizon : Nat =>
        Real.log (gaussianCriticalScale horizon) /
          gaussianCriticalScale horizon) atTop (𝓝 0) :=
    Real.isLittleO_log_id_atTop.tendsto_div_nhds_zero.comp
      tendsto_gaussianCriticalScale_atTop
  simpa [div_eq_mul_inv, mul_assoc, mul_comm, mul_left_comm] using
    hRatio.const_mul (1 / 2 : Real)

theorem eventually_gaussianNullTruncationScale_lt_critical :
    ∀ᶠ horizon : Nat in atTop,
      gaussianNullTruncationScale horizon < gaussianCriticalScale horizon := by
  filter_upwards
    [eventually_gaussianNullTruncationScale_eq,
      tendsto_gaussianCriticalScale_atTop.eventually (eventually_gt_atTop 1)] with
      horizon hFormula hCritical
  rw [hFormula]
  have hLog : 0 < Real.log (gaussianCriticalScale horizon) := Real.log_pos hCritical
  have hCorrection : 0 < Real.log (gaussianCriticalScale horizon) /
      (2 * gaussianCriticalScale horizon) := div_pos hLog (by positivity)
  linarith

theorem tendsto_gaussianNullTruncationScale_atTop :
    Tendsto gaussianNullTruncationScale atTop atTop := by
  have hLower : ∀ᶠ horizon : Nat in atTop,
      gaussianCriticalScale horizon - (1 / 2 : Real) ≤
        gaussianNullTruncationScale horizon := by
    filter_upwards
      [eventually_gaussianNullTruncationScale_eq,
        eventually_gaussianCriticalScale_pos] with horizon hFormula hCritical
    rw [hFormula]
    have hLog := Real.log_le_self hCritical.le
    have hCorrection : Real.log (gaussianCriticalScale horizon) /
        (2 * gaussianCriticalScale horizon) ≤ (1 / 2 : Real) := by
      apply (div_le_iff₀ (by positivity)).2
      nlinarith
    linarith
  refine Filter.tendsto_atTop_mono' atTop hLower ?_
  simpa only [sub_eq_add_neg] using
    Filter.tendsto_atTop_add_const_right atTop (- (1 / 2 : Real))
      tendsto_gaussianCriticalScale_atTop

theorem tendsto_gaussianCriticalScale_sub_truncation_zero :
    Tendsto
      (fun horizon : Nat =>
        gaussianCriticalScale horizon - gaussianNullTruncationScale horizon)
      atTop (𝓝 0) := by
  apply tendsto_gaussianCriticalScale_log_div_self_zero.congr'
  filter_upwards [eventually_gaussianNullTruncationScale_eq] with horizon hFormula
  rw [hFormula]
  ring

/-- Exact completing-square identity controlling the null maximum. -/
theorem eventually_nullTruncation_exponent_identity :
    ∀ᶠ horizon : Nat in atTop,
      Real.log (horizon : Real) - gaussianNullTruncationScale horizon ^ 2 / 2 =
        Real.log (gaussianCriticalScale horizon) / 2 -
          Real.log (gaussianCriticalScale horizon) ^ 2 /
            (8 * gaussianCriticalScale horizon ^ 2) := by
  filter_upwards
    [eventually_gaussianNullTruncationScale_eq,
      eventually_gaussianCriticalScale_sq,
      eventually_gaussianCriticalScale_pos] with horizon hFormula hSquare hPositive
  rw [hFormula]
  field_simp [ne_of_gt hPositive]
  nlinarith

/-- Exact completing-square identity for the shifted truncated second moment. -/
theorem eventually_shiftedTruncation_secondMoment_exponent_identity
    (offset : Real) :
    ∀ᶠ horizon : Nat in atTop,
      (gaussianCriticalScale horizon + offset) ^ 2 -
          (gaussianNullTruncationScale horizon -
            2 * (gaussianCriticalScale horizon + offset)) ^ 2 / 2 =
        Real.log (horizon : Real) - offset ^ 2 -
          Real.log (gaussianCriticalScale horizon) / 2 -
          Real.log (gaussianCriticalScale horizon) * offset /
            gaussianCriticalScale horizon -
          Real.log (gaussianCriticalScale horizon) ^ 2 /
            (8 * gaussianCriticalScale horizon ^ 2) := by
  filter_upwards
    [eventually_gaussianNullTruncationScale_eq,
      eventually_gaussianCriticalScale_sq,
      eventually_gaussianCriticalScale_pos] with horizon hFormula hSquare hPositive
  rw [hFormula]
  field_simp [ne_of_gt hPositive]
  nlinarith

/-- A finite offset from the diverging critical scale also diverges and is
eventually positive. -/
theorem tendsto_standardizedShift_atTop_of_sub_critical_tendsto
    (standardizedShift : Nat → Real) (offset : Real)
    (hOffset : Tendsto
      (fun horizon : Nat =>
        standardizedShift horizon - gaussianCriticalScale horizon)
      atTop (𝓝 offset)) :
    Tendsto standardizedShift atTop atTop := by
  have hSum := hOffset.add_atTop tendsto_gaussianCriticalScale_atTop
  apply hSum.congr'
  filter_upwards [] with horizon
  ring

theorem eventually_standardizedShift_pos_of_sub_critical_tendsto
    (standardizedShift : Nat → Real) (offset : Real)
    (hOffset : Tendsto
      (fun horizon : Nat =>
        standardizedShift horizon - gaussianCriticalScale horizon)
      atTop (𝓝 offset)) :
    ∀ᶠ horizon : Nat in atTop, 0 < standardizedShift horizon :=
  (tendsto_standardizedShift_atTop_of_sub_critical_tendsto
    standardizedShift offset hOffset).eventually (eventually_gt_atTop 0)

/-- Both fixed-offset candidate denominators are eventually positive. -/
theorem eventually_fixedOffset_denominators_pos
    (offset tolerance : Real) :
    (∀ᶠ horizon : Nat in atTop,
      0 < gaussianCriticalScale horizon + offset - tolerance) ∧
    (∀ᶠ horizon : Nat in atTop,
      0 < gaussianCriticalScale horizon + offset + tolerance) := by
  constructor
  · filter_upwards
      [tendsto_gaussianCriticalScale_atTop.eventually
        (eventually_gt_atTop (tolerance - offset))] with horizon hCritical
    linarith
  · filter_upwards
      [tendsto_gaussianCriticalScale_atTop.eventually
        (eventually_gt_atTop (-offset - tolerance))] with horizon hCritical
    linarith

/-- Positive-infinite offset implies positive-infinite standardized shift. -/
theorem tendsto_standardizedShift_atTop_of_sub_critical_atTop
    (standardizedShift : Nat → Real)
    (hOffset : Tendsto
      (fun horizon : Nat =>
        standardizedShift horizon - gaussianCriticalScale horizon)
      atTop atTop) :
    Tendsto standardizedShift atTop atTop := by
  have hSum := hOffset.atTop_add_atTop tendsto_gaussianCriticalScale_atTop
  apply hSum.congr'
  filter_upwards [] with horizon
  ring

/-- Negative-infinite offset is equivalently a positive-infinite critical gap. -/
theorem tendsto_critical_sub_standardizedShift_atTop_of_sub_critical_atBot
    (standardizedShift : Nat → Real)
    (hOffset : Tendsto
      (fun horizon : Nat =>
        standardizedShift horizon - gaussianCriticalScale horizon)
      atTop atBot) :
    Tendsto
      (fun horizon : Nat =>
        gaussianCriticalScale horizon - standardizedShift horizon)
      atTop atTop := by
  simpa only [neg_sub] using (tendsto_neg_atTop_iff.mpr hOffset)

end

end Mf.DP
