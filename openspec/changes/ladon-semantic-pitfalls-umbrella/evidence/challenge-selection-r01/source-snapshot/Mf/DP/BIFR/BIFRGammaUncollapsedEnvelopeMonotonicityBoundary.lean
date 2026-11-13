import Mathlib

open scoped BigOperators Topology
open Filter
open Asymptotics

namespace Mf
namespace DP

noncomputable section

/-!
## Uncollapsed finite-p BIFR envelope monotonicity boundary

This module is the Lean-facing scalar boundary for the positive BIFR
low-bandwidth p-dependence program.

The p-flatness note shows that the collapsed asymptotic factorwise proof is
flat in `p`.  The next theorem target is different: keep the uncollapsed
finite-`p` envelope pieces

* `A_p = Rbar(n,p,gamma_p)^2 / n`,
* `B_p = Sbar_2(p,gamma_p)^2`,
* `L_p = Sbar_1(p,gamma_p)^2`,

and prove product-level monotonicity of

* `A_p * B_p`,
* `A_p * L_p / b(p)`,
* `A_p * (B_p + L_p / b(p))`.

This file deliberately does not define the analytic gamma/harmonic/gamma-function
formulas.  It provides the scalar envelope API and the theorem wrappers that the
future analytic inequalities should instantiate.

The elementary `h₁,h₂` primitives used in the dominant residual coefficient
are formalized below.  The zeta, gamma, and digamma primitive interval
endpoints remain external certificate/theorem-import obligations.
-/

/-- Elementary harmonic-leading primitive
`h₁(η)=η^(1-2η)/(1-2η)` used in the dominant bounded-cross coefficient. -/
def bifrDominantCoeffH1 (η : ℝ) : ℝ :=
  η ^ (1 - 2 * η) / (1 - 2 * η)

/-- Elementary beta-tail-leading primitive
`h₂(η)=4η^(-2η)` used in the dominant bounded-cross coefficient. -/
def bifrDominantCoeffH2 (η : ℝ) : ℝ :=
  4 * η ^ (-2 * η)

/-- Logarithmic derivative of `bifrDominantCoeffH1`. -/
def bifrDominantCoeffH1LogDeriv (η : ℝ) : ℝ :=
  -2 * Real.log η + (1 - 2 * η) / η + 2 / (1 - 2 * η)

/-- Logarithmic derivative of `bifrDominantCoeffH2`. -/
def bifrDominantCoeffH2LogDeriv (η : ℝ) : ℝ :=
  -2 * Real.log η - 2

/-- Real-valued wrapper around Mathlib's complex digamma function.

Mathlib currently exposes `Complex.digamma`, not a dedicated `Real.digamma`.
The BIFR primitive certificate only needs real positive arguments, so this
wrapper is the Lean-facing source surface for the digamma recurrence rows. -/
def bifrRealDigamma (x : ℝ) : ℝ :=
  (Complex.digamma (x : ℂ)).re

/-- Local real log-gamma wrapper for positive-argument source formulas.

Mathlib does not currently expose a dedicated `Real.logGamma`; the gamma
inverse-square source formula uses `log (Gamma x)` before exponentiating the
resulting interval. -/
def bifrRealLogGamma (x : ℝ) : ℝ :=
  Real.log (Real.Gamma x)

/-- Gamma inverse-square primitive used by the primitive interval certificate. -/
def bifrGammaInvSq (x : ℝ) : ℝ :=
  (Real.Gamma x)⁻¹ ^ 2

/-- The `log A` derivative piece in the combined `b=p` `ell_1 / p`
leading-coefficient proof.

For \(A(\eta)=1/(2\eta^{2-2\eta}\Gamma(\eta)^2)\), this is
\((\log A)' = 2\log\eta-2/\eta+2-2\psi(\eta)\). -/
def bifrCombinedBpL1LogADerivative (η : ℝ) : ℝ :=
  2 * Real.log η - 2 / η + 2 - 2 * bifrRealDigamma η

/-- Positive-series partial sum used by the Route B half-shift digamma
certificate:
\(\sum_{n=1}^N \eta/(n(n+\eta))\).

Together with the imported source formula
\(\psi(1+\eta)\ge-\gamma_E+\sum_{n=1}^N\eta/(n(n+\eta))\), this is the
finite arithmetic layer behind the half-shift bound
\(\psi(1+\eta)\ge\log(\eta+1/2)\). -/
def bifrDigammaOnePlusEtaSeriesPartial (η : ℝ) (N : ℕ) : ℝ :=
  ∑ i ∈ Finset.range N,
    η / (((i + 1 : ℕ) : ℝ) * (((i + 1 : ℕ) : ℝ) + η))

/-- Reciprocal partial sum appearing when the digamma recurrence is iterated:
\(\sum_{n=1}^N 1/(\eta+n)\). -/
def bifrDigammaOnePlusEtaReciprocalPartial (η : ℝ) (N : ℕ) : ℝ :=
  ∑ i ∈ Finset.range N, (((i + 1 : ℕ) : ℝ) + η)⁻¹

/-- Closed elementary model for the raw-`T` log-derivative in the Route B
combined `b=p` proof.

For
\[
T_{\mathrm{raw}}(\eta)=
  \frac{\eta^{1-\eta}}{1-\eta}+8\eta^{-\eta},
\]
direct algebra gives
\[
(\log T_{\mathrm{raw}})' =
  -\log\eta-1+\frac{1}{(8-7\eta)(1-\eta)}.
\]
This definition is the theorem-facing target for the remaining eta-box
obligations. -/
def bifrCombinedBpL1RawTLogDerivativeModel (η : ℝ) : ℝ :=
  -Real.log η - 1 + ((8 - 7 * η) * (1 - η))⁻¹

/-- Route B \(A\)-leading coefficient model for the practical combined
`b=p` proof:
\[
A(\eta)=\frac{1}{2\eta^{2-2\eta}\Gamma(\eta)^2}.
\]
The `bifrGammaInvSq` wrapper keeps the gamma endpoint authority localized. -/
def bifrCombinedBpALeadingModel (η : ℝ) : ℝ :=
  bifrGammaInvSq η / (2 * η ^ (2 - 2 * η))

/-- Raw \(T\)-leading numerator for the practical combined `b=p` proof:
\[
\eta^{1-\eta}/(1-\eta)+8\eta^{-\eta}.
\] -/
def bifrCombinedBpRawTLeadingModel (η : ℝ) : ℝ :=
  η ^ (1 - η) / (1 - η) + 8 * η ^ (-η)

/-- Route B \(T\)-leading coefficient model:
\[
T(\eta)=\frac{\eta^{1-\eta}/(1-\eta)+8\eta^{-\eta}}{\Gamma(1-\eta)}.
\] -/
def bifrCombinedBpTLeadingModel (η : ℝ) : ℝ :=
  bifrCombinedBpRawTLeadingModel η * (Real.Gamma (1 - η))⁻¹

/-- Power-tail term `x^(-a)` used in the zeta finite-sum/integral-tail source
formula.  The actual primitive certificate records finite sums plus integral
tails for this term; the lemmas below formalize the antitone comparison layer
behind that source formula. -/
def bifrPowerTailTerm (a x : ℝ) : ℝ :=
  x ^ (-a)

/-- Unshifted finite power-tail partial sum over `i = N, ..., M-1`. -/
def bifrPowerTailPartial (a : ℝ) (N M : ℕ) : ℝ :=
  ∑ i ∈ Finset.Ico N M, bifrPowerTailTerm a i

/-- Shifted finite power-tail partial sum over `i+1`, used for the upper
integral comparison of a decreasing positive tail. -/
def bifrShiftedPowerTailPartial (a : ℝ) (N M : ℕ) : ℝ :=
  ∑ i ∈ Finset.Ico N M, bifrPowerTailTerm a (i + 1 : ℕ)

/-- Log-power tail term `log(x) x^(-a)` used for the positive series
representing `-ζ'(a)`. -/
def bifrLogPowerTailTerm (a x : ℝ) : ℝ :=
  Real.log x * x ^ (-a)

/-- Unshifted finite log-power partial sum over `i = N, ..., M-1`. -/
def bifrLogPowerTailPartial (a : ℝ) (N M : ℕ) : ℝ :=
  ∑ i ∈ Finset.Ico N M, bifrLogPowerTailTerm a i

/-- Shifted finite log-power partial sum over `i+1`. -/
def bifrShiftedLogPowerTailPartial (a : ℝ) (N M : ℕ) : ℝ :=
  ∑ i ∈ Finset.Ico N M, bifrLogPowerTailTerm a (i + 1 : ℕ)

/-- Antiderivative for the power-tail term `x^(-a)` when `a ≠ 1`. -/
def bifrPowerTailAntiderivative (a x : ℝ) : ℝ :=
  x ^ (1 - a) / (1 - a)

/-- Antiderivative for the log-power tail term `log(x)x^(-a)` when `a ≠ 1`. -/
def bifrLogPowerTailAntiderivative (a x : ℝ) : ℝ :=
  x ^ (1 - a) * (Real.log x / (1 - a) - 1 / (1 - a) ^ 2)

/-- Closed-form improper power-tail endpoint
`∫_N^∞ x^{-a} dx = N^(1-a)/(a-1)`. -/
def bifrPowerTailEndpoint (a N : ℝ) : ℝ :=
  N ^ (1 - a) / (a - 1)

/-- Closed-form improper log-power endpoint
`∫_N^∞ log(x)x^{-a} dx`. -/
def bifrLogPowerTailEndpoint (a N : ℝ) : ℝ :=
  N ^ (1 - a) * (Real.log N / (a - 1) + 1 / (a - 1) ^ 2)

/-- Power-tail source terms are antitone in the exponent on bases at least one.

This is the pointwise endpoint rule behind the zeta finite-prefix source
enclosures: for a fixed integer term \(m\ge1\), the largest value of \(m^{-a}\)
on an exponent box occurs at the left exponent endpoint. -/
theorem bifrPowerTailTerm_exponent_interval
    {a lo hi x : ℝ} (hx : 1 ≤ x) (hlo : lo ≤ a) (hhi : a ≤ hi) :
    bifrPowerTailTerm hi x ≤ bifrPowerTailTerm a x ∧
      bifrPowerTailTerm a x ≤ bifrPowerTailTerm lo x := by
  unfold bifrPowerTailTerm
  constructor
  · exact Real.rpow_le_rpow_of_exponent_le hx (by linarith : -hi ≤ -a)
  · exact Real.rpow_le_rpow_of_exponent_le hx (by linarith : -a ≤ -lo)

/-- Nat-indexed version of `bifrPowerTailTerm_exponent_interval`. -/
theorem bifrPowerTailTerm_nat_exponent_interval
    {a lo hi : ℝ} {m : ℕ}
    (hm : 1 ≤ m) (hlo : lo ≤ a) (hhi : a ≤ hi) :
    bifrPowerTailTerm hi (m : ℝ) ≤ bifrPowerTailTerm a (m : ℝ) ∧
      bifrPowerTailTerm a (m : ℝ) ≤ bifrPowerTailTerm lo (m : ℝ) :=
  bifrPowerTailTerm_exponent_interval (x := (m : ℝ))
    (by exact_mod_cast hm) hlo hhi

/-- Log-power source terms are antitone in the exponent on bases at least one.

The factor `log x` is nonnegative on this domain, so the same endpoint rule as
for the power-tail term applies.  This is the pointwise source-term rule behind
the positive series for `-ζ'(a)`. -/
theorem bifrLogPowerTailTerm_exponent_interval
    {a lo hi x : ℝ} (hx : 1 ≤ x) (hlo : lo ≤ a) (hhi : a ≤ hi) :
    bifrLogPowerTailTerm hi x ≤ bifrLogPowerTailTerm a x ∧
      bifrLogPowerTailTerm a x ≤ bifrLogPowerTailTerm lo x := by
  have hpow := bifrPowerTailTerm_exponent_interval
    (a := a) (lo := lo) (hi := hi) (x := x) hx hlo hhi
  have hlog_nonneg : 0 ≤ Real.log x := Real.log_nonneg hx
  unfold bifrPowerTailTerm at hpow
  unfold bifrLogPowerTailTerm
  constructor
  · exact mul_le_mul_of_nonneg_left hpow.1 hlog_nonneg
  · exact mul_le_mul_of_nonneg_left hpow.2 hlog_nonneg

/-- Nat-indexed version of `bifrLogPowerTailTerm_exponent_interval`. -/
theorem bifrLogPowerTailTerm_nat_exponent_interval
    {a lo hi : ℝ} {m : ℕ}
    (hm : 1 ≤ m) (hlo : lo ≤ a) (hhi : a ≤ hi) :
    bifrLogPowerTailTerm hi (m : ℝ) ≤ bifrLogPowerTailTerm a (m : ℝ) ∧
      bifrLogPowerTailTerm a (m : ℝ) ≤ bifrLogPowerTailTerm lo (m : ℝ) :=
  bifrLogPowerTailTerm_exponent_interval (x := (m : ℝ))
    (by exact_mod_cast hm) hlo hhi

/-- The closed-form power-tail endpoint is antitone in the exponent.

For \(N\ge1\), both factors \(N^{1-a}\) and \((a-1)^{-1}\) decrease as the
exponent `a` increases.  This theorem turns an exponent box into endpoint
bounds for the power-tail integral endpoint. -/
theorem bifrPowerTailEndpoint_exponent_interval
    {a lo hi N : ℝ} (hN : 1 ≤ N) (hlo_gt : 1 < lo)
    (hlo : lo ≤ a) (hhi : a ≤ hi) :
    bifrPowerTailEndpoint hi N ≤ bifrPowerTailEndpoint a N ∧
      bifrPowerTailEndpoint a N ≤ bifrPowerTailEndpoint lo N := by
  have hN_nonneg : 0 ≤ N := le_trans (by norm_num) hN
  have ha_gt : 1 < a := lt_of_lt_of_le hlo_gt hlo
  have hhi_gt : 1 < hi := lt_of_lt_of_le ha_gt hhi
  have hpow_hi_a : N ^ (1 - hi) ≤ N ^ (1 - a) :=
    Real.rpow_le_rpow_of_exponent_le hN (by linarith)
  have hpow_a_lo : N ^ (1 - a) ≤ N ^ (1 - lo) :=
    Real.rpow_le_rpow_of_exponent_le hN (by linarith)
  have hinv_hi_a : 1 / (hi - 1) ≤ 1 / (a - 1) :=
    one_div_le_one_div_of_le (by linarith : 0 < a - 1) (by linarith)
  have hinv_a_lo : 1 / (a - 1) ≤ 1 / (lo - 1) :=
    one_div_le_one_div_of_le (by linarith : 0 < lo - 1) (by linarith)
  have hpow_hi_nonneg : 0 ≤ N ^ (1 - hi) := Real.rpow_nonneg hN_nonneg _
  have hpow_a_nonneg : 0 ≤ N ^ (1 - a) := Real.rpow_nonneg hN_nonneg _
  have hinv_hi_nonneg : 0 ≤ 1 / (hi - 1) :=
    div_nonneg zero_le_one (by linarith : 0 ≤ hi - 1)
  have hinv_a_nonneg : 0 ≤ 1 / (a - 1) :=
    div_nonneg zero_le_one (by linarith : 0 ≤ a - 1)
  unfold bifrPowerTailEndpoint
  constructor
  · calc
      N ^ (1 - hi) / (hi - 1)
          = N ^ (1 - hi) * (1 / (hi - 1)) := by ring
      _ ≤ N ^ (1 - a) * (1 / (a - 1)) :=
          mul_le_mul hpow_hi_a hinv_hi_a hinv_hi_nonneg hpow_a_nonneg
      _ = N ^ (1 - a) / (a - 1) := by ring
  · calc
      N ^ (1 - a) / (a - 1)
          = N ^ (1 - a) * (1 / (a - 1)) := by ring
      _ ≤ N ^ (1 - lo) * (1 / (lo - 1)) :=
          mul_le_mul hpow_a_lo hinv_a_lo hinv_a_nonneg
            (Real.rpow_nonneg hN_nonneg _)
      _ = N ^ (1 - lo) / (lo - 1) := by ring

/-- The closed-form log-power endpoint is antitone in the exponent.

For \(N\ge1\), the power factor, reciprocal term, and reciprocal-square term
all decrease with `a`; the logarithm factor is nonnegative. -/
theorem bifrLogPowerTailEndpoint_exponent_interval
    {a lo hi N : ℝ} (hN : 1 ≤ N) (hlo_gt : 1 < lo)
    (hlo : lo ≤ a) (hhi : a ≤ hi) :
    bifrLogPowerTailEndpoint hi N ≤ bifrLogPowerTailEndpoint a N ∧
      bifrLogPowerTailEndpoint a N ≤ bifrLogPowerTailEndpoint lo N := by
  have hN_nonneg : 0 ≤ N := le_trans (by norm_num) hN
  have hlogN_nonneg : 0 ≤ Real.log N := Real.log_nonneg hN
  have ha_gt : 1 < a := lt_of_lt_of_le hlo_gt hlo
  have hhi_gt : 1 < hi := lt_of_lt_of_le ha_gt hhi
  have hpow_hi_a : N ^ (1 - hi) ≤ N ^ (1 - a) :=
    Real.rpow_le_rpow_of_exponent_le hN (by linarith)
  have hpow_a_lo : N ^ (1 - a) ≤ N ^ (1 - lo) :=
    Real.rpow_le_rpow_of_exponent_le hN (by linarith)
  have hinv_hi_a : 1 / (hi - 1) ≤ 1 / (a - 1) :=
    one_div_le_one_div_of_le (by linarith : 0 < a - 1) (by linarith)
  have hinv_a_lo : 1 / (a - 1) ≤ 1 / (lo - 1) :=
    one_div_le_one_div_of_le (by linarith : 0 < lo - 1) (by linarith)
  have hinv_hi_nonneg : 0 ≤ 1 / (hi - 1) :=
    div_nonneg zero_le_one (by linarith : 0 ≤ hi - 1)
  have hinv_a_nonneg : 0 ≤ 1 / (a - 1) :=
    div_nonneg zero_le_one (by linarith : 0 ≤ a - 1)
  have hinv_lo_nonneg : 0 ≤ 1 / (lo - 1) :=
    div_nonneg zero_le_one (by linarith : 0 ≤ lo - 1)
  have hinv_sq_hi_a :
      1 / (hi - 1) ^ 2 ≤ 1 / (a - 1) ^ 2 := by
    have hden : (a - 1) ^ 2 ≤ (hi - 1) ^ 2 := by nlinarith
    exact one_div_le_one_div_of_le (sq_pos_of_ne_zero (by linarith : a - 1 ≠ 0)) hden
  have hinv_sq_a_lo :
      1 / (a - 1) ^ 2 ≤ 1 / (lo - 1) ^ 2 := by
    have hden : (lo - 1) ^ 2 ≤ (a - 1) ^ 2 := by nlinarith
    exact one_div_le_one_div_of_le (sq_pos_of_ne_zero (by linarith : lo - 1 ≠ 0)) hden
  have hfactor_hi_a :
      Real.log N / (hi - 1) + 1 / (hi - 1) ^ 2 ≤
        Real.log N / (a - 1) + 1 / (a - 1) ^ 2 := by
    have hlogpart :
        Real.log N / (hi - 1) ≤ Real.log N / (a - 1) := by
      calc
        Real.log N / (hi - 1) = Real.log N * (1 / (hi - 1)) := by ring
        _ ≤ Real.log N * (1 / (a - 1)) :=
            mul_le_mul_of_nonneg_left hinv_hi_a hlogN_nonneg
        _ = Real.log N / (a - 1) := by ring
    exact add_le_add hlogpart hinv_sq_hi_a
  have hfactor_a_lo :
      Real.log N / (a - 1) + 1 / (a - 1) ^ 2 ≤
        Real.log N / (lo - 1) + 1 / (lo - 1) ^ 2 := by
    have hlogpart :
        Real.log N / (a - 1) ≤ Real.log N / (lo - 1) := by
      calc
        Real.log N / (a - 1) = Real.log N * (1 / (a - 1)) := by ring
        _ ≤ Real.log N * (1 / (lo - 1)) :=
            mul_le_mul_of_nonneg_left hinv_a_lo hlogN_nonneg
        _ = Real.log N / (lo - 1) := by ring
    exact add_le_add hlogpart hinv_sq_a_lo
  have hfactor_hi_nonneg :
      0 ≤ Real.log N / (hi - 1) + 1 / (hi - 1) ^ 2 := by
    exact add_nonneg
      (div_nonneg hlogN_nonneg (by linarith : 0 ≤ hi - 1))
      (div_nonneg zero_le_one (sq_nonneg _))
  have hfactor_a_nonneg :
      0 ≤ Real.log N / (a - 1) + 1 / (a - 1) ^ 2 := by
    exact add_nonneg
      (div_nonneg hlogN_nonneg (by linarith : 0 ≤ a - 1))
      (div_nonneg zero_le_one (sq_nonneg _))
  unfold bifrLogPowerTailEndpoint
  constructor
  · exact mul_le_mul hpow_hi_a hfactor_hi_a hfactor_hi_nonneg
      (Real.rpow_nonneg hN_nonneg _)
  · exact mul_le_mul hpow_a_lo hfactor_a_lo hfactor_a_nonneg
      (Real.rpow_nonneg hN_nonneg _)

/-- Tail partial sums over `Ico N M` converge to the total sum with the
finite prefix removed.

This generic bookkeeping theorem is the series-convergence half of the BIFR
zeta source-bound bridge.  It converts Mathlib summability facts into the
tail-partial convergence hypotheses consumed by the conditional source-bound
wrappers below. -/
theorem tendsto_finset_sum_Ico_atTop_of_summable
    {f : ℕ → ℝ} (hf : Summable f) (N : ℕ) :
    Tendsto (fun M : ℕ => ∑ i ∈ Finset.Ico N M, f i) atTop
      (𝓝 ((∑' i : ℕ, f i) - ∑ i ∈ Finset.range N, f i)) := by
  have hsum : Tendsto (fun M : ℕ => ∑ i ∈ Finset.range M, f i) atTop
      (𝓝 (∑' i : ℕ, f i)) := hf.hasSum.tendsto_sum_nat
  have hconst : Tendsto (fun _ : ℕ => ∑ i ∈ Finset.range N, f i) atTop
      (𝓝 (∑ i ∈ Finset.range N, f i)) := tendsto_const_nhds
  have hsub := hsum.sub hconst
  refine hsub.congr' ?_
  filter_upwards [eventually_ge_atTop N] with M hNM
  rw [Finset.sum_Ico_eq_sub _ hNM]

/-- The shifted tail `∑ f(i+1)` with its first `N` terms removed is the same
tail as `∑ f(i)` with its first `N+1` terms removed.

This is the tail-identification bookkeeping needed by the zeta and zeta-prime
source rows: their lower and upper finite-tail partial shapes converge to the
same source tail. -/
theorem tsum_shiftedTail_eq_tsumTail_succ
    {f : ℕ → ℝ} (hf : Summable f) (N : ℕ) :
    ((∑' i : ℕ, f (i + 1)) - ∑ i ∈ Finset.range N, f (i + 1)) =
      ((∑' i : ℕ, f i) - ∑ i ∈ Finset.range (N + 1), f i) := by
  have hg : Summable (fun i : ℕ => f (i + 1)) :=
    (summable_nat_add_iff 1).mpr hf
  have hshift := hg.sum_add_tsum_nat_add N
  have htail := hf.sum_add_tsum_nat_add (N + 1)
  have hshift' :
      (∑' i : ℕ, f (i + 1)) - ∑ i ∈ Finset.range N, f (i + 1) =
        ∑' i : ℕ, f (i + N + 1) := by
    rw [← hshift]
    abel
  have htail' :
      (∑' i : ℕ, f i) - ∑ i ∈ Finset.range (N + 1), f i =
        ∑' i : ℕ, f (i + (N + 1)) := by
    rw [← htail]
    abel
  rw [hshift', htail']
  simp [Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]

/-- The power-tail sequence used by the `ζ(a)` source row is summable for
`a > 1`. -/
theorem summable_bifrPowerTailTerm_of_one_lt
    {a : ℝ} (ha : 1 < a) :
    Summable (fun n : ℕ => bifrPowerTailTerm a (n : ℝ)) := by
  unfold bifrPowerTailTerm
  exact Real.summable_nat_rpow.mpr (by linarith)

/-- The shifted power-tail sequence used by the upper zeta source row is
summable for `a > 1`. -/
theorem summable_bifrShiftedPowerTailTerm_of_one_lt
    {a : ℝ} (ha : 1 < a) :
    Summable (fun n : ℕ => bifrPowerTailTerm a (((n + 1 : ℕ) : ℝ))) := by
  have h := summable_bifrPowerTailTerm_of_one_lt (a := a) ha
  simpa only [Nat.cast_add, Nat.cast_one] using (summable_nat_add_iff 1).mpr h

/-- Convergence of the unshifted finite power-tail partials. -/
theorem tendsto_bifrPowerTailPartial_atTop_of_one_lt
    {a : ℝ} (ha : 1 < a) (N : ℕ) :
    Tendsto (fun M : ℕ => bifrPowerTailPartial a N M) atTop
      (𝓝 ((∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) -
        ∑ i ∈ Finset.range N, bifrPowerTailTerm a (i : ℝ))) := by
  unfold bifrPowerTailPartial
  exact tendsto_finset_sum_Ico_atTop_of_summable
    (summable_bifrPowerTailTerm_of_one_lt (a := a) ha) N

/-- Convergence of the shifted finite power-tail partials. -/
theorem tendsto_bifrShiftedPowerTailPartial_atTop_of_one_lt
    {a : ℝ} (ha : 1 < a) (N : ℕ) :
    Tendsto (fun M : ℕ => bifrShiftedPowerTailPartial a N M) atTop
      (𝓝 ((∑' i : ℕ, bifrPowerTailTerm a (((i + 1 : ℕ) : ℝ))) -
        ∑ i ∈ Finset.range N, bifrPowerTailTerm a (((i + 1 : ℕ) : ℝ)))) := by
  unfold bifrShiftedPowerTailPartial
  exact tendsto_finset_sum_Ico_atTop_of_summable
    (summable_bifrShiftedPowerTailTerm_of_one_lt (a := a) ha) N

/-- The log-power tail sequence used by the `-ζ'(a)` source row is summable
for the restricted BIFR exponent range `a ≥ 3/2`.

The proof uses the standard bound `log n ≤ n^(1/4)/(1/4)` and compares
`log n * n^(-a)` with the summable p-series `4 n^(-5/4)`. -/
theorem summable_bifrLogPowerTailTerm_of_three_halves_le
    {a : ℝ} (ha : (3 / 2 : ℝ) ≤ a) :
    Summable (fun n : ℕ => bifrLogPowerTailTerm a (n : ℝ)) := by
  have hs : Summable (fun n : ℕ => (4 : ℝ) * (n : ℝ) ^ (-(5 : ℝ) / 4)) := by
    exact (Real.summable_nat_rpow.mpr
      (by norm_num : (-(5 : ℝ) / 4) < -1)).mul_left 4
  refine Summable.of_norm_bounded_eventually_nat
    (f := fun n : ℕ => bifrLogPowerTailTerm a (n : ℝ))
    (g := fun n : ℕ => (4 : ℝ) * (n : ℝ) ^ (-(5 : ℝ) / 4)) hs ?_
  filter_upwards [eventually_ge_atTop (1 : ℕ)] with n hn
  unfold bifrLogPowerTailTerm
  have hn1 : (1 : ℝ) ≤ (n : ℝ) := by exact_mod_cast hn
  have hnpos : 0 < (n : ℝ) := lt_of_lt_of_le zero_lt_one hn1
  have hnnonneg : 0 ≤ (n : ℝ) := le_of_lt hnpos
  have hlog_nonneg : 0 ≤ Real.log (n : ℝ) := Real.log_nonneg hn1
  have hlog : ‖Real.log (n : ℝ)‖ ≤
      (n : ℝ) ^ ((1 : ℝ) / 4) / ((1 : ℝ) / 4) := by
    rw [Real.norm_of_nonneg hlog_nonneg]
    exact Real.log_natCast_le_rpow_div n
      (by norm_num : (0 : ℝ) < (1 : ℝ) / 4)
  have hpow_nonneg : 0 ≤ (n : ℝ) ^ (-a) := Real.rpow_nonneg hnnonneg _
  have hmul : ‖Real.log (n : ℝ) * (n : ℝ) ^ (-a)‖ ≤
      ((n : ℝ) ^ ((1 : ℝ) / 4) / ((1 : ℝ) / 4)) * (n : ℝ) ^ (-a) := by
    rw [norm_mul, Real.norm_of_nonneg hpow_nonneg]
    exact mul_le_mul_of_nonneg_right hlog hpow_nonneg
  calc
    ‖Real.log (n : ℝ) * (n : ℝ) ^ (-a)‖
        ≤ ((n : ℝ) ^ ((1 : ℝ) / 4) / ((1 : ℝ) / 4)) *
            (n : ℝ) ^ (-a) := hmul
    _ = 4 * ((n : ℝ) ^ ((1 : ℝ) / 4) * (n : ℝ) ^ (-a)) := by ring
    _ = 4 * (n : ℝ) ^ ((1 : ℝ) / 4 - a) := by
      rw [← Real.rpow_add hnpos]
      ring_nf
    _ ≤ 4 * (n : ℝ) ^ (-(5 : ℝ) / 4) := by
      have hexp : (1 : ℝ) / 4 - a ≤ -(5 : ℝ) / 4 := by linarith
      exact mul_le_mul_of_nonneg_left
        (Real.rpow_le_rpow_of_exponent_le hn1 hexp) (by norm_num)

/-- Shifted log-power tail summability for the `-ζ'(a)` upper source row. -/
theorem summable_bifrShiftedLogPowerTailTerm_of_three_halves_le
    {a : ℝ} (ha : (3 / 2 : ℝ) ≤ a) :
    Summable (fun n : ℕ => bifrLogPowerTailTerm a (((n + 1 : ℕ) : ℝ))) := by
  have h := summable_bifrLogPowerTailTerm_of_three_halves_le (a := a) ha
  simpa only [Nat.cast_add, Nat.cast_one] using (summable_nat_add_iff 1).mpr h

/-- Convergence of the unshifted finite log-power partials. -/
theorem tendsto_bifrLogPowerTailPartial_atTop_of_three_halves_le
    {a : ℝ} (ha : (3 / 2 : ℝ) ≤ a) (N : ℕ) :
    Tendsto (fun M : ℕ => bifrLogPowerTailPartial a N M) atTop
      (𝓝 ((∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) -
        ∑ i ∈ Finset.range N, bifrLogPowerTailTerm a (i : ℝ))) := by
  unfold bifrLogPowerTailPartial
  exact tendsto_finset_sum_Ico_atTop_of_summable
    (summable_bifrLogPowerTailTerm_of_three_halves_le (a := a) ha) N

/-- Convergence of the shifted finite log-power partials. -/
theorem tendsto_bifrShiftedLogPowerTailPartial_atTop_of_three_halves_le
    {a : ℝ} (ha : (3 / 2 : ℝ) ≤ a) (N : ℕ) :
    Tendsto (fun M : ℕ => bifrShiftedLogPowerTailPartial a N M) atTop
      (𝓝 ((∑' i : ℕ, bifrLogPowerTailTerm a (((i + 1 : ℕ) : ℝ))) -
        ∑ i ∈ Finset.range N, bifrLogPowerTailTerm a (((i + 1 : ℕ) : ℝ)))) := by
  unfold bifrShiftedLogPowerTailPartial
  exact tendsto_finset_sum_Ico_atTop_of_summable
    (summable_bifrShiftedLogPowerTailTerm_of_three_halves_le (a := a) ha) N

/-- Power factor `s^(1-2η)` in the bounded-cross residual model. -/
def bifrCrossPower (s η : ℝ) : ℝ :=
  s ^ (1 - 2 * η)

/-- Eta-derivative expression for a model term
`D(eta) * s^(1-2 eta)` when `D'` is supplied separately. -/
def bifrCrossModelEtaDerivExpr (D D' s η : ℝ) : ℝ :=
  (D' - 2 * Real.log s * D) * bifrCrossPower s η

/-- Source formula for the eta-derivative of `s^(1-2η)`. -/
theorem hasDerivAt_bifrCrossPower_eta
    {s η : ℝ} (hs : 0 < s) :
    HasDerivAt (fun z : ℝ => bifrCrossPower s z)
      ((-2 * Real.log s) * bifrCrossPower s η) η := by
  unfold bifrCrossPower
  have hbase : HasDerivAt (fun _ : ℝ => s) 0 η := hasDerivAt_const η s
  have hexp : HasDerivAt (fun z : ℝ => 1 - 2 * z) (-2) η := by
    simpa using
      (hasDerivAt_const η (1 : ℝ)).sub
        ((hasDerivAt_const η (2 : ℝ)).mul (hasDerivAt_id η))
  simpa [mul_comm, mul_left_comm, mul_assoc] using hbase.rpow hexp hs

/-- Source formula for residual model terms `D(η) * s^(1-2η)`.

The coefficient source formula supplies `D'`; this theorem adds the derivative
of the cross-power factor and packages the result as
`bifrCrossModelEtaDerivExpr`. -/
theorem hasDerivWithinAt_bifrCrossModel
    {Dfun : ℝ → ℝ} {D' s η : ℝ} {S : Set ℝ}
    (hs : 0 < s)
    (hD : HasDerivWithinAt Dfun D' S η) :
    HasDerivWithinAt (fun z : ℝ => Dfun z * bifrCrossPower s z)
      (bifrCrossModelEtaDerivExpr (Dfun η) D' s η) S η := by
  have hpow :
      HasDerivWithinAt (fun z : ℝ => bifrCrossPower s z)
        ((-2 * Real.log s) * bifrCrossPower s η) S η :=
    (hasDerivAt_bifrCrossPower_eta (s := s) (η := η) hs).hasDerivWithinAt
  have hmul := hD.mul hpow
  unfold bifrCrossModelEtaDerivExpr
  convert hmul using 1
  ring

/-- Continuity of the shared cross-power factor as a function of eta. -/
theorem continuousOn_bifrCrossPower_eta
    {s ηp ηq : ℝ} (hs : 0 < s) :
    ContinuousOn (fun η : ℝ => bifrCrossPower s η) (Set.Icc ηp ηq) := by
  unfold bifrCrossPower
  have hexp_cont :
      ContinuousOn (fun η : ℝ => 1 - 2 * η) (Set.Icc ηp ηq) :=
    (continuous_const.sub (continuous_const.mul continuous_id)).continuousOn
  exact (Real.continuous_const_rpow hs.ne').comp_continuousOn hexp_cont

/-- Algebraic sign consumer for residual-model derivative conditions.

If the supplied coefficient derivative satisfies `D' ≤ 2 log(s) D`, then the
eta-derivative expression for `D(eta) * s^(1-2eta)` is nonpositive. -/
theorem bifrCrossModelEtaDerivExpr_nonpos_of_coeff_log_deriv_bound
    {D D' s η : ℝ}
    (hcoeff : D' ≤ 2 * Real.log s * D)
    (hpower : 0 ≤ bifrCrossPower s η) :
    bifrCrossModelEtaDerivExpr D D' s η ≤ 0 := by
  unfold bifrCrossModelEtaDerivExpr
  exact mul_nonpos_of_nonpos_of_nonneg (sub_nonpos.mpr hcoeff) hpower

/-- Low-bandwidth reduction for the residual-model derivative condition.

Under `p ≥ 2`, with `eta = p / s`, one has `s ≥ 2 / eta`.  This theorem is
the scalar consumer for that shape: a coefficient bound against
`2 log(2/eta)` is enough to get the bound against `2 log(s)`. -/
theorem bifrCoeffLogDerivBound_of_lowBandwidth_eta_floor
    {D D' s η : ℝ}
    (hD : 0 ≤ D)
    (hη : 0 < η)
    (hs : 2 / η ≤ s)
    (hcoeff : D' ≤ 2 * Real.log (2 / η) * D) :
    D' ≤ 2 * Real.log s * D := by
  have htwo_eta_pos : 0 < 2 / η := div_pos (by norm_num) hη
  have hs_pos : 0 < s := lt_of_lt_of_le htwo_eta_pos hs
  have hlog : Real.log (2 / η) ≤ Real.log s :=
    Real.log_le_log htwo_eta_pos hs
  have hmul : 2 * Real.log (2 / η) * D ≤ 2 * Real.log s * D := by
    exact mul_le_mul_of_nonneg_right
      (mul_le_mul_of_nonneg_left hlog (by norm_num)) hD
  exact hcoeff.trans hmul

/-- Box-upper consumer for coefficient log-derivative bounds.  A certificate
may bound `D' / D` indirectly by proving `D' ≤ u * D`; if
`u ≤ 2 log(2/eta)`, this supplies the derivative condition used by the
component residual-model route. -/
theorem bifrCoeffLogDerivBound_of_box_upper
    {D D' u η : ℝ}
    (hD : 0 ≤ D)
    (hderiv : D' ≤ u * D)
    (hubox : u ≤ 2 * Real.log (2 / η)) :
    D' ≤ 2 * Real.log (2 / η) * D := by
  exact hderiv.trans (mul_le_mul_of_nonneg_right hubox hD)

/-- If a residual-model coefficient is nonincreasing and
`2 / eta >= 1`, then the coefficient derivative condition is automatic. -/
theorem bifrCoeffLogDerivBound_of_deriv_nonpos
    {D D' η : ℝ}
    (hD : 0 ≤ D)
    (hderiv : D' ≤ 0)
    (heta : 1 ≤ 2 / η) :
    D' ≤ 2 * Real.log (2 / η) * D := by
  have hlog_nonneg : 0 ≤ Real.log (2 / η) := Real.log_nonneg heta
  have hrhs_nonneg : 0 ≤ 2 * Real.log (2 / η) * D := by
    exact mul_nonneg (mul_nonneg (by norm_num) hlog_nonneg) hD
  exact hderiv.trans hrhs_nonneg

/-- Compact derivative-to-antitone wrapper on a closed eta interval.

The residual-model route usually proves a derivative expression is nonpositive
on the interior of an eta box.  This theorem packages Mathlib's mean-value
monotonicity result in the exact interval shape needed by the Route B
antitone bridge. -/
theorem antitoneOn_Icc_of_hasDerivWithinAt_nonpos
    {f f' : ℝ → ℝ} {a b : ℝ}
    (hcont : ContinuousOn f (Set.Icc a b))
    (hderiv :
      ∀ x ∈ interior (Set.Icc a b),
        HasDerivWithinAt f (f' x) (interior (Set.Icc a b)) x)
    (hnonpos : ∀ x ∈ interior (Set.Icc a b), f' x ≤ 0) :
    AntitoneOn f (Set.Icc a b) :=
  antitoneOn_of_hasDerivWithinAt_nonpos
    (D := Set.Icc a b) (f := f) (f' := f') (convex_Icc a b)
    hcont hderiv hnonpos

/-- Route B residual-model antitonicity from a nonpositive derivative
certificate on the adjacent eta interval. -/
theorem bifrResidualModel_antitoneOn_Icc_of_deriv_nonpos
    {model modelDeriv : ℝ → ℝ} {ηp ηq : ℝ}
    (hcont : ContinuousOn model (Set.Icc ηp ηq))
    (hderiv :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        HasDerivWithinAt model (modelDeriv η) (interior (Set.Icc ηp ηq)) η)
    (hnonpos : ∀ η ∈ interior (Set.Icc ηp ηq), modelDeriv η ≤ 0) :
    AntitoneOn model (Set.Icc ηp ηq) :=
  antitoneOn_Icc_of_hasDerivWithinAt_nonpos hcont hderiv hnonpos

/-- Residual cross-model antitonicity from coefficient derivative bounds.

For a model \(D(\eta)s^{1-2\eta}\), it is enough to prove a coefficient
source formula for \(D'\) and the logarithmic derivative inequality
`D' ≤ 2 log(s) D` on the interval interior.  This theorem composes the
cross-power derivative, the algebraic sign consumer, and the mean-value
antitonicity wrapper. -/
theorem bifrCrossModel_antitoneOn_Icc_of_coeff_deriv_bound
    {Dfun Dderiv : ℝ → ℝ} {s ηp ηq : ℝ}
    (hs : 0 < s)
    (hDcont : ContinuousOn Dfun (Set.Icc ηp ηq))
    (hDderiv :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        HasDerivWithinAt Dfun (Dderiv η) (interior (Set.Icc ηp ηq)) η)
    (hcoeff :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        Dderiv η ≤ 2 * Real.log s * Dfun η) :
    AntitoneOn (fun η : ℝ => Dfun η * bifrCrossPower s η)
      (Set.Icc ηp ηq) := by
  refine bifrResidualModel_antitoneOn_Icc_of_deriv_nonpos
    (modelDeriv := fun η => bifrCrossModelEtaDerivExpr (Dfun η) (Dderiv η) s η)
    ?cont ?deriv ?nonpos
  · exact hDcont.mul (continuousOn_bifrCrossPower_eta hs)
  · intro η hη
    exact hasDerivWithinAt_bifrCrossModel
      (Dfun := Dfun) (D' := Dderiv η) (s := s)
      (η := η) (S := interior (Set.Icc ηp ηq)) hs (hDderiv η hη)
  · intro η hη
    exact bifrCrossModelEtaDerivExpr_nonpos_of_coeff_log_deriv_bound
      (hcoeff η hη) (Real.rpow_nonneg (le_of_lt hs) _)

/-- Residual scale `s^(-1/8) log s` for the restricted adjacent theorem. -/
def bifrRestrictedResidualScale (s : ℝ) : ℝ :=
  s ^ (-(1 : ℝ) / 8) * Real.log s

/-- Derivative expression for the residual scale as a function of `s`. -/
def bifrRestrictedResidualScaleDerivExpr (s : ℝ) : ℝ :=
  ((-(1 : ℝ) / 8) * s ^ ((-(1 : ℝ) / 8) - 1)) * Real.log s +
    s ^ (-(1 : ℝ) / 8) * s⁻¹

/-- Source-formula theorem for the residual-scale derivative. -/
theorem hasDerivAt_bifrRestrictedResidualScale
    {s : ℝ} (hs : 0 < s) :
    HasDerivAt bifrRestrictedResidualScale
      (bifrRestrictedResidualScaleDerivExpr s) s := by
  unfold bifrRestrictedResidualScaleDerivExpr bifrRestrictedResidualScale
  have hpow : HasDerivAt (fun x : ℝ => x ^ (-(1 : ℝ) / 8))
      ((-(1 : ℝ) / 8) * s ^ ((-(1 : ℝ) / 8) - 1)) s := by
    simpa using
      (hasDerivAt_id s).rpow_const
        (p := (-(1 : ℝ) / 8)) (Or.inl hs.ne')
  have hlog : HasDerivAt Real.log s⁻¹ s := Real.hasDerivAt_log hs.ne'
  convert hpow.mul hlog using 1

/-- The residual-scale derivative is nonpositive once `log s ≥ 8`. -/
theorem bifrRestrictedResidualScaleDerivExpr_nonpos_of_log_ge_eight
    {s : ℝ} (hs : 0 < s) (hlog : 8 ≤ Real.log s) :
    bifrRestrictedResidualScaleDerivExpr s ≤ 0 := by
  unfold bifrRestrictedResidualScaleDerivExpr
  have hs_nonneg : 0 ≤ s := le_of_lt hs
  have hmul :
      s ^ (-(1 : ℝ) / 8) * s⁻¹ =
        s ^ ((-(1 : ℝ) / 8) - 1) := by
    rw [← Real.rpow_neg_one s, ← Real.rpow_add hs]
    ring_nf
  rw [hmul]
  have hcoef : (1 : ℝ) - Real.log s / 8 ≤ 0 := by linarith
  have hpow_nonneg :
      0 ≤ s ^ ((-(1 : ℝ) / 8) - 1) :=
    Real.rpow_nonneg hs_nonneg _
  calc
    ((-(1 : ℝ) / 8) * s ^ ((-(1 : ℝ) / 8) - 1)) * Real.log s +
        s ^ ((-(1 : ℝ) / 8) - 1)
        = s ^ ((-(1 : ℝ) / 8) - 1) * (1 - Real.log s / 8) := by ring
    _ ≤ 0 := mul_nonpos_of_nonneg_of_nonpos hpow_nonneg hcoef

/-- The residual scale is antitone above any point where `log s ≥ 8`.

This is the Lean counterpart of the monotonicity part of the r22 cutoff
certificate: after the endpoint is in the decreasing region, the worst scale is
attained at the endpoint. -/
theorem antitoneOn_bifrRestrictedResidualScale_of_log_ge_eight
    {a : ℝ} (ha : 0 < a) (hloga : 8 ≤ Real.log a) :
    AntitoneOn bifrRestrictedResidualScale (Set.Ici a) := by
  refine antitoneOn_of_hasDerivWithinAt_nonpos
    (f' := bifrRestrictedResidualScaleDerivExpr)
    (convex_Ici a) ?cont ?deriv ?nonpos
  · unfold bifrRestrictedResidualScale
    have hpow_cont :
        ContinuousOn (fun x : ℝ => x ^ (-(1 : ℝ) / 8)) (Set.Ici a) := by
      exact continuousOn_id.rpow_const
        (fun x hx => Or.inl (lt_of_lt_of_le ha hx).ne')
    have hlog_cont : ContinuousOn Real.log (Set.Ici a) := by
      exact Real.continuousOn_log.mono
        (fun x hx => (lt_of_lt_of_le ha hx).ne')
    exact hpow_cont.mul hlog_cont
  · intro x hx
    rw [interior_Ici] at hx
    have hpos : 0 < x := lt_of_lt_of_le ha hx.le
    exact (hasDerivAt_bifrRestrictedResidualScale hpos).hasDerivWithinAt
  · intro x hx
    rw [interior_Ici] at hx
    have hpos : 0 < x := lt_of_lt_of_le ha hx.le
    have hlogx : 8 ≤ Real.log x := by
      have hlelog : Real.log a ≤ Real.log x := Real.log_le_log ha hx.le
      exact hloga.trans hlelog
    exact bifrRestrictedResidualScaleDerivExpr_nonpos_of_log_ge_eight hpos hlogx

/-- If the endpoint residual scale is below the cutoff and the endpoint is in
the decreasing region, all larger `s` values also satisfy the cutoff. -/
theorem bifrRestrictedResidualScale_le_of_ge_endpoint
    {a s : ℝ}
    (ha : 0 < a)
    (hloga : 8 ≤ Real.log a)
    (has : a ≤ s)
    (hendpoint : bifrRestrictedResidualScale a ≤ (1 : ℝ) / 640) :
    bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 := by
  have hanti := antitoneOn_bifrRestrictedResidualScale_of_log_ge_eight ha hloga
  have hs_mem : s ∈ Set.Ici a := has
  have ha_mem : a ∈ Set.Ici a := by
    change a ≤ a
    exact le_rfl
  exact (hanti ha_mem hs_mem has).trans hendpoint

/-- Algebraic cutoff replay for the restricted residual scale.

The exact-rational cutoff certificate records that, at the proof-facing cutoff,
one can use the elementary bounds `log s ≤ 1771/20` and
`57344 ≤ s^(1/8)`.  This theorem is the Lean scalar replay of the final
arithmetic step:
\[
  s^{-1/8}\log s \le (1771/20)/57344 < 1/640.
\]
It does not prove the transcendental endpoint bounds themselves. -/
theorem bifrRestrictedResidualScale_le_one_div_640_of_log_and_root_bounds
    {s : ℝ}
    (hs : 1 ≤ s)
    (hlog_upper : Real.log s ≤ (1771 : ℝ) / 20)
    (hroot_lower : (57344 : ℝ) ≤ s ^ ((1 : ℝ) / 8)) :
    bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 := by
  unfold bifrRestrictedResidualScale
  have hs_nonneg : 0 ≤ s := le_trans (by norm_num) hs
  have hlog_nonneg : 0 ≤ Real.log s := Real.log_nonneg hs
  have hneg : s ^ (-(1 : ℝ) / 8) = (s ^ ((1 : ℝ) / 8))⁻¹ := by
    have hnegexp : (-(1 : ℝ) / 8) = -((1 : ℝ) / 8) := by norm_num
    rw [hnegexp, Real.rpow_neg hs_nonneg]
  rw [hneg]
  have hinv_upper : (s ^ ((1 : ℝ) / 8))⁻¹ ≤ (57344 : ℝ)⁻¹ :=
    inv_anti₀ (by norm_num) hroot_lower
  calc
    (s ^ ((1 : ℝ) / 8))⁻¹ * Real.log s
        ≤ (57344 : ℝ)⁻¹ * ((1771 : ℝ) / 20) := by
          exact mul_le_mul hinv_upper hlog_upper hlog_nonneg (by positivity)
    _ ≤ (1 : ℝ) / 640 := by norm_num

/-- Endpoint-plus-monotonicity cutoff replay.

If an endpoint `a` is in the decreasing region, all `s ≥ a` inherit the
residual-scale cutoff from the endpoint log/root arithmetic.  This is the
Lean-side scalar shape matching the r22 certificate's endpoint reduction. -/
theorem bifrRestrictedResidualScale_le_one_div_640_of_ge_endpoint_log_and_root_bounds
    {a s : ℝ}
    (ha : 0 < a)
    (hloga : 8 ≤ Real.log a)
    (has : a ≤ s)
    (hlog_upper : Real.log a ≤ (1771 : ℝ) / 20)
    (hroot_lower : (57344 : ℝ) ≤ a ^ ((1 : ℝ) / 8)) :
    bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 := by
  have ha_one : 1 ≤ a := by
    by_contra hnot
    have ha_lt_one : a < 1 := lt_of_not_ge hnot
    have hlog_lt_zero : Real.log a < 0 := Real.log_neg ha ha_lt_one
    linarith
  have hendpoint :
      bifrRestrictedResidualScale a ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_log_and_root_bounds
      ha_one hlog_upper hroot_lower
  exact bifrRestrictedResidualScale_le_of_ge_endpoint ha hloga has hendpoint

/-- Imported `log 2` lower bound implies that the cutoff endpoint
`2^(253/2)` is inside the decreasing region for
`s^(-1/8) log s`. -/
theorem bifrCutoffEndpoint_log_lower_of_log_two_lower
    (hlog_two_lower : (2 / 3 : ℝ) ≤ Real.log 2) :
    (8 : ℝ) ≤ Real.log ((2 : ℝ) ^ ((253 : ℝ) / 2)) := by
  have hpos2 : (0 : ℝ) < 2 := by norm_num
  rw [Real.log_rpow hpos2]
  nlinarith

/-- Imported `log 2` upper bound gives the endpoint logarithm bound used by
the exact cutoff replay. -/
theorem bifrCutoffEndpoint_log_upper_of_log_two_upper
    (hlog_two_upper : Real.log 2 ≤ (7 / 10 : ℝ)) :
    Real.log ((2 : ℝ) ^ ((253 : ℝ) / 2)) ≤ (1771 : ℝ) / 20 := by
  have hpos2 : (0 : ℝ) < 2 := by norm_num
  rw [Real.log_rpow hpos2]
  nlinarith

/-- Imported fractional-power lower bound gives the endpoint eighth-root
bound used by the exact cutoff replay. -/
theorem bifrCutoffEndpoint_root_lower_of_two_rpow_thirteen_sixteen
    (hpow : (7 / 4 : ℝ) ≤ (2 : ℝ) ^ ((13 : ℝ) / 16)) :
    (57344 : ℝ) ≤
      ((2 : ℝ) ^ ((253 : ℝ) / 2)) ^ ((1 : ℝ) / 8) := by
  have hpos2 : (0 : ℝ) < 2 := by norm_num
  have hnonneg2 : (0 : ℝ) ≤ 2 := by norm_num
  rw [← Real.rpow_mul hnonneg2]
  have hsplit :
      ((253 : ℝ) / 2) * ((1 : ℝ) / 8) =
        (15 : ℝ) + ((13 : ℝ) / 16) := by norm_num
  rw [hsplit, Real.rpow_add hpos2]
  have hpow15 : (2 : ℝ) ^ (15 : ℝ) = 32768 := by
    norm_num [show (15 : ℝ) = ((15 : ℕ) : ℝ) by norm_num,
      Real.rpow_natCast]
  rw [hpow15]
  nlinarith

/-- Concrete cutoff theorem for all `s ≥ 2^(253/2)`.

This theorem consumes only the imported elementary endpoint assumptions used by
the r22 cutoff certificate:
`2/3 ≤ log 2`, `log 2 ≤ 7/10`, and `7/4 ≤ 2^(13/16)`.
It then uses the Lean antitone theorem for `s^(-1/8) log s` to transfer the
endpoint cutoff to every larger horizon scale. -/
theorem bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
    {s : ℝ}
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (hlog_two_lower : (2 / 3 : ℝ) ≤ Real.log 2)
    (hlog_two_upper : Real.log 2 ≤ (7 / 10 : ℝ))
    (hpow : (7 / 4 : ℝ) ≤ (2 : ℝ) ^ ((13 : ℝ) / 16)) :
    bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 := by
  have hpos2 : (0 : ℝ) < 2 := by norm_num
  have hendpoint_pos : 0 < (2 : ℝ) ^ ((253 : ℝ) / 2) :=
    Real.rpow_pos_of_pos hpos2 _
  have hloga :
      (8 : ℝ) ≤ Real.log ((2 : ℝ) ^ ((253 : ℝ) / 2)) :=
    bifrCutoffEndpoint_log_lower_of_log_two_lower hlog_two_lower
  have hlog_upper :
      Real.log ((2 : ℝ) ^ ((253 : ℝ) / 2)) ≤ (1771 : ℝ) / 20 :=
    bifrCutoffEndpoint_log_upper_of_log_two_upper hlog_two_upper
  have hroot_lower :
      (57344 : ℝ) ≤
        ((2 : ℝ) ^ ((253 : ℝ) / 2)) ^ ((1 : ℝ) / 8) :=
    bifrCutoffEndpoint_root_lower_of_two_rpow_thirteen_sixteen hpow
  exact
    bifrRestrictedResidualScale_le_one_div_640_of_ge_endpoint_log_and_root_bounds
      hendpoint_pos hloga hsge hlog_upper hroot_lower

/-- Mathlib's decimal log bound implies the imported lower endpoint
`2/3 ≤ log 2`. -/
theorem bifrLogTwo_lower_two_thirds :
    (2 / 3 : ℝ) ≤ Real.log 2 := by
  exact le_of_lt (lt_of_lt_of_le (by norm_num) Real.log_two_gt_d9.le)

/-- Mathlib's decimal log bound implies the imported upper endpoint
`log 2 ≤ 7/10`. -/
theorem bifrLogTwo_upper_seven_tenths :
    Real.log 2 ≤ (7 / 10 : ℝ) := by
  exact le_of_lt (lt_of_lt_of_le Real.log_two_lt_d9 (by norm_num))

/-- The fractional-power endpoint \(2^{13/16}\ge7/4\), proved by the
rational check \((7/4)^{16}\le2^{13}\). -/
theorem bifrTwoRpowThirteenSixteenths_lower_seven_fourths :
    (7 / 4 : ℝ) ≤ (2 : ℝ) ^ ((13 : ℝ) / 16) := by
  have hpow16 : (7 / 4 : ℝ) ^ (16 : ℝ) ≤ (2 : ℝ) ^ (13 : ℝ) := by
    norm_num [show (16 : ℝ) = ((16 : ℕ) : ℝ) by norm_num,
      show (13 : ℝ) = ((13 : ℕ) : ℝ) by norm_num, Real.rpow_natCast]
  have hnonneg_powleft : (0 : ℝ) ≤ (7 / 4 : ℝ) ^ (16 : ℝ) := by
    positivity
  have htaken :=
    Real.rpow_le_rpow hnonneg_powleft hpow16
      (by norm_num : (0 : ℝ) ≤ (1 : ℝ) / 16)
  have hleft :
      ((7 / 4 : ℝ) ^ (16 : ℝ)) ^ ((1 : ℝ) / 16) =
        (7 / 4 : ℝ) := by
    rw [← Real.rpow_mul (by norm_num : (0 : ℝ) ≤ (7 / 4 : ℝ))]
    norm_num
  have hright :
      ((2 : ℝ) ^ (13 : ℝ)) ^ ((1 : ℝ) / 16) =
        (2 : ℝ) ^ ((13 : ℝ) / 16) := by
    rw [← Real.rpow_mul (by norm_num : (0 : ℝ) ≤ 2)]
    ring_nf
  rwa [hleft, hright] at htaken

/-- Concrete cutoff theorem for all `s ≥ 2^(253/2)` with no remaining
elementary cutoff imports. -/
theorem bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff_closed
    {s : ℝ}
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s) :
    bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
  bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
    hsge bifrLogTwo_lower_two_thirds bifrLogTwo_upper_seven_tenths
    bifrTwoRpowThirteenSixteenths_lower_seven_fourths

/-- The large-side cutoff implies the logarithmic side condition used by
the coefficient-step residual bounds. -/
theorem one_le_log_of_ge_two_rpow_cutoff_closed
    {s : ℝ}
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s) :
    (1 : ℝ) ≤ Real.log s := by
  have hpos2 : (0 : ℝ) < 2 := by norm_num
  have hendpoint_log :
      (8 : ℝ) ≤ Real.log ((2 : ℝ) ^ ((253 : ℝ) / 2)) :=
    bifrCutoffEndpoint_log_lower_of_log_two_lower bifrLogTwo_lower_two_thirds
  have hlog_endpoint_le_s :
      Real.log ((2 : ℝ) ^ ((253 : ℝ) / 2)) ≤ Real.log s :=
    Real.log_le_log (Real.rpow_pos_of_pos hpos2 _) hsge
  linarith

/-- The large-side cutoff implies the positive horizon side condition used by
the residual-scale and power-factor bounds. -/
theorem one_le_of_ge_two_rpow_cutoff_closed
    {s : ℝ}
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s) :
    (1 : ℝ) ≤ s := by
  have hpos2 : (0 : ℝ) < 2 := by norm_num
  have hs_pos : 0 < s :=
    lt_of_lt_of_le (Real.rpow_pos_of_pos hpos2 _) hsge
  have hlog : (1 : ℝ) ≤ Real.log s :=
    one_le_log_of_ge_two_rpow_cutoff_closed hsge
  by_contra hnot
  have hs_lt_one : s < 1 := lt_of_not_ge hnot
  have hlog_s_lt_zero : Real.log s < 0 := Real.log_neg hs_pos hs_lt_one
  linarith

/-- Source-formula theorem for the elementary `h₁` primitive.

This is the Lean counterpart of the `h1LogDerivative` row in the primitive
source-formula registry. -/
theorem hasDerivAt_bifrDominantCoeffH1
    {η : ℝ} (hη : 0 < η) (hden : 1 - 2 * η ≠ 0) :
    HasDerivAt bifrDominantCoeffH1
      (bifrDominantCoeffH1 η * bifrDominantCoeffH1LogDeriv η) η := by
  unfold bifrDominantCoeffH1 bifrDominantCoeffH1LogDeriv
  have hpow : HasDerivAt (fun x : ℝ => x ^ (1 - 2 * x))
      ((1 : ℝ) * (1 - 2 * η) * η ^ ((1 - 2 * η) - 1) +
        (-2) * η ^ (1 - 2 * η) * Real.log η) η := by
    simpa using
      (hasDerivAt_id η).rpow
        ((hasDerivAt_const η (1 : ℝ)).sub
          ((hasDerivAt_const η (2 : ℝ)).mul (hasDerivAt_id η))) hη
  have hinv : HasDerivAt (fun x : ℝ => (1 - 2 * x)⁻¹)
      (2 / (1 - 2 * η) ^ 2) η := by
    simpa using
      ((hasDerivAt_const η (1 : ℝ)).sub
        ((hasDerivAt_const η (2 : ℝ)).mul (hasDerivAt_id η))).inv hden
  have hprod := hpow.mul hinv
  convert hprod using 1
  rw [Real.rpow_sub_one hη.ne']
  field_simp [hη.ne', hden]
  ring

/-- Source-formula theorem for the elementary `h₂` primitive.

This is the Lean counterpart of the `h2LogDerivative` row in the primitive
source-formula registry. -/
theorem hasDerivAt_bifrDominantCoeffH2
    {η : ℝ} (hη : 0 < η) :
    HasDerivAt bifrDominantCoeffH2
      (bifrDominantCoeffH2 η * bifrDominantCoeffH2LogDeriv η) η := by
  unfold bifrDominantCoeffH2 bifrDominantCoeffH2LogDeriv
  have hpow : HasDerivAt (fun x : ℝ => x ^ (-2 * x))
      ((1 : ℝ) * (-2 * η) * η ^ ((-2 * η) - 1) +
        (-2) * η ^ (-2 * η) * Real.log η) η := by
    simpa using
      (hasDerivAt_id η).rpow
        ((hasDerivAt_const η (-2 : ℝ)).mul (hasDerivAt_id η)) hη
  have hmain := hpow.const_mul (4 : ℝ)
  convert hmain using 1
  rw [Real.rpow_sub_one hη.ne']
  field_simp [hη.ne']
  ring

/-- Restricted-interval version of the `h₁` source-formula theorem. -/
theorem hasDerivAt_bifrDominantCoeffH1_of_mem_restricted
    {η : ℝ} (hη : η ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)) :
    HasDerivAt bifrDominantCoeffH1
      (bifrDominantCoeffH1 η * bifrDominantCoeffH1LogDeriv η) η := by
  have hpos : 0 < η := by linarith [hη.1]
  have hden : 1 - 2 * η ≠ 0 := by
    have hden_pos : 0 < 1 - 2 * η := by linarith [hη.2]
    exact hden_pos.ne'
  exact hasDerivAt_bifrDominantCoeffH1 hpos hden

/-- Restricted-interval version of the `h₂` source-formula theorem. -/
theorem hasDerivAt_bifrDominantCoeffH2_of_mem_restricted
    {η : ℝ} (hη : η ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)) :
    HasDerivAt bifrDominantCoeffH2
      (bifrDominantCoeffH2 η * bifrDominantCoeffH2LogDeriv η) η := by
  have hpos : 0 < η := by linarith [hη.1]
  exact hasDerivAt_bifrDominantCoeffH2 hpos

/-- The elementary `h₁` primitive is positive on the restricted interval. -/
theorem bifrDominantCoeffH1_pos_of_mem_restricted
    {η : ℝ} (hη : η ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)) :
    0 < bifrDominantCoeffH1 η := by
  unfold bifrDominantCoeffH1
  have hpos : 0 < η := by linarith [hη.1]
  have hden : 0 < 1 - 2 * η := by linarith [hη.2]
  exact div_pos (Real.rpow_pos_of_pos hpos _) hden

/-- The elementary `h₂` primitive is positive on the restricted interval. -/
theorem bifrDominantCoeffH2_pos_of_mem_restricted
    {η : ℝ} (hη : η ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)) :
    0 < bifrDominantCoeffH2 η := by
  unfold bifrDominantCoeffH2
  have hpos : 0 < η := by linarith [hη.1]
  positivity

/-- Source-formula recurrence for the real digamma wrapper.

This is the Lean counterpart of the recurrence part of the
`recurrence_asymptotic_source_bounds_for_digamma` primitive source lemma.  It
does not formalize the large-argument asymptotic enclosure; it only closes the
recurrence identity using Mathlib's `Complex.digamma_apply_add_one`. -/
theorem bifrRealDigamma_apply_add_one {x : ℝ} (hx : 0 < x) :
    bifrRealDigamma (x + 1) = bifrRealDigamma x + x⁻¹ := by
  unfold bifrRealDigamma
  have hnonpole : ∀ m : ℕ, (x : ℂ) ≠ -m := by
    intro m hm
    have hm_real : (x : ℂ) = ((-(m : ℝ) : ℝ) : ℂ) := by
      simpa using hm
    have hre : x = -(m : ℝ) := by
      exact Complex.ofReal_injective hm_real
    have hnegpos : 0 < -(m : ℝ) := hre ▸ hx
    have hm_nonneg : (0 : ℝ) ≤ (m : ℝ) := by
      exact_mod_cast Nat.zero_le m
    linarith
  have h := Complex.digamma_apply_add_one (x : ℂ) hnonpole
  have hre := congrArg Complex.re h
  simpa using hre

/-- Recurrence-simplified form of the `log A` derivative for the combined
`b=p` route.

Using `ψ(η+1)=ψ(η)+1/η`, the apparent singular terms cancel:
`logA' = 2 * (log η + 1 - ψ(η+1))`.  This is the theorem-facing target used to
prove `logA' ≤ 0` from the simpler gap bound
`1 + log η ≤ ψ(η+1)`. -/
theorem bifrCombinedBpL1LogADerivative_eq_shifted_digamma_gap
    {η : ℝ} (hη : 0 < η) :
    bifrCombinedBpL1LogADerivative η =
      2 * (Real.log η + 1 - bifrRealDigamma (η + 1)) := by
  unfold bifrCombinedBpL1LogADerivative
  have hrec := bifrRealDigamma_apply_add_one (x := η) hη
  rw [hrec]
  field_simp [hη.ne']
  ring

/-- The shifted-digamma gap bound implies the `log A` derivative is
nonpositive. -/
theorem bifrCombinedBpL1LogADerivative_nonpos_of_shifted_digamma_gap
    {η : ℝ} (hη : 0 < η)
    (hgap : 1 + Real.log η ≤ bifrRealDigamma (η + 1)) :
    bifrCombinedBpL1LogADerivative η ≤ 0 := by
  rw [bifrCombinedBpL1LogADerivative_eq_shifted_digamma_gap hη]
  nlinarith

/-- Elementary logarithm comparison used by the Route B `log A` subclaim.

On the theorem interval \(0<\eta\le 1/4\), the bound `exp 1 < 3` gives
`exp 1 * η ≤ η + 1/2`, hence `1 + log η ≤ log (η + 1/2)`.  Combined with a
standard digamma lower bound `ψ(x) ≥ log (x - 1/2)` at `x = η + 1`, this would
close the `logA' ≤ 0` input. -/
theorem one_add_log_le_log_add_half_of_pos_le_quarter
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    1 + Real.log η ≤ Real.log (η + 1 / 2) := by
  have hmul : Real.exp 1 * η ≤ η + 1 / 2 := by
    calc
      Real.exp 1 * η ≤ 3 * η := by
        exact mul_le_mul_of_nonneg_right Real.exp_one_lt_three.le hη.le
      _ ≤ η + 1 / 2 := by nlinarith
  have hpos_mul : 0 < Real.exp 1 * η := mul_pos (Real.exp_pos 1) hη
  have hpos_add : 0 < η + 1 / 2 := by nlinarith
  have hlog := Real.log_le_log hpos_mul hmul
  simpa [Real.log_mul (Real.exp_pos 1).ne' hη.ne', Real.log_exp] using hlog

/-- If the classical shifted digamma lower bound
`log (η + 1/2) ≤ ψ(η + 1)` is available, then `logA' ≤ 0` follows on
`0 < η ≤ 1/4`.

This is the preferred theorem-facing route for the Route B `log A` subclaim:
formalize or import `ψ(x) ≥ log (x - 1/2)` for `x = η + 1`, then this wrapper
supplies the remaining elementary bridge. -/
theorem bifrCombinedBpL1LogADerivative_nonpos_of_digamma_ge_log_add_half
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hpsi : Real.log (η + 1 / 2) ≤ bifrRealDigamma (η + 1)) :
    bifrCombinedBpL1LogADerivative η ≤ 0 := by
  exact bifrCombinedBpL1LogADerivative_nonpos_of_shifted_digamma_gap hη
    ((one_add_log_le_log_add_half_of_pos_le_quarter hη hhi).trans hpsi)

/-- Source-assumption bridge for the Route B half-shift digamma certificate.

This theorem is intentionally scalar: a future source lemma supplies the
digamma finite-series lower bound, and the certificate supplies a rational
box proof that the same finite lower bound dominates the log upper line.  Lean
then composes those imported facts into the half-shift bound needed by
`bifrCombinedBpL1LogADerivative_nonpos_of_digamma_ge_log_add_half`. -/
theorem bifrDigammaOnePlusEta_ge_log_add_half_of_series_lower
    {η logUpper : ℝ} {N : ℕ}
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (hseries :
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N ≤
        bifrRealDigamma (η + 1)) :
    Real.log (η + 1 / 2) ≤ bifrRealDigamma (η + 1) :=
  hlog.trans (hbox.trans hseries)

/-- Second-order upper bound for `log(1-u)`.

This closes one source lemma used by the Route B half-shift certificate.  It
uses Mathlib's power-series identity for `-log(1-u)` and keeps the first two
nonnegative terms:
\(-\log(1-u)\ge u+u^2/2\). -/
theorem Real.log_one_sub_le_neg_sub_sq_half {u : ℝ}
    (hu0 : 0 ≤ u) (hu1 : u < 1) :
    Real.log (1 - u) ≤ -u - u ^ 2 / 2 := by
  have habs : |u| < 1 := by
    simpa [abs_of_nonneg hu0] using hu1
  have hsum := Real.hasSum_pow_div_log_of_abs_lt_one habs
  have hsumm := hsum.summable
  have hnonneg : ∀ n : ℕ, 0 ≤ u ^ (n + 1) / ((n : ℝ) + 1) := by
    intro n
    positivity
  have hpartial :
      (∑ i ∈ Finset.range 2, u ^ (i + 1) / ((i : ℝ) + 1)) ≤
        ∑' i : ℕ, u ^ (i + 1) / ((i : ℝ) + 1) :=
    hsumm.sum_le_tsum (Finset.range 2) (fun n _ => hnonneg n)
  have hpartial_eval :
      (∑ i ∈ Finset.range 2, u ^ (i + 1) / ((i : ℝ) + 1)) =
        u + u ^ 2 / 2 := by
    norm_num [Finset.sum_range_succ]
  have hmain : u + u ^ 2 / 2 ≤ -Real.log (1 - u) := by
    calc
      u + u ^ 2 / 2 =
          (∑ i ∈ Finset.range 2, u ^ (i + 1) / ((i : ℝ) + 1)) := by
            rw [hpartial_eval]
      _ ≤ ∑' i : ℕ, u ^ (i + 1) / ((i : ℝ) + 1) := hpartial
      _ = -Real.log (1 - u) := hsum.tsum_eq
  linarith

/-- Source-bound replacement for the Route B half-shift certificate's Euler
constant input.

The proof uses Mathlib's monotone upper sequence for Euler's constant at
index `32`, together with the decimal theorem `Real.log_two_gt_d9`.  The point
is not sharpness; it removes the imported numerical assumption
`\(\gamma_E \le 3/5\)` from the half-shift certificate route. -/
theorem bifrEulerMascheroniConstant_lt_three_fifths :
    Real.eulerMascheroniConstant < (3 / 5 : ℝ) := by
  refine (Real.eulerMascheroniConstant_lt_eulerMascheroniSeq' 32).trans ?_
  have hseq :
      Real.eulerMascheroniSeq' 32 =
        586061125622639 / 144403552893600 - Real.log (32 : ℝ) := by
    rw [Real.eulerMascheroniSeq']
    norm_num
  rw [hseq]
  have hlog32 : Real.log (32 : ℝ) = 5 * Real.log (2 : ℝ) := by
    rw [show (32 : ℝ) = 2 ^ 5 by norm_num, Real.log_pow]
    norm_num
  rw [hlog32]
  have hlog2 : (0.6931471803 : ℝ) < Real.log (2 : ℝ) :=
    Real.log_two_gt_d9
  nlinarith

/-- Non-strict form of `bifrEulerMascheroniConstant_lt_three_fifths`, matching
the certificate-side hypothesis shape. -/
theorem bifrEulerMascheroniConstant_le_three_fifths :
    Real.eulerMascheroniConstant ≤ (3 / 5 : ℝ) :=
  le_of_lt bifrEulerMascheroniConstant_lt_three_fifths

/-- Iterated real-digamma recurrence from `η+1` to `η+N+1`. -/
theorem bifrRealDigamma_one_add_eta_add_nat
    {η : ℝ} (hη : 0 ≤ η) (N : ℕ) :
    bifrRealDigamma (η + (N + 1 : ℕ)) =
      bifrRealDigamma (η + 1) +
        bifrDigammaOnePlusEtaReciprocalPartial η N := by
  induction N with
  | zero =>
      simp [bifrDigammaOnePlusEtaReciprocalPartial]
  | succ N ih =>
      have hx : 0 < η + (N + 1 : ℕ) := by positivity
      have hrec := bifrRealDigamma_apply_add_one (x := η + (N + 1 : ℕ)) hx
      have harg : η + ((N + 1) + 1 : ℕ) = η + (N + 1 : ℕ) + 1 := by
        norm_num
        ring
      rw [harg, hrec, ih]
      simp [bifrDigammaOnePlusEtaReciprocalPartial, Finset.sum_range_succ]
      ring

/-- The finite positive digamma-series partial equals a harmonic partial minus
the reciprocal partial from the iterated recurrence. -/
theorem bifrDigammaOnePlusEtaSeriesPartial_eq_harmonic_sub_reciprocal
    {η : ℝ} (hη : 0 ≤ η) (N : ℕ) :
    bifrDigammaOnePlusEtaSeriesPartial η N =
      (harmonic N : ℝ) - bifrDigammaOnePlusEtaReciprocalPartial η N := by
  induction N with
  | zero =>
      simp [bifrDigammaOnePlusEtaSeriesPartial,
        bifrDigammaOnePlusEtaReciprocalPartial]
  | succ N ih =>
      have hpos : 0 < ((N + 1 : ℕ) : ℝ) := by positivity
      have hden : ((N + 1 : ℕ) : ℝ) + η ≠ 0 := by positivity
      calc
        bifrDigammaOnePlusEtaSeriesPartial η (N + 1)
            = bifrDigammaOnePlusEtaSeriesPartial η N +
                η / (((N + 1 : ℕ) : ℝ) * (((N + 1 : ℕ) : ℝ) + η)) := by
              simp [bifrDigammaOnePlusEtaSeriesPartial, Finset.sum_range_succ]
        _ = ((harmonic N : ℝ) - bifrDigammaOnePlusEtaReciprocalPartial η N) +
                η / (((N + 1 : ℕ) : ℝ) * (((N + 1 : ℕ) : ℝ) + η)) := by
              rw [ih]
        _ = (harmonic (N + 1) : ℝ) -
                bifrDigammaOnePlusEtaReciprocalPartial η (N + 1) := by
              rw [harmonic_succ]
              simp only [bifrDigammaOnePlusEtaReciprocalPartial, Finset.sum_range_succ,
                Nat.cast_add, Nat.cast_one, Rat.cast_add, Rat.cast_inv,
                Rat.cast_natCast, Rat.cast_one]
              simp_rw [add_assoc, add_comm, add_left_comm]
              field_simp [hpos.ne', hden]
              ring_nf

/-- Exact value of the real digamma wrapper at positive integers:
\(\psi(N+1)=H_N-\gamma_E\). -/
theorem bifrRealDigamma_nat_add_one (N : ℕ) :
    bifrRealDigamma ((N + 1 : ℕ) : ℝ) =
      -Real.eulerMascheroniConstant + (harmonic N : ℝ) := by
  induction N with
  | zero =>
      unfold bifrRealDigamma
      have h := Complex.digamma_one
      have hre := congrArg Complex.re h
      norm_num at hre ⊢
      simpa using hre
  | succ N ih =>
      have hx : 0 < ((N + 1 : ℕ) : ℝ) := by positivity
      have hrec := bifrRealDigamma_apply_add_one (x := ((N + 1 : ℕ) : ℝ)) hx
      have harg : (((N + 1) + 1 : ℕ) : ℝ) = ((N + 1 : ℕ) : ℝ) + 1 := by
        norm_num
      rw [harg, hrec, ih, harmonic_succ]
      norm_num
      ring

/-- The local real digamma wrapper agrees with the real derivative of
`log ∘ Real.Gamma` on the positive real line. -/
theorem bifrRealDigamma_eq_deriv_log_Gamma {x : ℝ} (hx : 0 < x) :
    bifrRealDigamma x = deriv (Real.log ∘ Real.Gamma) x := by
  unfold bifrRealDigamma
  rw [Complex.digamma_def, logDeriv_apply]
  have hnonpoleC : ∀ m : ℕ, (x : ℂ) ≠ -m := by
    intro m hm
    have hre := congrArg Complex.re hm
    norm_num at hre
    have hmnonneg : (0 : ℝ) ≤ (m : ℝ) := by exact_mod_cast Nat.zero_le m
    nlinarith
  have hCder := (Complex.differentiableAt_Gamma (x : ℂ) hnonpoleC).hasDerivAt
  have hRealDer :
      HasDerivAt Real.Gamma ((deriv Complex.Gamma (x : ℂ)).re) x := by
    have h := hCder.real_of_complex
    have hfun :
        (fun y : ℝ => (Complex.Gamma (y : ℂ)).re) = Real.Gamma := by
      funext y
      rw [Complex.Gamma_ofReal]
      rfl
    simpa [hfun] using h
  have hgamma_pos : 0 < Real.Gamma x := Real.Gamma_pos_of_pos hx
  have hlogder :
      deriv (Real.log ∘ Real.Gamma) x =
        (deriv Complex.Gamma (x : ℂ)).re / Real.Gamma x := by
    rw [Function.comp_def]
    rw [deriv.log hRealDer.differentiableAt hgamma_pos.ne']
    rw [hRealDer.deriv]
  rw [hlogder, Complex.Gamma_ofReal]
  simp only [Complex.ofReal_re, Complex.ofReal_im, Complex.div_re,
    Complex.normSq_ofReal, mul_zero]
  field_simp [hgamma_pos.ne']
  ring_nf

/-- The real digamma wrapper is monotone on the positive real line.

This follows from the Bohr-Mollerup convexity theorem for `log ∘ Gamma` and
the identification of `bifrRealDigamma` with its real derivative. -/
theorem bifrRealDigamma_monotoneOn_pos :
    MonotoneOn bifrRealDigamma (Set.Ioi (0 : ℝ)) := by
  intro x hx y hy hxy
  have hfd : ∀ z ∈ Set.Ioi (0 : ℝ), DifferentiableAt ℝ (Real.log ∘ Real.Gamma) z := by
    intro z hz
    exact (Real.differentiableAt_Gamma (fun m ↦ by
      have hzpos : 0 < z := hz
      have hmnonneg : (0 : ℝ) ≤ (m : ℝ) := by exact_mod_cast Nat.zero_le m
      nlinarith [hzpos, hmnonneg])).log (Real.Gamma_pos_of_pos hz).ne'
  have hmono := Real.convexOn_log_Gamma.monotoneOn_deriv hfd hx hy hxy
  rwa [← bifrRealDigamma_eq_deriv_log_Gamma hx,
    ← bifrRealDigamma_eq_deriv_log_Gamma hy] at hmono

/-- The real digamma wrapper is nonpositive at `1`. -/
theorem bifrRealDigamma_one_nonpos :
    bifrRealDigamma 1 ≤ 0 := by
  have h := bifrRealDigamma_nat_add_one 0
  norm_num at h
  rw [h]
  exact neg_nonpos.mpr (le_of_lt ((by norm_num : (0 : ℝ) < 1 / 2).trans
    Real.one_half_lt_eulerMascheroniConstant))

/-- On the Route B `ell_1 / p` interval, the `ψ(1-η)` part of the raw
`T` log-derivative is nonpositive.

This reduces the remaining `logT'` box checks to elementary raw-`T`
derivative bounds: the special-function contribution only helps. -/
theorem bifrRealDigamma_one_sub_eta_nonpos {η : ℝ}
    (hη0 : 0 ≤ η) (hη1 : η < 1) :
    bifrRealDigamma (1 - η) ≤ 0 := by
  have hpos : 1 - η ∈ Set.Ioi (0 : ℝ) := by
    simp
    linarith
  have hone : (1 : ℝ) ∈ Set.Ioi (0 : ℝ) := by simp
  have hle : 1 - η ≤ 1 := by linarith
  exact (bifrRealDigamma_monotoneOn_pos hpos hone hle).trans
    bifrRealDigamma_one_nonpos

/-- If the elementary raw-`T` log-derivative is below a box bound, then the
actual `T` log-derivative, `rawLogDeriv + ψ(1-η)`, is below the same bound.

This is the Route B reduction that removes digamma from the remaining
`logT'` eta-box obligations. -/
theorem tLogDerivative_le_of_rawLogDerivative_le
    {η rawLogDeriv tBound : ℝ}
    (hη0 : 0 ≤ η) (hη1 : η < 1)
    (hraw : rawLogDeriv ≤ tBound) :
    rawLogDeriv + bifrRealDigamma (1 - η) ≤ tBound := by
  have hψ := bifrRealDigamma_one_sub_eta_nonpos hη0 hη1
  linarith

/-- The remaining Route B digamma source lemma can be reduced to endpoint
monotonicity after a finite recurrence.

If the shifted endpoint satisfies
\(-\gamma_E+H_N\le\psi(1+\eta+N)\), then the finite positive-series lower bound
at `1+η` follows.  In particular, a future monotonicity theorem for the real
digamma wrapper would prove this endpoint inequality from
`\psi(N+1)=-\gamma_E+H_N`. -/
theorem bifrDigammaOnePlusEta_euler_series_lower_of_endpoint_ge
    {η : ℝ} (hη : 0 ≤ η) {N : ℕ}
    (hendpoint :
      -Real.eulerMascheroniConstant + (harmonic N : ℝ) ≤
        bifrRealDigamma (η + (N + 1 : ℕ))) :
    -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N ≤
      bifrRealDigamma (η + 1) := by
  rw [bifrRealDigamma_one_add_eta_add_nat hη N] at hendpoint
  rw [bifrDigammaOnePlusEtaSeriesPartial_eq_harmonic_sub_reciprocal hη N]
  linarith

/-- Endpoint-monotonicity form of the remaining Route B digamma source lemma.

It is enough to prove that the real digamma wrapper is nondecreasing from
`N+1` to `N+1+η`; the exact positive-integer value and the finite recurrence
then give the positive-series lower bound at `1+η`. -/
theorem bifrDigammaOnePlusEta_euler_series_lower_of_endpoint_mono
    {η : ℝ} (hη : 0 ≤ η) {N : ℕ}
    (hmono :
      bifrRealDigamma (((N + 1 : ℕ) : ℝ)) ≤
        bifrRealDigamma (η + (N + 1 : ℕ))) :
    -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N ≤
      bifrRealDigamma (η + 1) :=
  bifrDigammaOnePlusEta_euler_series_lower_of_endpoint_ge hη
    ((bifrRealDigamma_nat_add_one N).symm ▸ hmono)

/-- Positive finite-series lower bound for the shifted digamma wrapper.

This closes the source formula previously imported by the Route B half-shift
certificate.  It is just the finite recurrence, the exact positive-integer
value of digamma, and monotonicity on the positive real line. -/
theorem bifrDigammaOnePlusEta_euler_series_lower
    {η : ℝ} (hη : 0 ≤ η) (N : ℕ) :
    -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N ≤
      bifrRealDigamma (η + 1) := by
  refine bifrDigammaOnePlusEta_euler_series_lower_of_endpoint_mono hη ?_
  apply bifrRealDigamma_monotoneOn_pos
  · change 0 < (((N + 1 : ℕ) : ℝ))
    positivity
  · change 0 < η + (N + 1 : ℕ)
    positivity
  · nlinarith

/-- Half-shift bridge with no remaining digamma source assumption.

The certificate supplies only the elementary/log-upper arithmetic rows
`hlog` and `hbox`; the digamma finite-series lower bound and Euler-constant
upper bound are now proved in Lean. -/
theorem bifrDigammaOnePlusEta_ge_log_add_half_of_certificate
    {η logUpper : ℝ} {N : ℕ}
    (hη : 0 ≤ η)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    Real.log (η + 1 / 2) ≤ bifrRealDigamma (η + 1) := by
  have hgamma :
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N ≤
        -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N := by
    linarith [bifrEulerMascheroniConstant_le_three_fifths]
  exact hlog.trans (hbox.trans (hgamma.trans
    (bifrDigammaOnePlusEta_euler_series_lower hη N)))

/-- Positivity certificate for the 8-term Route B half-shift rational gap.

After using `log(1-u) ≤ -u-u^2/2` with `u=1/2-η`, the remaining arithmetic is
a rational function. Its numerator has a positive Bernstein expansion on
`η ∈ [0, 1/4]`, which is what this lemma records. -/
theorem bifrDigammaHalfShiftEightTermNumerator_nonneg
    {η : ℝ} (hη : 0 ≤ η) (hhi : η ≤ (1 / 4 : ℝ)) :
    0 ≤
      35 * η ^ 10 + 1155 * η ^ 9 + 15522 * η ^ 8 + 107782 * η ^ 7 +
        396627 * η ^ 6 + 639387 * η ^ 5 - 207872 * η ^ 4 -
        1934772 * η ^ 3 - 1544952 * η ^ 2 + 269168 * η + 70560 := by
  let y : ℝ := 4 * η
  have hy0 : 0 ≤ y := by dsimp [y]; nlinarith
  have hy1 : 0 ≤ 1 - y := by dsimp [y]; nlinarith
  have hbern :
      35 * η ^ 10 + 1155 * η ^ 9 + 15522 * η ^ 8 + 107782 * η ^ 7 +
          396627 * η ^ 6 + 639387 * η ^ 5 - 207872 * η ^ 4 -
          1934772 * η ^ 3 - 1544952 * η ^ 2 + 269168 * η + 70560 =
        70560 * (1 - y) ^ 10 +
          10 * ((386446 : ℝ) / 5) * y * (1 - y) ^ 9 +
          45 * ((2456179 : ℝ) / 30) * y ^ 2 * (1 - y) ^ 8 +
          120 * ((53797361 : ℝ) / 640) * y ^ 3 * (1 - y) ^ 7 +
          210 * ((40123507 : ℝ) / 480) * y ^ 4 * (1 - y) ^ 6 +
          252 * ((328549349 : ℝ) / 4096) * y ^ 5 * (1 - y) ^ 5 +
          210 * ((3017423219 : ℝ) / 40960) * y ^ 6 * (1 - y) ^ 4 +
          120 * ((20875169753 : ℝ) / 327680) * y ^ 7 * (1 - y) ^ 3 +
          45 * ((24618204311 : ℝ) / 491520) * y ^ 8 * (1 - y) ^ 2 +
          10 * ((17080981335 : ℝ) / 524288) * y ^ 9 * (1 - y) +
          ((11510996175 : ℝ) / 1048576) * y ^ 10 := by
    dsimp [y]
    ring
  rw [hbern]
  positivity

/-- Direct 8-term rational arithmetic for the Route B half-shift certificate.

This removes the need for the 4096-box rational certificate in the half-shift
subroute: the same 8-term lower bound is globally enough on
`0 ≤ η ≤ 1/4`. -/
theorem bifrDigammaHalfShiftEightTermGap_nonneg
    {η : ℝ} (hη : 0 ≤ η) (hhi : η ≤ (1 / 4 : ℝ)) :
    0 ≤
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η 8 +
        (1 / 2 - η) + (1 / 2 - η) ^ 2 / 2 := by
  have hnum := bifrDigammaHalfShiftEightTermNumerator_nonneg hη hhi
  have hden1 : η + 1 ≠ 0 := by nlinarith
  have hden2 : η + 2 ≠ 0 := by nlinarith
  have hden3 : η + 3 ≠ 0 := by nlinarith
  have hden4 : η + 4 ≠ 0 := by nlinarith
  have hden5 : η + 5 ≠ 0 := by nlinarith
  have hden6 : η + 6 ≠ 0 := by nlinarith
  have hden7 : η + 7 ≠ 0 := by nlinarith
  have hden8 : η + 8 ≠ 0 := by nlinarith
  have hdenpos :
      0 < 70 * (η + 1) * (η + 2) * (η + 3) * (η + 4) *
        (η + 5) * (η + 6) * (η + 7) * (η + 8) := by
    positivity
  rw [show
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η 8 +
          (1 / 2 - η) + (1 / 2 - η) ^ 2 / 2 =
        (35 * η ^ 10 + 1155 * η ^ 9 + 15522 * η ^ 8 + 107782 * η ^ 7 +
          396627 * η ^ 6 + 639387 * η ^ 5 - 207872 * η ^ 4 -
          1934772 * η ^ 3 - 1544952 * η ^ 2 + 269168 * η + 70560) /
          (70 * (η + 1) * (η + 2) * (η + 3) * (η + 4) *
            (η + 5) * (η + 6) * (η + 7) * (η + 8)) by
        simp [bifrDigammaOnePlusEtaSeriesPartial, Finset.sum_range_succ]
        field_simp [hden1, hden2, hden3, hden4, hden5, hden6, hden7, hden8]
        ring]
  exact div_nonneg hnum hdenpos.le

/-- Direct Route B half-shift bound from the Lean-proved source lemmas and the
global 8-term rational certificate. -/
theorem bifrDigammaOnePlusEta_ge_log_add_half_direct
    {η : ℝ} (hη : 0 ≤ η) (hhi : η ≤ (1 / 4 : ℝ)) :
    Real.log (η + 1 / 2) ≤ bifrRealDigamma (η + 1) := by
  have hu0 : 0 ≤ 1 / 2 - η := by nlinarith
  have hu1 : 1 / 2 - η < 1 := by nlinarith
  have hlogUpper :
      Real.log (η + 1 / 2) ≤ -(1 / 2 - η) - (1 / 2 - η) ^ 2 / 2 := by
    have hlog :=
      Real.log_one_sub_le_neg_sub_sq_half (u := 1 / 2 - η) hu0 hu1
    convert hlog using 1
    ring_nf
  have hgap := bifrDigammaHalfShiftEightTermGap_nonneg hη hhi
  have hlogToSeries :
      Real.log (η + 1 / 2) ≤
        -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η 8 := by
    linarith
  have hgamma :
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η 8 ≤
        -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η 8 := by
    nlinarith [bifrEulerMascheroniConstant_le_three_fifths]
  exact hlogToSeries.trans (hgamma.trans
    (bifrDigammaOnePlusEta_euler_series_lower hη 8))

/-- Direct `logA' <= 0` bridge for Route B, no half-shift box certificate
required. -/
theorem bifrCombinedBpL1LogADerivative_nonpos_direct
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    bifrCombinedBpL1LogADerivative η ≤ 0 :=
  bifrCombinedBpL1LogADerivative_nonpos_of_digamma_ge_log_add_half hη hhi
    (bifrDigammaOnePlusEta_ge_log_add_half_direct hη.le hhi)

/-- Fully composed `logA' <= 0` bridge from the Route B half-shift
certificate arithmetic, with the digamma series and Euler-constant inputs now
proved in Lean. -/
theorem bifrCombinedBpL1LogADerivative_nonpos_of_certificate
    {η logUpper : ℝ} {N : ℕ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    bifrCombinedBpL1LogADerivative η ≤ 0 :=
  bifrCombinedBpL1LogADerivative_nonpos_of_digamma_ge_log_add_half hη hhi
    (bifrDigammaOnePlusEta_ge_log_add_half_of_certificate hη.le hlog hbox)

/-- Half-shift bridge with the Euler constant kept in the imported digamma
series source lemma.

This is the theorem-facing form of the remaining source obligation:
`hseries` is the positive finite-series lower bound
\(-\gamma_E+\sum_{n=1}^N \eta/(n(n+\eta))\le\psi(1+\eta)\).  The coarse
replacement \(-3/5\) is now handled internally by
`bifrEulerMascheroniConstant_le_three_fifths`. -/
theorem bifrDigammaOnePlusEta_ge_log_add_half_of_euler_series_lower
    {η logUpper : ℝ} {N : ℕ}
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (hseries :
      -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N ≤
        bifrRealDigamma (η + 1)) :
    Real.log (η + 1 / 2) ≤ bifrRealDigamma (η + 1) := by
  have hgamma :
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N ≤
        -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N := by
    linarith [bifrEulerMascheroniConstant_le_three_fifths]
  exact hlog.trans (hbox.trans (hgamma.trans hseries))

/-- Fully composed `logA' <= 0` bridge from the Route B half-shift source
assumptions. -/
theorem bifrCombinedBpL1LogADerivative_nonpos_of_series_lower
    {η logUpper : ℝ} {N : ℕ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (hseries :
      -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N ≤
        bifrRealDigamma (η + 1)) :
    bifrCombinedBpL1LogADerivative η ≤ 0 :=
  bifrCombinedBpL1LogADerivative_nonpos_of_digamma_ge_log_add_half hη hhi
    (bifrDigammaOnePlusEta_ge_log_add_half_of_series_lower hlog hbox hseries)

/-- Fully composed `logA' <= 0` bridge from the theorem-facing Route B
positive-series source lemma with the actual Euler constant. -/
theorem bifrCombinedBpL1LogADerivative_nonpos_of_euler_series_lower
    {η logUpper : ℝ} {N : ℕ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (hseries :
      -Real.eulerMascheroniConstant + bifrDigammaOnePlusEtaSeriesPartial η N ≤
        bifrRealDigamma (η + 1)) :
    bifrCombinedBpL1LogADerivative η ≤ 0 :=
  bifrCombinedBpL1LogADerivative_nonpos_of_digamma_ge_log_add_half hη hhi
    (bifrDigammaOnePlusEta_ge_log_add_half_of_euler_series_lower hlog hbox hseries)

/-- Source-formula recurrence for the local real log-gamma wrapper.

This closes the exact recurrence part of the gamma/Stirling primitive source
formula before the shifted large-argument log-gamma term is enclosed. -/
theorem bifrRealLogGamma_apply_add_one {x : ℝ} (hx : 0 < x) :
    bifrRealLogGamma (x + 1) = bifrRealLogGamma x + Real.log x := by
  unfold bifrRealLogGamma
  rw [Real.Gamma_add_one hx.ne']
  have hgamma_pos : 0 < Real.Gamma x := Real.Gamma_pos_of_pos hx
  rw [Real.log_mul hx.ne' hgamma_pos.ne']
  ring

/-- Source-formula recurrence for the gamma inverse-square primitive.

This is the Lean counterpart of the recurrence part of the
`recurrence_stirling_source_bounds_for_inv_gamma_sq` primitive source lemma.
It does not formalize Stirling's enclosure; it only closes the exact recurrence
used to shift the primitive endpoint from `x` to `x+1`. -/
theorem bifrGammaInvSq_apply_add_one {x : ℝ} (hx : 0 < x) :
    bifrGammaInvSq (x + 1) = x⁻¹ ^ 2 * bifrGammaInvSq x := by
  unfold bifrGammaInvSq
  rw [Real.Gamma_add_one hx.ne']
  ring

/-- Gamma inverse-square as an exponential of the local log-gamma wrapper.

This theorem isolates the final exponentiation step in the gamma primitive
source row: once a certificate encloses `log Gamma(x)`, monotonicity of `exp`
turns that into an interval for `Gamma(x)^{-2}`. -/
theorem bifrGammaInvSq_eq_exp_neg_two_logGamma {x : ℝ} (hx : 0 < x) :
    bifrGammaInvSq x = Real.exp (-2 * bifrRealLogGamma x) := by
  unfold bifrGammaInvSq bifrRealLogGamma
  have hgamma_pos : 0 < Real.Gamma x := Real.Gamma_pos_of_pos hx
  calc
    (Real.Gamma x)⁻¹ ^ 2
        = (Real.exp (Real.log (Real.Gamma x)))⁻¹ ^ 2 := by
            rw [Real.exp_log hgamma_pos]
    _ = Real.exp (-(Real.log (Real.Gamma x))) ^ 2 := by
            rw [Real.exp_neg]
    _ = Real.exp (2 * (-(Real.log (Real.Gamma x)))) := by
            rw [← Real.exp_nat_mul]
            norm_num
    _ = Real.exp (-2 * Real.log (Real.Gamma x)) := by ring_nf

/-- Certificate-facing exponentiation consumer for the gamma inverse-square row.

If a certificate provides an interval for `log Gamma(x)` and outward-rounded
endpoint exponentials, Lean composes them into an interval for
`Gamma(x)^{-2}`. -/
theorem bifrGammaInvSq_sourceInterval_of_logGamma_interval_bounds
    {x logLo logHi invLo invHi : ℝ}
    (hx : 0 < x)
    (hlogLo : logLo ≤ bifrRealLogGamma x)
    (hlogHi : bifrRealLogGamma x ≤ logHi)
    (hinvLo : invLo ≤ Real.exp (-2 * logHi))
    (hinvHi : Real.exp (-2 * logLo) ≤ invHi) :
    invLo ≤ bifrGammaInvSq x ∧ bifrGammaInvSq x ≤ invHi := by
  have hrepr := bifrGammaInvSq_eq_exp_neg_two_logGamma (x := x) hx
  have hlo :
      Real.exp (-2 * logHi) ≤ Real.exp (-2 * bifrRealLogGamma x) := by
    exact Real.exp_le_exp.mpr (by nlinarith)
  have hhi :
      Real.exp (-2 * bifrRealLogGamma x) ≤ Real.exp (-2 * logLo) := by
    exact Real.exp_le_exp.mpr (by nlinarith)
  constructor <;> linarith

/-- Pointwise interval for reciprocal recurrence terms over an `x`-box. -/
theorem bifrReciprocalShiftTerm_interval
    {x lo hi : ℝ} (j : ℕ)
    (hlo_pos : 0 < lo) (hlo : lo ≤ x) (hhi : x ≤ hi) :
    (hi + j)⁻¹ ≤ (x + j)⁻¹ ∧ (x + j)⁻¹ ≤ (lo + j)⁻¹ := by
  have hlo_j_pos : 0 < lo + (j : ℝ) := by positivity
  have hx_j_pos : 0 < x + (j : ℝ) := by linarith
  have hhi_j_pos : 0 < hi + (j : ℝ) := by linarith
  constructor
  · simpa [one_div] using
      one_div_le_one_div_of_le hx_j_pos (by linarith : x + (j : ℝ) ≤ hi + j)
  · simpa [one_div] using
      one_div_le_one_div_of_le hlo_j_pos (by linarith : lo + (j : ℝ) ≤ x + j)

/-- Finite reciprocal recurrence sum interval over an `x`-box. -/
theorem bifrReciprocalShiftFiniteSum_interval
    {x lo hi : ℝ} {M : ℕ}
    (hlo_pos : 0 < lo) (hlo : lo ≤ x) (hhi : x ≤ hi) :
    (∑ j ∈ Finset.range M, (hi + j)⁻¹) ≤
        ∑ j ∈ Finset.range M, (x + j)⁻¹ ∧
      (∑ j ∈ Finset.range M, (x + j)⁻¹) ≤
        ∑ j ∈ Finset.range M, (lo + j)⁻¹ := by
  constructor
  · exact Finset.sum_le_sum (fun j _ =>
      (bifrReciprocalShiftTerm_interval
        (x := x) (lo := lo) (hi := hi) j hlo_pos hlo hhi).1)
  · exact Finset.sum_le_sum (fun j _ =>
      (bifrReciprocalShiftTerm_interval
        (x := x) (lo := lo) (hi := hi) j hlo_pos hlo hhi).2)

/-- Pointwise interval for log recurrence terms over an `x`-box. -/
theorem bifrLogShiftTerm_interval
    {x lo hi : ℝ} (j : ℕ)
    (hlo_pos : 0 < lo) (hlo : lo ≤ x) (hhi : x ≤ hi) :
    Real.log (lo + j) ≤ Real.log (x + j) ∧
      Real.log (x + j) ≤ Real.log (hi + j) := by
  have hlo_j_pos : 0 < lo + (j : ℝ) := by positivity
  constructor
  · exact Real.log_le_log hlo_j_pos (by linarith)
  · have hx_j_pos : 0 < x + (j : ℝ) := by linarith
    exact Real.log_le_log hx_j_pos (by linarith)

/-- Finite log recurrence sum interval over an `x`-box. -/
theorem bifrLogShiftFiniteSum_interval
    {x lo hi : ℝ} {M : ℕ}
    (hlo_pos : 0 < lo) (hlo : lo ≤ x) (hhi : x ≤ hi) :
    (∑ j ∈ Finset.range M, Real.log (lo + j)) ≤
        ∑ j ∈ Finset.range M, Real.log (x + j) ∧
      (∑ j ∈ Finset.range M, Real.log (x + j)) ≤
        ∑ j ∈ Finset.range M, Real.log (hi + j) := by
  constructor
  · exact Finset.sum_le_sum (fun j _ =>
      (bifrLogShiftTerm_interval
        (x := x) (lo := lo) (hi := hi) j hlo_pos hlo hhi).1)
  · exact Finset.sum_le_sum (fun j _ =>
      (bifrLogShiftTerm_interval
        (x := x) (lo := lo) (hi := hi) j hlo_pos hlo hhi).2)

/-- Finite-shift recurrence for the real digamma wrapper.

This is the exact recurrence identity behind the primitive source row with
recurrence shift `M`: the source bound only needs an interval for
`ψ(x + M)` after this identity is applied. -/
theorem bifrRealDigamma_apply_add_nat {x : ℝ} (hx : 0 < x) (M : ℕ) :
    bifrRealDigamma (x + M) =
      bifrRealDigamma x + ∑ j ∈ Finset.range M, (x + j)⁻¹ := by
  induction M with
  | zero => simp
  | succ M ih =>
      have hxM : 0 < x + M := by positivity
      calc
        bifrRealDigamma (x + (Nat.succ M : ℕ))
            = bifrRealDigamma ((x + M) + 1) := by
              norm_num [Nat.cast_succ, add_assoc]
        _ = bifrRealDigamma (x + M) + (x + M)⁻¹ :=
              bifrRealDigamma_apply_add_one hxM
        _ = (bifrRealDigamma x + ∑ j ∈ Finset.range M, (x + j)⁻¹) +
              (x + M)⁻¹ := by rw [ih]
        _ = bifrRealDigamma x + ∑ j ∈ Finset.range (Nat.succ M), (x + j)⁻¹ := by
              rw [Finset.sum_range_succ]
              ring

/-- Rearranged finite-shift digamma recurrence used by the source enclosure. -/
theorem bifrRealDigamma_eq_shift_sub_sum {x : ℝ} (hx : 0 < x) (M : ℕ) :
    bifrRealDigamma x =
      bifrRealDigamma (x + M) - ∑ j ∈ Finset.range M, (x + j)⁻¹ := by
  rw [bifrRealDigamma_apply_add_nat hx M]
  ring

/-- Certificate-facing interval consumer for the shifted digamma recurrence.

If a certificate encloses the shifted value `ψ(x+M)` and the finite reciprocal
recurrence sum separately, then Lean composes those two intervals into an
interval for the primitive value `ψ(x)`. -/
theorem bifrRealDigamma_sourceInterval_of_shift_sum_interval_bounds
    {x shiftedLo shiftedHi sumLo sumHi : ℝ} {M : ℕ}
    (hx : 0 < x)
    (hshiftLo : shiftedLo ≤ bifrRealDigamma (x + M))
    (hshiftHi : bifrRealDigamma (x + M) ≤ shiftedHi)
    (hsumLo : sumLo ≤ ∑ j ∈ Finset.range M, (x + j)⁻¹)
    (hsumHi : (∑ j ∈ Finset.range M, (x + j)⁻¹) ≤ sumHi) :
    shiftedLo - sumHi ≤ bifrRealDigamma x ∧
      bifrRealDigamma x ≤ shiftedHi - sumLo := by
  have hrec := bifrRealDigamma_eq_shift_sub_sum (x := x) hx M
  constructor <;> linarith

/-- Finite-shift recurrence for the local real log-gamma wrapper. -/
theorem bifrRealLogGamma_apply_add_nat {x : ℝ} (hx : 0 < x) (M : ℕ) :
    bifrRealLogGamma (x + M) =
      bifrRealLogGamma x + ∑ j ∈ Finset.range M, Real.log (x + j) := by
  induction M with
  | zero => simp
  | succ M ih =>
      have hxM : 0 < x + M := by positivity
      calc
        bifrRealLogGamma (x + (Nat.succ M : ℕ))
            = bifrRealLogGamma ((x + M) + 1) := by
              norm_num [Nat.cast_succ, add_assoc]
        _ = bifrRealLogGamma (x + M) + Real.log (x + M) :=
              bifrRealLogGamma_apply_add_one hxM
        _ = (bifrRealLogGamma x + ∑ j ∈ Finset.range M, Real.log (x + j)) +
              Real.log (x + M) := by rw [ih]
        _ = bifrRealLogGamma x +
              ∑ j ∈ Finset.range (Nat.succ M), Real.log (x + j) := by
              rw [Finset.sum_range_succ]
              ring

/-- Rearranged finite-shift log-gamma recurrence used by the Stirling source
enclosure. -/
theorem bifrRealLogGamma_eq_shift_sub_sum {x : ℝ} (hx : 0 < x) (M : ℕ) :
    bifrRealLogGamma x =
      bifrRealLogGamma (x + M) - ∑ j ∈ Finset.range M, Real.log (x + j) := by
  rw [bifrRealLogGamma_apply_add_nat hx M]
  ring

/-- Certificate-facing interval consumer for the shifted log-gamma recurrence.

This is the log-gamma analogue of
`bifrRealDigamma_sourceInterval_of_shift_sum_interval_bounds`.  It composes a
shifted large-argument log-gamma enclosure with a finite logarithmic recurrence
sum enclosure. -/
theorem bifrRealLogGamma_sourceInterval_of_shift_sum_interval_bounds
    {x shiftedLo shiftedHi sumLo sumHi : ℝ} {M : ℕ}
    (hx : 0 < x)
    (hshiftLo : shiftedLo ≤ bifrRealLogGamma (x + M))
    (hshiftHi : bifrRealLogGamma (x + M) ≤ shiftedHi)
    (hsumLo : sumLo ≤ ∑ j ∈ Finset.range M, Real.log (x + j))
    (hsumHi : (∑ j ∈ Finset.range M, Real.log (x + j)) ≤ sumHi) :
    shiftedLo - sumHi ≤ bifrRealLogGamma x ∧
      bifrRealLogGamma x ≤ shiftedHi - sumLo := by
  have hrec := bifrRealLogGamma_eq_shift_sub_sum (x := x) hx M
  constructor <;> linarith

/-- Finite-shift recurrence for the gamma inverse-square primitive.

This is the exact recurrence identity behind the primitive source row with
recurrence shift `M`, before the shifted gamma value is enclosed by Stirling's
formula. -/
theorem bifrGammaInvSq_apply_add_nat {x : ℝ} (hx : 0 < x) (M : ℕ) :
    bifrGammaInvSq (x + M) =
      (∏ j ∈ Finset.range M, (x + j)⁻¹ ^ 2) * bifrGammaInvSq x := by
  induction M with
  | zero => simp
  | succ M ih =>
      have hxM : 0 < x + M := by positivity
      calc
        bifrGammaInvSq (x + (Nat.succ M : ℕ))
            = bifrGammaInvSq ((x + M) + 1) := by
              norm_num [Nat.cast_succ, add_assoc]
        _ = (x + M)⁻¹ ^ 2 * bifrGammaInvSq (x + M) :=
              bifrGammaInvSq_apply_add_one hxM
        _ = (x + M)⁻¹ ^ 2 *
              ((∏ j ∈ Finset.range M, (x + j)⁻¹ ^ 2) * bifrGammaInvSq x) := by
              rw [ih]
        _ = (∏ j ∈ Finset.range (Nat.succ M), (x + j)⁻¹ ^ 2) *
              bifrGammaInvSq x := by
              rw [Finset.prod_range_succ]
              ring

/-- The power-tail source term `x^(-a)` is antitone on any positive interval
when `a ≥ 0`. -/
theorem antitoneOn_bifrPowerTailTerm_of_nonneg
    {a lo hi : ℝ} (ha : 0 ≤ a) (hlo : 0 < lo) :
    AntitoneOn (bifrPowerTailTerm a) (Set.Icc lo hi) := by
  intro x hx y _hy hxy
  unfold bifrPowerTailTerm
  have hx_pos : 0 < x := lt_of_lt_of_le hlo hx.1
  exact Real.rpow_le_rpow_of_nonpos hx_pos hxy (neg_nonpos.mpr ha)

/-- Lower finite-tail source comparison for `x^(-a)`.

For a decreasing power tail, the integral over `[N,M]` is bounded by the
unshifted integer partial sum over `N, ..., M-1`.  This is the finite version
of the lower integral-tail bracketing used before taking the improper tail
limit in the zeta source formula. -/
theorem bifrPowerTailIntegralLower_le_partial
    {a : ℝ} {N M : ℕ}
    (hNM : N ≤ M) (ha : 0 ≤ a) (hNpos : 0 < (N : ℝ)) :
    (∫ x in (N : ℝ)..(M : ℝ), bifrPowerTailTerm a x) ≤
      bifrPowerTailPartial a N M := by
  unfold bifrPowerTailPartial
  exact
    (antitoneOn_bifrPowerTailTerm_of_nonneg (a := a)
      (lo := (N : ℝ)) (hi := (M : ℝ)) ha hNpos).integral_le_sum_Ico hNM

/-- Upper finite-tail source comparison for `x^(-a)`.

For a decreasing power tail, the shifted integer partial sum over
`N+1, ..., M` is bounded by the integral over `[N,M]`.  This is the finite
version of the upper integral-tail bracketing used by the zeta source formula. -/
theorem bifrShiftedPowerTailPartial_le_integralUpper
    {a : ℝ} {N M : ℕ}
    (hNM : N ≤ M) (ha : 0 ≤ a) (hNpos : 0 < (N : ℝ)) :
    bifrShiftedPowerTailPartial a N M ≤
      (∫ x in (N : ℝ)..(M : ℝ), bifrPowerTailTerm a x) := by
  unfold bifrShiftedPowerTailPartial
  exact
    (antitoneOn_bifrPowerTailTerm_of_nonneg (a := a)
      (lo := (N : ℝ)) (hi := (M : ℝ)) ha hNpos).sum_le_integral_Ico hNM

/-- Derivative of the closed-form antiderivative for the power tail. -/
theorem hasDerivAt_bifrPowerTailAntiderivative
    {a x : ℝ} (ha : a ≠ 1) (hx : 0 < x) :
    HasDerivAt (bifrPowerTailAntiderivative a) (bifrPowerTailTerm a x) x := by
  unfold bifrPowerTailAntiderivative bifrPowerTailTerm
  have hpow : HasDerivAt (fun y : ℝ => y ^ (1 - a))
      ((1 - a) * x ^ (-a)) x := by
    convert (hasDerivAt_id x).rpow_const
        (p := 1 - a) (Or.inl hx.ne') using 1
    simp [id]
  have h := hpow.div_const (1 - a)
  have hden : 1 - a ≠ 0 := by
    intro hzero
    apply ha
    linarith
  have hder : ((1 - a) * x ^ (-a)) / (1 - a) = x ^ (-a) := by
    field_simp [hden]
  simpa [hder] using h

/-- Closed-form finite interval evaluation of the power-tail integral. -/
theorem bifrPowerTailIntegral_eq_antiderivative_sub
    {a u v : ℝ} (ha : a ≠ 1) (hu : 0 < u) (huv : u ≤ v) :
    (∫ x in u..v, bifrPowerTailTerm a x) =
      bifrPowerTailAntiderivative a v - bifrPowerTailAntiderivative a u := by
  have hcont : ContinuousOn (bifrPowerTailAntiderivative a) (Set.Icc u v) := by
    unfold bifrPowerTailAntiderivative
    exact (continuousOn_id.rpow_const
      (fun x hx => Or.inl (lt_of_lt_of_le hu hx.1).ne')).div_const _
  have hderiv : ∀ x ∈ Set.Ioo u v,
      HasDerivAt (bifrPowerTailAntiderivative a) (bifrPowerTailTerm a x) x := by
    intro x hx
    exact hasDerivAt_bifrPowerTailAntiderivative ha (lt_trans hu hx.1)
  have hcontTerm : ContinuousOn (bifrPowerTailTerm a) (Set.Icc u v) := by
    unfold bifrPowerTailTerm
    exact continuousOn_id.rpow_const
      (fun x hx => Or.inl (lt_of_lt_of_le hu hx.1).ne')
  have hcontTermU : ContinuousOn (bifrPowerTailTerm a) (Set.uIcc u v) := by
    rw [Set.uIcc_of_le huv]
    exact hcontTerm
  have hint : IntervalIntegrable (bifrPowerTailTerm a) MeasureTheory.volume u v :=
    hcontTermU.intervalIntegrable
  exact intervalIntegral.integral_eq_sub_of_hasDerivAt_of_le huv hcont hderiv hint

/-- The power-tail antiderivative tends to zero at infinity for exponents
`a > 1`.

This is the first improper-limit endpoint in the zeta source formula.  Combined
with `bifrPowerTailIntegral_eq_antiderivative_sub`, it turns the finite
closed-form tail integral into the source interval
`N^(1-a)/(a-1)`. -/
theorem tendsto_bifrPowerTailAntiderivative_atTop
    {a : ℝ} (ha : 1 < a) :
    Tendsto (fun x : ℝ => bifrPowerTailAntiderivative a x) atTop (𝓝 0) := by
  unfold bifrPowerTailAntiderivative
  have hpos : 0 < a - 1 := by linarith
  have ht : Tendsto (fun x : ℝ => x ^ (-(a - 1))) atTop (𝓝 0) :=
    tendsto_rpow_neg_atTop hpos
  have hfun : (fun x : ℝ => x ^ (1 - a) / (1 - a)) =
      (fun x : ℝ => x ^ (-(a - 1)) / (1 - a)) := by
    funext x
    congr 2
    ring
  rw [hfun]
  simpa only [zero_div] using ht.div_const (1 - a)

/-- Closed-form improper power-tail integral.

This theorem is the Lean source surface for the integral-tail endpoint used by
the finite-sum source bounds for `ζ(a)` on the BIFR restricted exponent range. -/
theorem tendsto_bifrPowerTailIntegral_atTop
    {a N : ℝ} (ha : 1 < a) (hN : 0 < N) :
    Tendsto (fun M : ℝ => ∫ x in N..M, bifrPowerTailTerm a x) atTop
      (𝓝 (N ^ (1 - a) / (a - 1))) := by
  have hF := tendsto_bifrPowerTailAntiderivative_atTop (a := a) ha
  have hlim := hF.sub_const (bifrPowerTailAntiderivative a N)
  have htarget :
      (0 : ℝ) - bifrPowerTailAntiderivative a N =
        N ^ (1 - a) / (a - 1) := by
    unfold bifrPowerTailAntiderivative
    have hden : 1 - a = -(a - 1) := by ring
    rw [hden]
    have hne : a - 1 ≠ 0 := ne_of_gt (by linarith : 0 < a - 1)
    field_simp [hne]
    ring
  rw [← htarget]
  refine hlim.congr' ?_
  filter_upwards [eventually_ge_atTop N] with M hNM
  exact (bifrPowerTailIntegral_eq_antiderivative_sub (a := a) (u := N) (v := M)
    (by linarith) hN hNM).symm

/-- Conditional source bounds for the positive power-tail series.

If the two finite tail partial-sum shapes used by the source formula converge
to the same tail value, then the already-kernel-checked finite
sum/integral comparisons and improper endpoint formula imply the usual
integral-tail bracket:
\[
  \int_{N+1}^{\infty} x^{-a}\,dx
  \le \text{tail}
  \le \int_N^{\infty} x^{-a}\,dx.
\]
This theorem intentionally leaves the tail-series convergence hypothesis
external; it is the next source-authority layer after the improper endpoint
formulas. -/
theorem bifrPowerTailSourceBounds_of_partial_tendsto
    {a tail : ℝ} {N : ℕ}
    (ha : 1 < a) (hN : 0 < (N : ℝ))
    (hLowerTail :
      Tendsto (fun M : ℕ => bifrPowerTailPartial a (N + 1) M) atTop (𝓝 tail))
    (hUpperTail :
      Tendsto (fun M : ℕ => bifrShiftedPowerTailPartial a N M) atTop (𝓝 tail)) :
    ((N + 1 : ℕ) : ℝ) ^ (1 - a) / (a - 1) ≤ tail ∧
      tail ≤ (N : ℝ) ^ (1 - a) / (a - 1) := by
  have hN1pos : 0 < (((N + 1 : ℕ) : ℝ)) := by positivity
  have hIntLower :
      Tendsto
        (fun M : ℕ =>
          ∫ x in (((N + 1 : ℕ) : ℝ))..(M : ℝ), bifrPowerTailTerm a x)
        atTop (𝓝 ((((N + 1 : ℕ) : ℝ)) ^ (1 - a) / (a - 1))) :=
    (tendsto_bifrPowerTailIntegral_atTop
      (a := a) (N := ((N + 1 : ℕ) : ℝ)) ha hN1pos).comp
        tendsto_natCast_atTop_atTop
  have hIntUpper :
      Tendsto (fun M : ℕ => ∫ x in (N : ℝ)..(M : ℝ), bifrPowerTailTerm a x)
        atTop (𝓝 ((N : ℝ) ^ (1 - a) / (a - 1))) :=
    (tendsto_bifrPowerTailIntegral_atTop (a := a) (N := (N : ℝ)) ha hN).comp
      tendsto_natCast_atTop_atTop
  constructor
  · exact le_of_tendsto_of_tendsto hIntLower hLowerTail (by
      filter_upwards [eventually_ge_atTop (N + 1)] with M hM
      exact bifrPowerTailIntegralLower_le_partial (a := a) (N := N + 1) (M := M)
        hM (by linarith) hN1pos)
  · exact le_of_tendsto_of_tendsto hUpperTail hIntUpper (by
      filter_upwards [eventually_ge_atTop N] with M hM
      exact bifrShiftedPowerTailPartial_le_integralUpper (a := a) (N := N) (M := M)
        hM (by linarith) hN)

/-- Source bounds for the canonical power-tail series value.

This instantiates `bifrPowerTailSourceBounds_of_partial_tendsto` with the
kernel-checked power-tail summability and tail-identification lemmas, leaving
only numerical enclosure of the finite source expression as an external
certificate obligation. -/
theorem bifrPowerTailSourceBounds_tsum_tail
    {a : ℝ} {N : ℕ} (ha : 1 < a) (hN : 0 < (N : ℝ)) :
    ((N + 1 : ℕ) : ℝ) ^ (1 - a) / (a - 1) ≤
        ((∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) -
          ∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ)) ∧
      ((∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) -
          ∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ)) ≤
        (N : ℝ) ^ (1 - a) / (a - 1) := by
  let tail :=
    ((∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) -
      ∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ))
  have hLowerTail :
      Tendsto (fun M : ℕ => bifrPowerTailPartial a (N + 1) M) atTop (𝓝 tail) := by
    simpa [tail] using tendsto_bifrPowerTailPartial_atTop_of_one_lt
      (a := a) ha (N + 1)
  have hUpperTail :
      Tendsto (fun M : ℕ => bifrShiftedPowerTailPartial a N M) atTop (𝓝 tail) := by
    have hlim := tendsto_bifrShiftedPowerTailPartial_atTop_of_one_lt (a := a) ha N
    have htail_eq :
        ((∑' i : ℕ, bifrPowerTailTerm a (((i + 1 : ℕ) : ℝ))) -
          ∑ i ∈ Finset.range N, bifrPowerTailTerm a (((i + 1 : ℕ) : ℝ))) =
            tail := by
      dsimp [tail]
      exact tsum_shiftedTail_eq_tsumTail_succ
        (f := fun i : ℕ => bifrPowerTailTerm a (i : ℝ))
        (summable_bifrPowerTailTerm_of_one_lt (a := a) ha) N
    rwa [htail_eq] at hlim
  exact bifrPowerTailSourceBounds_of_partial_tendsto
    (a := a) (tail := tail) (N := N) ha hN hLowerTail hUpperTail

/-- Compose finite-prefix and tail interval bounds.

This is the last scalar interval-arithmetic step in the zeta/zeta-prime source
rows: once a finite source sum and its integral-tail remainder are separately
enclosed, their sum is enclosed by adding the lower and upper endpoints. -/
theorem add_interval_bounds_of_bounds
    {finite tail finiteLo finiteHi tailLo tailHi : ℝ}
    (hfiniteLo : finiteLo ≤ finite)
    (hfiniteHi : finite ≤ finiteHi)
    (htailLo : tailLo ≤ tail)
    (htailHi : tail ≤ tailHi) :
    finiteLo + tailLo ≤ finite + tail ∧
      finite + tail ≤ finiteHi + tailHi := by
  constructor <;> linarith

/-- Finite-sum interval arithmetic from pointwise interval bounds.

This is the source-sum counterpart of `add_interval_bounds_of_bounds`: if every
summand lies in its recorded interval, then the finite sum lies in the sum of
those intervals. -/
theorem finset_sum_interval_bounds_of_pointwise_bounds
    {α : Type*} {s : Finset α} {f lo hi : α → ℝ}
    (hlo : ∀ i ∈ s, lo i ≤ f i)
    (hhi : ∀ i ∈ s, f i ≤ hi i) :
    (∑ i ∈ s, lo i) ≤ ∑ i ∈ s, f i ∧
      (∑ i ∈ s, f i) ≤ ∑ i ∈ s, hi i := by
  constructor
  · exact Finset.sum_le_sum fun i hi_mem => hlo i hi_mem
  · exact Finset.sum_le_sum fun i hi_mem => hhi i hi_mem

/-- Finite-prefix interval arithmetic for the power-tail source sum. -/
theorem bifrPowerTailFinitePrefix_interval_of_pointwise_bounds
    {a : ℝ} {N : ℕ} {lo hi : ℕ → ℝ}
    (hlo : ∀ i ∈ Finset.range (N + 1), lo i ≤ bifrPowerTailTerm a (i : ℝ))
    (hhi : ∀ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ) ≤ hi i) :
    (∑ i ∈ Finset.range (N + 1), lo i) ≤
        ∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ) ∧
      (∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ)) ≤
        ∑ i ∈ Finset.range (N + 1), hi i :=
  finset_sum_interval_bounds_of_pointwise_bounds hlo hhi

/-- Finite-prefix interval arithmetic for the log-power source sum. -/
theorem bifrLogPowerTailFinitePrefix_interval_of_pointwise_bounds
    {a : ℝ} {N : ℕ} {lo hi : ℕ → ℝ}
    (hlo : ∀ i ∈ Finset.range (N + 1), lo i ≤ bifrLogPowerTailTerm a (i : ℝ))
    (hhi : ∀ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ) ≤ hi i) :
    (∑ i ∈ Finset.range (N + 1), lo i) ≤
        ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ) ∧
      (∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)) ≤
        ∑ i ∈ Finset.range (N + 1), hi i :=
  finset_sum_interval_bounds_of_pointwise_bounds hlo hhi

/-- Exponent-box finite-prefix interval for the nonzero power-tail source sum.

This specializes the pointwise endpoint rule to the actual finite-prefix shape
used by the zeta source row.  The remaining certificate obligation is numeric
endpoint evaluation of the two displayed finite sums. -/
theorem bifrPowerTailFinitePrefix_Icc_exponent_interval
    {a lo hi : ℝ} {N : ℕ} (hlo : lo ≤ a) (hhi : a ≤ hi) :
    (∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm hi (i : ℝ)) ≤
        ∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm a (i : ℝ) ∧
      (∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm a (i : ℝ)) ≤
        ∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm lo (i : ℝ) := by
  constructor
  · exact Finset.sum_le_sum fun i hi_mem =>
      (bifrPowerTailTerm_nat_exponent_interval
        (a := a) (lo := lo) (hi := hi) (m := i)
        (Finset.mem_Icc.mp hi_mem).1 hlo hhi).1
  · exact Finset.sum_le_sum fun i hi_mem =>
      (bifrPowerTailTerm_nat_exponent_interval
        (a := a) (lo := lo) (hi := hi) (m := i)
        (Finset.mem_Icc.mp hi_mem).1 hlo hhi).2

/-- Exponent-box finite-prefix interval for the log-power source sum.

The lower index `2` matches the positive source series for `-ζ'(a)`.  The
pointwise monotonicity has already absorbed the nonnegative logarithm factor,
so the finite-prefix sum is bounded by endpoint-prefix sums. -/
theorem bifrLogPowerTailFinitePrefix_Icc_exponent_interval
    {a lo hi : ℝ} {N : ℕ} (hlo : lo ≤ a) (hhi : a ≤ hi) :
    (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm hi (i : ℝ)) ≤
        ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ) ∧
      (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ)) ≤
        ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm lo (i : ℝ) := by
  constructor
  · exact Finset.sum_le_sum fun i hi_mem =>
      (bifrLogPowerTailTerm_nat_exponent_interval
        (a := a) (lo := lo) (hi := hi) (m := i)
        (le_trans (by norm_num : 1 ≤ 2) (Finset.mem_Icc.mp hi_mem).1) hlo hhi).1
  · exact Finset.sum_le_sum fun i hi_mem =>
      (bifrLogPowerTailTerm_nat_exponent_interval
        (a := a) (lo := lo) (hi := hi) (m := i)
        (le_trans (by norm_num : 1 ≤ 2) (Finset.mem_Icc.mp hi_mem).1) hlo hhi).2

/-- The range-prefix power sum equals the natural nonzero prefix.

The source theorem for the full `tsum` is phrased with `range (N+1)` because
that is the canonical `Nat` prefix for `tsum`; the zeta source formula records
the same finite prefix as `m=1,\ldots,N`.  The omitted `m=0` term is zero for
the exponent range used here. -/
theorem bifrPowerTailFinitePrefix_range_eq_Icc
    {a : ℝ} (ha : a ≠ 0) (N : ℕ) :
    (∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ)) =
      ∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm a (i : ℝ) := by
  symm
  refine Finset.sum_subset ?subset ?zero
  · intro i hi_mem
    exact Finset.mem_range.mpr (Nat.lt_succ_of_le (Finset.mem_Icc.mp hi_mem).2)
  · intro i hi_range hnot
    have hi_le : i ≤ N := Nat.le_of_lt_succ (Finset.mem_range.mp hi_range)
    have hi_not_ge : ¬ 1 ≤ i := by
      intro hge
      exact hnot (Finset.mem_Icc.mpr ⟨hge, hi_le⟩)
    have hi_zero : i = 0 := Nat.eq_zero_of_not_pos hi_not_ge
    subst hi_zero
    simp [bifrPowerTailTerm, ha]

/-- The range-prefix log-power sum equals the natural `m=2,\ldots,N` prefix.

The omitted `m=0` and `m=1` terms are zero, so the certificate can state finite
zeta-prime source prefixes in the usual `2..N` form. -/
theorem bifrLogPowerTailFinitePrefix_range_eq_Icc
    (a : ℝ) (N : ℕ) :
    (∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)) =
      ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ) := by
  symm
  refine Finset.sum_subset ?subset ?zero
  · intro i hi_mem
    exact Finset.mem_range.mpr (Nat.lt_succ_of_le (Finset.mem_Icc.mp hi_mem).2)
  · intro i hi_range hnot
    have hi_le : i ≤ N := Nat.le_of_lt_succ (Finset.mem_range.mp hi_range)
    have hi_not_ge : ¬ 2 ≤ i := by
      intro hge
      exact hnot (Finset.mem_Icc.mpr ⟨hge, hi_le⟩)
    have hi_le_one : i ≤ 1 := Nat.lt_succ_iff.mp (Nat.lt_of_not_ge hi_not_ge)
    interval_cases i <;> simp [bifrLogPowerTailTerm]

/-- Sign-reversal for interval bounds.

This is used by the zeta-prime source row: the finite-sum source expression is
the positive series for `-ζ'(a)`, while the primitive interval may be recorded
for `ζ'(a)` itself. -/
theorem neg_interval_bounds_of_bounds
    {x lo hi : ℝ} (hlo : lo ≤ x) (hhi : x ≤ hi) :
    -hi ≤ -x ∧ -x ≤ -lo := by
  constructor <;> linarith

/-- Source interval for the canonical power-tail primitive from a finite-prefix
enclosure.

The theorem consumes only the numerical finite-prefix enclosure as a hypothesis;
the tail enclosure is supplied by `bifrPowerTailSourceBounds_tsum_tail`.  This
is the Lean bridge from certified finite sums plus closed-form tail endpoints
to a source interval for the full `tsum` value used by the zeta primitive row. -/
theorem bifrPowerTailTsum_sourceInterval_of_finite_bounds
    {a finiteLo finiteHi : ℝ} {N : ℕ}
    (ha : 1 < a) (hN : 0 < (N : ℝ))
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ))
    (hfiniteHi :
      (∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ)) ≤ finiteHi) :
    finiteLo + ((N + 1 : ℕ) : ℝ) ^ (1 - a) / (a - 1) ≤
        (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ≤
        finiteHi + (N : ℝ) ^ (1 - a) / (a - 1) := by
  let finite := ∑ i ∈ Finset.range (N + 1), bifrPowerTailTerm a (i : ℝ)
  let tail := (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) - finite
  have htail := bifrPowerTailSourceBounds_tsum_tail (a := a) (N := N) ha hN
  have hsum : finite + tail = (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) := by
    dsimp [tail]
    ring
  have hinterval :=
    add_interval_bounds_of_bounds
      (finite := finite) (tail := tail)
      (finiteLo := finiteLo) (finiteHi := finiteHi)
      (tailLo := ((N + 1 : ℕ) : ℝ) ^ (1 - a) / (a - 1))
      (tailHi := (N : ℝ) ^ (1 - a) / (a - 1))
      hfiniteLo hfiniteHi htail.1 htail.2
  constructor
  · simpa [hsum] using hinterval.1
  · simpa [hsum] using hinterval.2

/-- Source interval for the canonical power-tail primitive from the natural
nonzero finite prefix `m=1,\ldots,N`.

This wrapper lets certificates use the displayed zeta source prefix directly;
the zero term required by the canonical `tsum` range prefix is handled by
`bifrPowerTailFinitePrefix_range_eq_Icc`. -/
theorem bifrPowerTailTsum_sourceInterval_of_Icc_finite_bounds
    {a finiteLo finiteHi : ℝ} {N : ℕ}
    (ha : 1 < a) (hN : 0 < (N : ℝ))
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm a (i : ℝ))
    (hfiniteHi :
      (∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm a (i : ℝ)) ≤ finiteHi) :
    finiteLo + ((N + 1 : ℕ) : ℝ) ^ (1 - a) / (a - 1) ≤
        (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ≤
        finiteHi + (N : ℝ) ^ (1 - a) / (a - 1) := by
  have hprefix := bifrPowerTailFinitePrefix_range_eq_Icc
    (a := a) (by linarith : a ≠ 0) N
  exact bifrPowerTailTsum_sourceInterval_of_finite_bounds
    (a := a) (N := N) ha hN
    (by simpa [hprefix] using hfiniteLo)
    (by simpa [hprefix] using hfiniteHi)

/-- Full power-tail source interval over an exponent box.

This is the theorem-facing source wrapper for the zeta row after endpoint
reduction: finite-prefix sums and closed-form tail endpoints are evaluated
only at the exponent-box endpoints. -/
theorem bifrPowerTailTsum_sourceInterval_of_Icc_exponent_bounds
    {a lo hi : ℝ} {N : ℕ}
    (hlo_gt : 1 < lo) (hN : 0 < (N : ℝ))
    (hlo : lo ≤ a) (hhi : a ≤ hi) :
    (∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm hi (i : ℝ)) +
        bifrPowerTailEndpoint hi (((N + 1 : ℕ) : ℝ)) ≤
        (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ≤
        (∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm lo (i : ℝ)) +
          bifrPowerTailEndpoint lo (N : ℝ) := by
  have ha : 1 < a := lt_of_lt_of_le hlo_gt hlo
  have hprefix :=
    bifrPowerTailFinitePrefix_Icc_exponent_interval
      (a := a) (lo := lo) (hi := hi) (N := N) hlo hhi
  have hsource :=
    bifrPowerTailTsum_sourceInterval_of_Icc_finite_bounds
      (a := a) (N := N) ha hN hprefix.1 hprefix.2
  have hN1 : 1 ≤ (((N + 1 : ℕ) : ℝ)) := by exact_mod_cast Nat.succ_pos N
  have hNge : 1 ≤ (N : ℝ) := by
    exact_mod_cast Nat.succ_le_of_lt (by exact_mod_cast hN)
  have htailLower :=
    (bifrPowerTailEndpoint_exponent_interval
      (a := a) (lo := lo) (hi := hi) (N := (((N + 1 : ℕ) : ℝ)))
      hN1 hlo_gt hlo hhi).1
  have htailUpper :=
    (bifrPowerTailEndpoint_exponent_interval
      (a := a) (lo := lo) (hi := hi) (N := (N : ℝ))
      hNge hlo_gt hlo hhi).2
  unfold bifrPowerTailEndpoint at htailLower htailUpper
  unfold bifrPowerTailEndpoint
  constructor
  · linarith
  · linarith

/-- Certificate-facing full power-tail source interval over an exponent box.

This is the final scalar consumer for the zeta finite-sum/integral-tail source
row: a certificate may provide outward-rounded lower/upper bounds for the
endpoint-prefix sums and endpoint-tail values, and Lean composes them into a
source interval for the full `tsum`. -/
theorem bifrPowerTailTsum_sourceInterval_of_endpoint_interval_bounds
    {a lo hi finiteLo finiteHi tailLo tailHi : ℝ} {N : ℕ}
    (hlo_gt : 1 < lo) (hN : 0 < (N : ℝ))
    (hlo : lo ≤ a) (hhi : a ≤ hi)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm hi (i : ℝ))
    (htailLo :
      tailLo ≤ bifrPowerTailEndpoint hi (((N + 1 : ℕ) : ℝ)))
    (hfiniteHi :
      (∑ i ∈ Finset.Icc 1 N, bifrPowerTailTerm lo (i : ℝ)) ≤ finiteHi)
    (htailHi :
      bifrPowerTailEndpoint lo (N : ℝ) ≤ tailHi) :
    finiteLo + tailLo ≤
        (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrPowerTailTerm a (i : ℝ)) ≤
        finiteHi + tailHi := by
  have hsource :=
    bifrPowerTailTsum_sourceInterval_of_Icc_exponent_bounds
      (a := a) (lo := lo) (hi := hi) (N := N) hlo_gt hN hlo hhi
  constructor <;> linarith

/-- Derivative of the log-power tail term used for `-ζ'(a)`. -/
theorem hasDerivAt_bifrLogPowerTailTerm
    {a x : ℝ} (hx : 0 < x) :
    HasDerivAt (bifrLogPowerTailTerm a)
      (x ^ (-a) * x⁻¹ * (1 - a * Real.log x)) x := by
  unfold bifrLogPowerTailTerm
  have hlog : HasDerivAt Real.log x⁻¹ x := Real.hasDerivAt_log hx.ne'
  have hpow : HasDerivAt (fun y : ℝ => y ^ (-a))
      ((-a) * x ^ (-a - 1)) x := by
    simpa using
      (hasDerivAt_id x).rpow_const
        (p := -a) (Or.inl hx.ne')
  have h := hlog.mul hpow
  convert h using 1
  have hpow_split : x ^ (-a - 1) = x ^ (-a) * x⁻¹ := by
    rw [← Real.rpow_neg_one x, ← Real.rpow_add hx]
    ring_nf
  rw [hpow_split]
  ring

/-- Derivative of the closed-form antiderivative for the log-power tail. -/
theorem hasDerivAt_bifrLogPowerTailAntiderivative
    {a x : ℝ} (ha : a ≠ 1) (hx : 0 < x) :
    HasDerivAt (bifrLogPowerTailAntiderivative a) (bifrLogPowerTailTerm a x) x := by
  unfold bifrLogPowerTailAntiderivative bifrLogPowerTailTerm
  have hpow : HasDerivAt (fun y : ℝ => y ^ (1 - a)) ((1 - a) * x ^ (-a)) x := by
    convert (hasDerivAt_id x).rpow_const
        (p := 1 - a) (Or.inl hx.ne') using 1
    simp [id]
  have hinner : HasDerivAt
      (fun y : ℝ => Real.log y / (1 - a) - 1 / (1 - a) ^ 2)
      (x⁻¹ / (1 - a)) x := by
    simpa using
      ((Real.hasDerivAt_log hx.ne').div_const (1 - a)).sub_const
        (1 / (1 - a) ^ 2)
  have h := hpow.mul hinner
  have hden : 1 - a ≠ 0 := by
    intro hzero
    apply ha
    linarith
  have hxpow : x ^ (1 - a) = x * x ^ (-a) := by
    rw [show 1 - a = 1 + (-a) by ring, Real.rpow_add hx, Real.rpow_one]
  convert h using 1
  rw [hxpow]
  field_simp [hden]
  ring_nf

/-- Closed-form finite interval evaluation of the log-power tail integral. -/
theorem bifrLogPowerTailIntegral_eq_antiderivative_sub
    {a u v : ℝ} (ha : a ≠ 1) (hu : 0 < u) (huv : u ≤ v) :
    (∫ x in u..v, bifrLogPowerTailTerm a x) =
      bifrLogPowerTailAntiderivative a v - bifrLogPowerTailAntiderivative a u := by
  have hcont : ContinuousOn (bifrLogPowerTailAntiderivative a) (Set.Icc u v) := by
    unfold bifrLogPowerTailAntiderivative
    have hpow : ContinuousOn (fun x : ℝ => x ^ (1 - a)) (Set.Icc u v) :=
      continuousOn_id.rpow_const (fun x hx => Or.inl (lt_of_lt_of_le hu hx.1).ne')
    have hlog : ContinuousOn Real.log (Set.Icc u v) :=
      Real.continuousOn_log.mono (fun x hx => (lt_of_lt_of_le hu hx.1).ne')
    exact hpow.mul ((hlog.div_const _).sub continuousOn_const)
  have hderiv : ∀ x ∈ Set.Ioo u v,
      HasDerivAt (bifrLogPowerTailAntiderivative a) (bifrLogPowerTailTerm a x) x := by
    intro x hx
    exact hasDerivAt_bifrLogPowerTailAntiderivative ha (lt_trans hu hx.1)
  have hcontTerm : ContinuousOn (bifrLogPowerTailTerm a) (Set.Icc u v) := by
    unfold bifrLogPowerTailTerm
    have hlog : ContinuousOn Real.log (Set.Icc u v) :=
      Real.continuousOn_log.mono (fun x hx => (lt_of_lt_of_le hu hx.1).ne')
    have hpow : ContinuousOn (fun x : ℝ => x ^ (-a)) (Set.Icc u v) :=
      continuousOn_id.rpow_const (fun x hx => Or.inl (lt_of_lt_of_le hu hx.1).ne')
    exact hlog.mul hpow
  have hcontTermU : ContinuousOn (bifrLogPowerTailTerm a) (Set.uIcc u v) := by
    rw [Set.uIcc_of_le huv]
    exact hcontTerm
  have hint : IntervalIntegrable (bifrLogPowerTailTerm a) MeasureTheory.volume u v :=
    hcontTermU.intervalIntegrable
  exact intervalIntegral.integral_eq_sub_of_hasDerivAt_of_le huv hcont hderiv hint

/-- Log-power decay at infinity for the exponent range `a > 1`.

This is the asymptotic fact behind the improper endpoint for the `-ζ'` source
formula: the logarithm grows more slowly than every positive power. -/
theorem tendsto_bifrLogMulPower_atTop
    {a : ℝ} (ha : 1 < a) :
    Tendsto (fun x : ℝ => Real.log x * x ^ (1 - a)) atTop (𝓝 0) := by
  have hpos : 0 < a - 1 := by linarith
  have hdiv : Tendsto (fun x : ℝ => Real.log x / x ^ (a - 1)) atTop (𝓝 0) :=
    (isLittleO_log_rpow_atTop hpos).tendsto_div_nhds_zero
  refine hdiv.congr' ?_
  filter_upwards [eventually_ge_atTop (0 : ℝ)] with x hx
  rw [show 1 - a = -(a - 1) by ring]
  rw [Real.rpow_neg hx]
  ring

/-- The log-power antiderivative tends to zero at infinity for exponents
`a > 1`. -/
theorem tendsto_bifrLogPowerTailAntiderivative_atTop
    {a : ℝ} (ha : 1 < a) :
    Tendsto (fun x : ℝ => bifrLogPowerTailAntiderivative a x) atTop (𝓝 0) := by
  unfold bifrLogPowerTailAntiderivative
  have hpos : 0 < a - 1 := by linarith
  have hpow : Tendsto (fun x : ℝ => x ^ (1 - a)) atTop (𝓝 0) := by
    have ht : Tendsto (fun x : ℝ => x ^ (-(a - 1))) atTop (𝓝 0) :=
      tendsto_rpow_neg_atTop hpos
    have hfun : (fun x : ℝ => x ^ (1 - a)) =
        (fun x : ℝ => x ^ (-(a - 1))) := by
      funext x
      congr 1
      ring
    rwa [hfun]
  have hlogpow := tendsto_bifrLogMulPower_atTop (a := a) ha
  have h1 := hlogpow.div_const (1 - a)
  have h2 := hpow.mul_const (1 / (1 - a) ^ 2)
  have hsub := h1.sub h2
  convert hsub using 1
  · funext x
    ring_nf
  · ring_nf

/-- Closed-form improper log-power tail integral.

This theorem is the Lean source surface for the integral-tail endpoint used by
the finite-sum source bounds for `-ζ'(a)` on the BIFR restricted exponent
range. -/
theorem tendsto_bifrLogPowerTailIntegral_atTop
    {a N : ℝ} (ha : 1 < a) (hN : 0 < N) :
    Tendsto (fun M : ℝ => ∫ x in N..M, bifrLogPowerTailTerm a x) atTop
      (𝓝 (N ^ (1 - a) * (Real.log N / (a - 1) + 1 / (a - 1) ^ 2))) := by
  have hF := tendsto_bifrLogPowerTailAntiderivative_atTop (a := a) ha
  have hlim := hF.sub_const (bifrLogPowerTailAntiderivative a N)
  have htarget :
      (0 : ℝ) - bifrLogPowerTailAntiderivative a N =
        N ^ (1 - a) * (Real.log N / (a - 1) + 1 / (a - 1) ^ 2) := by
    unfold bifrLogPowerTailAntiderivative
    have hne : a - 1 ≠ 0 := ne_of_gt (by linarith : 0 < a - 1)
    have hden : 1 - a = -(a - 1) := by ring
    rw [hden]
    field_simp [hne]
    ring
  rw [← htarget]
  refine hlim.congr' ?_
  filter_upwards [eventually_ge_atTop N] with M hNM
  exact (bifrLogPowerTailIntegral_eq_antiderivative_sub (a := a) (u := N) (v := M)
    (by linarith) hN hNM).symm

/-- The log-power source term `log(x)x^(-a)` is antitone on positive
intervals where `1 ≤ a log(x)`. -/
theorem antitoneOn_bifrLogPowerTailTerm_of_one_le_mul_log
    {a lo hi : ℝ} (hlo : 0 < lo)
    (hlog : ∀ x ∈ Set.Icc lo hi, 1 ≤ a * Real.log x) :
    AntitoneOn (bifrLogPowerTailTerm a) (Set.Icc lo hi) := by
  refine antitoneOn_of_hasDerivWithinAt_nonpos
    (D := Set.Icc lo hi)
    (f := bifrLogPowerTailTerm a)
    (f' := fun x => x ^ (-a) * x⁻¹ * (1 - a * Real.log x))
    (convex_Icc lo hi) ?cont ?deriv ?nonpos
  · unfold bifrLogPowerTailTerm
    have hlog_cont : ContinuousOn Real.log (Set.Icc lo hi) := by
      exact Real.continuousOn_log.mono
        (fun x hx => (lt_of_lt_of_le hlo hx.1).ne')
    have hpow_cont : ContinuousOn (fun x : ℝ => x ^ (-a)) (Set.Icc lo hi) := by
      exact continuousOn_id.rpow_const
        (fun x hx => Or.inl (lt_of_lt_of_le hlo hx.1).ne')
    exact hlog_cont.mul hpow_cont
  · intro x hx
    have hxIcc : x ∈ Set.Icc lo hi := interior_subset hx
    exact (hasDerivAt_bifrLogPowerTailTerm (lt_of_lt_of_le hlo hxIcc.1)).hasDerivWithinAt
  · intro x hx
    have hxIcc : x ∈ Set.Icc lo hi := interior_subset hx
    have hx_pos : 0 < x := lt_of_lt_of_le hlo hxIcc.1
    have hpow_nonneg : 0 ≤ x ^ (-a) := Real.rpow_nonneg hx_pos.le _
    have hinv_nonneg : 0 ≤ x⁻¹ := inv_nonneg.mpr hx_pos.le
    have hfactor : 1 - a * Real.log x ≤ 0 := by
      linarith [hlog x hxIcc]
    exact mul_nonpos_of_nonneg_of_nonpos
      (mul_nonneg hpow_nonneg hinv_nonneg) hfactor

/-- On intervals with left endpoint at least `2`, the `-ζ'` log-power tail
term is antitone for the exponent range used by the BIFR primitive
certificate. -/
theorem antitoneOn_bifrLogPowerTailTerm_of_three_halves_le
    {a lo hi : ℝ} (ha : (3 / 2 : ℝ) ≤ a) (hlo : 2 ≤ lo) :
    AntitoneOn (bifrLogPowerTailTerm a) (Set.Icc lo hi) := by
  have hlo_pos : 0 < lo := by linarith
  refine antitoneOn_bifrLogPowerTailTerm_of_one_le_mul_log
    (a := a) (lo := lo) (hi := hi) hlo_pos ?_
  intro x hx
  have hx_ge_two : (2 : ℝ) ≤ x := hlo.trans hx.1
  have hlogx : Real.log 2 ≤ Real.log x :=
    Real.log_le_log (by norm_num) hx_ge_two
  have hlogx_lower : (2 / 3 : ℝ) ≤ Real.log x :=
    bifrLogTwo_lower_two_thirds.trans hlogx
  calc
    (1 : ℝ) = (3 / 2) * (2 / 3) := by norm_num
    _ ≤ a * Real.log x := by
      have ha_nonneg : 0 ≤ a := by linarith
      exact mul_le_mul ha hlogx_lower (by linarith) ha_nonneg

/-- Lower finite-tail source comparison for the `-ζ'` log-power term. -/
theorem bifrLogPowerTailIntegralLower_le_partial
    {a : ℝ} {N M : ℕ}
    (hNM : N ≤ M) (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N) :
    (∫ x in (N : ℝ)..(M : ℝ), bifrLogPowerTailTerm a x) ≤
      bifrLogPowerTailPartial a N M := by
  unfold bifrLogPowerTailPartial
  exact
    (antitoneOn_bifrLogPowerTailTerm_of_three_halves_le (a := a)
      (lo := (N : ℝ)) (hi := (M : ℝ)) ha (by exact_mod_cast hN)).integral_le_sum_Ico hNM

/-- Upper finite-tail source comparison for the `-ζ'` log-power term. -/
theorem bifrShiftedLogPowerTailPartial_le_integralUpper
    {a : ℝ} {N M : ℕ}
    (hNM : N ≤ M) (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N) :
    bifrShiftedLogPowerTailPartial a N M ≤
      (∫ x in (N : ℝ)..(M : ℝ), bifrLogPowerTailTerm a x) := by
  unfold bifrShiftedLogPowerTailPartial
  exact
    (antitoneOn_bifrLogPowerTailTerm_of_three_halves_le (a := a)
      (lo := (N : ℝ)) (hi := (M : ℝ)) ha (by exact_mod_cast hN)).sum_le_integral_Ico hNM

/-- Conditional source bounds for the positive log-power tail series used by
`-ζ'(a)`.

The exponent side condition matches the monotonicity lemma used for the finite
sum/integral comparison.  The theorem leaves convergence of the two finite
tail partial-sum shapes as an explicit external hypothesis, then turns those
hypotheses into the closed-form integral-tail bracket for the limiting tail. -/
theorem bifrLogPowerTailSourceBounds_of_partial_tendsto
    {a tail : ℝ} {N : ℕ}
    (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N)
    (hLowerTail :
      Tendsto (fun M : ℕ => bifrLogPowerTailPartial a (N + 1) M) atTop (𝓝 tail))
    (hUpperTail :
      Tendsto (fun M : ℕ => bifrShiftedLogPowerTailPartial a N M) atTop (𝓝 tail)) :
    ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
        (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2) ≤ tail ∧
      tail ≤ (N : ℝ) ^ (1 - a) *
        (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2) := by
  have ha_gt : 1 < a := by linarith
  have hNpos : 0 < (N : ℝ) := by
    exact_mod_cast (lt_of_lt_of_le (by norm_num : 0 < 2) hN)
  have hN1pos : 0 < (((N + 1 : ℕ) : ℝ)) := by positivity
  have hIntLower :
      Tendsto
        (fun M : ℕ =>
          ∫ x in (((N + 1 : ℕ) : ℝ))..(M : ℝ), bifrLogPowerTailTerm a x)
        atTop
        (𝓝 ((((N + 1 : ℕ) : ℝ) ^ (1 - a) *
          (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2)))) :=
    (tendsto_bifrLogPowerTailIntegral_atTop
      (a := a) (N := ((N + 1 : ℕ) : ℝ)) ha_gt hN1pos).comp
        tendsto_natCast_atTop_atTop
  have hIntUpper :
      Tendsto (fun M : ℕ => ∫ x in (N : ℝ)..(M : ℝ), bifrLogPowerTailTerm a x)
        atTop
        (𝓝 ((N : ℝ) ^ (1 - a) *
          (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2))) :=
    (tendsto_bifrLogPowerTailIntegral_atTop (a := a) (N := (N : ℝ)) ha_gt hNpos).comp
      tendsto_natCast_atTop_atTop
  constructor
  · exact le_of_tendsto_of_tendsto hIntLower hLowerTail (by
      filter_upwards [eventually_ge_atTop (N + 1)] with M hM
      exact bifrLogPowerTailIntegralLower_le_partial (a := a) (N := N + 1) (M := M)
        hM ha (by omega))
  · exact le_of_tendsto_of_tendsto hUpperTail hIntUpper (by
      filter_upwards [eventually_ge_atTop N] with M hM
      exact bifrShiftedLogPowerTailPartial_le_integralUpper (a := a) (N := N) (M := M)
        hM ha hN)

/-- Source bounds for the canonical log-power tail series value used by
`-ζ'(a)`.

This removes the external finite-tail convergence/identification hypothesis
from the zeta-prime source row.  The remaining non-kernel obligation for that
row is numerical enclosure of the finite sums and closed-form tail endpoints. -/
theorem bifrLogPowerTailSourceBounds_tsum_tail
    {a : ℝ} {N : ℕ} (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N) :
    ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
        (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2) ≤
        ((∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) -
          ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)) ∧
      ((∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) -
          ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)) ≤
        (N : ℝ) ^ (1 - a) *
          (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2) := by
  let tail :=
    ((∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) -
      ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ))
  have hLowerTail :
      Tendsto (fun M : ℕ => bifrLogPowerTailPartial a (N + 1) M) atTop (𝓝 tail) := by
    simpa [tail] using tendsto_bifrLogPowerTailPartial_atTop_of_three_halves_le
      (a := a) ha (N + 1)
  have hUpperTail :
      Tendsto (fun M : ℕ => bifrShiftedLogPowerTailPartial a N M) atTop (𝓝 tail) := by
    have hlim := tendsto_bifrShiftedLogPowerTailPartial_atTop_of_three_halves_le
      (a := a) ha N
    have htail_eq :
        ((∑' i : ℕ, bifrLogPowerTailTerm a (((i + 1 : ℕ) : ℝ))) -
          ∑ i ∈ Finset.range N, bifrLogPowerTailTerm a (((i + 1 : ℕ) : ℝ))) =
            tail := by
      dsimp [tail]
      exact tsum_shiftedTail_eq_tsumTail_succ
        (f := fun i : ℕ => bifrLogPowerTailTerm a (i : ℝ))
        (summable_bifrLogPowerTailTerm_of_three_halves_le (a := a) ha) N
    rwa [htail_eq] at hlim
  exact bifrLogPowerTailSourceBounds_of_partial_tendsto
    (a := a) (tail := tail) (N := N) ha hN hLowerTail hUpperTail

/-- Source interval for the canonical log-power primitive from a finite-prefix
enclosure.

This is the zeta-prime analogue of
`bifrPowerTailTsum_sourceInterval_of_finite_bounds`.  The full `tsum` here is
the positive series for `-ζ'(a)`; sign reversal for a stored `ζ'(a)` interval is
left to the numerical/certificate layer. -/
theorem bifrLogPowerTailTsum_sourceInterval_of_finite_bounds
    {a finiteLo finiteHi : ℝ} {N : ℕ}
    (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ))
    (hfiniteHi :
      (∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)) ≤ finiteHi) :
    finiteLo + ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
        (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2) ≤
        (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
        finiteHi + (N : ℝ) ^ (1 - a) *
          (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2) := by
  let finite := ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)
  let tail := (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) - finite
  have htail := bifrLogPowerTailSourceBounds_tsum_tail (a := a) (N := N) ha hN
  have hsum : finite + tail = (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) := by
    dsimp [tail]
    ring
  have hinterval :=
    add_interval_bounds_of_bounds
      (finite := finite) (tail := tail)
      (finiteLo := finiteLo) (finiteHi := finiteHi)
      (tailLo := ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
        (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2))
      (tailHi := (N : ℝ) ^ (1 - a) *
        (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2))
      hfiniteLo hfiniteHi htail.1 htail.2
  constructor
  · simpa [hsum] using hinterval.1
  · simpa [hsum] using hinterval.2

/-- Source interval for the canonical log-power primitive from the natural
finite prefix `m=2,\ldots,N`.

This is the zeta-prime counterpart of
`bifrPowerTailTsum_sourceInterval_of_Icc_finite_bounds`: certificates can
record the usual positive finite prefix for `-ζ'(a)` directly. -/
theorem bifrLogPowerTailTsum_sourceInterval_of_Icc_finite_bounds
    {a finiteLo finiteHi : ℝ} {N : ℕ}
    (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ))
    (hfiniteHi :
      (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ)) ≤ finiteHi) :
    finiteLo + ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
        (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2) ≤
        (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
        finiteHi + (N : ℝ) ^ (1 - a) *
          (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2) := by
  have hprefix := bifrLogPowerTailFinitePrefix_range_eq_Icc a N
  exact bifrLogPowerTailTsum_sourceInterval_of_finite_bounds
    (a := a) (N := N) ha hN
    (by simpa [hprefix] using hfiniteLo)
    (by simpa [hprefix] using hfiniteHi)

/-- Full positive log-power source interval over an exponent box.

This is the endpoint-reduced source wrapper for the positive series
representing `-ζ'(a)`. -/
theorem bifrLogPowerTailTsum_sourceInterval_of_Icc_exponent_bounds
    {a lo hi : ℝ} {N : ℕ}
    (hlo_ge : (3 / 2 : ℝ) ≤ lo) (hN : 2 ≤ N)
    (hlo : lo ≤ a) (hhi : a ≤ hi) :
    (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm hi (i : ℝ)) +
        bifrLogPowerTailEndpoint hi (((N + 1 : ℕ) : ℝ)) ≤
        (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
        (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm lo (i : ℝ)) +
          bifrLogPowerTailEndpoint lo (N : ℝ) := by
  have ha : (3 / 2 : ℝ) ≤ a := hlo_ge.trans hlo
  have hlo_gt : 1 < lo := by linarith
  have hprefix :=
    bifrLogPowerTailFinitePrefix_Icc_exponent_interval
      (a := a) (lo := lo) (hi := hi) (N := N) hlo hhi
  have hsource :=
    bifrLogPowerTailTsum_sourceInterval_of_Icc_finite_bounds
      (a := a) (N := N) ha hN hprefix.1 hprefix.2
  have hN1 : 1 ≤ (((N + 1 : ℕ) : ℝ)) := by exact_mod_cast Nat.succ_pos N
  have hNge : 1 ≤ (N : ℝ) := by
    exact_mod_cast (le_trans (by norm_num : 1 ≤ 2) hN)
  have htailLower :=
    (bifrLogPowerTailEndpoint_exponent_interval
      (a := a) (lo := lo) (hi := hi) (N := (((N + 1 : ℕ) : ℝ)))
      hN1 hlo_gt hlo hhi).1
  have htailUpper :=
    (bifrLogPowerTailEndpoint_exponent_interval
      (a := a) (lo := lo) (hi := hi) (N := (N : ℝ))
      hNge hlo_gt hlo hhi).2
  unfold bifrLogPowerTailEndpoint at htailLower htailUpper
  unfold bifrLogPowerTailEndpoint
  constructor
  · linarith
  · linarith

/-- Certificate-facing positive log-power source interval over an exponent box.

This is the final scalar consumer for the positive `-ζ'` source row: a
certificate may provide outward-rounded lower/upper bounds for the
endpoint-prefix sums and endpoint-tail values, and Lean composes them into a
source interval for the full positive `tsum`. -/
theorem bifrLogPowerTailTsum_sourceInterval_of_endpoint_interval_bounds
    {a lo hi finiteLo finiteHi tailLo tailHi : ℝ} {N : ℕ}
    (hlo_ge : (3 / 2 : ℝ) ≤ lo) (hN : 2 ≤ N)
    (hlo : lo ≤ a) (hhi : a ≤ hi)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm hi (i : ℝ))
    (htailLo :
      tailLo ≤ bifrLogPowerTailEndpoint hi (((N + 1 : ℕ) : ℝ)))
    (hfiniteHi :
      (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm lo (i : ℝ)) ≤ finiteHi)
    (htailHi :
      bifrLogPowerTailEndpoint lo (N : ℝ) ≤ tailHi) :
    finiteLo + tailLo ≤
        (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      (∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
        finiteHi + tailHi := by
  have hsource :=
    bifrLogPowerTailTsum_sourceInterval_of_Icc_exponent_bounds
      (a := a) (lo := lo) (hi := hi) (N := N) hlo_ge hN hlo hhi
  constructor <;> linarith

/-- Signed source interval for the zeta-prime primitive.

The log-power `tsum` source formula bounds the positive series for
`-\zeta'(a)`.  This theorem adds the final sign reversal, so a certificate that
encloses the finite positive prefix can obtain a Lean-backed interval for the
signed primitive `\zeta'(a)` as `-tsum`. -/
theorem bifrZetaPrimeSignedSourceInterval_of_finite_bounds
    {a finiteLo finiteHi : ℝ} {N : ℕ}
    (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ))
    (hfiniteHi :
      (∑ i ∈ Finset.range (N + 1), bifrLogPowerTailTerm a (i : ℝ)) ≤ finiteHi) :
    -(finiteHi + (N : ℝ) ^ (1 - a) *
          (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2)) ≤
        -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
      -(finiteLo + ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
        (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2)) := by
  have hpos :=
    bifrLogPowerTailTsum_sourceInterval_of_finite_bounds
      (a := a) (N := N) ha hN hfiniteLo hfiniteHi
  exact neg_interval_bounds_of_bounds hpos.1 hpos.2

/-- Signed source interval for the zeta-prime primitive from the natural
`m=2,\ldots,N` finite prefix. -/
theorem bifrZetaPrimeSignedSourceInterval_of_Icc_finite_bounds
    {a finiteLo finiteHi : ℝ} {N : ℕ}
    (ha : (3 / 2 : ℝ) ≤ a) (hN : 2 ≤ N)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ))
    (hfiniteHi :
      (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm a (i : ℝ)) ≤ finiteHi) :
    -(finiteHi + (N : ℝ) ^ (1 - a) *
          (Real.log (N : ℝ) / (a - 1) + 1 / (a - 1) ^ 2)) ≤
        -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
        -(finiteLo + ((N + 1 : ℕ) : ℝ) ^ (1 - a) *
          (Real.log (((N + 1 : ℕ) : ℝ)) / (a - 1) + 1 / (a - 1) ^ 2)) := by
  have hpos :=
    bifrLogPowerTailTsum_sourceInterval_of_Icc_finite_bounds
      (a := a) (N := N) ha hN hfiniteLo hfiniteHi
  exact neg_interval_bounds_of_bounds hpos.1 hpos.2

/-- Signed zeta-prime source interval over an exponent box.

The positive log-power source theorem bounds `-ζ'(a)` by endpoint-prefix sums
and endpoint tails.  This theorem performs the final sign reversal for the
stored signed primitive. -/
theorem bifrZetaPrimeSignedSourceInterval_of_Icc_exponent_bounds
    {a lo hi : ℝ} {N : ℕ}
    (hlo_ge : (3 / 2 : ℝ) ≤ lo) (hN : 2 ≤ N)
    (hlo : lo ≤ a) (hhi : a ≤ hi) :
    -((∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm lo (i : ℝ)) +
          bifrLogPowerTailEndpoint lo (N : ℝ)) ≤
        -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤
        -((∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm hi (i : ℝ)) +
          bifrLogPowerTailEndpoint hi (((N + 1 : ℕ) : ℝ))) := by
  have hpos :=
    bifrLogPowerTailTsum_sourceInterval_of_Icc_exponent_bounds
      (a := a) (lo := lo) (hi := hi) (N := N) hlo_ge hN hlo hhi
  exact neg_interval_bounds_of_bounds hpos.1 hpos.2

/-- Certificate-facing signed zeta-prime source interval over an exponent box.

This wraps the positive log-power endpoint certificate and applies the sign
reversal needed for the stored signed primitive.  Certificates can therefore
store separate outward-rounded positive-source bounds and signed primitive
bounds without redoing the finite-sum/integral-tail argument. -/
theorem bifrZetaPrimeSignedSourceInterval_of_endpoint_interval_bounds
    {a lo hi finiteLo finiteHi tailLo tailHi signedLo signedHi : ℝ} {N : ℕ}
    (hlo_ge : (3 / 2 : ℝ) ≤ lo) (hN : 2 ≤ N)
    (hlo : lo ≤ a) (hhi : a ≤ hi)
    (hfiniteLo :
      finiteLo ≤ ∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm hi (i : ℝ))
    (htailLo :
      tailLo ≤ bifrLogPowerTailEndpoint hi (((N + 1 : ℕ) : ℝ)))
    (hfiniteHi :
      (∑ i ∈ Finset.Icc 2 N, bifrLogPowerTailTerm lo (i : ℝ)) ≤ finiteHi)
    (htailHi :
      bifrLogPowerTailEndpoint lo (N : ℝ) ≤ tailHi)
    (hsignedLo : signedLo ≤ -(finiteHi + tailHi))
    (hsignedHi : -(finiteLo + tailLo) ≤ signedHi) :
    signedLo ≤ -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ∧
      -(∑' i : ℕ, bifrLogPowerTailTerm a (i : ℝ)) ≤ signedHi := by
  have hpos :=
    bifrLogPowerTailTsum_sourceInterval_of_endpoint_interval_bounds
      (a := a) (lo := lo) (hi := hi) (N := N)
      hlo_ge hN hlo hhi hfiniteLo htailLo hfiniteHi htailHi
  have hneg := neg_interval_bounds_of_bounds hpos.1 hpos.2
  constructor <;> linarith


/-- Numeric power bound used in the `p ≥ 3` beta-branch proof. -/
theorem bifr_three_halves_rpow_quarter_le_six_fifths :
    (3 / 2 : ℝ) ^ ((1 : ℝ) / 4) ≤ 6 / 5 := by
  have hnonneg_left : 0 ≤ (3 / 2 : ℝ) ^ ((1 : ℝ) / 4) :=
    Real.rpow_nonneg (by norm_num) _
  have hnonneg_right : 0 ≤ (6 / 5 : ℝ) := by norm_num
  rw [← Real.rpow_le_rpow_iff hnonneg_left hnonneg_right
    (by norm_num : (0 : ℝ) < 4)]
  have hleft : ((3 / 2 : ℝ) ^ ((1 : ℝ) / 4)) ^ (4 : ℝ) = 3 / 2 := by
    rw [← Real.rpow_mul (by norm_num : (0 : ℝ) ≤ (3 / 2 : ℝ))]
    norm_num
  rw [hleft]
  norm_num

/-- Numeric logarithm lower bound used in the `p ≥ 3` beta-branch proof. -/
theorem bifr_four_log_three_halves_ge_eight_fifths :
    (8 / 5 : ℝ) ≤ 4 * Real.log (3 / 2) := by
  have h := Real.le_log_one_add_of_nonneg (x := (1 / 2 : ℝ)) (by norm_num)
  norm_num at h ⊢
  nlinarith

/-- Numeric power bound used in the `p = 2` beta-branch proof. -/
theorem bifr_two_rpow_fifth_le_twenty_three_twentieths :
    (2 : ℝ) ^ ((1 : ℝ) / 5) ≤ 23 / 20 := by
  have hnonneg_left : 0 ≤ (2 : ℝ) ^ ((1 : ℝ) / 5) :=
    Real.rpow_nonneg (by norm_num) _
  have hnonneg_right : 0 ≤ (23 / 20 : ℝ) := by norm_num
  rw [← Real.rpow_le_rpow_iff hnonneg_left hnonneg_right
    (by norm_num : (0 : ℝ) < 5)]
  have hleft : ((2 : ℝ) ^ ((1 : ℝ) / 5)) ^ (5 : ℝ) = 2 := by
    rw [← Real.rpow_mul (by norm_num : (0 : ℝ) ≤ 2)]
    norm_num
  rw [hleft]
  norm_num

/-- Numeric logarithm lower bound used in the `p = 2` beta-branch proof. -/
theorem bifr_four_log_four_thirds_ge_twenty_three_twentieths :
    (23 / 20 : ℝ) ≤ 4 * Real.log (4 / 3) := by
  have h := Real.sum_range_le_log_div (x := (1 / 7 : ℝ))
    (by norm_num) (by norm_num) 2
  norm_num at h ⊢
  nlinarith

/-- Beta second-branch comparison inequality for the `p ≥ 3` case.

Under the low-bandwidth condition `p ≤ s/4`, this proves the scalar
inequality equivalent to the second branch of the paper's beta minimum being
no larger than the first branch:
\[
  \left(\frac{p}{p-1}\right)^{p/s}
  \le 4\log\frac{2p}{p+1}.
\]
This closes the non-numeric part of the beta branch proof in Lean for real
`p`; integer instantiations with `p ≥ 3` can use it directly after casting. -/
theorem bifrBetaSecondBranchLogIneq_of_three_le
    {p s : ℝ}
    (hp3 : 3 ≤ p) (hs : 0 < s) (hp_le : p ≤ s / 4) :
    (p / (p - 1)) ^ (p / s) ≤ 4 * Real.log (2 * p / (p + 1)) := by
  have hp_pos : 0 < p := by linarith
  have hden_pos : 0 < p - 1 := by linarith
  have hbase_nonneg : 0 ≤ p / (p - 1) := div_nonneg hp_pos.le hden_pos.le
  have hbase_le : p / (p - 1) ≤ (3 / 2 : ℝ) := by
    rw [div_le_iff₀ hden_pos]
    nlinarith
  have hexp_nonneg : 0 ≤ p / s := div_nonneg hp_pos.le hs.le
  have hleft_le_base :
      (p / (p - 1)) ^ (p / s) ≤ (3 / 2 : ℝ) ^ (p / s) :=
    Real.rpow_le_rpow hbase_nonneg hbase_le hexp_nonneg
  have hexp_le : p / s ≤ (1 : ℝ) / 4 := by
    rw [div_le_iff₀ hs]
    linarith
  have hbase_exp_le :
      (3 / 2 : ℝ) ^ (p / s) ≤ (3 / 2 : ℝ) ^ ((1 : ℝ) / 4) :=
    Real.rpow_le_rpow_of_exponent_le (by norm_num) hexp_le
  have hleft_le_log32 :
      (p / (p - 1)) ^ (p / s) ≤ 4 * Real.log (3 / 2) := by
    calc
      (p / (p - 1)) ^ (p / s) ≤ (3 / 2 : ℝ) ^ (p / s) := hleft_le_base
      _ ≤ (3 / 2 : ℝ) ^ ((1 : ℝ) / 4) := hbase_exp_le
      _ ≤ 6 / 5 := bifr_three_halves_rpow_quarter_le_six_fifths
      _ ≤ 8 / 5 := by norm_num
      _ ≤ 4 * Real.log (3 / 2) := bifr_four_log_three_halves_ge_eight_fifths
  have harg_le : (3 / 2 : ℝ) ≤ 2 * p / (p + 1) := by
    have hden2 : 0 < p + 1 := by linarith
    rw [le_div_iff₀ hden2]
    nlinarith
  have hlog_le : 4 * Real.log (3 / 2) ≤ 4 * Real.log (2 * p / (p + 1)) := by
    have hlog := Real.log_le_log (by norm_num : (0 : ℝ) < 3 / 2) harg_le
    nlinarith
  exact hleft_le_log32.trans hlog_le

/-- Beta second-branch comparison inequality for the boundary case `p = 2`.

The natural-language proof uses `n ≥ 128`; this scalar Lean version uses the
slightly cleaner sufficient condition `10 ≤ s`, which is implied by
`s = sqrt n` and `n ≥ 128`. -/
theorem bifrBetaSecondBranchLogIneq_of_p_eq_two
    {s : ℝ} (hs : 10 ≤ s) :
    (2 : ℝ) ^ (2 / s) ≤ 4 * Real.log (4 / 3) := by
  have hs_pos : 0 < s := by linarith
  have hexp_le : (2 : ℝ) / s ≤ (1 : ℝ) / 5 := by
    rw [div_le_iff₀ hs_pos]
    linarith
  have hpow_le : (2 : ℝ) ^ (2 / s) ≤ (2 : ℝ) ^ ((1 : ℝ) / 5) :=
    Real.rpow_le_rpow_of_exponent_le (by norm_num) hexp_le
  calc
    (2 : ℝ) ^ (2 / s) ≤ (2 : ℝ) ^ ((1 : ℝ) / 5) := hpow_le
    _ ≤ 23 / 20 := bifr_two_rpow_fifth_le_twenty_three_twentieths
    _ ≤ 4 * Real.log (4 / 3) :=
      bifr_four_log_four_thirds_ge_twenty_three_twentieths

/-- Source-formula theorem for the power factor in the bounded-cross model. -/
theorem hasDerivAt_bifrCrossPower
    {s η : ℝ} (hs : 0 < s) :
    HasDerivAt (fun η => bifrCrossPower s η)
      (-2 * bifrCrossPower s η * Real.log s) η := by
  unfold bifrCrossPower
  have hg : HasDerivAt (fun η : ℝ => 1 - 2 * η) (-2) η := by
    simpa using
      (hasDerivAt_const η (1 : ℝ)).sub
        ((hasDerivAt_const η (2 : ℝ)).mul (hasDerivAt_id η))
  have h := hg.const_rpow hs
  convert h using 1
  ring

/-- Mean-value bridge from a pointwise derivative bound on an interval to a
finite-step absolute bound.

This is the scalar tool needed to turn coefficient and power derivative bounds
into adjacent-step bounds for the bounded-cross model. -/
theorem abs_sub_le_of_hasDerivAt_bound_on_Icc
    {f f' : ℝ → ℝ} {a b C x y : ℝ}
    (hderiv : ∀ z ∈ Set.Icc a b, HasDerivAt f (f' z) z)
    (hbound : ∀ z ∈ Set.Icc a b, |f' z| ≤ C)
    (hx : x ∈ Set.Icc a b) (hy : y ∈ Set.Icc a b) :
    |f y - f x| ≤ C * |y - x| := by
  have hf : ∀ z ∈ Set.Icc a b, DifferentiableAt ℝ f z := by
    intro z hz
    exact (hderiv z hz).differentiableAt
  have hb : ∀ z ∈ Set.Icc a b, ‖deriv f z‖ ≤ C := by
    intro z hz
    rw [(hderiv z hz).deriv]
    simpa [Real.norm_eq_abs] using hbound z hz
  have h :=
    Convex.norm_image_sub_le_of_norm_deriv_le hf hb (convex_Icc a b) hx hy
  simpa [Real.norm_eq_abs] using h

/-- Mean-value bridge specialized to the BIFR bounded-cross power factor. -/
theorem abs_bifrCrossPower_sub_le_of_deriv_bound_on_Icc
    {s a b C x y : ℝ}
    (hs : 0 < s)
    (hbound :
      ∀ z ∈ Set.Icc a b, |-2 * bifrCrossPower s z * Real.log s| ≤ C)
    (hx : x ∈ Set.Icc a b) (hy : y ∈ Set.Icc a b) :
    |bifrCrossPower s y - bifrCrossPower s x| ≤ C * |y - x| :=
  abs_sub_le_of_hasDerivAt_bound_on_Icc
    (fun z _ => hasDerivAt_bifrCrossPower (η := z) hs) hbound hx hy

/-- On the restricted interval, the absolute power factor is at most
`s^(7/8)` for `s ≥ 1`. -/
theorem abs_bifrCrossPower_le_seven_eighth
    {s η : ℝ} (hs : 1 ≤ s)
    (hη : η ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)) :
    |bifrCrossPower s η| ≤ s ^ ((7 : ℝ) / 8) := by
  unfold bifrCrossPower
  have hs_nonneg : 0 ≤ s := le_trans (by norm_num) hs
  have hexp : 1 - 2 * η ≤ (7 : ℝ) / 8 := by linarith [hη.1]
  have hpow := Real.rpow_le_rpow_of_exponent_le hs hexp
  rw [abs_of_nonneg (Real.rpow_nonneg hs_nonneg _)]
  exact hpow

/-- Derivative-size bound for the bounded-cross power factor on the restricted
interval. -/
theorem abs_bifrCrossPower_deriv_le_restricted
    {s η : ℝ} (hs : 1 ≤ s)
    (hη : η ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)) :
    |-2 * bifrCrossPower s η * Real.log s| ≤
      2 * s ^ ((7 : ℝ) / 8) * Real.log s := by
  have hpower := abs_bifrCrossPower_le_seven_eighth hs hη
  have hlog : 0 ≤ Real.log s := Real.log_nonneg hs
  calc
    |-2 * bifrCrossPower s η * Real.log s|
        = 2 * |bifrCrossPower s η| * Real.log s := by
          rw [abs_mul, abs_mul, abs_of_nonneg hlog]
          norm_num
    _ ≤ 2 * s ^ ((7 : ℝ) / 8) * Real.log s := by
          gcongr

/-- Concrete adjacent-step bound for the bounded-cross power factor.

If `s ≥ 1`, both normalized endpoints lie in `[1/16,1/4]`, and the step is at
most `1/s`, then the power-factor variation is bounded by the residual scale.
This is the power-step half of the intended `16 + 16 = 32` bounded-cross model
budget. -/
theorem abs_bifrCrossPower_sub_le_two_residualScale
    {s ηp ηq : ℝ} (hs : 1 ≤ s)
    (hp : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hq : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s) :
    |bifrCrossPower s ηq - bifrCrossPower s ηp| ≤
      2 * bifrRestrictedResidualScale s := by
  have hs_pos : 0 < s := lt_of_lt_of_le zero_lt_one hs
  have hs_nonneg : 0 ≤ s := le_of_lt hs_pos
  have hmv :=
    abs_bifrCrossPower_sub_le_of_deriv_bound_on_Icc
      (s := s) (a := (1 / 16 : ℝ)) (b := (1 / 4 : ℝ))
      (C := 2 * s ^ ((7 : ℝ) / 8) * Real.log s)
      hs_pos
      (fun z hz => abs_bifrCrossPower_deriv_le_restricted hs hz)
      hp hq
  have hmult_nonneg : 0 ≤ 2 * s ^ ((7 : ℝ) / 8) * Real.log s := by
    exact mul_nonneg (mul_nonneg (by norm_num) (Real.rpow_nonneg hs_nonneg _))
      (Real.log_nonneg hs)
  have hstep_bound :
      (2 * s ^ ((7 : ℝ) / 8) * Real.log s) * |ηq - ηp| ≤
        (2 * s ^ ((7 : ℝ) / 8) * Real.log s) * (1 / s) :=
    mul_le_mul_of_nonneg_left hstep hmult_nonneg
  calc
    |bifrCrossPower s ηq - bifrCrossPower s ηp|
        ≤ (2 * s ^ ((7 : ℝ) / 8) * Real.log s) * |ηq - ηp| := hmv
    _ ≤ (2 * s ^ ((7 : ℝ) / 8) * Real.log s) * (1 / s) := hstep_bound
    _ = 2 * bifrRestrictedResidualScale s := by
      unfold bifrRestrictedResidualScale
      rw [one_div, ← Real.rpow_neg_one]
      calc
        2 * s ^ (7 / 8 : ℝ) * Real.log s * s ^ (-1 : ℝ)
            = 2 * ((s ^ (7 / 8 : ℝ) * s ^ (-1 : ℝ)) * Real.log s) := by
              ring
        _ = 2 * (s ^ ((7 / 8 : ℝ) + (-1 : ℝ)) * Real.log s) := by
              rw [Real.rpow_add hs_pos]
        _ = 2 * (s ^ (-(1 : ℝ) / 8) * Real.log s) := by
              ring_nf

/-- Coefficient-step contribution under a pointwise derivative bound.

This is the scalar bridge for the dominant bounded-cross coefficient `D(η)`.
If `|D'| ≤ C` on the interval and the destination power weight is at most `W`,
then the coefficient-change contribution is at most
`(C * W) * |η_q - η_p|`. -/
theorem abs_coeff_step_times_weight_le_of_deriv_bound_on_Icc
    {D D' : ℝ → ℝ} {a b C W ηp ηq wq : ℝ}
    (hderiv : ∀ z ∈ Set.Icc a b, HasDerivAt D (D' z) z)
    (hbound : ∀ z ∈ Set.Icc a b, |D' z| ≤ C)
    (hp : ηp ∈ Set.Icc a b) (hq : ηq ∈ Set.Icc a b)
    (hweight : |wq| ≤ W) :
    |D ηq - D ηp| * |wq| ≤ (C * W) * |ηq - ηp| := by
  have hmv :
      |D ηq - D ηp| ≤ C * |ηq - ηp| :=
    abs_sub_le_of_hasDerivAt_bound_on_Icc hderiv hbound hp hq
  calc
    |D ηq - D ηp| * |wq| ≤ (C * |ηq - ηp|) * W := by
      exact mul_le_mul hmv hweight (abs_nonneg _)
        (le_trans (abs_nonneg _) hmv)
    _ = (C * W) * |ηq - ηp| := by ring

/-- Concrete coefficient-step contribution bound for the restricted
bounded-cross residual model.

The logarithmic cutoff assumption `1 ≤ log s` is the asymptotic-side condition
used to absorb the non-logarithmic coefficient step into the residual scale
`s^(-1/8) log s`. -/
theorem abs_coeff_step_times_weight_le_residualScale
    {D D' : ℝ → ℝ} {s ηp ηq wq : ℝ}
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hbound : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hp : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hq : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hweight : |wq| ≤ s ^ ((7 : ℝ) / 8)) :
    |D ηq - D ηp| * |wq| ≤ 16 * bifrRestrictedResidualScale s := by
  have hs_pos : 0 < s := lt_of_lt_of_le zero_lt_one hs
  have hcoeff :
      |D ηq - D ηp| * |wq| ≤
        (16 * s ^ ((7 : ℝ) / 8)) * |ηq - ηp| := by
    exact
      abs_coeff_step_times_weight_le_of_deriv_bound_on_Icc
        hderiv hbound hp hq hweight
  have hmult_nonneg : 0 ≤ 16 * s ^ ((7 : ℝ) / 8) := by positivity
  have hto_nolog :
      (16 * s ^ ((7 : ℝ) / 8)) * (1 / s) =
        16 * s ^ (-(1 : ℝ) / 8) := by
    rw [one_div, ← Real.rpow_neg_one]
    calc
      16 * s ^ (7 / 8 : ℝ) * s ^ (-1 : ℝ)
          = 16 * (s ^ (7 / 8 : ℝ) * s ^ (-1 : ℝ)) := by ring
      _ = 16 * s ^ ((7 / 8 : ℝ) + (-1 : ℝ)) := by
            rw [Real.rpow_add hs_pos]
      _ = 16 * s ^ (-(1 : ℝ) / 8) := by ring_nf
  calc
    |D ηq - D ηp| * |wq|
        ≤ (16 * s ^ ((7 : ℝ) / 8)) * |ηq - ηp| := hcoeff
    _ ≤ (16 * s ^ ((7 : ℝ) / 8)) * (1 / s) :=
        mul_le_mul_of_nonneg_left hstep hmult_nonneg
    _ = 16 * s ^ (-(1 : ℝ) / 8) := hto_nolog
    _ ≤ 16 * bifrRestrictedResidualScale s := by
      unfold bifrRestrictedResidualScale
      have hnonneg : 0 ≤ 16 * s ^ (-(1 : ℝ) / 8) := by positivity
      calc
        16 * s ^ (-(1 : ℝ) / 8)
            = (16 * s ^ (-(1 : ℝ) / 8)) * 1 := by ring
        _ ≤ (16 * s ^ (-(1 : ℝ) / 8)) * Real.log s :=
            mul_le_mul_of_nonneg_left hlog hnonneg
        _ = 16 * (s ^ (-(1 : ℝ) / 8) * Real.log s) := by ring

/-- Scalar data for the squared uncollapsed finite-`p` envelope.

`A`, `B`, and `L` stand for the uncollapsed paper bounds
`Rbar^2 / n`, `Sbar_2^2`, and `Sbar_1^2`.  `sep` is the separation term
`b(p)` used in the `ell_1 / b` contribution. -/
structure BIFRUncollapsedEnvelopeFamily where
  A : ℕ → ℝ
  B : ℕ → ℝ
  L : ℕ → ℝ
  sep : ℕ → ℝ

namespace BIFRUncollapsedEnvelopeFamily

/-- Squared single-participation envelope component `A_p * B_p`. -/
def singleSq (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) : ℝ :=
  env.A p * env.B p

/-- Squared `ell_1 / b` envelope component `A_p * L_p / b(p)`. -/
def l1OverBSq (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) : ℝ :=
  env.A p * env.L p / env.sep p

/-- Squared combined multi-participation envelope without the harmless scalar
factor `k`: `A_p * (B_p + L_p / b(p))`. -/
def multiSq (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) : ℝ :=
  env.singleSq p + env.l1OverBSq p

@[simp] theorem multiSq_eq
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) :
    env.multiSq p = env.singleSq p + env.l1OverBSq p := rfl

/-- Finite-side certificate for the restricted adjacent single-component drop.

The large-horizon residual bridge closes the case `2^(253/2) ≤ s`.  This
record is the theorem-facing shape of the complementary finite interval
certificate below that cutoff: the certificate must both live below the cutoff
and prove the adjacent strict drop for the concrete single-participation
component. -/
structure RestrictedFiniteSingleDropCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) (s : ℝ) : Prop where
  belowCutoff : s < (2 : ℝ) ^ ((253 : ℝ) / 2)
  singleDrop : env.singleSq (p + 1) < env.singleSq p

/-- Finite-side certificate for the practical combined `b=p` adjacent drop.

This is the finite-interval import surface for the Route B theorem contract.
The large-horizon branch is intended to use the combined leading coefficient
and residual bridge; below the cutoff, a future finite interval certificate
must prove the strict adjacent drop for the combined envelope directly. -/
structure RestrictedFiniteMultiDropCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) (s : ℝ) : Prop where
  belowCutoff : s < (2 : ℝ) ^ ((253 : ℝ) / 2)
  multiDrop : env.multiSq (p + 1) < env.multiSq p

/-- Build a finite-side certificate from a checked positive lower bound on the
single-component delta.

This is the scalar Lean counterpart of a finite interval row whose checker
certifies
`0 < lower ≤ singleSq p - singleSq (p+1)`.  It deliberately says nothing about
how the lower bound was obtained; interval-box soundness remains the finite
certificate's responsibility. -/
theorem RestrictedFiniteSingleDropCertificate.of_delta_lower_bound
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {s lower : ℝ}
    (hbelow : s < (2 : ℝ) ^ ((253 : ℝ) / 2))
    (hlower_pos : 0 < lower)
    (hlower_le : lower ≤ env.singleSq p - env.singleSq (p + 1)) :
    RestrictedFiniteSingleDropCertificate env p s := by
  refine ⟨hbelow, ?_⟩
  linarith

/-- Build a finite-side combined certificate from a checked positive lower
bound on the combined-envelope delta. -/
theorem RestrictedFiniteMultiDropCertificate.of_delta_lower_bound
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {s lower : ℝ}
    (hbelow : s < (2 : ℝ) ^ ((253 : ℝ) / 2))
    (hlower_pos : 0 < lower)
    (hlower_le : lower ≤ env.multiSq p - env.multiSq (p + 1)) :
    RestrictedFiniteMultiDropCertificate env p s := by
  refine ⟨hbelow, ?_⟩
  linarith

/-- Finite-side certificate for a whole integer range of adjacent transitions.

The final below-cutoff proof is expected to be box- or range-based rather than
one point at a time.  This record is the Lean import shape for such a finite
certificate: for every integer `p` in `[pLo,pHi]`, the certificate supplies the
strict adjacent single-component drop. -/
structure RestrictedFiniteSingleDropIntervalCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (pLo pHi : ℕ) (s : ℝ) : Prop where
  belowCutoff : s < (2 : ℝ) ^ ((253 : ℝ) / 2)
  singleDropOfMem :
    ∀ p, pLo ≤ p → p ≤ pHi → env.singleSq (p + 1) < env.singleSq p

/-- Build a finite interval certificate from checked positive lower bounds
for every integer transition in the interval.

This is the range analogue of
`RestrictedFiniteSingleDropCertificate.of_delta_lower_bound`.  The proof of the
lower bounds still belongs to the finite interval certificate/checker; this
theorem is only the scalar Lean import surface. -/
theorem RestrictedFiniteSingleDropIntervalCertificate.of_pointwise_lower_bound
    (env : BIFRUncollapsedEnvelopeFamily) {pLo pHi : ℕ} {s : ℝ}
    {lower : ℕ → ℝ}
    (hbelow : s < (2 : ℝ) ^ ((253 : ℝ) / 2))
    (hlower_pos :
      ∀ p, pLo ≤ p → p ≤ pHi → 0 < lower p)
    (hlower_le :
      ∀ p, pLo ≤ p → p ≤ pHi →
        lower p ≤ env.singleSq p - env.singleSq (p + 1)) :
    RestrictedFiniteSingleDropIntervalCertificate env pLo pHi s := by
  refine ⟨hbelow, ?_⟩
  intro p hpLo hpHi
  have hpos := hlower_pos p hpLo hpHi
  have hle := hlower_le p hpLo hpHi
  linarith

/-- Extract a point certificate from a finite interval certificate. -/
theorem RestrictedFiniteSingleDropIntervalCertificate.to_point_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {pLo pHi p : ℕ} {s : ℝ}
    (cert : RestrictedFiniteSingleDropIntervalCertificate env pLo pHi s)
    (hpLo : pLo ≤ p) (hpHi : p ≤ pHi) :
    RestrictedFiniteSingleDropCertificate env p s :=
  ⟨cert.belowCutoff, cert.singleDropOfMem p hpLo hpHi⟩

/-- Finite-side certificate for a whole integer range of practical combined
`b=p` adjacent transitions. -/
structure RestrictedFiniteMultiDropIntervalCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (pLo pHi : ℕ) (s : ℝ) : Prop where
  belowCutoff : s < (2 : ℝ) ^ ((253 : ℝ) / 2)
  multiDropOfMem :
    ∀ p, pLo ≤ p → p ≤ pHi → env.multiSq (p + 1) < env.multiSq p

/-- Build a finite combined interval certificate from checked positive lower
bounds for every integer transition in the interval. -/
theorem RestrictedFiniteMultiDropIntervalCertificate.of_pointwise_lower_bound
    (env : BIFRUncollapsedEnvelopeFamily) {pLo pHi : ℕ} {s : ℝ}
    {lower : ℕ → ℝ}
    (hbelow : s < (2 : ℝ) ^ ((253 : ℝ) / 2))
    (hlower_pos :
      ∀ p, pLo ≤ p → p ≤ pHi → 0 < lower p)
    (hlower_le :
      ∀ p, pLo ≤ p → p ≤ pHi →
        lower p ≤ env.multiSq p - env.multiSq (p + 1)) :
    RestrictedFiniteMultiDropIntervalCertificate env pLo pHi s := by
  refine ⟨hbelow, ?_⟩
  intro p hpLo hpHi
  have hpos := hlower_pos p hpLo hpHi
  have hle := hlower_le p hpLo hpHi
  linarith

/-- Extract a combined point certificate from a finite interval certificate. -/
theorem RestrictedFiniteMultiDropIntervalCertificate.to_point_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {pLo pHi p : ℕ} {s : ℝ}
    (cert : RestrictedFiniteMultiDropIntervalCertificate env pLo pHi s)
    (hpLo : pLo ≤ p) (hpHi : p ≤ pHi) :
    RestrictedFiniteMultiDropCertificate env p s :=
  ⟨cert.belowCutoff, cert.multiDropOfMem p hpLo hpHi⟩

/-- Component monotonicity immediately gives monotonicity of the combined
uncollapsed envelope.  This is the main wrapper used after proving the single
and `ell_1 / b` components. -/
theorem multiSq_mono_of_components
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hsingle : env.singleSq q ≤ env.singleSq p)
    (hl1 : env.l1OverBSq q ≤ env.l1OverBSq p) :
    env.multiSq q ≤ env.multiSq p := by
  simp [multiSq]
  linarith

/-- Adjacent component drops imply adjacent monotonicity of the combined
envelope. -/
theorem multiSq_adjacent_mono_of_components
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hsingle : env.singleSq (p + 1) ≤ env.singleSq p)
    (hl1 : env.l1OverBSq (p + 1) ≤ env.l1OverBSq p) :
    env.multiSq (p + 1) ≤ env.multiSq p :=
  env.multiSq_mono_of_components hsingle hl1

/-- Dyadic component drops imply dyadic monotonicity of the combined envelope. -/
theorem multiSq_dyadic_mono_of_components
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hsingle : env.singleSq (2 * p) ≤ env.singleSq p)
    (hl1 : env.l1OverBSq (2 * p) ≤ env.l1OverBSq p) :
    env.multiSq (2 * p) ≤ env.multiSq p :=
  env.multiSq_mono_of_components hsingle hl1

/-- Product-level proof seam for the single-participation component.

This is the algebraic form suggested by diagnostics: the sensitivity-envelope
gain must dominate the RMSE-envelope loss.  Instantiating this theorem with
`Ap = A_p`, `Aq = A_q`, `Bp = B_p`, and `Bq = B_q` proves
`A_q * B_q ≤ A_p * B_p`. -/
theorem singleSq_drop_of_gain_dominates_loss
    (Ap Aq Bp Bq : ℝ)
    (hgain :
      Bq * (Aq - Ap) ≤ Ap * (Bp - Bq)) :
    Aq * Bq ≤ Ap * Bp := by
  nlinarith

/-- Scalar residual bridge for the restricted leading-coefficient route.

If a quantity is decomposed as `leading + error` at `p` and `q`, the leading
drop is at least `c0`, and the one-step error changes by at most `c0 / 2`,
then the total quantity strictly drops.  This is the Lean-facing endpoint for
the restricted residual proof note:

`A_p B_p = sqrt(n) C(eta_p) + E_p`.
-/
theorem drop_of_leading_gap_and_residual_bound
    (left right leadingLeft leadingRight errorLeft errorRight c0 : ℝ)
    (hleft : left = leadingLeft + errorLeft)
    (hright : right = leadingRight + errorRight)
    (hleading : c0 ≤ leadingLeft - leadingRight)
    (hresidual : |errorLeft - errorRight| ≤ c0 / 2)
    (hc0 : 0 < c0) :
    right < left := by
  have hresidual_lower : -(c0 / 2) ≤ errorLeft - errorRight := by
    exact neg_le_of_abs_le hresidual
  have hdrop : c0 / 2 ≤ left - right := by
    rw [hleft, hright]
    linarith
  linarith

/-- Adjacent single-participation strict drop from a leading term and a
one-step residual bound. -/
theorem singleSq_adjacent_lt_of_leading_gap_and_residual_bound
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ errorP errorQ c0 : ℝ)
    (hp :
      env.singleSq p = leadingP + errorP)
    (hq :
      env.singleSq (p + 1) = leadingQ + errorQ)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hresidual : |errorP - errorQ| ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.singleSq (p + 1) < env.singleSq p :=
  drop_of_leading_gap_and_residual_bound
    (env.singleSq p) (env.singleSq (p + 1))
    leadingP leadingQ errorP errorQ c0 hp hq hleading hresidual hc0

/-- Adjacent combined-envelope strict drop from a leading term and a one-step
residual bound.

This is the scalar boundary for the practical `b=p` route.  The analytic side
may prove a leading coefficient drop directly for
`A_p * (B_p + L_p / p)` and then supply a one-step residual bound, without
separately proving the single and `ell_1 / b` component drops.  The separation
choice `b=p` is encoded upstream by instantiating `env.sep p = p`; this wrapper
only consumes the resulting combined scalar sequence. -/
theorem multiSq_adjacent_lt_of_leading_gap_and_residual_bound
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ errorP errorQ c0 : ℝ)
    (hp :
      env.multiSq p = leadingP + errorP)
    (hq :
      env.multiSq (p + 1) = leadingQ + errorQ)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hresidual : |errorP - errorQ| ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.multiSq (p + 1) < env.multiSq p :=
  drop_of_leading_gap_and_residual_bound
    (env.multiSq p) (env.multiSq (p + 1))
    leadingP leadingQ errorP errorQ c0 hp hq hleading hresidual hc0

/-- Adjacent combined-envelope strict drop from a leading gap and signed
residual monotonicity.

This is the sharper scalar boundary suggested by the current practical
`b=p` diagnostic.  If

`env.multiSq p = leadingP + errorP`,
`env.multiSq (p+1) = leadingQ + errorQ`,

the leading term drops by a positive amount, and the residual does not
increase (`errorQ ≤ errorP`), then the exact combined envelope strictly drops.
No absolute residual scale or large-horizon cutoff is needed at this scalar
layer. -/
theorem multiSq_adjacent_lt_of_leading_gap_and_signed_residual_mono
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ errorP errorQ c0 : ℝ)
    (hp :
      env.multiSq p = leadingP + errorP)
    (hq :
      env.multiSq (p + 1) = leadingQ + errorQ)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hresidual : errorQ ≤ errorP)
    (hc0 : 0 < c0) :
    env.multiSq (p + 1) < env.multiSq p := by
  rw [hp, hq]
  have hlead_pos : 0 < leadingP - leadingQ := lt_of_lt_of_le hc0 hleading
  linarith

/-- Concrete Route B signed-residual bridge with the current leading-gap
normalization `c₀ = 1`. -/
theorem multiSq_adjacent_lt_of_combined_signed_residual_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ errorP errorQ : ℝ)
    (hp : env.multiSq p = leadingP + errorP)
    (hq : env.multiSq (p + 1) = leadingQ + errorQ)
    (hleading : (1 : ℝ) ≤ leadingP - leadingQ)
    (hresidual : errorQ ≤ errorP) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_leading_gap_and_signed_residual_mono
    leadingP leadingQ errorP errorQ 1 hp hq hleading hresidual (by norm_num)

/-- Componentwise signed-residual handoff for the practical combined route.

The current diagnostic records a stronger pattern than combined residual
monotonicity: the sampled residuals for `singleSq` and `l1OverBSq` are each
nonincreasing after subtracting their own leading coefficients.  This theorem
is the scalar consumer for that route.  It combines component decompositions,
a positive total leading gap, and componentwise residual monotonicity into the
strict combined-envelope drop. -/
theorem multiSq_adjacent_lt_of_component_signed_residual_mono
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ c0 : ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      c0 ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hsingleResidual : singleErrorQ ≤ singleErrorP)
    (hl1Residual : l1ErrorQ ≤ l1ErrorP)
    (hc0 : 0 < c0) :
    env.multiSq (p + 1) < env.multiSq p := by
  rw [multiSq, multiSq, hsingleP, hsingleQ, hl1P, hl1Q]
  have hlead_pos :
      0 < (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ) :=
    lt_of_lt_of_le hc0 hleading
  linarith

/-- Concrete componentwise signed-residual bridge with leading gap normalized
to `1`. -/
theorem multiSq_adjacent_lt_of_component_signed_residual_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ : ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hsingleResidual : singleErrorQ ≤ singleErrorP)
    (hl1Residual : l1ErrorQ ≤ l1ErrorP) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_component_signed_residual_mono
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ 1
    hsingleP hsingleQ hl1P hl1Q hleading hsingleResidual hl1Residual
    (by norm_num)

/-- Nonnegativity of a residual delta from a fractional model lower bound.

The current Route B diagnostics suggest a theorem-facing contract of the form
`actualDelta ≥ (999/1000) * modelDelta`: the residual drop may be slightly
smaller than the model drop, but it preserves a fixed positive fraction.  This
scalar lemma isolates the only algebra needed to turn such a certificate plus
model nonnegativity into signed residual monotonicity. -/
theorem residualDelta_nonneg_of_model_fraction_lower
    {actualDelta modelDelta ratio : ℝ}
    (hratio : 0 ≤ ratio)
    (hmodel : 0 ≤ modelDelta)
    (hlower : ratio * modelDelta ≤ actualDelta) :
    0 ≤ actualDelta := by
  exact le_trans (mul_nonneg hratio hmodel) hlower

/-- Concrete `999/1000` version of
`residualDelta_nonneg_of_model_fraction_lower`, matching the maintained Route
B component remainder-budget artifact. -/
theorem residualDelta_nonneg_of_999_1000_model_lower
    {actualDelta modelDelta : ℝ}
    (hmodel : 0 ≤ modelDelta)
    (hlower : ((999 : ℝ) / 1000) * modelDelta ≤ actualDelta) :
    0 ≤ actualDelta :=
  residualDelta_nonneg_of_model_fraction_lower
    (actualDelta := actualDelta) (modelDelta := modelDelta)
    (ratio := (999 : ℝ) / 1000) (by norm_num) hmodel hlower

/-- Componentwise Route B bridge from a generic fractional residual-model
contract.

This is the theorem-facing replacement for tuning-specific hardcoded
fractions.  A relaxed certificate can instantiate `ratio = 99/100`, `1/2`, or
any other nonnegative public constant; the old `999/1000` bridge below remains
as a compatibility wrapper for maintained stress artifacts. -/
theorem multiSq_adjacent_lt_of_component_model_fraction_residual_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (ratio singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
      singleModelDelta l1ModelDelta : ℝ)
    (hratio : 0 ≤ ratio)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hsingleModel : 0 ≤ singleModelDelta)
    (hl1Model : 0 ≤ l1ModelDelta)
    (hsingleLower :
      ratio * singleModelDelta ≤ singleErrorP - singleErrorQ)
    (hl1Lower :
      ratio * l1ModelDelta ≤ l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hsingleDrop :
      0 ≤ singleErrorP - singleErrorQ :=
    residualDelta_nonneg_of_model_fraction_lower
      (actualDelta := singleErrorP - singleErrorQ)
      (modelDelta := singleModelDelta) (ratio := ratio)
      hratio hsingleModel hsingleLower
  have hl1Drop :
      0 ≤ l1ErrorP - l1ErrorQ :=
    residualDelta_nonneg_of_model_fraction_lower
      (actualDelta := l1ErrorP - l1ErrorQ)
      (modelDelta := l1ModelDelta) (ratio := ratio)
      hratio hl1Model hl1Lower
  exact env.multiSq_adjacent_lt_of_component_signed_residual_bridge
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
    hsingleP hsingleQ hl1P hl1Q hleading (by linarith) (by linarith)

/-- Componentwise Route B bridge from the `999/1000` residual-model contract.

This is the current theorem-facing scalar endpoint for the practical
`b=p` route.  The analytic side may prove, for each component residual,
that the actual one-step residual drop covers at least \(999/1000\) of a
nonnegative model drop.  This wrapper converts those two fractional
lower bounds into componentwise signed residual monotonicity and then invokes
the combined-envelope handoff. -/
theorem multiSq_adjacent_lt_of_component_999_1000_model_residual_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
      singleModelDelta l1ModelDelta : ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hsingleModel : 0 ≤ singleModelDelta)
    (hl1Model : 0 ≤ l1ModelDelta)
    (hsingleLower :
      ((999 : ℝ) / 1000) * singleModelDelta ≤ singleErrorP - singleErrorQ)
    (hl1Lower :
      ((999 : ℝ) / 1000) * l1ModelDelta ≤ l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_component_model_fraction_residual_bridge
    ((999 : ℝ) / 1000)
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
    singleModelDelta l1ModelDelta
    (by norm_num) hsingleP hsingleQ hl1P hl1Q hleading
    hsingleModel hl1Model hsingleLower hl1Lower

/-- Componentwise Route B bridge using model values and a generic fractional
residual-model contract. -/
theorem multiSq_adjacent_lt_of_component_model_fraction_value_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (ratio singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
      singleModelP singleModelQ l1ModelP l1ModelQ : ℝ)
    (hratio : 0 ≤ ratio)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hsingleModelMono : singleModelQ ≤ singleModelP)
    (hl1ModelMono : l1ModelQ ≤ l1ModelP)
    (hsingleLower :
      ratio * (singleModelP - singleModelQ) ≤
        singleErrorP - singleErrorQ)
    (hl1Lower :
      ratio * (l1ModelP - l1ModelQ) ≤
        l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_component_model_fraction_residual_bridge
    ratio singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
    (singleModelP - singleModelQ) (l1ModelP - l1ModelQ)
    hratio hsingleP hsingleQ hl1P hl1Q hleading
    (sub_nonneg.mpr hsingleModelMono) (sub_nonneg.mpr hl1ModelMono)
    hsingleLower hl1Lower

/-- Componentwise Route B bridge using model values instead of model deltas.

This is the more natural theorem-facing form for the next analytic step:
prove that the single and \(L/p\) residual models are nonincreasing from `p`
to `p+1`, and prove that the actual residual drops cover \(999/1000\) of the
corresponding model drops.  The wrapper computes the nonnegative model deltas
and delegates to
`multiSq_adjacent_lt_of_component_999_1000_model_residual_bridge`. -/
theorem multiSq_adjacent_lt_of_component_999_1000_model_value_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
      singleModelP singleModelQ l1ModelP l1ModelQ : ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hsingleModelMono : singleModelQ ≤ singleModelP)
    (hl1ModelMono : l1ModelQ ≤ l1ModelP)
    (hsingleLower :
      ((999 : ℝ) / 1000) * (singleModelP - singleModelQ) ≤
        singleErrorP - singleErrorQ)
    (hl1Lower :
      ((999 : ℝ) / 1000) * (l1ModelP - l1ModelQ) ≤
        l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_component_model_fraction_value_bridge
    ((999 : ℝ) / 1000)
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
    singleModelP singleModelQ l1ModelP l1ModelQ
    (by norm_num)
    hsingleP hsingleQ hl1P hl1Q hleading
    hsingleModelMono hl1ModelMono
    hsingleLower hl1Lower

/-- Record-shaped Route B handoff for a generic fractional component
residual-model bridge. -/
structure CombinedBpComponentModelFractionValueBridgeCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) (ratio : ℝ) where
  ratio_nonneg : 0 ≤ ratio
  singleLeadingP : ℝ
  singleLeadingQ : ℝ
  singleErrorP : ℝ
  singleErrorQ : ℝ
  l1LeadingP : ℝ
  l1LeadingQ : ℝ
  l1ErrorP : ℝ
  l1ErrorQ : ℝ
  singleModelP : ℝ
  singleModelQ : ℝ
  l1ModelP : ℝ
  l1ModelQ : ℝ
  single_decomp_p :
    env.singleSq p = singleLeadingP + singleErrorP
  single_decomp_q :
    env.singleSq (p + 1) = singleLeadingQ + singleErrorQ
  l1_decomp_p :
    env.l1OverBSq p = l1LeadingP + l1ErrorP
  l1_decomp_q :
    env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ
  leading_gap :
    (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
      (singleLeadingQ + l1LeadingQ)
  single_model_mono : singleModelQ ≤ singleModelP
  l1_model_mono : l1ModelQ ≤ l1ModelP
  single_fractional_lower :
    ratio * (singleModelP - singleModelQ) ≤
      singleErrorP - singleErrorQ
  l1_fractional_lower :
    ratio * (l1ModelP - l1ModelQ) ≤
      l1ErrorP - l1ErrorQ

/-- A generic fractional component residual-model certificate proves the
adjacent combined `b=p` drop. -/
theorem CombinedBpComponentModelFractionValueBridgeCertificate.multiDrop
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {ratio : ℝ}
    (cert :
      CombinedBpComponentModelFractionValueBridgeCertificate env p ratio) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_component_model_fraction_value_bridge
    ratio
    cert.singleLeadingP cert.singleLeadingQ cert.singleErrorP cert.singleErrorQ
    cert.l1LeadingP cert.l1LeadingQ cert.l1ErrorP cert.l1ErrorQ
    cert.singleModelP cert.singleModelQ cert.l1ModelP cert.l1ModelQ
    cert.ratio_nonneg
    cert.single_decomp_p cert.single_decomp_q
    cert.l1_decomp_p cert.l1_decomp_q cert.leading_gap
    cert.single_model_mono cert.l1_model_mono
    cert.single_fractional_lower cert.l1_fractional_lower

/-- Top-level alias for JSON/checker consumers of the generic fractional
component residual-model certificate. -/
theorem multiSq_adjacent_lt_of_combined_bp_component_model_fraction_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {ratio : ℝ}
    (cert :
      CombinedBpComponentModelFractionValueBridgeCertificate env p ratio) :
    env.multiSq (p + 1) < env.multiSq p :=
  cert.multiDrop env

/-- Record-shaped Route B handoff for the component residual-model route.

This packages the practical `b=p` model-value bridge into the same certificate
style as the later residual-budget handoffs.  A future interval or analytic
artifact can instantiate the fields with:

* the single and \(L/p\) leading/residual decompositions,
* a unit leading-gap lower bound,
* monotonicity of both component residual models, and
* the \(999/1000\) fractional lower bounds comparing actual residual drops to
  model drops.

The record deliberately contains only scalar hypotheses; it does not define the
BIFR formulas for the leading terms or residual models. -/
structure CombinedBpComponentModelValueBridgeCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) where
  singleLeadingP : ℝ
  singleLeadingQ : ℝ
  singleErrorP : ℝ
  singleErrorQ : ℝ
  l1LeadingP : ℝ
  l1LeadingQ : ℝ
  l1ErrorP : ℝ
  l1ErrorQ : ℝ
  singleModelP : ℝ
  singleModelQ : ℝ
  l1ModelP : ℝ
  l1ModelQ : ℝ
  single_decomp_p :
    env.singleSq p = singleLeadingP + singleErrorP
  single_decomp_q :
    env.singleSq (p + 1) = singleLeadingQ + singleErrorQ
  l1_decomp_p :
    env.l1OverBSq p = l1LeadingP + l1ErrorP
  l1_decomp_q :
    env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ
  leading_gap :
    (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
      (singleLeadingQ + l1LeadingQ)
  single_model_mono : singleModelQ ≤ singleModelP
  l1_model_mono : l1ModelQ ≤ l1ModelP
  single_fractional_lower :
    ((999 : ℝ) / 1000) * (singleModelP - singleModelQ) ≤
      singleErrorP - singleErrorQ
  l1_fractional_lower :
    ((999 : ℝ) / 1000) * (l1ModelP - l1ModelQ) ≤
      l1ErrorP - l1ErrorQ

/-- A complete component residual-model certificate proves the adjacent
combined `b=p` drop. -/
theorem CombinedBpComponentModelValueBridgeCertificate.multiDrop
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (cert :
      CombinedBpComponentModelValueBridgeCertificate env p) :
    env.multiSq (p + 1) < env.multiSq p :=
  env.multiSq_adjacent_lt_of_component_999_1000_model_value_bridge
    cert.singleLeadingP cert.singleLeadingQ cert.singleErrorP cert.singleErrorQ
    cert.l1LeadingP cert.l1LeadingQ cert.l1ErrorP cert.l1ErrorQ
    cert.singleModelP cert.singleModelQ cert.l1ModelP cert.l1ModelQ
    cert.single_decomp_p cert.single_decomp_q
    cert.l1_decomp_p cert.l1_decomp_q cert.leading_gap
    cert.single_model_mono cert.l1_model_mono
    cert.single_fractional_lower cert.l1_fractional_lower

/-- Top-level alias for JSON/checker consumers of
`CombinedBpComponentModelValueBridgeCertificate.multiDrop`. -/
theorem multiSq_adjacent_lt_of_combined_bp_component_model_value_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (cert :
      CombinedBpComponentModelValueBridgeCertificate env p) :
    env.multiSq (p + 1) < env.multiSq p :=
  cert.multiDrop env

/-- Componentwise Route B bridge using antitone residual-model functions.

This is the most direct scalar consumer for the derivative route.  If the
single and \(L/p\) residual model functions are antitone on the eta interval
from `ηp` to `ηq`, then the model-value bridge receives
`model q ≤ model p`.  The fractional residual lower bounds are stated against
the corresponding endpoint differences. -/
theorem multiSq_adjacent_lt_of_component_999_1000_model_antitone_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ ηp ηq : ℝ)
    (singleModel l1Model : ℝ → ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hη : ηp ≤ ηq)
    (hsingleAnti : AntitoneOn singleModel (Set.Icc ηp ηq))
    (hl1Anti : AntitoneOn l1Model (Set.Icc ηp ηq))
    (hsingleLower :
      ((999 : ℝ) / 1000) * (singleModel ηp - singleModel ηq) ≤
        singleErrorP - singleErrorQ)
    (hl1Lower :
      ((999 : ℝ) / 1000) * (l1Model ηp - l1Model ηq) ≤
        l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hηp_mem : ηp ∈ Set.Icc ηp ηq := ⟨le_rfl, hη⟩
  have hηq_mem : ηq ∈ Set.Icc ηp ηq := ⟨hη, le_rfl⟩
  exact env.multiSq_adjacent_lt_of_component_999_1000_model_value_bridge
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ
    (singleModel ηp) (singleModel ηq) (l1Model ηp) (l1Model ηq)
    hsingleP hsingleQ hl1P hl1Q hleading
    (hsingleAnti hηp_mem hηq_mem hη) (hl1Anti hηp_mem hηq_mem hη)
    hsingleLower hl1Lower

/-- Componentwise Route B bridge from coefficient derivative conditions.

For each component residual model \(D(\eta)s^{1-2\eta}\), a coefficient source
formula for \(D'\) plus the inequality \(D'\le 2\log(s)D\) proves antitonicity
on the adjacent eta interval.  This theorem then feeds those antitone models
into the \(999/1000\) component residual bridge. -/
theorem multiSq_adjacent_lt_of_component_999_1000_cross_model_deriv_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ ηp ηq s : ℝ)
    (singleD singleDderiv l1D l1Dderiv : ℝ → ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hη : ηp ≤ ηq)
    (hs : 0 < s)
    (hsingleCont : ContinuousOn singleD (Set.Icc ηp ηq))
    (hsingleDeriv :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        HasDerivWithinAt singleD (singleDderiv η)
          (interior (Set.Icc ηp ηq)) η)
    (hsingleCoeff :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        singleDderiv η ≤ 2 * Real.log s * singleD η)
    (hl1Cont : ContinuousOn l1D (Set.Icc ηp ηq))
    (hl1Deriv :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        HasDerivWithinAt l1D (l1Dderiv η)
          (interior (Set.Icc ηp ηq)) η)
    (hl1Coeff :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        l1Dderiv η ≤ 2 * Real.log s * l1D η)
    (hsingleLower :
      ((999 : ℝ) / 1000) *
          (singleD ηp * bifrCrossPower s ηp -
            singleD ηq * bifrCrossPower s ηq) ≤
        singleErrorP - singleErrorQ)
    (hl1Lower :
      ((999 : ℝ) / 1000) *
          (l1D ηp * bifrCrossPower s ηp -
            l1D ηq * bifrCrossPower s ηq) ≤
        l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hsingleAnti :
      AntitoneOn (fun η : ℝ => singleD η * bifrCrossPower s η)
        (Set.Icc ηp ηq) :=
    bifrCrossModel_antitoneOn_Icc_of_coeff_deriv_bound
      (Dfun := singleD) (Dderiv := singleDderiv)
      (s := s) (ηp := ηp) (ηq := ηq)
      hs hsingleCont hsingleDeriv hsingleCoeff
  have hl1Anti :
      AntitoneOn (fun η : ℝ => l1D η * bifrCrossPower s η)
        (Set.Icc ηp ηq) :=
    bifrCrossModel_antitoneOn_Icc_of_coeff_deriv_bound
      (Dfun := l1D) (Dderiv := l1Dderiv)
      (s := s) (ηp := ηp) (ηq := ηq)
      hs hl1Cont hl1Deriv hl1Coeff
  exact env.multiSq_adjacent_lt_of_component_999_1000_model_antitone_bridge
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ ηp ηq
    (fun η : ℝ => singleD η * bifrCrossPower s η)
    (fun η : ℝ => l1D η * bifrCrossPower s η)
    hsingleP hsingleQ hl1P hl1Q hleading hη
    hsingleAnti hl1Anti hsingleLower hl1Lower

/-- Low-bandwidth specialization of the component residual-model derivative
bridge.

The derivative-condition diagnostics naturally prove
\[
  D'(\eta)\le 2\log(2/\eta)D(\eta).
\]
In the BIFR adjacent regime \(p\ge2\), \(\eta=p/s\) gives
\(s\ge2/\eta\), so the coefficient bound against \(2\log(2/\eta)\) implies
the bound against \(2\log(s)\) required by the cross-model antitone theorem. -/
theorem multiSq_adjacent_lt_of_component_999_1000_cross_model_lowBandwidth_bridge
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (singleLeadingP singleLeadingQ singleErrorP singleErrorQ
      l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ ηp ηq s : ℝ)
    (singleD singleDderiv l1D l1Dderiv : ℝ → ℝ)
    (hsingleP :
      env.singleSq p = singleLeadingP + singleErrorP)
    (hsingleQ :
      env.singleSq (p + 1) = singleLeadingQ + singleErrorQ)
    (hl1P :
      env.l1OverBSq p = l1LeadingP + l1ErrorP)
    (hl1Q :
      env.l1OverBSq (p + 1) = l1LeadingQ + l1ErrorQ)
    (hleading :
      (1 : ℝ) ≤ (singleLeadingP + l1LeadingP) -
        (singleLeadingQ + l1LeadingQ))
    (hη : ηp ≤ ηq)
    (hs : 0 < s)
    (hsingleCont : ContinuousOn singleD (Set.Icc ηp ηq))
    (hsingleDeriv :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        HasDerivWithinAt singleD (singleDderiv η)
          (interior (Set.Icc ηp ηq)) η)
    (hsingleNonneg :
      ∀ η ∈ interior (Set.Icc ηp ηq), 0 ≤ singleD η)
    (hsingleEtaPos :
      ∀ η ∈ interior (Set.Icc ηp ηq), 0 < η)
    (hsingleFloor :
      ∀ η ∈ interior (Set.Icc ηp ηq), 2 / η ≤ s)
    (hsingleCoeffLow :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        singleDderiv η ≤ 2 * Real.log (2 / η) * singleD η)
    (hl1Cont : ContinuousOn l1D (Set.Icc ηp ηq))
    (hl1Deriv :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        HasDerivWithinAt l1D (l1Dderiv η)
          (interior (Set.Icc ηp ηq)) η)
    (hl1Nonneg :
      ∀ η ∈ interior (Set.Icc ηp ηq), 0 ≤ l1D η)
    (hl1EtaPos :
      ∀ η ∈ interior (Set.Icc ηp ηq), 0 < η)
    (hl1Floor :
      ∀ η ∈ interior (Set.Icc ηp ηq), 2 / η ≤ s)
    (hl1CoeffLow :
      ∀ η ∈ interior (Set.Icc ηp ηq),
        l1Dderiv η ≤ 2 * Real.log (2 / η) * l1D η)
    (hsingleLower :
      ((999 : ℝ) / 1000) *
          (singleD ηp * bifrCrossPower s ηp -
            singleD ηq * bifrCrossPower s ηq) ≤
        singleErrorP - singleErrorQ)
    (hl1Lower :
      ((999 : ℝ) / 1000) *
          (l1D ηp * bifrCrossPower s ηp -
            l1D ηq * bifrCrossPower s ηq) ≤
        l1ErrorP - l1ErrorQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  refine env.multiSq_adjacent_lt_of_component_999_1000_cross_model_deriv_bridge
    singleLeadingP singleLeadingQ singleErrorP singleErrorQ
    l1LeadingP l1LeadingQ l1ErrorP l1ErrorQ ηp ηq s
    singleD singleDderiv l1D l1Dderiv
    hsingleP hsingleQ hl1P hl1Q hleading hη hs
    hsingleCont hsingleDeriv ?singleCoeff
    hl1Cont hl1Deriv ?l1Coeff hsingleLower hl1Lower
  · intro η hηint
    exact bifrCoeffLogDerivBound_of_lowBandwidth_eta_floor
      (hsingleNonneg η hηint) (hsingleEtaPos η hηint)
      (hsingleFloor η hηint) (hsingleCoeffLow η hηint)
  · intro η hηint
    exact bifrCoeffLogDerivBound_of_lowBandwidth_eta_floor
      (hl1Nonneg η hηint) (hl1EtaPos η hηint)
      (hl1Floor η hηint) (hl1CoeffLow η hηint)

/-- Adjacent combined-envelope strict drop from a leading gap and a one-step
residual-delta bound.

This is the preferred scalar bridge for the practical combined `b=p` route.
The analytic side may package the full one-step residual as
`residualDelta = E_p - E_q`, absorbing the right residual into `leadingQ`. -/
theorem multiSq_adjacent_lt_of_leading_gap_and_residual_delta_bound
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ residualDelta K scale c0 : ℝ)
    (hp :
      env.multiSq p = leadingP + residualDelta)
    (hq :
      env.multiSq (p + 1) = leadingQ)
    (_hscale : 0 ≤ scale)
    (hresidual : |residualDelta| ≤ K * scale)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hKhalf : K * scale ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hresidual' : |residualDelta - 0| ≤ c0 / 2 := by
    simpa using hresidual.trans hKhalf
  exact
    env.multiSq_adjacent_lt_of_leading_gap_and_residual_bound
      leadingP leadingQ residualDelta 0 c0 hp (by simpa using hq)
      hleading hresidual' hc0

/-- Concrete large-side combined `b=p` bridge with current constants.

The new direct Route B leading derivative margin gives a natural leading gap
target `c₀ = 1`.  With the theorem-facing total residual budget `K = 40`, the
existing large-side cutoff `scale ≤ 1/640` is far stronger than needed:
`40 * scale ≤ 1/16 ≤ 1/2`. -/
theorem multiSq_adjacent_lt_of_combined_bridge_40
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ residualDelta scale : ℝ)
    (hp : env.multiSq p = leadingP + residualDelta)
    (hq : env.multiSq (p + 1) = leadingQ)
    (hscale : 0 ≤ scale)
    (hresidual : |residualDelta| ≤ 40 * scale)
    (hleading : (1 : ℝ) ≤ leadingP - leadingQ)
    (hcutoff : scale ≤ 1 / 640) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hKhalf : (40 : ℝ) * scale ≤ (1 : ℝ) / 2 := by
    calc
      (40 : ℝ) * scale ≤ 40 * (1 / 640 : ℝ) := by
        exact mul_le_mul_of_nonneg_left hcutoff (by norm_num)
      _ ≤ (1 : ℝ) / 2 := by norm_num
  exact
    env.multiSq_adjacent_lt_of_leading_gap_and_residual_delta_bound
      leadingP leadingQ residualDelta 40 scale 1
      hp hq hscale hresidual hleading hKhalf (by norm_num)

/-- Large-side combined `b=p` bridge using the standard BIFR residual scale. -/
theorem multiSq_adjacent_lt_of_combined_bridge_40_residualScale
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {s : ℝ}
    (leadingP leadingQ residualDelta : ℝ)
    (hp : env.multiSq p = leadingP + residualDelta)
    (hq : env.multiSq (p + 1) = leadingQ)
    (hs : 1 ≤ s)
    (hresidual : |residualDelta| ≤ 40 * bifrRestrictedResidualScale s)
    (hleading : (1 : ℝ) ≤ leadingP - leadingQ)
    (hcutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  exact
    env.multiSq_adjacent_lt_of_combined_bridge_40
      leadingP leadingQ residualDelta (bifrRestrictedResidualScale s)
      hp hq hscale hresidual hleading hcutoff

/-- Coarse derivative dominance for the combined `b=p` leading coefficient.

The active Route B proof target splits the combined leading coefficient as a
single-participation coefficient plus an `ell_1 / p` coefficient.  A convenient
analytic route is to prove the deliberately loose bounds
`singleDeriv ≤ 1` and `l1OverPDeriv ≤ -100`; Lean then records that the
combined derivative is at most `-99`, hence strictly negative. -/
theorem combinedBpLeadingDerivative_le_neg_of_component_bounds
    {singleDeriv l1OverPDeriv : ℝ}
    (hsingle : singleDeriv ≤ 1)
    (hl1 : l1OverPDeriv ≤ -100) :
    singleDeriv + l1OverPDeriv ≤ -99 ∧ singleDeriv + l1OverPDeriv < 0 := by
  constructor <;> linarith

/-- Factorized proof seam for the deliberately loose single-component
derivative input in Route B.

The single leading coefficient can be written as `coeff`, with derivative
`coeff * logDeriv`.  If a future certificate or analytic proof supplies
`0 ≤ coeff`, `coeff ≤ 9/4`, and `logDeriv ≤ 1/4`, then the imported
`C_single' ≤ 1` hypothesis needed by the combined `b=p` derivative boxes
follows. -/
theorem singleLeadingDerivative_le_one_of_coeff_and_log_deriv
    {coeff logDeriv deriv : ℝ}
    (hderiv : deriv = coeff * logDeriv)
    (hcoeff_nonneg : 0 ≤ coeff)
    (hcoeff : coeff ≤ 9 / 4)
    (hlog : logDeriv ≤ 1 / 4) :
    deriv ≤ 1 := by
  subst deriv
  by_cases hlog_nonneg : 0 ≤ logDeriv
  · calc
      coeff * logDeriv ≤ (9 / 4 : ℝ) * logDeriv := by
        exact mul_le_mul_of_nonneg_right hcoeff hlog_nonneg
      _ ≤ (9 / 4 : ℝ) * (1 / 4 : ℝ) := by
        exact mul_le_mul_of_nonneg_left hlog (by norm_num)
      _ ≤ 1 := by norm_num
  · have hlog_nonpos : logDeriv ≤ 0 := le_of_not_ge hlog_nonneg
    have hprod_nonpos : coeff * logDeriv ≤ 0 :=
      mul_nonpos_of_nonneg_of_nonpos hcoeff_nonneg hlog_nonpos
    linarith

/-- Sinc-normalized form of the single-participation leading coefficient.

This is algebraically the same as
`sin(π η)^2 / (2 π^2 η^2) * (4 - 7η)/(1 - 2η)` away from `η=0`, but the
`sinc` form lets Lean consume Mathlib's global `sinc_le_one` bound directly. -/
def bifrSingleLeadingCoefficientModel (η : ℝ) : ℝ :=
  (Real.sinc (Real.pi * η)) ^ 2 / 2 * ((4 - 7 * η) / (1 - 2 * η))

/-- The sinc-normalized single-leading coefficient model equals the explicit
sine formula away from `η=0`. -/
theorem bifrSingleLeadingCoefficientModel_eq_sin_formula
    {η : ℝ} (hη : η ≠ 0) :
    bifrSingleLeadingCoefficientModel η =
      (Real.sin (Real.pi * η) ^ 2 / (2 * Real.pi ^ 2 * η ^ 2)) *
        ((4 - 7 * η) / (1 - 2 * η)) := by
  have hπη : Real.pi * η ≠ 0 := mul_ne_zero Real.pi_ne_zero hη
  rw [bifrSingleLeadingCoefficientModel, Real.sinc_of_ne_zero hπη]
  field_simp [hπη, Real.pi_ne_zero, hη]

/-- Crude but fully Lean-backed lower bound for the sinc factor on the Route B
combined `b=p` interval.

This uses Mathlib's `sin_gt_sub_cube` and the elementary endpoint
`π η ≤ 1` when `η ≤ 1/4`.  It is intentionally not sharp; its role is to make
the reflection-based coefficient route target a very weak but theorem-friendly
positive lower bound. -/
theorem bifrSinc_pi_mul_eta_gt_three_four
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    (3 / 4 : ℝ) < Real.sinc (Real.pi * η) := by
  have hxpos : 0 < Real.pi * η := mul_pos Real.pi_pos hη
  have hxle1 : Real.pi * η ≤ 1 := by
    have hpi4 : Real.pi * η ≤ Real.pi * (1 / 4 : ℝ) :=
      mul_le_mul_of_nonneg_left hhi Real.pi_pos.le
    have hpi4_lt_one : Real.pi * (1 / 4 : ℝ) < 1 := by
      nlinarith [Real.pi_lt_four]
    exact le_of_lt (lt_of_le_of_lt hpi4 hpi4_lt_one)
  have hsin := Real.sin_gt_sub_cube hxpos hxle1
  have hxne : Real.pi * η ≠ 0 := ne_of_gt hxpos
  rw [Real.sinc_of_ne_zero hxne]
  change (3 / 4 : ℝ) < Real.sin (Real.pi * η) / (Real.pi * η)
  rw [lt_div_iff₀ hxpos]
  nlinarith [hsin, hxle1, sq_nonneg (Real.pi * η)]

/-- The reflection route only needs a very weak lower bound once the combined
derivative consumer is stated with the natural `coeff ≥ 2` threshold.

If a later algebra lemma shows
`(32 / η) * sinc(π η)^2 ≤ A(η)T(η)^2/η`, this theorem immediately supplies the
remaining scalar budget. -/
theorem two_le_bifrSincLowerCoefficient
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    (2 : ℝ) ≤ (32 / η) * (Real.sinc (Real.pi * η)) ^ 2 := by
  have hsinc_gt : (3 / 4 : ℝ) < Real.sinc (Real.pi * η) :=
    bifrSinc_pi_mul_eta_gt_three_four hη hhi
  have hsinc_sq : (9 / 16 : ℝ) ≤ (Real.sinc (Real.pi * η)) ^ 2 := by
    nlinarith [hsinc_gt]
  have h32div : (128 : ℝ) ≤ 32 / η := by
    rw [le_div_iff₀ hη]
    nlinarith
  calc
    (2 : ℝ) ≤ (128 : ℝ) * (9 / 16 : ℝ) := by norm_num
    _ ≤ (32 / η) * (Real.sinc (Real.pi * η)) ^ 2 := by
      exact mul_le_mul h32div hsinc_sq (by norm_num) (by nlinarith)

/-- Gamma-reflection algebra for the Route B coefficient route.

This removes the remaining special-function product from the direct
coefficient lower-bound attempt:
\[
\Gamma(\eta)^{-2}\Gamma(1-\eta)^{-2}
  = \left(\frac{\sin(\pi\eta)}{\pi}\right)^2.
\] -/
theorem bifrGammaInvSq_mul_one_sub_eq_sin_sq
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    (Real.Gamma η)⁻¹ ^ 2 * (Real.Gamma (1 - η))⁻¹ ^ 2 =
      (Real.sin (Real.pi * η) / Real.pi) ^ 2 := by
  have href := Real.Gamma_mul_Gamma_one_sub η
  have hsinpos : 0 < Real.sin (Real.pi * η) := by
    apply Real.sin_pos_of_pos_of_lt_pi
    · positivity
    · nlinarith [Real.pi_pos, hη, hhi]
  have hπne : Real.pi ≠ 0 := Real.pi_ne_zero
  have hsinne : Real.sin (Real.pi * η) ≠ 0 := ne_of_gt hsinpos
  have hmul :
      (Real.Gamma η)⁻¹ * (Real.Gamma (1 - η))⁻¹ =
        Real.sin (Real.pi * η) / Real.pi := by
    rw [← mul_inv, href]
    field_simp [hπne, hsinne]
  calc
    (Real.Gamma η)⁻¹ ^ 2 * (Real.Gamma (1 - η))⁻¹ ^ 2
        = ((Real.Gamma η)⁻¹ * (Real.Gamma (1 - η))⁻¹) ^ 2 := by ring
    _ = (Real.sin (Real.pi * η) / Real.pi) ^ 2 := by rw [hmul]

/-- The raw `T` leading numerator is bounded below by its beta-tail term. -/
theorem bifrCombinedBpRawTLeadingModel_ge_tail
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    8 * η ^ (-η) ≤ bifrCombinedBpRawTLeadingModel η := by
  rw [bifrCombinedBpRawTLeadingModel]
  have hden : 0 < 1 - η := by linarith
  have hnonneg : 0 ≤ η ^ (1 - η) / (1 - η) := by positivity
  linarith

/-- Exact reflection-normalized coefficient supplied by the beta-tail part of
the `ell_1 / p` leading model.

This is the algebraic bridge from the gamma/reflection route to the crude
sinc lower bound used by the combined `b=p` derivative consumer. -/
theorem bifrCombinedBpTailCoefficient_eq_sinc_lower
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    ((Real.Gamma η)⁻¹ ^ 2 / (2 * η ^ (2 - 2 * η)) *
        ((8 * η ^ (-η) * (Real.Gamma (1 - η))⁻¹) ^ 2) / η) =
      (32 / η) * (Real.sinc (Real.pi * η)) ^ 2 := by
  have href := bifrGammaInvSq_mul_one_sub_eq_sin_sq hη hhi
  have hxne : Real.pi * η ≠ 0 := mul_ne_zero Real.pi_ne_zero hη.ne'
  have hsinc : Real.sinc (Real.pi * η) = Real.sin (Real.pi * η) / (Real.pi * η) :=
    Real.sinc_of_ne_zero hxne
  have h1 :
      ((Real.Gamma η)⁻¹ ^ 2 / (2 * η ^ (2 - 2 * η)) *
          ((8 * η ^ (-η) * (Real.Gamma (1 - η))⁻¹) ^ 2) / η) =
      (32 / η) * (((Real.Gamma η)⁻¹ ^ 2 * (Real.Gamma (1 - η))⁻¹ ^ 2) *
          (η ^ (-η)) ^ 2 / η ^ (2 - 2 * η)) := by
    ring
  have hpow1 : (η ^ (-η)) ^ 2 = η ^ (-2 * η) := by
    rw [← Real.rpow_natCast]
    rw [← Real.rpow_mul hη.le]
    ring_nf
  have hpow2 : η ^ (-2 * η) / η ^ (2 - 2 * η) = η ^ (-2 : ℝ) := by
    rw [← Real.rpow_sub hη]
    congr 1
    ring
  have hpow3 : η ^ 2 * η ^ (-2 : ℝ) = 1 := by
    rw [← Real.rpow_natCast]
    rw [← Real.rpow_add hη]
    norm_num
  rw [h1, href, hpow1]
  have hinner :
      (Real.sin (Real.pi * η) / Real.pi) ^ 2 * η ^ (-2 * η) / η ^ (2 - 2 * η) =
        (Real.sinc (Real.pi * η)) ^ 2 := by
    calc
      (Real.sin (Real.pi * η) / Real.pi) ^ 2 * η ^ (-2 * η) / η ^ (2 - 2 * η)
          = (Real.sin (Real.pi * η) / Real.pi) ^ 2 *
              (η ^ (-2 * η) / η ^ (2 - 2 * η)) := by ring
      _ = (Real.sin (Real.pi * η) / Real.pi) ^ 2 * η ^ (-2 : ℝ) := by
        rw [hpow2]
      _ = (Real.sinc (Real.pi * η)) ^ 2 := by
        rw [hsinc]
        field_simp [Real.pi_ne_zero, hη.ne']
        nlinarith [hpow3]
  rw [hinner]

/-- The crude sinc lower coefficient is below the actual `ell_1 / p` leading
coefficient model on the practical Route B interval.

The proof keeps only the beta-tail piece of the raw \(T\) numerator and then
uses the reflection identity above. -/
theorem bifrSincLowerCoefficient_le_l1OverPModelCoefficient
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    (32 / η) * (Real.sinc (Real.pi * η)) ^ 2 ≤
      bifrCombinedBpALeadingModel η * bifrCombinedBpTLeadingModel η ^ 2 / η := by
  have hraw_tail : 8 * η ^ (-η) ≤ bifrCombinedBpRawTLeadingModel η :=
    bifrCombinedBpRawTLeadingModel_ge_tail hη hhi
  have htail_nonneg : 0 ≤ 8 * η ^ (-η) := by positivity
  have hraw_nonneg : 0 ≤ bifrCombinedBpRawTLeadingModel η :=
    htail_nonneg.trans hraw_tail
  have hgamma_sq_nonneg : 0 ≤ (Real.Gamma (1 - η))⁻¹ ^ 2 := sq_nonneg _
  have htail_sq :
      (8 * η ^ (-η) * (Real.Gamma (1 - η))⁻¹) ^ 2 ≤
        (bifrCombinedBpRawTLeadingModel η * (Real.Gamma (1 - η))⁻¹) ^ 2 := by
    calc
      (8 * η ^ (-η) * (Real.Gamma (1 - η))⁻¹) ^ 2
          = (8 * η ^ (-η)) ^ 2 * (Real.Gamma (1 - η))⁻¹ ^ 2 := by ring
      _ ≤ (bifrCombinedBpRawTLeadingModel η) ^ 2 *
          (Real.Gamma (1 - η))⁻¹ ^ 2 := by
        exact mul_le_mul_of_nonneg_right
          (pow_le_pow_left₀ htail_nonneg hraw_tail 2) hgamma_sq_nonneg
      _ = (bifrCombinedBpRawTLeadingModel η * (Real.Gamma (1 - η))⁻¹) ^ 2 := by ring
  have hA_nonneg :
      0 ≤ (Real.Gamma η)⁻¹ ^ 2 / (2 * η ^ (2 - 2 * η)) := by positivity
  have htail_coeff :
      ((Real.Gamma η)⁻¹ ^ 2 / (2 * η ^ (2 - 2 * η)) *
          ((8 * η ^ (-η) * (Real.Gamma (1 - η))⁻¹) ^ 2) / η) ≤
        ((Real.Gamma η)⁻¹ ^ 2 / (2 * η ^ (2 - 2 * η)) *
          ((bifrCombinedBpRawTLeadingModel η * (Real.Gamma (1 - η))⁻¹) ^ 2) / η) := by
    exact div_le_div_of_nonneg_right
      (mul_le_mul_of_nonneg_left htail_sq hA_nonneg) hη.le
  rw [← bifrCombinedBpTailCoefficient_eq_sinc_lower hη hhi]
  exact htail_coeff

/-- Fully Lean-backed direct lower bound for the practical combined `b=p`
`ell_1 / p` leading coefficient. -/
theorem l1OverPModelCoefficient_ge_two_direct
    {η : ℝ} (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ)) :
    (2 : ℝ) ≤ bifrCombinedBpALeadingModel η *
      bifrCombinedBpTLeadingModel η ^ 2 / η :=
  (two_le_bifrSincLowerCoefficient hη hhi).trans
    (bifrSincLowerCoefficient_le_l1OverPModelCoefficient hη hhi)

/-- The single-leading coefficient model is nonnegative on the Route B
interval. -/
theorem bifrSingleLeadingCoefficientModel_nonneg
    {η : ℝ} (hhi : η ≤ (1 / 4 : ℝ)) :
    0 ≤ bifrSingleLeadingCoefficientModel η := by
  have hden : 0 < 1 - 2 * η := by linarith
  have hnum : 0 ≤ 4 - 7 * η := by linarith
  rw [bifrSingleLeadingCoefficientModel]
  positivity

/-- The single-leading coefficient model is at most `9/4` on the Route B
interval.

The proof uses only `|sinc x| ≤ 1` and the rational endpoint bound
`(4-7η)/(1-2η) ≤ 9/2` for `η ≤ 1/4`. -/
theorem bifrSingleLeadingCoefficientModel_le_nine_fourths
    {η : ℝ} (hhi : η ≤ (1 / 4 : ℝ)) :
    bifrSingleLeadingCoefficientModel η ≤ (9 / 4 : ℝ) := by
  have hsinc_abs : |Real.sinc (Real.pi * η)| ≤ (1 : ℝ) :=
    Real.abs_sinc_le_one (Real.pi * η)
  have hsinc_sq : (Real.sinc (Real.pi * η)) ^ 2 ≤ (1 : ℝ) := by
    nlinarith [abs_nonneg (Real.sinc (Real.pi * η)),
      abs_mul_abs_self (Real.sinc (Real.pi * η))]
  have hden : 0 < 1 - 2 * η := by linarith
  have hnum : 0 ≤ 4 - 7 * η := by linarith
  have hratio_nonneg : 0 ≤ (4 - 7 * η) / (1 - 2 * η) := by
    exact div_nonneg hnum hden.le
  have hratio : (4 - 7 * η) / (1 - 2 * η) ≤ (9 / 2 : ℝ) := by
    rw [div_le_iff₀ hden]
    nlinarith
  rw [bifrSingleLeadingCoefficientModel]
  calc
    (Real.sinc (Real.pi * η)) ^ 2 / 2 * ((4 - 7 * η) / (1 - 2 * η))
        ≤ (1 / 2 : ℝ) * ((4 - 7 * η) / (1 - 2 * η)) := by
      nlinarith
    _ ≤ (1 / 2 : ℝ) * (9 / 2 : ℝ) := by
      exact mul_le_mul_of_nonneg_left hratio (by norm_num)
    _ = (9 / 4 : ℝ) := by norm_num

/-- Elementary rational upper model for the single-leading log derivative after
using the standard bound `cot x ≤ 1/x - x/3` and `π² ≥ 9`.

The actual single log derivative is
`2π cot(πη)-2/η-7/(4-7η)+2/(1-2η)`.  The trigonometric estimate reduces it to
this rational expression. -/
def bifrSingleLogDerivativeUpperModel (η : ℝ) : ℝ :=
  -6 * η - 7 / (4 - 7 * η) + 2 / (1 - 2 * η)

/-- Numerical π bound used by the single log-derivative bridge. -/
theorem bifr_pi_sq_ge_nine : (9 : ℝ) ≤ Real.pi ^ 2 := by
  nlinarith [Real.pi_gt_three]

/-- The standard cotangent estimate feeds the elementary rational upper model
for the single-leading log derivative.

This theorem deliberately leaves the trigonometric source inequality as the
hypothesis `hcot`.  The rest is scalar bookkeeping: multiply by `2π`, cancel
the `2/η` term, and use `π² ≥ 9` to replace `-2π²η/3` by `-6η`. -/
theorem singleLeadingLogDerivative_le_model_of_cot_bound
    {η logDeriv : ℝ} (hη : 0 < η)
    (hlog :
      logDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hcot :
      Real.cot (Real.pi * η) ≤ 1 / (Real.pi * η) - (Real.pi * η) / 3)
    (hpi_sq : (9 : ℝ) ≤ Real.pi ^ 2) :
    logDeriv ≤ bifrSingleLogDerivativeUpperModel η := by
  have htwopi_nonneg : 0 ≤ 2 * Real.pi := by positivity
  have hcot_scaled :
      2 * Real.pi * Real.cot (Real.pi * η) ≤
        2 / η - (2 * Real.pi ^ 2 * η) / 3 := by
    have hmul := mul_le_mul_of_nonneg_left hcot htwopi_nonneg
    have hrewrite :
        2 * Real.pi * (1 / (Real.pi * η) - (Real.pi * η) / 3) =
          2 / η - (2 * Real.pi ^ 2 * η) / 3 := by
      field_simp [hη.ne', Real.pi_ne_zero]
    exact hmul.trans_eq hrewrite
  rw [hlog, bifrSingleLogDerivativeUpperModel]
  nlinarith [hη, hpi_sq, hcot_scaled]

/-- Derivative of the auxiliary function used in the cotangent source bound.

For \(g(x)=(1-x^2/3)\sin x-x\cos x\), one has
\[
g'(x)=\frac{x}{3}(\sin x-x\cos x).
\]
Together with `Real.le_tan`, this proves \(g\) is nondecreasing on the route
interval. -/
theorem bifrCotAux_deriv (x : ℝ) :
    deriv (fun t : ℝ => (1 - t ^ 2 / 3) * Real.sin t - t * Real.cos t) x =
      x / 3 * (Real.sin x - x * Real.cos x) := by
  have hpoly : deriv (fun t : ℝ => (1 - t ^ 2 / 3)) x = -2 * x / 3 := by
    rw [show (fun t : ℝ => (1 - t ^ 2 / 3)) =
      (fun t : ℝ => 1 - (fun t : ℝ => t ^ 2 / 3) t) by rfl]
    rw [deriv_fun_sub]
    · rw [deriv_const]
      rw [show deriv (fun t : ℝ => t ^ 2 / 3) x = (2 * x) / 3 by
        rw [show (fun t : ℝ => t ^ 2 / 3) =
          fun t : ℝ => (fun t : ℝ => t ^ 2) t / 3 by rfl]
        rw [deriv_div_const]
        rw [deriv_pow_field]
        ring]
      ring
    · fun_prop
    · fun_prop
  rw [deriv_fun_sub]
  · rw [deriv_fun_mul]
    · rw [deriv_fun_mul]
      · rw [hpoly]
        simp
        ring_nf
      · fun_prop
      · fun_prop
    · fun_prop
    · fun_prop
  · fun_prop
  · fun_prop

/-- The inner inequality behind the cotangent source bound:
`x * cos x <= sin x` on `[0, π/2)`.

This is just `Real.le_tan` multiplied by the positive cosine. -/
theorem bifr_mul_cos_le_sin_of_nonneg_of_lt_pi_div_two
    {x : ℝ} (h0 : 0 ≤ x) (hpi : x < Real.pi / 2) :
    x * Real.cos x ≤ Real.sin x := by
  have hcos : 0 < Real.cos x :=
    Real.cos_pos_of_mem_Ioo ⟨by linarith [Real.pi_pos], hpi⟩
  have htan := Real.le_tan h0 hpi
  rw [Real.tan_eq_sin_div_cos] at htan
  have hmul := (mul_le_mul_iff_of_pos_right hcos).mpr htan
  field_simp [hcos.ne'] at hmul
  exact hmul

/-- Standard route source bound for cotangent:
\[
\cot x \le 1/x-x/3
\]
on \(0<x\le\pi/4\).

The proof avoids a Taylor import.  It applies the mean-value monotonicity
criterion to \(g(x)=(1-x^2/3)\sin x-x\cos x\); the derivative is
\((x/3)(\sin x-x\cos x)\), nonnegative by `Real.le_tan`. -/
theorem bifr_cot_le_inv_sub_third
    {x : ℝ} (h0 : 0 < x) (hhi : x ≤ Real.pi / 4) :
    Real.cot x ≤ 1 / x - x / 3 := by
  let g : ℝ → ℝ := fun t => (1 - t ^ 2 / 3) * Real.sin t - t * Real.cos t
  have hmono : MonotoneOn g (Set.Icc 0 x) := by
    refine monotoneOn_of_deriv_nonneg (convex_Icc 0 x) ?hcont ?hdiff ?hnonneg
    · fun_prop
    · fun_prop
    · intro y hy
      rw [bifrCotAux_deriv]
      have hyI : y ∈ Set.Ioo 0 x := by
        simpa [interior_Icc, h0.ne'] using hy
      have hy0 : 0 ≤ y := le_of_lt hyI.1
      have hyx : y ≤ x := le_of_lt hyI.2
      have hypi : y < Real.pi / 2 := by
        linarith [hyx, hhi, Real.pi_pos]
      have hinner := bifr_mul_cos_le_sin_of_nonneg_of_lt_pi_div_two hy0 hypi
      nlinarith [hy0, hinner]
  have hxmem : x ∈ Set.Icc 0 x := ⟨h0.le, le_rfl⟩
  have h0mem : (0 : ℝ) ∈ Set.Icc 0 x := ⟨le_rfl, h0.le⟩
  have hg_nonneg : 0 ≤ g x := by
    have := hmono h0mem hxmem h0.le
    simpa [g] using this
  have hsin : 0 < Real.sin x := by
    have hxpi : x < Real.pi := by
      linarith [hhi, Real.pi_pos]
    exact Real.sin_pos_of_pos_of_lt_pi h0 hxpi
  have hmain : x * Real.cos x ≤ (1 - x ^ 2 / 3) * Real.sin x := by
    dsimp [g] at hg_nonneg
    linarith
  rw [Real.cot_eq_cos_div_sin]
  rw [div_le_iff₀ hsin]
  field_simp [h0.ne']
  nlinarith [hmain]

/-- Route-B specialization of the cotangent source bound feeding the
single-leading log-derivative model.

This removes the cotangent inequality from the imported single-branch inputs:
the remaining numerical source here is only `π² ≥ 9`, which downstream
certificates can supply or replace by a Mathlib bound. -/
theorem singleLeadingLogDerivative_le_model_on_route
    {η logDeriv : ℝ} (hη : 0 < η) (hηhi : η ≤ (1 / 4 : ℝ))
    (hlog :
      logDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    logDeriv ≤ bifrSingleLogDerivativeUpperModel η := by
  have hx0 : 0 < Real.pi * η := by positivity
  have hxhi : Real.pi * η ≤ Real.pi / 4 := by
    nlinarith [Real.pi_pos, hηhi]
  exact singleLeadingLogDerivative_le_model_of_cot_bound hη hlog
    (bifr_cot_le_inv_sub_third hx0 hxhi) bifr_pi_sq_ge_nine

/-- If the actual single-leading log derivative is bounded by the elementary
upper model and the model arithmetic is certified, then it is at most `1/4`.

The omitted arithmetic subclaim is elementary:
`bifrSingleLogDerivativeUpperModel η ≤ 1/4` on the Route B interval.  It is
kept as an explicit certificate/analytic input here because the current proof
frontier is the combined `b=p` theorem, not denominator normalization for this
rational inequality. -/
theorem singleLeadingLogDerivative_le_quarter_of_upper_model
    {η logDeriv : ℝ}
    (hmodel : logDeriv ≤ bifrSingleLogDerivativeUpperModel η)
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ)) :
    logDeriv ≤ (1 / 4 : ℝ) :=
  hmodel.trans hquarter

/-- The elementary rational single-log upper model is at most `1/4` on the
Route B interval.

This closes the exact-rational certificate seam recorded by
`combined_bp_single_log_derivative_model_certificate_r01.json`.  The algebraic
identity is
\[
M(\eta)-1/4 =
-\frac{\eta(336\eta^2-346\eta+81)}
        {4(4-7\eta)(1-2\eta)}.
\]
On \(0\le\eta\le1/4\), the denominator is positive and the quadratic is
bounded below by its right-endpoint value. -/
theorem bifrSingleLogDerivativeUpperModel_le_quarter_on_route
    {η : ℝ} (hη_nonneg : 0 ≤ η) (hηhi : η ≤ (1 / 4 : ℝ)) :
    bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ) := by
  have hden₁ : 0 < 4 - 7 * η := by nlinarith
  have hden₂ : 0 < 1 - 2 * η := by nlinarith
  have hden₁n : 4 - η * 7 ≠ 0 := by nlinarith
  have hden₂n : 1 - η * 2 ≠ 0 := by nlinarith
  have hden : 0 < 4 * (4 - 7 * η) * (1 - 2 * η) := by positivity
  have hden₃ : 4 - η * 15 + η ^ 2 * 14 ≠ 0 := by
    have hprod : 0 < (4 - 7 * η) * (1 - 2 * η) := by positivity
    suffices 4 - η * 15 + η ^ 2 * 14 = (4 - 7 * η) * (1 - 2 * η) by
      rw [this]
      exact hprod.ne'
    ring
  have hq : 0 ≤ 336 * η ^ 2 - 346 * η + 81 := by
    have hleft : 0 ≤ (1 / 4 : ℝ) - η := by linarith
    have hright : 0 ≤ 262 - 336 * η := by nlinarith
    have hprod : 0 ≤ ((1 / 4 : ℝ) - η) * (262 - 336 * η) :=
      mul_nonneg hleft hright
    nlinarith [hprod]
  have hnum : -η * (336 * η ^ 2 - 346 * η + 81) ≤ 0 := by
    nlinarith
  have hdiff :
      bifrSingleLogDerivativeUpperModel η - (1 / 4 : ℝ) =
        (-η * (336 * η ^ 2 - 346 * η + 81)) /
          (4 * (4 - 7 * η) * (1 - 2 * η)) := by
    rw [eq_div_iff hden.ne']
    rw [bifrSingleLogDerivativeUpperModel]
    field_simp [hden₁.ne', hden₂.ne', hden₁n, hden₂n]
    ring_nf
  have hle :
      bifrSingleLogDerivativeUpperModel η - (1 / 4 : ℝ) ≤ 0 := by
    rw [hdiff]
    exact div_nonpos_of_nonpos_of_nonneg hnum (le_of_lt hden)
  linarith

/-- Direct Route B single-log derivative bound after the cotangent source
estimate.  No imported rational model certificate is needed. -/
theorem singleLeadingLogDerivative_le_quarter_on_route
    {η logDeriv : ℝ} (hη_nonneg : 0 ≤ η) (hηhi : η ≤ (1 / 4 : ℝ))
    (hmodel : logDeriv ≤ bifrSingleLogDerivativeUpperModel η) :
    logDeriv ≤ (1 / 4 : ℝ) :=
  singleLeadingLogDerivative_le_quarter_of_upper_model hmodel
    (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη_nonneg hηhi)

/-- Route B single-derivative consumer specialized to the sinc-normalized
single-leading coefficient model.

After identifying the actual single coefficient with
`bifrSingleLeadingCoefficientModel η`, the only remaining analytic input here
is `(log C_single)' ≤ 1/4`. -/
theorem singleLeadingDerivative_le_one_of_model_coeff_and_log_deriv
    {η logDeriv deriv : ℝ}
    (hderiv : deriv = bifrSingleLeadingCoefficientModel η * logDeriv)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : logDeriv ≤ (1 / 4 : ℝ)) :
    deriv ≤ 1 :=
  singleLeadingDerivative_le_one_of_coeff_and_log_deriv hderiv
    (bifrSingleLeadingCoefficientModel_nonneg hhi)
    (bifrSingleLeadingCoefficientModel_le_nine_fourths hhi)
    hlog

/-- Route B single-derivative consumer using the elementary rational upper
model for the single log derivative.  The remaining imported/certified inputs
are the cotangent-to-model comparison and the model arithmetic
`model ≤ 1/4`. -/
theorem singleLeadingDerivative_le_one_of_model_upper
    {η logDeriv deriv : ℝ}
    (hderiv : deriv = bifrSingleLeadingCoefficientModel η * logDeriv)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hmodel : logDeriv ≤ bifrSingleLogDerivativeUpperModel η)
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ)) :
    deriv ≤ 1 :=
  singleLeadingDerivative_le_one_of_model_coeff_and_log_deriv hderiv hhi
    (singleLeadingLogDerivative_le_quarter_of_upper_model hmodel hquarter)

/-- Route-B single-leading derivative consumer.

After the sinc coefficient bound, cotangent source bound, and π bound are
kernel-checked, the only remaining per-box input is the exact rational model
arithmetic `bifrSingleLogDerivativeUpperModel η ≤ 1/4`. -/
theorem singleLeadingDerivative_le_one_on_route
    {η logDeriv deriv : ℝ} (hη : 0 < η) (hηhi : η ≤ (1 / 4 : ℝ))
    (hderiv : deriv = bifrSingleLeadingCoefficientModel η * logDeriv)
    (hlog :
      logDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ)) :
    deriv ≤ 1 :=
  singleLeadingDerivative_le_one_of_model_upper hderiv hηhi
    (singleLeadingLogDerivative_le_model_on_route hη hηhi hlog) hquarter

/-- Direct Route B single-leading derivative consumer.

This is the preferred single-branch endpoint: cotangent, π, sinc coefficient,
and rational upper-model arithmetic are all discharged in Lean on
`0 < η ≤ 1/4`. -/
theorem singleLeadingDerivative_le_one_on_route_direct
    {η logDeriv deriv : ℝ} (hη : 0 < η) (hηhi : η ≤ (1 / 4 : ℝ))
    (hderiv : deriv = bifrSingleLeadingCoefficientModel η * logDeriv)
    (hlog :
      logDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    deriv ≤ 1 :=
  singleLeadingDerivative_le_one_of_model_coeff_and_log_deriv hderiv hηhi
    (singleLeadingLogDerivative_le_quarter_on_route hη.le hηhi
      (singleLeadingLogDerivative_le_model_on_route hη hηhi hlog))

/-- Factorized proof seam for the negative `ell_1 / p` leading derivative.

If the `ell_1 / p` leading coefficient is at least `100` and its logarithmic
derivative is at most `-1`, then its ordinary derivative, represented as
`coeff * logDeriv`, is at most `-100`.  This is the scalar Lean endpoint for
the factorized Route B diagnostic. -/
theorem l1OverPLeadingDerivative_le_neg_of_coeff_and_log_deriv
    {coeff logDeriv : ℝ}
    (hcoeff : 100 ≤ coeff)
    (hlog : logDeriv ≤ -1) :
    coeff * logDeriv ≤ -100 := by
  calc
    coeff * logDeriv ≤ 100 * logDeriv := by
      exact mul_le_mul_of_nonpos_right hcoeff (by linarith)
    _ ≤ 100 * (-1) := by
      exact mul_le_mul_of_nonneg_left hlog (by norm_num)
    _ = -100 := by norm_num

/-- Flexible version of the Route B `ell_1 / p` derivative seam.

The earlier packet-facing endpoint used the convenient budget `coeff ≥ 100`.
For proof search this theorem keeps the actual arithmetic visible: if
`1 + coeff * logDeriv ≤ margin`, then the combined derivative is at most that
margin after the already-proved single-component bound `singleDeriv ≤ 1`.
This lets later direct coefficient proofs use a much weaker positive
coefficient lower bound than `100` when only negativity is needed. -/
theorem combinedBpLeadingDerivative_le_margin_of_single_and_l1_log
    {singleDeriv coeff logDeriv margin : ℝ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff_nonneg : 0 ≤ coeff)
    (hlog : logDeriv ≤ -1)
    (hbudget : 1 - coeff ≤ margin) :
    singleDeriv + coeff * logDeriv ≤ margin := by
  have hl1 : coeff * logDeriv ≤ coeff * (-1) := by
    exact mul_le_mul_of_nonneg_left hlog hcoeff_nonneg
  have hsum : singleDeriv + coeff * logDeriv ≤ 1 - coeff := by
    linarith
  exact hsum.trans hbudget

/-- Minimal negativity consumer for the practical combined `b=p` leading
derivative.

The `ell_1 / p` log derivative is at most `-1`.  Therefore a coefficient lower
bound `coeff ≥ 2` already beats the single-component upper bound `≤ 1`, giving a
strictly negative combined derivative. -/
theorem combinedBpLeadingDerivative_lt_zero_of_coeff_two_and_log
    {singleDeriv coeff logDeriv : ℝ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff : 2 ≤ coeff)
    (hlog : logDeriv ≤ -1) :
    singleDeriv + coeff * logDeriv < 0 := by
  have hcoeff_nonneg : 0 ≤ coeff := by linarith
  have hle :
      singleDeriv + coeff * logDeriv ≤ (-1 : ℝ) :=
    combinedBpLeadingDerivative_le_margin_of_single_and_l1_log
      hsingle hcoeff_nonneg hlog (by linarith)
  linarith

/-- Box-budget arithmetic for the `ell_1 / p` log-derivative.

The factorized Route B proof decomposes
`(log C_l1/p)'` as `logADeriv + 2 * tLogDeriv + negInvEta`.  On each eta box
the diagnostic proposes simple bounds for `tLogDeriv` and `negInvEta`, while
`logADeriv ≤ 0` is intended as a global subclaim.  This theorem records the
scalar arithmetic turning those box bounds into `(log C_l1/p)' ≤ -1`. -/
theorem l1OverPLogDerivative_le_neg_one_of_box_bounds
    {logADeriv tLogDeriv negInvEta tBound negInvBound : ℝ}
    (hlogA : logADeriv ≤ 0)
    (ht : tLogDeriv ≤ tBound)
    (hinv : negInvEta ≤ negInvBound)
    (hbudget : 2 * tBound + negInvBound ≤ -1) :
    logADeriv + 2 * tLogDeriv + negInvEta ≤ -1 := by
  nlinarith

/-- Route B `ell_1 / p` log-derivative box consumer with the `log A` input
discharged by the half-shift certificate bridge.

After `bifrCombinedBpL1LogADerivative_nonpos_of_certificate`, each eta box only
needs a `logT'` upper bound, the elementary `-1/η` upper bound, and the scalar
box budget. -/
theorem l1OverPLogDerivative_le_neg_one_of_certificate_box
    {η logUpper tLogDeriv negInvEta tBound negInvBound : ℝ} {N : ℕ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (ht : tLogDeriv ≤ tBound)
    (hinv : negInvEta ≤ negInvBound)
    (hbudget : 2 * tBound + negInvBound ≤ -1) :
    bifrCombinedBpL1LogADerivative η + 2 * tLogDeriv + negInvEta ≤ -1 :=
  l1OverPLogDerivative_le_neg_one_of_box_bounds
    (bifrCombinedBpL1LogADerivative_nonpos_of_certificate hη hhi hlog hbox)
    ht hinv hbudget

/-- Route B `ell_1 / p` log-derivative box consumer where the remaining `T`
input is the elementary raw-`T` log-derivative.

The actual `T` log-derivative is `rawLogDeriv + ψ(1-η)`.  Since
`ψ(1-η) ≤ 0` on the route interval, a raw-derivative upper bound is enough.
This is the preferred current surface for the five eta-box obligations because
it removes the last special-function term from the `T` boxes. -/
theorem l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT
    {η logUpper rawLogDeriv negInvEta tBound negInvBound : ℝ} {N : ℕ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (hraw : rawLogDeriv ≤ tBound)
    (hinv : negInvEta ≤ negInvBound)
    (hbudget : 2 * tBound + negInvBound ≤ -1) :
    bifrCombinedBpL1LogADerivative η +
      2 * (rawLogDeriv + bifrRealDigamma (1 - η)) + negInvEta ≤ -1 := by
  have hη0 : 0 ≤ η := le_of_lt hη
  have hη1 : η < 1 := by linarith
  have ht :
      rawLogDeriv + bifrRealDigamma (1 - η) ≤ tBound :=
    tLogDerivative_le_of_rawLogDerivative_le hη0 hη1 hraw
  exact l1OverPLogDerivative_le_neg_one_of_certificate_box
    hη hhi hlog hbox ht hinv hbudget

/-- Route B `ell_1 / p` log-derivative box consumer specialized to the closed
elementary raw-`T` derivative model.

After the raw derivative is algebraically simplified, each eta box only needs
to upper-bound `bifrCombinedBpL1RawTLogDerivativeModel η`. -/
theorem l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model
    {η logUpper negInvEta tBound negInvBound : ℝ} {N : ℕ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N)
    (hraw : bifrCombinedBpL1RawTLogDerivativeModel η ≤ tBound)
    (hinv : negInvEta ≤ negInvBound)
    (hbudget : 2 * tBound + negInvBound ≤ -1) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) + negInvEta ≤ -1 :=
  l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT
    hη hhi hlog hbox hraw hinv hbudget

/-- Route B `ell_1 / p` log-derivative box consumer using the direct Lean
half-shift proof for `logA' <= 0`.

Compared with `l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model`,
this theorem removes the `hlog`/`hbox` certificate inputs from the box seam. -/
theorem l1OverPLogDerivative_le_neg_one_of_direct_logA_rawT_model
    {η negInvEta tBound negInvBound : ℝ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (hraw : bifrCombinedBpL1RawTLogDerivativeModel η ≤ tBound)
    (hinv : negInvEta ≤ negInvBound)
    (hbudget : 2 * tBound + negInvBound ≤ -1) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) + negInvEta ≤ -1 := by
  have ht :
      bifrCombinedBpL1RawTLogDerivativeModel η + bifrRealDigamma (1 - η) ≤
        tBound := by
    have hη0 : 0 ≤ η := le_of_lt hη
    have hη1 : η < 1 := by linarith
    exact tLogDerivative_le_of_rawLogDerivative_le hη0 hη1 hraw
  exact l1OverPLogDerivative_le_neg_one_of_box_bounds
    (bifrCombinedBpL1LogADerivative_nonpos_direct hη hhi)
    ht hinv hbudget

/-- Split the closed raw-`T` model bound into a logarithm bound and a rational
reciprocal-factor bound.

This is the small scalar seam for the remaining five eta boxes: prove
`-log η` from the lower dyadic endpoint, prove the reciprocal factor from the
upper dyadic endpoint, then add the two budgets. -/
theorem bifrCombinedBpL1RawTLogDerivativeModel_le_of_parts
    {η negLogBound recipBound tBound : ℝ}
    (hlog : -Real.log η ≤ negLogBound)
    (hrecip : ((8 - 7 * η) * (1 - η))⁻¹ ≤ recipBound)
    (hbudget : negLogBound - 1 + recipBound ≤ tBound) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ tBound := by
  unfold bifrCombinedBpL1RawTLogDerivativeModel
  linarith

/-- If the reciprocal denominator has a positive lower bound, then its inverse
has the corresponding upper bound. -/
theorem bifrRawTReciprocal_le_of_den_ge
    {η denLower : ℝ}
    (hpos : 0 < denLower)
    (hden : denLower ≤ (8 - 7 * η) * (1 - η)) :
    ((8 - 7 * η) * (1 - η))⁻¹ ≤ denLower⁻¹ := by
  exact (inv_le_inv₀ (hpos.trans_le hden) hpos).2 hden

/-- Dyadic lower endpoint bound for the `-log η` part of the raw-`T` model.

If \(2^{-k}\le\eta\), then \(-\log\eta\le k\log 2\).  The five Route B
eta boxes use this with `k = 12, 6, 5, 4, 3`. -/
theorem neg_log_le_nat_mul_log_two_of_zpow_le
    {η : ℝ} {k : ℕ}
    (hlo : (2 : ℝ) ^ (-(k : ℤ)) ≤ η) :
    -Real.log η ≤ (k : ℝ) * Real.log 2 := by
  have hlowpos : 0 < (2 : ℝ) ^ (-(k : ℤ)) := zpow_pos (by norm_num) _
  have hlog := Real.log_le_log hlowpos hlo
  have hlowlog :
      Real.log ((2 : ℝ) ^ (-(k : ℤ))) = -(k : ℝ) * Real.log 2 := by
    rw [Real.log_zpow]
    norm_num
  rw [hlowlog] at hlog
  linarith

/-- The raw-`T` reciprocal denominator
`(8 - 7η) * (1 - η)` is decreasing on the theorem interval.  Therefore an
upper endpoint `hi` gives a denominator lower bound for the whole box. -/
theorem bifrRawTDen_ge_of_le_right_endpoint
    {η hi : ℝ}
    (hηhi : η ≤ hi) (hhi : hi ≤ (1 / 4 : ℝ)) :
    (8 - 7 * hi) * (1 - hi) ≤ (8 - 7 * η) * (1 - η) := by
  have hdiff_nonneg : 0 ≤ hi - η := by linarith
  have hfactor_nonneg : 0 ≤ 15 - 7 * (η + hi) := by
    nlinarith
  have hprod : 0 ≤ (hi - η) * (15 - 7 * (η + hi)) :=
    mul_nonneg hdiff_nonneg hfactor_nonneg
  nlinarith [hprod]

/-- Reciprocal bound for the raw-`T` denominator from a dyadic box right
endpoint. -/
theorem bifrRawTReciprocal_le_of_le_right_endpoint
    {η hi : ℝ}
    (hηhi : η ≤ hi) (hhi : hi ≤ (1 / 4 : ℝ))
    (hpos : 0 < (8 - 7 * hi) * (1 - hi)) :
    ((8 - 7 * η) * (1 - η))⁻¹ ≤ ((8 - 7 * hi) * (1 - hi))⁻¹ :=
  bifrRawTReciprocal_le_of_den_ge hpos
    (bifrRawTDen_ge_of_le_right_endpoint hηhi hhi)

/-- Dyadic-box consumer for the closed raw-`T` derivative model.

This packages the proof shape for each remaining Route B box:

* `2^{-k} ≤ η` controls `-log η`;
* `η ≤ hi` controls the reciprocal denominator by its right endpoint;
* the two scalar budgets imply the desired raw-`T` upper bound. -/
theorem bifrCombinedBpL1RawTLogDerivativeModel_le_of_dyadic_box
    {η hi negLogBound recipBound tBound : ℝ} {k : ℕ}
    (hlo : (2 : ℝ) ^ (-(k : ℤ)) ≤ η)
    (hηhi : η ≤ hi) (hhi : hi ≤ (1 / 4 : ℝ))
    (hdenpos : 0 < (8 - 7 * hi) * (1 - hi))
    (hlogBudget : (k : ℝ) * Real.log 2 ≤ negLogBound)
    (hrecipBudget : ((8 - 7 * hi) * (1 - hi))⁻¹ ≤ recipBound)
    (hbudget : negLogBound - 1 + recipBound ≤ tBound) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ tBound :=
  bifrCombinedBpL1RawTLogDerivativeModel_le_of_parts
    ((neg_log_le_nat_mul_log_two_of_zpow_le hlo).trans hlogBudget)
    ((bifrRawTReciprocal_le_of_le_right_endpoint hηhi hhi hdenpos).trans
      hrecipBudget)
    hbudget

/-- First Route B raw-`T` box:
`η ∈ [2^-12, 1/64]` implies the raw model is at most `8`. -/
theorem bifrRawTModel_le_eight_on_box₁ {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ)) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ 8 :=
  bifrCombinedBpL1RawTLogDerivativeModel_le_of_dyadic_box
    (hi := (1 / 64 : ℝ)) (negLogBound := (42 / 5 : ℝ))
    (recipBound := (1 / 7 : ℝ)) hlo hhi (by norm_num) (by norm_num)
    (le_of_lt (by nlinarith [Real.log_two_lt_d9])) (by norm_num) (by norm_num)

/-- Second Route B raw-`T` box:
`η ∈ [2^-6, 1/32]` implies the raw model is at most `4`. -/
theorem bifrRawTModel_le_four_on_box₂ {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ)) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ 4 :=
  bifrCombinedBpL1RawTLogDerivativeModel_le_of_dyadic_box
    (hi := (1 / 32 : ℝ)) (negLogBound := (21 / 5 : ℝ))
    (recipBound := (1 / 7 : ℝ)) hlo hhi (by norm_num) (by norm_num)
    (le_of_lt (by nlinarith [Real.log_two_lt_d9])) (by norm_num) (by norm_num)

/-- Third Route B raw-`T` box:
`η ∈ [2^-5, 1/16]` implies the raw model is at most `3`. -/
theorem bifrRawTModel_le_three_on_box₃ {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ)) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ 3 :=
  bifrCombinedBpL1RawTLogDerivativeModel_le_of_dyadic_box
    (hi := (1 / 16 : ℝ)) (negLogBound := (7 / 2 : ℝ))
    (recipBound := (1 / 6 : ℝ)) hlo hhi (by norm_num) (by norm_num)
    (le_of_lt (by nlinarith [Real.log_two_lt_d9])) (by norm_num) (by norm_num)

/-- Fourth Route B raw-`T` box:
`η ∈ [2^-4, 1/8]` implies the raw model is at most `2`. -/
theorem bifrRawTModel_le_two_on_box₄ {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ)) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ 2 :=
  bifrCombinedBpL1RawTLogDerivativeModel_le_of_dyadic_box
    (hi := (1 / 8 : ℝ)) (negLogBound := (14 / 5 : ℝ))
    (recipBound := (1 / 5 : ℝ)) hlo hhi (by norm_num) (by norm_num)
    (le_of_lt (by nlinarith [Real.log_two_lt_d9])) (by norm_num) (by norm_num)

/-- Fifth Route B raw-`T` box:
`η ∈ [2^-3, 1/4]` implies the raw model is at most `3/2`. -/
theorem bifrRawTModel_le_three_halves_on_box₅ {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ)) :
    bifrCombinedBpL1RawTLogDerivativeModel η ≤ (3 / 2 : ℝ) :=
  bifrCombinedBpL1RawTLogDerivativeModel_le_of_dyadic_box
    (hi := (1 / 4 : ℝ)) (negLogBound := (21 / 10 : ℝ))
    (recipBound := (2 / 5 : ℝ)) hlo hhi (by norm_num) (by norm_num)
    (le_of_lt (by nlinarith [Real.log_two_lt_d9])) (by norm_num) (by norm_num)

/-- Right-endpoint bound for the `-1/η` term on a positive eta box. -/
theorem neg_inv_le_neg_inv_of_le_right_endpoint
    {η hi : ℝ} (hη : 0 < η) (hηhi : η ≤ hi) :
    -η⁻¹ ≤ -hi⁻¹ := by
  have hhi_pos : 0 < hi := hη.trans_le hηhi
  have hinv : hi⁻¹ ≤ η⁻¹ := (inv_le_inv₀ hhi_pos hη).2 hηhi
  linarith

/-- Full first Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-12, 1/64]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₁
    {η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model
    hη (hhi.trans (by norm_num)) hlog hbox
    (bifrRawTModel_le_eight_on_box₁ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Direct first Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-12, 1/64]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₁_direct
    {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ)) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_direct_logA_rawT_model
    hη (hhi.trans (by norm_num))
    (bifrRawTModel_le_eight_on_box₁ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Full second Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-6, 1/32]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₂
    {η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model
    hη (hhi.trans (by norm_num)) hlog hbox
    (bifrRawTModel_le_four_on_box₂ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Direct second Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-6, 1/32]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₂_direct
    {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ)) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_direct_logA_rawT_model
    hη (hhi.trans (by norm_num))
    (bifrRawTModel_le_four_on_box₂ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Full third Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-5, 1/16]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₃
    {η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model
    hη (hhi.trans (by norm_num)) hlog hbox
    (bifrRawTModel_le_three_on_box₃ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Direct third Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-5, 1/16]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₃_direct
    {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ)) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_direct_logA_rawT_model
    hη (hhi.trans (by norm_num))
    (bifrRawTModel_le_three_on_box₃ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Full fourth Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-4, 1/8]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₄
    {η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model
    hη (hhi.trans (by norm_num)) hlog hbox
    (bifrRawTModel_le_two_on_box₄ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Direct fourth Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-4, 1/8]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₄_direct
    {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ)) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_direct_logA_rawT_model
    hη (hhi.trans (by norm_num))
    (bifrRawTModel_le_two_on_box₄ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Full fifth Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-3, 1/4]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₅
    {η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_certificate_box_rawT_model
    hη hhi hlog hbox
    (bifrRawTModel_le_three_halves_on_box₅ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Direct fifth Route B `ell_1 / p` log-derivative box:
`η ∈ [2^-3, 1/4]`. -/
theorem l1OverPLogDerivative_le_neg_one_on_box₅_direct
    {η : ℝ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ)) :
    bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹ ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact l1OverPLogDerivative_le_neg_one_of_direct_logA_rawT_model
    hη hhi
    (bifrRawTModel_le_three_halves_on_box₅ hlo hhi)
    (neg_inv_le_neg_inv_of_le_right_endpoint hη hhi)
    (by norm_num)

/-- Convert a proved Route B `ell_1 / p` log-derivative box into the
coefficient derivative bound `≤ -100`. -/
theorem l1OverPLeadingDerivative_le_neg_of_coeff_and_box_log_deriv
    {coeff logDeriv : ℝ}
    (hcoeff : 100 ≤ coeff)
    (hlogDeriv : logDeriv ≤ -1) :
    coeff * logDeriv ≤ -100 :=
  l1OverPLeadingDerivative_le_neg_of_coeff_and_log_deriv hcoeff hlogDeriv

/-- First full Route B `ell_1 / p` derivative box:
`η ∈ [2^-12, 1/64]`. -/
theorem l1OverPLeadingDerivative_le_neg_on_box₁
    {coeff η logUpper : ℝ} {N : ℕ}
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -100 :=
  l1OverPLeadingDerivative_le_neg_of_coeff_and_box_log_deriv hcoeff
    (l1OverPLogDerivative_le_neg_one_on_box₁ hlo hhi hlog hbox)

/-- Second full Route B `ell_1 / p` derivative box:
`η ∈ [2^-6, 1/32]`. -/
theorem l1OverPLeadingDerivative_le_neg_on_box₂
    {coeff η logUpper : ℝ} {N : ℕ}
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -100 :=
  l1OverPLeadingDerivative_le_neg_of_coeff_and_box_log_deriv hcoeff
    (l1OverPLogDerivative_le_neg_one_on_box₂ hlo hhi hlog hbox)

/-- Third full Route B `ell_1 / p` derivative box:
`η ∈ [2^-5, 1/16]`. -/
theorem l1OverPLeadingDerivative_le_neg_on_box₃
    {coeff η logUpper : ℝ} {N : ℕ}
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -100 :=
  l1OverPLeadingDerivative_le_neg_of_coeff_and_box_log_deriv hcoeff
    (l1OverPLogDerivative_le_neg_one_on_box₃ hlo hhi hlog hbox)

/-- Fourth full Route B `ell_1 / p` derivative box:
`η ∈ [2^-4, 1/8]`. -/
theorem l1OverPLeadingDerivative_le_neg_on_box₄
    {coeff η logUpper : ℝ} {N : ℕ}
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -100 :=
  l1OverPLeadingDerivative_le_neg_of_coeff_and_box_log_deriv hcoeff
    (l1OverPLogDerivative_le_neg_one_on_box₄ hlo hhi hlog hbox)

/-- Fifth full Route B `ell_1 / p` derivative box:
`η ∈ [2^-3, 1/4]`. -/
theorem l1OverPLeadingDerivative_le_neg_on_box₅
    {coeff η logUpper : ℝ} {N : ℕ}
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -100 :=
  l1OverPLeadingDerivative_le_neg_of_coeff_and_box_log_deriv hcoeff
    (l1OverPLogDerivative_le_neg_one_on_box₅ hlo hhi hlog hbox)

/-- First Route B combined leading-derivative box:
`η ∈ [2^-12, 1/64]`. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₁
    {singleDeriv coeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) < 0 :=
  combinedBpLeadingDerivative_le_neg_of_component_bounds hsingle
    (l1OverPLeadingDerivative_le_neg_on_box₁ hcoeff hlo hhi hlog hbox)

/-- Second Route B combined leading-derivative box:
`η ∈ [2^-6, 1/32]`. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₂
    {singleDeriv coeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) < 0 :=
  combinedBpLeadingDerivative_le_neg_of_component_bounds hsingle
    (l1OverPLeadingDerivative_le_neg_on_box₂ hcoeff hlo hhi hlog hbox)

/-- Third Route B combined leading-derivative box:
`η ∈ [2^-5, 1/16]`. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₃
    {singleDeriv coeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) < 0 :=
  combinedBpLeadingDerivative_le_neg_of_component_bounds hsingle
    (l1OverPLeadingDerivative_le_neg_on_box₃ hcoeff hlo hhi hlog hbox)

/-- Fourth Route B combined leading-derivative box:
`η ∈ [2^-4, 1/8]`. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₄
    {singleDeriv coeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) < 0 :=
  combinedBpLeadingDerivative_le_neg_of_component_bounds hsingle
    (l1OverPLeadingDerivative_le_neg_on_box₄ hcoeff hlo hhi hlog hbox)

/-- Fifth Route B combined leading-derivative box:
`η ∈ [2^-3, 1/4]`. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₅
    {singleDeriv coeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hcoeff : 100 ≤ coeff)
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + coeff * (bifrCombinedBpL1LogADerivative η +
      2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
        bifrRealDigamma (1 - η)) - η⁻¹) < 0 :=
  combinedBpLeadingDerivative_le_neg_of_component_bounds hsingle
    (l1OverPLeadingDerivative_le_neg_on_box₅ hcoeff hlo hhi hlog hbox)

/-- Scalar lower-bound consumer for the Route B `ell_1 / p` leading
coefficient.

If `aLower ≤ A(η)`, `tLower ≤ T(η)`, and `η ≤ etaUpper`, with the scalar budget
`100 * etaUpper ≤ aLower * tLower^2`, then
`A(η) * T(η)^2 / η ≥ 100`.  This is the theorem-facing endpoint for boxwise
coefficient-lower certificates. -/
theorem l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    {η aCoeff tCoeff aLower tLower etaUpper : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ etaUpper)
    (haLower : 0 ≤ aLower)
    (htLower : 0 ≤ tLower)
    (ha : aLower ≤ aCoeff)
    (ht : tLower ≤ tCoeff)
    (hbudget : 100 * etaUpper ≤ aLower * tLower ^ 2) :
    100 ≤ aCoeff * tCoeff ^ 2 / η := by
  have hη_nonneg : 0 ≤ η := le_of_lt hη
  have haCoeff_nonneg : 0 ≤ aCoeff := haLower.trans ha
  have htCoeff_nonneg : 0 ≤ tCoeff := htLower.trans ht
  have ht_sq : tLower ^ 2 ≤ tCoeff ^ 2 := by
    nlinarith
  have hprod : aLower * tLower ^ 2 ≤ aCoeff * tCoeff ^ 2 := by
    exact mul_le_mul ha ht_sq (sq_nonneg tLower) haCoeff_nonneg
  have hbudget' : 100 * etaUpper ≤ aCoeff * tCoeff ^ 2 :=
    hbudget.trans hprod
  have hstep : 100 * η ≤ aCoeff * tCoeff ^ 2 := by
    calc
      100 * η ≤ 100 * etaUpper := by nlinarith
      _ ≤ aCoeff * tCoeff ^ 2 := hbudget'
  exact (le_div_iff₀ hη).2 hstep

/-- Model-specialized lower-bound consumer for the Route B `ell_1 / p`
leading coefficient.

This is the handoff that future gamma/power endpoint certificates should feed:
lower bounds on the actual `A(η)` and `T(η)` models imply the coefficient
bound \(A(\eta)T(\eta)^2/\eta\ge100\). -/
theorem l1OverPModelCoefficient_ge_hundred_of_factor_lower_bounds
    {η aLower tLower etaUpper : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ etaUpper)
    (haLower : 0 ≤ aLower)
    (htLower : 0 ≤ tLower)
    (ha : aLower ≤ bifrCombinedBpALeadingModel η)
    (ht : tLower ≤ bifrCombinedBpTLeadingModel η)
    (hbudget : 100 * etaUpper ≤ aLower * tLower ^ 2) :
    100 ≤
      bifrCombinedBpALeadingModel η * bifrCombinedBpTLeadingModel η ^ 2 / η :=
  l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    hη hηhi haLower htLower ha ht hbudget

/-- Generic combined Route B leading-derivative consumer using the actual
single-leading route and the actual \(A,T\)-factor models.

This theorem is intentionally still certificate-facing: the remaining inputs
are lower bounds for the \(A,T\)-models, the rational single-log model bound,
and a box/certificate proof of the `ell_1 / p` log-derivative bound. -/
theorem combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    {singleDeriv singleLogDeriv η l1LogDeriv aLower tLower etaUpper : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ (1 / 4 : ℝ))
    (hηupper : η ≤ etaUpper)
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (haLower : 0 ≤ aLower)
    (htLower : 0 ≤ tLower)
    (ha : aLower ≤ bifrCombinedBpALeadingModel η)
    (ht : tLower ≤ bifrCombinedBpTLeadingModel η)
    (hbudget : 100 * etaUpper ≤ aLower * tLower ^ 2)
    (hl1log : l1LogDeriv ≤ -1) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
            bifrCombinedBpTLeadingModel η ^ 2 / η) * l1LogDeriv ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
            bifrCombinedBpTLeadingModel η ^ 2 / η) * l1LogDeriv < 0 := by
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη hηhi hsingleDeriv hsingleLog hquarter
  have hcoeff :
      100 ≤
        bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η :=
    l1OverPModelCoefficient_ge_hundred_of_factor_lower_bounds
      hη hηupper haLower htLower ha ht hbudget
  exact combinedBpLeadingDerivative_le_neg_of_component_bounds hsingle
    (l1OverPLeadingDerivative_le_neg_of_coeff_and_log_deriv hcoeff hl1log)

/-- Direct-coefficient version of the practical combined `b=p` leading
derivative consumer.

This is the preferred handoff for the reflection route.  It removes the old
boxwise \(A\)- and \(T\)-factor lower-bound inputs: once a direct proof or
certificate gives
`2 ≤ A(η) * T(η)^2 / η`, the already-proved single route and
`ell_1/p` log-derivative bound imply that the combined leading derivative is
strictly negative. -/
theorem combinedBpLeadingDerivative_lt_zero_of_model_coeff_and_single_route
    {singleDeriv singleLogDeriv η l1LogDeriv : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hcoeff :
      2 ≤ bifrCombinedBpALeadingModel η *
        bifrCombinedBpTLeadingModel η ^ 2 / η)
    (hl1log : l1LogDeriv ≤ -1) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
            bifrCombinedBpTLeadingModel η ^ 2 / η) * l1LogDeriv < 0 := by
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη hηhi hsingleDeriv hsingleLog
      (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le hηhi)
  exact combinedBpLeadingDerivative_lt_zero_of_coeff_two_and_log
    hsingle hcoeff hl1log

/-- Quantitative version of the direct-coefficient Route B consumer.

The same inputs used for strict negativity actually give the stronger bound
`≤ -1`, because the single branch contributes at most `1`, while the
`ell_1/p` branch contributes at most `-2`.  This is the leading-gap handoff
needed by the exact adjacent combined-envelope transfer. -/
theorem combinedBpLeadingDerivative_le_neg_one_of_model_coeff_and_single_route
    {singleDeriv singleLogDeriv η l1LogDeriv : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hcoeff :
      2 ≤ bifrCombinedBpALeadingModel η *
        bifrCombinedBpTLeadingModel η ^ 2 / η)
    (hl1log : l1LogDeriv ≤ -1) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
            bifrCombinedBpTLeadingModel η ^ 2 / η) * l1LogDeriv ≤ -1 := by
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη hηhi hsingleDeriv hsingleLog
      (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le hηhi)
  have hcoeff_nonneg :
      0 ≤ bifrCombinedBpALeadingModel η *
        bifrCombinedBpTLeadingModel η ^ 2 / η := by
    linarith
  exact combinedBpLeadingDerivative_le_margin_of_single_and_l1_log
    hsingle hcoeff_nonneg hl1log (by linarith)

/-- Direct Route B combined derivative consumer.

This is the theorem-facing endpoint for the current practical `b=p` leading
coefficient route: the coefficient lower bound is now proved internally from
reflection, the beta-tail part of \(T\), and the crude sinc lower bound. -/
theorem combinedBpLeadingDerivative_lt_zero_of_direct_coeff_and_single_route
    {singleDeriv singleLogDeriv η l1LogDeriv : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hl1log : l1LogDeriv ≤ -1) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
            bifrCombinedBpTLeadingModel η ^ 2 / η) * l1LogDeriv < 0 :=
  combinedBpLeadingDerivative_lt_zero_of_model_coeff_and_single_route
    hη hηhi hsingleDeriv hsingleLog
    (l1OverPModelCoefficient_ge_two_direct hη hηhi) hl1log

/-- Direct Route B combined derivative consumer with quantitative margin
`≤ -1`. -/
theorem combinedBpLeadingDerivative_le_neg_one_of_direct_coeff_and_single_route
    {singleDeriv singleLogDeriv η l1LogDeriv : ℝ}
    (hη : 0 < η)
    (hηhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hl1log : l1LogDeriv ≤ -1) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
            bifrCombinedBpTLeadingModel η ^ 2 / η) * l1LogDeriv ≤ -1 :=
  combinedBpLeadingDerivative_le_neg_one_of_model_coeff_and_single_route
    hη hηhi hsingleDeriv hsingleLog
    (l1OverPModelCoefficient_ge_two_direct hη hηhi) hl1log

/-- First Route B coefficient lower box:
`η ∈ (0, 1/64]`, `A ≥ 2/5`, and `T ≥ 8` imply
`C_{ell_1/p} ≥ 100`. -/
theorem l1OverPCoefficient_ge_hundred_on_box₁
    {η aCoeff tCoeff : ℝ}
    (hη : 0 < η) (hhi : η ≤ (1 / 64 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff) :
    100 ≤ aCoeff * tCoeff ^ 2 / η :=
  l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    hη hhi (by norm_num) (by norm_num) ha ht (by norm_num)

/-- Second Route B coefficient lower box:
`η ∈ (0, 1/32]`, `A ≥ 2/5`, and `T ≥ 8` imply
`C_{ell_1/p} ≥ 100`. -/
theorem l1OverPCoefficient_ge_hundred_on_box₂
    {η aCoeff tCoeff : ℝ}
    (hη : 0 < η) (hhi : η ≤ (1 / 32 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff) :
    100 ≤ aCoeff * tCoeff ^ 2 / η :=
  l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    hη hhi (by norm_num) (by norm_num) ha ht (by norm_num)

/-- Third Route B coefficient lower box:
`η ∈ (0, 1/16]`, `A ≥ 3/8`, and `T ≥ 8` imply
`C_{ell_1/p} ≥ 100`. -/
theorem l1OverPCoefficient_ge_hundred_on_box₃
    {η aCoeff tCoeff : ℝ}
    (hη : 0 < η) (hhi : η ≤ (1 / 16 : ℝ))
    (ha : (3 / 8 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff) :
    100 ≤ aCoeff * tCoeff ^ 2 / η :=
  l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    hη hhi (by norm_num) (by norm_num) ha ht (by norm_num)

/-- Fourth Route B coefficient lower box:
`η ∈ (0, 1/8]`, `A ≥ 1/3`, and `T ≥ 9` imply
`C_{ell_1/p} ≥ 100`. -/
theorem l1OverPCoefficient_ge_hundred_on_box₄
    {η aCoeff tCoeff : ℝ}
    (hη : 0 < η) (hhi : η ≤ (1 / 8 : ℝ))
    (ha : (1 / 3 : ℝ) ≤ aCoeff)
    (ht : (9 : ℝ) ≤ tCoeff) :
    100 ≤ aCoeff * tCoeff ^ 2 / η :=
  l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    hη hhi (by norm_num) (by norm_num) ha ht (by norm_num)

/-- Fifth Route B coefficient lower box:
`η ∈ (0, 1/4]`, `A ≥ 3/10`, and `T ≥ 19/2` imply
`C_{ell_1/p} ≥ 100`. -/
theorem l1OverPCoefficient_ge_hundred_on_box₅
    {η aCoeff tCoeff : ℝ}
    (hη : 0 < η) (hhi : η ≤ (1 / 4 : ℝ))
    (ha : (3 / 10 : ℝ) ≤ aCoeff)
    (ht : (19 / 2 : ℝ) ≤ tCoeff) :
    100 ≤ aCoeff * tCoeff ^ 2 / η :=
  l1OverPCoefficient_ge_hundred_of_factor_lower_bounds
    hη hhi (by norm_num) (by norm_num) ha ht (by norm_num)

/-- First Route B combined derivative box with factor lower bounds inlined. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₁_of_factor_bounds
    {singleDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_on_box₁ hsingle
    (l1OverPCoefficient_ge_hundred_on_box₁ hη hhi ha ht) hlo hhi hlog hbox

/-- Second Route B combined derivative box with factor lower bounds inlined. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₂_of_factor_bounds
    {singleDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_on_box₂ hsingle
    (l1OverPCoefficient_ge_hundred_on_box₂ hη hhi ha ht) hlo hhi hlog hbox

/-- Third Route B combined derivative box with factor lower bounds inlined. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₃_of_factor_bounds
    {singleDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (ha : (3 / 8 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_on_box₃ hsingle
    (l1OverPCoefficient_ge_hundred_on_box₃ hη hhi ha ht) hlo hhi hlog hbox

/-- Fourth Route B combined derivative box with factor lower bounds inlined. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₄_of_factor_bounds
    {singleDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (ha : (1 / 3 : ℝ) ≤ aCoeff)
    (ht : (9 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_on_box₄ hsingle
    (l1OverPCoefficient_ge_hundred_on_box₄ hη hhi ha ht) hlo hhi hlog hbox

/-- Fifth Route B combined derivative box with factor lower bounds inlined. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₅_of_factor_bounds
    {singleDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hsingle : singleDeriv ≤ 1)
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (ha : (3 / 10 : ℝ) ≤ aCoeff)
    (ht : (19 / 2 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_on_box₅ hsingle
    (l1OverPCoefficient_ge_hundred_on_box₅ hη hhi ha ht) hlo hhi hlog hbox

/-- First Route B combined derivative box with the single-leading branch routed
through the sinc/cotangent model theorem.

The remaining single-branch numerical input is the rational certificate
`bifrSingleLogDerivativeUpperModel η ≤ 1/4`; the trigonometric and π bounds are
kernel-checked by `singleLeadingDerivative_le_one_on_route`. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₁_of_factor_bounds_and_single_route
    {singleDeriv singleLogDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη (hhi.trans (by norm_num))
      hsingleDeriv hsingleLog hquarter
  exact combinedBpLeadingDerivative_le_neg_on_box₁_of_factor_bounds
    hsingle hlo hhi ha ht hlog hbox

/-- Second Route B combined derivative box with the single-leading branch routed
through the sinc/cotangent model theorem. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₂_of_factor_bounds_and_single_route
    {singleDeriv singleLogDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη (hhi.trans (by norm_num))
      hsingleDeriv hsingleLog hquarter
  exact combinedBpLeadingDerivative_le_neg_on_box₂_of_factor_bounds
    hsingle hlo hhi ha ht hlog hbox

/-- Third Route B combined derivative box with the single-leading branch routed
through the sinc/cotangent model theorem. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₃_of_factor_bounds_and_single_route
    {singleDeriv singleLogDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (3 / 8 : ℝ) ≤ aCoeff)
    (ht : (8 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη (hhi.trans (by norm_num))
      hsingleDeriv hsingleLog hquarter
  exact combinedBpLeadingDerivative_le_neg_on_box₃_of_factor_bounds
    hsingle hlo hhi ha ht hlog hbox

/-- Fourth Route B combined derivative box with the single-leading branch routed
through the sinc/cotangent model theorem. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₄_of_factor_bounds_and_single_route
    {singleDeriv singleLogDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (1 / 3 : ℝ) ≤ aCoeff)
    (ht : (9 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη (hhi.trans (by norm_num))
      hsingleDeriv hsingleLog hquarter
  exact combinedBpLeadingDerivative_le_neg_on_box₄_of_factor_bounds
    hsingle hlo hhi ha ht hlog hbox

/-- Fifth Route B combined derivative box with the single-leading branch routed
through the sinc/cotangent model theorem. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₅_of_factor_bounds_and_single_route
    {singleDeriv singleLogDeriv aCoeff tCoeff η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (3 / 10 : ℝ) ≤ aCoeff)
    (ht : (19 / 2 : ℝ) ≤ tCoeff)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
    singleDeriv + (aCoeff * tCoeff ^ 2 / η) *
      (bifrCombinedBpL1LogADerivative η +
        2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
          bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  have hsingle : singleDeriv ≤ 1 :=
    singleLeadingDerivative_le_one_on_route hη hhi hsingleDeriv hsingleLog hquarter
  exact combinedBpLeadingDerivative_le_neg_on_box₅_of_factor_bounds
    hsingle hlo hhi ha ht hlog hbox

/-- First full Route B combined derivative box using the named \(A,T\)-factor
models and the single-leading route. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₁_of_model_bounds_and_single_route
    {singleDeriv singleLogDeriv η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (8 : ℝ) ≤ bifrCombinedBpTLeadingModel η)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog hquarter
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₁ hlo hhi hlog hbox)

/-- Second full Route B combined derivative box using the named \(A,T\)-factor
models and the single-leading route. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₂_of_model_bounds_and_single_route
    {singleDeriv singleLogDeriv η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (2 / 5 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (8 : ℝ) ≤ bifrCombinedBpTLeadingModel η)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog hquarter
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₂ hlo hhi hlog hbox)

/-- Third full Route B combined derivative box using the named \(A,T\)-factor
models and the single-leading route. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₃_of_model_bounds_and_single_route
    {singleDeriv singleLogDeriv η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (3 / 8 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (8 : ℝ) ≤ bifrCombinedBpTLeadingModel η)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog hquarter
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₃ hlo hhi hlog hbox)

/-- Fourth full Route B combined derivative box using the named \(A,T\)-factor
models and the single-leading route. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₄_of_model_bounds_and_single_route
    {singleDeriv singleLogDeriv η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (1 / 3 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (9 : ℝ) ≤ bifrCombinedBpTLeadingModel η)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog hquarter
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₄ hlo hhi hlog hbox)

/-- Fifth full Route B combined derivative box using the named \(A,T\)-factor
models and the single-leading route. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₅_of_model_bounds_and_single_route
    {singleDeriv singleLogDeriv η logUpper : ℝ} {N : ℕ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (hquarter : bifrSingleLogDerivativeUpperModel η ≤ (1 / 4 : ℝ))
    (ha : (3 / 10 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (19 / 2 : ℝ) ≤ bifrCombinedBpTLeadingModel η)
    (hlog : Real.log (η + 1 / 2) ≤ logUpper)
    (hbox : logUpper ≤ -(3 / 5 : ℝ) + bifrDigammaOnePlusEtaSeriesPartial η N) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη hhi hhi hsingleDeriv hsingleLog hquarter
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₅ hlo hhi hlog hbox)

/-- First Route B combined derivative box using the named \(A,T\)-factor
models, the single-leading route, and the direct Lean half-shift proof for the
`ell_1 / p` log-derivative seam.

This is the preferred current Route B endpoint for the first dyadic box: it no
longer imports a half-shift `logUpper` certificate. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₁_of_model_bounds_and_single_route_direct
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (ha : (2 / 5 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (8 : ℝ) ≤ bifrCombinedBpTLeadingModel η) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog
    (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le
      (hhi.trans (by norm_num)))
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₁_direct hlo hhi)

/-- Second Route B combined derivative box using named \(A,T\)-factor models
and the direct Lean `ell_1 / p` log-derivative seam. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₂_of_model_bounds_and_single_route_direct
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (ha : (2 / 5 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (8 : ℝ) ≤ bifrCombinedBpTLeadingModel η) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog
    (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le
      (hhi.trans (by norm_num)))
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₂_direct hlo hhi)

/-- Third Route B combined derivative box using named \(A,T\)-factor models
and the direct Lean `ell_1 / p` log-derivative seam. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₃_of_model_bounds_and_single_route_direct
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (ha : (3 / 8 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (8 : ℝ) ≤ bifrCombinedBpTLeadingModel η) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog
    (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le
      (hhi.trans (by norm_num)))
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₃_direct hlo hhi)

/-- Fourth Route B combined derivative box using named \(A,T\)-factor models
and the direct Lean `ell_1 / p` log-derivative seam. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₄_of_model_bounds_and_single_route_direct
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (ha : (1 / 3 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (9 : ℝ) ≤ bifrCombinedBpTLeadingModel η) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη (hhi.trans (by norm_num)) hhi hsingleDeriv hsingleLog
    (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le
      (hhi.trans (by norm_num)))
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₄_direct hlo hhi)

/-- Fifth Route B combined derivative box using named \(A,T\)-factor models
and the direct Lean `ell_1 / p` log-derivative seam. -/
theorem combinedBpLeadingDerivative_le_neg_on_box₅_of_model_bounds_and_single_route_direct
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η))
    (ha : (3 / 10 : ℝ) ≤ bifrCombinedBpALeadingModel η)
    (ht : (19 / 2 : ℝ) ≤ bifrCombinedBpTLeadingModel η) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -99 ∧
      singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_of_model_factor_bounds_and_single_route
    hη hhi hhi hsingleDeriv hsingleLog
    (bifrSingleLogDerivativeUpperModel_le_quarter_on_route hη.le hhi)
    (by norm_num) (by norm_num) ha ht (by norm_num)
    (l1OverPLogDerivative_le_neg_one_on_box₅_direct hlo hhi)

/-- First Route B combined derivative box with no imported coefficient lower
bounds.  The coefficient budget is supplied by the direct reflection/sinc
route. -/
theorem combinedBpLeadingDerivative_lt_zero_on_box₁_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_lt_zero_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₁_direct hlo hhi)

/-- Second Route B combined derivative box with no imported coefficient lower
bounds. -/
theorem combinedBpLeadingDerivative_lt_zero_on_box₂_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_lt_zero_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₂_direct hlo hhi)

/-- Third Route B combined derivative box with no imported coefficient lower
bounds. -/
theorem combinedBpLeadingDerivative_lt_zero_on_box₃_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_lt_zero_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₃_direct hlo hhi)

/-- Fourth Route B combined derivative box with no imported coefficient lower
bounds. -/
theorem combinedBpLeadingDerivative_lt_zero_on_box₄_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_lt_zero_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₄_direct hlo hhi)

/-- Fifth Route B combined derivative box with no imported coefficient lower
bounds. -/
theorem combinedBpLeadingDerivative_lt_zero_on_box₅_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) < 0 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_lt_zero_of_direct_coeff_and_single_route
    hη hhi hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₅_direct hlo hhi)

/-- First Route B combined derivative box with direct coefficient route and
quantitative margin `≤ -1`. -/
theorem combinedBpLeadingDerivative_le_neg_one_on_box₁_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(12 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 64 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_one_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₁_direct hlo hhi)

/-- Second Route B combined derivative box with direct coefficient route and
quantitative margin `≤ -1`. -/
theorem combinedBpLeadingDerivative_le_neg_one_on_box₂_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(6 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 32 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_one_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₂_direct hlo hhi)

/-- Third Route B combined derivative box with direct coefficient route and
quantitative margin `≤ -1`. -/
theorem combinedBpLeadingDerivative_le_neg_one_on_box₃_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(5 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 16 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_one_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₃_direct hlo hhi)

/-- Fourth Route B combined derivative box with direct coefficient route and
quantitative margin `≤ -1`. -/
theorem combinedBpLeadingDerivative_le_neg_one_on_box₄_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(4 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 8 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_one_of_direct_coeff_and_single_route
    hη (hhi.trans (by norm_num)) hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₄_direct hlo hhi)

/-- Fifth Route B combined derivative box with direct coefficient route and
quantitative margin `≤ -1`. -/
theorem combinedBpLeadingDerivative_le_neg_one_on_box₅_direct_coeff
    {singleDeriv singleLogDeriv η : ℝ}
    (hlo : (2 : ℝ) ^ (-(3 : ℤ)) ≤ η)
    (hhi : η ≤ (1 / 4 : ℝ))
    (hsingleDeriv :
      singleDeriv = bifrSingleLeadingCoefficientModel η * singleLogDeriv)
    (hsingleLog :
      singleLogDeriv =
        2 * Real.pi * Real.cot (Real.pi * η) - 2 / η -
          7 / (4 - 7 * η) + 2 / (1 - 2 * η)) :
    singleDeriv +
        (bifrCombinedBpALeadingModel η *
          bifrCombinedBpTLeadingModel η ^ 2 / η) *
          (bifrCombinedBpL1LogADerivative η +
            2 * (bifrCombinedBpL1RawTLogDerivativeModel η +
              bifrRealDigamma (1 - η)) - η⁻¹) ≤ -1 := by
  have hη : 0 < η := (zpow_pos (by norm_num : (0 : ℝ) < 2) _).trans_le hlo
  exact combinedBpLeadingDerivative_le_neg_one_of_direct_coeff_and_single_route
    hη hhi hsingleDeriv hsingleLog
    (l1OverPLogDerivative_le_neg_one_on_box₅_direct hlo hhi)

/-- Combine three residual bucket bounds into one residual bound.

This is the scalar endpoint for the v9/v10 diagnostic decomposition into
leading-block, tail-main, and bounded-cross buckets. -/
theorem abs_sub_sum3_le_of_bucket_bounds
    (a₁ a₂ a₃ b₁ b₂ b₃ k₁ k₂ k₃ K scale : ℝ)
    (hscale : 0 ≤ scale)
    (h₁ : |a₁ - b₁| ≤ k₁ * scale)
    (h₂ : |a₂ - b₂| ≤ k₂ * scale)
    (h₃ : |a₃ - b₃| ≤ k₃ * scale)
    (hK : k₁ + k₂ + k₃ ≤ K) :
    |(a₁ + a₂ + a₃) - (b₁ + b₂ + b₃)| ≤ K * scale := by
  have htri₁ :
      |(a₁ - b₁) + (a₂ - b₂) + (a₃ - b₃)| ≤
        |a₁ - b₁| + |a₂ - b₂| + |a₃ - b₃| := by
    calc
      |(a₁ - b₁) + (a₂ - b₂) + (a₃ - b₃)|
          ≤ |(a₁ - b₁) + (a₂ - b₂)| + |a₃ - b₃| := by
            exact abs_add_le ((a₁ - b₁) + (a₂ - b₂)) (a₃ - b₃)
      _ ≤ (|a₁ - b₁| + |a₂ - b₂|) + |a₃ - b₃| := by
            have h := abs_add_le (a₁ - b₁) (a₂ - b₂)
            linarith
      _ = |a₁ - b₁| + |a₂ - b₂| + |a₃ - b₃| := by ring
  have hsum :
      |a₁ - b₁| + |a₂ - b₂| + |a₃ - b₃| ≤
        (k₁ + k₂ + k₃) * scale := by
    calc
      |a₁ - b₁| + |a₂ - b₂| + |a₃ - b₃|
          ≤ k₁ * scale + k₂ * scale + k₃ * scale := by linarith
      _ = (k₁ + k₂ + k₃) * scale := by ring
  have hKscale : (k₁ + k₂ + k₃) * scale ≤ K * scale :=
    mul_le_mul_of_nonneg_right hK hscale
  have hrewrite :
      (a₁ + a₂ + a₃) - (b₁ + b₂ + b₃) =
        (a₁ - b₁) + (a₂ - b₂) + (a₃ - b₃) := by ring
  rw [hrewrite]
  exact htri₁.trans (hsum.trans hKscale)

/-- Grouped small-bucket bound from three unit component budgets.

This is the scalar consumer for the grouped small-bucket obligation artifact:
if bounded-cross non-model remainder, leading-block residual, and tail-main
bucket are each bounded by one residual-scale unit, their grouped contribution
is bounded by `3 * scale`. -/
theorem abs_groupedSmallBucket_le_three_of_component_unit_bounds
    (boundedCrossRemainder leadingBlockResidual tailMain scale : ℝ)
    (hscale : 0 ≤ scale)
    (hbounded : |boundedCrossRemainder| ≤ 1 * scale)
    (hleading : |leadingBlockResidual| ≤ 1 * scale)
    (htail : |tailMain| ≤ 1 * scale) :
    |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
      3 * scale := by
  have h :=
    abs_sub_sum3_le_of_bucket_bounds
      boundedCrossRemainder leadingBlockResidual tailMain
      0 0 0 1 1 1 3 scale hscale
      (by simpa using hbounded)
      (by simpa using hleading)
      (by simpa using htail)
      (by norm_num)
  simpa using h

/-- The theorem-facing grouped small-bucket budget used by the restricted
bridge.

The diagnostic obligation artifact currently records each of the three
non-dominant buckets below one scale unit.  The proof bridge only needs the
looser theorem-facing budget `K_small = 8`, leaving slack for later analytic
estimates. -/
theorem abs_groupedSmallBucket_le_eight_of_component_unit_bounds
    (boundedCrossRemainder leadingBlockResidual tailMain scale : ℝ)
    (hscale : 0 ≤ scale)
    (hbounded : |boundedCrossRemainder| ≤ 1 * scale)
    (hleading : |leadingBlockResidual| ≤ 1 * scale)
    (htail : |tailMain| ≤ 1 * scale) :
    |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
      8 * scale := by
  have hthree :=
    abs_groupedSmallBucket_le_three_of_component_unit_bounds
      boundedCrossRemainder leadingBlockResidual tailMain scale
      hscale hbounded hleading htail
  have hle : (3 : ℝ) * scale ≤ 8 * scale :=
    mul_le_mul_of_nonneg_right (by norm_num) hscale
  exact hthree.trans hle

/-- Endpoint-plus-antitone bridge for one normalized large-side bucket.

The r17 decay-profile diagnostic suggests proving each normalized component
bucket is antitone above the cutoff.  This scalar lemma is the reusable endpoint
of that route: once the cutoff endpoint is below a target `K`, every larger
`s` is below the same target. -/
theorem normalizedBucket_le_of_large_side_antitone_endpoint
    {bucketNorm : ℝ → ℝ} {cutoff s K : ℝ}
    (hanti : AntitoneOn bucketNorm (Set.Ici cutoff))
    (hs : cutoff ≤ s)
    (hend : bucketNorm cutoff ≤ K) :
    bucketNorm s ≤ K := by
  have hcutoff_mem : cutoff ∈ Set.Ici cutoff := by
    change cutoff ≤ cutoff
    exact le_rfl
  have hs_mem : s ∈ Set.Ici cutoff := hs
  exact (hanti hcutoff_mem hs_mem hs).trans hend

/-- Endpoint eta-monotonicity bridge for one normalized cutoff bucket.

The r19 endpoint-sweep diagnostic suggests proving the cutoff endpoint profile
is monotone in `η`, with the largest endpoint at the right side of the
restricted interval.  This scalar lemma captures that route: once the right
endpoint is bounded by `K`, every smaller endpoint in the interval is bounded
by `K`. -/
theorem normalizedEndpoint_le_of_eta_monotone_right_endpoint
    {endpointNorm : ℝ → ℝ} {η left right K : ℝ}
    (hmono : MonotoneOn endpointNorm (Set.Icc left right))
    (hη : η ∈ Set.Icc left right)
    (hright : endpointNorm right ≤ K) :
    endpointNorm η ≤ K := by
  have hright_mem : right ∈ Set.Icc left right := by
    exact ⟨hη.1.trans hη.2, le_rfl⟩
  exact (hmono hη hright_mem hη.2).trans hright

/-- Two-parameter endpoint-plus-decay bridge for one normalized bucket.

The r18/r20 diagnostics split the large-side small-bucket obligation into two
monotonicity claims: for a fixed `η`, the normalized bucket decreases with the
horizon scale `s`; at the cutoff scale, the endpoint profile increases with
`η`, so the right endpoint of the restricted interval is the worst sampled
case.  This scalar lemma combines those two reductions. -/
theorem normalizedBucket_le_of_eta_endpoint_and_large_side_antitone
    {bucketNorm : ℝ → ℝ → ℝ} {η left right cutoff s K : ℝ}
    (hanti : AntitoneOn (fun t => bucketNorm η t) (Set.Ici cutoff))
    (hmonoEndpoint : MonotoneOn (fun z => bucketNorm z cutoff) (Set.Icc left right))
    (hη : η ∈ Set.Icc left right)
    (hs : cutoff ≤ s)
    (hrightEndpoint : bucketNorm right cutoff ≤ K) :
    bucketNorm η s ≤ K := by
  have hend : bucketNorm η cutoff ≤ K :=
    normalizedEndpoint_le_of_eta_monotone_right_endpoint
      (endpointNorm := fun z => bucketNorm z cutoff)
      hmonoEndpoint hη hrightEndpoint
  exact normalizedBucket_le_of_large_side_antitone_endpoint hanti hs hend

/-- Grouped small-bucket bound from normalized component decay profiles.

This is the Lean scalar version of the r17 endpoint-plus-monotone-decay route.
If the normalized bounded-cross non-model remainder, leading-block residual,
and tail-main profiles are antitone above the cutoff and each cutoff endpoint
is at most one, then the actual grouped small bucket satisfies the
theorem-facing \(K_{\mathrm{small}}\le8\) budget at every larger `s`.

The functions `boundedNorm`, `leadingNorm`, and `tailNorm` are normalized
absolute bucket profiles, i.e. values whose product with `scale` bounds the
corresponding unnormalized bucket. -/
theorem abs_groupedSmallBucket_le_eight_of_large_side_decay_profiles
    (boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ)
    (hscale : 0 ≤ scale)
    (hs : cutoff ≤ s)
    (hboundedAnti : AntitoneOn boundedNorm (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn leadingNorm (Set.Ici cutoff))
    (htailAnti : AntitoneOn tailNorm (Set.Ici cutoff))
    (hboundedEndpoint : boundedNorm cutoff ≤ 1)
    (hleadingEndpoint : leadingNorm cutoff ≤ 1)
    (htailEndpoint : tailNorm cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm s * scale)
    (hleading :
      |leadingBlockResidual| ≤ leadingNorm s * scale)
    (htail :
      |tailMain| ≤ tailNorm s * scale) :
    |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
      8 * scale := by
  have hboundedNorm : boundedNorm s ≤ 1 :=
    normalizedBucket_le_of_large_side_antitone_endpoint
      hboundedAnti hs hboundedEndpoint
  have hleadingNorm : leadingNorm s ≤ 1 :=
    normalizedBucket_le_of_large_side_antitone_endpoint
      hleadingAnti hs hleadingEndpoint
  have htailNorm : tailNorm s ≤ 1 :=
    normalizedBucket_le_of_large_side_antitone_endpoint
      htailAnti hs htailEndpoint
  have hboundedUnit :
      |boundedCrossRemainder| ≤ 1 * scale :=
    hbounded.trans (mul_le_mul_of_nonneg_right hboundedNorm hscale)
  have hleadingUnit :
      |leadingBlockResidual| ≤ 1 * scale :=
    hleading.trans (mul_le_mul_of_nonneg_right hleadingNorm hscale)
  have htailUnit :
      |tailMain| ≤ 1 * scale :=
    htail.trans (mul_le_mul_of_nonneg_right htailNorm hscale)
  exact
    abs_groupedSmallBucket_le_eight_of_component_unit_bounds
      boundedCrossRemainder leadingBlockResidual tailMain scale
      hscale hboundedUnit hleadingUnit htailUnit

/-- Grouped small-bucket bound from eta-endpoint and large-side decay profiles.

This is the scalar form matching the r18/r20 split.  Each normalized bucket is
a two-parameter profile in `(η,s)`.  The hypotheses say that, for the current
`η`, the profile is antitone above the cutoff in `s`, while the cutoff endpoint
is monotone in `η` over the restricted interval.  It is then enough to bound
the right endpoint at the cutoff. -/
theorem abs_groupedSmallBucket_le_eight_of_eta_endpoint_decay_profiles
    (boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s η left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hscale : 0 ≤ scale)
    (hη : η ∈ Set.Icc left right)
    (hs : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm η t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm η t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm η t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm η s * scale)
    (hleading :
      |leadingBlockResidual| ≤ leadingNorm η s * scale)
    (htail :
      |tailMain| ≤ tailNorm η s * scale) :
    |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
      8 * scale := by
  have hboundedEndpoint : boundedNorm η cutoff ≤ 1 :=
    normalizedEndpoint_le_of_eta_monotone_right_endpoint
      (endpointNorm := fun z => boundedNorm z cutoff)
      hboundedEndpointMono hη hboundedRightEndpoint
  have hleadingEndpoint : leadingNorm η cutoff ≤ 1 :=
    normalizedEndpoint_le_of_eta_monotone_right_endpoint
      (endpointNorm := fun z => leadingNorm z cutoff)
      hleadingEndpointMono hη hleadingRightEndpoint
  have htailEndpoint : tailNorm η cutoff ≤ 1 :=
    normalizedEndpoint_le_of_eta_monotone_right_endpoint
      (endpointNorm := fun z => tailNorm z cutoff)
      htailEndpointMono hη htailRightEndpoint
  exact
    abs_groupedSmallBucket_le_eight_of_large_side_decay_profiles
      boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s
      (fun t => boundedNorm η t) (fun t => leadingNorm η t) (fun t => tailNorm η t)
      hscale hs hboundedAnti hleadingAnti htailAnti
      hboundedEndpoint hleadingEndpoint htailEndpoint
      hbounded hleading htail

/-- Record-shaped import surface for eta-endpoint and large-side decay profiles.

This packages the remaining large-side grouped-small-bucket proof obligations:
three normalized bucket profiles, eta-monotone cutoff endpoints, horizon
antitonicity for the current eta, right-endpoint unit bounds, and the actual
bucket-to-profile inequalities.  It is intentionally abstract: future analytic
proofs or audited certificates can instantiate this record without changing the
final scalar handoff theorem. -/
structure RestrictedEtaEndpointDecayProfileCertificate
    (boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s η left right : ℝ) :
    Type where
  boundedNorm : ℝ → ℝ → ℝ
  leadingNorm : ℝ → ℝ → ℝ
  tailNorm : ℝ → ℝ → ℝ
  scale_nonneg : 0 ≤ scale
  eta_mem : η ∈ Set.Icc left right
  cutoff_le_s : cutoff ≤ s
  bounded_antitone : AntitoneOn (fun t => boundedNorm η t) (Set.Ici cutoff)
  leading_antitone : AntitoneOn (fun t => leadingNorm η t) (Set.Ici cutoff)
  tail_antitone : AntitoneOn (fun t => tailNorm η t) (Set.Ici cutoff)
  bounded_endpoint_mono :
    MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right)
  leading_endpoint_mono :
    MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right)
  tail_endpoint_mono :
    MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right)
  bounded_right_endpoint : boundedNorm right cutoff ≤ 1
  leading_right_endpoint : leadingNorm right cutoff ≤ 1
  tail_right_endpoint : tailNorm right cutoff ≤ 1
  bounded_bucket :
    |boundedCrossRemainder| ≤ boundedNorm η s * scale
  leading_bucket :
    |leadingBlockResidual| ≤ leadingNorm η s * scale
  tail_bucket :
    |tailMain| ≤ tailNorm η s * scale

/-- A record-shaped eta-endpoint/large-side profile certificate supplies the
grouped \(K_{\mathrm{small}}\le8\) residual budget. -/
theorem RestrictedEtaEndpointDecayProfileCertificate.groupedSmallBucket_bound
    {boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s η left right : ℝ}
    (cert :
      RestrictedEtaEndpointDecayProfileCertificate
        boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s η left right) :
    |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
      8 * scale :=
  abs_groupedSmallBucket_le_eight_of_eta_endpoint_decay_profiles
    boundedCrossRemainder leadingBlockResidual tailMain scale cutoff s η left right
    cert.boundedNorm cert.leadingNorm cert.tailNorm
    cert.scale_nonneg cert.eta_mem cert.cutoff_le_s
    cert.bounded_antitone cert.leading_antitone cert.tail_antitone
    cert.bounded_endpoint_mono cert.leading_endpoint_mono cert.tail_endpoint_mono
    cert.bounded_right_endpoint cert.leading_right_endpoint cert.tail_right_endpoint
    cert.bounded_bucket cert.leading_bucket cert.tail_bucket

/-- Combine a dominant model budget and a smaller-bucket budget into one
residual bound.

This matches the r13 residual replay surface: the bounded-cross model term gets
budget `Kcross`, while the bounded-cross non-model remainder, leading-block
residual, and tail-main bucket are grouped into `Ksmall`. -/
theorem abs_add_le_of_cross_small_budget
    (cross small Kcross Ksmall K scale : ℝ)
    (hscale : 0 ≤ scale)
    (hcross : |cross| ≤ Kcross * scale)
    (hsmall : |small| ≤ Ksmall * scale)
    (hK : Kcross + Ksmall ≤ K) :
    |cross + small| ≤ K * scale := by
  have htri : |cross + small| ≤ |cross| + |small| :=
    abs_add_le cross small
  have hsum : |cross| + |small| ≤ (Kcross + Ksmall) * scale := by
    calc
      |cross| + |small| ≤ Kcross * scale + Ksmall * scale := by linarith
      _ = (Kcross + Ksmall) * scale := by ring
  have hKscale : (Kcross + Ksmall) * scale ≤ K * scale :=
    mul_le_mul_of_nonneg_right hK hscale
  exact htri.trans (hsum.trans hKscale)

/-- Decompose the bounded-cross model step into coefficient and power parts.

For the intended residual application, `Dp,Dq` are values of the dominant
coefficient `D(η)`, while `wp,wq` are powers `s^(1-2η)`.  This theorem says
that a `16 * scale` budget for the coefficient-change contribution and another
`16 * scale` budget for the power-change contribution give the
`32 * scale` bounded-cross model budget. -/
theorem abs_cross_model_step_le_of_factor_budgets
    (Dp Dq wp wq scale : ℝ)
    (hcoeff : |Dq - Dp| * |wq| ≤ 16 * scale)
    (hpower : |Dp| * |wq - wp| ≤ 16 * scale) :
    |Dq * wq - Dp * wp| ≤ 32 * scale := by
  have hdecomp :
      Dq * wq - Dp * wp = (Dq - Dp) * wq + Dp * (wq - wp) := by
    ring
  calc
    |Dq * wq - Dp * wp|
        = |(Dq - Dp) * wq + Dp * (wq - wp)| := by rw [hdecomp]
    _ ≤ |(Dq - Dp) * wq| + |Dp * (wq - wp)| :=
        abs_add_le ((Dq - Dp) * wq) (Dp * (wq - wp))
    _ = |Dq - Dp| * |wq| + |Dp| * |wq - wp| := by rw [abs_mul, abs_mul]
    _ ≤ 16 * scale + 16 * scale := by linarith
    _ = 32 * scale := by ring

/-- Bounded-cross model step from the theorem-facing coefficient budgets.

Assume `|D'| ≤ 16`, `|D(η_p)| ≤ 8`, both normalized endpoints lie in the
restricted interval, the adjacent step is at most `1/s`, and `1 ≤ log s`.
Then the full model step
`D(η)s^(1-2η)` has the intended `32 * s^(-1/8) log s` budget.

This is the scalar endpoint supplied by the r13 dominant-coefficient
certificate plus the power-factor theorem above. -/
theorem abs_cross_model_step_le_of_restricted_factor_bounds
    {D D' : ℝ → ℝ} {s ηp ηq : ℝ}
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hp : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hq : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s) :
    |D ηq * bifrCrossPower s ηq - D ηp * bifrCrossPower s ηp| ≤
      32 * bifrRestrictedResidualScale s := by
  have hweight : |bifrCrossPower s ηq| ≤ s ^ ((7 : ℝ) / 8) :=
    abs_bifrCrossPower_le_seven_eighth hs hq
  have hcoeff :
      |D ηq - D ηp| * |bifrCrossPower s ηq| ≤
        16 * bifrRestrictedResidualScale s :=
    abs_coeff_step_times_weight_le_residualScale
      hs hlog hderiv hDprime hp hq hstep hweight
  have hpower_step :
      |bifrCrossPower s ηq - bifrCrossPower s ηp| ≤
        2 * bifrRestrictedResidualScale s :=
    abs_bifrCrossPower_sub_le_two_residualScale hs hp hq hstep
  have hpower :
      |D ηp| * |bifrCrossPower s ηq - bifrCrossPower s ηp| ≤
        16 * bifrRestrictedResidualScale s := by
    calc
      |D ηp| * |bifrCrossPower s ηq - bifrCrossPower s ηp|
          ≤ 8 * (2 * bifrRestrictedResidualScale s) := by
            exact mul_le_mul hDp hpower_step (abs_nonneg _)
              (le_trans (abs_nonneg _) hDp)
      _ = 16 * bifrRestrictedResidualScale s := by ring
  exact
    abs_cross_model_step_le_of_factor_budgets
      (D ηp) (D ηq) (bifrCrossPower s ηp) (bifrCrossPower s ηq)
      (bifrRestrictedResidualScale s) hcoeff hpower

/-- Strict adjacent drop from a leading gap and three residual bucket bounds. -/
theorem singleSq_adjacent_lt_of_leading_gap_and_residual_buckets
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ : ℝ)
    (p₁ p₂ p₃ q₁ q₂ q₃ k₁ k₂ k₃ K scale c0 : ℝ)
    (hp :
      env.singleSq p = leadingP + (p₁ + p₂ + p₃))
    (hq :
      env.singleSq (p + 1) = leadingQ + (q₁ + q₂ + q₃))
    (hscale : 0 ≤ scale)
    (h₁ : |p₁ - q₁| ≤ k₁ * scale)
    (h₂ : |p₂ - q₂| ≤ k₂ * scale)
    (h₃ : |p₃ - q₃| ≤ k₃ * scale)
    (hK : k₁ + k₂ + k₃ ≤ K)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hKhalf : K * scale ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hbuckets :
      |(p₁ + p₂ + p₃) - (q₁ + q₂ + q₃)| ≤ K * scale :=
    abs_sub_sum3_le_of_bucket_bounds
      p₁ p₂ p₃ q₁ q₂ q₃ k₁ k₂ k₃ K scale hscale h₁ h₂ h₃ hK
  have hresidual :
      |(p₁ + p₂ + p₃) - (q₁ + q₂ + q₃)| ≤ c0 / 2 :=
    hbuckets.trans hKhalf
  exact
    env.singleSq_adjacent_lt_of_leading_gap_and_residual_bound
      leadingP leadingQ (p₁ + p₂ + p₃) (q₁ + q₂ + q₃) c0
      hp hq hleading hresidual hc0

/-- Strict adjacent drop from a leading gap and a cross/small residual split.

The intended instantiation is `Kcross = 32`, `Ksmall = 1`, and
`K = Ktotal = 40`; the theorem is stated generally so later analytic
certificates can choose sharper constants.  Here `crossDelta + smallDelta`
is the one-step residual difference `E_p - E_q`; the right residual is absorbed
into `leadingQ`, so this theorem instantiates the symmetric residual bridge
with `errorQ = 0`. -/
theorem singleSq_adjacent_lt_of_leading_gap_and_cross_small_residual
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (leadingP leadingQ : ℝ)
    (crossDelta smallDelta Kcross Ksmall K scale c0 : ℝ)
    (hp : env.singleSq p = leadingP + (crossDelta + smallDelta))
    (hq : env.singleSq (p + 1) = leadingQ)
    (hscale : 0 ≤ scale)
    (hcross : |crossDelta| ≤ Kcross * scale)
    (hsmall : |smallDelta| ≤ Ksmall * scale)
    (hK : Kcross + Ksmall ≤ K)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hKhalf : K * scale ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hresidual :
      |(crossDelta + smallDelta) - 0| ≤ c0 / 2 := by
    have hbudget :
        |crossDelta + smallDelta| ≤ K * scale :=
      abs_add_le_of_cross_small_budget
        crossDelta smallDelta Kcross Ksmall K scale
        hscale hcross hsmall hK
    simpa using hbudget.trans hKhalf
  exact
    env.singleSq_adjacent_lt_of_leading_gap_and_residual_bound
      leadingP leadingQ (crossDelta + smallDelta) 0 c0
      hp (by simpa using hq) hleading hresidual hc0

/-- Adjacent single-component drop from leading gap, bounded-cross model
factor budgets, and a grouped smaller-bucket residual budget.

This is the current strongest scalar endpoint for the restricted route.  The
cross residual is instantiated as
`D(η_p)s^(1-2η_p)-D(η_q)s^(1-2η_q)`.  The theorem consumes the
theorem-facing coefficient assumptions `|D'| ≤ 16`, `|D(η_p)| ≤ 8`, the
restricted adjacent step assumptions, and a separate small-bucket bound. -/
theorem singleSq_adjacent_lt_of_leading_gap_cross_model_and_small_residual
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta Ksmall Ktotal c0 : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ Ksmall * bifrRestrictedResidualScale s)
    (hK : 32 + Ksmall ≤ Ktotal)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hKhalf : Ktotal * bifrRestrictedResidualScale s ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hcross_rev :
      |D ηq * bifrCrossPower s ηq - D ηp * bifrCrossPower s ηp| ≤
        32 * bifrRestrictedResidualScale s :=
    abs_cross_model_step_le_of_restricted_factor_bounds
      hs hlog hderiv hDprime hDp hpη hqη hstep
  have hcross :
      |D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq| ≤
        32 * bifrRestrictedResidualScale s := by
    simpa [abs_sub_comm] using hcross_rev
  exact
    singleSq_adjacent_lt_of_leading_gap_and_cross_small_residual
      env leadingP leadingQ
      (D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq)
      smallDelta 32 Ksmall Ktotal (bifrRestrictedResidualScale s) c0
      hp_eq hq_eq hscale hcross hsmall hK hleading hKhalf hc0

/-- Concrete restricted adjacent-drop bridge with the current proof-facing
constants.

This specializes the scalar endpoint to the r13/r21 constants:
`K_cross = 32`, `K_small = 8`, `K_total = 40`, and leading gap `c₀ = 1/8`.
The only remaining asymptotic-side scalar input is the cutoff
`bifrRestrictedResidualScale s ≤ 1/640`, which is exactly the condition
ensuring `40 * scale ≤ (1/8)/2`. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 / 8 : ℝ) ≤ leadingP - leadingQ)
    (hcutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hK : (32 : ℝ) + 8 ≤ 40 := by norm_num
  have hKhalf : (40 : ℝ) * bifrRestrictedResidualScale s ≤ (1 / 8 : ℝ) / 2 := by
    calc
      (40 : ℝ) * bifrRestrictedResidualScale s ≤ 40 * (1 / 640 : ℝ) := by
        exact mul_le_mul_of_nonneg_left hcutoff (by norm_num)
      _ = (1 / 8 : ℝ) / 2 := by norm_num
  exact
    singleSq_adjacent_lt_of_leading_gap_cross_model_and_small_residual
      env leadingP leadingQ smallDelta 8 40 (1 / 8)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hK hleading hKhalf (by norm_num)

/-- Adjacent combined-envelope drop from leading gap, a bounded-cross model,
and a grouped smaller residual.

This is the Route B analogue of
`singleSq_adjacent_lt_of_leading_gap_cross_model_and_small_residual`, but for
the practical combined `b=p` objective `multiSq`.  The cross residual is
modeled by `D(η)s^(1-2η)`, while `smallDelta` groups the bounded-cross
non-model remainder, leading-block residual, and tail-main bucket. -/
theorem multiSq_adjacent_lt_of_leading_gap_cross_model_and_small_residual
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta Ksmall Ktotal c0 : ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ Ksmall * bifrRestrictedResidualScale s)
    (hK : 32 + Ksmall ≤ Ktotal)
    (hleading : c0 ≤ leadingP - leadingQ)
    (hKhalf : Ktotal * bifrRestrictedResidualScale s ≤ c0 / 2)
    (hc0 : 0 < c0) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hcross_rev :
      |D ηq * bifrCrossPower s ηq - D ηp * bifrCrossPower s ηp| ≤
        32 * bifrRestrictedResidualScale s :=
    abs_cross_model_step_le_of_restricted_factor_bounds
      hs hlog hderiv hDprime hDp hpη hqη hstep
  have hcross :
      |D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq| ≤
        32 * bifrRestrictedResidualScale s := by
    simpa [abs_sub_comm] using hcross_rev
  have hresidual :
      |(D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta|
        ≤ Ktotal * bifrRestrictedResidualScale s :=
    abs_add_le_of_cross_small_budget
      (D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq)
      smallDelta 32 Ksmall Ktotal (bifrRestrictedResidualScale s)
      hscale hcross hsmall hK
  exact
    env.multiSq_adjacent_lt_of_leading_gap_and_residual_delta_bound
      leadingP leadingQ
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta)
      Ktotal (bifrRestrictedResidualScale s) c0
      hp_eq hq_eq hscale hresidual hleading hKhalf hc0

/-- Concrete Route B combined-envelope bridge with the current proof-facing
constants.

This specializes the combined model-plus-small-residual bridge to
`K_cross = 32`, `K_small = 8`, `K_total = 40`, and leading gap `c₀ = 1`.
The residual-scale cutoff `scale ≤ 1/640` is deliberately stronger than
needed, matching the existing large-side cutoff artifacts. -/
theorem multiSq_adjacent_lt_of_combined_restricted_bridge_40
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 : ℝ) ≤ leadingP - leadingQ)
    (hcutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hK : (32 : ℝ) + 8 ≤ 40 := by norm_num
  have hKhalf : (40 : ℝ) * bifrRestrictedResidualScale s ≤ (1 : ℝ) / 2 := by
    calc
      (40 : ℝ) * bifrRestrictedResidualScale s ≤ 40 * (1 / 640 : ℝ) := by
        exact mul_le_mul_of_nonneg_left hcutoff (by norm_num)
      _ ≤ (1 : ℝ) / 2 := by norm_num
  exact
    multiSq_adjacent_lt_of_leading_gap_cross_model_and_small_residual
      env leadingP leadingQ smallDelta 8 40 1
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hK hleading hKhalf (by norm_num)

/-- Concrete Route B combined-envelope bridge for all large horizon scales.

This removes the residual-scale cutoff from the theorem interface by reusing
the existing closed cutoff arithmetic for `s ≥ 2^(253/2)`.  The remaining
inputs are the analytic/certificate facts for the combined residual model:
coefficient derivative bounds, coefficient size, adjacent eta step, and the
grouped smaller-residual budget. -/
theorem multiSq_adjacent_lt_of_combined_restricted_bridge_40_of_ge_two_rpow_cutoff_closed
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 : ℝ) ≤ leadingP - leadingQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hs : 1 ≤ s := one_le_of_ge_two_rpow_cutoff_closed hsge
  have hlog : 1 ≤ Real.log s := one_le_log_of_ge_two_rpow_cutoff_closed hsge
  have hcutoff :
      bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
      hsge bifrLogTwo_lower_two_thirds bifrLogTwo_upper_seven_tenths
      bifrTwoRpowThirteenSixteenths_lower_seven_fourths
  exact
    multiSq_adjacent_lt_of_combined_restricted_bridge_40
      env leadingP leadingQ smallDelta hp_eq hq_eq hs hlog
      hderiv hDprime hDp hpη hqη hstep hsmall hleading hcutoff

/-- Concrete Route B combined-envelope bridge using large-side decay profiles
for the grouped smaller residual buckets.

This is the `multiSq` version of the existing single-component profile bridge:
the three normalized small-bucket profiles supply `K_small = 8`, and the
dominant combined residual model supplies the `K_cross = 32` budget. -/
theorem multiSq_adjacent_lt_of_combined_restricted_bridge_40_of_large_side_decay_profiles
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn boundedNorm (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn leadingNorm (Set.Ici cutoff))
    (htailAnti : AntitoneOn tailNorm (Set.Ici cutoff))
    (hboundedEndpoint : boundedNorm cutoff ≤ 1)
    (hleadingEndpoint : leadingNorm cutoff ≤ 1)
    (htailEndpoint : tailNorm cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 : ℝ) ≤ leadingP - leadingQ)
    (hresidualCutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hsmall :
      |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
        8 * bifrRestrictedResidualScale s :=
    abs_groupedSmallBucket_le_eight_of_large_side_decay_profiles
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s
      boundedNorm leadingNorm tailNorm
      hscale hcutoff_s hboundedAnti hleadingAnti htailAnti
      hboundedEndpoint hleadingEndpoint htailEndpoint
      hbounded hleadingBucket htail
  exact
    multiSq_adjacent_lt_of_combined_restricted_bridge_40
      env leadingP leadingQ
      (boundedCrossRemainder + leadingBlockResidual + tailMain)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hleadingGap hresidualCutoff

/-- Concrete Route B combined-envelope bridge using eta-endpoint and
large-side decay profiles for the grouped smaller residual buckets.

This is the scalar handoff for the endpoint-sweep route: cutoff profiles are
monotone in `η`, large-side profiles are antitone in `s`, and the right
endpoint at the cutoff is at most one for each bucket. -/
theorem multiSq_adjacent_lt_of_combined_restricted_bridge_40_of_eta_endpoint_decay_profiles
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 : ℝ) ≤ leadingP - leadingQ)
    (hresidualCutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hsmall :
      |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
        8 * bifrRestrictedResidualScale s :=
    abs_groupedSmallBucket_le_eight_of_eta_endpoint_decay_profiles
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s ηp left right
      boundedNorm leadingNorm tailNorm
      hscale hη hcutoff_s hboundedAnti hleadingAnti htailAnti
      hboundedEndpointMono hleadingEndpointMono htailEndpointMono
      hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
      hbounded hleadingBucket htail
  exact
    multiSq_adjacent_lt_of_combined_restricted_bridge_40
      env leadingP leadingQ
      (boundedCrossRemainder + leadingBlockResidual + tailMain)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hleadingGap hresidualCutoff

/-- Route B combined-envelope endpoint/decay bridge for all large horizon
scales.

This is the current strongest scalar endpoint for the practical combined
`b=p` proof route.  It combines the dominant residual model, eta-endpoint and
large-side decay certificates for the grouped smaller buckets, and the closed
cutoff arithmetic from `s ≥ 2^(253/2)`. -/
theorem multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profiles_ge_two_rpow_cutoff_closed
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 : ℝ) ≤ leadingP - leadingQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hs : 1 ≤ s := one_le_of_ge_two_rpow_cutoff_closed hsge
  have hlog : 1 ≤ Real.log s := one_le_log_of_ge_two_rpow_cutoff_closed hsge
  have hcutoff :
      bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
      hsge bifrLogTwo_lower_two_thirds bifrLogTwo_upper_seven_tenths
      bifrTwoRpowThirteenSixteenths_lower_seven_fourths
  exact
    multiSq_adjacent_lt_of_combined_restricted_bridge_40_of_eta_endpoint_decay_profiles
      env leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
      boundedNorm leadingNorm tailNorm
      hp_eq hq_eq hs hlog hη hcutoff_s
      hboundedAnti hleadingAnti htailAnti
      hboundedEndpointMono hleadingEndpointMono htailEndpointMono
      hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
      hbounded hleadingBucket htail
      hderiv hDprime hDp hpη hqη hstep hleadingGap hcutoff

/-- Route B combined-envelope bridge from a record-shaped endpoint/decay
certificate.

This is the intended import surface for future analytic or interval
certificates: the certificate supplies the grouped \(K_{\mathrm{small}}\le8\)
profile facts, while the remaining hypotheses are the combined residual-model
coefficient bounds and the leading-gap decomposition. -/
theorem multiSq_adjacent_lt_of_combined_eta_endpoint_decay_certificate_ge_two_rpow_cutoff_closed
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (cert :
      RestrictedEtaEndpointDecayProfileCertificate
        boundedCrossRemainder leadingBlockResidual tailMain
        (bifrRestrictedResidualScale s) cutoff s ηp left right)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 : ℝ) ≤ leadingP - leadingQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  have hs : 1 ≤ s := one_le_of_ge_two_rpow_cutoff_closed hsge
  have hlog : 1 ≤ Real.log s := one_le_log_of_ge_two_rpow_cutoff_closed hsge
  have hcutoff :
      bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
      hsge bifrLogTwo_lower_two_thirds bifrLogTwo_upper_seven_tenths
      bifrTwoRpowThirteenSixteenths_lower_seven_fourths
  have hsmall :
      |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
        8 * bifrRestrictedResidualScale s :=
    cert.groupedSmallBucket_bound
  exact
    multiSq_adjacent_lt_of_combined_restricted_bridge_40
      env leadingP leadingQ
      (boundedCrossRemainder + leadingBlockResidual + tailMain)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hleadingGap hcutoff

/-- Concrete restricted adjacent-drop bridge using large-side decay profiles
for the grouped smaller residual buckets.

This theorem directly connects the r17-style endpoint-plus-antitone route to
the `K_small = 8`, `K_total = 40` bridge.  The three residual buckets are the
bounded-cross non-model remainder, the leading-block residual, and the
tail-main bucket; their normalized profiles bound the actual bucket sizes after
multiplication by `bifrRestrictedResidualScale s`. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_of_large_side_decay_profiles
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn boundedNorm (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn leadingNorm (Set.Ici cutoff))
    (htailAnti : AntitoneOn tailNorm (Set.Ici cutoff))
    (hboundedEndpoint : boundedNorm cutoff ≤ 1)
    (hleadingEndpoint : leadingNorm cutoff ≤ 1)
    (htailEndpoint : tailNorm cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 / 8 : ℝ) ≤ leadingP - leadingQ)
    (hresidualCutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hsmall :
      |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
        8 * bifrRestrictedResidualScale s :=
    abs_groupedSmallBucket_le_eight_of_large_side_decay_profiles
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s
      boundedNorm leadingNorm tailNorm
      hscale hcutoff_s hboundedAnti hleadingAnti htailAnti
      hboundedEndpoint hleadingEndpoint htailEndpoint
      hbounded hleadingBucket htail
  exact
    singleSq_adjacent_lt_of_restricted_bridge_40
      env leadingP leadingQ
      (boundedCrossRemainder + leadingBlockResidual + tailMain)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hleadingGap hresidualCutoff

/-- Concrete restricted adjacent-drop bridge using eta-endpoint and large-side
decay profiles for the grouped smaller residual buckets.

This is the scalar theorem that matches the r18/r20 evidence split most
directly.  The normalized residual buckets are two-parameter profiles in
`(η,s)`: the cutoff endpoint profiles are monotone in `η`, and for the current
`η` the large-side profiles are antitone in `s`.  Right-endpoint bounds at the
cutoff are therefore enough to feed the grouped `K_small = 8` residual budget
into the `K_total = 40` restricted bridge. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_of_eta_endpoint_decay_profiles
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 / 8 : ℝ) ≤ leadingP - leadingQ)
    (hresidualCutoff : bifrRestrictedResidualScale s ≤ 1 / 640) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hsmall :
      |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
        8 * bifrRestrictedResidualScale s :=
    abs_groupedSmallBucket_le_eight_of_eta_endpoint_decay_profiles
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s ηp left right
      boundedNorm leadingNorm tailNorm
      hscale hη hcutoff_s hboundedAnti hleadingAnti htailAnti
      hboundedEndpointMono hleadingEndpointMono htailEndpointMono
      hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
      hbounded hleadingBucket htail
  exact
    singleSq_adjacent_lt_of_restricted_bridge_40
      env leadingP leadingQ
      (boundedCrossRemainder + leadingBlockResidual + tailMain)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hleadingGap hresidualCutoff

/-- Eta-endpoint and large-side decay bridge with exact cutoff arithmetic.

This is the same endpoint/decay-profile bridge as
`singleSq_adjacent_lt_of_restricted_bridge_40_of_eta_endpoint_decay_profiles`,
but it consumes the scalar log/root cutoff replay inputs instead of a bare
`bifrRestrictedResidualScale s ≤ 1/640` hypothesis. -/
theorem singleSq_adjacent_lt_of_eta_endpoint_decay_profiles_and_log_root_bounds
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hlog_upper : Real.log s ≤ (1771 : ℝ) / 20)
    (hroot_lower : (57344 : ℝ) ≤ s ^ ((1 : ℝ) / 8))
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hcutoff : bifrRestrictedResidualScale s ≤ 1 / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_log_and_root_bounds
      hs hlog_upper hroot_lower
  exact
    singleSq_adjacent_lt_of_restricted_bridge_40_of_eta_endpoint_decay_profiles
      env leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
      boundedNorm leadingNorm tailNorm
      hp_eq hq_eq hs hlog hη hcutoff_s
      hboundedAnti hleadingAnti htailAnti
      hboundedEndpointMono hleadingEndpointMono htailEndpointMono
      hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
      hbounded hleadingBucket htail
      hderiv hDprime hDp hpη hqη hstep hleadingGap hcutoff

/-- Eta-endpoint and large-side decay bridge for all large horizon scales.

This is the closed large-side interface for the r18/r20 proof route.  It
combines eta-endpoint monotonicity, horizon antitonicity, and right-endpoint
unit bounds for the three normalized small-bucket profiles, then feeds the
result into the already closed `s ≥ 2^(253/2)` residual-scale cutoff bridge. -/
theorem singleSq_adjacent_lt_of_eta_endpoint_decay_profiles_ge_two_rpow_cutoff_closed
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hs : 1 ≤ s := one_le_of_ge_two_rpow_cutoff_closed hsge
  have hlog : 1 ≤ Real.log s := one_le_log_of_ge_two_rpow_cutoff_closed hsge
  have hscale : 0 ≤ bifrRestrictedResidualScale s := by
    unfold bifrRestrictedResidualScale
    exact mul_nonneg (Real.rpow_nonneg (le_trans (by norm_num) hs) _)
      (Real.log_nonneg hs)
  have hsmall :
      |boundedCrossRemainder + leadingBlockResidual + tailMain| ≤
        8 * bifrRestrictedResidualScale s :=
    abs_groupedSmallBucket_le_eight_of_eta_endpoint_decay_profiles
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s ηp left right
      boundedNorm leadingNorm tailNorm
      hscale hη hcutoff_s hboundedAnti hleadingAnti htailAnti
      hboundedEndpointMono hleadingEndpointMono htailEndpointMono
      hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
      hbounded hleadingBucket htail
  have hcutoff :
      bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
      hsge bifrLogTwo_lower_two_thirds bifrLogTwo_upper_seven_tenths
      bifrTwoRpowThirteenSixteenths_lower_seven_fourths
  exact
    singleSq_adjacent_lt_of_restricted_bridge_40
      env leadingP leadingQ
      (boundedCrossRemainder + leadingBlockResidual + tailMain)
      hp_eq hq_eq hs hlog hderiv hDprime hDp hpη hqη hstep
      hsmall hleadingGap hcutoff

/-- Concrete restricted adjacent-drop bridge using the exact cutoff replay
inputs rather than a bare residual-scale cutoff.

The assumptions `Real.log s ≤ 1771/20` and `57344 ≤ s^(1/8)` are the two scalar
endpoint bounds replayed by the r22 cutoff artifact from imported elementary
facts.  This theorem keeps the final constant plumbing in Lean while still
leaving those endpoint bounds as explicit hypotheses. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_of_log_and_root_bounds
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hs : 1 ≤ s) (hlog : 1 ≤ Real.log s)
    (hlog_upper : Real.log s ≤ (1771 : ℝ) / 20)
    (hroot_lower : (57344 : ℝ) ≤ s ^ ((1 : ℝ) / 8))
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hcutoff :
      bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_log_and_root_bounds
      hs hlog_upper hroot_lower
  exact
    singleSq_adjacent_lt_of_restricted_bridge_40
      env leadingP leadingQ smallDelta hp_eq hq_eq hs hlog
      hderiv hDprime hDp hpη hqη hstep hsmall hleading hcutoff

/-- Concrete restricted adjacent-drop bridge for all horizon scales
`s ≥ 2^(253/2)`.

This removes the final cutoff-arithmetic certificate from the theorem
interface.  The remaining imported endpoint facts are the elementary
transcendental bounds `2/3 ≤ log 2`, `log 2 ≤ 7/10`, and
`7/4 ≤ 2^(13/16)`. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_of_ge_two_rpow_cutoff
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (hlog_two_lower : (2 / 3 : ℝ) ≤ Real.log 2)
    (hlog_two_upper : Real.log 2 ≤ (7 / 10 : ℝ))
    (hpow : (7 / 4 : ℝ) ≤ (2 : ℝ) ^ ((13 : ℝ) / 16))
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p := by
  have hs : 1 ≤ s := one_le_of_ge_two_rpow_cutoff_closed hsge
  have hlog : 1 ≤ Real.log s := one_le_log_of_ge_two_rpow_cutoff_closed hsge
  have hcutoff :
      bifrRestrictedResidualScale s ≤ (1 : ℝ) / 640 :=
    bifrRestrictedResidualScale_le_one_div_640_of_ge_two_rpow_cutoff
      hsge hlog_two_lower hlog_two_upper hpow
  exact
    singleSq_adjacent_lt_of_restricted_bridge_40
      env leadingP leadingQ smallDelta hp_eq hq_eq hs hlog
      hderiv hDprime hDp hpη hqη hstep hsmall hleading hcutoff

/-- Concrete restricted adjacent-drop bridge for all horizon scales
`s ≥ 2^(253/2)`, with the cutoff endpoint fully discharged by Lean/Mathlib.

Compared with
`singleSq_adjacent_lt_of_restricted_bridge_40_of_ge_two_rpow_cutoff`, this
version no longer requires imported scalar facts about `log 2` or
`2^(13/16)`.  The remaining hypotheses are the real analytic inputs:
coefficient bounds, small-bucket residual bound, restricted endpoint
membership, adjacent step size, leading gap, and the horizon cutoff. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_of_ge_two_rpow_cutoff_closed
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p :=
  singleSq_adjacent_lt_of_restricted_bridge_40_of_ge_two_rpow_cutoff
    env leadingP leadingQ smallDelta hp_eq hq_eq hsge
    bifrLogTwo_lower_two_thirds bifrLogTwo_upper_seven_tenths
    bifrTwoRpowThirteenSixteenths_lower_seven_fourths
    hderiv hDprime hDp hpη hqη hstep hsmall hleading

/-- Restricted adjacent-drop bridge with an explicit finite-certificate branch.

The large-horizon branch is
`singleSq_adjacent_lt_of_restricted_bridge_40_of_ge_two_rpow_cutoff_closed`.
The small-horizon branch is a future finite interval certificate for
`s < 2^(253/2)`.  This theorem is intentionally only scalar glue: it does not
prove the finite certificate, but it makes the final handoff explicit and
prevents the below-cutoff obligation from being hidden in prose. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_or_finite_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hfinite :
      s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
        env.singleSq (p + 1) < env.singleSq p)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p := by
  by_cases hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s
  · exact
      singleSq_adjacent_lt_of_restricted_bridge_40_of_ge_two_rpow_cutoff_closed
        env leadingP leadingQ smallDelta hp_eq hq_eq hsge
        hderiv hDprime hDp hpη hqη hstep hsmall hleading
  · exact hfinite (lt_of_not_ge hsge)

/-- Record-shaped version of
`singleSq_adjacent_lt_of_restricted_bridge_40_or_finite_certificate`.

This is the intended Lean consumer for a future finite interval-box
certificate: the finite branch supplies a named
`RestrictedFiniteSingleDropCertificate`, while the large branch remains the
closed residual bridge above `2^(253/2)`. -/
theorem singleSq_adjacent_lt_of_restricted_bridge_40_or_finite_certificate_record
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ} (leadingP leadingQ smallDelta : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) + smallDelta))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hfinite :
      s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
        RestrictedFiniteSingleDropCertificate env p s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hsmall : |smallDelta| ≤ 8 * bifrRestrictedResidualScale s)
    (hleading : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p :=
  singleSq_adjacent_lt_of_restricted_bridge_40_or_finite_certificate
    env leadingP leadingQ smallDelta hp_eq hq_eq
    (fun hslt => (hfinite hslt).singleDrop)
    hderiv hDprime hDp hpη hqη hstep hsmall hleading

/-- Restricted adjacent-drop bridge with eta-endpoint large-side profiles and
an explicit finite-certificate branch.

This is the strongest current scalar handoff for the single-component route:
below the cutoff it delegates to a future finite interval certificate; above
the cutoff it uses the eta-endpoint/horizon-decay profile bridge with the
closed \(s\ge2^{253/2}\) cutoff arithmetic. -/
theorem singleSq_adjacent_lt_of_eta_endpoint_decay_profiles_or_finite_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (hfinite :
      s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
        RestrictedFiniteSingleDropCertificate env p s)
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p := by
  by_cases hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s
  · exact
      singleSq_adjacent_lt_of_eta_endpoint_decay_profiles_ge_two_rpow_cutoff_closed
        env leadingP leadingQ
        boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
        boundedNorm leadingNorm tailNorm
        hp_eq hq_eq hsge hη hcutoff_s
        hboundedAnti hleadingAnti htailAnti
        hboundedEndpointMono hleadingEndpointMono htailEndpointMono
        hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
        hbounded hleadingBucket htail
        hderiv hDprime hDp hpη hqη hstep hleadingGap
  · exact (hfinite (lt_of_not_ge hsge)).singleDrop

/-- Record-shaped version of
`singleSq_adjacent_lt_of_eta_endpoint_decay_profiles_or_finite_certificate`.

The large-side profile obligations are packaged in a
`RestrictedEtaEndpointDecayProfileCertificate`; the below-cutoff branch remains
the same future finite interval certificate. -/
theorem singleSq_adjacent_lt_of_eta_endpoint_decay_profile_certificate_or_finite
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (hp_eq : env.singleSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.singleSq (p + 1) = leadingQ)
    (profileCert :
      RestrictedEtaEndpointDecayProfileCertificate
        boundedCrossRemainder leadingBlockResidual tailMain
        (bifrRestrictedResidualScale s) cutoff s ηp left right)
    (hfinite :
      s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
        RestrictedFiniteSingleDropCertificate env p s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 / 8 : ℝ) ≤ leadingP - leadingQ) :
    env.singleSq (p + 1) < env.singleSq p :=
  singleSq_adjacent_lt_of_eta_endpoint_decay_profiles_or_finite_certificate
    env leadingP leadingQ
    boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
    profileCert.boundedNorm profileCert.leadingNorm profileCert.tailNorm
    hp_eq hq_eq hfinite profileCert.eta_mem profileCert.cutoff_le_s
    profileCert.bounded_antitone profileCert.leading_antitone profileCert.tail_antitone
    profileCert.bounded_endpoint_mono profileCert.leading_endpoint_mono
    profileCert.tail_endpoint_mono
    profileCert.bounded_right_endpoint profileCert.leading_right_endpoint
    profileCert.tail_right_endpoint
    profileCert.bounded_bucket profileCert.leading_bucket profileCert.tail_bucket
    hderiv hDprime hDp hpη hqη hstep hleadingGap

/-- Complete record-shaped handoff for the restricted single-component route.

This packages all current theorem inputs for the restricted adjacent
`A_p * B_p` drop: the exact decomposition of `singleSq p`, the large-side
eta-endpoint profile certificate, the below-cutoff finite certificate branch,
and the dominant-coefficient derivative/size hypotheses.  It is still an
import surface, not a proof of the analytic endpoint or finite-box obligations. -/
structure RestrictedSingleComponentHandoffCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) (D D' : ℝ → ℝ)
    (s ηp ηq leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ) :
    Type where
  singleP_eq : env.singleSq p = leadingP +
    ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
      (boundedCrossRemainder + leadingBlockResidual + tailMain))
  singleQ_eq : env.singleSq (p + 1) = leadingQ
  profileCert :
    RestrictedEtaEndpointDecayProfileCertificate
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s ηp left right
  finiteCert :
    s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
      RestrictedFiniteSingleDropCertificate env p s
  deriv_bound :
    ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z
  dprime_bound : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16
  d_at_p_bound : |D ηp| ≤ 8
  eta_p_mem : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)
  eta_q_mem : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)
  eta_step : |ηq - ηp| ≤ 1 / s
  leading_gap : (1 / 8 : ℝ) ≤ leadingP - leadingQ

/-- A complete restricted single-component handoff certificate proves the
adjacent single-component drop at the scalar boundary. -/
theorem RestrictedSingleComponentHandoffCertificate.singleDrop
    {env : BIFRUncollapsedEnvelopeFamily} {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ}
    (cert :
      RestrictedSingleComponentHandoffCertificate
        env p D D' s ηp ηq leadingP leadingQ
        boundedCrossRemainder leadingBlockResidual tailMain cutoff left right) :
    env.singleSq (p + 1) < env.singleSq p :=
  singleSq_adjacent_lt_of_eta_endpoint_decay_profile_certificate_or_finite
    env leadingP leadingQ
    boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
    cert.singleP_eq cert.singleQ_eq cert.profileCert cert.finiteCert
    cert.deriv_bound cert.dprime_bound cert.d_at_p_bound
    cert.eta_p_mem cert.eta_q_mem cert.eta_step cert.leading_gap

/-- Non-method spelling of
`RestrictedSingleComponentHandoffCertificate.singleDrop` for JSON/packet
metadata that tracks theorem names rather than method projections. -/
theorem singleSq_adjacent_lt_of_restricted_single_component_handoff_certificate
    {env : BIFRUncollapsedEnvelopeFamily} {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ}
    (cert :
      RestrictedSingleComponentHandoffCertificate
        env p D D' s ηp ηq leadingP leadingQ
        boundedCrossRemainder leadingBlockResidual tailMain cutoff left right) :
    env.singleSq (p + 1) < env.singleSq p :=
  cert.singleDrop

/-- Route B combined-envelope bridge with eta-endpoint large-side profiles and
an explicit finite-certificate branch.

Above the \(2^{253/2}\) cutoff this uses the combined endpoint/decay profile
bridge.  Below the cutoff it delegates to a future finite interval certificate
for the practical combined `b=p` envelope. -/
theorem multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profiles_or_finite_certificate
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (boundedNorm leadingNorm tailNorm : ℝ → ℝ → ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (hfinite :
      s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
        RestrictedFiniteMultiDropCertificate env p s)
    (hη : ηp ∈ Set.Icc left right)
    (hcutoff_s : cutoff ≤ s)
    (hboundedAnti : AntitoneOn (fun t => boundedNorm ηp t) (Set.Ici cutoff))
    (hleadingAnti : AntitoneOn (fun t => leadingNorm ηp t) (Set.Ici cutoff))
    (htailAnti : AntitoneOn (fun t => tailNorm ηp t) (Set.Ici cutoff))
    (hboundedEndpointMono :
      MonotoneOn (fun z => boundedNorm z cutoff) (Set.Icc left right))
    (hleadingEndpointMono :
      MonotoneOn (fun z => leadingNorm z cutoff) (Set.Icc left right))
    (htailEndpointMono :
      MonotoneOn (fun z => tailNorm z cutoff) (Set.Icc left right))
    (hboundedRightEndpoint : boundedNorm right cutoff ≤ 1)
    (hleadingRightEndpoint : leadingNorm right cutoff ≤ 1)
    (htailRightEndpoint : tailNorm right cutoff ≤ 1)
    (hbounded :
      |boundedCrossRemainder| ≤ boundedNorm ηp s * bifrRestrictedResidualScale s)
    (hleadingBucket :
      |leadingBlockResidual| ≤ leadingNorm ηp s * bifrRestrictedResidualScale s)
    (htail :
      |tailMain| ≤ tailNorm ηp s * bifrRestrictedResidualScale s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 : ℝ) ≤ leadingP - leadingQ) :
    env.multiSq (p + 1) < env.multiSq p := by
  by_cases hsge : (2 : ℝ) ^ ((253 : ℝ) / 2) ≤ s
  · exact
      multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profiles_ge_two_rpow_cutoff_closed
        env leadingP leadingQ
        boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
        boundedNorm leadingNorm tailNorm
        hp_eq hq_eq hsge hη hcutoff_s
        hboundedAnti hleadingAnti htailAnti
        hboundedEndpointMono hleadingEndpointMono htailEndpointMono
        hboundedRightEndpoint hleadingRightEndpoint htailRightEndpoint
        hbounded hleadingBucket htail
        hderiv hDprime hDp hpη hqη hstep hleadingGap
  · exact (hfinite (lt_of_not_ge hsge)).multiDrop

/-- Record-shaped version of
`multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profiles_or_finite_certificate`.

The large-side profile obligations are packaged in
`RestrictedEtaEndpointDecayProfileCertificate`; the below-cutoff branch is the
future finite interval certificate for the practical combined `b=p` envelope. -/
theorem multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profile_certificate_or_finite
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq : ℝ}
    (leadingP leadingQ : ℝ)
    (boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ)
    (hp_eq : env.multiSq p = leadingP +
      ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
        (boundedCrossRemainder + leadingBlockResidual + tailMain)))
    (hq_eq : env.multiSq (p + 1) = leadingQ)
    (profileCert :
      RestrictedEtaEndpointDecayProfileCertificate
        boundedCrossRemainder leadingBlockResidual tailMain
        (bifrRestrictedResidualScale s) cutoff s ηp left right)
    (hfinite :
      s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
        RestrictedFiniteMultiDropCertificate env p s)
    (hderiv : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z)
    (hDprime : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16)
    (hDp : |D ηp| ≤ 8)
    (hpη : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hqη : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4))
    (hstep : |ηq - ηp| ≤ 1 / s)
    (hleadingGap : (1 : ℝ) ≤ leadingP - leadingQ) :
    env.multiSq (p + 1) < env.multiSq p :=
  multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profiles_or_finite_certificate
    env leadingP leadingQ
    boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
    profileCert.boundedNorm profileCert.leadingNorm profileCert.tailNorm
    hp_eq hq_eq hfinite profileCert.eta_mem profileCert.cutoff_le_s
    profileCert.bounded_antitone profileCert.leading_antitone profileCert.tail_antitone
    profileCert.bounded_endpoint_mono profileCert.leading_endpoint_mono
    profileCert.tail_endpoint_mono
    profileCert.bounded_right_endpoint profileCert.leading_right_endpoint
    profileCert.tail_right_endpoint
    profileCert.bounded_bucket profileCert.leading_bucket profileCert.tail_bucket
    hderiv hDprime hDp hpη hqη hstep hleadingGap

/-- Complete record-shaped handoff for the practical combined `b=p` route.

This packages the current final theorem inputs for the adjacent combined drop:
the exact decomposition of `multiSq p`, the large-side eta-endpoint profile
certificate, the below-cutoff finite certificate branch, and the dominant
combined-residual coefficient derivative/size hypotheses. -/
structure RestrictedMultiComponentHandoffCertificate
    (env : BIFRUncollapsedEnvelopeFamily) (p : ℕ) (D D' : ℝ → ℝ)
    (s ηp ηq leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ) :
    Type where
  multiP_eq : env.multiSq p = leadingP +
    ((D ηp * bifrCrossPower s ηp - D ηq * bifrCrossPower s ηq) +
      (boundedCrossRemainder + leadingBlockResidual + tailMain))
  multiQ_eq : env.multiSq (p + 1) = leadingQ
  profileCert :
    RestrictedEtaEndpointDecayProfileCertificate
      boundedCrossRemainder leadingBlockResidual tailMain
      (bifrRestrictedResidualScale s) cutoff s ηp left right
  finiteCert :
    s < (2 : ℝ) ^ ((253 : ℝ) / 2) →
      RestrictedFiniteMultiDropCertificate env p s
  deriv_bound :
    ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), HasDerivAt D (D' z) z
  dprime_bound : ∀ z ∈ Set.Icc (1 / 16 : ℝ) (1 / 4), |D' z| ≤ 16
  d_at_p_bound : |D ηp| ≤ 8
  eta_p_mem : ηp ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)
  eta_q_mem : ηq ∈ Set.Icc (1 / 16 : ℝ) (1 / 4)
  eta_step : |ηq - ηp| ≤ 1 / s
  leading_gap : (1 : ℝ) ≤ leadingP - leadingQ

/-- A complete practical combined handoff certificate proves the adjacent
combined `b=p` drop at the scalar boundary. -/
theorem RestrictedMultiComponentHandoffCertificate.multiDrop
    {env : BIFRUncollapsedEnvelopeFamily} {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ}
    (cert :
      RestrictedMultiComponentHandoffCertificate
        env p D D' s ηp ηq leadingP leadingQ
        boundedCrossRemainder leadingBlockResidual tailMain cutoff left right) :
    env.multiSq (p + 1) < env.multiSq p :=
  multiSq_adjacent_lt_of_combined_eta_endpoint_decay_profile_certificate_or_finite
    env leadingP leadingQ
    boundedCrossRemainder leadingBlockResidual tailMain cutoff left right
    cert.multiP_eq cert.multiQ_eq cert.profileCert cert.finiteCert
    cert.deriv_bound cert.dprime_bound cert.d_at_p_bound
    cert.eta_p_mem cert.eta_q_mem cert.eta_step cert.leading_gap

/-- Non-method spelling of
`RestrictedMultiComponentHandoffCertificate.multiDrop` for JSON/packet
metadata that tracks theorem names rather than method projections. -/
theorem multiSq_adjacent_lt_of_restricted_multi_component_handoff_certificate
    {env : BIFRUncollapsedEnvelopeFamily} {p : ℕ} {D D' : ℝ → ℝ}
    {s ηp ηq leadingP leadingQ
      boundedCrossRemainder leadingBlockResidual tailMain cutoff left right : ℝ}
    (cert :
      RestrictedMultiComponentHandoffCertificate
        env p D D' s ηp ηq leadingP leadingQ
        boundedCrossRemainder leadingBlockResidual tailMain cutoff left right) :
    env.multiSq (p + 1) < env.multiSq p :=
  cert.multiDrop

/-- Product-level proof seam for the `ell_1 / b` component after the
separation divisor has already been folded into the `L` term. -/
theorem l1Sq_drop_of_gain_dominates_loss
    (Ap Aq Lp Lq : ℝ)
    (hgain :
      Lq * (Aq - Ap) ≤ Ap * (Lp - Lq)) :
    Aq * Lq ≤ Ap * Lp := by
  nlinarith

/-- Single-participation component monotonicity from the product-level seam. -/
theorem singleSq_mono_of_gain_dominates_loss
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hgain :
      env.B q * (env.A q - env.A p) ≤
        env.A p * (env.B p - env.B q)) :
    env.singleSq q ≤ env.singleSq p := by
  simpa [singleSq] using
    singleSq_drop_of_gain_dominates_loss
      (env.A p) (env.A q) (env.B p) (env.B q) hgain

/-- Trivial single-participation monotonicity when both factors decrease.

The diagnostics split transitions into this easy case and the nontrivial
gain-dominates-loss case where `A` increases. -/
theorem singleSq_mono_of_factors_nonincreasing
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hA : env.A q ≤ env.A p)
    (hB : env.B q ≤ env.B p)
    (hAq_nonneg : 0 ≤ env.A q)
    (hBp_nonneg : 0 ≤ env.B p) :
    env.singleSq q ≤ env.singleSq p := by
  calc
    env.singleSq q = env.A q * env.B q := rfl
    _ ≤ env.A q * env.B p := by
      exact mul_le_mul_of_nonneg_left hB hAq_nonneg
    _ ≤ env.A p * env.B p := by
      exact mul_le_mul_of_nonneg_right hA hBp_nonneg

/-- `ell_1 / b` component monotonicity from the product-level seam, stated
directly for the already divided component `A_p * L_p / b(p)`.

The analytic proof can target this form, avoiding separate monotonicity claims
for `A`, `L`, and `sep`. -/
theorem l1OverBSq_mono_of_direct_component_drop
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hdrop : env.A q * env.L q / env.sep q ≤ env.A p * env.L p / env.sep p) :
    env.l1OverBSq q ≤ env.l1OverBSq p := by
  simpa [l1OverBSq] using hdrop

/-- `ell_1 / b` component monotonicity from the same gain-dominates-loss seam
as the single-participation component, with the separation divisor folded into
the second factor.

This is the form suggested by the r02 diagnostics:
`M_p = L_p / sep_p`, and the product drop follows from
`M_q (A_q - A_p) ≤ A_p (M_p - M_q)`. -/
theorem l1OverBSq_mono_of_gain_dominates_loss
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hgain :
      (env.L q / env.sep q) * (env.A q - env.A p) ≤
        env.A p * (env.L p / env.sep p - env.L q / env.sep q)) :
    env.l1OverBSq q ≤ env.l1OverBSq p := by
  convert
    singleSq_drop_of_gain_dominates_loss
      (env.A p) (env.A q)
      (env.L p / env.sep p) (env.L q / env.sep q) hgain
    using 1
  · simp [l1OverBSq, div_eq_mul_inv]
    ring
  · simp [l1OverBSq, div_eq_mul_inv]
    ring

/-- Trivial `ell_1 / b` monotonicity when both factors decrease after folding
the separation divisor into `M_p = L_p / sep_p`. -/
theorem l1OverBSq_mono_of_factors_nonincreasing
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hA : env.A q ≤ env.A p)
    (hM : env.L q / env.sep q ≤ env.L p / env.sep p)
    (hAq_nonneg : 0 ≤ env.A q)
    (hMp_nonneg : 0 ≤ env.L p / env.sep p) :
    env.l1OverBSq q ≤ env.l1OverBSq p := by
  calc
    env.l1OverBSq q = env.A q * (env.L q / env.sep q) := by
      simp [l1OverBSq, div_eq_mul_inv]
      ring
    _ ≤ env.A q * (env.L p / env.sep p) := by
      exact mul_le_mul_of_nonneg_left hM hAq_nonneg
    _ ≤ env.A p * (env.L p / env.sep p) := by
      exact mul_le_mul_of_nonneg_right hA hMp_nonneg
    _ = env.l1OverBSq p := by
      simp [l1OverBSq, div_eq_mul_inv]
      ring

/-- Adjacent single-participation monotonicity from the gain-dominates-loss
seam. -/
theorem singleSq_adjacent_mono_of_gain_dominates_loss
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hgain :
      env.B (p + 1) * (env.A (p + 1) - env.A p) ≤
        env.A p * (env.B p - env.B (p + 1))) :
    env.singleSq (p + 1) ≤ env.singleSq p :=
  env.singleSq_mono_of_gain_dominates_loss hgain

/-- Dyadic single-participation monotonicity from the gain-dominates-loss
seam. -/
theorem singleSq_dyadic_mono_of_gain_dominates_loss
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hgain :
      env.B (2 * p) * (env.A (2 * p) - env.A p) ≤
        env.A p * (env.B p - env.B (2 * p))) :
    env.singleSq (2 * p) ≤ env.singleSq p :=
  env.singleSq_mono_of_gain_dominates_loss hgain

/-- Adjacent `ell_1 / b` monotonicity from the gain-dominates-loss seam. -/
theorem l1OverBSq_adjacent_mono_of_gain_dominates_loss
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hgain :
      (env.L (p + 1) / env.sep (p + 1)) *
          (env.A (p + 1) - env.A p) ≤
        env.A p *
          (env.L p / env.sep p - env.L (p + 1) / env.sep (p + 1))) :
    env.l1OverBSq (p + 1) ≤ env.l1OverBSq p :=
  env.l1OverBSq_mono_of_gain_dominates_loss hgain

/-- Dyadic `ell_1 / b` monotonicity from the gain-dominates-loss seam. -/
theorem l1OverBSq_dyadic_mono_of_gain_dominates_loss
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hgain :
      (env.L (2 * p) / env.sep (2 * p)) *
          (env.A (2 * p) - env.A p) ≤
        env.A p *
          (env.L p / env.sep p - env.L (2 * p) / env.sep (2 * p))) :
    env.l1OverBSq (2 * p) ≤ env.l1OverBSq p :=
  env.l1OverBSq_mono_of_gain_dominates_loss hgain

/-- Combined monotonicity from a product-level single-participation seam and a
direct `ell_1 / b` component drop. -/
theorem multiSq_mono_of_single_gain_and_l1_drop
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hsingleGain :
      env.B q * (env.A q - env.A p) ≤
        env.A p * (env.B p - env.B q))
    (hl1Drop :
      env.A q * env.L q / env.sep q ≤ env.A p * env.L p / env.sep p) :
    env.multiSq q ≤ env.multiSq p :=
  env.multiSq_mono_of_components
    (env.singleSq_mono_of_gain_dominates_loss hsingleGain)
    (env.l1OverBSq_mono_of_direct_component_drop hl1Drop)

/-- Combined monotonicity from product-level seams for both components. -/
theorem multiSq_mono_of_component_gains
    (env : BIFRUncollapsedEnvelopeFamily) {p q : ℕ}
    (hsingleGain :
      env.B q * (env.A q - env.A p) ≤
        env.A p * (env.B p - env.B q))
    (hl1Gain :
      (env.L q / env.sep q) * (env.A q - env.A p) ≤
        env.A p * (env.L p / env.sep p - env.L q / env.sep q)) :
    env.multiSq q ≤ env.multiSq p :=
  env.multiSq_mono_of_components
    (env.singleSq_mono_of_gain_dominates_loss hsingleGain)
    (env.l1OverBSq_mono_of_gain_dominates_loss hl1Gain)

/-- Adjacent combined monotonicity from product-level seams for both
components. -/
theorem multiSq_adjacent_mono_of_component_gains
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hsingleGain :
      env.B (p + 1) * (env.A (p + 1) - env.A p) ≤
        env.A p * (env.B p - env.B (p + 1)))
    (hl1Gain :
      (env.L (p + 1) / env.sep (p + 1)) *
          (env.A (p + 1) - env.A p) ≤
        env.A p *
          (env.L p / env.sep p - env.L (p + 1) / env.sep (p + 1))) :
    env.multiSq (p + 1) ≤ env.multiSq p :=
  env.multiSq_mono_of_component_gains hsingleGain hl1Gain

/-- Dyadic combined monotonicity from product-level seams for both components. -/
theorem multiSq_dyadic_mono_of_component_gains
    (env : BIFRUncollapsedEnvelopeFamily) {p : ℕ}
    (hsingleGain :
      env.B (2 * p) * (env.A (2 * p) - env.A p) ≤
        env.A p * (env.B p - env.B (2 * p)))
    (hl1Gain :
      (env.L (2 * p) / env.sep (2 * p)) *
          (env.A (2 * p) - env.A p) ≤
        env.A p *
          (env.L p / env.sep p - env.L (2 * p) / env.sep (2 * p))) :
    env.multiSq (2 * p) ≤ env.multiSq p :=
  env.multiSq_mono_of_component_gains hsingleGain hl1Gain

end BIFRUncollapsedEnvelopeFamily

end

end DP
end Mf
