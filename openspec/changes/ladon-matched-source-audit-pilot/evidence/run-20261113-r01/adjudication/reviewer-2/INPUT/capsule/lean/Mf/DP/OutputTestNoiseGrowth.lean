import Mf.DP.LawAccountingOracle
import Mf.DP.SampledGaussianOutputMoments
import Mathlib.Probability.Moments.Variance

/-!
# Direct Chebyshev noise growth

This module proves the finite-horizon lower bound on Gaussian noise variance
from exact output-law moments and one ordered approximate-DP inequality.  The
argument tests the released sum at half of its source-law mean and uses
Chebyshev under each neighboring law.
-/

open Filter MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

private lemma orderedApproxDPLawPair_measureReal_le
    {mu nu : ProbabilityMeasure Real} {epsilon delta : Real} (hdelta : 0 ≤ delta)
    (h : OrderedApproxDPLawPair mu nu epsilon delta)
    {s : Set Real} (hs : MeasurableSet s) :
    (mu : Measure Real).real s ≤
      Real.exp epsilon * (nu : Measure Real).real s + delta := by
  have hENNReal := h s hs
  have hleft : (mu : Measure Real) s ≠ ⊤ := measure_ne_top _ _
  have hmul : ENNReal.ofReal (Real.exp epsilon) * (nu : Measure Real) s ≠ ⊤ :=
    ENNReal.mul_ne_top ENNReal.ofReal_ne_top (measure_ne_top _ _)
  have hright : ENNReal.ofReal (Real.exp epsilon) * (nu : Measure Real) s +
      ENNReal.ofReal delta ≠ ⊤ :=
    ENNReal.add_ne_top.mpr ⟨hmul, ENNReal.ofReal_ne_top⟩
  have hreal := (ENNReal.toReal_le_toReal hleft hright).2 hENNReal
  change ((mu : Measure Real) s).toReal ≤ _
  rw [ENNReal.toReal_add hmul ENNReal.ofReal_ne_top, ENNReal.toReal_mul,
    ENNReal.toReal_ofReal (Real.exp_pos _).le,
    ENNReal.toReal_ofReal hdelta] at hreal
  exact hreal

private lemma chebyshev_measureReal_le
    {mu : Measure Real} [IsProbabilityMeasure mu] {X : Real → Real} {c : Real}
    (hX : MemLp X 2 mu) (hc : 0 < c) :
    mu.real {omega | c ≤ |X omega - ∫ x, X x ∂mu|} ≤
      variance X mu / c ^ 2 := by
  have hchebyshev := meas_ge_le_variance_div_sq hX hc
  let event : Set Real := {omega | c ≤ |X omega - ∫ x, X x ∂mu|}
  have hevent : event = {omega | c ≤ |X omega - ∫ x, X x ∂mu|} := rfl
  rw [← hevent] at hchebyshev
  have hreal : (mu event).toReal ≤
      (ENNReal.ofReal (variance X mu / c ^ 2)).toReal :=
    (ENNReal.toReal_le_toReal (measure_ne_top _ _) ENNReal.ofReal_ne_top).2 hchebyshev
  change (mu {omega | c ≤ |X omega - ∫ x, X x ∂mu|}).toReal ≤ _
  rw [← hevent]
  rw [ENNReal.toReal_ofReal] at hreal
  · exact hreal
  · exact div_nonneg (variance_nonneg X mu) (sq_nonneg c)

