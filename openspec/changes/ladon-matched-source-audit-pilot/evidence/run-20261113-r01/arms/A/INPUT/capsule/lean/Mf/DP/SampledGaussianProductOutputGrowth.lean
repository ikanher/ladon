import Mf.DP.OutputTestNoiseGrowth

/-!
# Product privacy implies released-sum noise growth

The complete sampled-Gaussian product output contains at least as much
accounting information as its coordinate sum.  This module connects a product
profile threshold to the existing direct Chebyshev output test and exposes the
result with standard deviation as the public noise parameter.
-/

open Filter MeasureTheory
open scoped BigOperators

namespace Mf.DP

noncomputable section

/-- Coordinate summation cannot increase the exact binary accounting profile. -/
theorem sampledGaussianOutputSum_profile_le_productProfile
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) (epsilon : Real) :
    binaryAccountingProfile
        (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
          sensitivity noiseVariance)
        (sampledGaussianOutputSumReferenceLaw horizon noiseVariance) epsilon ≤
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate
          sensitivity noiseVariance)
        (sampledGaussianReferenceProductLaw horizon noiseVariance) epsilon := by
  let sumFn : (Fin horizon → Real) → Real := fun sample => ∑ coordinate, sample coordinate
  change binaryAccountingProfile
      ((sampledGaussianSourceProductLaw horizon samplingRate hRate
        sensitivity noiseVariance).map (by fun_prop))
      ((sampledGaussianReferenceProductLaw horizon noiseVariance).map (by fun_prop)) epsilon ≤ _
  exact binaryAccountingProfile_map_le sumFn (by fun_prop)
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity noiseVariance)
    (sampledGaussianReferenceProductLaw horizon noiseVariance) epsilon

/-- A complete-product profile threshold supplies the ordered output-sum DP inequality. -/
theorem sampledGaussian_productProfileThreshold_implies_outputOrderedDP
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) (epsilon delta : Real)
    (hProfile : binaryAccountingProfile
      (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity noiseVariance)
      (sampledGaussianReferenceProductLaw horizon noiseVariance) epsilon ≤
        ENNReal.ofReal delta) :
    OrderedApproxDPLawPair
      (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate sensitivity noiseVariance)
      (sampledGaussianOutputSumReferenceLaw horizon noiseVariance) epsilon delta := by
  have hpairs := (binaryAccountingProfile_le_iff
    (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate sensitivity noiseVariance)
    (sampledGaussianOutputSumReferenceLaw horizon noiseVariance) epsilon delta).mp
      ((sampledGaussianOutputSum_profile_le_productProfile
        horizon samplingRate hRate sensitivity noiseVariance epsilon).trans hProfile)
  exact hpairs.1

/-- Product privacy forces eventual linear growth of per-step noise variance. -/
theorem sampledGaussian_noiseStddev_sq_eventually_linear_of_productProfile
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : Nat → NNReal) (epsilon delta : Real)
    (hRatePos : 0 < samplingRate) (hSensitivity : 0 < sensitivity)
    (hDelta : 0 ≤ delta) (hDeltaOne : delta < 1)
    (hPrivate : ∀ horizon : Nat, 0 < horizon →
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
          (noiseStddev horizon ^ 2))
        (sampledGaussianReferenceProductLaw horizon (noiseStddev horizon ^ 2)) epsilon ≤
          ENNReal.ofReal delta) :
    ∃ c : Real, 0 < c ∧ ∀ᶠ horizon : Nat in atTop,
      c * (horizon : Real) ≤ (noiseStddev horizon : Real) ^ 2 := by
  have hgrowth := sampledGaussian_noiseVariance_eventually_linear
    samplingRate hRate sensitivity (fun horizon => noiseStddev horizon ^ 2)
    epsilon delta hRatePos hSensitivity hDelta hDeltaOne
    (fun horizon hHorizon =>
      sampledGaussian_productProfileThreshold_implies_outputOrderedDP
        horizon samplingRate hRate sensitivity (noiseStddev horizon ^ 2)
        epsilon delta (hPrivate horizon hHorizon))
  obtain ⟨coefficient, hCoefficient, hgrowth⟩ := hgrowth
  refine ⟨coefficient, hCoefficient, ?_⟩
  filter_upwards [hgrowth] with horizon h
  simpa using h

end

end Mf.DP
