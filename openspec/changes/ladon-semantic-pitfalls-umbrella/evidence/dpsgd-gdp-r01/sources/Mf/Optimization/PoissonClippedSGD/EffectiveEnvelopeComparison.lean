import Mf.DP.PoissonGaussianEffectiveCalibration
import Mf.Optimization.PoissonClippedSGD.FormulaEnvelopeComparison
/-!
# Complete envelope comparison for certified numerical calibration

The represented-input selector uses less than twice every feasible variance.
The accepted one-sided noise comparison controls all six own-public-step terms,
including positive L1. The infimum need not be attained; actual risks are not
ordered by this sufficient-envelope comparison.
-/
noncomputable section
open Mf.DP Mf.DP.PoissonGaussianHistogram Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
/-- The certified numerically calibrated envelope is at most twice every product-feasible envelope. -/
theorem effective_envelope_le_twice_feasible {n d T : ℕ} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T)
    {ε δ L0 L1 F sigma : ℝ} (hε : 0 ≤ ε) (hδ : 0 < δ)
    (hδτ : δ < 1-(1-(data.q : ℝ))^T)
    (aq : RationalScalarInput (data.q : ℝ))
    (aε : RationalScalarInput ε) (aδ : RationalScalarInput δ)
    (hL0 : 0 < L0) (hL1 : 0 ≤ L1) (hF : 0 ≤ F) (hsigma : 0 ≤ sigma)
    (W : NNReal) (hW : PoissonGaussianProductProfile.profile T data.q data.q_le_one W ε ≤ δ) :
    data.publicVarianceEnvelope T L0 L1 F sigma (effectiveCalibratedVariance T data.q data.q_le_one aq aε aδ hT data.q_pos hε hδ hδτ) ≤
      2*data.publicVarianceEnvelope T L0 L1 F sigma W := by
  have hs := effectiveCalibratedVariance_spec T data.q data.q_le_one aq aε aδ hT data.q_pos hε hδ hδτ
  have hc := hs.2.2.2.2 W hW
  have hWp : (0 : ℝ) < W := by linarith [hs.1]
  have hqr : (0 : ℝ) < data.q := data.q_pos
  have hCr := data.clipping_pos
  have hb := poissonVariance_nonneg (N := n) hqr (show (data.q : ℝ) ≤ 1 from data.q_le_one)
  have hscale : 0 < data.clipping*Real.sqrt (d : ℝ)/((data.q : ℝ)*n) := by positivity
  have h := localRate_publicStepsize_double_variance_cap (T := (T : ℝ)) hL0 hL1 hb
    (div_pos hCr hqr) hCr hscale hs.1 hWp hF (by exact_mod_cast hT) hsigma hc.le
  change 32*_ ≤ 2*(32*_)
  have hh := mul_le_mul_of_nonneg_left h (by norm_num : (0 : ℝ) ≤ 32)
  unfold normalizedSumNoise
  nlinarith only [hh]

/-- The complete factor-two envelope comparison also holds against the feasible infimum. -/
theorem effective_envelope_le_twice_infimum {n d T : ℕ} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T)
    {ε δ L0 L1 F sigma : ℝ} (hε : 0 ≤ ε) (hδ : 0 < δ)
    (hδτ : δ < 1-(1-(data.q : ℝ))^T)
    (aq : RationalScalarInput (data.q : ℝ))
    (aε : RationalScalarInput ε) (aδ : RationalScalarInput δ)
    (hL0 : 0 < L0) (hL1 : 0 ≤ L1) (hF : 0 ≤ F) (hsigma : 0 ≤ sigma) :
    data.publicVarianceEnvelope T L0 L1 F sigma (effectiveCalibratedVariance T data.q data.q_le_one aq aε aδ hT data.q_pos hε hδ hδτ) ≤
      2*sInf (data.feasibleEnvelopeValues T ε δ L0 L1 F sigma) := by
  let W := PoissonGaussianProductProfile.optimalVariance T data.q data.q_le_one hε hδ hδτ
  have hs := PoissonGaussianProductProfile.optimalVariance_spec T data.q data.q_le_one hε hδ hδτ
  have hne : (data.feasibleEnvelopeValues T ε δ L0 L1 F sigma).Nonempty :=
    ⟨data.publicVarianceEnvelope T L0 L1 F sigma W, W, hs.1, hs.2.1.le, rfl⟩
  have hh : data.publicVarianceEnvelope T L0 L1 F sigma
      (effectiveCalibratedVariance T data.q data.q_le_one aq aε aδ hT data.q_pos hε hδ hδτ)/2 ≤
      sInf (data.feasibleEnvelopeValues T ε δ L0 L1 F sigma) := by
    apply le_csInf hne
    rintro r ⟨V,hV,hp,rfl⟩
    have hc := data.effective_envelope_le_twice_feasible hn hd hT hε hδ hδτ aq aε aδ hL0 hL1 hF hsigma V hp
    linarith
  linarith
end Mf.Optimization.PoissonClippedSGD.PrivacyData
