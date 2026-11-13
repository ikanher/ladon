import Mf.Optimization.StochasticApproximation.MultiplicativeDescent

open MeasureTheory Filter Finset Set
open scoped Topology
namespace Mf.Optimization.StochasticApproximation
noncomputable section

/- A one point probability space makes the stochastic counterexample a genuine
   probability model, while keeping every random variable deterministic. -/
abbrev N3Ω := Unit
abbrev N3μ : Measure N3Ω := Measure.dirac ()

def n3Filtration : Filtration ℕ (inferInstance : MeasurableSpace N3Ω) := ⊤
def n3X : ℕ → N3Ω → ℝ := fun n _ => -(n : ℝ)
def n3A : ℕ → N3Ω → ℝ := fun _ _ => 0
def n3B : ℕ → N3Ω → ℝ := fun _ _ => 1
def n3C : ℕ → N3Ω → ℝ := fun _ _ => 0

theorem n3_singleton_counterexample
    : StronglyAdapted n3Filtration n3X ∧
      StronglyAdapted n3Filtration n3A ∧
      StronglyAdapted n3Filtration n3B ∧
      StronglyAdapted n3Filtration n3C ∧
      (∀ n, Integrable (n3X n) N3μ) ∧
      (∀ n, Integrable (n3B n) N3μ) ∧
      (∀ n, Integrable (n3C n) N3μ) ∧
      (∀ᵐ ω ∂N3μ, ∀ n, 0 ≤ n3A n ω) ∧
      (∀ᵐ ω ∂N3μ, ∀ n, 0 ≤ n3B n ω) ∧
      (∀ᵐ ω ∂N3μ, Summable (fun n => n3A n ω)) ∧
      (∀ᵐ ω ∂N3μ, Summable (fun n => n3C n ω)) ∧
      (∀ n, N3μ[n3X (n + 1) | n3Filtration n] ≤ᵐ[N3μ]
        fun ω => (1 + n3A n ω) * n3X n ω - n3B n ω + n3C n ω) ∧
      ¬ (∀ᵐ ω ∂N3μ, Summable (fun n => n3B n ω)) := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · intro n; exact stronglyMeasurable_const
  · intro n; exact stronglyMeasurable_const
  · intro n; exact stronglyMeasurable_const
  · intro n; exact stronglyMeasurable_const
  · intro n; exact integrable_const _
  · intro n; exact integrable_const _
  · intro n; exact integrable_const _
  · filter_upwards [] with ω n; simp [n3A]
  · filter_upwards [] with ω n; simp [n3B]
  · filter_upwards [] with ω
    simpa [n3A] using (summable_zero : Summable (fun _ : ℕ => (0 : ℝ)))
  · filter_upwards [] with ω
    simpa [n3C] using (summable_zero : Summable (fun _ : ℕ => (0 : ℝ)))
  · intro n
    have hc := condExp_of_stronglyMeasurable (n3Filtration.le n)
      (stronglyMeasurable_const : StronglyMeasurable[n3Filtration n]
        (fun _ : N3Ω => (-(n + 1 : ℕ) : ℝ)))
      (show Integrable (fun _ : N3Ω => (-(↑(n + 1) : ℝ))) N3μ from
        integrable_const (-(↑(n + 1) : ℝ)))
    filter_upwards [] with ω
    change N3μ[(fun _ : N3Ω => (-(↑(n + 1) : ℝ))) | n3Filtration n] ω ≤ _
    rw [hc]
    simp [n3A, n3B, n3C, n3X]
    linarith
  · intro h
    have h0 : Summable (fun _ : ℕ => (1 : ℝ)) := by
      change ∀ᵐ ω ∂N3μ, Summable (fun _ : ℕ => (1 : ℝ)) at h
      by_contra hs
      have heq := ae_iff.mp h
      have : () ∈ {ω : N3Ω | ¬ Summable (fun _ : ℕ => (1 : ℝ))} := by simpa using hs
      have hpos : N3μ {ω : N3Ω | ¬ Summable (fun _ : ℕ => (1 : ℝ))} ≠ 0 := by
        simp [N3μ, this]
      exact hpos heq
    have ht := h0.tendsto_atTop_zero
    have hc : Tendsto (fun _ : ℕ => (1 : ℝ)) atTop (𝓝 1) := tendsto_const_nhds
    have : (1 : ℝ) = 0 := tendsto_nhds_unique hc ht
    norm_num at this

theorem n3_singleton_absolute_error : ∀ᵐ ω ∂N3μ, Summable (fun n => |n3C n ω|) := by
  exact Filter.Eventually.of_forall (fun ω => by simp [n3C])
#print axioms n3_singleton_counterexample
#print axioms n3_singleton_absolute_error

end
end Mf.Optimization.StochasticApproximation
