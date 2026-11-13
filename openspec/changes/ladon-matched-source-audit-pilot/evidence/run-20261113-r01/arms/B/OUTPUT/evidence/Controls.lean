import Mf.DP.Training.KOutOfT.TrainingMechanism
import Mf.DP.SampledGaussianFiniteBracketCalibration

open Mf.DP Mf.DP.Training.KOutOfT

example : fixedCardinalityScheduleMass 2 1 ({0} : Finset (Fin 2)) = (1 / 2 : ℝ) := by
  norm_num [fixedCardinalityScheduleMass, bisFixedCardUniformMass]
example : fixedCardinalityScheduleMass 2 1 (∅ : Finset (Fin 2)) = 0 := by
  norm_num [fixedCardinalityScheduleMass, bisFixedCardUniformMass]
example : fixedCardinalityScheduleMass 2 1 (Finset.univ : Finset (Fin 2)) = 0 := by
  norm_num [fixedCardinalityScheduleMass, bisFixedCardUniformMass]

-- The original upper endpoint accepts the zero-dimensional horizon and negative parameters.
example (q : NNReal) (hq : q ≤ 1) (a b : ℝ) (s : NNReal) (hs : 0 < s) :
  binaryAccountingProfile
    (sampledGaussianSourceProductLaw 0 q hq (-1) (s ^ 2))
    (sampledGaussianReferenceProductLaw 0 (s ^ 2)) (-1) ≤
  sampledGaussianProductFiniteProfileUpperBoundWithThresholds 0 q (-1) (-1) a b s := by
  exact sampledGaussianProductBinaryProfile_le_finiteProfileUpperBoundWithThresholds
    0 q hq (-1) (-1) a b s hs

#print Mf.DP.sampledGaussian_calibration_interval_of_finiteBracketWithThresholds_certificates
#print Mf.DP.Training.KOutOfT.kOutOfTTrainingTranscript
