import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch4096
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonOneBatch8192
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch4096
import Mf.DP.PoissonGaussianReferenceCertificates.EpochsEpsilonEightBatch8192
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD consumers of four saved epoch-budget floor certificates

Population 50000, nominal batch 4096 or 8192, horizon 98 or 49, epsilon 1 or 8,
and delta 1e-5 are fixed by the case. The original exact decimal variances,
forward orders and margins are retained. Singleton selection uses fallback
order64 but selects the saved candidate with its own forward order. The
reverse floor is proved zero, and both complete privacy branches are certified.
No privacy-budget premise remains in the actual consumer. Its public step and
full local-smooth utility use exactly the saved candidate's noise. Dimension,
clipping and measurable query/objective families remain quantified.
-/

noncomputable section
open MeasureTheory Mf.DP Mf.DP.PoissonRawMomentCalibration
open Mf.DP.PoissonGaussianReferenceCertificates
open Mf.Optimization.ClippedSGD
namespace Mf.Optimization.PoissonClippedSGD.SavedEpochFloor

inductive Case where
  | epsilonOneBatch4096
  | epsilonOneBatch8192
  | epsilonEightBatch4096
  | epsilonEightBatch8192
  deriving DecidableEq

def horizon : Case → ℕ
  | .epsilonOneBatch4096 => 98
  | .epsilonOneBatch8192 => 49
  | .epsilonEightBatch4096 => 98
  | .epsilonEightBatch8192 => 49

def epsilon : Case → ℝ
  | .epsilonOneBatch4096 => 1
  | .epsilonOneBatch8192 => 1
  | .epsilonEightBatch4096 => 8
  | .epsilonEightBatch8192 => 8

def q : Case → ℚ
  | .epsilonOneBatch4096 => EpochsEpsilonOneBatch4096.q
  | .epsilonOneBatch8192 => EpochsEpsilonOneBatch8192.q
  | .epsilonEightBatch4096 => EpochsEpsilonEightBatch4096.q
  | .epsilonEightBatch8192 => EpochsEpsilonEightBatch8192.q

def candidate : Case → Candidate
  | .epsilonOneBatch4096 => EpochsEpsilonOneBatch4096.candidate
  | .epsilonOneBatch8192 => EpochsEpsilonOneBatch8192.candidate
  | .epsilonEightBatch4096 => EpochsEpsilonEightBatch4096.candidate
  | .epsilonEightBatch8192 => EpochsEpsilonEightBatch8192.candidate

instance horizon_neZero (c : Case) : NeZero (horizon c) :=
  ⟨by cases c <;> norm_num [horizon]⟩
lemma epsilon_pos (c : Case) : 0 < epsilon c := by cases c <;> norm_num [epsilon]
lemma selected_candidate (c : Case) :
    select (horizon c) (q c) (epsilon c) (1/100000) 64 [candidate c] = candidate c := by
  cases c
  case epsilonOneBatch4096 => exact EpochsEpsilonOneBatch4096.selected_candidate
  case epsilonOneBatch8192 => exact EpochsEpsilonOneBatch8192.selected_candidate
  case epsilonEightBatch4096 => exact EpochsEpsilonEightBatch4096.selected_candidate
  case epsilonEightBatch8192 => exact EpochsEpsilonEightBatch8192.selected_candidate

end Mf.Optimization.PoissonClippedSGD.SavedEpochFloor

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
open SavedEpochFloor

/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_epochs_floor_private_convergence
    (c : SavedEpochFloor.Case) {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (SavedEpochFloor.q c : ℝ))
    (hmult : data.multiplier = Real.sqrt (SavedEpochFloor.candidate c).variance)
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
      (f data.initial - fLow) (SavedEpochFloor.horizon c) sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg (SavedEpochFloor.horizon c)) (SavedEpochFloor.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g (SavedEpochFloor.horizon c)) (SavedEpochFloor.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g (SavedEpochFloor.horizon c)) (SavedEpochFloor.epsilon c) (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (SavedEpochFloor.candidate c).variance / ((data.q : ℝ) * 50000) ^ 2 ∧
    ((SavedEpochFloor.horizon c) : ℝ)⁻¹ * ∑ t : Fin (SavedEpochFloor.horizon c),
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          (SavedEpochFloor.horizon c) t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d (SavedEpochFloor.horizon c) data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d (SavedEpochFloor.horizon c) data.q data.q_le_one s) ≤ rate := by
  have hsel : select (SavedEpochFloor.horizon c) data.q (SavedEpochFloor.epsilon c) (1/100000)
      64 [SavedEpochFloor.candidate c] = SavedEpochFloor.candidate c := by
    rw [hq]
    exact SavedEpochFloor.selected_candidate c
  have hm : data.multiplier = Real.sqrt
      (select (SavedEpochFloor.horizon c) data.q (SavedEpochFloor.epsilon c) (1/100000)
        64 [SavedEpochFloor.candidate c]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := SavedEpochFloor.horizon c) (by norm_num) hd (SavedEpochFloor.epsilon_pos c)
    (by norm_num) (by norm_num) 64 (by norm_num) [SavedEpochFloor.candidate c]
    hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [Nat.cast_ofNat] using h

end Mf.Optimization.PoissonClippedSGD.PrivacyData
