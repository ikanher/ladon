import Mf.DP.Profile.RationalExpInterval
import Mf.DP.Profile.RationalOutwardIntervalConvergence

namespace Mf
namespace DP

open Filter Topology

namespace RationalExpInterval

open Mf.Optimization.SDE.DPAdamFixedBetaSignedExpIntervalCertificate

private theorem tendsto_taylorLowerRat_cast
    (remainder : ℚ) :
    Tendsto
      (fun order => (expTaylorLowerRat remainder order : ℝ))
      atTop
      (𝓝 (Real.exp (remainder : ℝ))) := by
  simpa [expTaylorLowerRat, Real.exp_eq_exp_ℝ] using
    (NormedSpace.expSeries_div_hasSum_exp
      (remainder : ℝ)).tendsto_sum_nat

private theorem tendsto_succ_div_self_real :
    Tendsto
      (fun order : ℕ => ((order + 1 : ℕ) : ℝ) / order)
      atTop
      (𝓝 1) := by
  have h :=
    (tendsto_const_nhds :
      Tendsto (fun _ : ℕ => (1 : ℝ)) atTop (𝓝 1)).add
      (tendsto_one_div_atTop_nhds_zero_nat (𝕜 := ℝ))
  have h' :
      Tendsto (fun order : ℕ => (1 : ℝ) + 1 / order)
        atTop (𝓝 1) := by
    simpa using h
  refine h'.congr' ?_
  filter_upwards [eventually_gt_atTop (0 : ℕ)] with order horder
  field_simp
  norm_num

private theorem tendsto_taylorRemainderRat_cast
    (remainder : ℚ) :
    Tendsto
      (fun order =>
        ((remainder : ℝ) ^ order / order.factorial) *
          (((order + 1 : ℕ) : ℝ) / order))
      atTop
      (𝓝 0) := by
  have hmain :
      Tendsto
        (fun order => (remainder : ℝ) ^ order / order.factorial)
        atTop
        (𝓝 0) :=
    FloorSemiring.tendsto_pow_div_factorial_atTop (remainder : ℝ)
  simpa using hmain.mul tendsto_succ_div_self_real

private theorem taylorUpperRat_cast_eq
    (remainder : ℚ) (order : ℕ) :
    (expTaylorUpperRat remainder order : ℝ) =
      (expTaylorLowerRat remainder order : ℝ) +
        ((remainder : ℝ) ^ order / order.factorial) *
          (((order + 1 : ℕ) : ℝ) / order) := by
  cases order with
  | zero =>
      simp [expTaylorUpperRat]
  | succ order =>
      simp only [expTaylorUpperRat, Rat.cast_add, Rat.cast_mul,
        Rat.cast_pow, Rat.cast_natCast, Rat.cast_div]
      field_simp
      push_cast
      rw [pow_succ]

private theorem tendsto_taylorUpperRat_cast
    (remainder : ℚ) :
    Tendsto
      (fun order => (expTaylorUpperRat remainder order : ℝ))
      atTop
      (𝓝 (Real.exp (remainder : ℝ))) := by
  have h :=
    (tendsto_taylorLowerRat_cast remainder).add
      (tendsto_taylorRemainderRat_cast remainder)
  have h' :
      Tendsto
        (fun order =>
          (expTaylorLowerRat remainder order : ℝ) +
            ((remainder : ℝ) ^ order / order.factorial) *
              (((order + 1 : ℕ) : ℝ) / order))
        atTop
        (𝓝 (Real.exp (remainder : ℝ))) := by
    simpa using h
  refine h'.congr' ?_
  filter_upwards with order
  exact (taylorUpperRat_cast_eq remainder order).symm

