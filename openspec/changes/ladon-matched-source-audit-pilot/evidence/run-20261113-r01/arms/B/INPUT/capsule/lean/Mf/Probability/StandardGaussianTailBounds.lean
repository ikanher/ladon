import Mf.DP.StandardGaussianCore

/-!
# Standard Gaussian tail bounds

Scalar standard-normal tail analysis, finite Mills continued fractions, and
explicit CDF/PDF bounds. This probability owner preserves the historical
`Mf.DP` declaration namespace while remaining below analytic-DP predicates and
signed-measure privacy closure.
-/

namespace Mf
namespace DP

open Filter

open scoped BigOperators Topology

noncomputable section

/--
Rectangle lower bound for the standard-normal CDF.

If a generated CDF artifact proves that the standard-normal density is at least
`m` on a finite interval `[a,b]` lying below `t`, Lean can turn that local PDF
lower bound into a CDF lower bound `m * (b - a) <= Phi(t)`.
-/
theorem stdNormalCDFReal_lower_of_Icc_pdf_lower
    {a b t m : ℝ}
    (hab : a ≤ b)
    (hbt : b ≤ t)
    (hpdf : ∀ x ∈ Set.Icc a b, m ≤ stdPdf x) :
    m * (b - a) ≤ stdNormalCDFReal t := by
  have hconst : (∫ _x in Set.Icc a b, m) = m * (b - a) := by
    rw [MeasureTheory.integral_const]
    simp [MeasureTheory.Measure.real, Real.volume_Icc, hab, mul_comm]
  have hstd_int : MeasureTheory.IntegrableOn stdPdf (Set.Iic t) MeasureTheory.volume := by
    have h : MeasureTheory.Integrable stdPdf MeasureTheory.volume := by
      change MeasureTheory.Integrable
        (ProbabilityTheory.gaussianPDFReal 0 (1 : NNReal)) MeasureTheory.volume
      exact ProbabilityTheory.integrable_gaussianPDFReal 0 (1 : NNReal)
    exact h.integrableOn
  have hstd_int_cell : MeasureTheory.IntegrableOn stdPdf (Set.Icc a b) MeasureTheory.volume := by
    have h : MeasureTheory.Integrable stdPdf MeasureTheory.volume := by
      change MeasureTheory.Integrable
        (ProbabilityTheory.gaussianPDFReal 0 (1 : NNReal)) MeasureTheory.volume
      exact ProbabilityTheory.integrable_gaussianPDFReal 0 (1 : NNReal)
    exact h.integrableOn
  have hcell_finite : MeasureTheory.volume (Set.Icc a b) ≠ ⊤ := by
    rw [Real.volume_Icc]
    exact ENNReal.ofReal_ne_top
  have hconst_int :
      MeasureTheory.IntegrableOn (fun _x : ℝ => m) (Set.Icc a b) MeasureTheory.volume := by
    exact MeasureTheory.integrableOn_const hcell_finite
  have hcell_le : (∫ _x in Set.Icc a b, m) ≤ ∫ x in Set.Icc a b, stdPdf x := by
    exact MeasureTheory.setIntegral_mono_on hconst_int hstd_int_cell measurableSet_Icc hpdf
  have hsubset : Set.Icc a b ⊆ Set.Iic t := by
    intro x hx
    exact le_trans hx.2 hbt
  have hstd_nonneg : 0 ≤ᶠ[MeasureTheory.ae (MeasureTheory.volume.restrict (Set.Iic t))] stdPdf :=
    Filter.Eventually.of_forall fun x => le_of_lt (by
      rw [stdPdf_eq_stdNormalPdfReal]
      exact stdNormalPdfReal_pos x)
  have hcell_to_tail : (∫ x in Set.Icc a b, stdPdf x) ≤ ∫ x in Set.Iic t, stdPdf x := by
    exact MeasureTheory.setIntegral_mono_set hstd_int hstd_nonneg
      (Filter.Eventually.of_forall hsubset)
  calc
    m * (b - a) = ∫ _x in Set.Icc a b, m := hconst.symm
    _ ≤ ∫ x in Set.Icc a b, stdPdf x := hcell_le
    _ ≤ ∫ x in Set.Iic t, stdPdf x := hcell_to_tail
    _ = stdNormalCDFReal t := (stdNormalCDFReal_eq_integral_Iic t).symm

