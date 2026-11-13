import Mathlib.Analysis.SpecialFunctions.Exp

/-!
# Signed exponential interval certificates

This owner turns exact rational Taylor endpoints into intervals for a signed
real exponential. A nonnegative magnitude is divided by a power of two until
the remainder lies in `[0, 1]`; the existing Mathlib Taylor bounds are then
raised through the exact dyadic scaling identity. Negative inputs use
reciprocal interval transport.

The theorem is neutral numerical infrastructure. It does not consume runtime
floating-point exponentials or assert that an arbitrary decimal library rounds
outward.
-/

open scoped BigOperators

set_option autoImplicit false

namespace Mf.Optimization.SDE
namespace DPAdamFixedBetaSignedExpIntervalCertificate

noncomputable section

/-- Lower Taylor polynomial used by the existing Gaussian product owner. -/
def expTaylorLower (remainder : ℝ) (order : ℕ) : ℝ :=
  ∑ index ∈ Finset.range order,
    remainder ^ index / index.factorial

/-- Upper Taylor expression from `Real.exp_bound'` on `[0, 1]`. -/
def expTaylorUpper (remainder : ℝ) (order : ℕ) : ℝ :=
  expTaylorLower remainder order +
    remainder ^ order * (order + 1) / (order.factorial * order)

/-- Exact rational lower endpoint emitted by a finite checker. -/
def expTaylorLowerRat (remainder : ℚ) (order : ℕ) : ℚ :=
  ∑ index ∈ Finset.range order,
    remainder ^ index / index.factorial

/-- Exact rational upper endpoint emitted by a finite checker. -/
def expTaylorUpperRat (remainder : ℚ) (order : ℕ) : ℚ :=
  expTaylorLowerRat remainder order +
    remainder ^ order * (order + 1) / (order.factorial * order)

/-- Rational remainder selected by dyadic range reduction. -/
def dyadicRemainder (magnitude : ℚ) (power : ℕ) : ℚ :=
  magnitude / ((2 ^ power : ℕ) : ℚ)

theorem dyadicRemainder_nonneg
    {magnitude : ℚ}
    (power : ℕ)
    (hmagnitude : 0 ≤ magnitude) :
    0 ≤ dyadicRemainder magnitude power := by
  unfold dyadicRemainder
  positivity

theorem dyadicRemainder_le_one
    {magnitude : ℚ}
    (power : ℕ)
    (hmagnitude : magnitude ≤ ((2 ^ power : ℕ) : ℚ)) :
    dyadicRemainder magnitude power ≤ 1 := by
  rw [dyadicRemainder, div_le_one]
  · exact hmagnitude
  · positivity

theorem twoPow_mul_dyadicRemainder
    (magnitude : ℚ)
    (power : ℕ) :
    ((2 ^ power : ℕ) : ℚ) * dyadicRemainder magnitude power =
      magnitude := by
  rw [dyadicRemainder, mul_div_cancel₀]
  positivity

@[simp] theorem expTaylorLowerRat_cast
    (remainder : ℚ) (order : ℕ) :
    ((expTaylorLowerRat remainder order : ℚ) : ℝ) =
      expTaylorLower (remainder : ℝ) order := by
  simp [expTaylorLowerRat, expTaylorLower]

@[simp] theorem expTaylorUpperRat_cast
    (remainder : ℚ) (order : ℕ) :
    ((expTaylorUpperRat remainder order : ℚ) : ℝ) =
      expTaylorUpper (remainder : ℝ) order := by
  simp [expTaylorUpperRat, expTaylorUpper]

/-- A positive-order lower Taylor endpoint is strictly positive for a
nonnegative remainder. This supplies the reciprocal branch's denominator. -/
theorem expTaylorLower_pos
    {remainder : ℝ} {order : ℕ}
    (hremainder : 0 ≤ remainder)
    (horder : 0 < order) :
    0 < expTaylorLower remainder order := by
  have hzero : 0 ∈ Finset.range order := Finset.mem_range.mpr horder
  have hterms :
      ∀ index ∈ Finset.range order,
        0 ≤ remainder ^ index / index.factorial := by
    intro index _hindex
    positivity
  have hone :
      (1 : ℝ) ≤
        ∑ index ∈ Finset.range order,
          remainder ^ index / index.factorial := by
    have hsingle :=
      Finset.single_le_sum
        (fun index (hindex : index ∈ Finset.range order) =>
          hterms index hindex)
        hzero
    simpa using hsingle
  exact lt_of_lt_of_le zero_lt_one (by
    simpa [expTaylorLower] using hone)

