import Mf.DP.SampledGaussianOracleConvergence

/-!
# Calibrated standard deviation for sampled Gaussian products

Calibration is exposed in standard-deviation units.  The underlying law
constructors continue to receive variance, so the wrapper passes the square of
the public parameter.  The infimum is total and makes no finite-horizon
attainment or positivity claim.
-/

namespace Mf.DP

noncomputable section

/-- Exact sampled-Gaussian product profile parameterized by noise standard deviation. -/
def sampledGaussianProductProfileStddev
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (epsilon : Real) : ENNReal :=
  binaryAccountingProfile
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
      (noiseStddev ^ 2))
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2)) epsilon

/-- Corrected public domain for sampled-Gaussian calibration. -/
def SampledGaussianCalibrationAdmissible
    (samplingRate : NNReal) (sensitivity epsilon delta : Real) : Prop :=
  0 < samplingRate ∧ samplingRate ≤ 1 ∧ 0 < sensitivity ∧
    0 ≤ epsilon ∧ 0 < delta ∧ delta < 1

/-- Standard deviations whose exact product accounting profile meets the target slack. -/
def sampledGaussianFeasibleStddevSet
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) : Set NNReal :=
  {noiseStddev | sampledGaussianProductProfileStddev horizon samplingRate hRate
    sensitivity noiseStddev epsilon ≤ ENNReal.ofReal delta}

@[simp] theorem mem_sampledGaussianFeasibleStddevSet_iff
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) (noiseStddev : NNReal) :
    noiseStddev ∈ sampledGaussianFeasibleStddevSet horizon samplingRate hRate
        sensitivity epsilon delta ↔
      sampledGaussianProductProfileStddev horizon samplingRate hRate sensitivity
        noiseStddev epsilon ≤ ENNReal.ofReal delta :=
  Iff.rfl

/-- Nonnegative infimum of feasible sampled-Gaussian noise standard deviations. -/
def sampledGaussianCalibratedStddev
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon delta : Real) : NNReal :=
  sInf (sampledGaussianFeasibleStddevSet horizon samplingRate hRate
    sensitivity epsilon delta)

end

end Mf.DP