private theorem tendsto_positiveLower_cast
    (x : ℚ) (power : ℕ) :
    Tendsto
      (fun order => (positiveLower x power order : ℝ))
      atTop
      (𝓝 (Real.exp (magnitude x : ℝ))) := by
  let remainder := dyadicRemainder (magnitude x) power
  have hpow :=
    (tendsto_taylorLowerRat_cast remainder).pow (2 ^ power : ℕ)
  have hscale :
      (magnitude x : ℝ) =
        ((2 ^ power : ℕ) : ℝ) * (remainder : ℝ) := by
    exact_mod_cast
      (twoPow_mul_dyadicRemainder (magnitude x) power).symm
  have hexp :
      (Real.exp (remainder : ℝ)) ^ (2 ^ power : ℕ) =
        Real.exp (magnitude x : ℝ) := by
    symm
    exact exp_eq_pow_two_of_eq_twoPow_mul power hscale
  simpa [positiveLower, remainder, hexp] using hpow

private theorem tendsto_positiveUpper_cast
    (x : ℚ) (power : ℕ) :
    Tendsto
      (fun order => (positiveUpper x power order : ℝ))
      atTop
      (𝓝 (Real.exp (magnitude x : ℝ))) := by
  let remainder := dyadicRemainder (magnitude x) power
  have hpow :=
    (tendsto_taylorUpperRat_cast remainder).pow (2 ^ power : ℕ)
  have hscale :
      (magnitude x : ℝ) =
        ((2 ^ power : ℕ) : ℝ) * (remainder : ℝ) := by
    exact_mod_cast
      (twoPow_mul_dyadicRemainder (magnitude x) power).symm
  have hexp :
      (Real.exp (remainder : ℝ)) ^ (2 ^ power : ℕ) =
        Real.exp (magnitude x : ℝ) := by
    symm
    exact exp_eq_pow_two_of_eq_twoPow_mul power hscale
  simpa [positiveUpper, remainder, hexp] using hpow

/--
For every fixed input and dyadic reduction power, the real interpretation of
the rational exponential interval width tends to zero as the Taylor order
increases.
-/
theorem tendsto_interval_width_cast
    (x : ℚ)
    (power : ℕ) :
    Tendsto
      (fun order => ((interval x power order).width : ℝ))
      atTop
      (𝓝 0) := by
  by_cases hx : x < 0
  · have hlower :=
      (tendsto_positiveUpper_cast x power).inv₀
        (ne_of_gt (Real.exp_pos (magnitude x : ℝ)))
    have hupper :=
      (tendsto_positiveLower_cast x power).inv₀
        (ne_of_gt (Real.exp_pos (magnitude x : ℝ)))
    have hsub := hupper.sub hlower
    have hsub' :
        Tendsto
          (fun order =>
            ((positiveLower x power order : ℝ))⁻¹ -
              ((positiveUpper x power order : ℝ))⁻¹)
          atTop
          (𝓝 0) := by
      simpa using hsub
    refine hsub'.congr' ?_
    filter_upwards with order
    simp [RationalOutwardInterval.width, interval, hx]
  · have hsub :=
      (tendsto_positiveUpper_cast x power).sub
        (tendsto_positiveLower_cast x power)
    have hsub' :
        Tendsto
          (fun order =>
            (positiveUpper x power order : ℝ) -
              (positiveLower x power order : ℝ))
          atTop
          (𝓝 0) := by
      simpa using hsub
    refine hsub'.congr' ?_
    filter_upwards with order
    simp [RationalOutwardInterval.width, interval, hx]

/-- Epsilon form used by a fair finite search over Taylor orders. -/
theorem eventually_interval_width_lt
    (x : ℚ)
    (power : ℕ)
    {tolerance : ℝ}
    (htolerance : 0 < tolerance) :
    ∀ᶠ order in atTop,
      ((interval x power order).width : ℝ) < tolerance :=
  (tendsto_interval_width_cast x power).eventually
    (gt_mem_nhds htolerance)

/--
For a fixed rational input and a sufficient dyadic power, the complete
signed exponential interval converges to the exact exponential as the
positive Taylor order increases.
-/
theorem interval_convergesTo
    (x : ℚ)
    (power : ℕ)
    (hpower : PowerSufficient x power) :
    RationalOutwardInterval.ConvergesTo
      (fun order => interval x power (order + 1))
      (Real.exp (x : ℝ)) := by
  apply
    RationalOutwardInterval.convergesTo_of_encloses_of_tendsto_width
  · exact .of_forall fun order =>
      interval_encloses x power (order + 1) hpower (Nat.succ_pos order)
  · exact
      (tendsto_interval_width_cast x power).comp
        (Filter.tendsto_add_atTop_nat 1)

