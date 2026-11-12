import Mf.Optimization.PoissonClippedSGD.GDPFormula
import Mf.Optimization.ScalingLawLossLR

/-!
# Admissible learning-rate selection for the SGD upper bound

The reciprocal-plus-linear learning-rate objective is the one in the corrected
Poisson SGD coefficient. The unconstrained square-root minimizer reuses
`peakLRTradeoff_min_le`; the stability cap is imposed here. Tuning is analytic:
a privacy application must still choose public parameters across neighbors.
-/

namespace Mf.Optimization.PoissonClippedSGD
noncomputable section

/-- Reciprocal gap and linear noise tradeoff, with the clipping-bias constant. -/
def stepRateD (eta F T L Q bias : ℝ) : ℝ :=
  4 * F / (eta * T) + bias + 2 * eta * L * Q

/-- Positive-gap, positive-variance optimum subject to the supplied public cap. -/
def optimalStep (F T L Q cap : ℝ) : ℝ :=
  min cap (Real.sqrt (2 * F / (T * L * Q)))

/-- The stability cap from the corrected Poisson descent theorem. -/
def poissonStepCap (L kappa : ℝ) : ℝ := 1 / (L * (1 + kappa))

private theorem capped_tradeoff_min {a b cap eta : ℝ}
    (ha : 0 < a) (hb : 0 < b) (hcap : 0 < cap)
    (heta : 0 < eta) (hetacap : eta ≤ cap) :
    peakLRTradeoff a b (min cap (Real.sqrt (a / b))) ≤ peakLRTradeoff a b eta := by
  let r := Real.sqrt (a / b)
  have hr : 0 < r := Real.sqrt_pos.mpr (div_pos ha hb)
  have hrsq : r ^ 2 = a / b := Real.sq_sqrt (div_pos ha hb).le
  have haeq : a = b * r ^ 2 := by rw [hrsq]; field_simp
  by_cases hrcap : r ≤ cap
  · rw [min_eq_right hrcap]
    exact peakLRTradeoff_min_le a b eta ha hb heta
  · rw [min_eq_left (le_of_not_ge hrcap)]
    have hcapr : cap ≤ r := le_of_lt (lt_of_not_ge hrcap)
    have hprod : eta * cap ≤ r ^ 2 := by
      calc
        eta * cap ≤ cap * cap := mul_le_mul_of_nonneg_right hetacap hcap.le
        _ ≤ r * r := mul_self_le_mul_self hcap.le hcapr
        _ = r ^ 2 := by ring
    have hgap : peakLRTradeoff a b eta - peakLRTradeoff a b cap =
        (cap - eta) * (a / (eta * cap) - b) := by
      unfold peakLRTradeoff
      field_simp
      ring
    have hab : b ≤ a / (eta * cap) := by
      apply (le_div_iff₀ (mul_pos heta hcap)).mpr
      rw [haeq]
      exact mul_le_mul_of_nonneg_left hprod hb.le
    have : 0 ≤ peakLRTradeoff a b eta - peakLRTradeoff a b cap := by
      rw [hgap]
      exact mul_nonneg (sub_nonneg.mpr hetacap) (sub_nonneg.mpr hab)
    linarith

theorem optimalStep_pos {F T L Q cap : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hQ : 0 < Q) (hcap : 0 < cap) :
    0 < optimalStep F T L Q cap := by
  unfold optimalStep
  exact lt_min hcap (Real.sqrt_pos.mpr (by positivity))

theorem optimalStep_le_cap (F T L Q cap : ℝ) : optimalStep F T L Q cap ≤ cap :=
  min_le_left _ _

/-- The cap-truncated square root minimizes the actual SGD coefficient. -/
theorem stepRateD_optimal {F T L Q cap eta bias : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hQ : 0 < Q)
    (hcap : 0 < cap) (heta : 0 < eta) (hetacap : eta ≤ cap) :
    stepRateD (optimalStep F T L Q cap) F T L Q bias ≤
      stepRateD eta F T L Q bias := by
  have h := capped_tradeoff_min (a := 4 * F / T) (b := 2 * L * Q)
    (by positivity) (by positivity) hcap heta hetacap
  have hratio : (4 * F / T) / (2 * L * Q) = 2 * F / (T * L * Q) := by ring
  rw [hratio] at h
  have hid (e : ℝ) : stepRateD e F T L Q bias = peakLRTradeoff (4 * F / T) (2 * L * Q) e + bias := by
    unfold stepRateD peakLRTradeoff
    ring
  rw [hid, hid]
  dsimp only [optimalStep]
  linarith

