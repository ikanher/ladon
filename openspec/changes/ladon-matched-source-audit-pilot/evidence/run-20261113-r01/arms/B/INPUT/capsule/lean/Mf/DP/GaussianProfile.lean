import Mf.DP.StandardGaussianCore
import Mf.DP.FiniteGaussianPrivacy

/-!
# Gaussian privacy profile and supporting-line identities

The scalar profile is the analytic Gaussian expression at unit variance.
Curve and reflection identities hold at every real epsilon for positive
Gaussian parameter. Nonnegativity follows from the attained one-dimensional
likelihood region in the generic finite Gaussian comparison owner; no sampling
accountant or matrix mechanism is involved. The definition remains total at
zero, where it is not asserted to be a valid privacy profile for every epsilon.

These are the Gaussian differential privacy profiles of Dong, Roth and Su,
*Gaussian Differential Privacy* (2019), with source retained under
`paper/theory/mu-dp/`.
-/

namespace Mf.DP
open Mf.Probability.FiniteGaussian Mf.DP.FiniteGaussianPrivacyBasis
open Mf.DP.FiniteGaussianPrivacy
noncomputable section

/-- GDP privacy profile parameterized by the scalar Gaussian parameter `μ`. -/
def gdpProfile (μ ε : ℝ) : ℝ :=
  analyticGaussianExpr μ 1 ε

/-- First standard-normal CDF argument in the scalar GDP profile. -/
def gdpProfileCDFPlusArg (μ ε : ℝ) : ℝ :=
  μ / 2 - ε / μ

/-- Second standard-normal CDF argument in the scalar GDP profile. -/
def gdpProfileCDFMinusArg (μ ε : ℝ) : ℝ :=
  -μ / 2 - ε / μ

/-- Curve identity (F1): with `ε = μ t - μ²/2`,
`1 - δG(ε) = Φ(t-μ) + e^ε Φ(-t)`. Only `Φ(-x) = 1 - Φ(x)` is used. -/
theorem gdpProfile_curve {μ : ℝ} (hμ : 0 < μ) (t : ℝ) :
    1 - gdpProfile μ (μ * t - μ ^ 2 / 2)
      = stdNormalCDFReal (t - μ)
        + Real.exp (μ * t - μ ^ 2 / 2) * stdNormalCDFReal (-t) := by
  have hμ0 : μ ≠ 0 := hμ.ne'
  have hp : privacyLossArgPlus μ 1 (μ * t - μ ^ 2 / 2) = -(t - μ) := by
    unfold privacyLossArgPlus
    field_simp
    ring
  have hm : privacyLossArgMinus μ 1 (μ * t - μ ^ 2 / 2) = -t := by
    unfold privacyLossArgMinus
    field_simp
    ring
  unfold gdpProfile analyticGaussianExpr
  rw [hp, hm, stdNormalCDFReal_neg (t - μ)]
  ring

/-- Reflection identity (F3): `δG(ε) = 1 - e^ε + e^ε δG(-ε)` for every real `ε`. -/
theorem gdpProfile_reflect {μ : ℝ} (hμ : 0 < μ) (ε : ℝ) :
    gdpProfile μ ε = 1 - Real.exp ε + Real.exp ε * gdpProfile μ (-ε) := by
  -- write ε = μ t - μ²/2 and -ε = μ (μ - t) - μ²/2, then use F1 twice.
  set t : ℝ := ε / μ + μ / 2 with ht
  have h1 : μ * t - μ ^ 2 / 2 = ε := by
    rw [ht]; field_simp; ring
  have h2 : μ * (μ - t) - μ ^ 2 / 2 = -ε := by
    rw [ht]; field_simp; ring
  have c1 := gdpProfile_curve hμ t
  have c2 := gdpProfile_curve hμ (μ - t)
  rw [h1] at c1
  rw [h2] at c2
  have e1 : μ - t - μ = -t := by ring
  have e2 : -(μ - t) = t - μ := by ring
  rw [e1, e2] at c2
  have hexp : Real.exp ε * Real.exp (-ε) = 1 := by
    rw [← Real.exp_add]; simp
  -- c1 : 1 - δ ε = Φ(t-μ) + e^ε Φ(-t);  c2 : 1 - δ(-ε) = Φ(-t) + e^{-ε} Φ(t-μ)
  have : Real.exp ε * (1 - gdpProfile μ (-ε))
      = Real.exp ε * stdNormalCDFReal (-t) + stdNormalCDFReal (t - μ) := by
    rw [c2, mul_add, ← mul_assoc, hexp, one_mul]
  linear_combination this - c1

