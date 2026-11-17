import Mf.DP.ClassicalEventDPProfileSubsampling

open Mf.DP
namespace Probe

-- Definition-level check: the named surface does not construct a sampled law.
theorem surface_only (P : PrivacyObject) (p ε : ℝ) :
    P.subsampleTradeoffAt p ε = TradeoffFunction.pSamplingOperator p (P.tradeoffAt ε) := rfl

-- Conditional composition: no mechanism or source-premise closure is claimed.
theorem operator_to_scalar
    (S : ClassicalSubsamplingAppendixState) (ε δ : ℝ)
    (hp0 : 0 ≤ S.p) (hp1 : S.p ≤ 1) (hε : 0 ≤ ε)
    (hk : S.k = -Real.exp ε) (hb : S.b = 1 - δ)
    (hfeas : ClassicalSubsamplingAppendixFeasible S) :
    (TradeoffFunction.pSamplingOperator S.p
      (TradeoffFunction.ofDPEventBound ε δ)).eval S.alpha ≤ S.beta := by
  have harg : 0 < 1 - S.p + S.p * Real.exp ε := by
    have hexp := Real.one_le_exp_iff.mpr hε
    nlinarith
  exact le_trans
    (pSamplingOperator_ofDPEventBound_le_classicalSubsamplingEventBoundWitness harg S.alpha)
    (classicalSubsamplingAppendixEventBoundWitness_le_beta S hp0 hp1 hε hk hb hfeas)

#print surface_only
#print operator_to_scalar
#print ClassicalSubsamplingAppendixFeasible
#print axioms surface_only
#print axioms operator_to_scalar
end Probe
