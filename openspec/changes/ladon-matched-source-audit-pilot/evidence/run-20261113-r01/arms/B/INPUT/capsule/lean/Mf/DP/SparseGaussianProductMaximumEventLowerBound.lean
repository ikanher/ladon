import Mf.DP.FiniteProfileEventLowerBound
import Mf.DP.SampledGaussianProductMaximumEvent

/-!
# Maximum-event lower witnesses for sparse Gaussian products

The maximum-coordinate event is a certified lower witness for the forward
hockey-stick profile.  This owner deliberately does not optimize the
threshold and does not claim that the event is profile-optimal.
-/

open MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- The real-valued maximum-event witness used by numerical certificates. -/
def sparseGaussianProductMaximumEventForwardLowerBoundReal
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) : Real :=
  let p : Real :=
    (1 - (samplingRate : Real)) * stdNormalCDFReal threshold +
      (samplingRate : Real) *
        stdNormalCDFReal (threshold - standardizedShift)
  1 - p ^ horizon - Real.exp epsilon *
    (1 - (stdNormalCDFReal threshold) ^ horizon)

def sparseGaussianProductMaximumEventForwardLowerBound
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) : ENNReal :=
  1 -
      ((1 - (samplingRate : ENNReal)) *
          ENNReal.ofReal (stdNormalCDFReal threshold) +
        (samplingRate : ENNReal) *
          ENNReal.ofReal (stdNormalCDFReal (threshold - standardizedShift))) ^ horizon -
    ENNReal.ofReal (Real.exp epsilon) *
      (1 - (ENNReal.ofReal (stdNormalCDFReal threshold)) ^ horizon)

/-- The nonnegative witness is exactly the positive part of its real formula. -/
theorem ennreal_ofReal_sparseGaussianProductMaximumEventForwardLowerBoundReal
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) :
    ENNReal.ofReal
        (sparseGaussianProductMaximumEventForwardLowerBoundReal
          horizon samplingRate hRate standardizedShift epsilon threshold) =
      sparseGaussianProductMaximumEventForwardLowerBound
        horizon samplingRate hRate standardizedShift epsilon threshold := by
  let c : Real := stdNormalCDFReal threshold
  let d : Real := stdNormalCDFReal (threshold - standardizedShift)
  let q : Real := (samplingRate : Real)
  let p : Real := (1 - q) * c + q * d
  have hq0 : 0 ≤ q := by
    dsimp [q]
    positivity
  have hq1 : q ≤ 1 := by
    dsimp [q]
    exact_mod_cast hRate
  have hc0 : 0 ≤ c := stdNormalCDFReal_nonneg _
  have hc1 : c ≤ 1 := stdNormalCDFReal_le_one _
  have hd0 : 0 ≤ d := stdNormalCDFReal_nonneg _
  have hp0 : 0 ≤ p := by
    dsimp [p]
    positivity
  have hpow0 : 0 ≤ p ^ horizon := pow_nonneg hp0 _
  have hcPow0 : 0 ≤ c ^ horizon := pow_nonneg hc0 _
  have hqENN : ENNReal.ofReal q = (samplingRate : ENNReal) := by
    simp [q]
  have hOneMinusQ : ENNReal.ofReal (1 - q) = 1 - (samplingRate : ENNReal) := by
    rw [ENNReal.ofReal_sub 1 hq0, ENNReal.ofReal_one, hqENN]
  have hpENN : ENNReal.ofReal p =
      (1 - (samplingRate : ENNReal)) * ENNReal.ofReal c +
        (samplingRate : ENNReal) * ENNReal.ofReal d := by
    dsimp [p]
    rw [ENNReal.ofReal_add]
    · rw [ENNReal.ofReal_mul (sub_nonneg.mpr hq1), hOneMinusQ]
      rw [ENNReal.ofReal_mul hq0, hqENN]
    · positivity
    · positivity
  have hpowENN : ENNReal.ofReal (p ^ horizon) =
      ((1 - (samplingRate : ENNReal)) * ENNReal.ofReal c +
        (samplingRate : ENNReal) * ENNReal.ofReal d) ^ horizon := by
    rw [ENNReal.ofReal_pow hp0, hpENN]
  have hCDFPow : ENNReal.ofReal (c ^ horizon) =
      (ENNReal.ofReal c) ^ horizon := ENNReal.ofReal_pow hc0 _
  have hInner : ENNReal.ofReal (1 - c ^ horizon) =
      1 - (ENNReal.ofReal c) ^ horizon := by
    rw [ENNReal.ofReal_sub 1 hcPow0, ENNReal.ofReal_one, hCDFPow]
  have hExp : 0 ≤ Real.exp epsilon := (Real.exp_pos _).le
  have hTail0 : 0 ≤ 1 - c ^ horizon := by
    have hcPow1 : c ^ horizon ≤ 1 := pow_le_one₀ hc0 hc1
    linarith
  have hExpTail : ENNReal.ofReal (Real.exp epsilon * (1 - c ^ horizon)) =
      ENNReal.ofReal (Real.exp epsilon) *
        (1 - (ENNReal.ofReal c) ^ horizon) := by
    rw [ENNReal.ofReal_mul hExp, hInner]
  have hFinal0 : 0 ≤ Real.exp epsilon * (1 - c ^ horizon) :=
    mul_nonneg hExp hTail0
  dsimp [sparseGaussianProductMaximumEventForwardLowerBoundReal]
  unfold sparseGaussianProductMaximumEventForwardLowerBound
  change ENNReal.ofReal ((1 - p ^ horizon) -
      Real.exp epsilon * (1 - c ^ horizon)) =
    1 -
        ((1 - (samplingRate : ENNReal)) * ENNReal.ofReal c +
            (samplingRate : ENNReal) * ENNReal.ofReal d) ^ horizon -
      ENNReal.ofReal (Real.exp epsilon) *
        (1 - (ENNReal.ofReal c) ^ horizon)
  rw [ENNReal.ofReal_sub (1 - p ^ horizon) hFinal0,
    ENNReal.ofReal_sub 1 hpow0, ENNReal.ofReal_one, hpowENN, hExpTail]

