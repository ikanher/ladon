import Mf.DP.PoissonMomentSelection
import Mf.DP.Profile.RationalGaussianExpression

/-!
# Rational certificates for Poisson Gaussian moment calibration

Theorems 2 and 3 of *Rational arithmetic for Poisson Gaussian noise calibration*
(`latex/natural-language/poisson_gaussian_rational_calibration.tex`) justify an
exact rational test: an upper bound for the finite moment, raised to `T`, must
not exceed a lower bound for `delta * exp ((m-1)*epsilon)`. The exponential
bounds use the existing dyadic Taylor construction and its convergence proof.

`check` is executable and rejects invalid inputs. Acceptance implies the real
moment inequality. Every rational noise strictly above an admissible order
threshold eventually passes as precision increases. Every valid rational
request has a finite successful certificate, arbitrarily close above any
admissible order threshold. These are sufficient bounds, not optimal DP noise.
No original Abadi Lemma 3 range condition is an acceptance gate.
-/

open Filter Topology
open scoped BigOperators
namespace Mf.DP.PoissonMomentCalibration.Rational

/-- Dyadic Taylor bounds at positive Taylor order `n+1`, with rational endpoints. -/
def expInterval (x : ℚ) (n : ℕ) : RationalOutwardInterval :=
  (RationalGaussianExpression.exponential x).interval n

lemma expInterval_encloses (x : ℚ) (n : ℕ) :
    (expInterval x n).Encloses (Real.exp (x : ℝ)) :=
  RationalGaussianExpression.interval_encloses (.exponential x) n

lemma expInterval_converges (x : ℚ) :
    RationalOutwardInterval.ConvergesTo (expInterval x) (Real.exp (x : ℝ)) :=
  RationalGaussianExpression.interval_converges (.exponential x)

def weight (m j : ℕ) (q : ℚ) : ℚ := (m.choose j : ℚ) * (1 - q) ^ (m - j) * q ^ j
def exponent (j : ℕ) (σ : ℚ) : ℚ := (((j : ℚ) ^ 2 - j) * (1 / σ ^ 2)) / 2
/-- Nonnegative binomial weights preserve the exponential upper bounds. -/
def momentUpper (m : ℕ) (q σ : ℚ) (n : ℕ) : ℚ :=
  ∑ j ∈ Finset.range (m + 1), weight m j q * (expInterval (exponent j σ) n).upper
/-- Lower bound for the exponential privacy budget; no logarithm is computed. -/
def budgetLower (m : ℕ) (eps δ : ℚ) (n : ℕ) : ℚ :=
  δ * (expInterval (((m : ℚ) - 1) * eps) n).lower

def Valid (T m : ℕ) (eps δ q σ : ℚ) : Prop :=
  0 < T ∧ 2 ≤ m ∧ 0 < eps ∧ 0 < δ ∧ δ < 1 ∧ 0 < q ∧ q < 1 ∧ 0 < σ
instance (T m : ℕ) (eps δ q σ : ℚ) : Decidable (Valid T m eps δ q σ) := by
  unfold Valid; infer_instance

/-- Finite exact-rational acceptance test, including all parameter-domain checks. -/
def check (T m : ℕ) (eps δ q σ : ℚ) (n : ℕ) : Bool :=
  decide (Valid T m eps δ q σ ∧ momentUpper m q σ n ^ T ≤ budgetLower m eps δ n)

lemma moment_le_upper {m : ℕ} {q σ : ℚ} (hq : 0 ≤ q) (hq1 : q ≤ 1) (n : ℕ) :
    sampledGaussianRenyiMoment m q (1 / (σ : ℝ) ^ 2) ≤ (momentUpper m q σ n : ℝ) := by
  unfold momentUpper sampledGaussianRenyiMoment
  push_cast
  apply Finset.sum_le_sum
  intro j _
  have hw : (0 : ℝ) ≤ (weight m j q : ℝ) := by
    exact_mod_cast (show 0 ≤ weight m j q by unfold weight; positivity)
  have he := (expInterval_encloses (exponent j σ) n).2
  simp only [exponent, Rat.cast_div, Rat.cast_mul, Rat.cast_sub, Rat.cast_pow,
    Rat.cast_natCast, Rat.cast_ofNat, Rat.cast_one] at he
  simpa only [weight, exponent, Rat.cast_mul, Rat.cast_sub, Rat.cast_pow, Rat.cast_natCast,
    Rat.cast_one] using mul_le_mul_of_nonneg_left he hw

lemma budgetLower_le {m : ℕ} {eps δ : ℚ} (hδ : 0 ≤ δ) (n : ℕ) :
    (budgetLower m eps δ n : ℝ) ≤ (δ : ℝ) * Real.exp (((m : ℝ) - 1) * eps) := by
  have he := (expInterval_encloses (((m : ℚ) - 1) * eps) n).1
  push_cast at he
  simpa [budgetLower] using mul_le_mul_of_nonneg_left he (show (0 : ℝ) ≤ δ by exact_mod_cast hδ)

