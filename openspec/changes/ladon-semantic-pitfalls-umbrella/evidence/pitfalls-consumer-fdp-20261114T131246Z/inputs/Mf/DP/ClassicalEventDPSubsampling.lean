import Mf.DP.FDPSubsampling
import Mf.DP.TradeoffFunction

namespace Mf
namespace DP

noncomputable section

/-!
Classical event-DP subsampling surface.

This module is the theorem-facing home for the classical `(ε', pδ)` privacy
amplification-by-subsampling layer that sits strictly below the sharper `f`-DP
`C_p(f)` endpoint.

The intended literature anchors are:
- `"Gaussian Differential Privacy" (Dong, Roth, Su, 2019)`:
  `paper/theory/mu-dp/subsample.tex#L100`,
  `paper/theory/mu-dp/subsample.tex#L136`
- the local appendix proof path:
  `paper/theory/mu-dp/appendices/property.tex#L224`

This file now lands the reusable public parameter surface and the current
tradeoff-surface theorem: the local `C_p` operator applied to an `(ε, δ)`
event-bound witness stays below the classical `(ε', pδ)` event-bound witness.

What remains outside this module is the stronger appendix-level theorem tracked
by `Mf.DP.ClassicalEventDPProfileSubsampling`, which is the profile/event layer
needed by downstream exact sampled-Gaussian consumers.
-/

/--
Classical sampled privacy parameter
`ε' = log (1 - p + p * exp ε)`.

This is the reparameterization used by the classical `(ε', pδ)` subsampling
theorem.
-/
def classicalSubsamplingEpsilon (p ε : ℝ) : ℝ :=
  Real.log (1 - p + p * Real.exp ε)

/-- Classical sampled delta scaling `δ' = pδ`. -/
def classicalSubsamplingDelta (p δ : ℝ) : ℝ :=
  p * δ

/--
Named theorem-facing classical sampled event-bound witness
`f_{ε', pδ}`.
-/
def classicalSubsamplingEventBoundWitness (p ε δ : ℝ) : TradeoffFunction :=
  TradeoffFunction.ofDPEventBound
    (classicalSubsamplingEpsilon p ε)
    (classicalSubsamplingDelta p δ)

/--
The classical sampled privacy parameter exponentiates back to the expected
affine slope `1 - p + p * exp ε` whenever the logarithm argument is positive.
-/
theorem classicalSubsamplingEpsilon_exp
    {p ε : ℝ}
    (harg : 0 < 1 - p + p * Real.exp ε) :
    Real.exp (classicalSubsamplingEpsilon p ε) = 1 - p + p * Real.exp ε := by
  simpa [classicalSubsamplingEpsilon] using Real.exp_log harg

/--
Under the standard subsampling side conditions, the classical sampled privacy
parameter is nonnegative.
-/
theorem classicalSubsamplingEpsilon_nonneg
    {p ε : ℝ}
    (hp0 : 0 ≤ p)
    (hε : 0 ≤ ε) :
    0 ≤ classicalSubsamplingEpsilon p ε := by
  have hexp : 1 ≤ Real.exp ε := Real.one_le_exp_iff.mpr hε
  have harg_ge_one : 1 ≤ 1 - p + p * Real.exp ε := by
    nlinarith
  exact Real.log_nonneg harg_ge_one

/-- The classical sampled delta parameter is nonnegative for nonnegative inputs. -/
theorem classicalSubsamplingDelta_nonneg
    {p δ : ℝ}
    (hp0 : 0 ≤ p)
    (hδ0 : 0 ≤ δ) :
    0 ≤ classicalSubsamplingDelta p δ := by
  exact mul_nonneg hp0 hδ0

@[simp] theorem classicalSubsamplingEventBoundWitness_eval
    (p ε δ α : ℝ) :
    (classicalSubsamplingEventBoundWitness p ε δ).eval α =
      1 - classicalSubsamplingDelta p δ
        - Real.exp (classicalSubsamplingEpsilon p ε) * α := by
  rfl

/--
The classical sampled event-bound witness evaluates exactly as the affine
weighted branch obtained by averaging `f_{ε,δ}` with the identity tradeoff
surface.

This is the affine side of the appendix argument in
`paper/theory/mu-dp/appendices/property.tex#L224`; the remaining work for the
full classical theorem is to show that the same witness survives the extra
inverse/convexification structure of `C_p`.
-/
theorem classicalSubsamplingEventBoundWitness_eval_eq_withIdentityWeight
    {p ε δ α : ℝ}
    (harg : 0 < 1 - p + p * Real.exp ε) :
    (classicalSubsamplingEventBoundWitness p ε δ).eval α =
      (TradeoffFunction.withIdentityWeight p (TradeoffFunction.ofDPEventBound ε δ)).eval α := by
  rw [classicalSubsamplingEventBoundWitness_eval, TradeoffFunction.withIdentityWeight_eval,
    TradeoffFunction.ofDPEventBound_eval]
  rw [classicalSubsamplingEpsilon_exp harg]
  simp [classicalSubsamplingDelta]
  ring

/--
The named classical witness is exactly the weighted branch `f_p` applied to the
base event-bound witness `f_(ε,δ)`.
-/
theorem classicalSubsamplingEventBoundWitness_eq_withIdentityWeight
    {p ε δ : ℝ}
    (harg : 0 < 1 - p + p * Real.exp ε) :
    classicalSubsamplingEventBoundWitness p ε δ =
      TradeoffFunction.withIdentityWeight p (TradeoffFunction.ofDPEventBound ε δ) := by
  apply TradeoffFunction.eq_of_eval_eq
  intro α
  exact classicalSubsamplingEventBoundWitness_eval_eq_withIdentityWeight harg

/--
Classical event-DP subsampling theorem on the current public `C_p` tradeoff
surface.

This is the direct local consumer theorem: the theorem-facing `p`-sampling
operator applied to `f_(ε,δ)` stays below the classical sampled event-bound
witness `f_(ε', pδ)`. The proof is the weighted-branch half of the appendix
argument, made explicit on the current Lean `C_p` surface.
-/
theorem pSamplingOperator_ofDPEventBound_le_classicalSubsamplingEventBoundWitness
    {p ε δ : ℝ}
    (harg : 0 < 1 - p + p * Real.exp ε) :
    (TradeoffFunction.pSamplingOperator p (TradeoffFunction.ofDPEventBound ε δ)).PointwiseLE
      (classicalSubsamplingEventBoundWitness p ε δ) := by
  rw [classicalSubsamplingEventBoundWitness_eq_withIdentityWeight harg]
  exact TradeoffFunction.pSamplingOperator_le_withIdentityWeight p
    (TradeoffFunction.ofDPEventBound ε δ)

end
end DP
end Mf