/-- Exact exponential scaling through multiplication by a power of two. -/
theorem exp_eq_pow_two_of_eq_twoPow_mul
    {value remainder : ℝ}
    (power : ℕ)
    (hvalue :
      value = ((2 ^ power : ℕ) : ℝ) * remainder) :
    Real.exp value = (Real.exp remainder) ^ (2 ^ power : ℕ) := by
  rw [hvalue]
  exact Real.exp_nat_mul remainder (2 ^ power)

theorem expTaylorLower_pow_two_le_exp_of_eq_twoPow_mul
    {value remainder : ℝ}
    (power order : ℕ)
    (hremainder : 0 ≤ remainder)
    (hvalue :
      value = ((2 ^ power : ℕ) : ℝ) * remainder) :
    (expTaylorLower remainder order) ^ (2 ^ power : ℕ) ≤
      Real.exp value := by
  have hlower :
      expTaylorLower remainder order ≤ Real.exp remainder := by
    simpa [expTaylorLower] using Real.sum_le_exp_of_nonneg hremainder order
  have hlower_nonneg :
      0 ≤ expTaylorLower remainder order := by
    unfold expTaylorLower
    exact Finset.sum_nonneg fun index _ =>
      div_nonneg (pow_nonneg hremainder index) (Nat.cast_nonneg index.factorial)
  rw [exp_eq_pow_two_of_eq_twoPow_mul power hvalue]
  exact pow_le_pow_left₀ hlower_nonneg hlower (2 ^ power)

theorem exp_le_expTaylorUpper_pow_two_of_eq_twoPow_mul
    {value remainder : ℝ}
    (power : ℕ)
    {order : ℕ}
    (hremainder0 : 0 ≤ remainder)
    (hremainder1 : remainder ≤ 1)
    (horder : 0 < order)
    (hvalue :
      value = ((2 ^ power : ℕ) : ℝ) * remainder) :
    Real.exp value ≤
      (expTaylorUpper remainder order) ^ (2 ^ power : ℕ) := by
  have hupper :
      Real.exp remainder ≤ expTaylorUpper remainder order := by
    simpa [expTaylorUpper, expTaylorLower] using
      Real.exp_bound' hremainder0 hremainder1 horder
  rw [exp_eq_pow_two_of_eq_twoPow_mul power hvalue]
  exact pow_le_pow_left₀ (Real.exp_pos remainder).le hupper (2 ^ power)

/-- Positive signed branch after exact dyadic range reduction. -/
theorem exp_mem_Icc_taylor_pow_two_of_eq_twoPow_mul
    {value remainder : ℝ}
    (power : ℕ)
    {order : ℕ}
    (hremainder0 : 0 ≤ remainder)
    (hremainder1 : remainder ≤ 1)
    (horder : 0 < order)
    (hvalue :
      value = ((2 ^ power : ℕ) : ℝ) * remainder) :
    Real.exp value ∈ Set.Icc
      ((expTaylorLower remainder order) ^ (2 ^ power : ℕ))
      ((expTaylorUpper remainder order) ^ (2 ^ power : ℕ)) := by
  exact ⟨
    expTaylorLower_pow_two_le_exp_of_eq_twoPow_mul
      power order hremainder0 hvalue,
    exp_le_expTaylorUpper_pow_two_of_eq_twoPow_mul
      power hremainder0 hremainder1 horder hvalue⟩

/-- Negative signed branch. Reciprocal monotonicity reverses the positive
Taylor endpoints. -/
theorem exp_neg_mem_Icc_reciprocal_taylor_pow_two_of_eq_twoPow_mul
    {value remainder : ℝ}
    (power : ℕ)
    {order : ℕ}
    (hremainder0 : 0 ≤ remainder)
    (hremainder1 : remainder ≤ 1)
    (horder : 0 < order)
    (hvalue :
      value = ((2 ^ power : ℕ) : ℝ) * remainder) :
    Real.exp (-value) ∈ Set.Icc
      (((expTaylorUpper remainder order) ^ (2 ^ power : ℕ))⁻¹)
      (((expTaylorLower remainder order) ^ (2 ^ power : ℕ))⁻¹) := by
  have hpositive :=
    exp_mem_Icc_taylor_pow_two_of_eq_twoPow_mul
      power hremainder0 hremainder1 horder hvalue
  have hlower_pos :
      0 <
        (expTaylorLower remainder order) ^ (2 ^ power : ℕ) :=
    pow_pos (expTaylorLower_pos hremainder0 horder) _
  constructor
  · have hupper_pos :
        0 < (expTaylorUpper remainder order) ^ (2 ^ power : ℕ) :=
      lt_of_lt_of_le (Real.exp_pos value) hpositive.2
    rw [Real.exp_neg]
    exact (inv_le_inv₀ hupper_pos (Real.exp_pos value)).2 hpositive.2
  · rw [Real.exp_neg]
    exact (inv_le_inv₀ (Real.exp_pos value) hlower_pos).2 hpositive.1