/--
For a fixed rational input interval and sufficient dyadic power, the width
of its exponential image converges to the spread between the exact
exponentials of the two endpoints.
-/
theorem tendsto_ofInputInterval_width_cast
    (input : RationalOutwardInterval)
    (power : ℕ)
    (hlowerPower : PowerSufficient input.lower power)
    (hupperPower : PowerSufficient input.upper power) :
    Tendsto
      (fun order =>
        ((ofInputInterval input power (order + 1)).width : ℝ))
      atTop
      (𝓝
        (Real.exp (input.upper : ℝ) -
          Real.exp (input.lower : ℝ))) := by
  have hlower :=
    (interval_convergesTo input.lower power hlowerPower).1
  have hupper :=
    (interval_convergesTo input.upper power hupperPower).2
  have hsub := hupper.sub hlower
  refine hsub.congr' (.of_forall fun order => ?_)
  simp [ofInputInterval, RationalOutwardInterval.width]

/--
A convergent rational sequence is eventually small enough for the
stage-index dyadic power.  This is the range-reduction fact used by the
common finite-family schedule below.
-/
theorem eventually_powerSufficient_of_tendsto
    {input : ℕ → ℚ}
    {value : ℝ}
    (hinput :
      Tendsto (fun precision => (input precision : ℝ))
        atTop (𝓝 value)) :
    ∀ᶠ precision in atTop,
      PowerSufficient (input precision) precision := by
  have habs :
      Tendsto (fun precision => |(input precision : ℝ)|)
        atTop (𝓝 |value|) :=
    hinput.abs
  have hbounded :
      ∀ᶠ precision in atTop,
        |(input precision : ℝ)| < |value| + 1 :=
    habs.eventually (gt_mem_nhds (lt_add_one |value|))
  have hpow :
      Tendsto (fun precision : ℕ => (2 : ℝ) ^ precision)
        atTop atTop :=
    tendsto_pow_atTop_atTop_of_one_lt (by norm_num)
  have hpast :
      ∀ᶠ precision in atTop,
        |value| + 1 ≤ (2 : ℝ) ^ precision :=
    hpow.eventually_ge_atTop (|value| + 1)
  filter_upwards [hbounded, hpast] with precision hinputBound hpowerBound
  unfold PowerSufficient magnitude
  have hreal :
      |(input precision : ℝ)| ≤ (2 : ℝ) ^ precision :=
    (le_of_lt hinputBound).trans hpowerBound
  exact_mod_cast hreal

private theorem exists_common_order_width_lt
    {ι : Type*}
    [Finite ι]
    (input : ι → RationalOutwardInterval)
    (power : ℕ)
    (hpower : ∀ index,
      PowerSufficient (input index).lower power ∧
        PowerSufficient (input index).upper power)
    {tolerance : ℝ}
    (htolerance : 0 < tolerance) :
    ∃ order : ℕ,
      0 < order ∧
        ∀ index,
          ((ofInputInterval
            (input index) power order).width : ℝ) <
            (Real.exp ((input index).upper : ℝ) -
              Real.exp ((input index).lower : ℝ)) +
              tolerance := by
  classical
  letI := Fintype.ofFinite ι
  have horders :
      ∀ᶠ order in atTop,
        ∀ index ∈ (Finset.univ : Finset ι),
          ((ofInputInterval
            (input index) power (order + 1)).width : ℝ) <
            (Real.exp ((input index).upper : ℝ) -
              Real.exp ((input index).lower : ℝ)) +
              tolerance := by
    rw [Finset.eventually_all]
    intro index _hindex
    exact
      (tendsto_ofInputInterval_width_cast
        (input index) power
        (hpower index).1 (hpower index).2).eventually
        (gt_mem_nhds (lt_add_of_pos_right _ htolerance))
  obtain ⟨order, horder⟩ := horders.exists
  exact ⟨order + 1, Nat.succ_pos order, fun index =>
    horder index (Finset.mem_univ index)⟩

