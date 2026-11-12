import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch4096
import Mf.DP.PoissonGaussianReferenceCertificates.StepsEpsilonOneBatch8192
import Mf.Optimization.PoissonClippedSGD.RawMomentConvergence

/-!
# Actual DP-SGD consumers of saved Gaussian-reference certificates

Two saved centered-forward cases at epsilon1, T1000 and nominal batches4096/8192 retain orders8/7 and use the actual Bennett reverse order. Fallback initializer1024 selects the unchanged candidates.
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
namespace Mf.Optimization.PoissonClippedSGD.SavedCenteredBennett

inductive Case where
  | stepsEpsilonOneBatch4096
  | stepsEpsilonOneBatch8192
  deriving DecidableEq

def horizon : Case → ℕ
  | .stepsEpsilonOneBatch4096 => 1000
  | .stepsEpsilonOneBatch8192 => 1000

def epsilon : Case → ℝ
  | .stepsEpsilonOneBatch4096 => 1
  | .stepsEpsilonOneBatch8192 => 1

def q : Case → ℚ
  | .stepsEpsilonOneBatch4096 => StepsEpsilonOneBatch4096.q
  | .stepsEpsilonOneBatch8192 => StepsEpsilonOneBatch8192.q

def candidate : Case → Candidate
  | .stepsEpsilonOneBatch4096 => StepsEpsilonOneBatch4096.candidate
  | .stepsEpsilonOneBatch8192 => StepsEpsilonOneBatch8192.candidate

instance horizon_neZero (c : Case) : NeZero (horizon c) :=
  ⟨by cases c <;> norm_num [horizon]⟩
lemma epsilon_pos (c : Case) : 0 < epsilon c := by cases c <;> norm_num [epsilon]
lemma selected_candidate (c : Case) :
    select (horizon c) (q c) (epsilon c) (1/100000) 1024 [candidate c] = candidate c := by
  cases c
  case stepsEpsilonOneBatch4096 => exact StepsEpsilonOneBatch4096.selected_candidate
  case stepsEpsilonOneBatch8192 => exact StepsEpsilonOneBatch8192.selected_candidate

end Mf.Optimization.PoissonClippedSGD.SavedCenteredBennett

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData
open SavedCenteredBennett

/-- The unchanged saved candidate has actual transcript/output privacy and same-noise utility. -/
theorem savedGrid_centered_bennett_private_convergence
    (c : SavedCenteredBennett.Case) {d : ℕ} {Record : Type} (data : PrivacyData 50000 d)
    (hd : 0 < d) (hq : (data.q : ℝ) = (SavedCenteredBennett.q c : ℝ))
    (hmult : data.multiplier = Real.sqrt (SavedCenteredBennett.candidate c).variance)
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
      (f data.initial - fLow) (SavedCenteredBennett.horizon c) sigma data.clipping (poissonVariance 50000 data.q) s
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg (SavedCenteredBennett.horizon c)) (SavedCenteredBennett.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g (SavedCenteredBennett.horizon c)) (SavedCenteredBennett.epsilon c) (1/100000) ∧
    ApproxDP OptionalRecordAdjacent (data.optionalUniformLaw g (SavedCenteredBennett.horizon c)) (SavedCenteredBennett.epsilon c) (1/100000) ∧
    s ^ 2 = data.clipping ^ 2 * d * (SavedCenteredBennett.candidate c).variance / ((data.q : ℝ) * 50000) ^ 2 ∧
    ((SavedCenteredBennett.horizon c) : ℝ)⁻¹ * ∑ t : Fin (SavedCenteredBennett.horizon c),
      (∫ ω, ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          (SavedCenteredBennett.horizon c) t.val t.isLt.le ω))‖ ∂gaussianHistoryLaw 50000 d (SavedCenteredBennett.horizon c) data.q data.q_le_one s) ≤ rate ∧
    (∫ p, ‖vectorMean (fun i => slotGradient g D i
      (output data.eta data.q data.clipping (slotGradient g D) data.initial p))‖
      ∂outputLaw 50000 d (SavedCenteredBennett.horizon c) data.q data.q_le_one s) ≤ rate := by
  have hsel : select (SavedCenteredBennett.horizon c) data.q (SavedCenteredBennett.epsilon c) (1/100000)
      1024 [SavedCenteredBennett.candidate c] = SavedCenteredBennett.candidate c := by
    rw [hq]
    exact SavedCenteredBennett.selected_candidate c
  have hm : data.multiplier = Real.sqrt
      (select (SavedCenteredBennett.horizon c) data.q (SavedCenteredBennett.epsilon c) (1/100000)
        1024 [SavedCenteredBennett.candidate c]).variance := by
    rw [hsel]
    exact hmult
  have h := data.rawMoment_private_convergence_of_selection
    (T := SavedCenteredBennett.horizon c) (by norm_num) hd (SavedCenteredBennett.epsilon_pos c)
    (by norm_num) (by norm_num) 1024 (by norm_num) [SavedCenteredBennett.candidate c]
    hm hsigma hL0 hL1 heta g hg D f hf hloc hvariance fLow hlower
  rw [hsel] at h
  simpa only [Nat.cast_ofNat] using h

end Mf.Optimization.PoissonClippedSGD.PrivacyData
