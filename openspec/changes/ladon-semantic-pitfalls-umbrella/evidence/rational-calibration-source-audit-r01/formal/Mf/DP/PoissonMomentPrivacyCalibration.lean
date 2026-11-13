import Mf.DP.PoissonMomentSelection
import Mf.DP.PoissonAdaptiveQuerySeed

/-!
# Instance-calibrated privacy for the actual adaptive Poisson mechanism

Theorem 3 of `latex/natural-language/poisson_gaussian_instance_calibration.tex`
chooses noise by the exact finite binomial moment. These theorems consume the
selected moment inequality on the actual optional-record transcript law,
including full-history queries, independent public initialization, and common
randomized postprocessing. Every multiplier at least the selected value is
covered; no additional epsilon cutoff is assumed.

The minimum is over the explicitly chosen finite family of integer moments.
It is not a claim of optimal noise for differential privacy or an implementation
of numerical root finding.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
namespace Mf.DP.PoissonMomentCalibration

lemma tailBudget_le_of_moment {T m : ℕ} {q σ eps δ : ℝ}
    (hm : 2 ≤ m) (hq : 0 < q) (hq1 : q ≤ 1) (hσ : 0 < σ) (hδ : 0 < δ)
    (hc : (T : ℝ) * Real.log (sampledGaussianRenyiMoment m q (1 / σ ^ 2)) ≤
      ((m : ℝ) - 1) * eps - Real.log (1 / δ)) :
    Real.exp (((m : ℝ) - 1) *
      ((T : ℝ) * max 0 (sampledGaussianForwardRho m q (1 / σ ^ 2)) - eps)) ≤ δ := by
  have hmR : (2 : ℝ) ≤ m := by exact_mod_cast hm
  have hden : 0 < (m : ℝ) - 1 := by linarith
  have hl := log_moment_pos hm hq hq1 (by positivity : 0 < 1 / σ ^ 2)
  unfold sampledGaussianForwardRho
  rw [max_eq_right (div_pos hl hden).le]
  have hid : ((m : ℝ) - 1) *
      ((T : ℝ) * (Real.log (sampledGaussianRenyiMoment m q (1 / σ ^ 2)) /
        ((m : ℝ) - 1)) - eps) =
      (T : ℝ) * Real.log (sampledGaussianRenyiMoment m q (1 / σ ^ 2)) -
        ((m : ℝ) - 1) * eps := by field_simp
  rw [hid]
  calc
    _ ≤ Real.exp (-Real.log (1 / δ)) := Real.exp_le_exp.2 (by linarith)
    _ = δ := by rw [Real.exp_neg, Real.exp_log (one_div_pos.mpr hδ), inv_div, div_one]

private lemma constant_budget (rho : ℝ) (T : ℕ) :
    adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ) * rho := by
  induction T with
  | zero => simp
  | succ T ih => simp [adaptiveRenyiBudget_succ, ih, Nat.cast_add, add_mul]

end Mf.DP.PoissonMomentCalibration

namespace Mf.DP.PoissonAdaptiveQuery.Data
open PoissonMomentCalibration
open Mf.Optimization

/-- A checked finite-moment inequality certifies the actual optional-record law. -/
theorem optionalTranscript_approxDP_of_moment
    {n d T m : ℕ} {Record : Type} (data : Data n d) {eps δ : ℝ}
    (hm : 2 ≤ m) (hδ : 0 < δ)
    (hc : (T : ℝ) * Real.log (sampledGaussianRenyiMoment m data.q (1 / data.multiplier ^ 2)) ≤
      ((m : ℝ) - 1) * eps - Real.log (1 / δ))
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) eps δ := by
  have ht := tailBudget_le_of_moment hm (by exact_mod_cast data.q_pos)
    data.q_le_one data.multiplier_pos hδ hc
  apply approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T eps)
  simp only [PoissonMomentCalibration.constant_budget, SDE.euclideanSampledGaussianSharpStepRho]
  convert ht using 1
  rfl