/--
Every finite family of convergent rational input intervals admits one common
positive Taylor-order schedule even when each interval encloses a moving
stage target rather than the final limit.

The input interval endpoints and the moving target must converge to the same
limit.  At each stage, the exponential interval then encloses the exponential
of that stage's target.  A common finite-family order makes its excess width
vanish, so the resulting intervals converge to the exponential of the final
limit.

This theorem is the appropriate interface for rounded quantities such as a
tail exponent built from a convergent rational upper bound: the point input at
one stage encloses its own exact rational value, but generally does not
enclose the limiting real value.
-/
theorem exists_common_ofInputInterval_movingTarget_schedule
    {ι : Type*}
    [Finite ι]
    (input : ι → ℕ → RationalOutwardInterval)
    (target : ι → ℕ → ℝ)
    (value : ι → ℝ)
    (hconverges : ∀ index,
      RationalOutwardInterval.ConvergesTo
        (input index) (value index))
    (htarget : ∀ index,
      Tendsto (target index) atTop (𝓝 (value index)))
    (hencloses : ∀ precision index,
      (input index precision).Encloses (target index precision)) :
    ∃ order : ℕ → ℕ,
      (∀ precision, 0 < order precision) ∧
        ∀ index,
          RationalOutwardInterval.ConvergesTo
            (fun precision =>
              ofInputInterval
                (input index precision)
                precision
                (order precision))
            (Real.exp (value index)) := by
  classical
  letI := Fintype.ofFinite ι
  have hpower :
      ∀ᶠ precision in atTop,
        ∀ index ∈ (Finset.univ : Finset ι),
          PowerSufficient
              (input index precision).lower precision ∧
            PowerSufficient
              (input index precision).upper precision := by
    rw [Finset.eventually_all]
    intro index _hindex
    exact
      (eventually_powerSufficient_of_tendsto
        (hconverges index).1).and
      (eventually_powerSufficient_of_tendsto
        (hconverges index).2)
  have hstage :
      ∀ precision, ∃ order : ℕ,
        0 < order ∧
          ((∀ index,
              PowerSufficient
                  (input index precision).lower precision ∧
                PowerSufficient
                  (input index precision).upper precision) →
            ∀ index,
              ((ofInputInterval
                (input index precision)
                precision order).width : ℝ) <
                (Real.exp ((input index precision).upper : ℝ) -
                  Real.exp ((input index precision).lower : ℝ)) +
                  1 / ((precision + 1 : ℕ) : ℝ)) := by
    intro precision
    by_cases hprecision :
        ∀ index,
          PowerSufficient
              (input index precision).lower precision ∧
            PowerSufficient
              (input index precision).upper precision
    · obtain ⟨order, horder, hwidth⟩ :=
        exists_common_order_width_lt
          (fun index => input index precision)
          precision hprecision
          (tolerance := 1 / ((precision + 1 : ℕ) : ℝ))
          (by positivity)
      exact ⟨order, horder, fun _ => hwidth⟩
    · exact ⟨1, by norm_num, fun hp => (hprecision hp).elim⟩
  choose order horder using hstage
  refine ⟨order, fun precision => (horder precision).1, ?_⟩
  intro index
  have hpowerAll :
      ∀ᶠ precision in atTop,
        ∀ index,
          PowerSufficient
              (input index precision).lower precision ∧
            PowerSufficient
              (input index precision).upper precision :=
    hpower.mono fun _ hprecision index =>
      hprecision index (Finset.mem_univ index)
  have houtEncloses :
      ∀ᶠ precision in atTop,
        (ofInputInterval
          (input index precision)
          precision
          (order precision)).Encloses
          (Real.exp (target index precision)) :=
    hpowerAll.mono fun precision hprecision =>
      ofInputInterval_encloses
        precision (order precision)
        (hencloses precision index)
        (hprecision index).1
        (hprecision index).2
        (horder precision).1
  have hspread :
      Tendsto
        (fun precision =>
          Real.exp ((input index precision).upper : ℝ) -
            Real.exp ((input index precision).lower : ℝ))
        atTop
        (𝓝 0) := by
    have hlower :=
      (Real.continuous_exp.tendsto (value index)).comp
        (hconverges index).1
    have hupper :=
      (Real.continuous_exp.tendsto (value index)).comp
        (hconverges index).2
    simpa using hupper.sub hlower
  have htolerance :
      Tendsto
        (fun precision : ℕ =>
          1 / ((precision + 1 : ℕ) : ℝ))
        atTop
        (𝓝 0) := by
    simpa using
      (tendsto_one_div_add_atTop_nhds_zero_nat (𝕜 := ℝ))
  have hwidth :
      Tendsto
        (fun precision =>
          ((ofInputInterval
            (input index precision)
            precision
            (order precision)).width : ℝ))
        atTop
        (𝓝 0) := by
    have hsqueeze :
        Tendsto
          (fun precision =>
            ((ofInputInterval
              (input index precision)
              precision
              (order precision)).width : ℝ))
          atTop
          (𝓝 (0 + 0)) := by
      apply tendsto_of_tendsto_of_tendsto_of_le_of_le'
        tendsto_const_nhds (hspread.add htolerance)
      · filter_upwards [houtEncloses] with precision hprecision
        have hvalid :
            (ofInputInterval
              (input index precision)
              precision
              (order precision)).Valid := by
          exact_mod_cast hprecision.1.trans hprecision.2
        exact_mod_cast
          (RationalOutwardInterval.valid_iff_width_nonnegative.mp hvalid)
      · filter_upwards [hpowerAll] with precision hprecision
        exact le_of_lt ((horder precision).2 hprecision index)
    simpa using hsqueeze
  have htargetExp :
      Tendsto
        (fun precision => Real.exp (target index precision))
        atTop
        (𝓝 (Real.exp (value index))) :=
    (Real.continuous_exp.tendsto (value index)).comp (htarget index)
  exact
    RationalOutwardInterval.convergesTo_of_moving_encloses_of_tendsto_width
      houtEncloses htargetExp hwidth