theorem sparseGaussianProductMaximumEventForwardLowerBound_le_profile
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon threshold : Real) :
    sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        standardizedShift epsilon threshold ≤
      eventHockeyStickProfile
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real))
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real)) epsilon := by
  unfold sparseGaussianProductMaximumEventForwardLowerBound
  have hWitness := eventHockeyStickProfile_ge_measurableEvent
    (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
      Measure (Fin horizon → Real))
    (standardGaussianProductLaw horizon : Measure (Fin horizon → Real)) epsilon
    (sparseGaussianProductMaximumEvent horizon threshold)
    (measurableSet_sparseGaussianProductMaximumEvent horizon threshold)
  rw [sparseGaussianProductLaw_maximumEvent_probability] at hWitness
  have hstdEvent :
      (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
          (sparseGaussianProductMaximumEvent horizon threshold) =
        1 - (ENNReal.ofReal (stdNormalCDFReal threshold)) ^ horizon := by
    simpa [standardGaussianProductLaw,
      ProbabilityMeasure.ennreal_coeFn_eq_coeFn_toMeasure] using
      standardGaussianProductLaw_maximumEvent_probability horizon threshold
  rw [hstdEvent] at hWitness
  exact hWitness

theorem iSup_sparseGaussianProductMaximumEventForwardLowerBound_le_profile
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift epsilon : Real) :
    (⨆ threshold : Real,
      sparseGaussianProductMaximumEventForwardLowerBound horizon samplingRate hRate
        standardizedShift epsilon threshold) ≤
      eventHockeyStickProfile
        (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift :
          Measure (Fin horizon → Real))
        (standardGaussianProductLaw horizon : Measure (Fin horizon → Real)) epsilon := by
  refine iSup_le ?_
  intro threshold
  exact sparseGaussianProductMaximumEventForwardLowerBound_le_profile
    horizon samplingRate hRate standardizedShift epsilon threshold

end

end Mf.DP
