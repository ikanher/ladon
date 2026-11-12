import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch64
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch256
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch1024
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch2048
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch4096
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch512
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch1024
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch2048
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD consumers of eight saved reciprocal-moment certificates

At population 50000, epsilon8 and delta1e-5, these saved cases cover nominal
batches1024/2048/4096 with1000 steps, and batches64/256/512/1024/2048 with
horizons6250/1563/782/391/196. Every case retains its exact decimal variance,
margin and both moment orders. The complete two-direction budget keeps the
actual reciprocal-product bound and the full reverse exponential multiplier.
Singleton selection with fallback order64 chooses precisely the saved candidate.
The actual consumer supplies transcript/final/uniform privacy and both
pre-update utility bounds at that noise and its own public sufficient step.
No budget premise remains; dimension, clipping and measurable query/objective
families remain quantified under the local-smooth utility hypotheses.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.PoissonRawMomentCalibration
open Mf.DP.PoissonGaussianReferenceCertificates
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.SavedReciprocal

inductive Case where
  | epochsEpsilonEightBatch64
  | epochsEpsilonEightBatch256
  | stepsEpsilonEightBatch1024
  | stepsEpsilonEightBatch2048
  | stepsEpsilonEightBatch4096
  | epochsEpsilonEightBatch512
  | epochsEpsilonEightBatch1024
  | epochsEpsilonEightBatch2048
  deriving DecidableEq

def horizon : Case → ℕ
  | .epochsEpsilonEightBatch64 => 6250
  | .epochsEpsilonEightBatch256 => 1563
  | .stepsEpsilonEightBatch1024 => 1000
  | .stepsEpsilonEightBatch2048 => 1000
  | .stepsEpsilonEightBatch4096 => 1000
  | .epochsEpsilonEightBatch512 => 782
  | .epochsEpsilonEightBatch1024 => 391
  | .epochsEpsilonEightBatch2048 => 196

def epsilon (_c : Case) : ℝ := 8

def q : Case → ℚ
  | .epochsEpsilonEightBatch64 => EpochsEpsilonEightBatch64.q
  | .epochsEpsilonEightBatch256 => EpochsEpsilonEightBatch256.q
  | .stepsEpsilonEightBatch1024 => StepsEpsilonEightBatch1024.q
  | .stepsEpsilonEightBatch2048 => StepsEpsilonEightBatch2048.q
  | .stepsEpsilonEightBatch4096 => StepsEpsilonEightBatch4096.q
  | .epochsEpsilonEightBatch512 => EpochsEpsilonEightBatch512.q
  | .epochsEpsilonEightBatch1024 => EpochsEpsilonEightBatch1024.q
  | .epochsEpsilonEightBatch2048 => EpochsEpsilonEightBatch2048.q

def candidate : Case → Candidate
  | .epochsEpsilonEightBatch64 => EpochsEpsilonEightBatch64.candidate
  | .epochsEpsilonEightBatch256 => EpochsEpsilonEightBatch256.candidate
  | .stepsEpsilonEightBatch1024 => StepsEpsilonEightBatch1024.candidate
  | .stepsEpsilonEightBatch2048 => StepsEpsilonEightBatch2048.candidate
  | .stepsEpsilonEightBatch4096 => StepsEpsilonEightBatch4096.candidate
  | .epochsEpsilonEightBatch512 => EpochsEpsilonEightBatch512.candidate
  | .epochsEpsilonEightBatch1024 => EpochsEpsilonEightBatch1024.candidate
  | .epochsEpsilonEightBatch2048 => EpochsEpsilonEightBatch2048.candidate

instance horizon_neZero (c : Case) : NeZero (horizon c) :=
  ⟨by cases c <;> norm_num [horizon]⟩
lemma epsilon_pos (c : Case) : 0 < epsilon c := by norm_num [epsilon]
lemma selected_candidate (c : Case) :
    select (horizon c) (q c) (epsilon c) (1/100000) 64 [candidate c] = candidate c := by
  cases c
  case epochsEpsilonEightBatch64 => exact EpochsEpsilonEightBatch64.selected_candidate
  case epochsEpsilonEightBatch256 => exact EpochsEpsilonEightBatch256.selected_candidate
  case stepsEpsilonEightBatch1024 => exact StepsEpsilonEightBatch1024.selected_candidate
  case stepsEpsilonEightBatch2048 => exact StepsEpsilonEightBatch2048.selected_candidate
  case stepsEpsilonEightBatch4096 => exact StepsEpsilonEightBatch4096.selected_candidate
  case epochsEpsilonEightBatch512 => exact EpochsEpsilonEightBatch512.selected_candidate
  case epochsEpsilonEightBatch1024 => exact EpochsEpsilonEightBatch1024.selected_candidate
  case epochsEpsilonEightBatch2048 => exact EpochsEpsilonEightBatch2048.selected_candidate

end Mf.Optimization.PoissonClippedSGD.SavedReciprocal

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
open SavedReciprocal

/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_reciprocal_private_convergence
    (c : SavedReciprocal.Case) {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (SavedReciprocal.q c : ℝ))
    (hmult : data.multiplier = Real.sqrt (SavedReciprocal.candidate c).variance)
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
      (f data.initial - fLow) (SavedReciprocal.horizon c) sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg (SavedReciprocal.horizon c)) (SavedReciprocal.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g (SavedReciprocal.horizon c)) (SavedReciprocal.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g (SavedReciprocal.horizon c)) (SavedReciprocal.epsilon c) (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (SavedReciprocal.candidate c).variance / ((data.q : ℝ) * 50000) ^ 2 ∧
    ((SavedReciprocal.horizon c) : ℝ)⁻¹ * ∑ t : Fin (SavedReciprocal.horizon c),
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          (SavedReciprocal.horizon c) t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d (SavedReciprocal.horizon c) data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d (SavedReciprocal.horizon c) data.q data.q_le_one s) ≤ rate := by
  have hsel : select (SavedReciprocal.horizon c) data.q (SavedReciprocal.epsilon c) (1/100000)
      64 [SavedReciprocal.candidate c] = SavedReciprocal.candidate c := by
    rw [hq]
    exact SavedReciprocal.selected_candidate c
  have hm : data.multiplier = Real.sqrt
      (select (SavedReciprocal.horizon c) data.q (SavedReciprocal.epsilon c) (1/100000)
        64 [SavedReciprocal.candidate c]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := SavedReciprocal.horizon c) (by norm_num) hd (SavedReciprocal.epsilon_pos c)
    (by norm_num) (by norm_num) 64 (by norm_num) [SavedReciprocal.candidate c]
    hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [Nat.cast_ofNat] using h

end Mf.Optimization.PoissonClippedSGD.PrivacyData
