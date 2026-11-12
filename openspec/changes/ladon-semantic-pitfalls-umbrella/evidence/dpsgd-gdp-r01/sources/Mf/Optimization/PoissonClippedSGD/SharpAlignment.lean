import Mf.Optimization.PoissonClippedSGD.Alignment

/-!
# Sharper alignment of the full-vector clipped population mean

The quarter-margin displacement bound gives the stronger small-gradient bias
premise used by the three-regime alignment. The public theorem derives both
mean-level premises from the same raw finite-population variance assumption as
`clippedMean_alignment` in `Alignment.lean`.
-/

namespace Mf.Optimization.PoissonClippedSGD

noncomputable section

open scoped BigOperators
open Mf.DP

/-- Quarter-margin clipping displacement: `(a - m)_+ ≤ a²/(4m)`. -/
theorem norm_sub_clip_le_sq_div_four_margin {d : ℕ}
    (c : ℝ) (x v : EuclideanSpace ℝ (Fin d))
    (hmargin : 0 < c - ‖v‖) :
    ‖x - euclideanBallClip c x‖ ≤ ‖x - v‖ ^ 2 / (4 * (c - ‖v‖)) := by
  by_cases hx : ‖x‖ ≤ c
  · simp only [euclideanBallClip, if_pos hx, sub_self, norm_zero]
    positivity
  · have hc_lt : c < ‖x‖ := lt_of_not_ge hx
    have hxpos : 0 < ‖x‖ := by
      have := norm_nonneg v
      linarith
    have hres : ‖x - euclideanBallClip c x‖ = ‖x‖ - c := by
      rw [euclideanBallClip, if_neg hx]
      rw [show x - (c / ‖x‖) • x = (1 - c / ‖x‖) • x by module,
        norm_smul, Real.norm_eq_abs]
      have hratio : c / ‖x‖ < 1 := (div_lt_one hxpos).2 hc_lt
      rw [abs_of_nonneg (by linarith : 0 ≤ 1 - c / ‖x‖)]
      field_simp [hxpos.ne']
    have htri : ‖x‖ ≤ ‖x - v‖ + ‖v‖ := by
      calc
        ‖x‖ = ‖(x - v) + v‖ := by congr 1; abel
        _ ≤ ‖x - v‖ + ‖v‖ := norm_add_le _ _
    rw [hres, le_div_iff₀ (by positivity)]
    nlinarith [sq_nonneg (‖x - v‖ - 2 * (c - ‖v‖))]

/-- Averaged quarter-margin bias bound. -/
theorem norm_clippedMean_sub_mean_le_quarter {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (c : ℝ)
    (hmargin : 0 < c - ‖vectorMean g‖) :
    ‖clippedMean c g - vectorMean g‖ ≤
      meanSqDeviation g (vectorMean g) / (4 * (c - ‖vectorMean g‖)) := by
  rw [norm_sub_rev]
  change ‖vectorMean g - vectorMean (fun i => euclideanBallClip c (g i))‖ ≤ _
  rw [← vectorMean_sub]
  calc
    _ ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i - euclideanBallClip c (g i)‖ :=
      norm_vectorMean_le _
    _ ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i - vectorMean g‖ ^ 2 / (4 * (c - ‖vectorMean g‖)) := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      exact Finset.sum_le_sum fun i _ =>
        norm_sub_clip_le_sq_div_four_margin c _ _ hmargin
    _ = meanSqDeviation g (vectorMean g) / (4 * (c - ‖vectorMean g‖)) := by
      simp [meanSqDeviation, Finset.sum_div, mul_div_assoc]

/-- Half-radius regime (closed): bias at most `σ²/(2c)`. -/
theorem norm_clippedMean_sub_mean_le_of_half {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (c sigma : ℝ) (hc : 0 < c)
    (hsmall : ‖vectorMean g‖ ≤ c / 2)
    (hvariance : meanSqDeviation g (vectorMean g) ≤ sigma ^ 2) :
    ‖clippedMean c g - vectorMean g‖ ≤ sigma ^ 2 / (2 * c) := by
  have hm : 0 < c - ‖vectorMean g‖ := by linarith
  calc
    _ ≤ meanSqDeviation g (vectorMean g) / (4 * (c - ‖vectorMean g‖)) :=
      norm_clippedMean_sub_mean_le_quarter g c hm
    _ ≤ sigma ^ 2 / (4 * (c / 2)) := by
      gcongr
      linarith
    _ = sigma ^ 2 / (2 * c) := by ring

/-- Geometric three-regime sharpening of `alignment_of_clipping_bias`. -/
theorem alignment_of_clipping_bias_sharp {d : ℕ}
    (v mu : EuclideanSpace ℝ (Fin d)) (c sigma : ℝ)
    (hc : 0 < c) (hsigma : 0 ≤ sigma) (hclip : 4 * sigma ≤ c)
    (hproj : ‖mu - euclideanBallClip c v‖ ^ 2 ≤ sigma ^ 2)
    (hsmall : ‖v‖ ≤ c / 2 → ‖mu - v‖ ≤ sigma ^ 2 / (2 * c)) :
    (3 / 8 : ℝ) * min (‖v‖ ^ 2) (c * ‖v‖) +
        (1 / 2 : ℝ) * ‖mu‖ ^ 2 - sigma ^ 4 / (8 * c ^ 2) ≤
      inner ℝ v mu := by
  set r : ℝ := ‖v‖ with hr
  have hr0 : 0 ≤ r := norm_nonneg _
  have hsig4 : sigma ≤ c / 4 := by linarith
  have hpolar : ‖mu - v‖ ^ 2 = ‖mu‖ ^ 2 - 2 * inner ℝ v mu + r ^ 2 := by
    simpa [r, real_inner_comm] using norm_sub_sq_real mu v
  have hb0 : 0 ≤ sigma ^ 4 / (8 * c ^ 2) := by positivity
  by_cases hs : r ≤ c / 2
  · have hmin : min (r ^ 2) (c * r) = r ^ 2 := min_eq_left (by nlinarith)
    rw [hmin]
    have hb := hsmall hs
    have hsq : ‖mu - v‖ ^ 2 ≤ (sigma ^ 2 / (2 * c)) ^ 2 :=
      (sq_le_sq₀ (norm_nonneg _) (by positivity)).2 hb
    have hval : (sigma ^ 2 / (2 * c)) ^ 2 = 2 * (sigma ^ 4 / (8 * c ^ 2)) := by
      field_simp; ring
    nlinarith [sq_nonneg r]
  · have hlt : c / 2 < r := lt_of_not_ge hs
    by_cases hm : r ≤ c
    · have hmin : min (r ^ 2) (c * r) = r ^ 2 := min_eq_left (by nlinarith)
      rw [hmin]
      have hclipv : euclideanBallClip c v = v := by
        simp [euclideanBallClip, show ‖v‖ ≤ c from hm]
      rw [hclipv] at hproj
      have hsr : sigma ^ 2 ≤ r ^ 2 / 4 := by nlinarith
      nlinarith
    · have hcr : c < r := lt_of_not_ge hm
      have hmin : min (r ^ 2) (c * r) = c * r := min_eq_right (by nlinarith)
      rw [hmin]
      have hrpos : 0 < r := lt_trans hc hcr
      have hclipv : euclideanBallClip c v = (c / r) • v := by
        simp [euclideanBallClip, r, show ¬ ‖v‖ ≤ c from not_le_of_gt hcr]
      rw [hclipv] at hproj
      have hexp : ‖mu - (c / r) • v‖ ^ 2 =
          ‖mu‖ ^ 2 - 2 * (c / r) * inner ℝ v mu + (c / r) ^ 2 * r ^ 2 := by
        rw [norm_sub_sq_real, inner_smul_right, norm_smul, Real.norm_eq_abs,
          abs_of_nonneg (by positivity : 0 ≤ c / r), real_inner_comm]
        ring
      have hcr2 : (c / r) ^ 2 * r ^ 2 = c ^ 2 := by field_simp
      rw [hexp, hcr2] at hproj
      -- (c/r) ⟪v,μ⟫ ≥ (‖μ‖² + c² - σ²)/2; multiply by r/c.
      have hkey : c * inner ℝ v mu ≥ r * (‖mu‖ ^ 2 + c ^ 2 - sigma ^ 2) / 2 := by
        have h1 : 2 * (c / r) * inner ℝ v mu ≥ ‖mu‖ ^ 2 + c ^ 2 - sigma ^ 2 := by
          linarith
        have h2 : 2 * (c / r) * inner ℝ v mu * r = 2 * c * inner ℝ v mu := by
          field_simp
        nlinarith
      have hsigc : sigma ^ 2 ≤ c ^ 2 / 16 := by nlinarith
      have hmu : r * ‖mu‖ ^ 2 ≥ c * ‖mu‖ ^ 2 := by
        nlinarith [sq_nonneg ‖mu‖]
      -- c ⟪v,μ⟫ ≥ (c‖μ‖² + r c² - r c²/16)/2 = c(‖μ‖²/2 + 15 r c /32)
      have hfinal : inner ℝ v mu ≥ ‖mu‖ ^ 2 / 2 + 15 * c * r / 32 := by
        have : c * inner ℝ v mu ≥ c * (‖mu‖ ^ 2 / 2 + 15 * c * r / 32) := by
          nlinarith
        exact le_of_mul_le_mul_left (by linarith) hc
      nlinarith

/-- Sharpened finite-population alignment (proof-lattice v0 §6). -/
theorem clippedMean_alignment_sharp
    {n d : ℕ} (hn : 0 < n)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (c sigma : ℝ) (hc : 0 < c) (hsigma : 0 ≤ sigma)
    (hclip : 4 * sigma ≤ c)
    (hvariance : meanSqDeviation g (vectorMean g) ≤ sigma ^ 2) :
    (3 / 8 : ℝ) * min (‖vectorMean g‖ ^ 2) (c * ‖vectorMean g‖) +
        (1 / 2 : ℝ) * ‖clippedMean c g‖ ^ 2 - sigma ^ 4 / (8 * c ^ 2) ≤
      inner ℝ (vectorMean g) (clippedMean c g) := by
  apply alignment_of_clipping_bias_sharp _ _ c sigma hc hsigma hclip
  · exact (clippedMean_center_distance_sq_le hn c hc.le g).trans hvariance
  · intro hsmall
    exact norm_clippedMean_sub_mean_le_of_half g c sigma hc hsmall hvariance

/-- The old public statement follows from the sharpened one. -/
theorem clippedMean_alignment_of_sharp
    {n d : ℕ} (hn : 0 < n)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (c sigma : ℝ) (hc : 0 < c) (hsigma : 0 ≤ sigma)
    (hclip : 4 * sigma ≤ c)
    (hvariance : meanSqDeviation g (vectorMean g) ≤ sigma ^ 2) :
    (1 / 4 : ℝ) * min (‖vectorMean g‖ ^ 2) (c * ‖vectorMean g‖) +
        (1 / 2 : ℝ) * ‖clippedMean c g‖ ^ 2 - 2 * sigma ^ 4 / c ^ 2 ≤
      inner ℝ (vectorMean g) (clippedMean c g) := by
  have h := clippedMean_alignment_sharp hn g c sigma hc hsigma hclip hvariance
  have hmin : 0 ≤ min (‖vectorMean g‖ ^ 2) (c * ‖vectorMean g‖) :=
    le_min (sq_nonneg _) (by positivity)
  have hb : sigma ^ 4 / (8 * c ^ 2) ≤ 2 * sigma ^ 4 / c ^ 2 := by
    rw [div_le_div_iff₀ (by positivity) (by positivity)]
    nlinarith [pow_nonneg hsigma 4, sq_nonneg c]
  nlinarith

end

end Mf.Optimization.PoissonClippedSGD