private theorem noiseVariance_lowerBound_algebra
    {q sensitivity horizon noiseVariance epsilon delta sourceVariance referenceVariance : Real}
    (hhorizon : 0 < horizon)
    (hsource : sourceVariance =
      horizon * (noiseVariance + q * (1 - q) * sensitivity ^ 2))
    (hreference : referenceVariance = horizon * noiseVariance)
    (hevent : (1 - delta) * (q * sensitivity * horizon / 2) ^ 2 ≤
      sourceVariance + Real.exp epsilon * referenceVariance) :
    noiseVariance ≥
      q ^ 2 * sensitivity ^ 2 * (1 - delta) * horizon /
          (4 * (1 + Real.exp epsilon)) -
        q * (1 - q) * sensitivity ^ 2 / (1 + Real.exp epsilon) := by
  have hexp : 0 < 1 + Real.exp epsilon := by positivity
  rw [hsource, hreference] at hevent
  have hbound :
      q ^ 2 * sensitivity ^ 2 * (1 - delta) * horizon / 4 ≤
        q * (1 - q) * sensitivity ^ 2 +
          (1 + Real.exp epsilon) * noiseVariance := by
    have hscaled :
        (q ^ 2 * sensitivity ^ 2 * (1 - delta) * horizon / 4) * horizon ≤
          (q * (1 - q) * sensitivity ^ 2 +
            (1 + Real.exp epsilon) * noiseVariance) * horizon := by
      nlinarith [hevent]
    exact le_of_mul_le_mul_right hscaled hhorizon
  rw [ge_iff_le]
  have hrearrange :
      q ^ 2 * sensitivity ^ 2 * (1 - delta) * horizon /
          (4 * (1 + Real.exp epsilon)) -
        q * (1 - q) * sensitivity ^ 2 / (1 + Real.exp epsilon) =
      (q ^ 2 * sensitivity ^ 2 * (1 - delta) * horizon / 4 -
        q * (1 - q) * sensitivity ^ 2) / (1 + Real.exp epsilon) := by
    field_simp
  rw [hrearrange]
  apply (div_le_iff₀ hexp).2
  nlinarith [hbound]

