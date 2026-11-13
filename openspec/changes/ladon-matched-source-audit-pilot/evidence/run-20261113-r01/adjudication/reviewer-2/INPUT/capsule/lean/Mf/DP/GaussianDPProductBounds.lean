import Mf.DP.GaussianCore
import Mathlib.Analysis.Real.Pi.Bounds

/-!
# Certified product-bound helpers for Gaussian scalar rows

This module isolates small theorem-facing interval facts needed by generated
scalar-row packages.  It does not mention a particular scalar CDF proof family:
Mills, interval rows, or future CDF backends can use these helpers to turn
certified exponential and rational-factor bounds into bounds on products with
`stdNormalPdfReal`.
-/

namespace Mf
namespace DP

noncomputable section

/-- Taylor lower bound for `exp x` at nonnegative `x`. -/
theorem exp_taylor_lower_of_nonneg
    {x : ℝ}
    (hx : 0 ≤ x)
    (n : ℕ) :
    (∑ i ∈ Finset.range n, x ^ i / i.factorial) ≤ Real.exp x :=
  Real.sum_le_exp_of_nonneg hx n

/-- Taylor upper bound for `exp x` on the unit interval. -/
theorem exp_taylor_upper_of_mem_unit
    {x : ℝ}
    (hx0 : 0 ≤ x)
    (hx1 : x ≤ 1)
    {n : ℕ}
    (hn : 0 < n) :
    Real.exp x ≤
      (∑ i ∈ Finset.range n, x ^ i / i.factorial) +
        x ^ n * (n + 1) / (n.factorial * n) :=
  Real.exp_bound' hx0 hx1 hn

/--
Turn any positive lower bound on `exp A` into an upper bound on `exp (-A)`.

This is useful for row-local Taylor lower sums: Mathlib's
`Real.sum_le_exp_of_nonneg` can prove `S ≤ exp A`, and this lemma converts that
fact into `exp (-A) ≤ S⁻¹`.
-/
theorem exp_neg_le_inv_of_le_exp
    {A expLower : ℝ}
    (hexpLower_pos : 0 < expLower)
    (hexpLower_le : expLower ≤ Real.exp A) :
    Real.exp (-A) ≤ expLower⁻¹ := by
  rw [Real.exp_neg]
  exact (inv_le_inv₀ (Real.exp_pos A) hexpLower_pos).2 hexpLower_le

/--
Turn any upper bound on `exp A` into a lower bound on `exp (-A)`.

This is the companion to `exp_neg_le_inv_of_le_exp` for future row-local
Taylor upper bounds on `exp A`.
-/
theorem inv_le_exp_neg_of_exp_le
    {A expUpper : ℝ}
    (hexpUpper : Real.exp A ≤ expUpper) :
    expUpper⁻¹ ≤ Real.exp (-A) := by
  have hexpUpper_pos : 0 < expUpper :=
    lt_of_lt_of_le (Real.exp_pos A) hexpUpper
  rw [Real.exp_neg]
  exact (inv_le_inv₀ hexpUpper_pos (Real.exp_pos A)).2 hexpUpper

/--
Lower-bound `exp (n + r)` from separate lower bounds on `exp 1` and `exp r`.

Generated row-local interval proofs can use this after splitting
`x^2/2 = n + r` with `0 ≤ r ≤ 1`.
-/
theorem exp_nat_add_lower_bound
    (n : ℕ) {r expOneLower expRLower : ℝ}
    (hone_nonneg : 0 ≤ expOneLower)
    (hr_nonneg : 0 ≤ expRLower)
    (hone : expOneLower ≤ Real.exp 1)
    (hr : expRLower ≤ Real.exp r) :
    expOneLower ^ n * expRLower ≤ Real.exp ((n : ℝ) + r) := by
  have hpown : expOneLower ^ n ≤ Real.exp 1 ^ n :=
    pow_le_pow_left₀ hone_nonneg hone n
  have htrue_pow_nonneg : 0 ≤ Real.exp 1 ^ n :=
    pow_nonneg (Real.exp_pos 1).le n
  calc
    expOneLower ^ n * expRLower
        ≤ Real.exp 1 ^ n * Real.exp r :=
      mul_le_mul hpown hr hr_nonneg htrue_pow_nonneg
    _ = Real.exp ((n : ℝ) + r) := by
      rw [← Real.exp_nat_mul, ← Real.exp_add]
      congr 1
      ring

