import Mf.DP.PoissonPairNonfloorBennettScaleBound
import Mf.Optimization.ClippedSGD.NoiseMonotonicity
import Mf.Optimization.PoissonClippedSGD.PairNonfloorBennettConvergence

/-!
# Bounded-scale privacy and global-smooth utility for actual Poisson SGD

For every run at the pair/non-floor Bennett calibration with T*q²<=M, the
calibrated variance is bounded by a public function of M, epsilon and delta.
For global smoothness (L1=0), the public step is independent of noise, and the
full six-term envelope is bounded by substitution of the cap noise. This
continues the finite Gaussian-reference extension of Appendix C.4.2 of
Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping* (ICML 2023).

The conclusion retains the run's actual calibrated noise in its probability
laws. Cap noise appears only in the upper envelope. It gives both transcript
and output privacy, and pre-update/uniform utility, without a budget premise.
It does not compare actual errors, prove final-iterate utility, handle retuning
at L1>0, or establish a gap to numerical PLD. The exact-Gaussian q=1 branch
remains a separate endpoint.
-/

noncomputable section
open MeasureTheory
open Mf.DP
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The full actual-run guarantee with a uniform variance cap and its global-smooth
utility envelope; both public selectors agree, while the law uses actual noise. -/
theorem pairNonfloorBennett_boundedScale_private_convergence
    {n d T : ℕ} [NeZero T] {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d)
    {ε δ : ℝ} (hε : 0 < ε) (hδ0 : 0 < δ) (hδ1 : δ < 1)
    (hq1 : data.q < 1)
    (hmult : data.multiplier =
      Real.sqrt (PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ))
    {M : ℝ} (hM : 0 < M) (hscale : (T : ℝ) * (data.q : ℝ) ^ 2 ≤ M)
    {sigma L0 : ℝ}
    (hsigma : 0 ≤ sigma) (hL0 : 0 < L0)
    (heta : data.eta = publicStepsize L0 0 (1 + poissonVariance n data.q)
      (poissonVariance n data.q) (data.clipping / data.q) data.clipping
      (normalizedSumNoise n d data.q data.clipping data.multiplier))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin n → Option Record)
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => slotGradient g D i x)) x)
    (hloc : LocalSmoothGradient (fun x => vectorMean (fun i => slotGradient g D i x)) L0 0)
    (hvariance : ∀ x, meanSqDeviation (fun i => slotGradient g D i x)
      (vectorMean (fun i => slotGradient g D i x)) ≤ sigma ^ 2)
    (fLow : ℝ) (hlower : ∀ x, fLow ≤ f x) :
    let s := normalizedSumNoise n d data.q data.clipping data.multiplier
    let Vcap := PoissonPairNonfloorBennettScaleBound.scaleVarianceCap M ε δ
    let sCap := normalizedSumNoise n d data.q data.clipping (Real.sqrt Vcap)
    let rate := 32 * localRate data.eta (clippedCurvature L0 0 data.clipping)
      (f data.initial - fLow) T sigma data.clipping (poissonVariance n data.q) sCap
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) ε δ ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g T) ε δ ∧
    s ^ 2 = data.clipping ^ 2 * d * 
      PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ /
        ((data.q : ℝ) * n) ^ 2 ∧
    PoissonPairNonfloorBennettCalibration.calibratedVariance T data.q ε δ ≤ Vcap ∧
    s ≤ sCap ∧
    data.eta = publicStepsize L0 0 (1 + poissonVariance n data.q)
      (poissonVariance n data.q) (data.clipping / data.q) data.clipping sCap ∧
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
    hmult hsigma hL0 (le_refl 0) heta g hg D f hf hloc hvariance fLow hlower
  dsimp only at h ⊢
  have hstep := poisson_publicStepsize_spec (N := n) hq0
    (by exact_mod_cast data.q_le_one : (data.q : ℝ) ≤ 1)
    hL0 (le_refl 0) data.clipping_pos hs
  rw [← heta] at hstep
  have hrate := mul_le_mul_of_nonneg_left
    (localRate_mono_noise hstep.1.le
      (clippedCurvature_pos hL0 (le_refl 0) data.clipping_pos.le).le
      data.clipping_pos hs.le hsCap
      (F := f data.initial - fLow) (T := (T : ℝ)) (sigma := sigma)
      (b := poissonVariance n data.q)) (show (0 : ℝ) ≤ 32 by norm_num)
  refine ⟨h.1, h.2.1, h.2.2.1, h.2.2.2.1, hcap, hsCap, ?_,
    h.2.2.2.2.1.trans hrate, h.2.2.2.2.2.trans hrate⟩
  simpa only [publicStepsize_zero] using heta

end Mf.Optimization.PoissonClippedSGD.PrivacyData
