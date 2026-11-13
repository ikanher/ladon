import Mf.DP.LawAccountingOracle
import Mathlib.Probability.Distributions.Gaussian.Real

/-!
# Gaussian noise monotonicity

This module realizes larger Gaussian variance as the addition of one common
independent centered Gaussian law.  The exact binary accounting profile is
therefore antitone in the variance parameter.
-/

open MeasureTheory

namespace Mf.DP

noncomputable section

/-- Add an independent centered Gaussian law of variance `variance` to `mu`. -/
def gaussianNoiseLaw
    (mu : ProbabilityMeasure Real) (variance : NNReal) : ProbabilityMeasure Real :=
  ⟨(mu : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 variance, by
    infer_instance⟩

/-- Adding a residual Gaussian variance realizes the corresponding larger-noise law. -/
lemma gaussianNoiseLaw_residualVariance
    (mu : ProbabilityMeasure Real) {small large residual : NNReal}
    (hvariance : large = small + residual) :
    gaussianNoiseLaw mu large =
      ⟨((mu : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 small) ∗
          ProbabilityTheory.gaussianReal 0 residual, by infer_instance⟩ := by
  apply Subtype.ext
  simp [gaussianNoiseLaw, hvariance, Measure.conv_assoc,
    ProbabilityTheory.gaussianReal_conv_gaussianReal]

/-- Increasing a common Gaussian variance cannot increase exact binary accounting. -/
theorem binaryAccountingProfile_gaussianNoiseVariance_antitone
    (mu nu : ProbabilityMeasure Real) (epsilon : Real)
    {small large : NNReal} (hvariance : small ≤ large) :
    binaryAccountingProfile (gaussianNoiseLaw mu large)
        (gaussianNoiseLaw nu large) epsilon ≤
      binaryAccountingProfile (gaussianNoiseLaw mu small)
        (gaussianNoiseLaw nu small) epsilon := by
  let residual : NNReal := large - small
  have hresidual : large = small + residual :=
    (add_tsub_cancel_of_le hvariance).symm
  rw [gaussianNoiseLaw_residualVariance mu hresidual,
    gaussianNoiseLaw_residualVariance nu hresidual]
  change binaryAccountingProfile
    (⟨((mu : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 small) ∗
      ProbabilityTheory.gaussianReal 0 residual, by infer_instance⟩)
    (⟨((nu : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 small) ∗
      ProbabilityTheory.gaussianReal 0 residual, by infer_instance⟩) epsilon ≤ _
  exact binaryAccountingProfile_add_common_noise_le
    (⟨(mu : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 small, by infer_instance⟩)
    (⟨(nu : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 small, by infer_instance⟩)
    (⟨ProbabilityTheory.gaussianReal 0 residual, by infer_instance⟩) epsilon

end

end Mf.DP
