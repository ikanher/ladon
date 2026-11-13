import Mf.DP.GaussianPrivacyLoss
import Mf.DP.SparseGaussianLikelihoodRatio
import Mf.DP.SparseGaussianProductLikelihoodRatio

/-!
# Maximum-coordinate events for normalized sampled-Gaussian products

This owner defines the finite threshold event used by the first
nonasymptotic profile bracket.  It proves only exact event measurability and
product probabilities; no optimality claim about the event is made here.
-/

open MeasureTheory ProbabilityTheory Set
open scoped BigOperators

namespace Mf.DP

noncomputable section

/-- At least one normalized product coordinate exceeds the supplied threshold. -/
def sparseGaussianProductMaximumEvent
    (horizon : Nat) (threshold : Real) : Set (Fin horizon → Real) :=
  {sample | ∃ coordinate, threshold < sample coordinate}

def sparseGaussianProductBelowBox
    (horizon : Nat) (threshold : Real) : Set (Fin horizon → Real) :=
  Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold)

/-- At least one product coordinate exceeds a threshold in the unnormalized
sampled-Gaussian coordinates. -/
def sampledGaussianProductMaximumEvent
    (horizon : Nat) (threshold : Real) : Set (Fin horizon → Real) :=
  {sample | ∃ coordinate, threshold < sample coordinate}

theorem measurableSet_sampledGaussianProductMaximumEvent
    (horizon : Nat) (threshold : Real) :
    MeasurableSet (sampledGaussianProductMaximumEvent horizon threshold) := by
  unfold sampledGaussianProductMaximumEvent
  rw [show {sample : Fin horizon → Real | ∃ coordinate, threshold < sample coordinate} =
      ⋃ coordinate : Fin horizon, (fun sample : Fin horizon → Real => sample coordinate) ⁻¹'
        Set.Ioi threshold by
    ext sample
    simp]
  exact MeasurableSet.iUnion fun coordinate =>
    measurableSet_Ioi.preimage (measurable_pi_apply coordinate)

theorem sampledGaussianProductMaximumEvent_preimage_positiveScale
    (horizon : Nat) (threshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    (positiveGaussianProductScaleEquiv horizon noiseStddev hStddev) ⁻¹'
        sparseGaussianProductMaximumEvent horizon threshold =
      sampledGaussianProductMaximumEvent horizon
        ((noiseStddev : Real) * threshold) := by
  ext sample
  simp only [Set.mem_preimage, sparseGaussianProductMaximumEvent,
    sampledGaussianProductMaximumEvent]
  have he : (positiveGaussianProductScaleEquiv horizon noiseStddev hStddev) sample =
      fun coordinate => sample coordinate / (noiseStddev : Real) := by
    ext coordinate
    change positiveGaussianScaleEquiv noiseStddev hStddev (sample coordinate) = _
    simp
  rw [he]
  change (∃ coordinate, threshold < sample coordinate / (noiseStddev : Real)) ↔ _
  constructor
  · rintro ⟨coordinate, hcoordinate⟩
    exact ⟨coordinate, by
      simpa [mul_comm] using
        (lt_div_iff₀ (by exact_mod_cast hStddev : (0 : Real) < noiseStddev)).mp hcoordinate⟩
  · rintro ⟨coordinate, hcoordinate⟩
    refine ⟨coordinate, (lt_div_iff₀
      (by exact_mod_cast hStddev : (0 : Real) < noiseStddev)).mpr ?_⟩
    simpa [mul_comm] using hcoordinate

private theorem sparseGaussianProductMaximumEvent_eq_compl_belowBox
    (horizon : Nat) (threshold : Real) :
    sparseGaussianProductMaximumEvent horizon threshold =
      (sparseGaussianProductBelowBox horizon threshold)ᶜ := by
  ext sample
  simp [sparseGaussianProductMaximumEvent, sparseGaussianProductBelowBox,
    Pi.le_def]

theorem measurableSet_sparseGaussianProductMaximumEvent
    (horizon : Nat) (threshold : Real) :
    MeasurableSet (sparseGaussianProductMaximumEvent horizon threshold) := by
  rw [sparseGaussianProductMaximumEvent_eq_compl_belowBox]
  exact (MeasurableSet.univ_pi (fun _ => measurableSet_Iic)).compl

theorem measurableSet_sparseGaussianProductBelowBox
    (horizon : Nat) (threshold : Real) :
    MeasurableSet (sparseGaussianProductBelowBox horizon threshold) :=
  MeasurableSet.univ_pi (fun _ => measurableSet_Iic)

private theorem standardGaussianProductLaw_belowBox
    (horizon : Nat) (threshold : Real) :
  (ProbabilityMeasure.pi (fun _ : Fin horizon => standardGaussianProbabilityMeasure))
        (sparseGaussianProductBelowBox horizon threshold) =
      ∏ _ : Fin horizon, standardGaussianProbabilityMeasure (Set.Iic threshold) := by
  change (ProbabilityMeasure.pi (fun _ : Fin horizon => standardGaussianProbabilityMeasure))
      (Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold)) = _
  rw [ProbabilityMeasure.pi_pi]

