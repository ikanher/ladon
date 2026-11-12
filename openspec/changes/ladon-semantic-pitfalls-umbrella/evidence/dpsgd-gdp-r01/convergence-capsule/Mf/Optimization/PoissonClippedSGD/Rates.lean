import Mf.Optimization.PoissonClippedSGD.CoefficientComparison
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Tactic

/-!
# Physical rate expressions and their coefficient comparison

Appendix A of `docs/poisson-clipped-sgd/TARGET.md` compares the unsplit bound
with the Poisson and original six-term expressions. The assumptions below
include the clipping-to-variance ratio and the Poisson stepsize restriction.
-/

noncomputable section

namespace Mf.Optimization.PoissonClippedSGD

def poissonRateD (eta L kappa sigma s F T c : ℝ) : ℝ :=
  4 * F / (eta*T) + 8 * sigma^4 / c^2 + 2 * eta * L * (kappa * sigma^2 + s^2)

def poissonRate (eta L kappa sigma s F T c : ℝ) : ℝ :=
  sigma^2/c + sigma * Real.sqrt (eta*L*kappa) +
    Real.sqrt (F/(eta*T)) + F/(eta*T*c) +
    Real.sqrt (eta*L)*s + eta*L*s^2/c

def oldRate (eta L n q sigma s F T c : ℝ) : ℝ :=
  sigma^2/c + sigma * Real.sqrt (eta*L/(q*n)) +
    Real.sqrt (F/(eta*T)) + F/(eta*T*c) +
    Real.sqrt (eta*L)*s + eta*L*s^2/c