/--
Exact output moments and an ordered approximate-DP inequality force the
paper's finite-horizon lower bound on the per-step noise variance.
-/
theorem noiseVariance_lowerBound_of_orderedApproxDP_outputMoments
    (source reference : ProbabilityMeasure Real)
    (q sensitivity horizon noiseVariance epsilon delta : Real)
    (hq : 0 < q) (_hqOne : q ≤ 1) (hsensitivity : 0 < sensitivity)
    (hhorizon : 0 < horizon) (_hnoise : 0 ≤ noiseVariance)
    (hdelta : 0 ≤ delta) (_hdeltaOne : delta < 1)
    (hsourceMem : MemLp (fun x : Real => x) 2 (source : Measure Real))
    (hsourceMean : ∫ x, x ∂(source : Measure Real) = q * sensitivity * horizon)
    (hsourceVariance : variance (fun x : Real => x) (source : Measure Real) =
      horizon * (q * (1 - q) * sensitivity ^ 2 + noiseVariance))
    (hreferenceMem : MemLp (fun x : Real => x) 2 (reference : Measure Real))
    (hreferenceMean : ∫ x, x ∂(reference : Measure Real) = 0)
    (hreferenceVariance : variance (fun x : Real => x) (reference : Measure Real) =
      horizon * noiseVariance)
    (hprivate : OrderedApproxDPLawPair source reference epsilon delta) :
    noiseVariance ≥
      q ^ 2 * sensitivity ^ 2 * (1 - delta) * horizon /
          (4 * (1 + Real.exp epsilon)) -
        q * (1 - q) * sensitivity ^ 2 / (1 + Real.exp epsilon) := by
  let threshold : Real := q * sensitivity * horizon / 2
  have hthreshold : 0 < threshold := by
    dsimp [threshold]
    positivity
  let event : Set Real := Ioi threshold
  have heventMeas : MeasurableSet event := measurableSet_Ioi
  have hsourceIncl : eventᶜ ⊆
      {x : Real | threshold ≤ |x - ∫ y, y ∂(source : Measure Real)|} := by
    intro x hx
    have hxle : x ≤ threshold := le_of_not_gt (by simpa [event] using hx)
    rw [hsourceMean]
    dsimp [threshold] at hxle ⊢
    rw [abs_of_nonpos]
    · nlinarith [mul_pos (mul_pos hq hsensitivity) hhorizon]
    · nlinarith [mul_pos (mul_pos hq hsensitivity) hhorizon]
  have hreferenceIncl : event ⊆
      {x : Real | threshold ≤ |x - ∫ y, y ∂(reference : Measure Real)|} := by
    intro x hx
    have htx : threshold < x := by simpa [event] using hx
    rw [hreferenceMean]
    change threshold ≤ |x - 0|
    rw [sub_zero, abs_of_pos (lt_trans hthreshold htx)]
    exact htx.le
  have hsourceBad := chebyshev_measureReal_le hsourceMem hthreshold
  have hsourceComp : (source : Measure Real).real eventᶜ ≤
      variance (fun x : Real => x) (source : Measure Real) / threshold ^ 2 :=
    (measureReal_mono hsourceIncl).trans hsourceBad
  rw [probReal_compl_eq_one_sub heventMeas] at hsourceComp
  have hsourceLower :
      1 - variance (fun x : Real => x) (source : Measure Real) / threshold ^ 2 ≤
        (source : Measure Real).real event := by
    linarith
  have hreferenceBad := chebyshev_measureReal_le hreferenceMem hthreshold
  have hreferenceUpper : (reference : Measure Real).real event ≤
      variance (fun x : Real => x) (reference : Measure Real) / threshold ^ 2 :=
    (measureReal_mono hreferenceIncl).trans hreferenceBad
  have hdp := orderedApproxDPLawPair_measureReal_le hdelta hprivate heventMeas
  have hcombined :
      1 - variance (fun x : Real => x) (source : Measure Real) / threshold ^ 2 ≤
        Real.exp epsilon *
          (variance (fun x : Real => x) (reference : Measure Real) / threshold ^ 2) +
            delta :=
    hsourceLower.trans (hdp.trans (by
      simpa [add_comm] using (add_le_add_right
        (mul_le_mul_of_nonneg_left hreferenceUpper (Real.exp_pos epsilon).le) delta)))
  have hthresholdSq : 0 < threshold ^ 2 := sq_pos_of_pos hthreshold
  have hscaled := mul_le_mul_of_nonneg_right hcombined hthresholdSq.le
  have hmomentEvent :
      (1 - delta) * threshold ^ 2 ≤
        variance (fun x : Real => x) (source : Measure Real) +
          Real.exp epsilon *
            variance (fun x : Real => x) (reference : Measure Real) := by
    field_simp [hthresholdSq.ne'] at hscaled
    nlinarith [hscaled]
  have hsourceVariance' : variance (fun x : Real => x) (source : Measure Real) =
      horizon * (noiseVariance + q * (1 - q) * sensitivity ^ 2) := by
    rw [hsourceVariance]
    ring
  apply noiseVariance_lowerBound_algebra hhorizon hsourceVariance' hreferenceVariance
  simpa [threshold] using hmomentEvent

/--
The exact sampled-Gaussian source and reference laws satisfy the finite-horizon
noise-variance lower bound whenever their ordered approximate-DP inequality
holds.  Unlike the eventual theorem, this statement keeps the finite-horizon
correction term visible.
-/
theorem noiseVariance_lowerBound_of_sampledGaussianOutputLaws
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) (epsilon delta : Real)
    (hRatePos : 0 < samplingRate) (hSensitivity : 0 < sensitivity)
    (hHorizon : 0 < horizon) (hDelta : 0 ≤ delta) (hDeltaOne : delta < 1)
    (hPrivate : OrderedApproxDPLawPair
      (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
        sensitivity noiseVariance)
      (sampledGaussianOutputSumReferenceLaw horizon noiseVariance)
      epsilon delta) :
    (noiseVariance : Real) ≥
      (samplingRate : Real) ^ 2 * sensitivity ^ 2 * (1 - delta) *
          (horizon : Real) / (4 * (1 + Real.exp epsilon)) -
        (samplingRate : Real) * (1 - (samplingRate : Real)) * sensitivity ^ 2 /
          (1 + Real.exp epsilon) := by
  apply noiseVariance_lowerBound_of_orderedApproxDP_outputMoments
    (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
      sensitivity noiseVariance)
    (sampledGaussianOutputSumReferenceLaw horizon noiseVariance)
    (samplingRate : Real) sensitivity (horizon : Real) (noiseVariance : Real)
    epsilon delta
  · exact_mod_cast hRatePos
  · exact_mod_cast hRate
  · exact hSensitivity
  · exact_mod_cast hHorizon
  · exact NNReal.coe_nonneg noiseVariance
  · exact hDelta
  · exact hDeltaOne
  · exact sampledGaussianOutputSumSource_memLp horizon samplingRate hRate
      sensitivity noiseVariance
  · exact integral_id_sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
      sensitivity noiseVariance
  · exact variance_id_sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
      sensitivity noiseVariance
  · exact sampledGaussianOutputSumReference_memLp horizon noiseVariance
  · exact integral_id_sampledGaussianOutputSumReferenceLaw horizon noiseVariance
  · exact variance_id_sampledGaussianOutputSumReferenceLaw horizon noiseVariance
  · exact hPrivate