/-- The Gaussian profile is nonnegative for positive parameter, for every real epsilon. -/
theorem gdpProfile_nonneg_of_pos
    (μ ε : ℝ)
    (hμ : 0 < μ) :
    0 ≤ gdpProfile μ ε := by
  let d : Vector 1 := fun _ => μ / 2
  let r : ℝ := (μ / 2) ^ 2
  let j : Set (Vector 1) :=
    posRegion
      (fun y : Vector 1 =>
        density 1 d y
          - Real.exp ε * density 1 (fun i => -d i) y)
  have hr : 0 < r := by
    unfold r
    positivity
  have hrEq : r = sqDist d (fun _ => (0 : ℝ)) := by
    unfold r d
    simp [sqDist]
  have hj : MeasurableSet j := by
    unfold j
    exact measurableSet_centered_privacyLoss_posRegion
      (d := d) (σ := 1) (ε := ε) (by norm_num)
  have hgap_nonneg :
      0 ≤ (measure 1 d).real j
            - Real.exp ε * (measure 1 (fun i => -d i)).real j := by
    exact centered_posRegion_hahn_nonneg_of_pos
      (d := d) (σ := 1) (ε := ε) (by norm_num)
      hj
      (by
        intro y hy
        exact hy)
  have hgap_eq :
      (measure 1 d).real j
        - Real.exp ε * (measure 1 (fun i => -d i)).real j
        = gdpProfile μ ε := by
    calc
      (measure 1 d).real j
        - Real.exp ε * (measure 1 (fun i => -d i)).real j
          =
        (stdNormalMeasure.real
            (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) 1 ε))
          - Real.exp ε
              * stdNormalMeasure.real
                  (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) 1 ε))) := by
            unfold j
            exact centered_posRegion_gap_eq_explicitEventExpr_two_sqrt
              (d := d) (r := r) (σ := 1) (ε := ε) (by norm_num) hr hrEq
      _ = bridgeProfile (Real.sqrt r / 1) ε := by
            exact explicitEventExpr_two_sqrt_eq_bridgeProfile r 1 ε (by norm_num) hr
      _ = bridgeProfile (μ / 2) ε := by
            unfold r
            have hsqrt : Real.sqrt ((μ / 2) ^ 2) = μ / 2 := by
              rw [Real.sqrt_sq_eq_abs, abs_of_pos (by linarith)]
            simp [hsqrt]
      _ = gdpProfile μ ε := by
            have htwo : 2 * (μ / 2) = μ := by ring
            simp [bridgeProfile, bridgeU, bridgeV, gdpProfile,
              analyticGaussianExpr, privacyLossArgPlus, privacyLossArgMinus, htwo, neg_div]
  have : 0 ≤ (measure 1 d).real j
      - Real.exp ε * (measure 1 (fun i => -d i)).real j := hgap_nonneg
  rw [hgap_eq] at this
  exact this

/-- The finite Gaussian profile is strictly below one. -/
theorem gdpProfile_lt_one (μ ε : ℝ) : gdpProfile μ ε < 1 := by
  unfold gdpProfile analyticGaussianExpr
  have h1 := lt_of_lt_of_le
    (strictMono_stdNormalCDFReal (lt_add_one (privacyLossArgPlus μ 1 ε)))
    (stdNormalCDFReal_le_one _)
  have h2 := mul_nonneg (Real.exp_pos ε).le
    (stdNormalCDFReal_nonneg (privacyLossArgMinus μ 1 ε))
  linarith


/-- Positive-parameter Gaussian profiles equal the neutral finite-Gaussian bridge profile. -/
theorem gdpProfile_eq_finiteGaussianBridgeProfile {μ ε : ℝ} (hμ : μ ≠ 0) :
    gdpProfile μ ε = FiniteGaussianPrivacy.bridgeProfile (μ / 2) ε := by
  have hU : μ / 2 - ε / μ = FiniteGaussianPrivacy.bridgeU (μ / 2) ε := by
    unfold FiniteGaussianPrivacy.bridgeU
    field_simp [hμ]
  have hV : -μ / 2 - ε / μ = FiniteGaussianPrivacy.bridgeV (μ / 2) ε := by
    unfold FiniteGaussianPrivacy.bridgeV
    field_simp [hμ]
  simp only [gdpProfile, analyticGaussianExpr, privacyLossArgPlus, privacyLossArgMinus,
    FiniteGaussianPrivacy.bridgeProfile]
  norm_num only [one_pow, mul_one, div_one]
  rw [hU, hV]

/--
The scalar GDP profile is monotone in the positive GDP parameter.

The proof is a direct transport of `FiniteGaussianPrivacy.strictMonoOn_bridgeProfile`
through `gdpProfile_eq_finiteGaussianBridgeProfile`.
-/
theorem gdpProfile_monoOn_pos
    (ε : ℝ) :
    MonotoneOn (fun μ : ℝ => gdpProfile μ ε) (Set.Ioi 0) := by
  intro μ hμ ν hν hle
  have hμ_ne : μ ≠ 0 := (ne_of_gt hμ)
  have hν_ne : ν ≠ 0 := (ne_of_gt hν)
  change gdpProfile μ ε ≤ gdpProfile ν ε
  rw [gdpProfile_eq_finiteGaussianBridgeProfile (μ := μ) (ε := ε) hμ_ne]
  rw [gdpProfile_eq_finiteGaussianBridgeProfile (μ := ν) (ε := ε) hν_ne]
  have hμ_pos : 0 < μ := by simpa using hμ
  have hν_pos : 0 < ν := by simpa using hν
  have hμ_half : μ / 2 ∈ Set.Ioi (0 : ℝ) := by
    exact div_pos hμ_pos (by norm_num)
  have hν_half : ν / 2 ∈ Set.Ioi (0 : ℝ) := by
    exact div_pos hν_pos (by norm_num)
  have hhalf_le : μ / 2 ≤ ν / 2 := by
    exact div_le_div_of_nonneg_right hle (by norm_num)
  exact (strictMonoOn_bridgeProfile ε).monotoneOn hμ_half hν_half hhalf_le


end
end Mf.DP