/-- Monotone transformation from D to the reported bound preserves the optimizer. -/
theorem stepUpper_optimal {F T L Q cap eta bias c : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hQ : 0 < Q)
    (hcap : 0 < cap) (heta : 0 < eta) (hetacap : eta ≤ cap) (hc : 0 ≤ c) :
    stationarityUpper c (stepRateD (optimalStep F T L Q cap) F T L Q bias) ≤
      stationarityUpper c (stepRateD eta F T L Q bias) :=
  stationarityUpper_mono hc (stepRateD_optimal hF hT hL hQ hcap heta hetacap)

theorem poissonStepCap_pos {L kappa : ℝ} (hL : 0 < L) (hk : 0 ≤ kappa) :
    0 < poissonStepCap L kappa := by unfold poissonStepCap; positivity

theorem le_poissonStepCap_iff {eta L kappa : ℝ} (hL : 0 < L) (hk : 0 ≤ kappa) :
    eta ≤ poissonStepCap L kappa ↔ eta * L * (1 + kappa) ≤ 1 := by
  unfold poissonStepCap
  rw [le_div_iff₀ (show 0 < L * (1 + kappa) by positivity)]
  rw [mul_assoc]

/-- With zero initial gap and positive noise, halving the step improves D strictly. -/
theorem zero_gap_halving_strict {eta T L Q bias : ℝ}
    (heta : 0 < eta) (hL : 0 < L) (hQ : 0 < Q) :
    stepRateD (eta / 2) 0 T L Q bias < stepRateD eta 0 T L Q bias := by
  unfold stepRateD
  simp only [mul_zero, zero_div, zero_add]
  nlinarith [mul_pos (mul_pos heta hL) hQ]

/-- The bias is the strict lower edge in the zero-gap positive-noise case. -/
theorem zero_gap_bias_lt {eta T L Q bias : ℝ}
    (heta : 0 < eta) (hL : 0 < L) (hQ : 0 < Q) :
    bias < stepRateD eta 0 T L Q bias := by
  unfold stepRateD
  simp only [mul_zero, zero_div, zero_add]
  have : 0 < 2 * eta * L * Q := by positivity
  linarith

/-- The zero-gap coefficient tends to the bias as the positive step vanishes. -/
theorem zero_gap_tendsto_bias (T L Q bias : ℝ) :
    Filter.Tendsto (fun eta : ℝ => stepRateD eta 0 T L Q bias)
      (nhdsWithin 0 (Set.Ioi 0)) (nhds bias) := by
  have h : Continuous (fun eta : ℝ => stepRateD eta 0 T L Q bias) := by
    simp only [stepRateD, mul_zero, zero_div, zero_add]
    fun_prop
  simpa only [stepRateD, mul_zero, zero_div, zero_add, zero_mul, add_zero] using
    (h.continuousAt (x := 0)).tendsto.mono_left nhdsWithin_le_nhds

/-- A positive step cannot attain the zero-gap positive-variance infimum. -/
theorem zero_gap_no_minimum {T L Q cap bias : ℝ} (hL : 0 < L) (hQ : 0 < Q) :
    ¬ ∃ eta : ℝ, 0 < eta ∧ eta ≤ cap ∧
      ∀ e : ℝ, 0 < e → e ≤ cap →
        stepRateD eta 0 T L Q bias ≤ stepRateD e 0 T L Q bias := by
  rintro ⟨eta, heta, hecap, hmin⟩
  have hhalf : eta / 2 ≤ cap := le_trans (by linarith) hecap
  have h := hmin (eta / 2) (by positivity) hhalf
  exact (not_le_of_gt (zero_gap_halving_strict heta hL hQ)) h

/-- With no variance, the largest admissible step minimizes the reciprocal term. -/
theorem zero_variance_cap_min {F T L cap eta bias : ℝ}
    (hF : 0 ≤ F) (hT : 0 < T) (_hcap : 0 < cap)
    (heta : 0 < eta) (hetacap : eta ≤ cap) :
    stepRateD cap F T L 0 bias ≤ stepRateD eta F T L 0 bias := by
  unfold stepRateD
  simp only [mul_zero, add_zero]
  have h := div_le_div_of_nonneg_left (show 0 ≤ 4 * F by positivity) (mul_pos heta hT)
    (mul_le_mul_of_nonneg_right hetacap hT.le)
  linarith

theorem zero_gap_zero_variance (eta T L bias : ℝ) :
    stepRateD eta 0 T L 0 bias = bias := by simp [stepRateD]

/-- Reducing Q reduces the coefficient at any fixed nonnegative step. -/
theorem stepRateD_mono_variance {eta F T L Q Q' bias : ℝ}
    (heta : 0 ≤ eta) (hL : 0 ≤ L) (hQ : Q' ≤ Q) :
    stepRateD eta F T L Q' bias ≤ stepRateD eta F T L Q bias := by
  unfold stepRateD
  have h := mul_le_mul_of_nonneg_left hQ (show 0 ≤ 2 * eta * L by positivity)
  linarith

end
end Mf.Optimization.PoissonClippedSGD
