import Mf.DP.GaussianDP
import Mf.DP.GaussianDPProductBounds

namespace Mf
namespace DP

noncomputable section

/-!
# A universal linear Gaussian privacy-profile bound

This deliberately conservative bound is useful for constructive total
calibration: it avoids numerical CDF evaluation while still converging to zero
as the signal-to-noise ratio tends to zero.
-/

/-- The standard-normal density is universally bounded by `1 / 2`. -/
theorem stdNormalPdfReal_le_one_half (x : ℝ) :
    stdNormalPdfReal x ≤ 1 / 2 := by
  have hexp : Real.exp (-(x ^ 2) / 2) ≤ 1 := by
    rw [Real.exp_le_one_iff]
    nlinarith [sq_nonneg x]
  have hpdf :
      stdNormalPdfReal x ≤
        (39894228040144 : ℝ) / 100000000000000 := by
    simpa using
      (stdNormalPdfReal_le_of_exp_neg_sq_half_le
        (x := x) (expUpper := (1 : ℝ)) hexp)
  exact hpdf.trans (by norm_num)

/-- A rational `1 / 2` Lipschitz bound for the standard-normal CDF. -/
theorem stdNormalCDFReal_sub_le_half_mul_sub
    {x y : ℝ}
    (hxy : x ≤ y) :
    stdNormalCDFReal y - stdNormalCDFReal x ≤ (y - x) / 2 := by
  have hnorm :
      ‖stdNormalCDFReal y - stdNormalCDFReal x‖ ≤
        (1 / 2 : ℝ) * ‖y - x‖ := by
    exact convex_univ.norm_image_sub_le_of_norm_hasDerivWithin_le
      (f := stdNormalCDFReal)
      (f' := stdNormalPdfReal)
      (fun z _hz => (hasDerivAt_stdNormalCDFReal z).hasDerivWithinAt)
      (fun z _hz => by
        rw [Real.norm_eq_abs, abs_of_pos (stdNormalPdfReal_pos z)]
        exact stdNormalPdfReal_le_one_half z)
      (Set.mem_univ x) (Set.mem_univ y)
  have hdiff_nonneg :
      0 ≤ stdNormalCDFReal y - stdNormalCDFReal x :=
    sub_nonneg.mpr (stdNormalCDFReal_mono hxy)
  have harg_nonneg : 0 ≤ y - x := sub_nonneg.mpr hxy
  have hnorm' :
      stdNormalCDFReal y - stdNormalCDFReal x ≤
        (1 / 2 : ℝ) * (y - x) := by
    simpa [Real.norm_eq_abs, abs_of_nonneg hdiff_nonneg,
      abs_of_nonneg harg_nonneg] using hnorm
  linarith

/--
For nonnegative GDP parameter and privacy budget, the Gaussian privacy profile
is at most half the GDP parameter.
-/
theorem gdpProfile_le_mu_div_two
    {μ ε : ℝ}
    (hμ : 0 ≤ μ)
    (hε : 0 ≤ ε) :
    gdpProfile μ ε ≤ μ / 2 := by
  have hexp : 1 ≤ Real.exp ε := Real.one_le_exp hε
  have hminus_nonneg :
      0 ≤ stdNormalCDFReal (gdpProfileCDFMinusArg μ ε) :=
    stdNormalCDFReal_nonneg _
  have hscale :
      stdNormalCDFReal (gdpProfileCDFMinusArg μ ε) ≤
        Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε) := by
    simpa [one_mul] using
      (mul_le_mul_of_nonneg_right hexp hminus_nonneg)
  have hprofile :
      gdpProfile μ ε ≤
        stdNormalCDFReal (gdpProfileCDFPlusArg μ ε) -
          stdNormalCDFReal (gdpProfileCDFMinusArg μ ε) := by
    rw [gdpProfile_eq]
    exact sub_le_sub_left hscale _
  have hargs :
      gdpProfileCDFMinusArg μ ε ≤ gdpProfileCDFPlusArg μ ε := by
    unfold gdpProfileCDFMinusArg gdpProfileCDFPlusArg
    linarith
  have hcdf := stdNormalCDFReal_sub_le_half_mul_sub hargs
  have hwidth :
      gdpProfileCDFPlusArg μ ε - gdpProfileCDFMinusArg μ ε = μ := by
    unfold gdpProfileCDFPlusArg gdpProfileCDFMinusArg
    ring
  rw [hwidth] at hcdf
  exact hprofile.trans hcdf

end

end DP
end Mf
