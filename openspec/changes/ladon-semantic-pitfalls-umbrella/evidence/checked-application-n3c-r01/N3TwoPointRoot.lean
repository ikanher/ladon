import Mf.Optimization.StochasticApproximation.MultiplicativeDescent
open MeasureTheory Filter Set
open scoped Topology
namespace N3TwoPointRoot
noncomputable def μ : Measure Bool := (2 : ENNReal)⁻¹ • Measure.count
instance : IsProbabilityMeasure μ := by
  constructor
  rw [μ, Measure.smul_apply, Measure.count_apply MeasurableSet.univ]
  norm_num [Set.encard_pair]
  exact ENNReal.inv_mul_cancel (by norm_num) (by norm_num)
def F : Filtration ℕ (inferInstance : MeasurableSpace Bool) := Filtration.const ℕ _ le_rfl
def X (_n : ℕ) (ω : Bool) : ℝ := if ω then 1 else 0
def Z (_n : ℕ) (_ω : Bool) : ℝ := 0
lemma ae_all (p : Bool → Prop) : (∀ᵐ ω ∂μ, p ω) ↔ ∀ ω, p ω := by
  rw [μ, Measure.ae_ennreal_smul_measure_iff (by norm_num : (2 : ENNReal)⁻¹ ≠ 0), Measure.ae_count_iff]
def Premises : Prop :=
  StronglyAdapted F X ∧ StronglyAdapted F Z ∧
  (∀ n, Integrable (X n) μ) ∧ (∀ n, Integrable (Z n) μ) ∧
  (∀ᵐ ω ∂μ, ∀ n, 0 ≤ X n ω) ∧ (∀ᵐ ω ∂μ, ∀ n, 0 ≤ Z n ω) ∧
  (∀ᵐ ω ∂μ, Summable (fun n => Z n ω)) ∧
  (∀ᵐ ω ∂μ, Summable (fun n => |Z n ω|)) ∧
  (∀ n, μ[X (n+1) | F n] ≤ᵐ[μ] fun ω => (1+Z n ω)*X n ω - Z n ω + Z n ω)
theorem model_hypotheses : Premises := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact fun n => (measurable_of_finite (X n)).stronglyMeasurable
  · exact stronglyAdapted_const F 0
  · exact fun n => Integrable.of_finite
  · exact fun n => Integrable.of_finite
  · exact Filter.Eventually.of_forall (fun ω n => by cases ω <;> norm_num [X])
  · exact Filter.Eventually.of_forall (fun ω n => by simp [Z])
  · exact Filter.Eventually.of_forall (fun ω => by simp [Z])
  · exact Filter.Eventually.of_forall (fun ω => by simp [Z])
  · intro n
    have heq := condExp_of_stronglyMeasurable (F.le n) ((measurable_of_finite (X (n+1))).stronglyMeasurable) (Integrable.of_finite (μ := μ) (f := X (n+1)))
    rw [heq]
    exact Filter.Eventually.of_forall (fun ω => by simp [X, Z])
theorem samplewise_limit : ∀ᵐ ω ∂μ, Summable (fun n => Z n ω) ∧ ∃ x, 0 ≤ x ∧ Tendsto (fun n => X n ω) atTop (𝓝 x) := by
  rcases model_hypotheses with ⟨hx, hz, hxi, hzi, hx0, hz0, hzs, _, hstep⟩
  exact Mf.Optimization.StochasticApproximation.almost_supermartingale_converges F X Z Z Z hx hz hz hz hxi hzi hzi hx0 hz0 hz0 hzs hzs hstep
theorem no_common_limit : ¬ ∃ x : ℝ, ∀ᵐ ω ∂μ, Tendsto (fun n => X n ω) atTop (𝓝 x) := by
  rintro ⟨x, hx⟩
  have h := (ae_all _).mp hx
  have ht : (1 : ℝ) = x := by simpa [X] using h true
  have hf : (0 : ℝ) = x := by simpa [X] using h false
  linarith
#print axioms model_hypotheses
#print axioms samplewise_limit
#print axioms no_common_limit
end N3TwoPointRoot
