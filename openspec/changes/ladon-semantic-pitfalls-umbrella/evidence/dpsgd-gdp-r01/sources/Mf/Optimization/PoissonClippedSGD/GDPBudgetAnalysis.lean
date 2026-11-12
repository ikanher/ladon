import Mf.Optimization.PoissonClippedSGD.GDPStepsize
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.Calculus.Deriv.MeanValue
import Mathlib.Algebra.Order.Floor.Ring

/-!
# Fixed-step and fixed-epoch consequences of the SGD GDP formula

The logarithmic perspective controls total noise variance at fixed step count.
Together with the Poisson stability cap, it orders the SGD upper bound for
fixed or separately tuned public steps. These comparisons concern bounds.
Exact expected-pass identities and ceiling-rounded horizons are treated separately.
-/

namespace Mf.Optimization.PoissonClippedSGD
open Set
noncomputable section

private def logPerspective (a s : ℝ) : ℝ := s * Real.log (1 + a / s)

private theorem logPerspective_hasDerivAt {a s : ℝ} (ha : 0 < a) (hs : 0 < s) :
    HasDerivAt (logPerspective a)
      (Real.log (1 + a / s) - (a / s) / (1 + a / s)) s := by
  have hd := (hasDerivAt_const s a).div (hasDerivAt_id s) hs.ne'
  have hl := ((hasDerivAt_const s (1 : ℝ)).add hd).log
    (show 1 + a / s ≠ 0 by positivity)
  have hp := (hasDerivAt_id s).mul hl
  convert hp using 1 <;> try rfl
  dsimp
  field_simp [hs.ne']
  ring


private theorem logPerspective_mono {a : ℝ} (ha : 0 < a) :
    MonotoneOn (logPerspective a) (Ioi 0) := by
  apply monotoneOn_of_deriv_nonneg (convex_Ioi 0)
    (fun s hs => (logPerspective_hasDerivAt ha hs).continuousAt.continuousWithinAt)
    (fun s hs =>
      (logPerspective_hasDerivAt ha (by simpa using hs)).differentiableAt.differentiableWithinAt)
  intro s hs
  have hs0 : 0 < s := by simpa using hs
  rw [(logPerspective_hasDerivAt ha hs0).deriv]
  have hz : 0 < 1 + a / s := by positivity
  have h := Real.one_sub_inv_le_log_of_pos hz
  have hid : 1 - (1 + a / s)⁻¹ = (a / s) / (1 + a / s) := by
    field_simp
    ring
  rw [hid] at h
  linarith

/-- Increasing q increases the logarithmic denominator of the total noise variance. -/
theorem gdp_log_mass_mono {q q' T mu : ℝ}
    (hq : 0 < q) (hqq : q ≤ q') (hT : 0 < T) (hmu : 0 < mu) :
    q ^ 2 * Real.log (1 + mu ^ 2 / (T * q ^ 2)) ≤
      q' ^ 2 * Real.log (1 + mu ^ 2 / (T * q' ^ 2)) := by
  have hq' : 0 < q' := hq.trans_le hqq
  have h := logPerspective_mono (a := mu ^ 2 / T) (by positivity)
    (sq_pos_of_pos hq) (sq_pos_of_pos hq') (sq_le_sq₀ hq.le hq'.le |>.mpr hqq)
  simpa only [logPerspective, div_div] using h

/-- The Poisson sampling coefficient decreases with q at public population size. -/
theorem poisson_kappa_antitone {n q q' : ℝ} (hn : 0 < n)
    (hq : 0 < q) (hqq : q ≤ q') :
    (1 - q') / (q' * n) ≤ (1 - q) / (q * n) := by
  have hq' : 0 < q' := hq.trans_le hqq
  have h := one_div_le_one_div_of_le hq hqq
  have hid (r : ℝ) (hr : r ≠ 0) : (1 - r) / (r * n) = (1 / r - 1) / n := by
    field_simp
  rw [hid q' hq'.ne', hid q hq.ne']
  exact div_le_div_of_nonneg_right (sub_le_sub_right h 1) hn.le

/-- The variance of the raw GDP-formula noise decreases at fixed T and mu. -/
theorem gdpFormulaVariance_antitone {n d q q' T c mu : ℝ}
    (hn : 0 < n) (hd : 0 ≤ d) (hq : 0 < q) (hqq : q ≤ q')
    (hT : 0 < T) (hmu : 0 < mu) :
    gdpFormulaVariance n d q' T c mu ≤ gdpFormulaVariance n d q T c mu := by
  have hm := gdp_log_mass_mono hq hqq hT hmu
  unfold gdpFormulaVariance
  apply div_le_div_of_nonneg_left (by positivity)
    (show 0 < n ^ 2 * q ^ 2 * Real.log (1 + mu ^ 2 / (T * q ^ 2)) by
      exact mul_pos (by positivity) (gdpFormula_log_pos hq hT hmu))
  simpa only [mul_assoc] using mul_le_mul_of_nonneg_left hm (sq_nonneg n)

theorem gdpTotalVariance_antitone {n d q q' T c sigma mu : ℝ}
    (hn : 0 < n) (hd : 0 ≤ d) (hq : 0 < q) (hqq : q ≤ q')
    (hT : 0 < T) (hmu : 0 < mu) :
    gdpTotalVariance n d q' T c sigma mu ≤ gdpTotalVariance n d q T c sigma mu := by
  exact add_le_add
    (mul_le_mul_of_nonneg_right (poisson_kappa_antitone hn hq hqq) (sq_nonneg sigma))
    (gdpFormulaVariance_antitone hn hd hq hqq hT hmu)

theorem gdpTotalVariance_pos {n d q T c sigma mu : ℝ}
    (hn : 0 < n) (hd : 0 < d) (hq : 0 < q) (hq1 : q ≤ 1)
    (hT : 0 < T) (hc : 0 < c) (hmu : 0 < mu) :
    0 < gdpTotalVariance n d q T c sigma mu := by
  unfold gdpTotalVariance gdpFormulaVariance
  have hk : 0 ≤ (1 - q) / (q * n) := div_nonneg (sub_nonneg.mpr hq1) (by positivity)
  have hv : 0 < c ^ 2 * d / (n ^ 2 * q ^ 2 * Real.log (1 + mu ^ 2 / (T * q ^ 2))) := by
    exact div_pos (by positivity) (mul_pos (by positivity) (gdpFormula_log_pos hq hT hmu))
  exact add_pos_of_nonneg_of_pos (mul_nonneg hk (sq_nonneg sigma)) hv

/-- Fixed-eta, fixed-step comparison of the actual SGD descent coefficients. -/
theorem gdpFormulaD_antitone_batch {eta L n d q q' sigma F T c mu : ℝ}
    (heta : 0 ≤ eta) (hL : 0 ≤ L) (hn : 0 < n) (hd : 0 ≤ d)
    (hq : 0 < q) (hqq : q ≤ q') (hT : 0 < T) (hmu : 0 < mu) :
    gdpFormulaD eta L n d q' sigma F T c mu ≤
      gdpFormulaD eta L n d q sigma F T c mu := by
  change stepRateD eta F T L (gdpTotalVariance n d q' T c sigma mu) (8 * sigma ^ 4 / c ^ 2) ≤
    stepRateD eta F T L (gdpTotalVariance n d q T c sigma mu) (8 * sigma ^ 4 / c ^ 2)
  exact stepRateD_mono_variance heta hL (gdpTotalVariance_antitone hn hd hq hqq hT hmu)

theorem gdpUpper_antitone_batch {eta L n d q q' sigma F T c mu : ℝ}
    (heta : 0 ≤ eta) (hL : 0 ≤ L) (hn : 0 < n) (hd : 0 ≤ d)
    (hq : 0 < q) (hqq : q ≤ q') (hT : 0 < T) (hc : 0 ≤ c) (hmu : 0 < mu) :
    stationarityUpper c (gdpFormulaD eta L n d q' sigma F T c mu) ≤
      stationarityUpper c (gdpFormulaD eta L n d q sigma F T c mu) :=
  stationarityUpper_mono hc (gdpFormulaD_antitone_batch heta hL hn hd hq hqq hT hmu)

/-- The admissible stepsize interval expands as q increases. -/
theorem poissonStepCap_mono_batch {L n q q' : ℝ}
    (hL : 0 < L) (hn : 0 < n) (hq : 0 < q) (hqq : q ≤ q') (hq'1 : q' ≤ 1) :
    poissonStepCap L ((1 - q) / (q * n)) ≤ poissonStepCap L ((1 - q') / (q' * n)) := by
  have hq' : 0 < q' := hq.trans_le hqq
  have hk' : 0 ≤ (1 - q') / (q' * n) := div_nonneg (sub_nonneg.mpr hq'1) (by positivity)
  unfold poissonStepCap
  apply one_div_le_one_div_of_le (show 0 < L * (1 + (1 - q') / (q' * n)) by positivity)
  exact mul_le_mul_of_nonneg_left
    (add_le_add_right (poisson_kappa_antitone hn hq hqq) 1) hL.le

/-- Positive-gap bound after reselecting the best admissible public step at each batch. -/
theorem gdpUpper_retuned_antitone_batch {L n d q q' sigma F T c mu : ℝ}
    (hL : 0 < L) (hn : 0 < n) (hd : 0 < d)
    (hq : 0 < q) (hqq : q ≤ q') (hq'1 : q' ≤ 1)
    (hF : 0 < F) (hT : 0 < T) (hc : 0 < c) (hmu : 0 < mu) :
    let Q := gdpTotalVariance n d q T c sigma mu
    let Q' := gdpTotalVariance n d q' T c sigma mu
    let cap := poissonStepCap L ((1 - q) / (q * n))
    let cap' := poissonStepCap L ((1 - q') / (q' * n))
    stationarityUpper c (gdpFormulaD (optimalStep F T L Q' cap') L n d q' sigma F T c mu) ≤
      stationarityUpper c (gdpFormulaD (optimalStep F T L Q cap) L n d q sigma F T c mu) := by
  dsimp only
  let Q := gdpTotalVariance n d q T c sigma mu
  let Q' := gdpTotalVariance n d q' T c sigma mu
  let cap := poissonStepCap L ((1 - q) / (q * n))
  let cap' := poissonStepCap L ((1 - q') / (q' * n))
  have hq' : 0 < q' := hq.trans_le hqq
  have hq1 : q ≤ 1 := hqq.trans hq'1
  have hk : 0 ≤ (1 - q) / (q * n) := div_nonneg (sub_nonneg.mpr hq1) (by positivity)
  have hk' : 0 ≤ (1 - q') / (q' * n) := div_nonneg (sub_nonneg.mpr hq'1) (by positivity)
  have hQ : 0 < Q := gdpTotalVariance_pos hn hd hq hq1 hT hc hmu
  have hQ' : 0 < Q' := gdpTotalVariance_pos hn hd hq' hq'1 hT hc hmu
  have hcap : 0 < cap := poissonStepCap_pos hL hk
  have hcap' : 0 < cap' := poissonStepCap_pos hL hk'
  have he : 0 < optimalStep F T L Q cap := optimalStep_pos hF hT hL hQ hcap
  have hecap' : optimalStep F T L Q cap ≤ cap' :=
    (optimalStep_le_cap F T L Q cap).trans (poissonStepCap_mono_batch hL hn hq hqq hq'1)
  calc
    _ ≤ stationarityUpper c (gdpFormulaD (optimalStep F T L Q cap) L n d q' sigma F T c mu) :=
      stepUpper_optimal hF hT hL hQ' hcap' he hecap' hc.le
    _ ≤ _ := gdpUpper_antitone_batch he.le hL.le hn hd.le hq hqq hT hc.le hmu

/-- Exact expected-pass substitution, only on the domain where integer T satisfies Tq=E. -/
theorem gdpFormulaD_exact_epochs {T : ℕ} (_hT : 0 < T) (eta L n d q sigma F E c mu : ℝ)
    (hq : 0 < q) (hE : (T : ℝ) * q = E) :
    gdpFormulaD eta L n d q sigma F T c mu =
      4 * F * q / (eta * E) + 8 * sigma ^ 4 / c ^ 2 +
      2 * eta * L * ((1 - q) / (q * n) * sigma ^ 2) +
      2 * eta * L * c ^ 2 * d / (n ^ 2 * q ^ 2 * Real.log (1 + mu ^ 2 / (E * q))) := by
  rw [gdpFormulaD_expanded, ← hE]
  have hmass : (T : ℝ) * q * q = (T : ℝ) * q ^ 2 := by ring
  rw [hmass]
  congr 2
  field_simp

/-- Rounded expected-pass horizons retain the rounding slack explicitly. -/
theorem rounded_epochs_bounds {E q : ℝ} (hE : 0 < E) (hq : 0 < q) :
    E ≤ (⌈E / q⌉₊ : ℝ) * q ∧ (⌈E / q⌉₊ : ℝ) * q < E + q := by
  constructor
  · exact (div_le_iff₀ hq).mp (Nat.le_ceil (E / q))
  · have h := Nat.ceil_lt_add_one (div_pos hE hq).le
    have hm := mul_lt_mul_of_pos_right h hq
    have hid : (E / q + 1) * q = E + q := by field_simp
    rwa [hid] at hm

end
end Mf.Optimization.PoissonClippedSGD