/--
Certified decimal lower bound for `exp (-1)`.

This is the lower-bound companion to the upper decimal used by tail-only GDP
rows.  It is deliberately coarse but useful for generated CDF lower cells:
`exp (-A)` is bounded below by a power of this constant whenever `A` is below
the corresponding integer floor.
-/
abbrev expNegOneDecimalLower : ℝ :=
  (36787944116 : ℝ) / 100000000000

theorem expNegOneDecimalLower_le_exp_neg_one :
    expNegOneDecimalLower ≤ Real.exp (-1) := by
  have h : expNegOneDecimalLower = (0.36787944116 : ℝ) := by
    norm_num [expNegOneDecimalLower]
  rw [h]
  exact le_of_lt Real.exp_neg_one_gt_d9

theorem expNegOneDecimalLower_pow_le_exp_neg
    (n : ℕ) {A : ℝ}
    (hA : A ≤ (n : ℝ)) :
    expNegOneDecimalLower ^ n ≤ Real.exp (-A) := by
  calc
    expNegOneDecimalLower ^ n ≤ Real.exp (-1) ^ n := by
      exact pow_le_pow_left₀ (by norm_num [expNegOneDecimalLower])
        expNegOneDecimalLower_le_exp_neg_one n
    _ = Real.exp (-(n : ℝ)) := by
      rw [← Real.exp_nat_mul]
      ring_nf
    _ ≤ Real.exp (-A) := Real.exp_le_exp.mpr (neg_le_neg hA)

