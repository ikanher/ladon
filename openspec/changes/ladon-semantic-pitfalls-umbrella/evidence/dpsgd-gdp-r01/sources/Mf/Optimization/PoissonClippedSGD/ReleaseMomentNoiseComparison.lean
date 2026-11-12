import Mf.Optimization.PoissonClippedSGD.FreshReleaseMoments

/-!
# Noise scaling of the exact release-moment ceilings

The GDP-informed Adam response r01, *A complete balanced-quadratic Adam
envelope on an explicit stabilizer regime*, Corollary 8 (2026-10-25), uses
the nonnegative coefficients of M2 and M4 in the coordinate noise variance.
These release-level inequalities are independent of the optimizer consuming them.
-/

set_option autoImplicit false
namespace Mf.Optimization.PoissonClippedSGD

theorem normalizedCountMoment_nonneg (n m : ℕ) {q : ℝ}
    (hq : 0 ≤ q) (hq1 : q ≤ 1) : 0 ≤ normalizedCountMoment n m q := by
  exact div_nonneg (Mf.DP.poissonParticipationCountMoment_nonneg n m hq hq1)
    (pow_nonneg (mul_nonneg hq (Nat.cast_nonneg n)) m)

theorem releaseSecondMoment_nonneg (n d : ℕ) {q : ℝ}
    (hq : 0 ≤ q) (hq1 : q ≤ 1) (C σ : ℝ) :
    0 ≤ releaseSecondMoment n d q C σ := by
  have := normalizedCountMoment_nonneg n 2 hq hq1
  unfold releaseSecondMoment
  positivity

theorem releaseFourthMoment_nonneg (n d : ℕ) {q : ℝ}
    (hq : 0 ≤ q) (hq1 : q ≤ 1) (C σ : ℝ) :
    0 ≤ releaseFourthMoment n d q C σ := by
  have := normalizedCountMoment_nonneg n 2 hq hq1
  have := normalizedCountMoment_nonneg n 4 hq hq1
  unfold releaseFourthMoment
  positivity

/-- A variance cap scales the second release ceiling by the same factor. -/
theorem releaseSecondMoment_noise_le (n d : ℕ) {q C σ₁ σ₂ k : ℝ}
    (hq : 0 ≤ q) (hq1 : q ≤ 1) (hk : 1 ≤ k)
    (hσ : σ₂^2 ≤ k*σ₁^2) :
    releaseSecondMoment n d q C σ₂ ≤ k*releaseSecondMoment n d q C σ₁ := by
  have hbase : 0 ≤ C^2*normalizedCountMoment n 2 q :=
    mul_nonneg (sq_nonneg C) (normalizedCountMoment_nonneg n 2 hq hq1)
  have hd := mul_le_mul_of_nonneg_left hσ (Nat.cast_nonneg d : (0:ℝ) ≤ d)
  unfold releaseSecondMoment
  nlinarith [mul_nonneg (sub_nonneg.mpr hk) hbase]

/-- A variance cap scales the fourth release ceiling by its square. -/
theorem releaseFourthMoment_noise_le (n d : ℕ) {q C σ₁ σ₂ k : ℝ}
    (hq : 0 ≤ q) (hq1 : q ≤ 1) (hk : 1 ≤ k)
    (hσ : σ₂^2 ≤ k*σ₁^2) :
    releaseFourthMoment n d q C σ₂ ≤ k^2*releaseFourthMoment n d q C σ₁ := by
  have hk0 : 0 ≤ k := by linarith
  have hk2 : 1 ≤ k^2 := by nlinarith
  have hbase : 0 ≤ C^4*normalizedCountMoment n 4 q :=
    mul_nonneg (by positivity) (normalizedCountMoment_nonneg n 4 hq hq1)
  have hc : 0 ≤ 2*((d:ℝ)+2)*(C^2*normalizedCountMoment n 2 q) := by
    have := normalizedCountMoment_nonneg n 2 hq hq1
    positivity
  have hσ' : σ₂^2 ≤ k^2*σ₁^2 := by
    nlinarith [mul_nonneg (by nlinarith : 0 ≤ k^2-k) (sq_nonneg σ₁)]
  have hfour : σ₂^4 ≤ k^2*σ₁^4 := by
    have hh := pow_le_pow_left₀ (sq_nonneg σ₂) hσ 2
    nlinarith only [hh]
  have hcross := mul_le_mul_of_nonneg_left hσ' hc
  have hlast := mul_le_mul_of_nonneg_left hfour
    (show 0 ≤ (d:ℝ)*((d:ℝ)+2) by positivity)
  unfold releaseFourthMoment
  nlinarith only [hcross, hlast, mul_nonneg (sub_nonneg.mpr hk2) hbase]

end Mf.Optimization.PoissonClippedSGD
