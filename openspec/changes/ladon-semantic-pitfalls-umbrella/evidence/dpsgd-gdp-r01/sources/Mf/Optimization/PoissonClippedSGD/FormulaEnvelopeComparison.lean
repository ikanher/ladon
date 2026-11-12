import Mf.DP.PoissonGaussianFormulaCalibration
import Mf.Optimization.PoissonClippedSGD.NoiseCalibration
import Mf.Optimization.ClippedSGD.NoiseContractionVariance
import Mf.Optimization.ClippedSGD.SamplerStepsize
/-!
# Complete own-selector envelope comparison for finite formula calibration

The selected variance is below twice every product-feasible variance. The
proved one-sided noise comparison therefore bounds all six terms at each
variance's own public step by factor two, including positive L1 and zero
objective gap or stochastic variance. Taking the infimum does not assume
monotonicity or attainment of the envelope. This concerns sufficient envelopes,
not an ordering of actual risks or joint optimization over arbitrary steps.

The calibration is the finite exact-CDF formula selector. A certified numerical
accountant requires the separate elementary evaluation and rounding layer.
-/

noncomputable section
open Mf.DP Mf.DP.PoissonGaussianHistogram Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Full six-term envelope at the variance-dependent public sufficient step. -/
def publicVarianceEnvelope {n d : ℕ} (data : PrivacyData n d)
    (T : ℕ) (L0 L1 F sigma V : ℝ) : ℝ :=
  let s := normalizedSumNoise n d data.q data.clipping (Real.sqrt V)
  32*localRate (publicStepsize L0 L1 (1+poissonVariance n data.q)
    (poissonVariance n data.q) (data.clipping/data.q) data.clipping s)
    (clippedCurvature L0 L1 data.clipping) F T sigma data.clipping (poissonVariance n data.q) s

/-- The formula-calibrated envelope is at most twice every product-feasible envelope. -/
theorem formula_envelope_le_twice_feasible {n d T : ℕ} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T)
    {ε δ L0 L1 F sigma : ℝ} (hε : 0 ≤ ε) (hδ : 0 < δ)
    (hδτ : δ < 1-(1-(data.q : ℝ))^T)
    (hL0 : 0 < L0) (hL1 : 0 ≤ L1) (hF : 0 ≤ F) (hsigma : 0 ≤ sigma)
    (W : NNReal) (hW : PoissonGaussianProductProfile.profile T data.q data.q_le_one W ε ≤ δ) :
    data.publicVarianceEnvelope T L0 L1 F sigma (formulaCalibratedVariance T data.q ε δ) ≤
      2*data.publicVarianceEnvelope T L0 L1 F sigma W := by
  have hs := formulaCalibratedVariance_spec T hT data.q data.q_le_one data.q_pos hε hδ hδτ
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

/-- Envelopes at positive product-feasible variances, with the public selector fixed. -/
def feasibleEnvelopeValues {n d : ℕ} (data : PrivacyData n d)
    (T : ℕ) (ε δ L0 L1 F sigma : ℝ) : Set ℝ :=
  {r | ∃ W : NNReal, 0 < W ∧ PoissonGaussianProductProfile.profile T data.q data.q_le_one W ε ≤ δ ∧
    r = data.publicVarianceEnvelope T L0 L1 F sigma W}

/-- The complete factor-two envelope comparison also holds against the feasible infimum. -/
theorem formula_envelope_le_twice_infimum {n d T : ℕ} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T)
    {ε δ L0 L1 F sigma : ℝ} (hε : 0 ≤ ε) (hδ : 0 < δ)
    (hδτ : δ < 1-(1-(data.q : ℝ))^T)
    (hL0 : 0 < L0) (hL1 : 0 ≤ L1) (hF : 0 ≤ F) (hsigma : 0 ≤ sigma) :
    data.publicVarianceEnvelope T L0 L1 F sigma (formulaCalibratedVariance T data.q ε δ) ≤
      2*sInf (data.feasibleEnvelopeValues T ε δ L0 L1 F sigma) := by
  let W := PoissonGaussianProductProfile.optimalVariance T data.q data.q_le_one hε hδ hδτ
  have hs := PoissonGaussianProductProfile.optimalVariance_spec T data.q data.q_le_one hε hδ hδτ
  have hne : (data.feasibleEnvelopeValues T ε δ L0 L1 F sigma).Nonempty :=
    ⟨data.publicVarianceEnvelope T L0 L1 F sigma W, W, hs.1, hs.2.1.le, rfl⟩
  have hh : data.publicVarianceEnvelope T L0 L1 F sigma
      (formulaCalibratedVariance T data.q ε δ)/2 ≤
      sInf (data.feasibleEnvelopeValues T ε δ L0 L1 F sigma) := by
    apply le_csInf hne
    rintro r ⟨V,hV,hp,rfl⟩
    have hc := data.formula_envelope_le_twice_feasible hn hd hT hε hδ hδτ hL0 hL1 hF hsigma V hp
    linarith
  linarith
end Mf.Optimization.PoissonClippedSGD.PrivacyData
