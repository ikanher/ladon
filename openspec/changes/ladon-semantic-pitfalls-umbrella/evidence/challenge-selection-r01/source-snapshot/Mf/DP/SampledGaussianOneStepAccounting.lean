import Mf.DP.FullBatchGaussianAccounting
import Mf.DP.TwoPointMixtureAccounting
import Mf.DP.MatchedGaussianSourceNormalization
import Mf.DP.SampledGaussianOneStepEffectiveNoise

/-!
# Exact one-step sampled Gaussian accounting

This module identifies the scalar one-step profile with the law-level,
two-sided accounting oracle.  The forward mixture profile is reduced to an
ordinary shifted-Gaussian profile.  The reverse profile is then shown to be no
larger by splitting on the residual reference coefficient.
-/

open MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

/-- The scalar `Psi` formula is the sampling rate times an ordinary Gaussian profile. -/
theorem oneStepSampledGaussianPsi_eq_rate_mul_scalarGaussianSigmaProfile
    (epsilon q sensitivity noiseStddev : Real)
    (hepsilon : 0 ≤ epsilon) (hq : 0 < q)
    (hsensitivity : 0 < sensitivity) (hnoise : 0 < noiseStddev) :
    oneStepSampledGaussianPsi epsilon q (noiseStddev / sensitivity) =
      q * Training.scalarGaussianSigmaProfile sensitivity
        (oneStepSampledGaussianLogRatio epsilon q) noiseStddev := by
  unfold oneStepSampledGaussianPsi Training.scalarGaussianSigmaProfile
  rw [gdpProfile_eq]
  unfold oneStepSampledGaussianPsiArgPlus oneStepSampledGaussianPsiArgMinus
  unfold gdpProfileCDFPlusArg gdpProfileCDFMinusArg
  have hs_ne : sensitivity ≠ 0 := hsensitivity.ne'
  have hn_ne : noiseStddev ≠ 0 := hnoise.ne'
  have hexpLog : Real.exp (oneStepSampledGaussianLogRatio epsilon q) =
      oneStepSampledGaussianH epsilon q / q := by
    apply Real.exp_log
    apply div_pos
    · unfold oneStepSampledGaussianH
      have := Real.one_le_exp hepsilon
      linarith
    · exact hq
  rw [hexpLog]
  have hplus :
      -(noiseStddev / sensitivity) * oneStepSampledGaussianLogRatio epsilon q +
          1 / (2 * (noiseStddev / sensitivity)) =
        sensitivity / noiseStddev / 2 -
          oneStepSampledGaussianLogRatio epsilon q / (sensitivity / noiseStddev) := by
    field_simp [hs_ne, hn_ne]
    ring
  have hminus :
      -(noiseStddev / sensitivity) * oneStepSampledGaussianLogRatio epsilon q -
          1 / (2 * (noiseStddev / sensitivity)) =
        -(sensitivity / noiseStddev) / 2 -
          oneStepSampledGaussianLogRatio epsilon q / (sensitivity / noiseStddev) := by
    field_simp [hs_ne, hn_ne]
    ring
  rw [hplus, hminus]
  field_simp [hq.ne']

/-- The ordered forward sampled-Gaussian profile is exactly the scalar `Psi` profile. -/
theorem sampledGaussianOneStep_eventHockeyStickProfile_eq_psi
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (epsilon : Real)
    (hepsilon : 0 ≤ epsilon) (hRatePos : 0 < samplingRate)
    (hSensitivity : 0 < sensitivity) (hNoise : 0 < noiseStddev) :
    eventHockeyStickProfile
        (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
          (noiseStddev ^ 2) : Measure Real)
        (sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2) : Measure Real)
        epsilon =
      ENNReal.ofReal (oneStepSampledGaussianPsi epsilon samplingRate
        ((noiseStddev : Real) / sensitivity)) := by
  let source : ProbabilityMeasure Real :=
    ⟨gaussianReal sensitivity (noiseStddev ^ 2), by infer_instance⟩
  let reference : ProbabilityMeasure Real :=
    sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2)
  rw [sampledGaussianOneStepSourceLaw_eq_gaussianMixture]
  change eventHockeyStickProfile
      ((1 - samplingRate : NNReal) • (reference : Measure Real) +
        samplingRate • (source : Measure Real))
      (reference : Measure Real) epsilon = _
  rw [eventHockeyStickProfile_twoPointMixture_forward
    source reference samplingRate hRatePos hRate epsilon hepsilon]
  change (samplingRate : ENNReal) * eventHockeyStickProfile
      (source : Measure Real) (reference : Measure Real)
      (oneStepSampledGaussianLogRatio epsilon samplingRate) = _
  have hgaussian := gaussianShiftEventHockeyStickProfile_eq_scalar
    sensitivity noiseStddev (oneStepSampledGaussianLogRatio epsilon samplingRate)
      hSensitivity (by exact_mod_cast hNoise)
  change eventHockeyStickProfile
      (source : Measure Real) (reference : Measure Real)
      (oneStepSampledGaussianLogRatio epsilon samplingRate) =
    ENNReal.ofReal (Training.scalarGaussianSigmaProfile sensitivity
      (oneStepSampledGaussianLogRatio epsilon samplingRate) noiseStddev) at hgaussian
  rw [hgaussian, ENNReal.coe_nnreal_eq]
  rw [← ENNReal.ofReal_mul (show 0 ≤ (samplingRate : Real) by positivity)]
  exact congrArg ENNReal.ofReal
    (oneStepSampledGaussianPsi_eq_rate_mul_scalarGaussianSigmaProfile
      epsilon samplingRate sensitivity noiseStddev hepsilon
      (by exact_mod_cast hRatePos) hSensitivity (by exact_mod_cast hNoise)).symm

