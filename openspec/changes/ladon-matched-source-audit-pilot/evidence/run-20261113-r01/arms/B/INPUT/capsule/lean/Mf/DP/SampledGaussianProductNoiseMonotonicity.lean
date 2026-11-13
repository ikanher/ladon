import Mf.DP.SampledGaussianCalibratedStddev
import Mathlib.MeasureTheory.Constructions.Pi

/-!
# Product sampled-Gaussian noise monotonicity

Larger coordinatewise Gaussian variance is realized by adding one independent
residual Gaussian vector to both neighboring product laws.  Common randomized
postprocessing therefore makes the exact binary profile antitone in variance
and in the public standard-deviation parameter.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

/-- Independent centered Gaussian coordinates with a common variance. -/
def centeredGaussianProductLaw (horizon : Nat) (variance : NNReal) :
    ProbabilityMeasure (Fin horizon → Real) :=
  ProbabilityMeasure.pi (fun _ => ⟨gaussianReal 0 variance, by infer_instance⟩)

/-- Add two finite real vectors coordinatewise. -/
def coordinatewiseAdd (horizon : Nat) :
    (Fin horizon → Real) × (Fin horizon → Real) → (Fin horizon → Real) :=
  fun pair coordinate => pair.1 coordinate + pair.2 coordinate

theorem measurable_coordinatewiseAdd (horizon : Nat) :
    Measurable (coordinatewiseAdd horizon) := by
  unfold coordinatewiseAdd
  fun_prop

/-- Reassociate two finite product measures and apply the same map coordinatewise. -/
theorem map_productMeasures_coordinatewise
    {ι X Z Y : Type*} [Fintype ι]
    [MeasurableSpace X] [MeasurableSpace Z] [MeasurableSpace Y]
    (f : X × Z → Y) (hf : Measurable f)
    (mu : ι → Measure X) (rho : ι → Measure Z)
    [∀ i, IsFiniteMeasure (mu i)] [∀ i, IsFiniteMeasure (rho i)]
    [∀ i, SigmaFinite (mu i)] [∀ i, SigmaFinite (rho i)] :
    Measure.map (fun pair : (ι → X) × (ι → Z) =>
        fun i => f (pair.1 i, pair.2 i))
        ((Measure.pi mu).prod (Measure.pi rho)) =
      Measure.pi (fun i => Measure.map f ((mu i).prod (rho i))) := by
  let e : (ι → X × Z) ≃ᵐ (ι → X) × (ι → Z) :=
    MeasurableEquiv.arrowProdEquivProdArrow X Z ι
  have he : Measure.map e (Measure.pi (fun i => (mu i).prod (rho i))) =
      (Measure.pi mu).prod (Measure.pi rho) :=
    measurePreserving_arrowProdEquivProdArrow X Z ι mu rho |>.map_eq
  rw [← he, Measure.map_map (by fun_prop) e.measurable]
  have hfun :
      (fun pair : (ι → X) × (ι → Z) => fun i => f (pair.1 i, pair.2 i)) ∘ e =
        (fun sample : ι → X × Z => fun i => f (sample i)) := by
    funext sample i
    rfl
  rw [hfun, Measure.pi_map_pi (fun _ => hf.aemeasurable)]

/-- Adding a residual Gaussian vector realizes the larger-variance sampled source product. -/
theorem sampledGaussianSourceProductLaw_add_residual
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (small large residual : NNReal)
    (hvariance : large = small + residual) :
    Measure.map (coordinatewiseAdd horizon)
      ((sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity small).prod
        (centeredGaussianProductLaw horizon residual) :
        Measure ((Fin horizon → Real) × (Fin horizon → Real))) =
      (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity large :
        Measure (Fin horizon → Real)) := by
  let mu : Fin horizon → Measure Real := fun _ =>
    (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity small : Measure Real)
  let rho : Fin horizon → Measure Real := fun _ => gaussianReal 0 residual
  change Measure.map (coordinatewiseAdd horizon)
      ((Measure.pi mu).prod (Measure.pi rho)) = _
  unfold coordinatewiseAdd
  rw [map_productMeasures_coordinatewise
    (fun pair : Real × Real => pair.1 + pair.2)
    (measurable_fst.add measurable_snd) mu rho]
  congr 1
  funext coordinate
  change (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity small :
      Measure Real) ∗ gaussianReal 0 residual = _
  simp [sampledGaussianOneStepSourceLaw, gaussianNoiseLaw, hvariance,
    Measure.conv_assoc, gaussianReal_conv_gaussianReal]

