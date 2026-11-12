import Mf.Optimization.PoissonClippedSGD.MatchedParameters

/-!
# Exact parameter boundaries for the matched Poisson comparison

The singleton example has expected batch size one half, epsilon equal to q²T,
and the largest allowed delta. It checks the repaired domain without imposing
a lower bound of one on the expected batch size, and checks both exact RMS
noise energies at that boundary.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.MatchedParametersAudit
open MatchedParameters Mf.Optimization.ClippedSGD

theorem singletonBoundary : MatchedPrivacyDomain 1 1 4 (1 / 2) 1 1 (Real.exp (-1)) := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num, by norm_num,
    by norm_num, by norm_num, by norm_num, by norm_num, Real.exp_pos _, le_rfl⟩

example : (baselineNoise 1 1 4 (1 / 2) 1 1 (Real.exp (-1))) ^ 2 = 64 := by
  rw [baselineNoise_sq singletonBoundary]
  norm_num [one_div, Real.log_inv, Real.log_exp]

example : (gaussianReferenceNoise 1 1 4 (1 / 2) 1 1 (Real.exp (-1))) ^ 2 = 128 := by
  rw [gaussianReferenceNoise_sq singletonBoundary]
  norm_num [one_div, Real.log_inv, Real.log_exp]

example {L1 : ℝ} (hL1 : 0 ≤ L1) :
    let s := gaussianReferenceNoise 1 1 4 (1 / 2) 1 1 (Real.exp (-1))
    let η := publicStepsize 1 L1 (1 + poissonVariance 1 (1 / 2))
      (poissonVariance 1 (1 / 2)) (1 / (1 / 2)) 1 s
    0 < η ∧ StepConditions η 1 L1 (1 + poissonVariance 1 (1 / 2))
      (poissonVariance 1 (1 / 2)) (1 / (1 / 2)) 1 s :=
  gaussianReference_publicStepsize_spec singletonBoundary (by norm_num) hL1

#print axioms calibratedVariance_eq_two_mul
#print axioms gaussianReferenceNoise_eq
#print axioms baselineNoise_pos
#print axioms gaussianReferenceNoise_pos
#print axioms baselineNoise_sq
#print axioms gaussianReferenceNoise_sq
#print axioms baseline_publicStepsize_spec
#print axioms gaussianReference_publicStepsize_spec
#print axioms singletonBoundary

end Mf.Optimization.PoissonClippedSGD.MatchedParametersAudit