/-- The reverse ordered profile of the two-point Gaussian mixture is at most its forward profile. -/
theorem twoPointGaussian_reverseProfile_le_forwardProfile
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) (epsilon : Real)
    (hepsilon : 0 ≤ epsilon) (hRatePos : 0 < samplingRate) :
    eventHockeyStickProfile
        (gaussianReal 0 noiseVariance)
        ((1 - samplingRate : NNReal) • gaussianReal 0 noiseVariance +
          samplingRate • gaussianReal sensitivity noiseVariance) epsilon ≤
      eventHockeyStickProfile
        ((1 - samplingRate : NNReal) • gaussianReal 0 noiseVariance +
          samplingRate • gaussianReal sensitivity noiseVariance)
        (gaussianReal 0 noiseVariance) epsilon := by
  let source : ProbabilityMeasure Real :=
    ⟨gaussianReal sensitivity noiseVariance, by infer_instance⟩
  let reference : ProbabilityMeasure Real :=
    ⟨gaussianReal 0 noiseVariance, by infer_instance⟩
  let c : Real := 1 - Real.exp epsilon * (1 - (samplingRate : Real))
  by_cases hc : c ≤ 0
  · have hzero :=
      eventHockeyStickProfile_twoPointMixture_reverse_eq_zero_of_nonpos
        source reference samplingRate hRate epsilon hc
    change eventHockeyStickProfile
        (gaussianReal 0 noiseVariance)
        ((1 - samplingRate : NNReal) • gaussianReal 0 noiseVariance +
          samplingRate • gaussianReal sensitivity noiseVariance) epsilon = 0 at hzero
    rw [hzero]
    exact bot_le
  · have hcpos : 0 < c := lt_of_not_ge hc
    have hreverse := eventHockeyStickProfile_twoPointMixture_reverse_of_pos
      source reference samplingRate hRatePos hRate epsilon hcpos
    have hforward := eventHockeyStickProfile_twoPointMixture_forward
      source reference samplingRate hRatePos hRate epsilon hepsilon
    change eventHockeyStickProfile
        (gaussianReal 0 noiseVariance)
        ((1 - samplingRate : NNReal) • gaussianReal 0 noiseVariance +
          samplingRate • gaussianReal sensitivity noiseVariance) epsilon =
      ENNReal.ofReal c * eventHockeyStickProfile
        (gaussianReal 0 noiseVariance) (gaussianReal sensitivity noiseVariance)
        (Real.log (Real.exp epsilon * (samplingRate : Real) / c)) at hreverse
    change eventHockeyStickProfile
        ((1 - samplingRate : NNReal) • gaussianReal 0 noiseVariance +
          samplingRate • gaussianReal sensitivity noiseVariance)
        (gaussianReal 0 noiseVariance) epsilon =
      (samplingRate : ENNReal) * eventHockeyStickProfile
        (gaussianReal sensitivity noiseVariance) (gaussianReal 0 noiseVariance)
        (Real.log ((Real.exp epsilon - 1 + (samplingRate : Real)) /
          (samplingRate : Real))) at hforward
    rw [hreverse, hforward]
    rw [gaussianShiftEventHockeyStickProfiles_eq]
    have hqR : 0 < (samplingRate : Real) := by exact_mod_cast hRatePos
    have hqOne : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
    have hexpOne : 1 ≤ Real.exp epsilon := Real.one_le_exp hepsilon
    have hcLeQ : c ≤ (samplingRate : Real) := by
      dsimp [c]
      nlinarith [mul_nonneg (sub_nonneg.mpr hexpOne) (sub_nonneg.mpr hqOne)]
    have hcENN : ENNReal.ofReal c ≤ (samplingRate : ENNReal) := by
      rw [ENNReal.coe_nnreal_eq]
      exact ENNReal.ofReal_le_ofReal hcLeQ
    have hnumPos : 0 < Real.exp epsilon - 1 + (samplingRate : Real) := by
      linarith
    have hcross :
        c * (Real.exp epsilon - 1 + (samplingRate : Real)) ≤
          Real.exp epsilon * (samplingRate : Real) * (samplingRate : Real) := by
      have hid :
          Real.exp epsilon * (samplingRate : Real) ^ 2 -
              c * (Real.exp epsilon - 1 + (samplingRate : Real)) =
            (Real.exp epsilon - 1) ^ 2 * (1 - (samplingRate : Real)) := by
        dsimp [c]
        ring
      have hnonneg :
          0 ≤ (Real.exp epsilon - 1) ^ 2 * (1 - (samplingRate : Real)) := by
        positivity
      nlinarith
    have hratio :
        (Real.exp epsilon - 1 + (samplingRate : Real)) /
            (samplingRate : Real) ≤
          Real.exp epsilon * (samplingRate : Real) / c := by
      rw [div_le_div_iff₀ hqR hcpos]
      nlinarith
    have hlog :
        Real.log ((Real.exp epsilon - 1 + (samplingRate : Real)) /
            (samplingRate : Real)) ≤
          Real.log (Real.exp epsilon * (samplingRate : Real) / c) := by
      exact Real.log_le_log (div_pos hnumPos hqR) hratio
    exact mul_le_mul hcENN
      (eventHockeyStickProfile_antitone_epsilon
        (gaussianReal 0 noiseVariance)
        (gaussianReal sensitivity noiseVariance) hlog) bot_le bot_le

