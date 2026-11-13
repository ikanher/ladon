import Mf.DP.Profile.RationalOutwardInterval
import Mf.CertifiedNumerics.SignedExpTaylor

namespace Mf
namespace DP

/-!
# Outward rational intervals for the real exponential

This module gives a neutral interface to the existing signed Taylor
construction.  A stage supplies a dyadic range-reduction power and a positive
Taylor order.  All endpoints are exact rationals.
-/

namespace RationalExpInterval

open Mf.Optimization.SDE.DPAdamFixedBetaSignedExpIntervalCertificate

/-- Absolute rational input used by dyadic range reduction. -/
def magnitude (x : ℚ) : ℚ := |x|

/-- Lower endpoint for a nonnegative input magnitude. -/
def positiveLower (x : ℚ) (power order : ℕ) : ℚ :=
  (expTaylorLowerRat (dyadicRemainder (magnitude x) power) order) ^
    (2 ^ power : ℕ)

/-- Upper endpoint for a nonnegative input magnitude. -/
def positiveUpper (x : ℚ) (power order : ℕ) : ℚ :=
  (expTaylorUpperRat (dyadicRemainder (magnitude x) power) order) ^
    (2 ^ power : ℕ)

/--
Signed exponential interval.  Negative inputs use the reciprocal interval,
with endpoint order reversed.
-/
def interval (x : ℚ) (power order : ℕ) : RationalOutwardInterval :=
  if x < 0 then
    ⟨(positiveUpper x power order)⁻¹,
      (positiveLower x power order)⁻¹⟩
  else
    ⟨positiveLower x power order, positiveUpper x power order⟩

/-- The lower endpoint of every positive-order exponential interval is
strictly positive.  This sign fact is useful when subsequent certified
arithmetic treats exponential images as nonnegative intervals. -/
theorem interval_lower_pos
    (x : ℚ) (power order : ℕ) (horder : 0 < order) :
    0 < (interval x power order).lower := by
  have hremainder :
      0 ≤ dyadicRemainder (magnitude x) power :=
    dyadicRemainder_nonneg power (abs_nonneg x)
  have hlower :
      0 < expTaylorLowerRat (dyadicRemainder (magnitude x) power) order := by
    have hreal :
        0 < (expTaylorLowerRat
          (dyadicRemainder (magnitude x) power) order : ℝ) := by
      rw [expTaylorLowerRat_cast]
      exact expTaylorLower_pos (by exact_mod_cast hremainder) horder
    exact_mod_cast hreal
  have hupper :
      0 < expTaylorUpperRat (dyadicRemainder (magnitude x) power) order := by
    unfold expTaylorUpperRat
    have htail :
        0 ≤ dyadicRemainder (magnitude x) power ^ order * (order + 1) /
          (order.factorial * order) := by
      positivity
    linarith
  by_cases hx : x < 0
  · simp only [interval, hx, if_true]
    exact inv_pos.mpr (pow_pos hupper _)
  · simp only [interval, hx, if_false, positiveLower]
    exact pow_pos hlower _

theorem magnitude_nonnegative (x : ℚ) :
    0 ≤ magnitude x := abs_nonneg x

/-- A sufficient dyadic power for the exact rational input. -/
def PowerSufficient (x : ℚ) (power : ℕ) : Prop :=
  magnitude x ≤ ((2 ^ power : ℕ) : ℚ)

instance (x : ℚ) (power : ℕ) : Decidable (PowerSufficient x power) := by
  unfold PowerSufficient
  infer_instance

/--
A power sufficient for a nonnegative upper input is sufficient for every
nonnegative smaller input. This lets certificate replay validate one public
range-reduction cap instead of every element of a finite family.
-/
theorem powerSufficient_of_nonnegative_le
    {x upper : ℚ}
    {power : ℕ}
    (hx : 0 ≤ x)
    (hxu : x ≤ upper)
    (hupper : PowerSufficient upper power) :
    PowerSufficient x power := by
  have hu : 0 ≤ upper := hx.trans hxu
  unfold PowerSufficient magnitude at hupper ⊢
  rw [abs_of_nonneg hu] at hupper
  rw [abs_of_nonneg hx]
  exact hxu.trans hupper

/--
Monotone exponential image of a rational input interval.  Only the lower
endpoint of the lower exponential interval and the upper endpoint of the
upper exponential interval are retained.
-/
def ofInputInterval
    (input : RationalOutwardInterval)
    (power order : ℕ) :
    RationalOutwardInterval :=
  ⟨(interval input.lower power order).lower,
    (interval input.upper power order).upper⟩