/--
Every finite family of convergent rational input intervals admits one common
positive Taylor-order schedule whose exponential images converge
simultaneously.  The dyadic power at stage `precision` is exactly
`precision`; only the common Taylor order is selected.

The enclosure assumption is the ordinary outward-rounding invariant.  No
uniform Taylor estimate beyond the already proved fixed-input convergence is
needed: at each stage one order is chosen for the finite family, with excess
width at most `1 / (precision + 1)`.

The conclusion is asymptotic.  Early stages, including precision zero, need
not satisfy the range-reduction condition.  A sound finite evaluator must
still check `PowerSufficient` at every stage it accepts.
-/
theorem exists_common_ofInputInterval_schedule
    {ι : Type*}
    [Finite ι]
    (input : ι → ℕ → RationalOutwardInterval)
    (value : ι → ℝ)
    (hconverges : ∀ index,
      RationalOutwardInterval.ConvergesTo
        (input index) (value index))
    (hencloses : ∀ precision index,
      (input index precision).Encloses (value index)) :
    ∃ order : ℕ → ℕ,
      (∀ precision, 0 < order precision) ∧
        ∀ index,
          RationalOutwardInterval.ConvergesTo
            (fun precision =>
              ofInputInterval
                (input index precision)
                precision
                (order precision))
            (Real.exp (value index)) := by
  classical
  letI := Fintype.ofFinite ι
  have hpower :
      ∀ᶠ precision in atTop,
        ∀ index ∈ (Finset.univ : Finset ι),
          PowerSufficient
              (input index precision).lower precision ∧
            PowerSufficient
              (input index precision).upper precision := by
    rw [Finset.eventually_all]
    intro index _hindex
    exact
      (eventually_powerSufficient_of_tendsto
        (hconverges index).1).and
      (eventually_powerSufficient_of_tendsto
        (hconverges index).2)
  have hstage :
      ∀ precision, ∃ order : ℕ,
        0 < order ∧
          ((∀ index,
              PowerSufficient
                  (input index precision).lower precision ∧
                PowerSufficient
                  (input index precision).upper precision) →
            ∀ index,
              ((ofInputInterval
                (input index precision)
                precision order).width : ℝ) <
                (Real.exp ((input index precision).upper : ℝ) -
                  Real.exp ((input index precision).lower : ℝ)) +
                  1 / ((precision + 1 : ℕ) : ℝ)) := by
    intro precision
    by_cases hprecision :
        ∀ index,
          PowerSufficient
              (input index precision).lower precision ∧
            PowerSufficient
              (input index precision).upper precision
    · obtain ⟨order, horder, hwidth⟩ :=
        exists_common_order_width_lt
          (fun index => input index precision)
          precision hprecision
          (tolerance := 1 / ((precision + 1 : ℕ) : ℝ))
          (by positivity)
      exact ⟨order, horder, fun _ => hwidth⟩
    · exact ⟨1, by norm_num, fun hp => (hprecision hp).elim⟩
  choose order horder using hstage
  refine ⟨order, fun precision => (horder precision).1, ?_⟩
  intro index
  have hpowerAll :
      ∀ᶠ precision in atTop,
        ∀ index,
          PowerSufficient
              (input index precision).lower precision ∧
            PowerSufficient
              (input index precision).upper precision :=
    hpower.mono fun _ hprecision index =>
      hprecision index (Finset.mem_univ index)
  have houtEncloses :
      ∀ᶠ precision in atTop,
        (ofInputInterval
          (input index precision)
          precision
          (order precision)).Encloses
          (Real.exp (value index)) :=
    hpowerAll.mono fun precision hprecision =>
      ofInputInterval_encloses
        precision (order precision)
        (hencloses precision index)
        (hprecision index).1
        (hprecision index).2
        (horder precision).1
  have hspread :
      Tendsto
        (fun precision =>
          Real.exp ((input index precision).upper : ℝ) -
            Real.exp ((input index precision).lower : ℝ))
        atTop
        (𝓝 0) := by
    have hlower :=
      (Real.continuous_exp.tendsto (value index)).comp
        (hconverges index).1
    have hupper :=
      (Real.continuous_exp.tendsto (value index)).comp
        (hconverges index).2
    simpa using hupper.sub hlower
  have htolerance :
      Tendsto
        (fun precision : ℕ =>
          1 / ((precision + 1 : ℕ) : ℝ))
        atTop
        (𝓝 0) := by
    simpa using
      (tendsto_one_div_add_atTop_nhds_zero_nat (𝕜 := ℝ))
  have hwidth :
      Tendsto
        (fun precision =>
          ((ofInputInterval
            (input index precision)
            precision
            (order precision)).width : ℝ))
        atTop
        (𝓝 0) := by
    have hsqueeze :
        Tendsto
          (fun precision =>
            ((ofInputInterval
              (input index precision)
              precision
              (order precision)).width : ℝ))
          atTop
          (𝓝 (0 + 0)) := by
      apply tendsto_of_tendsto_of_tendsto_of_le_of_le'
        tendsto_const_nhds (hspread.add htolerance)
      · filter_upwards [houtEncloses] with precision hprecision
        have hvalid :
            (ofInputInterval
              (input index precision)
              precision
              (order precision)).Valid := by
          exact_mod_cast hprecision.1.trans hprecision.2
        exact_mod_cast
          (RationalOutwardInterval.valid_iff_width_nonnegative.mp hvalid)
      · filter_upwards [hpowerAll] with precision hprecision
        exact le_of_lt ((horder precision).2 hprecision index)
    simpa using hsqueeze
  exact
    RationalOutwardInterval.convergesTo_of_encloses_of_tendsto_width
      houtEncloses hwidth

end RationalExpInterval

end DP
end Mf