/--
Upper-bound `exp (n + r)` from separate upper bounds on `exp 1` and `exp r`.
-/
theorem exp_nat_add_upper_bound
    (n : ℕ) {r expOneUpper expRUpper : ℝ}
    (hone : Real.exp 1 ≤ expOneUpper)
    (hr : Real.exp r ≤ expRUpper) :
    Real.exp ((n : ℝ) + r) ≤ expOneUpper ^ n * expRUpper := by
  have hone_upper_nonneg : 0 ≤ expOneUpper :=
    le_trans (Real.exp_pos 1).le hone
  have hpown : Real.exp 1 ^ n ≤ expOneUpper ^ n :=
    pow_le_pow_left₀ (Real.exp_pos 1).le hone n
  calc
    Real.exp ((n : ℝ) + r)
        = Real.exp 1 ^ n * Real.exp r := by
      rw [← Real.exp_nat_mul, ← Real.exp_add]
      congr 1
      ring
    _ ≤ expOneUpper ^ n * expRUpper :=
      mul_le_mul hpown hr (Real.exp_pos r).le
        (pow_nonneg hone_upper_nonneg n)

/--
Upper-bound `exp x` by first bounding `x ≤ n + r`, then using certified
upper bounds for `exp 1` and `exp r`.

Generated finite-grid rows use this to turn rational endpoint arithmetic into
the exponential upper bounds consumed by box-envelope certificates.
-/
theorem exp_le_of_le_nat_add_unit_upper
    {x r expOneUpper expRUpper upper : ℝ}
    (n : ℕ)
    (hx : x ≤ (n : ℝ) + r)
    (hone : Real.exp 1 ≤ expOneUpper)
    (hr : Real.exp r ≤ expRUpper)
    (hupper : expOneUpper ^ n * expRUpper ≤ upper) :
    Real.exp x ≤ upper := by
  exact le_trans (Real.exp_le_exp.mpr hx)
    (le_trans (exp_nat_add_upper_bound n hone hr) hupper)

/--
Lower-bound `exp x` by first proving `n + r ≤ x`, then using certified lower
bounds for `exp 1` and `exp r`.

This is the lower-bound companion used by reverse box-envelope rows.
-/
theorem lower_le_exp_of_nat_add_unit_lower
    {x r expOneLower expRLower lower : ℝ}
    (n : ℕ)
    (hx : (n : ℝ) + r ≤ x)
    (hone_nonneg : 0 ≤ expOneLower)
    (hr_nonneg : 0 ≤ expRLower)
    (hone : expOneLower ≤ Real.exp 1)
    (hr : expRLower ≤ Real.exp r)
    (hlower : lower ≤ expOneLower ^ n * expRLower) :
    lower ≤ Real.exp x := by
  exact le_trans hlower
    (le_trans
      (exp_nat_add_lower_bound n hone_nonneg hr_nonneg hone hr)
      (Real.exp_le_exp.mpr hx))

/--
Upper-bound `exp (-x)` by lower-bounding `exp x` through a certified
`n + r` split.

This is the shape needed for local Gaussian reference-density envelopes:
`exp (-sqLower / (2σ²))` is bounded by the inverse of a certified lower bound
on `exp (sqLower / (2σ²))`.
-/
theorem exp_neg_le_of_nat_add_unit_lower
    {x r expOneLower expRLower upper : ℝ}
    (n : ℕ)
    (hx : (n : ℝ) + r ≤ x)
    (hone_nonneg : 0 ≤ expOneLower)
    (hr_nonneg : 0 ≤ expRLower)
    (hone : expOneLower ≤ Real.exp 1)
    (hr : expRLower ≤ Real.exp r)
    (hpos : 0 < expOneLower ^ n * expRLower)
    (hupper : (expOneLower ^ n * expRLower)⁻¹ ≤ upper) :
    Real.exp (-x) ≤ upper := by
  have hLower :
      expOneLower ^ n * expRLower ≤ Real.exp x :=
    le_trans
      (exp_nat_add_lower_bound n hone_nonneg hr_nonneg hone hr)
      (Real.exp_le_exp.mpr hx)
  exact le_trans (exp_neg_le_inv_of_le_exp hpos hLower) hupper

/--
Lower-bound `exp (-x)` by upper-bounding `exp x` through a certified
`n + r` split.