private theorem input_eq_signed_magnitude_of_nonnegative
    {x : ℚ} (hx : ¬x < 0) :
    (x : ℝ) = (magnitude x : ℝ) := by
  have hx0 : 0 ≤ x := le_of_not_gt hx
  simp [magnitude, abs_of_nonneg hx0]

private theorem input_eq_signed_magnitude_of_negative
    {x : ℚ} (hx : x < 0) :
    (x : ℝ) = -(magnitude x : ℝ) := by
  have hx0 : x ≤ 0 := le_of_lt hx
  simp [magnitude, abs_of_nonpos hx0]

/--
Every valid stage encloses the exact real exponential of the rational input.
-/
theorem interval_encloses
    (x : ℚ)
    (power order : ℕ)
    (hpower : PowerSufficient x power)
    (horder : 0 < order) :
    (interval x power order).Encloses (Real.exp (x : ℝ)) := by
  have hbase :=
    exp_rat_signed_mem_Icc_taylor_of_nonneg_le_twoPow
      (magnitude x) (decide (x < 0)) power
      (magnitude_nonnegative x) hpower horder
  by_cases hx : x < 0
  · simp only [decide_eq_true hx, if_true] at hbase
    rw [input_eq_signed_magnitude_of_negative hx]
    simp only [interval, hx, if_true, RationalOutwardInterval.Encloses]
    change
      (((positiveUpper x power order)⁻¹ : ℚ) : ℝ) ≤
          Real.exp (-(magnitude x : ℝ)) ∧
        Real.exp (-(magnitude x : ℝ)) ≤
          (((positiveLower x power order)⁻¹ : ℚ) : ℝ)
    simpa only [
      positiveLower,
      positiveUpper,
      Rat.cast_inv,
      Rat.cast_pow,
      expTaylorLowerRat_cast,
      expTaylorUpperRat_cast,
      Set.mem_Icc,
    ] using hbase
  · simp only [decide_eq_false hx, Bool.false_eq_true, if_false] at hbase
    rw [input_eq_signed_magnitude_of_nonnegative hx]
    simp only [interval, hx, if_false, RationalOutwardInterval.Encloses]
    change
      ((positiveLower x power order : ℚ) : ℝ) ≤
          Real.exp (magnitude x : ℝ) ∧
        Real.exp (magnitude x : ℝ) ≤
          ((positiveUpper x power order : ℚ) : ℝ)
    simpa only [
      positiveLower,
      positiveUpper,
      Rat.cast_pow,
      expTaylorLowerRat_cast,
      expTaylorUpperRat_cast,
      Set.mem_Icc,
    ] using hbase

/-- Sound exponential stages always have ordered endpoints. -/
theorem interval_valid
    (x : ℚ)
    (power order : ℕ)
    (hpower : PowerSufficient x power)
    (horder : 0 < order) :
    (interval x power order).Valid :=
  by
    have hencloses := interval_encloses x power order hpower horder
    exact_mod_cast (hencloses.1.trans hencloses.2)

/-- The monotone interval image encloses `exp value`. -/
theorem ofInputInterval_encloses
    {input : RationalOutwardInterval}
    {value : ℝ}
    (power order : ℕ)
    (hinput : input.Encloses value)
    (hlowerPower : PowerSufficient input.lower power)
    (hupperPower : PowerSufficient input.upper power)
    (horder : 0 < order) :
    (ofInputInterval input power order).Encloses (Real.exp value) := by
  have hlower :=
    interval_encloses input.lower power order hlowerPower horder
  have hupper :=
    interval_encloses input.upper power order hupperPower horder
  constructor
  · exact hlower.1.trans
      (Real.exp_le_exp.mpr hinput.1)
  · exact (Real.exp_le_exp.mpr hinput.2).trans hupper.2

/-- Sound monotone exponential images have ordered endpoints. -/
theorem ofInputInterval_valid
    {input : RationalOutwardInterval}
    {value : ℝ}
    (power order : ℕ)
    (hinput : input.Encloses value)
    (hlowerPower : PowerSufficient input.lower power)
    (hupperPower : PowerSufficient input.upper power)
    (horder : 0 < order) :
    (ofInputInterval input power order).Valid := by
  have hencloses :=
    ofInputInterval_encloses power order hinput
      hlowerPower hupperPower horder
  exact_mod_cast (hencloses.1.trans hencloses.2)

end RationalExpInterval

end DP
end Mf