lemma check_power_sound {T m n : ℕ} {eps δ q σ : ℚ}
    (hc : check T m eps δ q σ n = true) :
    Valid T m eps δ q σ ∧
    sampledGaussianRenyiMoment m q (1 / (σ : ℝ) ^ 2) ^ T ≤
      (δ : ℝ) * Real.exp (((m : ℝ) - 1) * eps) := by
  obtain ⟨hv, hc⟩ := of_decide_eq_true hc
  refine ⟨hv, ?_⟩
  have hq : (0 : ℝ) ≤ q := by exact_mod_cast hv.2.2.2.2.2.1.le
  have hq1 : (q : ℝ) ≤ 1 := by exact_mod_cast hv.2.2.2.2.2.2.1.le
  have hp := (sampledGaussianRenyiMoment_pos m (1 / (σ : ℝ) ^ 2) hq hq1).le
  calc
    _ ≤ (momentUpper m q σ n : ℝ) ^ T :=
      pow_le_pow_left₀ hp (moment_le_upper hv.2.2.2.2.2.1.le hv.2.2.2.2.2.2.1.le n) T
    _ ≤ (budgetLower m eps δ n : ℝ) := by exact_mod_cast hc
    _ ≤ _ := budgetLower_le hv.2.2.2.1.le n

/-- Accepted rational bounds imply the real logarithmic moment condition. -/
lemma check_sound {T m n : ℕ} {eps δ q σ : ℚ}
    (hc : check T m eps δ q σ n = true) :
    Valid T m eps δ q σ ∧
    (T : ℝ) * Real.log (sampledGaussianRenyiMoment m q (1 / (σ : ℝ) ^ 2)) ≤
      ((m : ℝ) - 1) * eps - Real.log (1 / (δ : ℝ)) := by
  obtain ⟨hv, hc⟩ := check_power_sound hc
  refine ⟨hv, ?_⟩
  have hq : (0 : ℝ) ≤ q := by exact_mod_cast hv.2.2.2.2.2.1.le
  have hq1 : (q : ℝ) ≤ 1 := by exact_mod_cast hv.2.2.2.2.2.2.1.le
  have hδ : (0 : ℝ) < δ := by exact_mod_cast hv.2.2.2.1
  have hp := sampledGaussianRenyiMoment_pos m (1 / (σ : ℝ) ^ 2) hq hq1
  have hl := Real.log_le_log (pow_pos hp T) hc
  rw [Real.log_pow, Real.log_mul (ne_of_gt hδ) (ne_of_gt (Real.exp_pos _)), Real.log_exp] at hl
  simpa [Real.log_div, add_comm] using hl

lemma momentUpper_tendsto (m : ℕ) (q σ : ℚ) :
    Tendsto (fun n => (momentUpper m q σ n : ℝ)) atTop
      (𝓝 (sampledGaussianRenyiMoment m q (1 / (σ : ℝ) ^ 2))) := by
  have h := tendsto_finsetSum (Finset.range (m + 1)) (fun j _ =>
    (expInterval_converges (exponent j σ)).2.const_mul (weight m j q : ℝ))
  simpa [momentUpper, sampledGaussianRenyiMoment, exponent, weight] using h

lemma budgetLower_tendsto (m : ℕ) (eps δ : ℚ) :
    Tendsto (fun n => (budgetLower m eps δ n : ℝ)) atTop
      (𝓝 ((δ : ℝ) * Real.exp (((m : ℝ) - 1) * eps))) := by
  simpa [budgetLower] using
    (expInterval_converges (((m : ℚ) - 1) * eps)).1.const_mul (δ : ℝ)

/-- Strict privacy slack ensures success at every sufficiently large precision. -/
theorem eventually_check_of_strict {T m : ℕ} {eps δ q σ : ℚ}
    (hv : Valid T m eps δ q σ)
    (hs : sampledGaussianRenyiMoment m q (1 / (σ : ℝ) ^ 2) ^ T <
      (δ : ℝ) * Real.exp (((m : ℝ) - 1) * eps)) :
    ∀ᶠ n in atTop, check T m eps δ q σ n = true := by
  have ht := (budgetLower_tendsto m eps δ).sub ((momentUpper_tendsto m q σ).pow T)
  have he := ht.eventually (Ioi_mem_nhds (sub_pos.mpr hs))
  filter_upwards [he] with n hn
  apply decide_eq_true
  exact ⟨hv, by exact_mod_cast (sub_pos.mp hn).le⟩