This is useful when a generated row wants a nontrivial lower bound for a
negative likelihood-ratio exponent.
-/
theorem lower_le_exp_neg_of_le_nat_add_unit_upper
    {x r expOneUpper expRUpper lower : ℝ}
    (n : ℕ)
    (hx : x ≤ (n : ℝ) + r)
    (hone : Real.exp 1 ≤ expOneUpper)
    (hr : Real.exp r ≤ expRUpper)
    (hlower : lower ≤ (expOneUpper ^ n * expRUpper)⁻¹) :
    lower ≤ Real.exp (-x) := by
  have hUpper :
      Real.exp x ≤ expOneUpper ^ n * expRUpper :=
    le_trans (Real.exp_le_exp.mpr hx)
      (exp_nat_add_upper_bound n hone hr)
  exact le_trans hlower (inv_le_exp_neg_of_exp_le hUpper)

/-- A tight rational upper bound on the standard-normal density normalizer. -/
theorem inv_sqrt_two_mul_pi_le_399_div_1000 :
    (Real.sqrt (2 * Real.pi))⁻¹ ≤ (399 : ℝ) / 1000 := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [inv_le_comm₀ hpos (by norm_num : (0 : ℝ) < (399 : ℝ) / 1000)]
  norm_num
  rw [← Real.sqrt_mul (x := (2 : ℝ)) (y := Real.pi) (by norm_num)]
  rw [Real.le_sqrt (by norm_num : (0 : ℝ) ≤ (1000 : ℝ) / 399) (by positivity)]
  nlinarith [Real.pi_gt_d4]

/-- A tight rational lower bound on the standard-normal density normalizer. -/
theorem inv_sqrt_two_mul_pi_ge_3989_div_10000 :
    (3989 : ℝ) / 10000 ≤ (Real.sqrt (2 * Real.pi))⁻¹ := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [le_inv_comm₀ (by norm_num : (0 : ℝ) < (3989 : ℝ) / 10000) hpos]
  norm_num
  rw [← Real.sqrt_mul (x := (2 : ℝ)) (y := Real.pi) (by norm_num)]
  rw [Real.sqrt_le_left (by norm_num : (0 : ℝ) ≤ (10000 : ℝ) / 3989)]
  nlinarith [Real.pi_lt_d4]

/--
Ten-decimal rational upper bound on the standard-normal density normalizer.

The selected count-bucket scalar margins are small enough that the coarse
`399/1000` bound is only useful as a smoke lemma; row-local product intervals
should use this tighter bound or a generated refinement.
-/
theorem inv_sqrt_two_mul_pi_le_3989422805_div_10000000000 :
    (Real.sqrt (2 * Real.pi))⁻¹ ≤ (3989422805 : ℝ) / 10000000000 := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [inv_le_comm₀ hpos
    (by norm_num : (0 : ℝ) < (3989422805 : ℝ) / 10000000000)]
  norm_num
  rw [← Real.sqrt_mul (x := (2 : ℝ)) (y := Real.pi) (by norm_num)]
  rw [Real.le_sqrt (by norm_num : (0 : ℝ) ≤ (2000000000 : ℝ) / 797884561)
    (by positivity)]
  nlinarith [Real.pi_gt_d20]

/-- Ten-decimal rational lower bound on the standard-normal density normalizer. -/
theorem inv_sqrt_two_mul_pi_ge_3989422804_div_10000000000 :
    (3989422804 : ℝ) / 10000000000 ≤ (Real.sqrt (2 * Real.pi))⁻¹ := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [le_inv_comm₀
    (by norm_num : (0 : ℝ) < (3989422804 : ℝ) / 10000000000) hpos]
  norm_num
  rw [← Real.sqrt_mul (x := (2 : ℝ)) (y := Real.pi) (by norm_num)]
  rw [Real.sqrt_le_left
    (by norm_num : (0 : ℝ) ≤ (2500000000 : ℝ) / 997355701)]
  nlinarith [Real.pi_lt_d20]

/--
Fourteen-decimal rational upper bound on the standard-normal density
normalizer.

This is tight enough for the selected symbolic-Mills aggregate margins.
-/
theorem inv_sqrt_two_mul_pi_le_39894228040144_div_100000000000000 :
    (Real.sqrt (2 * Real.pi))⁻¹ ≤
      (39894228040144 : ℝ) / 100000000000000 := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [inv_le_comm₀ hpos
    (by norm_num : (0 : ℝ) < (39894228040144 : ℝ) / 100000000000000)]
  norm_num
  rw [← Real.sqrt_mul (x := (2 : ℝ)) (y := Real.pi) (by norm_num)]
  rw [Real.le_sqrt (by positivity) (by positivity)]
  nlinarith [Real.pi_gt_d20]

