import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch64
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch64
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch256
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch256
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch512
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD consumers of exact saved-grid certificates

These saved 1000-step candidates are certified at their original exact decimal
multiplier variances and delta 1e-5: nominal batches 64 and 256, each at
epsilon 1 and 8, plus nominal batch 512 at epsilon 8. Population 50000 and each q=B/50000 are fixed;
dimension, clipping and the measurable query/objective family remain quantified.
The public selector chooses each exact candidate, so actual privacy and full
local-smooth utility apply at its saved noise and that noise's public step.
No budget premise is retained.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.PoissonRawMomentCalibration
open Mf.DP.PoissonGaussianReferenceCertificates
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_steps_epsilonEight_batch64_private_convergence
    {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (StepsEpsilonEightBatch64.q : ℝ))
    (hmult : data.multiplier = Real.sqrt (StepsEpsilonEightBatch64.V : ℝ))
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
      (f data.initial - fLow) 1000 sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg 1000) 8 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g 1000) 8 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g 1000) 8 (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (StepsEpsilonEightBatch64.V : ℝ) / ((data.q : ℝ) * 50000) ^ 2 ∧
    (1000 : ℝ)⁻¹ * ∑ t : Fin 1000,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          1000 t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate := by
  have hsel : select 1000 data.q 8 (1/100000) 3 [StepsEpsilonEightBatch64.candidate] = StepsEpsilonEightBatch64.candidate := by
    rw [hq]
    exact StepsEpsilonEightBatch64.selected_candidate
  have hm : data.multiplier = Real.sqrt (select 1000 data.q 8 (1/100000) 3 [StepsEpsilonEightBatch64.candidate]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := 1000) (by norm_num) hd (by norm_num) (by norm_num) (by norm_num)
    3 (by norm_num) [StepsEpsilonEightBatch64.candidate] hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [StepsEpsilonEightBatch64.candidate, Nat.cast_ofNat] using h


/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_steps_epsilonOne_batch64_private_convergence
    {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (StepsEpsilonOneBatch64.q : ℝ))
    (hmult : data.multiplier = Real.sqrt (StepsEpsilonOneBatch64.V : ℝ))
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
      (f data.initial - fLow) 1000 sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg 1000) 1 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g 1000) 1 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g 1000) 1 (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (StepsEpsilonOneBatch64.V : ℝ) / ((data.q : ℝ) * 50000) ^ 2 ∧
    (1000 : ℝ)⁻¹ * ∑ t : Fin 1000,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          1000 t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate := by
  have hsel : select 1000 data.q 1 (1/100000) 12 [StepsEpsilonOneBatch64.candidate] = StepsEpsilonOneBatch64.candidate := by
    rw [hq]
    exact StepsEpsilonOneBatch64.selected_candidate
  have hm : data.multiplier = Real.sqrt (select 1000 data.q 1 (1/100000) 12 [StepsEpsilonOneBatch64.candidate]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := 1000) (by norm_num) hd (by norm_num) (by norm_num) (by norm_num)
    12 (by norm_num) [StepsEpsilonOneBatch64.candidate] hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [StepsEpsilonOneBatch64.candidate, Nat.cast_ofNat] using h


/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_steps_epsilonEight_batch256_private_convergence
    {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (StepsEpsilonEightBatch256.q : ℝ))
    (hmult : data.multiplier = Real.sqrt (StepsEpsilonEightBatch256.V : ℝ))
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
      (f data.initial - fLow) 1000 sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg 1000) 8 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g 1000) 8 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g 1000) 8 (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (StepsEpsilonEightBatch256.V : ℝ) / ((data.q : ℝ) * 50000) ^ 2 ∧
    (1000 : ℝ)⁻¹ * ∑ t : Fin 1000,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          1000 t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate := by
  have hsel : select 1000 data.q 8 (1/100000) 3 [StepsEpsilonEightBatch256.candidate] = StepsEpsilonEightBatch256.candidate := by
    rw [hq]
    exact StepsEpsilonEightBatch256.selected_candidate
  have hm : data.multiplier = Real.sqrt (select 1000 data.q 8 (1/100000) 3 [StepsEpsilonEightBatch256.candidate]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := 1000) (by norm_num) hd (by norm_num) (by norm_num) (by norm_num)
    3 (by norm_num) [StepsEpsilonEightBatch256.candidate] hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [StepsEpsilonEightBatch256.candidate, Nat.cast_ofNat] using h


/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_steps_epsilonOne_batch256_private_convergence
    {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (StepsEpsilonOneBatch256.q : ℝ))
    (hmult : data.multiplier = Real.sqrt (StepsEpsilonOneBatch256.V : ℝ))
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
      (f data.initial - fLow) 1000 sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg 1000) 1 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g 1000) 1 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g 1000) 1 (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (StepsEpsilonOneBatch256.V : ℝ) / ((data.q : ℝ) * 50000) ^ 2 ∧
    (1000 : ℝ)⁻¹ * ∑ t : Fin 1000,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          1000 t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate := by
  have hsel : select 1000 data.q 1 (1/100000) 18 [StepsEpsilonOneBatch256.candidate] = StepsEpsilonOneBatch256.candidate := by
    rw [hq]
    exact StepsEpsilonOneBatch256.selected_candidate
  have hm : data.multiplier = Real.sqrt (select 1000 data.q 1 (1/100000) 18 [StepsEpsilonOneBatch256.candidate]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := 1000) (by norm_num) hd (by norm_num) (by norm_num) (by norm_num)
    18 (by norm_num) [StepsEpsilonOneBatch256.candidate] hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [StepsEpsilonOneBatch256.candidate, Nat.cast_ofNat] using h


/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_steps_epsilonEight_batch512_private_convergence
    {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (StepsEpsilonEightBatch512.q : ℝ))
    (hmult : data.multiplier = Real.sqrt (StepsEpsilonEightBatch512.V : ℝ))
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
      (f data.initial - fLow) 1000 sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg 1000) 8 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g 1000) 8 (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g 1000) 8 (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (StepsEpsilonEightBatch512.V : ℝ) / ((data.q : ℝ) * 50000) ^ 2 ∧
    (1000 : ℝ)⁻¹ * ∑ t : Fin 1000,
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          1000 t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d 1000 data.q data.q_le_one s) ≤ rate := by
  have hsel : select 1000 data.q 8 (1/100000) 4 [StepsEpsilonEightBatch512.candidate] = StepsEpsilonEightBatch512.candidate := by
    rw [hq]
    exact StepsEpsilonEightBatch512.selected_candidate
  have hm : data.multiplier = Real.sqrt (select 1000 data.q 8 (1/100000) 4 [StepsEpsilonEightBatch512.candidate]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := 1000) (by norm_num) hd (by norm_num) (by norm_num) (by norm_num)
    4 (by norm_num) [StepsEpsilonEightBatch512.candidate] hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [StepsEpsilonEightBatch512.candidate, Nat.cast_ofNat] using h

end Mf.Optimization.PoissonClippedSGD.PrivacyData
