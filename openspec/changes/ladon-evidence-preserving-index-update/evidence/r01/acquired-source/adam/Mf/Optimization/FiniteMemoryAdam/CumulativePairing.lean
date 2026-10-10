import Mf.Optimization.FiniteMemoryAdam.HistoryBound

/-!
# Signed pairing for cumulative initialized Adam

The cumulative argument proposed in the R20 independent review, Technical
Appendix Sections 5–8 (scope recorded in the active OpenSpec change
`finite-adam-cumulative-signed-memory-utility`), controls a denominator ceiling
only after checking the sign of the numerator. These deterministic inequalities
retain the residual's adverse sign and pay for denominator exceptions using a
nonnegative per-update charge. They assume neither centered residuals nor
independence from the denominator. The actual initialized-history cap is valid
for every horizon and every real release sequence.
-/

namespace Mf.Optimization.FiniteMemoryAdam.Cumulative
noncomputable section
open Mf.Optimization.SDE.DPAdamFixedBetaCoupledCorrectedMoments

/-- Sign-sensitive pairing with the actual numerator and denominator retained. -/
theorem pairing_lower {g M D A B H m G K n : ℝ}
    (hm : 0 < m) (hA : m ≤ A) (hB : 0 < B) (hBH : B ≤ H)
    (hG : |g| ≤ G) (hK : |D| ≤ K)
    (hM : M = A * g + n) (hD : D = M / B) :
    m / H * g ^ 2 - (G / H + K / m) * |n| ≤ g * D := by
  have hH : 0 < H := hB.trans_le hBH
  have hG0 : 0 ≤ G := (abs_nonneg g).trans hG
  have hK0 : 0 ≤ K := (abs_nonneg D).trans hK
  have hnum : m * g ^ 2 - G * |n| ≤ g * M := by
    have hgn := neg_abs_le (g * n)
    rw [abs_mul] at hgn
    have hgG := mul_le_mul_of_nonneg_right hG (abs_nonneg n)
    have ham := mul_le_mul_of_nonneg_right hA (sq_nonneg g)
    rw [hM]
    nlinarith
  have hid : g * D = (g * M) / B := by rw [hD]; ring
  by_cases hsign : 0 ≤ g * M
  · have hd := div_le_div_of_nonneg_left hsign hB hBH
    have hl := div_le_div_of_nonneg_right hnum hH.le
    have he : (m * g ^ 2 - G * |n|) / H = m / H * g ^ 2 - G / H * |n| := by ring
    rw [he] at hl
    have hk : 0 ≤ K / m * |n| := mul_nonneg (div_nonneg hK0 hm.le) (abs_nonneg n)
    rw [hid]
    nlinarith
  · have hsign' : g * M < 0 := lt_of_not_ge hsign
    have hg0 : g ≠ 0 := by intro h; simp [h] at hsign'
    have hga : 0 < |g| := abs_pos.mpr hg0
    have hgn := neg_abs_le (g * n)
    rw [abs_mul] at hgn
    have ham := mul_le_mul_of_nonneg_right hA (sq_nonneg g)
    have hma : m * |g| ≤ |n| := by
      apply (mul_le_mul_iff_left₀ hga).mp
      rw [hM] at hsign'
      nlinarith [sq_abs g]
    have hgaN : |g| ≤ |n| / m := (le_div_iff₀ hm).mpr (by simpa [mul_comm] using hma)
    have hgD : -(|g| * K) ≤ g * D := by
      have h := neg_abs_le (g * D)
      rw [abs_mul] at h
      have hh := mul_le_mul_of_nonneg_left hK (abs_nonneg g)
      linarith
    have hneg : -(K / m * |n|) ≤ g * D := by
      have hh := mul_le_mul_of_nonneg_right hgaN hK0
      have he : |n| / m * K = K / m * |n| := by ring
      rw [he] at hh
      linarith
    have hbase : m / H * g ^ 2 - G / H * |n| ≤ 0 := by
      have hh : m * g ^ 2 - G * |n| ≤ 0 := hnum.trans hsign'.le
      have hd := div_nonpos_of_nonpos_of_nonneg hh hH.le
      have he : (m * g ^ 2 - G * |n|) / H = m / H * g ^ 2 - G / H * |n| := by ring
      rwa [he] at hd
    nlinarith

/-- A nonnegative per-update charge pays for every denominator exception. -/
theorem pairing_lower_with_charge {g M D A B H m G K n Q : ℝ}
    (hm : 0 < m) (hA : m ≤ A) (hB : 0 < B) (hH : 0 < H)
    (hG : |g| ≤ G) (hK : |D| ≤ K) (hQ : 0 ≤ Q)
    (hgood : Q < 1 → B ≤ H)
    (hM : M = A * g + n) (hD : D = M / B) :
    m / H * g ^ 2 - (G / H + K / m) * |n| -
      (m / H * G ^ 2 + K * G) * Q ≤ g * D := by
  have hG0 : 0 ≤ G := (abs_nonneg g).trans hG
  have hK0 : 0 ≤ K := (abs_nonneg D).trans hK
  have ha : 0 ≤ m / H := div_nonneg hm.le hH.le
  have hb : 0 ≤ (G / H + K / m) * |n| := by positivity
  have hc : 0 ≤ m / H * G ^ 2 + K * G := by positivity
  by_cases hsmall : Q < 1
  · have hp := pairing_lower hm hA hB (hgood hsmall) hG hK hM hD
    have hcharge := mul_nonneg hc hQ
    linarith
  · have hQ1 : 1 ≤ Q := le_of_not_gt hsmall
    have hsq : g ^ 2 ≤ G ^ 2 := by
      simpa only [sq_abs] using (sq_le_sq₀ (abs_nonneg g) hG0).mpr hG
    have hsq' := mul_le_mul_of_nonneg_left hsq ha
    have hc' := mul_le_mul_of_nonneg_left hQ1 hc
    have hp : -(K * G) ≤ g * D := by
      have h := neg_abs_le (g * D)
      rw [abs_mul] at h
      have hh := mul_le_mul hG hK (abs_nonneg D) hG0
      nlinarith
    nlinarith

/-- Default corrected memories supply an all-history, all-horizon cap. -/
theorem default_history_direction_cap {ζ : ℝ} (hζ : 0 < ζ)
    (y : ℕ → ℝ) (t : ℕ) :
    |scalarDirection (9/10) (999/1000) ζ (t+1)
      (firstHistory (9/10) y t) (secondHistory (999/1000) y t) (y t)| ≤ 73/10 := by
  have h := historyDirection_sq_le_uniform (by norm_num : (0:ℝ) ≤ 9/10)
    (by norm_num : (9/10:ℝ) < 1) (by norm_num : (999/1000:ℝ) < 1)
    (by norm_num : (9/10:ℝ)^2 < 999/1000) hζ y t
  norm_num [correctedMomentCouplingUniformConstant] at h
  exact (abs_le.mpr ⟨by nlinarith, by nlinarith⟩)

end
end Mf.Optimization.FiniteMemoryAdam.Cumulative

/- index-history-field repetition adam 1 -/

/- index-history-field repetition adam 2 -/

/- index-history-field repetition adam 3 -/

-- root ordinary storage observation

-- installed v0.2.2 preservation smoke

-- installed v0.2.2 preservation smoke