lemma strict_moment_of_noise_lt {T m : ℕ} {eps δ q σ : ℝ}
    (hT : 0 < T) (hm : admissible eps δ m) (hq : 0 < q) (hq1 : q ≤ 1)
    (hσ : noiseAtOrder T eps δ q m < σ) :
    (T : ℝ) * Real.log (sampledGaussianRenyiMoment m q (1 / σ ^ 2)) <
      ((m : ℝ) - 1) * eps - Real.log (1 / δ) := by
  have hn := noiseAtOrder_pos hT hm hq hq1
  let τ := (noiseAtOrder T eps δ q m + σ) / 2
  have ht : 0 < τ := by dsimp [τ]; linarith
  have hnt : noiseAtOrder T eps δ q m ≤ τ := by dsimp [τ]; linarith
  have hts : τ < σ := by dsimp [τ]; linarith
  have hs : 0 < σ := hn.trans hσ
  have hb := (fixedOrder_iff hT hm hq hq1 ht).2 hnt
  have hx : 1 / σ ^ 2 < 1 / τ ^ 2 :=
    one_div_lt_one_div_of_lt (sq_pos_of_pos ht) ((sq_lt_sq₀ ht.le hs.le).2 hts)
  have ha := strictMono_moment hm.1 hq hq1 hx
  have hl := Real.log_lt_log
    (sampledGaussianRenyiMoment_pos m (1 / σ ^ 2) hq.le hq1) ha
  exact (mul_lt_mul_of_pos_left hl (by exact_mod_cast hT)).trans_le hb

lemma power_lt_of_log_moment_lt {T m : ℕ} {eps δ q σ : ℝ}
    (hq : 0 ≤ q) (hq1 : q ≤ 1) (hδ : 0 < δ)
    (hc : (T : ℝ) * Real.log (sampledGaussianRenyiMoment m q (1 / σ ^ 2)) <
      ((m : ℝ) - 1) * eps - Real.log (1 / δ)) :
    sampledGaussianRenyiMoment m q (1 / σ ^ 2) ^ T < δ * Real.exp (((m : ℝ) - 1) * eps) := by
  have he := Real.exp_lt_exp.mpr hc
  rw [Real.exp_nat_mul, Real.exp_log (sampledGaussianRenyiMoment_pos m _ hq hq1),
    Real.exp_sub, Real.exp_log (one_div_pos.mpr hδ)] at he
  simpa [div_div, mul_comm] using he

/-- Every rational noise strictly above an admissible threshold eventually passes. -/
theorem eventually_check_of_noise_lt {T m : ℕ} {eps δ q σ : ℚ}
    (hv : Valid T m eps δ q σ)
    (hm : admissible (eps : ℝ) δ m)
    (hσ : noiseAtOrder T eps δ q m < (σ : ℝ)) :
    ∀ᶠ n in atTop, check T m eps δ q σ n = true := by
  have hq : (0 : ℝ) < q := by exact_mod_cast hv.2.2.2.2.2.1
  have hq1 : (q : ℝ) ≤ 1 := by exact_mod_cast hv.2.2.2.2.2.2.1.le
  have hδ : (0 : ℝ) < δ := by exact_mod_cast hv.2.2.2.1
  apply eventually_check_of_strict hv
  exact power_lt_of_log_moment_lt hq.le hq1 hδ
    (strict_moment_of_noise_lt hv.1 hm hq hq1 hσ)

/-- Rational noise can be certified arbitrarily close above a fixed-order threshold. -/
theorem exists_check_near_threshold {T m : ℕ} {eps δ q : ℚ} {η : ℝ}
    (hT : 0 < T) (heps : 0 < eps) (hδ : 0 < δ) (hδ1 : δ < 1)
    (hq : 0 < q) (hq1 : q < 1) (hm : admissible (eps : ℝ) δ m) (hη : 0 < η) :
    ∃ σ : ℚ, noiseAtOrder T eps δ q m < (σ : ℝ) ∧
      (σ : ℝ) < noiseAtOrder T eps δ q m + η ∧
      ∃ n, check T m eps δ q σ n = true := by
  obtain ⟨σ, hs, hs'⟩ := exists_rat_btwn
    (show noiseAtOrder T eps δ q m < noiseAtOrder T eps δ q m + η by linarith)
  have hn := noiseAtOrder_pos hT hm
    (show (0 : ℝ) < q by exact_mod_cast hq) (show (q : ℝ) ≤ 1 by exact_mod_cast hq1.le)
  have hσ : 0 < σ := by exact_mod_cast hn.trans hs
  refine ⟨σ, hs, hs', ?_⟩
  exact (eventually_check_of_noise_lt ⟨hT, hm.1, heps, hδ, hδ1, hq, hq1, hσ⟩ hm hs).exists

/-- Every valid rational request has a finite successful rational certificate. -/
theorem exists_check {T : ℕ} {eps δ q : ℚ}
    (hT : 0 < T) (heps : 0 < eps) (hδ : 0 < δ) (hδ1 : δ < 1)
    (hq : 0 < q) (hq1 : q < 1) :
    ∃ (m : ℕ) (σ : ℚ) (n : ℕ), check T m eps δ q σ n = true := by
  obtain ⟨m, hm⟩ := defaultOrders_nonempty
    (show (0 : ℝ) < eps by exact_mod_cast heps)
    (show (0 : ℝ) < δ by exact_mod_cast hδ) (show (δ : ℝ) < 1 by exact_mod_cast hδ1)
  obtain ⟨σ, _, _, n, hn⟩ := exists_check_near_threshold hT heps hδ hδ1 hq hq1
    (defaultOrders_admissible hm) (show (0 : ℝ) < 1 by norm_num)
  exact ⟨m, σ, n, hn⟩

end Mf.DP.PoissonMomentCalibration.Rational
