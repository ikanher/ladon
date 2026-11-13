import Mf.Optimization.StochasticApproximation.MultiplicativeDescent
open MeasureTheory Filter
open scoped Topology
open Mf.Optimization.StochasticApproximation
variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω} [IsProbabilityMeasure μ]
theorem n3Shifted (ℱ : Filtration ℕ mΩ) (X A B C : ℕ → Ω → ℝ)
    (hX : StronglyAdapted ℱ X) (hA : StronglyAdapted ℱ A)
    (hB : StronglyAdapted ℱ B) (hC : StronglyAdapted ℱ C)
    (hXi : ∀ n, Integrable (X n) μ) (hBi : ∀ n, Integrable (B n) μ)
    (hCi : ∀ n, Integrable (C n) μ)
    (K : ℝ) (hK : 0 ≤ K) (hlower : ∀ᵐ ω ∂μ, ∀ n, -K ≤ X n ω)
    (hA0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ A n ω)
    (hB0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ B n ω)
    (hAs : ∀ᵐ ω ∂μ, Summable (fun n => A n ω))
    (hCs : ∀ᵐ ω ∂μ, Summable (fun n => C n ω))
    (hstep : ∀ n, μ[X (n + 1) | ℱ n] ≤ᵐ[μ]
      fun ω => (1 + A n ω) * X n ω - B n ω + C n ω) :
    ∀ᵐ ω ∂μ, ∃ x, -K ≤ x ∧ Tendsto (fun n => X n ω) atTop (𝓝 x) ∧
      Summable (fun n => B n ω) := by
by
  let Y := fun n ω => X n ω + K
  have hY : StronglyAdapted ℱ Y := fun n => (hX n).add stronglyMeasurable_const
  have hYi : ∀ n, Integrable (Y n) μ := fun n => (hXi n).add (integrable_const K)
  have hY0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ Y n ω := hlower.mono (fun ω h n => by dsimp [Y]; linarith [h n])
  have hYstep : ∀ n, μ[Y (n + 1) | ℱ n] ≤ᵐ[μ] fun ω => (1 + A n ω) * Y n ω - B n ω + C n ω := by
    intro n
    have heq := condExp_add (hXi (n+1)) (integrable_const K) (ℱ n)
    filter_upwards [heq, hstep n, hA0] with ω heq hstep hA
    dsimp [Y] at *
    rw [condExp_const (ℱ.le n) K] at heq
    rw [heq]
    nlinarith [mul_nonneg hK (hA n)]
  have h := almost_supermartingale_converges ℱ Y A B C hY hA hB hC hYi hBi hCi hY0 hA0 hB0 hAs hCs hYstep
  filter_upwards [h] with ω hω
  rcases hω with ⟨hb, y, hy, hlim⟩
  refine ⟨y - K, by linarith, ?_, hb⟩
  convert hlim.sub_const K using 1 <;> simp [Y]

#print axioms n3Shifted