/-- Adding the same residual vector realizes the larger-variance reference product. -/
theorem sampledGaussianReferenceProductLaw_add_residual
    (horizon : Nat) (small large residual : NNReal)
    (hvariance : large = small + residual) :
    Measure.map (coordinatewiseAdd horizon)
      ((sampledGaussianReferenceProductLaw horizon small).prod
        (centeredGaussianProductLaw horizon residual) :
        Measure ((Fin horizon → Real) × (Fin horizon → Real))) =
      (sampledGaussianReferenceProductLaw horizon large :
        Measure (Fin horizon → Real)) := by
  simpa [sampledGaussianReferenceProductLaw, sampledGaussianSourceProductLaw,
    sampledGaussianOneStepSourceLaw_zeroSamplingRate] using
    (sampledGaussianSourceProductLaw_add_residual horizon 0 (by norm_num) 0
      small large residual hvariance)

/-- The exact sampled product profile is antitone in per-coordinate variance. -/
theorem sampledGaussianProductProfile_variance_antitone
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon : Real) {small large : NNReal} (hvariance : small ≤ large) :
    binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity large)
        (sampledGaussianReferenceProductLaw horizon large) epsilon ≤
      binaryAccountingProfile
        (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity small)
        (sampledGaussianReferenceProductLaw horizon small) epsilon := by
  let residual : NNReal := large - small
  have hsum : large = small + residual := (add_tsub_cancel_of_le hvariance).symm
  have hcontract := binaryAccountingProfile_common_randomized_map_le
    (coordinatewiseAdd horizon) (measurable_coordinatewiseAdd horizon)
    (sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity small)
    (sampledGaussianReferenceProductLaw horizon small)
    (centeredGaussianProductLaw horizon residual) epsilon
  have hsource :
      ((sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity small).prod
          (centeredGaussianProductLaw horizon residual)).map
            (measurable_coordinatewiseAdd horizon).aemeasurable =
        sampledGaussianSourceProductLaw horizon samplingRate hRate sensitivity large := by
    apply Subtype.ext
    exact sampledGaussianSourceProductLaw_add_residual horizon samplingRate hRate sensitivity
      small large residual hsum
  have hreference :
      ((sampledGaussianReferenceProductLaw horizon small).prod
          (centeredGaussianProductLaw horizon residual)).map
            (measurable_coordinatewiseAdd horizon).aemeasurable =
        sampledGaussianReferenceProductLaw horizon large := by
    apply Subtype.ext
    exact sampledGaussianReferenceProductLaw_add_residual horizon small large residual hsum
  rw [hsource, hreference] at hcontract
  exact hcontract

/-- The public standard-deviation profile is antitone in noise standard deviation. -/
theorem sampledGaussianProductProfileStddev_antitone
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity epsilon : Real) {small large : NNReal} (hStddev : small ≤ large) :
    sampledGaussianProductProfileStddev horizon samplingRate hRate sensitivity large epsilon ≤
      sampledGaussianProductProfileStddev horizon samplingRate hRate sensitivity small epsilon := by
  unfold sampledGaussianProductProfileStddev
  exact sampledGaussianProductProfile_variance_antitone horizon samplingRate hRate
    sensitivity epsilon (pow_le_pow_left' hStddev 2)

end

end Mf.DP