theorem standardGaussianProductLaw_maximumEvent_probability
    (horizon : Nat) (threshold : Real) :
    (ProbabilityMeasure.pi (fun _ : Fin horizon => standardGaussianProbabilityMeasure))
        (sparseGaussianProductMaximumEvent horizon threshold) =
      1 - (ENNReal.ofReal (stdNormalCDFReal threshold)) ^ horizon := by
  let below : Set (Fin horizon → Real) := sparseGaussianProductBelowBox horizon threshold
  have hbelow : MeasurableSet below := measurableSet_sparseGaussianProductBelowBox horizon threshold
  rw [sparseGaussianProductMaximumEvent_eq_compl_belowBox]
  simp only [ProbabilityMeasure.ennreal_coeFn_eq_coeFn_toMeasure]
  rw [MeasureTheory.measure_compl hbelow]
  dsimp [below]
  rw [Measure.pi_univ]
  simp only [measure_univ, Finset.prod_const_one]
  change 1 -
      (Measure.pi (fun _ : Fin horizon =>
        (standardGaussianProbabilityMeasure : Measure Real)))
        (Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold)) = _
  rw [Measure.pi_pi]
  have hprob2 :
      (∏ _ : Fin horizon,
        (standardGaussianProbabilityMeasure : Measure Real) (Set.Iic threshold)) =
        ENNReal.ofReal (stdNormalCDFReal threshold) ^ horizon := by
    have hstd :
        (standardGaussianProbabilityMeasure : Measure Real) (Set.Iic threshold) =
          ENNReal.ofReal (stdNormalCDFReal threshold) := by
      change gaussianReal 0 1 (Set.Iic threshold) = _
      rw [show gaussianReal 0 1 (Set.Iic threshold) =
        stdNormalMeasure (Set.Iic threshold) by
          simpa using gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift 0 threshold]
      rw [stdNormalCDFReal_eq_real_measure_Iic]
      exact (MeasureTheory.ofReal_measureReal (μ := stdNormalMeasure)
        (s := Set.Iic threshold) (by finiteness)).symm
    simpa [hstd]
  rw [hprob2]
  simp [stdNormalCDFReal_eq_real_measure_Iic]

private theorem sparseGaussianMixtureLaw_below_probability
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold : Real) :
    (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)
        (Set.Iic threshold) =
      (1 - (samplingRate : ENNReal)) * ENNReal.ofReal (stdNormalCDFReal threshold) +
        (samplingRate : ENNReal) *
          ENNReal.ofReal (stdNormalCDFReal (threshold - standardizedShift)) := by
  change (((1 - samplingRate : NNReal) : ENNReal) • gaussianReal 0 1 +
      (samplingRate : ENNReal) • gaussianReal standardizedShift 1) (Set.Iic threshold) = _
  rw [Measure.add_apply, Measure.smul_apply, Measure.smul_apply]
  have hzero := gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift
    0 threshold
  have hshift := gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift
    standardizedShift threshold
  have hzero' : gaussianReal 0 1 (Set.Iic threshold) =
      stdNormalMeasure (Set.Iic threshold) := by simpa using hzero
  have hshift' : gaussianReal standardizedShift 1 (Set.Iic threshold) =
      stdNormalMeasure (Set.Iic (threshold - standardizedShift)) := by
    simpa using hshift
  rw [hzero', hshift', stdNormalCDFReal_eq_real_measure_Iic]
  have hshiftMeasure :
      stdNormalMeasure (Set.Iic (threshold - standardizedShift)) =
        ENNReal.ofReal (stdNormalMeasure.real (Set.Iic (threshold - standardizedShift))) :=
      (MeasureTheory.ofReal_measureReal (μ := stdNormalMeasure)
      (s := Set.Iic (threshold - standardizedShift))).symm
  have hzeroMeasure :
      stdNormalMeasure (Set.Iic threshold) =
        ENNReal.ofReal (stdNormalMeasure.real (Set.Iic threshold)) :=
    (MeasureTheory.ofReal_measureReal (μ := stdNormalMeasure)
      (s := Set.Iic threshold)).symm
  rw [hzeroMeasure, hshiftMeasure]
  simp only [smul_eq_mul, ENNReal.coe_nnreal_eq, ENNReal.coe_sub]
  rw [stdNormalCDFReal_eq_real_measure_Iic (threshold - standardizedShift)]
  have hsub : (↑(1 - samplingRate) : Real) = 1 - (↑samplingRate : Real) := by
    rw [NNReal.coe_sub hRate]
    norm_num
  rw [hsub]
  have hcoeff : ENNReal.ofReal (1 - (↑samplingRate : Real)) =
      1 - ENNReal.ofReal (↑samplingRate : Real) := by
    rw [ENNReal.ofReal_sub (1 : Real) (NNReal.coe_nonneg samplingRate),
      ENNReal.ofReal_one]
  rw [hcoeff]

