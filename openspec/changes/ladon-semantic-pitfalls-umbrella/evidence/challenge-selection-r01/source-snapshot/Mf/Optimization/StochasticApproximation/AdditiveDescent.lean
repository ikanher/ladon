import Mf.Optimization.StochasticApproximation.StoppedDescent
import Mf.Optimization.StochasticApproximation.EnergyBalance

/-!
# Conditional descent with pathwise summable errors

Robbins and Siegmund, *A convergence theorem for non negative almost
supermartingales and some applications* (1971), provides the historical
almost-supermartingale principle. The inspected modern proof is Neri and
Powell, *A quantitative Robbins–Siegmund theorem*, arXiv:2410.15986v2,
proof `res:RS`; original-source access remains recorded in the H04 contract.

This file proves the additive-error case using the predictable-error stopping
adapter. Finite-prefix integrability suffices; no expectation of the infinite
error sum is assumed. Multiplicative normalization is a separate adapter.
-/

open MeasureTheory Filter Finset Set
open scoped Topology
namespace Mf.Optimization.StochasticApproximation

/-- A convergent compensated balance with a nonnegative state and dissipation
recovers summable dissipation and a finite nonnegative state limit. -/
theorem convergent_compensated_descent (Z d c M : ℕ → ℝ)
    (hZ : ∀ n, 0 ≤ Z n) (hd : ∀ n, 0 ≤ d n)
    (hc : Summable c) (hM : ∃ m, Tendsto M atTop (𝓝 m))
    (heq : ∀ n, M n = Z n + ∑ j ∈ range n, d j - ∑ j ∈ range n, c j) :
    Summable d ∧ ∃ z, 0 ≤ z ∧ Tendsto Z atTop (𝓝 z) := by
  obtain ⟨m,hm⟩ := hM
  have hsum := hm.add hc.hasSum.tendsto_sum_nat
  obtain ⟨R,hR⟩ := hsum.bddAbove_range
  have hds : Summable d := summable_of_sum_range_le hd (c := R) (by
    intro n
    have hb := hR (mem_range_self n)
    linarith [heq n,hZ n])
  have hz : Tendsto Z atTop (𝓝 (m + ∑' j, c j - ∑' j, d j)) := by
    have heq' : Z = fun n => M n + ∑ j ∈ range n, c j - ∑ j ∈ range n, d j := by
      funext n; linarith [heq n]
    rw [heq']
    exact hsum.sub hds.hasSum.tendsto_sum_nat
  exact ⟨hds,_,ge_of_tendsto hz (Eventually.of_forall hZ),hz⟩

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω} [IsProbabilityMeasure μ]

/-- The prefix including the current predictable increment is measurable now. -/
theorem predictable_sum_adapted (ℱ : Filtration ℕ mΩ) (c : ℕ → Ω → ℝ)
    (hc : StronglyAdapted ℱ c) :
    StronglyAdapted ℱ (fun n ω => ∑ j ∈ range (n+1), c j ω) := by
  intro n
  convert (Finset.stronglyMeasurable_sum (range (n+1)) (fun j hj =>
      (hc j).mono (ℱ.mono (Nat.le_of_lt_succ (mem_range.mp hj))))) using 1
  ext ω
  simp

