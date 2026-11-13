import Mf.DP.ClassicalEventDPSubsampling
import Mf.DP.ClassicalEventDPAppendixLP

namespace Mf
namespace DP

noncomputable section

/-!
Stronger classical event/profile subsampling surface.

This module is the reserved theorem-facing home for the stronger classical
subsampling theorem that sits above the current public `C_p` tradeoff surface in
`Mf.DP.ClassicalEventDPSubsampling`.

Current status:
- [ClassicalEventDPSubsampling.lean](./ClassicalEventDPSubsampling.lean) already
  proves the local public `C_p` tradeoff-surface statement
  `C_p(f_(ε,δ)) <= f_(ε', pδ)`
- downstream sampled-Gaussian packets now require a stronger event/profile
  theorem that can discharge profile-side inequalities, not just the current
  tradeoff-surface comparison

Primary literature anchors:
- `"Gaussian Differential Privacy" (Dong, Roth, Su, 2019)`:
  `paper/theory/mu-dp/subsample.tex#L136`,
  `paper/theory/mu-dp/subsample.tex#L143`
- appendix proof route:
  `paper/theory/mu-dp/appendices/property.tex#L224`
- counting refinement:
  `paper/theory/mu-dp/appendices/property.tex#L286`
- LP lemma:
  `paper/theory/mu-dp/appendices/property.tex#L316`

This file now sits immediately downstream of two helper layers:
- `Mf.DP.ClassicalEventDPSubsetReplacementCounting`, which formalizes the
  subset-replacement correspondence and counted summation theorem behind the
  extra appendix refinement `B >= k * Abar + b`
- `Mf.DP.ClassicalEventDPAppendixLP`, which formalizes the averaged-variable LP
  optimization problem and sampled witness lower bound

What is now formalized here:
- the theorem-facing parameter aliases for the stronger profile layer
- the explicit upstream dependency on the counted refinement and optimization
  layers
- the final appendix-state event-bound export corresponding to the stronger
  classical theorem route

Downstream consumers tracked by packet design:
- `lean-sampled-gaussian-total-column-sum-profile-inequality`
- `lean-sampled-gaussian-exact-poisson-profile-consumer`
-/

/-- Shared sampled privacy parameter alias for the stronger profile theorem. -/
abbrev classicalProfileSubsamplingEpsilon : ℝ → ℝ → ℝ :=
  classicalSubsamplingEpsilon

/-- Shared sampled delta scaling alias for the stronger profile theorem. -/
abbrev classicalProfileSubsamplingDelta : ℝ → ℝ → ℝ :=
  classicalSubsamplingDelta

/--
Final appendix-state event-bound export for the stronger classical subsampling
route.

This theorem packages the counted-refinement source and the appendix LP witness
layer into the classical sampled event-bound witness `f_(ε', pδ)` evaluated at
the sampled error level `alpha`.

It corresponds to the final parameter conversion in the appendix proof route:
- counted refinement source:
  `paper/theory/mu-dp/appendices/property.tex#L286`
- LP lemma:
  `paper/theory/mu-dp/appendices/property.tex#L316`
- witness lower bound:
  `paper/theory/mu-dp/appendices/property.tex#L339`
- stronger theorem route:
  `paper/theory/mu-dp/appendices/property.tex#L224`
-/
theorem classicalSubsamplingAppendixEventBoundWitness_le_beta
    (S : ClassicalSubsamplingAppendixState)
    (hp0 : 0 ≤ S.p)
    (hp1 : S.p ≤ 1)
    (hε : 0 ≤ ε)
    (hkEq : S.k = -Real.exp ε)
    (hbEq : S.b = 1 - δ)
    (hfeas : ClassicalSubsamplingAppendixFeasible S) :
    (classicalSubsamplingEventBoundWitness S.p ε δ).eval S.alpha ≤ S.beta := by
  have hk : S.k ≤ -1 := by
    rw [hkEq]
    nlinarith [Real.one_le_exp_iff.mpr hε]
  have hWitness :
      S.beta ≥ S.p * (S.k * S.alpha + S.b) + (1 - S.p) * (1 - S.alpha) := by
    exact classicalSubsamplingSampledWitnessLowerBound S hp0 hp1 hk hfeas
  have harg : 0 < 1 - S.p + S.p * Real.exp ε := by
    have hexp : 0 < Real.exp ε := Real.exp_pos ε
    nlinarith
  have hExp' :
      Real.exp (classicalProfileSubsamplingEpsilon S.p ε) = 1 - S.p + S.p * Real.exp ε := by
    simpa using classicalSubsamplingEpsilon_exp (p := S.p) (ε := ε) harg
  have hEval :
      (classicalSubsamplingEventBoundWitness S.p ε δ).eval S.alpha =
        S.p * (S.k * S.alpha + S.b) + (1 - S.p) * (1 - S.alpha) := by
    rw [classicalSubsamplingEventBoundWitness_eval, hkEq, hbEq, hExp']
    simp [classicalSubsamplingDelta]
    ring_nf
  rw [hEval]
  linarith

/--
Direct stronger classical event-bound inequality in sampled-parameter form.

This corollary restates the witness theorem without the tradeoff-function wrapper
so downstream profile packets can consume the classical sampled parameters
directly if that shape is more convenient.
-/
theorem classicalSubsamplingAppendixEventBound
    (S : ClassicalSubsamplingAppendixState)
    (hp0 : 0 ≤ S.p)
    (hp1 : S.p ≤ 1)
    (hε : 0 ≤ ε)
    (hkEq : S.k = -Real.exp ε)
    (hbEq : S.b = 1 - δ)
    (hfeas : ClassicalSubsamplingAppendixFeasible S) :
    1 - classicalProfileSubsamplingDelta S.p δ
        - Real.exp (classicalProfileSubsamplingEpsilon S.p ε) * S.alpha ≤ S.beta := by
  simpa [classicalSubsamplingEventBoundWitness_eval] using
    classicalSubsamplingAppendixEventBoundWitness_le_beta
      (S := S) hp0 hp1 hε hkEq hbEq hfeas

end
end DP
end Mf
