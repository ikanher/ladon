import Mf.Optimization.StochasticApproximation.AdditiveDescent
import Mathlib.Analysis.SpecialFunctions.Log.Summable
import Mathlib.MeasureTheory.Function.ConditionalExpectation.PullOut

/-!
# Random-error almost-supermartingale convergence

Robbins and Siegmund, *A convergence theorem for non negative almost
supermartingales and some applications* (1971), connects conditional descent
to almost-sure convergence. The inspected modern proof is Neri and Powell,
*A quantitative Robbins–Siegmund theorem*, arXiv:2410.15986v2, proof `res:RS`.
Original-source access remains an explicit historical gap in the H04 contract.

The normalization divides by a predictable product before taking conditional
expectations. It requires no integrability of the multiplicative error times
the state, and no integrability of the infinite error totals. The positive part
in the product only controls null-set representatives: it equals the original
product on the simultaneous nonnegative-error event. The final theorem allows
signed summable additive errors and recovers the original state and descent.
-/

open MeasureTheory Filter Finset Set
open scoped Topology
namespace Mf.Optimization.StochasticApproximation
variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω} [IsProbabilityMeasure μ]

/-- Predictable inflation product, made positive even on null-set representatives. -/
def inflationProduct (A : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  ∏ j ∈ range n, (1 + max (A j ω) 0)

/-- Every finite inflation product is at least one, so its inverse is bounded. -/
theorem inflationProduct_one_le (A : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) :
    1 ≤ inflationProduct A n ω := by
  apply Finset.one_le_prod
  intro j hj
  linarith [le_max_right (A j ω) 0]

/-- The next product contains exactly the current inflation factor. -/
theorem inflationProduct_succ (A : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) :
    inflationProduct A (n + 1) ω = inflationProduct A n ω * (1 + max (A n ω) 0) := by
  simp [inflationProduct,prod_range_succ]

/-- The product through the current adapted error is measurable before the next state. -/
theorem inflationProduct_predictable (ℱ : Filtration ℕ mΩ) (A : ℕ → Ω → ℝ)
    (hA : StronglyAdapted ℱ A) : StronglyAdapted ℱ (fun n => inflationProduct A (n + 1)) := by
  intro n
  unfold inflationProduct
  have hfactor (j : ℕ) (hj : j ∈ range (n + 1)) :
      StronglyMeasurable[ℱ n] (fun ω => 1 + max (A j ω) 0) := by
    have hm := (hA j).mono (ℱ.mono (Nat.le_of_lt_succ (mem_range.mp hj)))
    exact (measurable_const.add (hm.measurable.max measurable_const)).stronglyMeasurable
  convert (Finset.stronglyMeasurable_prod (range (n + 1)) hfactor) using 1
  ext ω
  simp

/-- Nonnegative summable inflation errors give a finite product limit at least one. -/
theorem inflationProduct_converges (A : ℕ → ℝ) (hA0 : ∀ n, 0 ≤ A n)
    (hA : Summable A) : ∃ p, 1 ≤ p ∧
      Tendsto (fun n => ∏ j ∈ range n, (1 + max (A j) 0)) atTop (𝓝 p) := by
  have heq : (fun n => ∏ j ∈ range n, (1 + max (A j) 0)) =
      (fun n => ∏ j ∈ range n, (1 + A j)) := by
    funext n; apply prod_congr rfl; intro j hj; rw [max_eq_left (hA0 j)]
  rw [heq]
  have ht := (Real.multipliable_one_add_of_summable hA).hasProd.tendsto_prod_nat
  refine ⟨_, ?_,ht⟩
  apply ge_of_tendsto' ht
  intro n
  exact Finset.one_le_prod (fun j hj => by linarith [hA0 j])

omit [IsProbabilityMeasure μ] in
/-- Division by a measurable denominator at least one preserves integrability. -/
theorem integrable_div_ge_one (f P : Ω → ℝ) (hf : Integrable f μ)
    (hP : AEStronglyMeasurable P μ) (hP1 : ∀ ω, 1 ≤ P ω) :
    Integrable (fun ω => f ω / P ω) μ := by
  apply hf.mono ((hf.aemeasurable.div hP.aemeasurable).aestronglyMeasurable)
  filter_upwards [] with ω
  change ‖f ω / P ω‖ ≤ ‖f ω‖
  rw [norm_div,Real.norm_eq_abs (P ω),abs_of_nonneg (by linarith [hP1 ω])]
  exact div_le_self (norm_nonneg _) (hP1 ω)

omit [IsProbabilityMeasure μ] in
/-- Pull out the bounded inverse product and normalize the original conditional row.
The product of the inflation error and the state is never separately integrated. -/
theorem normalized_conditional_descent (ℱ : Filtration ℕ mΩ)
    (X A B C P : ℕ → Ω → ℝ)
    (hX : ∀ n, Integrable (X n) μ)
    (hP : StronglyAdapted ℱ (fun n => P (n + 1)))
    (hP1 : ∀ n ω, 1 ≤ P n ω)
    (hrec : ∀ n, ∀ᵐ ω ∂μ, P (n + 1) ω = P n ω * (1 + A n ω))
    (hstep : ∀ n, μ[X (n + 1) | ℱ n] ≤ᵐ[μ]
      fun ω => (1 + A n ω) * X n ω - B n ω + C n ω) :
    ∀ n, μ[(fun ω => X (n + 1) ω / P (n + 1) ω) | ℱ n] ≤ᵐ[μ]
      fun ω => X n ω / P n ω - B n ω / P (n + 1) ω + C n ω / P (n + 1) ω := by
  intro n
  have hPi : AEStronglyMeasurable (P (n + 1)) μ :=
    ((hP n).mono (ℱ.le n)).aestronglyMeasurable
  have hint := integrable_div_ge_one (X (n + 1)) (P (n + 1)) (hX (n + 1)) hPi (hP1 (n + 1))
  have hinv : StronglyMeasurable[ℱ n] (fun ω => (P (n + 1) ω)⁻¹) :=
    (hP n).measurable.inv.stronglyMeasurable
  have hmul : Integrable ((fun ω => (P (n + 1) ω)⁻¹) * X (n + 1)) μ := by
    simpa only [Pi.mul_def, div_eq_mul_inv, mul_comm] using hint
  have hpull := condExp_mul_of_stronglyMeasurable_left hinv hmul (hX (n + 1))
  have hpull' : μ[(fun ω => X (n + 1) ω / P (n + 1) ω) | ℱ n] =ᵐ[μ]
      fun ω => μ[X (n + 1) | ℱ n] ω / P (n + 1) ω := by
    simpa only [Pi.mul_def,div_eq_mul_inv,mul_comm] using hpull
  filter_upwards [hpull',hrec n,hstep n] with ω heq hr hs
  rw [heq]
  have hp0 : 0 < P n ω := lt_of_lt_of_le zero_lt_one (hP1 n ω)
  have hp1 : 0 < P (n + 1) ω := lt_of_lt_of_le zero_lt_one (hP1 (n + 1) ω)
  calc
    _ ≤ ((1 + A n ω) * X n ω - B n ω + C n ω) / P (n + 1) ω :=
      div_le_div_of_nonneg_right hs hp1.le
    _ = _ := by
      field_simp [hp0.ne',hp1.ne']
      rw [hr]
      ring

/-- The entering inflation product is adapted, including its constant initial value. -/
theorem inflationProduct_adapted (ℱ : Filtration ℕ mΩ) (A : ℕ → Ω → ℝ)
    (hA : StronglyAdapted ℱ A) : StronglyAdapted ℱ (inflationProduct A) := by
  intro n
  cases n with
  | zero =>
      have heq : inflationProduct A 0 = fun _ => 1 := by funext ω; simp [inflationProduct]
      rw [heq]
      exact stronglyMeasurable_const
  | succ n => exact (inflationProduct_predictable ℱ A hA n).mono (ℱ.mono (Nat.le_succ n))

/-- Finite normalized descent retains the actual terminal expectation and needs
no expectation of the infinite perturbation sums. -/
theorem almost_supermartingale_finite (ℱ : Filtration ℕ mΩ)
    (X A B C : ℕ → Ω → ℝ)
    (hA : StronglyAdapted ℱ A)
    (hXi : ∀ n, Integrable (X n) μ) (hBi : ∀ n, Integrable (B n) μ)
    (hCi : ∀ n, Integrable (C n) μ)
    (hA0 : ∀ᵐ ω ∂μ, ∀ n, 0 ≤ A n ω)
    (hstep : ∀ n, μ[X (n + 1) | ℱ n] ≤ᵐ[μ]
      fun ω => (1 + A n ω) * X n ω - B n ω + C n ω) (N : ℕ) :
    (∫ ω, X N ω / inflationProduct A N ω ∂μ) +
      ∑ n ∈ range N, (∫ ω, B n ω / inflationProduct A (n + 1) ω ∂μ) ≤
    (∫ ω, X 0 ω ∂μ) +
      ∑ n ∈ range N, (∫ ω, C n ω / inflationProduct A (n + 1) ω ∂μ) := by
  have hPa := inflationProduct_adapted ℱ A hA
  have hPp := inflationProduct_predictable ℱ A hA
  have hP1 := inflationProduct_one_le A
  have hrec (n : ℕ) : ∀ᵐ ω ∂μ,
      inflationProduct A (n + 1) ω = inflationProduct A n ω * (1 + A n ω) := by
    filter_upwards [hA0] with ω hω
    simpa [max_eq_left (hω n)] using inflationProduct_succ A n ω
  have hnorm := normalized_conditional_descent ℱ X A B C (inflationProduct A)
    hXi hPp hP1 hrec hstep
  have htel := conditional_descent_finite ℱ
    (fun n ω => X n ω / inflationProduct A n ω)
    (fun n ω => B n ω / inflationProduct A (n + 1) ω)
    (fun n ω => C n ω / inflationProduct A (n + 1) ω)
    (fun n => integrable_div_ge_one _ _ (hXi n)
      ((hPa n).mono (ℱ.le n)).aestronglyMeasurable (hP1 n))
    (fun n => integrable_div_ge_one _ _ (hBi n)
      ((hPp n).mono (ℱ.le n)).aestronglyMeasurable (hP1 (n + 1)))
    (fun n => integrable_div_ge_one _ _ (hCi n)
      ((hPp n).mono (ℱ.le n)).aestronglyMeasurable (hP1 (n + 1))) hnorm N
  have heq : inflationProduct A 0 = fun _ => 1 := by funext ω; simp [inflationProduct]
  simpa only [heq,div_one] using htel

/-- Almost-surely summable multiplicative and additive errors in conditional descent
give finite nonnegative state convergence and summable dissipation almost surely.
No integrability of inflation errors or infinite error totals is assumed. -/
theorem almost_supermartingale_converges (ℱ : Filtration ℕ mΩ)
    (X A B C : ℕ → Ω → ℝ)
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
    ∀ᵐ ω ∂μ, Summable (fun n => B n ω) ∧
      ∃ x, 0 ≤ x ∧ Tendsto (fun n => X n ω) atTop (𝓝 x) := by
  let P := inflationProduct A
  let Z := fun n ω => X n ω / P n ω
  let d := fun n ω => B n ω / P (n + 1) ω
  let c := fun n ω => C n ω / P (n + 1) ω
  have hPa := inflationProduct_adapted ℱ A hA
  have hPp := inflationProduct_predictable ℱ A hA
  have hP1 := inflationProduct_one_le A
  have hPpos (n : ℕ) (ω : Ω) : 0 < P n ω := lt_of_lt_of_le zero_lt_one (hP1 n ω)
  have hZa : StronglyAdapted ℱ Z := fun n =>
    ((hX n).measurable.div (hPa n).measurable).stronglyMeasurable
  have hda : StronglyAdapted ℱ d := fun n =>
    ((hB n).measurable.div (hPp n).measurable).stronglyMeasurable
  have hca : StronglyAdapted ℱ c := fun n =>
    ((hC n).measurable.div (hPp n).measurable).stronglyMeasurable
  have hZi (n : ℕ) : Integrable (Z n) μ := integrable_div_ge_one _ _ (hXi n)
    ((hPa n).mono (ℱ.le n)).aestronglyMeasurable (hP1 n)
  have hdi (n : ℕ) : Integrable (d n) μ := integrable_div_ge_one _ _ (hBi n)
    ((hPp n).mono (ℱ.le n)).aestronglyMeasurable (hP1 (n + 1))
  have hci (n : ℕ) : Integrable (c n) μ := integrable_div_ge_one _ _ (hCi n)
    ((hPp n).mono (ℱ.le n)).aestronglyMeasurable (hP1 (n + 1))
  have hrec (n : ℕ) : ∀ᵐ ω ∂μ, P (n + 1) ω = P n ω * (1 + A n ω) := by
    filter_upwards [hA0] with ω hω
    simpa [P,max_eq_left (hω n)] using inflationProduct_succ A n ω
  have hnormal := normalized_conditional_descent ℱ X A B C P hXi hPp hP1 hrec hstep
  have hlim := additive_descent_converges ℱ Z d c hZa hda hca hZi hdi hci
    (by filter_upwards [hX0] with ω hω; exact fun n => div_nonneg (hω n) (hPpos n ω).le)
    (by filter_upwards [hB0] with ω hω; exact fun n => div_nonneg (hω n) (hPpos (n + 1) ω).le)
    (by
      filter_upwards [hCs] with ω hω
      apply hω.norm.of_norm_bounded
      intro n
      dsimp [c]
      rw [abs_div,abs_of_pos (hPpos (n + 1) ω)]
      exact div_le_self (abs_nonneg _) (hP1 (n + 1) ω)) hnormal
  filter_upwards [hlim,hAs,hA0,hB0] with ω ⟨hds,z,hz0,hz⟩ hAsω hAω hBω
  obtain ⟨p,hp1,hp⟩ := inflationProduct_converges (fun n => A n ω) hAω hAsω
  have hp' : Tendsto (fun n => P n ω) atTop (𝓝 p) := hp
  obtain ⟨R,hR⟩ := hp'.bddAbove_range
  have hBs : Summable (fun n => B n ω) := by
    apply Summable.of_nonneg_of_le hBω _ (hds.mul_left R)
    intro n
    have hd0 : 0 ≤ d n ω := div_nonneg (hBω n) (hPpos (n + 1) ω).le
    calc
      B n ω = P (n + 1) ω * d n ω := by dsimp [d]; field_simp [(hPpos (n + 1) ω).ne']
      _ ≤ R * d n ω := mul_le_mul_of_nonneg_right (hR (mem_range_self (n + 1))) hd0
  have hrecover : (fun n => P n ω * Z n ω) = (fun n => X n ω) := by
    funext n
    dsimp [Z]
    field_simp [(hPpos n ω).ne']
  refine ⟨hBs,p*z,mul_nonneg (by linarith) hz0,?_⟩
  simpa only [hrecover] using hp'.mul hz

end Mf.Optimization.StochasticApproximation
