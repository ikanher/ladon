import Mf.DP.FiniteProfileCoefficientDuality
import Mf.DP.SparseGaussianProductForwardUpperBound

/-!
# Reverse sparse-Gaussian product profile bounds

The direct mixture likelihood is bounded below by the probability that no
coordinate participates.  This gives a simple finite reverse hockey-stick
upper bound without any reciprocal-coefficient transport.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

set_option autoImplicit false

def sparseGaussianProductReverseLikelihoodFloorUpperBound
    (horizon : Nat) (samplingRate : NNReal) (epsilon : Real) : ENNReal :=
  ENNReal.ofReal
    (1 - Real.exp epsilon * (1 - (samplingRate : Real)) ^ horizon)

def sparseGaussianProductReverseReciprocalUpperBound
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift epsilon threshold : Real) : ENNReal :=
  ENNReal.ofReal
    (1 - Real.exp epsilon + Real.exp epsilon *
      (sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound horizon
        samplingRate standardizedShift (-epsilon) threshold).toReal)

def sparseGaussianProductReverseBestUpperBound
    (horizon : Nat) (samplingRate : NNReal)
    (standardizedShift epsilon threshold : Real) : ENNReal :=
  min (sparseGaussianProductReverseReciprocalUpperBound horizon samplingRate
      standardizedShift epsilon threshold)
    (sparseGaussianProductReverseLikelihoodFloorUpperBound horizon samplingRate epsilon)

/-- The reverse normalized product profile is controlled by the unsampled-mass
likelihood floor. -/
theorem sparseGaussianProductReverseProfile_le_likelihoodFloorUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon : Real) :
    eventHockeyStickProfile
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductReverseLikelihoodFloorUpperBound horizon samplingRate epsilon := by
  change eventHockeyStickProfile
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1))
      (Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)))
      epsilon ≤ _
  rw [sparseGaussianProductLaw_eq_withDensity horizon samplingRate hRate
    standardizedShift]
  let reference : ProbabilityMeasure (Fin horizon → Real) :=
    ⟨Measure.pi (fun _ : Fin horizon => gaussianReal 0 1), by infer_instance⟩
  have hreverse := eventHockeyStickProfile_withDensity_reverse reference
    (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real) standardizedShift)
    (measurable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
    (fun sample => (sparseGaussianProductLikelihoodRatio_pos horizon samplingRate hRate
      standardizedShift sample).le)
    epsilon
  have hreference : (reference : Measure (Fin horizon → Real)) =
      Measure.pi (fun _ : Fin horizon => gaussianReal 0 1) := rfl
  rw [hreference] at hreverse
  rw [hreverse]
  unfold sparseGaussianProductReverseLikelihoodFloorUpperBound
  calc
    (∫⁻ sample, ENNReal.ofReal
        (1 - Real.exp epsilon *
          sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
            standardizedShift sample)
        ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) ≤
      ∫⁻ _sample : Fin horizon → Real, ENNReal.ofReal
        (1 - Real.exp epsilon * (1 - (samplingRate : Real)) ^ horizon)
        ∂Measure.pi (fun _ : Fin horizon => gaussianReal 0 1) := by
      apply lintegral_mono
      intro sample
      apply ENNReal.ofReal_le_ofReal
      have hfloor := sparseGaussianProductLikelihoodRatio_ge_floor horizon samplingRate hRate
        standardizedShift sample
      exact sub_le_sub_left
        (mul_le_mul_of_nonneg_left hfloor (Real.exp_pos epsilon).le) 1
    _ = ENNReal.ofReal
        (1 - Real.exp epsilon * (1 - (samplingRate : Real)) ^ horizon) := by
      simp

/-- Reciprocal-coefficient reverse upper bound obtained from the forward bound
through the safe real-valued duality theorem. -/
theorem sparseGaussianProductReverseProfile_le_reciprocalUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) :
    eventHockeyStickProfile
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductReverseReciprocalUpperBound horizon samplingRate
        standardizedShift epsilon threshold := by
  change eventHockeyStickProfile
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1))
      (Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)))
      epsilon ≤ _
  rw [sparseGaussianProductLaw_eq_withDensity horizon samplingRate hRate
    standardizedShift]
  let reference : ProbabilityMeasure (Fin horizon → Real) :=
    ⟨Measure.pi (fun _ : Fin horizon => gaussianReal 0 1), by infer_instance⟩
  have hdual := eventHockeyStickProfile_withDensity_reverse_duality reference
    (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real) standardizedShift)
    (measurable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
    (fun sample => (sparseGaussianProductLikelihoodRatio_pos horizon samplingRate hRate
      standardizedShift sample).le)
    (integrable_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
    (integral_sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
      standardizedShift)
    epsilon
  have hreference : (reference : Measure (Fin horizon → Real)) =
      Measure.pi (fun _ : Fin horizon => gaussianReal 0 1) := rfl
  rw [hreference] at hdual
  rw [hdual]
  unfold sparseGaussianProductReverseReciprocalUpperBound
  apply ENNReal.ofReal_le_ofReal
  have hforwardBound :=
    sparseGaussianProductForwardProfile_le_cappedRestrictedSecondMomentUpperBound
      horizon samplingRate hRate standardizedShift (-epsilon) threshold
  change eventHockeyStickProfile
      (Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)))
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1)) (-epsilon) ≤ _
      at hforwardBound
  rw [sparseGaussianProductLaw_eq_withDensity horizon samplingRate hRate
    standardizedShift] at hforwardBound
  have htoReal :
      (eventHockeyStickProfile
        ((Measure.pi fun _ : Fin horizon => gaussianReal 0 1).withDensity
          fun sample => ENNReal.ofReal
            (sparseGaussianProductLikelihoodRatio horizon (samplingRate : Real)
              standardizedShift sample))
        (Measure.pi fun _ : Fin horizon => gaussianReal 0 1) (-epsilon)).toReal ≤
      (sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound horizon
        samplingRate standardizedShift (-epsilon) threshold).toReal := by
    apply ENNReal.toReal_mono
    · simp [sparseGaussianProductForwardCappedRestrictedSecondMomentUpperBound]
    · exact hforwardBound
  nlinarith [mul_le_mul_of_nonneg_left htoReal (Real.exp_pos epsilon).le]

/-- The selected reverse bound is the minimum of two independently verified
upper bounds. -/
theorem sparseGaussianProductReverseProfile_le_bestUpperBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) :
    eventHockeyStickProfile
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real)) epsilon ≤
      sparseGaussianProductReverseBestUpperBound horizon samplingRate
        standardizedShift epsilon threshold := by
  apply le_min
  · exact sparseGaussianProductReverseProfile_le_reciprocalUpperBound horizon
      samplingRate hRate standardizedShift epsilon threshold
  · exact sparseGaussianProductReverseProfile_le_likelihoodFloorUpperBound horizon
      samplingRate hRate standardizedShift epsilon

end

end Mf.DP
