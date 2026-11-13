import Mf.DP.GaussianNoiseMonotonicity
import Mathlib.Probability.ProbabilityMassFunction.Constructions
import Mathlib.Probability.ProductMeasure

/-!
# Exact sampled-Gaussian output laws

This module defines the one-step neighboring laws, their finite products, the
released coordinate sum, and its strict half-source-mean threshold event.  It
is a law-construction layer only; moment identities are proved separately.
-/

open MeasureTheory Set
open scoped BigOperators

namespace Mf.DP

noncomputable section

/-- A Bernoulli shift that is zero off-sample and `sensitivity` on-sample. -/
def bernoulliShiftLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) : ProbabilityMeasure Real :=
  ⟨(PMF.map (fun selected : Bool => if selected then sensitivity else 0)
      (PMF.bernoulli samplingRate hRate)).toMeasure, by infer_instance⟩

/-- One sampled neighboring step: a Bernoulli shift plus centered Gaussian noise. -/
def sampledGaussianOneStepSourceLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) : ProbabilityMeasure Real :=
  gaussianNoiseLaw
    (bernoulliShiftLaw samplingRate hRate sensitivity) noiseVariance

/-- One reference step: centered Gaussian noise with the same variance. -/
def sampledGaussianOneStepReferenceLaw
    (noiseVariance : NNReal) : ProbabilityMeasure Real :=
  ⟨ProbabilityTheory.gaussianReal 0 noiseVariance, by infer_instance⟩

/-- Independent finite product of the sampled neighboring one-step law. -/
def sampledGaussianSourceProductLaw
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    ProbabilityMeasure (Fin horizon → Real) :=
  ProbabilityMeasure.pi (fun _ =>
    sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity noiseVariance)

/-- Independent finite product of the reference one-step law. -/
def sampledGaussianReferenceProductLaw
    (horizon : Nat) (noiseVariance : NNReal) :
    ProbabilityMeasure (Fin horizon → Real) :=
  ProbabilityMeasure.pi (fun _ =>
    sampledGaussianOneStepReferenceLaw noiseVariance)

/-- Push a finite-vector law forward by coordinate summation. -/
def finiteSumOutputLaw
    (horizon : Nat) (mu : ProbabilityMeasure (Fin horizon → Real)) :
    ProbabilityMeasure Real :=
  let sumFn : (Fin horizon → Real) → Real := fun x => ∑ i, x i
  mu.map (by
    change AEMeasurable sumFn (mu : Measure (Fin horizon → Real))
    have hsum : Measurable sumFn := by fun_prop
    exact hsum.aemeasurable)

/-- Law of the released sum under the sampled neighboring product law. -/
def sampledGaussianOutputSumSourceLaw
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) : ProbabilityMeasure Real :=
  finiteSumOutputLaw horizon
    (sampledGaussianSourceProductLaw horizon samplingRate hRate
      sensitivity noiseVariance)

/-- Law of the released sum under the reference product law. -/
def sampledGaussianOutputSumReferenceLaw
    (horizon : Nat) (noiseVariance : NNReal) : ProbabilityMeasure Real :=
  finiteSumOutputLaw horizon
    (sampledGaussianReferenceProductLaw horizon noiseVariance)

/-- Half of the source-law output mean used by the direct distinguishing test. -/
def halfSourceMeanThreshold
    (horizon : Nat) (samplingRate : NNReal) (sensitivity : Real) : Real :=
  (samplingRate : Real) * sensitivity * (horizon : Real) / 2

/-- The released sum is strictly greater than half of its source-law mean. -/
def sampledGaussianOutputThresholdEvent
    (horizon : Nat) (samplingRate : NNReal) (sensitivity : Real) : Set Real :=
  Ioi (halfSourceMeanThreshold horizon samplingRate sensitivity)

theorem measurableSet_sampledGaussianOutputThresholdEvent
    (horizon : Nat) (samplingRate : NNReal) (sensitivity : Real) :
    MeasurableSet
      (sampledGaussianOutputThresholdEvent horizon samplingRate sensitivity) :=
  measurableSet_Ioi

/-! ## Degenerate parameter boundaries -/

