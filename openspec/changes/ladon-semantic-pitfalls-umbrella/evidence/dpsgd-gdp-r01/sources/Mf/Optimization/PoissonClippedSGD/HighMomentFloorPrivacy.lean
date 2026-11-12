import Mf.DP.PoissonHighMomentFloorGaussianProfile
import Mf.Optimization.PoissonClippedSGD.MixtureTranscript

/-!
# Exact-reference higher-moment privacy for adaptive Poisson SGD

The exact Gaussian separation and likelihood-floor alternative improve the
finite Gaussian-reference budget while preserving both adjacency directions
and the actual adaptive Poisson law. The common kernel is constructed for
each neighboring pair, with the fixed public denominator qN and multiplier
sqrt(V). Scalar budget feasibility remains an explicit intermediate premise;
public calibrations discharge it in consuming theorems.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.DP Mf.DP.PoissonHighMomentFloor

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData

/-- Both ordered event comparisons for any single optional-record deletion. -/
theorem optionalTranscript_highMomentFloor_eventBounds_of_deletion
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ : ℝ} (hV : 0 < V) (hθ : 0 < θ)
    (p : ℕ) (hp : 2 ≤ p) (hmult : data.multiplier = Real.sqrt V) (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hdel : OneRecordDeletion D D') {A : Set (SumHistory d T)} (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        poissonHighMomentFloorBudget T data.q V ε θ p ∧
    (data.optionalTranscriptLaw g hg T D').real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D).real A +
        poissonHighMomentFloorBudget T data.q V ε θ p := by
  cases n with
  | zero =>
      obtain ⟨i, _⟩ := hdel
      exact Fin.elim0 i
  | succ n =>
      obtain ⟨K, hK, hP, hQ⟩ := ActualMixture.optionalTranscript_commonMixtureKernel_variance
        data V hV hmult g hg D D' hdel T
      let : IsMarkovKernel K := hK
      exact actual_eventBounds_of_commonKernel hT data.q data.q_le_one
        (by exact_mod_cast data.q_pos) hV hθ p hp ε K _ _ hP hQ hA

/-- Universal higher-moment event bound for symmetric optional-record adjacency. -/
theorem optionalTranscript_highMomentFloor_eventBound
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ : ℝ} (hV : 0 < V) (hθ : 0 < θ)
    (p : ℕ) (hp : 2 ≤ p) (hmult : data.multiplier = Real.sqrt V) (ε : ℝ)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D D' : Fin n → Option Record)
    (hadj : OptionalRecordAdjacent D D') {A : Set (SumHistory d T)}
    (hA : MeasurableSet A) :
    (data.optionalTranscriptLaw g hg T D).real A ≤
      Real.exp ε * (data.optionalTranscriptLaw g hg T D').real A +
        poissonHighMomentFloorBudget T data.q V ε θ p := by
  rcases hadj with hdel | hdel
  · exact (data.optionalTranscript_highMomentFloor_eventBounds_of_deletion
      hT hV hθ p hp hmult ε g hg D D' hdel hA).1
  · exact (data.optionalTranscript_highMomentFloor_eventBounds_of_deletion
      hT hV hθ p hp hmult ε g hg D' D hdel hA).2

/-- A sufficient higher-moment budget certifies actual transcript DP. -/
theorem optionalTranscript_highMomentFloor_approxDP_of_budget
    {n d T : ℕ} {Record : Type} (data : PrivacyData n d)
    (hT : 1 ≤ T) {V θ ε δ : ℝ} (hV : 0 < V) (hθ : 0 < θ) (hδ : 0 ≤ δ)
    (p : ℕ) (hp : 2 ≤ p) (hmult : data.multiplier = Real.sqrt V)
    (hbudget : poissonHighMomentFloorBudget T data.q V ε θ p ≤ δ)
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
  have h := data.optionalTranscript_highMomentFloor_eventBound hT hV hθ p hp hmult ε
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
