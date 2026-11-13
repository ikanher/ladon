import Mf.DP.MatchedGaussianSourceNormalization
import Mf.DP.SampledGaussianProductEventDistance

/-!
# Sampled Gaussian product accounting convergence

The exact sampled source product is compared with its matched Gaussian source
product while the privacy reference law is kept identical.  The source-only
event-distance estimate therefore transports to the binary accounting profile
with the valid inherited bound `(1 + exp epsilon) * distance`.  No sharpness
claim is made for the identical-reference specialization.
-/

open Filter MeasureTheory
open scoped ENNReal NNReal Topology

namespace Mf.DP

noncomputable section

/-- Source event distance controls both directions of the actual/matched accountant. -/
theorem binaryAccountingProfile_actualMatched_stability
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal)
    (epsilon : Real) (distance : ENNReal)
    (hDistance : UniformEventDistance
      (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
        (noiseStddev ^ 2) : Measure (Fin horizon → Real))
      (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
        (noiseStddev ^ 2) : Measure (Fin horizon → Real)) distance) :
    binaryAccountingProfile
        (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon ≤
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon +
          (1 + ENNReal.ofReal (Real.exp epsilon)) * distance ∧
    binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon ≤
      binaryAccountingProfile
        (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon +
          (1 + ENNReal.ofReal (Real.exp epsilon)) * distance := by
  exact binaryAccountingProfile_stable_uniformEventDistance epsilon hDistance
    ((UniformEventDistance.refl _).mono
      (zero_le : (0 : ENNReal) ≤ distance))

/-- Eventual centered-source control yields eventual actual/matched accountant control. -/
theorem binaryAccountingProfile_eventually_actualMatched_close
    (noiseStddev : Nat → NNReal) (samplingRate : NNReal)
    (hRate : samplingRate ≤ 1) (sensitivity epsilon : Real)
    (distance : Nat → ENNReal)
    (hPositive : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon)
    (hCentered : ∀ᶠ horizon : Nat in atTop,
      UniformEventDistance
        (centeredBernoulliGaussianProductLaw horizon samplingRate hRate
          (sensitivity / (noiseStddev horizon : Real)) :
          Measure (Fin horizon → Real))
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
        (distance horizon)) :
    ∀ᶠ horizon : Nat in atTop,
      binaryAccountingProfile
          (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
            (noiseStddev horizon ^ 2))
          (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
          epsilon ≤
        binaryAccountingProfile
          (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
            (noiseStddev horizon ^ 2))
          (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
          epsilon + (1 + ENNReal.ofReal (Real.exp epsilon)) * distance horizon ∧
      binaryAccountingProfile
          (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
            (noiseStddev horizon ^ 2))
          (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
          epsilon ≤
        binaryAccountingProfile
          (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
            (noiseStddev horizon ^ 2))
          (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
          epsilon + (1 + ENNReal.ofReal (Real.exp epsilon)) * distance horizon := by
  filter_upwards [hPositive, hCentered] with horizon hStddev hDistance
  have hActual := sampledGaussianSourceProduct_uniformEventDistance_of_standardized
    horizon samplingRate hRate sensitivity (noiseStddev horizon) hStddev
      (distance horizon) hDistance
  exact binaryAccountingProfile_actualMatched_stability horizon samplingRate hRate
    sensitivity (noiseStddev horizon) epsilon (distance horizon) hActual

/-- Multiplying a vanishing event-distance witness by the fixed oracle factor preserves its limit. -/
theorem tendsto_oracleStabilityError_zero
    (epsilon : Real) (distance : Nat → ENNReal)
    (hDistance : Tendsto distance atTop (nhds 0)) :
    Tendsto (fun horizon =>
      (1 + ENNReal.ofReal (Real.exp epsilon)) * distance horizon)
      atTop (nhds 0) := by
  simpa using ENNReal.Tendsto.const_mul hDistance (by simp)

/-- Linear noise-variance growth packages the corrected source-law convergence theorem:
the exact sampled source products approach their matched Gaussian source products in
uniform event distance.  The privacy reference law is deliberately absent here. -/
theorem sampledGaussianSourceProduct_eventually_uniformEventDistance_of_growth
    (noiseStddev : Nat → NNReal) (samplingRate : NNReal)
    (hRate : samplingRate ≤ 1) (sensitivity : Real)
    {growthCoefficient : Real} (hCoefficient : 0 < growthCoefficient)
    (hSensitivity : 0 < sensitivity)
    (hGrowth : ∀ᶠ horizon : Nat in atTop,
      growthCoefficient * (horizon : Real) ≤ (noiseStddev horizon : Real) ^ 2) :
    ∃ distance : Nat → ENNReal,
      Tendsto distance atTop (nhds 0) ∧
      ∀ᶠ horizon : Nat in atTop,
        UniformEventDistance
          (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
            (noiseStddev horizon ^ 2) : Measure (Fin horizon → Real))
          (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
            (noiseStddev horizon ^ 2) : Measure (Fin horizon → Real))
          (distance horizon) := by
  obtain ⟨constant, _, hCentered⟩ :=
    centeredBernoulliGaussianProduct_eventually_expBound samplingRate hRate
      sensitivity noiseStddev hCoefficient hSensitivity hGrowth
  let distance : Nat → ENNReal := fun horizon => ENNReal.ofReal
    (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1))
  have hDistance : Tendsto distance atTop (nhds 0) := by
    simpa [distance] using tendsto_expProductEventDistance_zero constant
  have hPositive : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon := by
    filter_upwards [hGrowth, eventually_gt_atTop (0 : Nat)] with horizon hG hHorizon
    have hHorizonReal : 0 < (horizon : Real) := by exact_mod_cast hHorizon
    have hSquare : 0 < (noiseStddev horizon : Real) ^ 2 :=
      (mul_pos hCoefficient hHorizonReal).trans_le hG
    exact_mod_cast (by nlinarith : 0 < (noiseStddev horizon : Real))
  refine ⟨distance, hDistance, ?_⟩
  filter_upwards [hPositive, hCentered] with horizon hStddev hCenteredDistance
  exact sampledGaussianSourceProduct_uniformEventDistance_of_standardized
    horizon samplingRate hRate sensitivity (noiseStddev horizon) hStddev
      (distance horizon) hCenteredDistance

/-- Explicit linear variance growth is enough to compare the sampled accountant with
its matched-Gaussian accountant.  Unlike the privacy-driven corollary below, this
theorem applies to candidate sequences that may deliberately be infeasible. -/
theorem sampledGaussianProduct_accountingProfile_eventually_close_matched_of_growth
    (noiseStddev : Nat → NNReal) (samplingRate : NNReal)
    (hRate : samplingRate ≤ 1) (sensitivity epsilon : Real)
    {growthCoefficient : Real} (hCoefficient : 0 < growthCoefficient)
    (hSensitivity : 0 < sensitivity)
    (hGrowth : ∀ᶠ horizon : Nat in atTop,
      growthCoefficient * (horizon : Real) ≤ (noiseStddev horizon : Real) ^ 2) :
    ∃ error : Nat → ENNReal,
      Tendsto error atTop (nhds 0) ∧
      ∀ᶠ horizon : Nat in atTop,
        binaryAccountingProfile
            (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon ≤
          binaryAccountingProfile
            (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon + error horizon ∧
        binaryAccountingProfile
            (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon ≤
          binaryAccountingProfile
            (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon + error horizon := by
  obtain ⟨constant, _, hCentered⟩ :=
    centeredBernoulliGaussianProduct_eventually_expBound samplingRate hRate
      sensitivity noiseStddev hCoefficient hSensitivity hGrowth
  let distance : Nat → ENNReal := fun horizon => ENNReal.ofReal
    (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1))
  let error : Nat → ENNReal := fun horizon =>
    (1 + ENNReal.ofReal (Real.exp epsilon)) * distance horizon
  have hDistance : Tendsto distance atTop (nhds 0) := by
    simpa [distance] using tendsto_expProductEventDistance_zero constant
  have hError : Tendsto error atTop (nhds 0) := by
    simpa [error] using tendsto_oracleStabilityError_zero epsilon distance hDistance
  have hPositive : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon := by
    filter_upwards [hGrowth, eventually_gt_atTop (0 : Nat)] with horizon hG hHorizon
    have hHorizonReal : 0 < (horizon : Real) := by exact_mod_cast hHorizon
    have hSquare : 0 < (noiseStddev horizon : Real) ^ 2 :=
      (mul_pos hCoefficient hHorizonReal).trans_le hG
    exact_mod_cast (by nlinarith : 0 < (noiseStddev horizon : Real))
  have hProfiles := binaryAccountingProfile_eventually_actualMatched_close
    noiseStddev samplingRate hRate sensitivity epsilon distance hPositive hCentered
  refine ⟨error, hError, ?_⟩
  simpa [error] using hProfiles

/-- A complete-product-private sequence is asymptotically equivalent to its matched accountant. -/
theorem sampledGaussianProduct_accountingProfile_eventually_close_matched
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : Nat → NNReal) (epsilon delta : Real)
    (hRatePos : 0 < samplingRate) (hSensitivity : 0 < sensitivity)
    (hDelta : 0 ≤ delta) (hDeltaOne : delta < 1)
    (hPrivate : ∀ horizon : Nat, 0 < horizon →
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev horizon ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
        epsilon ≤ ENNReal.ofReal delta) :
    ∃ constant : Real, 0 ≤ constant ∧
      Tendsto (fun horizon : Nat => ENNReal.ofReal
        (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1)))
        atTop (nhds 0) ∧
      Tendsto (fun horizon : Nat =>
        (1 + ENNReal.ofReal (Real.exp epsilon)) * ENNReal.ofReal
          (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1)))
        atTop (nhds 0) ∧
      ∀ᶠ horizon : Nat in atTop,
        binaryAccountingProfile
            (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon ≤
          binaryAccountingProfile
            (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon + (1 + ENNReal.ofReal (Real.exp epsilon)) * ENNReal.ofReal
              (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1)) ∧
        binaryAccountingProfile
            (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon ≤
          binaryAccountingProfile
            (matchedGaussianSourceProductLaw horizon samplingRate sensitivity
              (noiseStddev horizon ^ 2))
            (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2))
            epsilon + (1 + ENNReal.ofReal (Real.exp epsilon)) * ENNReal.ofReal
              (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1)) := by
  obtain ⟨constant, hConstant, hDistanceLimit, hCentered⟩ :=
    sampledGaussianProduct_eventually_expBound_of_profile samplingRate hRate
      sensitivity noiseStddev epsilon delta hRatePos hSensitivity hDelta hDeltaOne
      hPrivate
  obtain ⟨growthCoefficient, hCoefficient, hGrowth⟩ :=
    sampledGaussian_noiseStddev_sq_eventually_linear_of_productProfile
      samplingRate hRate sensitivity noiseStddev epsilon delta hRatePos
      hSensitivity hDelta hDeltaOne hPrivate
  have hPositive : ∀ᶠ horizon : Nat in atTop, 0 < noiseStddev horizon := by
    filter_upwards [hGrowth, eventually_gt_atTop (0 : Nat)] with horizon hG hHorizon
    have hHorizonReal : 0 < (horizon : Real) := by exact_mod_cast hHorizon
    have hSquare : 0 < (noiseStddev horizon : Real) ^ 2 :=
      (mul_pos hCoefficient hHorizonReal).trans_le hG
    exact_mod_cast (by nlinarith : 0 < (noiseStddev horizon : Real))
  let distance : Nat → ENNReal := fun horizon => ENNReal.ofReal
    (Real.sqrt (Real.exp (constant / (horizon : Real)) - 1))
  have hProfiles := binaryAccountingProfile_eventually_actualMatched_close
    noiseStddev samplingRate hRate sensitivity epsilon distance hPositive hCentered
  refine ⟨constant, hConstant, hDistanceLimit, ?_, ?_⟩
  · exact tendsto_oracleStabilityError_zero epsilon distance hDistanceLimit
  · simpa [distance] using hProfiles

end

end Mf.DP