theorem poisson_rates_comparison
    (eta L c sigma s F T n q kappa : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsigma : 0 ≤ sigma) (hs : 0 ≤ s) (hF : 0 ≤ F)
    (hT : 0 < T) (hn : 0 < n) (hq : 0 < q) (hq1 : q ≤ 1)
    (hclip : 4*sigma ≤ c)
    (hkappa : kappa = (1-q)/(q*n))
    (hstep : eta*L*(1+kappa) ≤ 1) :
    Real.sqrt (poissonRateD eta L kappa sigma s F T c) +
        poissonRateD eta L kappa sigma s F T c / c ≤
      4 * poissonRate eta L kappa sigma s F T c ∧
    4 * poissonRate eta L kappa sigma s F T c ≤
      4 * oldRate eta L n q sigma s F T c := by
  have hk0 : 0 ≤ kappa := by
    rw [hkappa]
    have hden : 0 < q*n := mul_pos hq hn
    apply div_nonneg
    · linarith
    · exact hden.le
  let a : ℝ := Real.sqrt (F/(eta*T))
  let b : ℝ := sigma^2/c
  let u : ℝ := sigma * Real.sqrt (eta*L*kappa)
  let w : ℝ := Real.sqrt (eta*L) * s
  have hetaT : 0 < eta*T := mul_pos heta hT
  have hetaL : 0 < eta*L := mul_pos heta hL
  have ha : 0 ≤ a := Real.sqrt_nonneg _
  have hb : 0 ≤ b := div_nonneg (sq_nonneg sigma) hc.le
  have hw : 0 ≤ w := mul_nonneg (Real.sqrt_nonneg _) hs
  have hprod : eta*L*kappa ≤ 1 := by
    calc
      eta*L*kappa ≤ eta*L*(1+kappa) := by
        have hηL0 : 0 ≤ eta*L := mul_nonneg heta.le hL.le
        nlinarith [hηL0, hk0]
      _ ≤ 1 := hstep
  have hroot : Real.sqrt (eta*L*kappa) ≤ 1 := by
    rw [Real.sqrt_le_iff]
    exact ⟨by norm_num, by nlinarith [hprod]⟩
  have hu : 0 ≤ u := mul_nonneg hsigma (Real.sqrt_nonneg _)
  have hsigmac : sigma/c ≤ 1/4 := by
    rw [div_le_iff₀ hc]
    linarith
  have hsmallb : b/c ≤ 1/16 := by
    have hbc : b/c = (sigma/c)^2 := by
      dsimp [b]
      field_simp [ne_of_gt hc]
    have hsc0 : 0 ≤ sigma/c := div_nonneg hsigma hc.le
    have hsquare : (sigma/c)^2 ≤ (1/4)^2 :=
      (sq_le_sq₀ hsc0 (by norm_num)).2 hsigmac
    rw [hbc]
    norm_num at hsquare ⊢
    exact hsquare
  have hsmallu : u/c ≤ 1/4 := by
    have huSig : u ≤ sigma := by
      dsimp [u]
      nlinarith [mul_le_mul_of_nonneg_left hroot hsigma]
    calc
      u/c ≤ sigma/c := div_le_div_of_nonneg_right huSig hc.le
      _ ≤ 1/4 := hsigmac
  have hcmp := appendixA4_scalar_comparison c a b u w hc ha hb hu hw hsmallb hsmallu
  have hD : poissonRateD eta L kappa sigma s F T c =
      4*a^2 + 8*b^2 + 2*u^2 + 2*w^2 := by
    dsimp [poissonRateD, a, b, u, w]
    have hsF : Real.sqrt (F/(eta*T))^2 = F/(eta*T) :=
      Real.sq_sqrt (div_nonneg hF (hetaT.le))
    have hsk : Real.sqrt (eta*L*kappa)^2 = eta*L*kappa :=
      Real.sq_sqrt (mul_nonneg (mul_nonneg heta.le hL.le) hk0)
    have hsηL : Real.sqrt (eta*L)^2 = eta*L := Real.sq_sqrt hetaL.le
    rw [mul_pow, hsk, mul_pow, hsηL, hsF]
    field_simp [ne_of_gt hetaT, ne_of_gt hc]
    ring
  have hRP : poissonRate eta L kappa sigma s F T c =
      a + a^2/c + b + u + w + w^2/c := by
    dsimp [poissonRate, a, b, u, w]
    have hsF : Real.sqrt (F/(eta*T))^2 = F/(eta*T) :=
      Real.sq_sqrt (div_nonneg hF (hetaT.le))
    have hsηL : Real.sqrt (eta*L)^2 = eta*L := Real.sq_sqrt hetaL.le
    rw [mul_pow, hsηL, hsF]
    field_simp [ne_of_gt hetaT, ne_of_gt hc]
    ring
  have hfirst : Real.sqrt (poissonRateD eta L kappa sigma s F T c) +
      poissonRateD eta L kappa sigma s F T c / c ≤
        4 * poissonRate eta L kappa sigma s F T c := by
    rw [hD, hRP]
    exact hcmp
  have hkaple : kappa ≤ 1/(q*n) := by
    rw [hkappa]
    have hden : 0 < q*n := mul_pos hq hn
    have hnum : 0 ≤ 1-q := by linarith
    have hratio : (1-q)/(q*n) ≤ 1/(q*n) := by
      exact div_le_div_of_nonneg_right (by linarith) hden.le
    exact hratio
  have hηL0 : 0 ≤ eta*L := mul_nonneg heta.le hL.le
  have hratioProd : eta*L*kappa ≤ eta*L/(q*n) := by
    have hm := mul_le_mul_of_nonneg_left hkaple hηL0
    calc
      eta*L*kappa ≤ eta*L*(1/(q*n)) := by nlinarith
      _ = eta*L/(q*n) := by ring
  have hrootkap : Real.sqrt (eta*L*kappa) ≤ Real.sqrt (eta*L/(q*n)) :=
    Real.sqrt_le_sqrt hratioProd
  have hsecond : 4 * poissonRate eta L kappa sigma s F T c ≤
      4 * oldRate eta L n q sigma s F T c := by
    apply mul_le_mul_of_nonneg_left _ (by norm_num : (0:ℝ) ≤ 4)
    dsimp [poissonRate, oldRate]
    have hsamp : sigma * Real.sqrt (eta*L*kappa) ≤
        sigma * Real.sqrt (eta*L/(q*n)) :=
      mul_le_mul_of_nonneg_left hrootkap hsigma
    linarith
  exact ⟨hfirst, hsecond⟩

end Mf.Optimization.PoissonClippedSGD