/-- Compensate conditional descent by accumulated dissipation minus accumulated
error. Every prefix is integrable and the resulting process is a supermartingale. -/
theorem additive_descent_supermartingale (ℱ : Filtration ℕ mΩ)
    (Z d c : ℕ → Ω → ℝ)
    (hZ : StronglyAdapted ℱ Z) (hd : StronglyAdapted ℱ d) (hc : StronglyAdapted ℱ c)
    (hZi : ∀ n, Integrable (Z n) μ) (hdi : ∀ n, Integrable (d n) μ)
    (hci : ∀ n, Integrable (c n) μ)
    (hstep : ∀ n, μ[Z (n + 1) | ℱ n] ≤ᵐ[μ] fun ω => Z n ω - d n ω + c n ω) :
    Supermartingale (fun n ω => Z n ω + ∑ j ∈ range n, d j ω -
      ∑ j ∈ range n, c j ω) ℱ μ := by
  have hpre (f : ℕ → Ω → ℝ) (hf : StronglyAdapted ℱ f) (n : ℕ) :
      StronglyMeasurable[ℱ n] (fun ω => ∑ j ∈ range n, f j ω) := by
    convert (Finset.stronglyMeasurable_sum (range n) (fun j hj =>
        (hf j).mono (ℱ.mono (Nat.le_of_lt (mem_range.mp hj))))) using 1
    ext ω
    simp
  have hint (f : ℕ → Ω → ℝ) (hf : ∀ n, Integrable (f n) μ) (n : ℕ) :
      Integrable (fun ω => ∑ j ∈ range n, f j ω) μ :=
    integrable_finsetSum _ (fun j _ => hf j)
  apply supermartingale_nat
  · intro n; exact ((hZ n).add (hpre d hd n)).sub (hpre c hc n)
  · intro n; exact ((hZi n).add (hint d hdi n)).sub (hint c hci n)
  intro n
  have heqd := condExp_of_stronglyMeasurable (ℱ.le n)
    (predictable_sum_adapted ℱ d hd n) (hint d hdi (n+1))
  have heqc := condExp_of_stronglyMeasurable (ℱ.le n)
    (predictable_sum_adapted ℱ c hc n) (hint c hci (n+1))
  filter_upwards [hstep n,
    condExp_sub ((hZi (n+1)).add (hint d hdi (n+1))) (hint c hci (n+1)) (ℱ n),
    condExp_add (hZi (n+1)) (hint d hdi (n+1)) (ℱ n)] with ω hs hsub hadd
  simp only [Pi.add_def, Pi.sub_def] at hsub hadd
  rw [hsub,hadd,heqd,heqc]
  simp only [sum_range_succ]
  linarith

/-- Conditional additive descent with almost-surely summable errors yields
almost-sure convergence and finite accumulated dissipation. The error may be
signed; its infinite absolute sum need not have finite expectation. -/
theorem additive_descent_converges (ℱ : Filtration ℕ mΩ)
    (Z d c : ℕ → Ω → ℝ)
    (hZ : StronglyAdapted ℱ Z) (hd : StronglyAdapted ℱ d) (hc : StronglyAdapted ℱ c)
    (hZi : ∀ n, Integrable (Z n) μ) (hdi : ∀ n, Integrable (d n) μ)
    (hci : ∀ n, Integrable (c n) μ)
    (hZ0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ Z n ω)
    (hd0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ d n ω)
    (hcSum : ∀ᵐ ω ∂μ, Summable (fun n => c n ω))
    (hstep : ∀ n, μ[Z (n + 1) | ℱ n] ≤ᵐ[μ] fun ω => Z n ω - d n ω + c n ω) :
    ∀ᵐ ω ∂μ, Summable (fun n => d n ω) ∧
      ∃ z, 0 ≤ z ∧ Tendsto (fun n => Z n ω) atTop (𝓝 z) := by
  let M := fun n ω => Z n ω + ∑ j ∈ range n, d j ω - ∑ j ∈ range n, c j ω
  let Q := fun n ω => ∑ j ∈ range n, c j ω
  have hM := additive_descent_supermartingale ℱ Z d c hZ hd hc hZi hdi hci hstep
  have hlim := supermartingale_converges_of_predictable_lower_envelope ℱ M Q hM
    (predictable_sum_adapted ℱ c hc) (fun ω => by simp [Q])
    (by
      filter_upwards [hZ0,hd0] with ω hZω hdω
      intro n
      dsimp [M,Q]
      have hsum : 0 ≤ ∑ j ∈ range n, d j ω := sum_nonneg (fun j _ => hdω j)
      linarith [hZω n])
    (by
      filter_upwards [hcSum] with ω hcω
      exact hcω.hasSum.tendsto_sum_nat.bddAbove_range)
  filter_upwards [hlim,hZ0,hd0,hcSum] with ω hm hZω hdω hcω
  exact convergent_compensated_descent (fun n => Z n ω) (fun n => d n ω)
    (fun n => c n ω) (fun n => M n ω) hZω hdω hcω hm (fun n => rfl)

end Mf.Optimization.StochasticApproximation
