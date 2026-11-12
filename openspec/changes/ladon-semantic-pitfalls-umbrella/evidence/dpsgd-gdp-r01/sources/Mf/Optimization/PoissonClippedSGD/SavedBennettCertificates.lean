import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch64
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch256
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch512
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch1024
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch2048
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonEightBatch8192
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch512
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch1024
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch2048
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD consumers of saved Gaussian-reference certificates

Nine saved raw-moment cases use the actual public Bennett order and its certified logarithm/exponent bounds. Fallback initializer64 selects each unchanged candidate.
Every case retains its exact decimal variance, sampling probability, horizon,
margin and saved moment orders. The complete two-direction budget is proved
by the leaf owner. The actual consumer internally discharges singleton selection
and privacy, then uses the selected noise and its own public step for both
pre-update utility observables. No budget premise remains. Population50000 and
delta1e-5 are fixed; dimension, clipping and the measurable query/objective
families remain quantified under the local-smooth utility hypotheses.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.PoissonRawMomentCalibration
open Mf.DP.PoissonGaussianReferenceCertificates
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.SavedBennett

inductive Case where
  | epochsEpsilonOneBatch64
  | epochsEpsilonOneBatch256
  | stepsEpsilonOneBatch512
  | stepsEpsilonOneBatch1024
  | stepsEpsilonOneBatch2048
  | stepsEpsilonEightBatch8192
  | epochsEpsilonOneBatch512
  | epochsEpsilonOneBatch1024
  | epochsEpsilonOneBatch2048
  deriving DecidableEq

def horizon : Case → ℕ
  | .epochsEpsilonOneBatch64 => 6250
  | .epochsEpsilonOneBatch256 => 1563
  | .stepsEpsilonOneBatch512 => 1000
  | .stepsEpsilonOneBatch1024 => 1000
  | .stepsEpsilonOneBatch2048 => 1000
  | .stepsEpsilonEightBatch8192 => 1000
  | .epochsEpsilonOneBatch512 => 782
  | .epochsEpsilonOneBatch1024 => 391
  | .epochsEpsilonOneBatch2048 => 196

def epsilon : Case → ℝ
  | .epochsEpsilonOneBatch64 => 1
  | .epochsEpsilonOneBatch256 => 1
  | .stepsEpsilonOneBatch512 => 1
  | .stepsEpsilonOneBatch1024 => 1
  | .stepsEpsilonOneBatch2048 => 1
  | .stepsEpsilonEightBatch8192 => 8
  | .epochsEpsilonOneBatch512 => 1
  | .epochsEpsilonOneBatch1024 => 1
  | .epochsEpsilonOneBatch2048 => 1

def q : Case → ℚ
  | .epochsEpsilonOneBatch64 => EpochsEpsilonOneBatch64.q
  | .epochsEpsilonOneBatch256 => EpochsEpsilonOneBatch256.q
  | .stepsEpsilonOneBatch512 => StepsEpsilonOneBatch512.q
  | .stepsEpsilonOneBatch1024 => StepsEpsilonOneBatch1024.q
  | .stepsEpsilonOneBatch2048 => StepsEpsilonOneBatch2048.q
  | .stepsEpsilonEightBatch8192 => StepsEpsilonEightBatch8192.q
  | .epochsEpsilonOneBatch512 => EpochsEpsilonOneBatch512.q
  | .epochsEpsilonOneBatch1024 => EpochsEpsilonOneBatch1024.q
  | .epochsEpsilonOneBatch2048 => EpochsEpsilonOneBatch2048.q

def candidate : Case → Candidate
  | .epochsEpsilonOneBatch64 => EpochsEpsilonOneBatch64.candidate
  | .epochsEpsilonOneBatch256 => EpochsEpsilonOneBatch256.candidate
  | .stepsEpsilonOneBatch512 => StepsEpsilonOneBatch512.candidate
  | .stepsEpsilonOneBatch1024 => StepsEpsilonOneBatch1024.candidate
  | .stepsEpsilonOneBatch2048 => StepsEpsilonOneBatch2048.candidate
  | .stepsEpsilonEightBatch8192 => StepsEpsilonEightBatch8192.candidate
  | .epochsEpsilonOneBatch512 => EpochsEpsilonOneBatch512.candidate
  | .epochsEpsilonOneBatch1024 => EpochsEpsilonOneBatch1024.candidate
  | .epochsEpsilonOneBatch2048 => EpochsEpsilonOneBatch2048.candidate

instance horizon_neZero (c : Case) : NeZero (horizon c) :=
  ⟨by cases c <;> norm_num [horizon]⟩
lemma epsilon_pos (c : Case) : 0 < epsilon c := by cases c <;> norm_num [epsilon]
lemma selected_candidate (c : Case) :
    select (horizon c) (q c) (epsilon c) (1/100000) 64 [candidate c] = candidate c := by
  cases c
  case epochsEpsilonOneBatch64 => exact EpochsEpsilonOneBatch64.selected_candidate
  case epochsEpsilonOneBatch256 => exact EpochsEpsilonOneBatch256.selected_candidate
  case stepsEpsilonOneBatch512 => exact StepsEpsilonOneBatch512.selected_candidate
  case stepsEpsilonOneBatch1024 => exact StepsEpsilonOneBatch1024.selected_candidate
  case stepsEpsilonOneBatch2048 => exact StepsEpsilonOneBatch2048.selected_candidate
  case stepsEpsilonEightBatch8192 => exact StepsEpsilonEightBatch8192.selected_candidate
  case epochsEpsilonOneBatch512 => exact EpochsEpsilonOneBatch512.selected_candidate
  case epochsEpsilonOneBatch1024 => exact EpochsEpsilonOneBatch1024.selected_candidate
  case epochsEpsilonOneBatch2048 => exact EpochsEpsilonOneBatch2048.selected_candidate

end Mf.Optimization.PoissonClippedSGD.SavedBennett

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
open SavedBennett

/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_bennett_private_convergence
    (c : SavedBennett.Case) {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (SavedBennett.q c : ℝ))
    (hmult : data.multiplier = Real.sqrt (SavedBennett.candidate c).variance)
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
      (f data.initial - fLow) (SavedBennett.horizon c) sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg (SavedBennett.horizon c)) (SavedBennett.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g (SavedBennett.horizon c)) (SavedBennett.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g (SavedBennett.horizon c)) (SavedBennett.epsilon c) (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (SavedBennett.candidate c).variance / ((data.q : ℝ) * 50000) ^ 2 ∧
    ((SavedBennett.horizon c) : ℝ)⁻¹ * ∑ t : Fin (SavedBennett.horizon c),
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          (SavedBennett.horizon c) t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d (SavedBennett.horizon c) data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d (SavedBennett.horizon c) data.q data.q_le_one s) ≤ rate := by
  have hsel : select (SavedBennett.horizon c) data.q (SavedBennett.epsilon c) (1/100000)
      64 [SavedBennett.candidate c] = SavedBennett.candidate c := by
    rw [hq]
    exact SavedBennett.selected_candidate c
  have hm : data.multiplier = Real.sqrt
      (select (SavedBennett.horizon c) data.q (SavedBennett.epsilon c) (1/100000)
        64 [SavedBennett.candidate c]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := SavedBennett.horizon c) (by norm_num) hd (SavedBennett.epsilon_pos c)
    (by norm_num) (by norm_num) 64 (by norm_num) [SavedBennett.candidate c]
    hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [Nat.cast_ofNat] using h

end Mf.Optimization.PoissonClippedSGD.PrivacyData