theorem sparseGaussianProductLaw_maximumEvent_probability
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift threshold : Real) :
    (sparseGaussianProductLaw horizon samplingRate hRate standardizedShift : Measure
        (Fin horizon → Real))
        (sparseGaussianProductMaximumEvent horizon threshold) =
      1 -
        ((1 - (samplingRate : ENNReal)) *
            ENNReal.ofReal (stdNormalCDFReal threshold) +
          (samplingRate : ENNReal) *
            ENNReal.ofReal (stdNormalCDFReal (threshold - standardizedShift))) ^ horizon := by
  let below : Set (Fin horizon → Real) := sparseGaussianProductBelowBox horizon threshold
  have hbelow : MeasurableSet below := measurableSet_sparseGaussianProductBelowBox horizon threshold
  rw [sparseGaussianProductMaximumEvent_eq_compl_belowBox]
  rw [MeasureTheory.measure_compl hbelow (by finiteness)]
  simp only [sparseGaussianProductLaw]
  dsimp [below]
  rw [Measure.pi_univ]
  simp only [measure_univ, Finset.prod_const_one]
  change 1 -
      (Measure.pi (fun _ : Fin horizon =>
        (sparseGaussianMixtureLaw samplingRate hRate standardizedShift : Measure Real)))
        (Set.pi Set.univ (fun _ : Fin horizon => Set.Iic threshold)) = _
  rw [Measure.pi_pi]
  simp_rw [sparseGaussianMixtureLaw_below_probability samplingRate hRate
    standardizedShift threshold]
  simp [Finset.prod_const]

/-- Exact source maximum-event probability in public standard-deviation
coordinates. The raw threshold is `noiseStddev * normalizedThreshold`. -/
theorem sampledGaussianProductMaximumEvent_source_probability
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity normalizedThreshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity
        (noiseStddev ^ 2) : Measure (Fin horizon → Real))
        (sampledGaussianProductMaximumEvent horizon
          ((noiseStddev : Real) * normalizedThreshold)) =
      1 -
        ((1 - (samplingRate : ENNReal)) *
            ENNReal.ofReal (stdNormalCDFReal normalizedThreshold) +
          (samplingRate : ENNReal) *
            ENNReal.ofReal (stdNormalCDFReal
              (normalizedThreshold - sensitivity / (noiseStddev : Real)))) ^ horizon := by
  let scaleEquiv := positiveGaussianProductScaleEquiv horizon noiseStddev hStddev
  have hmap := sampledGaussianSourceProductLaw_map_positiveGaussianScale
    horizon samplingRate hRate sensitivity noiseStddev hStddev
  have hnormalized := sparseGaussianProductLaw_maximumEvent_probability horizon samplingRate
    hRate (sensitivity / (noiseStddev : Real)) normalizedThreshold
  rw [← hmap] at hnormalized
  rw [Measure.map_apply scaleEquiv.measurable
    (measurableSet_sparseGaussianProductMaximumEvent horizon normalizedThreshold)] at hnormalized
  rw [sampledGaussianProductMaximumEvent_preimage_positiveScale] at hnormalized
  exact hnormalized

/-- Exact reference maximum-event probability in public standard-deviation
coordinates. -/
theorem sampledGaussianProductMaximumEvent_reference_probability
    (horizon : Nat) (normalizedThreshold : Real) (noiseStddev : NNReal)
    (hStddev : 0 < noiseStddev) :
    (sampledGaussianReferenceProductLaw horizon (noiseStddev ^ 2) :
        Measure (Fin horizon → Real))
        (sampledGaussianProductMaximumEvent horizon
          ((noiseStddev : Real) * normalizedThreshold)) =
      1 - (ENNReal.ofReal (stdNormalCDFReal normalizedThreshold)) ^ horizon := by
  let scaleEquiv := positiveGaussianProductScaleEquiv horizon noiseStddev hStddev
  have hmap := sampledGaussianReferenceProductLaw_map_positiveGaussianScale
    horizon noiseStddev hStddev
  have hnormalized := standardGaussianProductLaw_maximumEvent_probability horizon
    normalizedThreshold
  have hnormalized' :
      (Measure.pi (fun _ : Fin horizon => gaussianReal 0 1))
          (sparseGaussianProductMaximumEvent horizon normalizedThreshold) =
        1 - (ENNReal.ofReal (stdNormalCDFReal normalizedThreshold)) ^ horizon := by
    rw [ProbabilityMeasure.ennreal_coeFn_eq_coeFn_toMeasure,
      ProbabilityMeasure.toMeasure_pi] at hnormalized
    simpa [standardGaussianProbabilityMeasure] using hnormalized
  rw [← hmap] at hnormalized'
  rw [Measure.map_apply scaleEquiv.measurable
    (measurableSet_sparseGaussianProductMaximumEvent horizon normalizedThreshold)] at hnormalized'
  dsimp [scaleEquiv] at hnormalized'
  rw [sampledGaussianProductMaximumEvent_preimage_positiveScale] at hnormalized'
  exact hnormalized'

end

end Mf.DP