theorem one_div_three_le_inv_sqrt_two_mul_pi :
    (1 : ℝ) / 3 ≤ (Real.sqrt (2 * Real.pi))⁻¹ := by
  have hpos : 0 < Real.sqrt (2 * Real.pi) := by positivity
  rw [div_eq_mul_inv, one_mul]
  rw [inv_le_inv₀ (by norm_num : (0 : ℝ) < 3) hpos]
  have hsqrt_lt : Real.sqrt (2 * Real.pi) < 3 := by
    rw [Real.sqrt_lt' (by norm_num : (0 : ℝ) < 3)]
    nlinarith [Real.pi_lt_four]
  exact hsqrt_lt.le

theorem one_div_three_le_inv_sqrt_two_mul_inv_sqrt_pi :
    (1 : ℝ) / 3 ≤ (Real.sqrt (2 : ℝ))⁻¹ * (Real.sqrt Real.pi)⁻¹ := by
  have h := one_div_three_le_inv_sqrt_two_mul_pi
  have hsplit : Real.sqrt (2 * Real.pi) = Real.sqrt (2 : ℝ) * Real.sqrt Real.pi := by
    rw [Real.sqrt_mul]
    positivity
  simpa [hsplit, mul_comm, mul_left_comm, mul_assoc] using h

/--
Coarse pointwise lower bound for the standard-normal density.

If `x^2 / 2` is below a natural-number floor `n`, then the standard-normal
density at `x` is at least `(expNegOneDecimalLower ^ n) / 3`.
The constant `1/3` is a certified lower bound on the normalizing factor
`1 / sqrt (2*pi)`.
-/
theorem stdPdf_lower_of_sq_half_le_nat
    (n : ℕ) {x : ℝ}
    (hx : x ^ 2 / 2 ≤ (n : ℝ)) :
    (expNegOneDecimalLower ^ n) / 3 ≤ stdPdf x := by
  rw [stdPdf_eq_stdNormalPdfReal]
  unfold stdNormalPdfReal
  have hexp : expNegOneDecimalLower ^ n ≤ Real.exp (-(x ^ 2 / 2)) :=
    expNegOneDecimalLower_pow_le_exp_neg n hx
  have hconst : (1 : ℝ) / 3 ≤ (Real.sqrt (2 : ℝ))⁻¹ * (Real.sqrt Real.pi)⁻¹ :=
    one_div_three_le_inv_sqrt_two_mul_inv_sqrt_pi
  have hmul := mul_le_mul hconst hexp (by positivity) (by positivity)
  have hleft :
      ((1 : ℝ) / 3) * expNegOneDecimalLower ^ n
        = expNegOneDecimalLower ^ n / 3 := by
    ring
  simpa [hleft, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using hmul

/--
Generated-cell lower bound for the standard-normal CDF.

This composes `stdNormalCDFReal_lower_of_Icc_pdf_lower` with the coarse
pointwise density lower bound above.  Generated artifacts only need to prove
that each cell sits below the queried CDF endpoint and has `x^2 / 2` below an
integer floor throughout the cell.
-/
theorem stdNormalCDFReal_lower_of_Icc_sq_half_le_nat
    (n : ℕ) {a b t : ℝ}
    (hab : a ≤ b)
    (hbt : b ≤ t)
    (hsq : ∀ x ∈ Set.Icc a b, x ^ 2 / 2 ≤ (n : ℝ)) :
    ((expNegOneDecimalLower ^ n) / 3) * (b - a) ≤ stdNormalCDFReal t :=
  stdNormalCDFReal_lower_of_Icc_pdf_lower hab hbt
    (fun x hx => stdPdf_lower_of_sq_half_le_nat n (hsq x hx))

/--
Denominator of a finite Mills-ratio continued fraction.

`millsCfDenomFrom x k n` represents the denominator

```text
x + k / (x + (k+1) / (... + (k+n-1) / x)).
```

The selected count-bucket sharp non-tail CDF row currently targets
`millsCf 25 x`, but the definition is generic so generated rows can choose a
smaller or larger odd order.
-/
def millsCfDenomFrom (x : ℝ) (k : ℕ) : ℕ → ℝ
  | 0 => x
  | n + 1 => x + (k : ℝ) / millsCfDenomFrom x (k + 1) n

/-- Derivative value for `millsCfDenomFrom`, following the same finite recursion. -/
def millsCfDenomDerivFrom (x : ℝ) (k : ℕ) : ℕ → ℝ
  | 0 => 1
  | n + 1 =>
      1 - (k : ℝ) * millsCfDenomDerivFrom x (k + 1) n /
        (millsCfDenomFrom x (k + 1) n) ^ 2

/-- Finite Mills-ratio continued-fraction candidate of order `n`. -/
def millsCf (n : ℕ) (x : ℝ) : ℝ :=
  (millsCfDenomFrom x 1 n)⁻¹

/-- Residual whose sign decides whether a finite Mills candidate is a lower/upper bound. -/
def millsCfResidual (n : ℕ) (x : ℝ) : ℝ :=
  x * millsCf n x -
    (-(millsCfDenomDerivFrom x 1 n) / (millsCfDenomFrom x 1 n) ^ 2) - 1

/-- Finite Mills continued-fraction denominators are positive for positive `x`. -/
lemma millsCfDenomFrom_pos {x : ℝ} (hx : 0 < x) (k n : ℕ) :
    0 < millsCfDenomFrom x k n := by
  induction n generalizing k with
  | zero =>
      simpa [millsCfDenomFrom] using hx
  | succ n ih =>
      have hden_pos : 0 < millsCfDenomFrom x (k + 1) n := ih (k + 1)
      have hdiv_nonneg : 0 ≤ (k : ℝ) / millsCfDenomFrom x (k + 1) n := by
        exact div_nonneg (Nat.cast_nonneg k) (le_of_lt hden_pos)
      simpa [millsCfDenomFrom] using add_pos_of_pos_of_nonneg hx hdiv_nonneg

/-- Finite Mills continued-fraction denominators are at least their input. -/
lemma le_millsCfDenomFrom {x : ℝ} (hx : 0 < x) (k n : ℕ) :
    x ≤ millsCfDenomFrom x k n := by
  cases n with
  | zero =>
      simp [millsCfDenomFrom]
  | succ n =>
      have hden_pos : 0 < millsCfDenomFrom x (k + 1) n :=
        millsCfDenomFrom_pos hx (k + 1) n
      have hdiv_nonneg : 0 ≤ (k : ℝ) / millsCfDenomFrom x (k + 1) n := by
        exact div_nonneg (Nat.cast_nonneg k) (le_of_lt hden_pos)
      have : x ≤ x + (k : ℝ) / millsCfDenomFrom x (k + 1) n :=
        le_add_of_nonneg_right hdiv_nonneg
      simpa [millsCfDenomFrom] using this

/-- Finite Mills continued fractions are positive for positive `x`. -/
lemma millsCf_pos {x : ℝ} (hx : 0 < x) (n : ℕ) :
    0 < millsCf n x := by
  unfold millsCf
  exact inv_pos.mpr (millsCfDenomFrom_pos hx 1 n)

/-- Every finite Mills continued fraction is bounded above by the one-term candidate. -/
lemma millsCf_le_inv {x : ℝ} (hx : 0 < x) (n : ℕ) :
    millsCf n x ≤ x⁻¹ := by
  unfold millsCf
  have hden_ge : x ≤ millsCfDenomFrom x 1 n := le_millsCfDenomFrom hx 1 n
  have hden_pos : 0 < millsCfDenomFrom x 1 n := millsCfDenomFrom_pos hx 1 n
  exact (inv_le_inv₀ hden_pos hx).2 hden_ge

/-- The density times any finite Mills continued-fraction candidate vanishes at `+∞`. -/
theorem tendsto_stdNormalPdfReal_mul_millsCf_atTop_zero (n : ℕ) :
    Tendsto (fun x : ℝ => stdNormalPdfReal x * millsCf n x) atTop (𝓝 0) := by
  apply squeeze_zero'
  · exact eventually_atTop.2
      ⟨1, fun x hx => by
        have hx_pos : 0 < x := lt_of_lt_of_le zero_lt_one hx
        exact mul_nonneg (le_of_lt (stdNormalPdfReal_pos x))
          (le_of_lt (millsCf_pos hx_pos n))⟩
  · exact eventually_atTop.2
      ⟨1, fun x hx => by
        have hx_pos : 0 < x := lt_of_lt_of_le zero_lt_one hx
        exact mul_le_mul_of_nonneg_left (millsCf_le_inv hx_pos n)
          (le_of_lt (stdNormalPdfReal_pos x))⟩
  · simpa using
      (tendsto_stdNormalPdfReal_atTop_zero.mul
        (tendsto_inv_atTop_zero : Tendsto (fun x : ℝ => x⁻¹) atTop (𝓝 0)))

/-- Derivative of finite Mills continued-fraction denominators. -/
lemma hasDerivAt_millsCfDenomFrom {x : ℝ} (hx : 0 < x) (k n : ℕ) :
    HasDerivAt (fun y : ℝ => millsCfDenomFrom y k n)
      (millsCfDenomDerivFrom x k n) x := by
  induction n generalizing k with
  | zero =>
      change HasDerivAt id 1 x
      exact hasDerivAt_id' x
  | succ n ih =>
      have hden_ne : millsCfDenomFrom x (k + 1) n ≠ 0 :=
        ne_of_gt (millsCfDenomFrom_pos hx (k + 1) n)
      have hconst : HasDerivAt (fun _y : ℝ => (k : ℝ)) 0 x :=
        hasDerivAt_const x (k : ℝ)
      have hdiv := hconst.div (ih (k + 1)) hden_ne
      have hadd := (hasDerivAt_id' x).add hdiv
      have hderiv :
          1 + (0 * millsCfDenomFrom x (k + 1) n -
                (k : ℝ) * millsCfDenomDerivFrom x (k + 1) n) /
                millsCfDenomFrom x (k + 1) n ^ 2
            = millsCfDenomDerivFrom x k (n + 1) := by
        simp [millsCfDenomDerivFrom]
        ring
      convert hadd using 1 <;>
        first | rfl |
          (simpa [millsCfDenomFrom, Function.id_def, Pi.add_apply,
            div_eq_mul_inv, pow_two] using hderiv.symm)

/-- Derivative of a finite Mills continued-fraction candidate. -/
lemma hasDerivAt_millsCf {x : ℝ} (hx : 0 < x) (n : ℕ) :
    HasDerivAt (fun y : ℝ => millsCf n y)
      (-(millsCfDenomDerivFrom x 1 n) / (millsCfDenomFrom x 1 n) ^ 2) x := by
  unfold millsCf
  have hden_ne : millsCfDenomFrom x 1 n ≠ 0 := ne_of_gt (millsCfDenomFrom_pos hx 1 n)
  have h := (hasDerivAt_millsCfDenomFrom hx 1 n).inv hden_ne
  convert h using 1 <;>
    first | rfl | (simp [millsCf, Pi.inv_apply] <;> ring)

@[simp] lemma millsCf_zero (x : ℝ) : millsCf 0 x = x⁻¹ := by
  simp [millsCf, millsCfDenomFrom]

lemma millsCf_one {x : ℝ} (hx : x ≠ 0) :
    millsCf 1 x = x / (1 + x ^ 2) := by
  simp [millsCf, millsCfDenomFrom]
  field_simp [hx]
  ring

/-- Standard-normal upper tail, named for Mills-ratio bounds. -/
def stdNormalUpperTailReal (x : ℝ) : ℝ :=
  stdNormalCDFReal (-x)

/-- Derivative of the standard-normal upper tail. -/
lemma hasDerivAt_stdNormalUpperTailReal (x : ℝ) :
  HasDerivAt stdNormalUpperTailReal (-stdNormalPdfReal x) x := by
  have hneg : HasDerivAt (fun y : ℝ => -y) (-1) x := by
    change HasDerivAt (Neg.neg : ℝ → ℝ) (-1) x
    exact (hasDerivAt_id' x).neg
  have h :=
    (hasDerivAt_stdNormalCDFReal (-x)).comp x hneg
  convert h using 1 <;>
    first | rfl | (simp [stdNormalUpperTailReal, Function.comp_def,
      stdNormalPdfReal_neg, mul_comm] <;> ring)

/-- The standard-normal upper tail tends to zero at `+∞`. -/
theorem tendsto_stdNormalUpperTailReal_atTop_zero :
    Tendsto stdNormalUpperTailReal atTop (𝓝 0) := by
  have hcdf : Tendsto stdNormalCDFReal atBot (𝓝 0) := by
    change Tendsto (ProbabilityTheory.cdf stdNormalMeasure) atBot (𝓝 0)
    exact ProbabilityTheory.tendsto_cdf_atBot (μ := stdNormalMeasure)
  change Tendsto (fun x : ℝ => stdNormalCDFReal (-x)) atTop (𝓝 0)
  simpa [Function.comp_def] using hcdf.comp tendsto_neg_atTop_atBot

/--
Derivative-comparison lower-bound seam for Mills-ratio candidates.

If `r` has derivative `r'`, the weighted density term `phi(x) * r(x)` tends to
zero at `+∞`, and `x*r(x) - r'(x) - 1 <= 0` to the right of `x0`, then
`phi(x0) * r(x0)` is a lower bound on the standard-normal upper tail
`Phi(-x0)`.
-/
theorem stdNormalUpperTailReal_lower_of_candidate_deriv_nonpos
    {r r' : ℝ → ℝ} {x0 : ℝ}
    (hr : ∀ x : ℝ, x0 ≤ x → HasDerivAt r (r' x) x)
    (hlim : Tendsto (fun x : ℝ => stdNormalPdfReal x * r x) atTop (𝓝 0))
    (hsign : ∀ x : ℝ, x0 < x → x * r x - r' x - 1 ≤ 0) :
    stdNormalPdfReal x0 * r x0 ≤ stdNormalUpperTailReal x0 := by
  let gap : ℝ → ℝ := fun x => stdNormalUpperTailReal x - stdNormalPdfReal x * r x
  have hgap_deriv :
      ∀ x : ℝ, x0 ≤ x →
        HasDerivAt gap (stdNormalPdfReal x * (x * r x - r' x - 1)) x := by
    intro x hx
    have hprod :
        HasDerivAt (fun y : ℝ => stdNormalPdfReal y * r y)
          ((-x * stdNormalPdfReal x) * r x + stdNormalPdfReal x * r' x) x :=
      (hasDerivAt_stdNormalPdfReal x).mul (hr x hx)
    have hgap := (hasDerivAt_stdNormalUpperTailReal x).sub hprod
    convert hgap using 1 <;>
      first | rfl | (simp [gap, Pi.sub_apply, Pi.mul_apply] <;> ring)
  have hanti : AntitoneOn gap (Set.Ici x0) := by
    apply antitoneOn_of_hasDerivWithinAt_nonpos (convex_Ici x0)
    · intro x hx
      exact (hgap_deriv x hx).continuousAt.continuousWithinAt
    · intro x hx
      have hxle : x0 ≤ x := le_of_lt (by simpa using hx)
      exact (hgap_deriv x hxle).hasDerivWithinAt
    · intro x hx
      have hx0 : x0 < x := by simpa using hx
      have hpdf_nonneg : 0 ≤ stdNormalPdfReal x := le_of_lt (stdNormalPdfReal_pos x)
      exact mul_nonpos_of_nonneg_of_nonpos hpdf_nonneg (hsign x hx0)
  have hgap_lim : Tendsto gap atTop (𝓝 0) := by
    simpa [gap] using tendsto_stdNormalUpperTailReal_atTop_zero.sub hlim
  have hbound : ∀ᶠ x in atTop, gap x ≤ gap x0 := by
    exact eventually_atTop.2
      ⟨x0, fun x hx =>
        hanti (by simp) (by simpa using hx) hx⟩
  have hzero : 0 ≤ gap x0 := le_of_tendsto hgap_lim hbound
  simpa [gap, sub_nonneg] using hzero

/--
Derivative-comparison upper-bound seam for Mills-ratio candidates.

If the residual `x*r(x) - r'(x) - 1` is nonnegative to the right of `x0`, then
`phi(x0) * r(x0)` upper-bounds the standard-normal upper tail.
-/
theorem stdNormalUpperTailReal_upper_of_candidate_deriv_nonneg
    {r r' : ℝ → ℝ} {x0 : ℝ}
    (hr : ∀ x : ℝ, x0 ≤ x → HasDerivAt r (r' x) x)
    (hlim : Tendsto (fun x : ℝ => stdNormalPdfReal x * r x) atTop (𝓝 0))
    (hsign : ∀ x : ℝ, x0 < x → 0 ≤ x * r x - r' x - 1) :
    stdNormalUpperTailReal x0 ≤ stdNormalPdfReal x0 * r x0 := by
  let gap : ℝ → ℝ := fun x => stdNormalUpperTailReal x - stdNormalPdfReal x * r x
  have hgap_deriv :
      ∀ x : ℝ, x0 ≤ x →
        HasDerivAt gap (stdNormalPdfReal x * (x * r x - r' x - 1)) x := by
    intro x hx
    have hprod :
        HasDerivAt (fun y : ℝ => stdNormalPdfReal y * r y)
          ((-x * stdNormalPdfReal x) * r x + stdNormalPdfReal x * r' x) x :=
      (hasDerivAt_stdNormalPdfReal x).mul (hr x hx)
    have hgap := (hasDerivAt_stdNormalUpperTailReal x).sub hprod
    convert hgap using 1 <;>
      first | rfl | (simp [gap, Pi.sub_apply, Pi.mul_apply] <;> ring)
  have hmono : MonotoneOn gap (Set.Ici x0) := by
    apply monotoneOn_of_hasDerivWithinAt_nonneg (convex_Ici x0)
    · intro x hx
      exact (hgap_deriv x hx).continuousAt.continuousWithinAt
    · intro x hx
      have hxle : x0 ≤ x := le_of_lt (by simpa using hx)
      exact (hgap_deriv x hxle).hasDerivWithinAt
    · intro x hx
      have hx0 : x0 < x := by simpa using hx
      have hpdf_nonneg : 0 ≤ stdNormalPdfReal x := le_of_lt (stdNormalPdfReal_pos x)
      exact mul_nonneg hpdf_nonneg (hsign x hx0)
  have hgap_lim : Tendsto gap atTop (𝓝 0) := by
    simpa [gap] using tendsto_stdNormalUpperTailReal_atTop_zero.sub hlim
  have hbound : ∀ᶠ x in atTop, gap x0 ≤ gap x := by
    exact eventually_atTop.2
      ⟨x0, fun x hx =>
        hmono (by simp) (by simpa using hx) hx⟩
  have hzero : gap x0 ≤ 0 := ge_of_tendsto hgap_lim hbound
  simpa [gap, sub_nonpos] using hzero

/--
Finite-Mills lower-bound consumer.

Generated high-order proofs only need to prove that `millsCfResidual n x <= 0`
to the right of the target point; this theorem supplies the derivative and
tail-limit obligations.
-/
theorem stdNormalCDFReal_neg_lower_of_millsCfResidual_nonpos
    {x0 : ℝ} (hx0 : 0 < x0) {n : ℕ}
    (hsign : ∀ x : ℝ, x0 < x → millsCfResidual n x ≤ 0) :
    stdNormalPdfReal x0 * millsCf n x0 ≤ stdNormalCDFReal (-x0) := by
  simpa [stdNormalUpperTailReal] using
    (stdNormalUpperTailReal_lower_of_candidate_deriv_nonpos
      (r := fun x : ℝ => millsCf n x)
      (r' := fun x : ℝ =>
        -(millsCfDenomDerivFrom x 1 n) / (millsCfDenomFrom x 1 n) ^ 2)
      (fun x hx => hasDerivAt_millsCf (lt_of_lt_of_le hx0 hx) n)
      (tendsto_stdNormalPdfReal_mul_millsCf_atTop_zero n)
      (by
        intro x hx
        simpa [millsCfResidual] using hsign x hx))

/--
Finite-Mills upper-bound consumer.

Generated high-order proofs only need to prove that `0 <= millsCfResidual n x`
to the right of the target point.
-/
theorem stdNormalCDFReal_neg_upper_of_millsCfResidual_nonneg
    {x0 : ℝ} (hx0 : 0 < x0) {n : ℕ}
    (hsign : ∀ x : ℝ, x0 < x → 0 ≤ millsCfResidual n x) :
    stdNormalCDFReal (-x0) ≤ stdNormalPdfReal x0 * millsCf n x0 := by
  simpa [stdNormalUpperTailReal] using
    (stdNormalUpperTailReal_upper_of_candidate_deriv_nonneg
      (r := fun x : ℝ => millsCf n x)
      (r' := fun x : ℝ =>
        -(millsCfDenomDerivFrom x 1 n) / (millsCfDenomFrom x 1 n) ^ 2)
      (fun x hx => hasDerivAt_millsCf (lt_of_lt_of_le hx0 hx) n)
      (tendsto_stdNormalPdfReal_mul_millsCf_atTop_zero n)
      (by
        intro x hx
        simpa [millsCfResidual] using hsign x hx))

/--
Classical one-term Mills upper bound for the standard-normal upper tail.

This theorem is intentionally weaker than the continued-fraction bounds needed
by the dominant count-bucket row, but it is a concrete proof that the
derivative-comparison seam can discharge a Mills-ratio candidate.
-/
theorem stdNormalUpperTailReal_le_pdf_mul_inv {x0 : ℝ} (hx0 : 0 < x0) :
    stdNormalUpperTailReal x0 ≤ stdNormalPdfReal x0 * x0⁻¹ := by
  apply stdNormalUpperTailReal_upper_of_candidate_deriv_nonneg
      (r := fun x : ℝ => x⁻¹) (r' := fun x : ℝ => -(x ^ 2)⁻¹)
  · intro x hx
    have hx_pos : 0 < x := lt_of_lt_of_le hx0 hx
    exact hasDerivAt_inv (ne_of_gt hx_pos)
  · simpa using
      (tendsto_stdNormalPdfReal_atTop_zero.mul
        (tendsto_inv_atTop_zero : Tendsto (fun x : ℝ => x⁻¹) atTop (𝓝 0)))
  · intro x hx
    have hx_pos : 0 < x := lt_trans hx0 hx
    have hx_ne : x ≠ 0 := ne_of_gt hx_pos
    calc
      0 ≤ (x ^ 2)⁻¹ := inv_nonneg.mpr (sq_nonneg x)
      _ = x * x⁻¹ - (-(x ^ 2)⁻¹) - 1 := by
        field_simp [hx_ne]
        ring

/--
Classical one-term Mills lower bound for the standard-normal upper tail.

This gives a concrete lower-bound candidate through the same derivative seam.
It is weaker than the selected-row continued fraction, but useful as a verified
fallback and as a regression guard for the lower-bound orientation.
-/
theorem stdNormalPdf_mul_millsFirstLower_le_upperTail (x0 : ℝ) :
    stdNormalPdfReal x0 * (x0 / (1 + x0 ^ 2)) ≤ stdNormalUpperTailReal x0 := by
  apply stdNormalUpperTailReal_lower_of_candidate_deriv_nonpos
      (r := fun x : ℝ => x / (1 + x ^ 2))
      (r' := fun x : ℝ => (1 - x ^ 2) / (1 + x ^ 2) ^ 2)
  · intro x _hx
    have hden_ne : 1 + x ^ 2 ≠ 0 := by positivity
    have hden_deriv : HasDerivAt (fun y : ℝ => 1 + y ^ 2) (2 * x) x := by
      convert (hasDerivAt_const (x := x) (c := (1 : ℝ))).add (hasDerivAt_pow 2 x) using 1 <;>
        first | rfl | simp [Pi.add_apply, Pi.pow_apply]
    have h := (hasDerivAt_id' x).div hden_deriv hden_ne
    convert h using 1 <;>
      first | rfl | (simp [Pi.div_apply, Function.id_def] <;> ring)
  · apply squeeze_zero'
    · exact eventually_atTop.2
        ⟨0, fun x hx => by
          have hx_nonneg : 0 ≤ x := by simpa using hx
          have hden_pos : 0 < 1 + x ^ 2 := by positivity
          exact mul_nonneg (le_of_lt (stdNormalPdfReal_pos x))
            (div_nonneg hx_nonneg (le_of_lt hden_pos))⟩
    · exact eventually_atTop.2
        ⟨0, fun x hx => by
          have hx_nonneg : 0 ≤ x := by simpa using hx
          have hden_pos : 0 < 1 + x ^ 2 := by positivity
          have hratio_le_one : x / (1 + x ^ 2) ≤ 1 := by
            rw [div_le_one hden_pos]
            nlinarith [sq_nonneg x, sq_nonneg (x - 1)]
          exact mul_le_of_le_one_right (le_of_lt (stdNormalPdfReal_pos x)) hratio_le_one⟩
    · exact tendsto_stdNormalPdfReal_atTop_zero
  · intro x _hx
    have hden_pos : 0 < 1 + x ^ 2 := by positivity
    have hden_ne : 1 + x ^ 2 ≠ 0 := ne_of_gt hden_pos
    calc
      x * (x / (1 + x ^ 2)) - ((1 - x ^ 2) / (1 + x ^ 2) ^ 2) - 1
          = -2 / (1 + x ^ 2) ^ 2 := by
            field_simp [hden_ne]
            ring
      _ ≤ 0 := by
        exact div_nonpos_of_nonpos_of_nonneg (by norm_num : (-2 : ℝ) ≤ 0) (sq_nonneg _)

/-- Mills continued-fraction alternation base case: order `0` is an upper bound. -/
theorem stdNormalCDFReal_neg_upper_of_millsCf_zero {x : ℝ} (hx : 0 < x) :
    stdNormalCDFReal (-x) ≤ stdNormalPdfReal x * millsCf 0 x := by
  simpa [stdNormalUpperTailReal] using stdNormalUpperTailReal_le_pdf_mul_inv hx

/-- Mills continued-fraction alternation base case: order `1` is a lower bound. -/
theorem stdNormalCDFReal_neg_lower_of_millsCf_one {x : ℝ} (hx : 0 < x) :
    stdNormalPdfReal x * millsCf 1 x ≤ stdNormalCDFReal (-x) := by
  rw [millsCf_one (ne_of_gt hx)]
  simpa [stdNormalUpperTailReal] using stdNormalPdf_mul_millsFirstLower_le_upperTail x

end

end DP
end Mf
