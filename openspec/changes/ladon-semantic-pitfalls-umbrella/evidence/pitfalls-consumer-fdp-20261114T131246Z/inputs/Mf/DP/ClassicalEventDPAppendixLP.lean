import Mf.DP.ClassicalEventDPSubsetReplacementCounting

namespace Mf
namespace DP

noncomputable section

/-!
Appendix LP optimization surface for classical subsampling.

This module isolates the linear-optimization step in the appendix proof of
`"Gaussian Differential Privacy" (Dong, Roth, Su, 2019)`.

Primary literature anchors:
- LP setup:
  `paper/theory/mu-dp/appendices/property.tex#L305`
- LP lemma:
  `paper/theory/mu-dp/appendices/property.tex#L316`
- sampled witness lower bound:
  `paper/theory/mu-dp/appendices/property.tex#L339`

Why LP appears here:
- after the subset-replacement counting step, the proof no longer reasons on
  subsets directly
- it reasons on the averaged type-I / type-II error variables
  `A, B, Abar, Bbar, alpha, beta`
- the remaining step is to lower-bound `beta` under linear constraints, which is
  exactly a small finite-dimensional linear program

This file sits immediately downstream of
`Mf.DP.ClassicalEventDPSubsetReplacementCounting`, which supplies the counted
refinement source behind the extra inequality `B >= k * Abar + b`.

The downstream theorem-facing consumer is
`Mf.DP.ClassicalEventDPProfileSubsampling`.
-/

/--
Appendix-level averaged state for the classical subsampling proof.

This packages the variables appearing in the appendix counting/LP route:
- `alphaIncluded`, `betaIncluded` correspond to `A, B`
- `alphaExcluded`, `betaExcluded` correspond to `Abar, Bbar`
- `alpha`, `beta` are the sampled averages
- `k = -exp ε` and `b = 1 - δ`
-/
structure ClassicalSubsamplingAppendixState where
  p : ℝ
  k : ℝ
  b : ℝ
  alpha : ℝ
  beta : ℝ
  alphaIncluded : ℝ
  betaIncluded : ℝ
  alphaExcluded : ℝ
  betaExcluded : ℝ

/--
Feasibility conditions used by the appendix LP/counting proof.

The final two inequalities are the two lower bounds on `B`: the standard
privacy-testing inequality and the extra counted refinement from the appendix.
-/
def ClassicalSubsamplingAppendixFeasible
    (S : ClassicalSubsamplingAppendixState) : Prop :=
  S.alpha = S.p * S.alphaIncluded + (1 - S.p) * S.alphaExcluded ∧
  S.beta = S.p * S.betaIncluded + (1 - S.p) * S.betaExcluded ∧
  S.alphaExcluded + S.betaExcluded = 1 ∧
  S.betaIncluded ≥ S.k * S.alphaIncluded + S.b ∧
  S.betaIncluded ≥ S.k * S.alphaExcluded + S.b

/-- The appendix lower-bound target `p (k alpha + b) + (1 - p) (1 - alpha)`. -/
def classicalSubsamplingAppendixLowerBound
    (p k b alpha : ℝ) : ℝ :=
  p * (k * alpha + b) + (1 - p) * (1 - alpha)

/--
Case split for the appendix LP lemma when `A <= Abar`.

