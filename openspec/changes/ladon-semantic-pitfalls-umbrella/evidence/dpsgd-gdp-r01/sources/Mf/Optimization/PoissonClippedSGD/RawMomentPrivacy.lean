import Mf.DP.PoissonRawMomentGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Actual adaptive Poisson privacy with the raw-moment reference alternative

The exact Gaussian-reference comparison uses the better of the centered and
raw forward moment allowances, retaining floor, reciprocal and Bennett reverse
branches and their full
composition factor. The pair-specific simulator constructs both actual law
identities, preserving optional-slot adjacency and public normalization qN.
A public calibration must discharge the scalar feasibility premise of the
approximate-DP adapter; the event theorem itself constructs its error bound.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonRawMomentGaussianProfile

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both ordered event comparisons for any single optional-record deletion. -/
theorem optionalTranscript_rawMoment_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ : ℝ} (hV : 0 < V) (hθ : 0 < θ)
    (p : ℕ) (hp : 2 ≤ p) (nrev : ℕ) (hnrev : 1 ≤ nrev) (hmult : data.multiplier = Real.sqrt V) (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        poissonRawMomentBudget T data.q V ε θ p nrev ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D).real A +
        poissonRawMomentBudget T data.q V ε θ p nrev := by
  cases n with
  | zero =>
      obtain ⟨i, _⟩ := hdel
      exact Fin.elim0 i
  | succ n =>
      obtain ⟨K, hK, hP, hQ⟩ := ActualMixture.optionalTranscript_commonMixtureKernel_variance
        data V hV hmult g hg D D' hdel T
      let : IsMarkovKernel K := hK
      exact actual_eventBounds_of_commonKernel hT data.q data.q_le_one
        (by exact_mod_cast data.q_pos) hV hθ p hp nrev hnrev ε K _ _ hP hQ hA

/-- Universal higher-moment event bound for symmetric optional-record adjacency. -/
theorem optionalTranscript_rawMoment_eventBound
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ : ℝ} (hV : 0 < V) (hθ : 0 < θ)
    (p : ℕ) (hp : 2 ≤ p) (nrev : ℕ) (hnrev : 1 ≤ nrev) (hmult : data.multiplier = Real.sqrt V) (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hadj : OptionalRecordAdjacent D D') {A : Set (SumHistory d T)}
    (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        poissonRawMomentBudget T data.q V ε θ p nrev := by
  rcases hadj with hdel | hdel
  · exact (data.optionalTranscript_rawMoment_eventBounds_of_deletion
      hT hV hθ p hp nrev hnrev hmult ε g hg D D' hdel hA).1
  · exact (data.optionalTranscript_rawMoment_eventBounds_of_deletion
      hT hV hθ p hp nrev hnrev hmult ε g hg D' D hdel hA).2

/-- A sufficient higher-moment budget certifies actual transcript DP. -/
theorem optionalTranscript_rawMoment_approxDP_of_budget
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ ε δ : ℝ} (hV : 0 < V) (hθ : 0 < θ) (hδ : 0 ≤ δ)
    (p : ℕ) (hp : 2 ≤ p) (nrev : ℕ) (hnrev : 1 ≤ nrev) (hmult : data.multiplier = Real.sqrt V)
    (hbudget : poissonRawMomentBudget T data.q V ε θ p nrev ≤ δ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) :
    ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) ε δ := by
  intro D D' hadj A hA
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D) := by
    unfold optionalTranscriptLaw
    infer_instance
  let : IsProbabilityMeasure (data.optionalTranscriptLaw g hg T D') := by
    unfold optionalTranscriptLaw
    infer_instance
  have h := data.optionalTranscript_rawMoment_eventBound hT hV hθ p hp nrev hnrev hmult ε
    g hg D D' hadj hA
  have hb : (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A + δ := by
    linarith
  have hh := ENNReal.ofReal_le_ofReal hb
  rw [ENNReal.ofReal_add (mul_nonneg (Real.exp_pos ε).le measureReal_nonneg) hδ,
    ENNReal.ofReal_mul (Real.exp_pos ε).le] at hh
  simpa only [measureReal_def,
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D) A),
    ENNReal.ofReal_toReal (measure_ne_top (data.optionalTranscriptLaw g hg T D') A)] using hh

end Mf.Optimization.PoissonClippedSGD.PrivacyData
