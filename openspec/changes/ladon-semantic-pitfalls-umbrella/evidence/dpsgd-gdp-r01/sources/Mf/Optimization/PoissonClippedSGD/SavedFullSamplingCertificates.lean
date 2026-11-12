import Mf.DP.PoissonGaussianReferenceCertificates.FullSampling
import Mf.Optimization.PoissonClippedSGD.FullSamplingConvergence

/-!
# Actual privacy and utility for the saved full-sampling cases

The four cases retain N=50000, q=1, delta=1e-5, horizons 1000 or 8,
epsilon 1 or 8 and the exact saved decimal variances. Their Gaussian-profile
budgets are proved by the certificate owner, not supplied by a caller.
The full-sampling transcript has the exact GDP comparison; the transcript,
final output and uniform pre-update output are approximately DP. Utility
bounds the average pre-update gradient and independent uniform pre-update
output at precisely the saved noise and its own public sufficient step.
Dimension, clipping and the measurable query/objective family remain quantified.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.GaussianTesting Mf.Optimization.ClippedSGD
open Mf.DP.PoissonGaussianReferenceCertificates
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- All four unchanged full-sampling saved inputs certify actual privacy and full utility. -/
theorem savedGrid_fullSampling_private_convergence
    (c : FullSampling.Case) {Record : Type} {d : ℕ} (data : PrivacyData 50000 d)
    (hd : 0 < d)
    (hq : data.q = 1)
    (hmult : data.multiplier = Real.sqrt (FullSampling.variance c : ℝ))
    {sigma L0 L1 : ℝ}
    (hsigma : 0 ≤ sigma) (hL0 : 0 < L0) (hL1 : 0 ≤ L1)
    (heta : data.eta = publicStepsize L0 L1 (1 + poissonVariance 50000 data.q)
      (poissonVariance 50000 data.q) (data.clipping / data.q) data.clipping
      (normalizedSumNoise 50000 d data.q data.clipping data.multiplier))
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin 50000 → Option Record)
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => slotGradient g D i x)) x)
    (hloc : LocalSmoothGradient (fun x => vectorMean (fun i => slotGradient g D i x)) L0 L1)
    (hvariance : ∀ x, meanSqDeviation (fun i => slotGradient g D i x)
      (vectorMean (fun i => slotGradient g D i x)) ≤ sigma ^ 2)
    (fLow : ℝ) (hlower : ∀ x, fLow ≤ f x) :
    let s := normalizedSumNoise 50000 d data.q data.clipping data.multiplier
    let rate := 32 * localRate data.eta (clippedCurvature L0 L1 data.clipping)
      (f data.initial - fLow) (FullSampling.horizon c) sigma data.clipping (poissonVariance 50000 data.q) s
    (∀ D D', OptionalRecordAdjacent D D' →
      GDPTestDominates (FullSampling.mu c) (data.optionalTranscriptLaw g hg (FullSampling.horizon c) D)
        (data.optionalTranscriptLaw g hg (FullSampling.horizon c) D')) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg (FullSampling.horizon c)) (FullSampling.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g (FullSampling.horizon c)) (FullSampling.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g (FullSampling.horizon c)) (FullSampling.epsilon c) (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (FullSampling.variance c : ℝ) / ((data.q : ℝ) * 50000) ^ 2 ∧
    ((FullSampling.horizon c) : ℝ)⁻¹ * ∑ t : Fin (FullSampling.horizon c),
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          (FullSampling.horizon c) t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d (FullSampling.horizon c) data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d (FullSampling.horizon c) data.q data.q_le_one s) ≤ rate := by
  have hm : data.multiplier = Real.sqrt ((FullSampling.horizon c : ℝ) / FullSampling.mu c ^ 2) := by
    rw [FullSampling.variance_identity]
    exact hmult
  have h := data.fullSampling_private_convergence (T := FullSampling.horizon c)
    (by norm_num) hd hq (FullSampling.mu_pos c) (FullSampling.epsilon_nonneg c)
    (by norm_num) (FullSampling.complete_budget c) hm hsigma hL0 hL1 heta
    g hg D f hf hloc hvariance fLow hlower
  simpa only [FullSampling.variance_identity, Nat.cast_ofNat] using h

end Mf.Optimization.PoissonClippedSGD.PrivacyData