/-- Every noise above the selected finite-family minimum certifies the actual transcript. -/
theorem optionalTranscript_approxDP_of_familyNoise
    {n d T : ℕ} {Record : Type} (data : Data n d) {eps δ : ℝ}
    {S : Finset ℕ} (hS : S.Nonempty) (hadm : ∀ m ∈ S, admissible eps δ m)
    (hT : 0 < T) (hδ : 0 < δ) (hnoise : familyNoise S T eps δ data.q ≤ data.multiplier)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) eps δ := by
  obtain ⟨m, hm, hc⟩ := (finiteFamily_iff hS hadm hT
    (by exact_mod_cast data.q_pos) data.q_le_one data.multiplier_pos).2 hnoise
  exact data.optionalTranscript_approxDP_of_moment (hadm m hm).1 hδ hc g hg

/-- A successful four-input calibration suffices at its output noise or any larger value. -/
theorem optionalTranscript_approxDP_of_calibrate
    {n d T : ℕ} {Record : Type} (data : Data n d) {eps δ : ℝ} {r : Calibration}
    (hr : calibrate T eps δ data.q = some r) (hnoise : r.noise ≤ data.multiplier)
    (g : Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (g r t)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) eps δ := by
  obtain ⟨hv, _, hadm, hn, _, _, _, hc⟩ := calibrate_spec hr
  have hq : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
  have ht := (fixedOrder_iff hv.1 hadm hq data.q_le_one hn).1 hc
  have hc' := (fixedOrder_iff hv.1 hadm hq data.q_le_one data.multiplier_pos).2 (ht.trans hnoise)
  exact data.optionalTranscript_approxDP_of_moment hadm.1 hv.2.2.1 hc' g hg

end Mf.DP.PoissonAdaptiveQuery.Data

namespace Mf.DP.PoissonAdaptiveQuerySeed.Data
open PoissonMomentCalibration

/-- The selected noise certifies public random initialization and the complete history. -/
theorem publicSeedTranscript_approxDP_of_calibrate
    {n d T : ℕ} {Seed Record : Type} [MeasurableSpace Seed]
    (data : PoissonAdaptiveQuery.Data n d) {eps δ : ℝ} {r : Calibration}
    (hr : calibrate T eps δ data.q = some r) (hnoise : r.noise ≤ data.multiplier)
    (μ : Measure Seed) [IsProbabilityMeasure μ]
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2)) :
    ApproxDP OptionalRecordAdjacent
      (fun D => μ ⊗ₘ optionalTranscriptKernel data g hg T D) eps δ := by
  apply Mf.DP.approxDP_publicSeed
  intro seed
  simpa only [optionalTranscriptKernel_apply] using
    data.optionalTranscript_approxDP_of_calibrate hr hnoise (g seed)
      (fun r t => (hg r t).comp measurable_prodMk_left)

/-- Common randomized postprocessing preserves the instance-calibrated guarantee. -/
theorem publicSeedPostprocess_approxDP_of_calibrate
    {n d T : ℕ} {Seed Record Output : Type} [MeasurableSpace Seed] [MeasurableSpace Output]
    (data : PoissonAdaptiveQuery.Data n d) {eps δ : ℝ} {r : Calibration}
    (hr : calibrate T eps δ data.q = some r) (hnoise : r.noise ≤ data.multiplier)
    (μ : Measure Seed) [IsProbabilityMeasure μ]
    (g : Seed → Record → (t : ℕ) → SumHistory d t → SumRelease d)
    (hg : ∀ r t, Measurable (fun p : Seed × SumHistory d t => g p.1 r t p.2))
    (kernel : Seed × SumHistory d T → Measure Output)
    (hkernel : ∀ event, MeasurableSet event → Measurable (fun h => kernel h event))
    (hprob : ∀ h, kernel h Set.univ = 1) :
    ApproxDP OptionalRecordAdjacent
      (fun D => (μ ⊗ₘ optionalTranscriptKernel data g hg T D).bind kernel) eps δ :=
  Training.ApproxDP.bind_right
    (publicSeedTranscript_approxDP_of_calibrate data hr hnoise μ g hg) kernel hkernel hprob

end Mf.DP.PoissonAdaptiveQuerySeed.Data