/-- Rational-facing signed interval certificate. A finite checker supplies a
nonnegative magnitude, a sign bit, a sufficient dyadic power, and a positive
Taylor order. -/
theorem exp_rat_signed_mem_Icc_taylor_of_nonneg_le_twoPow
    (magnitude : ℚ)
    (negative : Bool)
    (power : ℕ)
    {order : ℕ}
    (hmagnitude0 : 0 ≤ magnitude)
    (hmagnitudeUpper :
      magnitude ≤ ((2 ^ power : ℕ) : ℚ))
    (horder : 0 < order) :
    Real.exp
        (if negative then -(magnitude : ℝ) else (magnitude : ℝ)) ∈
      if negative then
        Set.Icc
          ((((expTaylorUpperRat
              (dyadicRemainder magnitude power) order : ℚ) : ℝ) ^
                (2 ^ power : ℕ))⁻¹)
          ((((expTaylorLowerRat
              (dyadicRemainder magnitude power) order : ℚ) : ℝ) ^
                (2 ^ power : ℕ))⁻¹)
      else
        Set.Icc
          (((expTaylorLowerRat
              (dyadicRemainder magnitude power) order : ℚ) : ℝ) ^
                (2 ^ power : ℕ))
          (((expTaylorUpperRat
              (dyadicRemainder magnitude power) order : ℚ) : ℝ) ^
                (2 ^ power : ℕ)) := by
  have hremainder0 :
      0 ≤ dyadicRemainder magnitude power :=
    dyadicRemainder_nonneg power hmagnitude0
  have hremainder1 :
      dyadicRemainder magnitude power ≤ 1 :=
    dyadicRemainder_le_one power hmagnitudeUpper
  have hscaleRat :
      magnitude =
        ((2 ^ power : ℕ) : ℚ) *
          dyadicRemainder magnitude power :=
    (twoPow_mul_dyadicRemainder magnitude power).symm
  have hscaleReal :
      (magnitude : ℝ) =
        ((2 ^ power : ℕ) : ℝ) *
          (dyadicRemainder magnitude power : ℝ) := by
    exact_mod_cast hscaleRat
  cases negative
  · have hpositive :=
      exp_mem_Icc_taylor_pow_two_of_eq_twoPow_mul
        (value := (magnitude : ℝ))
        (remainder := (dyadicRemainder magnitude power : ℝ))
        power
        (by exact_mod_cast hremainder0)
        (by exact_mod_cast hremainder1)
        horder hscaleReal
    simpa using hpositive
  · have hnegative :=
      exp_neg_mem_Icc_reciprocal_taylor_pow_two_of_eq_twoPow_mul
        (value := (magnitude : ℝ))
        (remainder := (dyadicRemainder magnitude power : ℝ))
        power
        (by exact_mod_cast hremainder0)
        (by exact_mod_cast hremainder1)
        horder hscaleReal
    simpa using hnegative

/-- Monotonic endpoint composition turns point certificates into an interval
certificate for every input between the supplied endpoints. -/
theorem exp_mem_Icc_of_mem_Icc_of_endpoint_bounds
    {inputLower inputUpper outputLower outputUpper value : ℝ}
    (hvalue : value ∈ Set.Icc inputLower inputUpper)
    (hlower : outputLower ≤ Real.exp inputLower)
    (hupper : Real.exp inputUpper ≤ outputUpper) :
    Real.exp value ∈ Set.Icc outputLower outputUpper := by
  exact ⟨
    hlower.trans (Real.exp_le_exp.mpr hvalue.1),
    (Real.exp_le_exp.mpr hvalue.2).trans hupper⟩

end

end DPAdamFixedBetaSignedExpIntervalCertificate
end Mf.Optimization.SDE
