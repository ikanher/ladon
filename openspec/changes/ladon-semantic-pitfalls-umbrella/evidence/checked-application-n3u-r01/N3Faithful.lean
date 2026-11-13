import Mf.Optimization.StochasticApproximation.MultiplicativeDescent
open MeasureTheory Filter
open scoped Topology
open Mf.Optimization.StochasticApproximation
variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω} [IsProbabilityMeasure μ]
example (ℱ : Filtration ℕ mΩ) (X A B C : ℕ → Ω → ℝ)
    (hX : StronglyAdapted ℱ X) (hA : StronglyAdapted ℱ A)
    (hB : StronglyAdapted ℱ B) (hC : StronglyAdapted ℱ C)
    (hXi : ∀ n, Integrable (X n) μ) (hBi : ∀ n, Integrable (B n) μ)
    (hCi : ∀ n, Integrable (C n) μ)
    (hX0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ X n ω)
    (hA0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ A n ω)
    (hB0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ B n ω)
    (hAs : ∀ᵐ ω ∂μ, Summable (fun n => A n ω))
    (hCs : ∀ᵐ ω ∂μ, Summable (fun n => C n ω))
    (hstep : ∀ n, μ[X (n + 1) | ℱ n] ≤ᵐ[μ]
      fun ω => (1 + A n ω) * X n ω - B n ω + C n ω) :
    ∀ᵐ ω ∂μ, ∃ x, 0 ≤ x ∧ Tendsto (fun n => X n ω) atTop (𝓝 x) ∧
      Summable (fun n => B n ω) := by
  skip