/-- Zero sensitivity erases the Bernoulli shift, so the neighboring one-step laws coincide. -/
theorem sampledGaussianOneStepSourceLaw_zeroSensitivity
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (noiseVariance : NNReal) :
    sampledGaussianOneStepSourceLaw samplingRate hRate 0 noiseVariance =
      sampledGaussianOneStepReferenceLaw noiseVariance := by
  have hmap : PMF.map (fun _ : Bool => (0 : Real))
      (PMF.bernoulli samplingRate hRate) = PMF.pure 0 := by
    convert PMF.map_const (p := PMF.bernoulli samplingRate hRate)
      (b := (0 : Real)) using 1
    congr 1
  apply Subtype.ext
  simp [sampledGaussianOneStepSourceLaw, sampledGaussianOneStepReferenceLaw,
    bernoulliShiftLaw, gaussianNoiseLaw, hmap, PMF.toMeasure_pure]

/-- Zero sampling rate erases the Bernoulli shift, so the neighboring one-step laws coincide. -/
theorem sampledGaussianOneStepSourceLaw_zeroSamplingRate
    (hRate : (0 : NNReal) ≤ 1) (sensitivity : Real)
    (noiseVariance : NNReal) :
    sampledGaussianOneStepSourceLaw 0 hRate sensitivity noiseVariance =
      sampledGaussianOneStepReferenceLaw noiseVariance := by
  have hBernoulli : PMF.bernoulli (0 : NNReal) hRate = PMF.pure false := by
    ext selected
    cases selected <;> simp [PMF.bernoulli_apply]
  have hmap : PMF.map (fun selected : Bool => if selected then sensitivity else 0)
      (PMF.bernoulli 0 hRate) = PMF.pure 0 := by
    rw [hBernoulli, PMF.pure_map]
    simp
  apply Subtype.ext
  simp [sampledGaussianOneStepSourceLaw, sampledGaussianOneStepReferenceLaw,
    bernoulliShiftLaw, gaussianNoiseLaw, hmap, PMF.toMeasure_pure]

/-- At zero Gaussian variance, the sampled one-step law is exactly the Bernoulli shift law. -/
theorem sampledGaussianOneStepSourceLaw_zeroNoiseVariance
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) :
    sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity 0 =
      bernoulliShiftLaw samplingRate hRate sensitivity := by
  apply Subtype.ext
  simp [sampledGaussianOneStepSourceLaw, gaussianNoiseLaw,
    ProbabilityTheory.gaussianReal_zero_var]

/-- At zero Gaussian variance, the reference one-step law is the point mass at zero. -/
theorem sampledGaussianOneStepReferenceLaw_zeroNoiseVariance :
    sampledGaussianOneStepReferenceLaw 0 =
      ⟨Measure.dirac (0 : Real), by infer_instance⟩ := by
  apply Subtype.ext
  simp [sampledGaussianOneStepReferenceLaw,
    ProbabilityTheory.gaussianReal_zero_var]

/-- Zero sensitivity makes the complete finite-horizon output laws coincide. -/
theorem sampledGaussianOutputSumSourceLaw_zeroSensitivity
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (noiseVariance : NNReal) :
    sampledGaussianOutputSumSourceLaw horizon samplingRate hRate 0 noiseVariance =
      sampledGaussianOutputSumReferenceLaw horizon noiseVariance := by
  simp [sampledGaussianOutputSumSourceLaw, sampledGaussianOutputSumReferenceLaw,
    sampledGaussianSourceProductLaw, sampledGaussianReferenceProductLaw,
    sampledGaussianOneStepSourceLaw_zeroSensitivity]

/-- Zero sampling rate makes the complete finite-horizon output laws coincide. -/
theorem sampledGaussianOutputSumSourceLaw_zeroSamplingRate
    (horizon : Nat) (hRate : (0 : NNReal) ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    sampledGaussianOutputSumSourceLaw horizon 0 hRate sensitivity noiseVariance =
      sampledGaussianOutputSumReferenceLaw horizon noiseVariance := by
  simp [sampledGaussianOutputSumSourceLaw, sampledGaussianOutputSumReferenceLaw,
    sampledGaussianSourceProductLaw, sampledGaussianReferenceProductLaw,
    sampledGaussianOneStepSourceLaw_zeroSamplingRate]

end

end Mf.DP