/-- Fourteen-decimal rational lower bound on the standard-normal density normalizer. -/
theorem inv_sqrt_two_mul_pi_ge_39894228040143_div_100000000000000 :
    (39894228040143 : ℝ) / 100000000000000 ≤
      (Real.sqrt (2 * Real.pi))⁻¹ := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [le_inv_comm₀
    (by norm_num : (0 : ℝ) < (39894228040143 : ℝ) / 100000000000000) hpos]
  norm_num
  rw [← Real.sqrt_mul (x := (2 : ℝ)) (y := Real.pi) (by norm_num)]
  rw [Real.sqrt_le_left (by positivity)]
  nlinarith [Real.pi_lt_d20]

/--
Upper-bound the standard-normal density from an upper bound on the exponential
factor `exp (-(x^2)/2)`.
-/
theorem stdNormalPdfReal_le_of_exp_neg_sq_half_le
    {x expUpper : ℝ}
    (hexp : Real.exp (-(x ^ 2) / 2) ≤ expUpper) :
    stdNormalPdfReal x ≤
      expUpper * ((39894228040144 : ℝ) / 100000000000000) := by
  unfold stdNormalPdfReal
  rw [div_eq_mul_inv]
  have hnorm_nonneg : 0 ≤ (Real.sqrt (2 * Real.pi))⁻¹ := by positivity
  have hexp_nonneg : 0 ≤ Real.exp (-(x ^ 2) / 2) := (Real.exp_pos _).le
  have hexpUpper_nonneg : 0 ≤ expUpper :=
    le_trans hexp_nonneg hexp
  exact mul_le_mul hexp
    inv_sqrt_two_mul_pi_le_39894228040144_div_100000000000000
    hnorm_nonneg hexpUpper_nonneg

/--
Lower-bound the standard-normal density from a nonnegative lower bound on the
exponential factor `exp (-(x^2)/2)`.
-/
theorem stdNormalPdfReal_ge_of_le_exp_neg_sq_half
    {x expLower : ℝ}
    (hexp : expLower ≤ Real.exp (-(x ^ 2) / 2)) :
    expLower * ((39894228040143 : ℝ) / 100000000000000) ≤
      stdNormalPdfReal x := by
  unfold stdNormalPdfReal
  rw [div_eq_mul_inv]
  have hnorm_lower_nonneg :
      0 ≤ (39894228040143 : ℝ) / 100000000000000 := by norm_num
  have hexp_nonneg : 0 ≤ Real.exp (-(x ^ 2) / 2) := (Real.exp_pos _).le
  exact mul_le_mul hexp
    inv_sqrt_two_mul_pi_ge_39894228040143_div_100000000000000
    hnorm_lower_nonneg hexp_nonneg

/--
Generic upper-bound transport for a density times a nonnegative scalar factor.
-/
theorem stdNormalPdfReal_mul_le_of_bounds
    {x factor pdfUpper factorUpper : ℝ}
    (hpdf : stdNormalPdfReal x ≤ pdfUpper)
    (hfactor : factor ≤ factorUpper)
    (hfactor_nonneg : 0 ≤ factor)
    (hpdfUpper_nonneg : 0 ≤ pdfUpper) :
    stdNormalPdfReal x * factor ≤ pdfUpper * factorUpper :=
  mul_le_mul hpdf hfactor hfactor_nonneg hpdfUpper_nonneg

/--
Generic lower-bound transport for a density times a nonnegative scalar factor.
-/
theorem lower_le_stdNormalPdfReal_mul_of_bounds
    {x factor pdfLower factorLower : ℝ}
    (hpdf : pdfLower ≤ stdNormalPdfReal x)
    (hfactor : factorLower ≤ factor)
    (hpdfLower_nonneg : 0 ≤ pdfLower)
    (hfactorLower_nonneg : 0 ≤ factorLower) :
    pdfLower * factorLower ≤ stdNormalPdfReal x * factor := by
  have hpdf_nonneg : 0 ≤ stdNormalPdfReal x :=
    le_trans hpdfLower_nonneg hpdf
  exact mul_le_mul hpdf hfactor hfactorLower_nonneg hpdf_nonneg

end

end DP
end Mf
