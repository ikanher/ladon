import Mf.DP.PoissonPairNonfloorBennettScaleBound
import Mf.Optimization.ClippedSGD.NoiseContractionVariance
import Mf.Optimization.PoissonClippedSGD.PairNonfloorBennettConvergence

/-!
# Bounded-scale actual Poisson SGD with local-smooth utility comparison

The pair/non-floor Bennett variance cap is consumed at the run's actual
positive noise and its own public selector, including L1>0. The sharp
noise-contraction theorem bounds its full envelope by 1+1/sqrt(2) times the
cap-noise envelope evaluated at the cap's own public selector.

This extends the finite Gaussian-reference analysis of Appendix C.4.2 of
Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping* (ICML 2023).
The probability laws retain actual noise. No privacy-budget premise, exact GDP,
PLD-optimality gap, actual-error ordering or final-iterate utility is asserted.
-/

noncomputable section
open MeasureTheory
open Mf.DP
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Actual transcript/output privacy and local-smooth pre-update/uniform utility
under a bounded composition scale, with each envelope using its own public step. -/
theorem pairNonfloorBennett_boundedScale_local_private_convergence
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hq1 : data.q < 1)
    (hmult : data.multiplier =
      Real.sqrt (PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ))
    {M : ℝ} (hM : 0 < M) (hscale : (T : ℝ) * (data.q : ℝ) ^ 2 ≤ M)
    {sigma L0 L1 : ℝ}
    (hsigma : 0 ≤ sigma) (hL0 : 0 < L0) (hL1 : 0 ≤ L1)
    (heta : data.eta = publicStepsize L0 L1 (1 + poissonVariance n data.q)
      (poissonVariance n data.q) (data.clipping / data.q) data.clipping
      (normalizedSumNoise n d data.q data.clipping data.multiplier))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin n → Option Record)
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => slotGradient g D i x)) x)
    (hloc : LocalSmoothGradient
      (fun x => vectorMean (fun i => slotGradient g D i x)) L0 L1)
    (hvariance : ∀ x, meanSqDeviation (fun i => slotGradient g D i x)
      (vectorMean (fun i => slotGradient g D i x)) ≤ sigma ^ 2)
    (fLow : ℝ) (hlower : ∀ x, fLow ≤ f x) :
    let s := normalizedSumNoise n d data.q data.clipping data.multiplier
    let Vcap := PoissonPairNonfloorBennettScaleBound.scaleVarianceCap M ε δ
    let sCap := normalizedSumNoise n d data.q data.clipping (Real.sqrt Vcap)
    let capStep := publicStepsize L0 L1 (1 + poissonVariance n data.q)
      (poissonVariance n data.q) (data.clipping / data.q) data.clipping sCap
    let rate := (1 + 1 / Real.sqrt 2) * (32 * localRate capStep (clippedCurvature L0 L1 data.clipping)
      (f data.initial - fLow) T sigma data.clipping (poissonVariance n data.q) sCap)
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ ∧
    s ^ 2 = data.clipping ^ 2 * d * 
      PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ /
        ((data.q : ℝ) * n) ^ 2 ∧
    PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ ≤ Vcap ∧
    s ≤ sCap ∧
    capStep ≤ data.eta ∧
    data.eta * s ^ 2 ≤ capStep * sCap ^ 2 ∧
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw n d T data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw n d T data.q data.q_le_one s) ≤ rate := by
  have hT : 1 ≤ T := Nat.pos_of_ne_zero (NeZero.ne T)
  have hq0 : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
  have hq1R : (data.q : ℝ) < 1 := by exact_mod_cast hq1
  have hcap := PoissonPairNonfloorBennettScaleBound.calibratedVariance_le_scaleVarianceCap
    hT hq0 hq1R hε hδ0 hδ1 hM hscale
  have hs := data.normalizedSumNoise_pos hn hd
  have hsCap : normalizedSumNoise n d data.q data.clipping data.multiplier ≤
      normalizedSumNoise n d data.q data.clipping
        (Real.sqrt (PoissonPairNonfloorBennettScaleBound.scaleVarianceCap M ε δ)) := by
    rw [hmult]
    unfold normalizedSumNoise
    have hC := data.clipping_pos
    exact mul_le_mul_of_nonneg_left (Real.sqrt_le_sqrt hcap) (by positivity)
  have h := data.pairNonfloorBennett_private_convergence hn hd hε hδ0 hδ1 hq1
    hmult hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  dsimp only at h ⊢
  have hb := poissonVariance_nonneg (N := n) hq0
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
  have hMmove : 0 < data.clipping / (data.q : ℝ) := div_pos data.clipping_pos hq0
  have hF := sub_nonneg.2 (hlower data.initial)
  have hTR : (0 : ℝ) < T := by exact_mod_cast hT
  have hp := publicStepsize_order_and_energy hL0 hL1
    (show 0 < 1 + poissonVariance n data.q by linarith) hb hMmove data.clipping_pos hs hsCap
  have hrate := localRate_publicStepsize_noise_contraction hL0 hL1 hb hMmove
    data.clipping_pos hs hsCap hF hTR hsigma
  rw [← heta] at hp hrate
  have hrate32 := mul_le_mul_of_nonneg_left hrate (show (0 : ℝ) ≤ 32 by norm_num)
  have hrate32' : 32 * localRate data.eta (clippedCurvature L0 L1 data.clipping)
      (f data.initial - fLow) T sigma data.clipping (poissonVariance n data.q)
      (normalizedSumNoise n d data.q data.clipping data.multiplier) ≤
      (1 + 1 / Real.sqrt 2) * (32 * localRate
        (publicStepsize L0 L1 (1 + poissonVariance n data.q) (poissonVariance n data.q)
          (data.clipping / data.q) data.clipping
          (normalizedSumNoise n d data.q data.clipping
            (Real.sqrt (PoissonPairNonfloorBennettScaleBound.scaleVarianceCap M ε δ))))
        (clippedCurvature L0 L1 data.clipping) (f data.initial - fLow) T sigma
        data.clipping (poissonVariance n data.q)
        (normalizedSumNoise n d data.q data.clipping
          (Real.sqrt (PoissonPairNonfloorBennettScaleBound.scaleVarianceCap M ε δ)))) := by
    nlinarith only [hrate32]
  exact ⟨h.1, h.2.1, h.2.2.1, h.2.2.2.1, hcap, hsCap, hp.1, hp.2,
    h.2.2.2.2.1.trans hrate32', h.2.2.2.2.2.trans hrate32'⟩

end Mf.Optimization.PoissonClippedSGD.PrivacyData