This corresponds to using the inequality `B >= kA + b` from the appendix proof.
-/
private theorem classicalSubsamplingAppendixLowerBound_le_beta_of_included_le_excluded
    (S : ClassicalSubsamplingAppendixState)
    (hp0 : 0 ≤ S.p)
    (hp1 : S.p ≤ 1)
    (hk : S.k ≤ -1)
    (hfeas : ClassicalSubsamplingAppendixFeasible S)
    (hcase : S.alphaIncluded ≤ S.alphaExcluded) :
    classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha ≤ S.beta := by
  rcases hfeas with ⟨hAlpha, hBeta, hExcluded, hIncludedBound, _hExcludedBound⟩
  have hBeta' :
      S.beta =
        S.p * S.betaIncluded + (1 - S.p) * (1 - S.alphaExcluded) := by
    nlinarith [hBeta, hExcluded]
  have hLower :
      S.p * (S.k * S.alphaIncluded + S.b) + (1 - S.p) * (1 - S.alphaExcluded) ≥
        classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha := by
    have hDiff :
        S.p * (S.k * S.alphaIncluded + S.b) + (1 - S.p) * (1 - S.alphaExcluded) -
          classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha =
          S.p * (1 - S.p) * (-S.k - 1) * (S.alphaExcluded - S.alphaIncluded) := by
      unfold classicalSubsamplingAppendixLowerBound
      rw [hAlpha]
      ring_nf
    have hp1' : 0 ≤ 1 - S.p := by linarith
    have hk' : 0 ≤ -S.k - 1 := by linarith
    have hcase' : 0 ≤ S.alphaExcluded - S.alphaIncluded := by linarith
    have hNonneg :
        0 ≤ S.p * (1 - S.p) * (-S.k - 1) * (S.alphaExcluded - S.alphaIncluded) := by
      exact mul_nonneg (mul_nonneg (mul_nonneg hp0 hp1') hk') hcase'
    nlinarith [hDiff, hNonneg]
  nlinarith [hBeta', hIncludedBound, hLower]

/--
Case split for the appendix LP lemma when `Abar <= A`.

This corresponds to using the extra counted refinement `B >= kAbar + b`.
-/
private theorem classicalSubsamplingAppendixLowerBound_le_beta_of_excluded_le_included
    (S : ClassicalSubsamplingAppendixState)
    (hp0 : 0 ≤ S.p)
    (_hp1 : S.p ≤ 1)
    (hk : S.k ≤ -1)
    (hfeas : ClassicalSubsamplingAppendixFeasible S)
    (hcase : S.alphaExcluded ≤ S.alphaIncluded) :
    classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha ≤ S.beta := by
  rcases hfeas with ⟨hAlpha, hBeta, hExcluded, _hIncludedBound, hExcludedBound⟩
  have hBeta' :
      S.beta =
        S.p * S.betaIncluded + (1 - S.p) * (1 - S.alphaExcluded) := by
    nlinarith [hBeta, hExcluded]
  have hLower :
      S.p * (S.k * S.alphaExcluded + S.b) + (1 - S.p) * (1 - S.alphaExcluded) ≥
        classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha := by
    have hDiff :
        S.p * (S.k * S.alphaExcluded + S.b) + (1 - S.p) * (1 - S.alphaExcluded) -
          classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha =
          S.p * (1 - S.p * (S.k + 1)) * (S.alphaIncluded - S.alphaExcluded) := by
      unfold classicalSubsamplingAppendixLowerBound
      rw [hAlpha]
      ring_nf
    have hk' : 0 ≤ 1 - S.p * (S.k + 1) := by
      nlinarith [hp0, hk]
    have hcase' : 0 ≤ S.alphaIncluded - S.alphaExcluded := by linarith
    have hNonneg :
        0 ≤ S.p * (1 - S.p * (S.k + 1)) * (S.alphaIncluded - S.alphaExcluded) := by
      exact mul_nonneg (mul_nonneg hp0 hk') hcase'
    nlinarith [hDiff, hNonneg]
  nlinarith [hBeta', hExcludedBound, hLower]

/--
Abstract appendix LP lower bound.

Given the averaged-variable constraints from the appendix proof and the side
condition `k <= -1` coming from `k = -exp ε`, the sampled average `beta` stays
above the classical lower-bound witness `p (k alpha + b) + (1 - p) (1 - alpha)`.

This is the theorem-facing Lean version of the LP lemma at
`paper/theory/mu-dp/appendices/property.tex#L316`.
-/
theorem classicalSubsamplingAppendixLowerBound_le_beta
    (S : ClassicalSubsamplingAppendixState)
    (hp0 : 0 ≤ S.p)
    (hp1 : S.p ≤ 1)
    (hk : S.k ≤ -1)
    (hfeas : ClassicalSubsamplingAppendixFeasible S) :
    classicalSubsamplingAppendixLowerBound S.p S.k S.b S.alpha ≤ S.beta := by
  by_cases hcase : S.alphaIncluded ≤ S.alphaExcluded
  · exact classicalSubsamplingAppendixLowerBound_le_beta_of_included_le_excluded
      S hp0 hp1 hk hfeas hcase
  · have hcase' : S.alphaExcluded ≤ S.alphaIncluded := le_of_not_ge hcase
    exact classicalSubsamplingAppendixLowerBound_le_beta_of_excluded_le_included
      S hp0 hp1 hk hfeas hcase'

/--
Sampled-witness lower bound extracted from the appendix LP state.

This is the direct lower-bound formula used immediately after the LP lemma in
`paper/theory/mu-dp/appendices/property.tex#L339`.
-/
theorem classicalSubsamplingSampledWitnessLowerBound
    (S : ClassicalSubsamplingAppendixState)
    (hp0 : 0 ≤ S.p)
    (hp1 : S.p ≤ 1)
    (hk : S.k ≤ -1)
    (hfeas : ClassicalSubsamplingAppendixFeasible S) :
    S.beta ≥ S.p * (S.k * S.alpha + S.b) + (1 - S.p) * (1 - S.alpha) := by
  exact classicalSubsamplingAppendixLowerBound_le_beta S hp0 hp1 hk hfeas

end
end DP
end Mf