/-- The exact two-sided one-step sampled-Gaussian accountant is the scalar `Psi` profile. -/
theorem sampledGaussianOneStep_binaryAccountingProfile_eq_psi
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (epsilon : Real)
    (hepsilon : 0 ≤ epsilon) (hRatePos : 0 < samplingRate)
    (hSensitivity : 0 < sensitivity) (hNoise : 0 < noiseStddev) :
    binaryAccountingProfile
        (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
          (noiseStddev ^ 2))
        (sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2)) epsilon =
      ENNReal.ofReal (oneStepSampledGaussianPsi epsilon samplingRate
        ((noiseStddev : Real) / sensitivity)) := by
  have hforward := sampledGaussianOneStep_eventHockeyStickProfile_eq_psi
    samplingRate hRate sensitivity noiseStddev epsilon hepsilon hRatePos
    hSensitivity hNoise
  have hreverse := twoPointGaussian_reverseProfile_le_forwardProfile
    samplingRate hRate sensitivity (noiseStddev ^ 2) epsilon hepsilon hRatePos
  have hreverseActual :
      eventHockeyStickProfile
          (sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2) : Measure Real)
          (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
            (noiseStddev ^ 2) : Measure Real) epsilon ≤
        eventHockeyStickProfile
          (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
            (noiseStddev ^ 2) : Measure Real)
          (sampledGaussianOneStepReferenceLaw (noiseStddev ^ 2) : Measure Real)
          epsilon := by
    rw [sampledGaussianOneStepSourceLaw_eq_gaussianMixture]
    exact hreverse
  unfold binaryAccountingProfile
  rw [max_eq_left hreverseActual]
  exact hforward

end

end Mf.DP
