import Mf.DP.PoissonMomentRationalCertificate
import Mf.DP.PoissonMomentPrivacyCalibration

/-!
# Fraction-only certificates for the actual adaptive Poisson mechanism

Theorem 2 of *Rational arithmetic for Poisson Gaussian noise calibration*
(`latex/natural-language/poisson_gaussian_rational_calibration.tex`) applies
an accepted rational moment bound to the actual optional-record transcript.
The public sampling rate must equal the certified rational rate, and the
actual Gaussian noise multiplier may equal or exceed the certified rational
noise. Full-history adaptation, independent public initialization and common
randomized postprocessing are preserved.
-/

noncomputable section
open MeasureTheory ProbabilityTheory

namespace Mf.DP.PoissonAdaptiveQuery.Data
open PoissonMomentCalibration

/-- A rational certificate suffices at its specified noise or any larger noise. -/
theorem optionalTranscript_approxDP_of_rationalCheck
    {n d T m precision : ℕ} {Record : Type} (data : Data n d)
    {eps δ q σ : ℚ} (hc : Rational.check T m eps δ q σ precision = true)
    (hq : (data.q : ℝ) = q) (hnoise : (σ : ℝ) ≤ data.multiplier)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) eps δ := by
  obtain ⟨hv, hb⟩ := Rational.check_sound hc
  have hσ : (0 : ℝ) < σ := by exact_mod_cast hv.2.2.2.2.2.2.2
  have hδ : (0 : ℝ) < δ := by exact_mod_cast hv.2.2.2.1
  have hq0 : (0 : ℝ) ≤ q := by exact_mod_cast hv.2.2.2.2.2.1.le
  have hq1 : (q : ℝ) ≤ 1 := by exact_mod_cast hv.2.2.2.2.2.2.1.le
  have hx : 1 / data.multiplier ^ 2 ≤ 1 / (σ : ℝ) ^ 2 :=
    one_div_le_one_div_of_le (sq_pos_of_pos hσ)
      ((sq_le_sq₀ hσ.le data.multiplier_pos.le).2 hnoise)
  have ha := sampledGaussianRenyiMoment_mono_separation m hq0 hq1 hx
  have hl := Real.log_le_log
    (sampledGaussianRenyiMoment_pos m _ hq0 hq1) ha
  apply data.optionalTranscript_approxDP_of_moment hv.2.1 hδ _ g hg
  rw [hq]
  exact (mul_le_mul_of_nonneg_left hl (Nat.cast_nonneg T)).trans hb

end Mf.DP.PoissonAdaptiveQuery.Data

namespace Mf.DP.PoissonAdaptiveQuerySeed.Data
open PoissonMomentCalibration

/-- Independent public initialization preserves the rationally certified guarantee. -/
theorem publicSeedTranscript_approxDP_of_rationalCheck
    {n d T m precision : ℕ} {Seed Record : Type} [MeasurableSpace Seed]
    (data : PoissonAdaptiveQuery.Data n d) {eps δ q σ : ℚ}
    (hc : Rational.check T m eps δ q σ precision = true)
    (hq : (data.q : ℝ) = q) (hnoise : (σ : ℝ) ≤ data.multiplier)
    (μ : Measure Seed) [IsProbabilityMeasure μ]
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2)) :
    ApproxDP OptionalRecordAdjacent
      (fun D => μ ⊗ₘ optionalTranscriptKernel data g hg T D) eps δ := by
  apply Mf.DP.approxDP_publicSeed
  intro seed
  simpa only [optionalTranscriptKernel_apply] using
    data.optionalTranscript_approxDP_of_rationalCheck hc hq hnoise (g seed)
      (fun r t => (hg r t).comp measurable_prodMk_left)

/-- Common randomized postprocessing preserves the fraction-only certificate. -/
theorem publicSeedPostprocess_approxDP_of_rationalCheck
    {n d T m precision : ℕ} {Seed Record Output : Type}
    [MeasurableSpace Seed] [MeasurableSpace Output]
    (data : PoissonAdaptiveQuery.Data n d) {eps δ q σ : ℚ}
    (hc : Rational.check T m eps δ q σ precision = true)
    (hq : (data.q : ℝ) = q) (hnoise : (σ : ℝ) ≤ data.multiplier)
    (μ : Measure Seed) [IsProbabilityMeasure μ]
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (kernel : Seed × SumHistory d T → Measure Output)
    (hkernel : ∀ event, MeasurableSet event → Measurable (fun h => kernel h event))
    (hprob : ∀ h, kernel h Set.univ = 1) :
    ApproxDP OptionalRecordAdjacent
      (fun D => (μ ⊗ₘ optionalTranscriptKernel data g hg T D).bind kernel) eps δ :=
  Training.ApproxDP.bind_right
    (publicSeedTranscript_approxDP_of_rationalCheck data hc hq hnoise μ g hg)
    kernel hkernel hprob

end Mf.DP.PoissonAdaptiveQuerySeed.Data