/--
Maintaining ordered approximate DP at every positive horizon forces an explicit
positive linear lower bound on the per-step Gaussian noise variance for all
sufficiently large horizons.
-/
theorem sampledGaussian_noiseVariance_eventually_linear
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : Nat → NNReal) (epsilon delta : Real)
    (hRatePos : 0 < samplingRate) (hSensitivity : 0 < sensitivity)
    (hDelta : 0 ≤ delta) (hDeltaOne : delta < 1)
    (hPrivate : ∀ horizon : Nat, 0 < horizon → OrderedApproxDPLawPair
      (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
        sensitivity (noiseVariance horizon))
      (sampledGaussianOutputSumReferenceLaw horizon (noiseVariance horizon))
      epsilon delta) :
    ∃ c : Real, 0 < c ∧
      ∀ᶠ horizon : Nat in atTop,
        c * (horizon : Real) ≤ (noiseVariance horizon : Real) := by
  let c : Real :=
    (samplingRate : Real) ^ 2 * sensitivity ^ 2 * (1 - delta) /
      (8 * (1 + Real.exp epsilon))
  let correction : Real :=
    (samplingRate : Real) * (1 - (samplingRate : Real)) * sensitivity ^ 2 /
      (1 + Real.exp epsilon)
  have hRateReal : 0 < (samplingRate : Real) := by exact_mod_cast hRatePos
  have hRateOneReal : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
  have hOneDelta : 0 < 1 - delta := sub_pos.mpr hDeltaOne
  have hc : 0 < c := by
    dsimp [c]
    positivity
  refine ⟨c, hc, ?_⟩
  obtain ⟨threshold, hThreshold⟩ :=
    exists_nat_ge (max (1 : Real) (correction / c))
  apply eventually_atTop.2
  refine ⟨threshold, fun horizon hHorizon ↦ ?_⟩
  have hThresholdOne : (1 : Real) ≤ (threshold : Real) :=
    (le_max_left _ _).trans hThreshold
  have hThresholdPos : 0 < threshold := by
    exact_mod_cast (lt_of_lt_of_le (zero_lt_one : (0 : Real) < 1) hThresholdOne)
  have hHorizonPos : 0 < horizon := lt_of_lt_of_le hThresholdPos hHorizon
  have hThresholdHorizon : (threshold : Real) ≤ (horizon : Real) := by
    exact_mod_cast hHorizon
  have hRatioHorizon : correction / c ≤ (horizon : Real) :=
    (le_max_right _ _).trans (hThreshold.trans hThresholdHorizon)
  have hCorrection : correction ≤ (horizon : Real) * c :=
    (div_le_iff₀ hc).mp hRatioHorizon
  have hFinite := noiseVariance_lowerBound_of_sampledGaussianOutputLaws
    horizon samplingRate hRate sensitivity (noiseVariance horizon) epsilon delta
    hRatePos hSensitivity hHorizonPos hDelta hDeltaOne (hPrivate horizon hHorizonPos)
  have hRewrite :
      (samplingRate : Real) ^ 2 * sensitivity ^ 2 * (1 - delta) *
          (horizon : Real) / (4 * (1 + Real.exp epsilon)) -
        (samplingRate : Real) * (1 - (samplingRate : Real)) * sensitivity ^ 2 /
          (1 + Real.exp epsilon) =
        2 * c * (horizon : Real) - correction := by
    dsimp [c, correction]
    have hden : 1 + Real.exp epsilon ≠ 0 := by positivity
    field_simp [hden]
    ring
  rw [hRewrite] at hFinite
  nlinarith

end

end Mf.DP
