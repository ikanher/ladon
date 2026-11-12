import Mf.Optimization.PoissonClippedSGD.Smoothness
import Mathlib.MeasureTheory.Function.L1Space.Integrable
import Mathlib.MeasureTheory.Function.LpSeminorm.TriangleInequality
import Mathlib.MeasureTheory.Function.LpSeminorm.CompareExp
import Mathlib.MeasureTheory.Function.L2Space
import Mathlib.Tactic

/-!
# Integrability along square-integrable iterates

Global Lipschitz gradients imply linear gradient growth and quadratic objective
growth. These estimates justify the expectations and telescoping in the
finite-horizon convergence argument of `docs/poisson-clipped-sgd/TARGET.md`.
-/

noncomputable section

namespace Mf.Optimization.PoissonClippedSGD

open MeasureTheory

variable {Ω E : Type*} [MeasurableSpace Ω] [NormedAddCommGroup E]
  [InnerProductSpace ℝ E] [CompleteSpace E] [MeasurableSpace E]
  [OpensMeasurableSpace E] [BorelSpace E]

private theorem grad_continuous_of_lipschitz
    (grad : E → E) (L : ℝ) (hL0 : 0 ≤ L)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖) : Continuous grad := by
  let K : NNReal := ⟨L, hL0⟩
  have hLip : LipschitzWith K grad := by
    apply LipschitzWith.of_dist_le_mul
    intro x y
    rw [dist_eq_norm, dist_eq_norm]
    change ‖grad x - grad y‖ ≤ L * ‖x-y‖
    exact hL x y
  exact hLip.continuous

/-- An L2 trajectory has an integrable true gradient norm under globally
Lipschitz gradients. -/
theorem integrable_norm_gradient_comp_of_memLp_two
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    (X : Ω → E) (hXmeas : Measurable X) (hX : MemLp X 2 μ)
    (grad : E → E) (L : ℝ)
    (hL0 : 0 ≤ L)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (x₀ : E) : Integrable (fun ω => ‖grad (X ω)‖) μ := by
  let delta : Ω → E := fun ω => X ω - x₀
  have hdeltaLp : MemLp delta 2 μ := by
    dsimp [delta]
    exact hX.sub (memLp_const x₀)
  have hdeltaInt : Integrable delta μ := hdeltaLp.integrable (by norm_num)
  have hdeltaNorm : Integrable (fun ω => ‖delta ω‖) μ := hdeltaInt.norm
  have hgradMeas : Measurable (fun ω => grad (X ω)) :=
    (grad_continuous_of_lipschitz grad L hL0 hL).measurable.comp hXmeas
  have hgradAEM : AEStronglyMeasurable (fun ω => ‖grad (X ω)‖) μ :=
    (continuous_norm.measurable.comp hgradMeas).aestronglyMeasurable
  have hmajor : Integrable (fun ω => ‖grad x₀‖ + L * ‖delta ω‖) μ := by
    exact (integrable_const ‖grad x₀‖).add (hdeltaNorm.const_mul L)
  apply hmajor.mono' hgradAEM
  filter_upwards with ω
  have hpoint := hL (X ω) x₀
  have htriangle : ‖grad (X ω)‖ ≤ ‖grad x₀‖ + ‖grad (X ω) - grad x₀‖ := by
    calc
      ‖grad (X ω)‖ = ‖grad x₀ + (grad (X ω) - grad x₀)‖ := by congr 1; abel
      _ ≤ _ := norm_add_le _ _
  have hbound : ‖grad (X ω)‖ ≤ ‖grad x₀‖ + L * ‖X ω - x₀‖ := by
    calc
      ‖grad (X ω)‖ ≤ ‖grad x₀‖ + ‖grad (X ω) - grad x₀‖ := htriangle
      _ ≤ ‖grad x₀‖ + L * ‖X ω - x₀‖ := add_le_add le_rfl hpoint
  simpa using hbound

/-- Smooth objectives with Lipschitz gradients are integrable along any
L2 trajectory on a probability space. -/
theorem integrable_objective_comp_of_memLp_two
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    (X : Ω → E) (hXmeas : Measurable X) (hX : MemLp X 2 μ)
    (f : E → ℝ) (grad : E → E) (L : ℝ)
    (hL0 : 0 ≤ L)
    (hf : ∀ x, HasGradientAt f (grad x) x)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (x₀ : E) : Integrable (fun ω => f (X ω)) μ := by
  let delta : Ω → E := fun ω => X ω - x₀
  let r : Ω → ℝ := fun ω => ‖delta ω‖
  have hdeltaLp : MemLp delta 2 μ := by
    dsimp [delta]
    exact hX.sub (memLp_const x₀)
  have hdeltaInt : Integrable delta μ := hdeltaLp.integrable (by norm_num)
  have hdeltaNorm : Integrable r μ := by simpa [r] using hdeltaInt.norm
  have hdeltaSq : Integrable (fun ω => r ω ^ 2) μ := by
    simpa [r, delta] using hdeltaLp.integrable_norm_pow' (p := 2)
  have hfCont : Continuous f := by
    rw [continuous_iff_continuousAt]
    intro z
    exact (hf z).continuousAt
  have hfMeas : Measurable (fun ω => f (X ω)) := hfCont.measurable.comp hXmeas
  have hfAEM : AEStronglyMeasurable (fun ω => f (X ω)) μ := hfMeas.aestronglyMeasurable
  have hmajor : Integrable (fun ω => |f x₀| + ‖grad x₀‖ * r ω +
      (2*L) * r ω ^ 2) μ := by
    have hlin := hdeltaNorm.const_mul ‖grad x₀‖
    have hquad := hdeltaSq.const_mul (2*L)
    exact ((integrable_const |f x₀|).add hlin).add hquad
  apply hmajor.mono' hfAEM
  filter_upwards with ω
  let z := X ω
  let ρ := ‖z-x₀‖
  have hup := smooth_descent_from_gradient_lipschitz f grad L hL0 hf hL x₀ z
  have hback := smooth_descent_from_gradient_lipschitz f grad L hL0 hf hL z x₀
  have hgradbound : ‖grad z‖ ≤ ‖grad x₀‖ + L*ρ := by
    have h := hL z x₀
    have ht : ‖grad z‖ ≤ ‖grad x₀‖ + ‖grad z-grad x₀‖ := by
      calc
        ‖grad z‖ = ‖grad x₀ + (grad z-grad x₀)‖ := by congr 1; abel
        _ ≤ _ := norm_add_le _ _
    have h' : ‖grad x₀‖ + ‖grad z - grad x₀‖ ≤ ‖grad x₀‖ + L * ‖z-x₀‖ :=
      add_le_add le_rfl h
    simpa [ρ] using ht.trans h' 
  have hinner0 : |inner ℝ (grad x₀) (z-x₀)| ≤ ‖grad x₀‖*ρ := by
    simpa [ρ] using abs_real_inner_le_norm (grad x₀) (z-x₀)
  have hinnerz : |inner ℝ (grad z) (z-x₀)| ≤ ‖grad z‖*ρ :=
    abs_real_inner_le_norm (grad z) (z-x₀)
  have hup' : f z ≤ f x₀ + ‖grad x₀‖*ρ + (L/2)*ρ^2 := by
    have := hup
    dsimp [ρ]
    have hi := real_inner_le_norm (grad x₀) (z-x₀)
    nlinarith
  have hlow' : -f z ≤ |f x₀| + ‖grad x₀‖*ρ + (2*L)*ρ^2 := by
    have hinnerBack : |inner ℝ (grad z) (x₀-z)| ≤ ‖grad z‖*ρ := by
      have hh := abs_real_inner_le_norm (grad z) (x₀-z)
      simpa [ρ, norm_sub_rev] using hh
    have hinnerUpper : inner ℝ (grad z) (x₀-z) ≤ ‖grad z‖*ρ :=
      (abs_le.mp hinnerBack).2
    have hback' : -f z ≤ |f x₀| + ‖grad z‖*ρ + (L/2)*ρ^2 := by
      have hq : ‖x₀-z‖^2 = ρ^2 := by simp [ρ, norm_sub_rev]
      rw [hq] at hback
      have hnegf : -f x₀ ≤ |f x₀| := neg_le_abs _
      linarith [hback, hinnerUpper, hnegf]
    have hρ : 0 ≤ ρ := norm_nonneg _
    have hmul := mul_le_mul_of_nonneg_right hgradbound hρ
    nlinarith [hback', hmul, hL0, sq_nonneg ρ]
  have habs : |f z| ≤ |f x₀| + ‖grad x₀‖*ρ + (2*L)*ρ^2 := by
    rw [abs_le]
    constructor
    · linarith [hlow']
    · calc
        f z ≤ f x₀ + ‖grad x₀‖*ρ + (L/2)*ρ^2 := hup'
        _ ≤ |f x₀| + ‖grad x₀‖*ρ + (2*L)*ρ^2 := by
          have hq : (L/2)*ρ^2 ≤ (2*L)*ρ^2 := by
            nlinarith [mul_nonneg hL0 (sq_nonneg ρ)]
          nlinarith [le_abs_self (f x₀), hq]
  simpa [z, r, delta, ρ] using habs


/-- The squared true gradient norm is integrable along an L2 trajectory. -/
theorem integrable_sq_norm_gradient_comp_of_memLp_two
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    (X : Ω → E) (hXmeas : Measurable X) (hX : MemLp X 2 μ)
    (grad : E → E) (L : ℝ) (hL0 : 0 ≤ L)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (x₀ : E) : Integrable (fun ω => ‖grad (X ω)‖ ^ 2) μ := by
  let delta : Ω → E := fun ω => X ω - x₀
  let r : Ω → ℝ := fun ω => ‖delta ω‖
  have hdeltaLp : MemLp delta 2 μ := by
    dsimp [delta]
    exact hX.sub (memLp_const x₀)
  have hdeltaInt : Integrable delta μ := hdeltaLp.integrable (by norm_num)
  have hdeltaNorm : Integrable r μ := by simpa [r] using hdeltaInt.norm
  have hdeltaSq : Integrable (fun ω => r ω ^ 2) μ := by
    simpa [r, delta] using hdeltaLp.integrable_norm_pow' (p := 2)
  have hgradMeas : Measurable (fun ω => grad (X ω)) :=
    (grad_continuous_of_lipschitz grad L hL0 hL).measurable.comp hXmeas
  have hsqAEM : AEStronglyMeasurable (fun ω => ‖grad (X ω)‖ ^ 2) μ := by
    exact ((continuous_norm.measurable.comp hgradMeas).pow_const 2).aestronglyMeasurable
  have hmajor : Integrable (fun ω => 2*‖grad x₀‖^2 + (2*L^2)*r ω^2) μ := by
    exact (integrable_const (2*‖grad x₀‖^2)).add (hdeltaSq.const_mul (2*L^2))
  apply hmajor.mono' hsqAEM
  filter_upwards with ω
  let ρ : ℝ := ‖X ω - x₀‖
  have hgrad : ‖grad (X ω)‖ ≤ ‖grad x₀‖ + L*ρ := by
    have htri : ‖grad (X ω)‖ ≤ ‖grad x₀‖ + ‖grad (X ω)-grad x₀‖ := by
      calc
        ‖grad (X ω)‖ = ‖grad x₀ + (grad (X ω)-grad x₀)‖ := by congr 1; abel
        _ ≤ _ := norm_add_le _ _
    have hLip := hL (X ω) x₀
    calc
      ‖grad (X ω)‖ ≤ ‖grad x₀‖ + ‖grad (X ω)-grad x₀‖ := htri
      _ ≤ ‖grad x₀‖ + L*‖X ω-x₀‖ := add_le_add le_rfl hLip
      _ = ‖grad x₀‖ + L*ρ := by simp [ρ]
  have hρ : 0 ≤ ρ := norm_nonneg _
  have hbase : 0 ≤ ‖grad x₀‖ + L*ρ := add_nonneg (norm_nonneg _) (mul_nonneg hL0 hρ)
  have hsq : (‖grad x₀‖ + L*ρ)^2 ≤ 2*‖grad x₀‖^2 + 2*L^2*ρ^2 := by
    nlinarith [sq_nonneg (‖grad x₀‖ - L*ρ)]
  have hmon : ‖grad (X ω)‖^2 ≤ (‖grad x₀‖ + L*ρ)^2 :=
    (sq_le_sq₀ (norm_nonneg _) hbase).2 hgrad
  dsimp [r, delta]
  simpa [ρ, mul_pow, mul_assoc, mul_left_comm, mul_comm] using hmon.trans hsq

/-- The clipped progress `min(‖∇f‖²,c‖∇f‖)` is integrable along an L2
trajectory. -/
theorem integrable_clipped_progress_comp_of_memLp_two
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    (X : Ω → E) (hXmeas : Measurable X) (hX : MemLp X 2 μ)
    (grad : E → E) (L c : ℝ) (hL0 : 0 ≤ L) (hc : 0 ≤ c)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖) :
    Integrable (fun ω => min (‖grad (X ω)‖^2) (c * ‖grad (X ω)‖)) μ := by
  have hgrad := integrable_norm_gradient_comp_of_memLp_two
    X hXmeas hX grad L hL0 hL 0
  -- Use the Lipschitz growth lemma directly; `f` is irrelevant to this endpoint.
  let g : Ω → ℝ := fun ω => ‖grad (X ω)‖
  have hgMeas : Measurable g :=
    (continuous_norm.measurable.comp
      ((grad_continuous_of_lipschitz grad L hL0 hL).measurable.comp hXmeas))
  have hprogMeas : Measurable (fun ω => min (g ω ^ 2) (c*g ω)) :=
    (hgMeas.pow_const 2).min (hgMeas.const_mul c)
  have hmajor : Integrable (fun ω => c*g ω) μ := hgrad.const_mul c
  apply hmajor.mono' hprogMeas.aestronglyMeasurable
  filter_upwards with ω
  have hg0 : 0 ≤ g ω := norm_nonneg _
  have hleft0 : 0 ≤ g ω ^ 2 := sq_nonneg _
  have hright0 : 0 ≤ c*g ω := mul_nonneg hc hg0
  have hp0 : 0 ≤ min (g ω ^ 2) (c*g ω) := le_min hleft0 hright0
  simpa [g, Real.norm_eq_abs, abs_of_nonneg hp0] using min_le_right (g ω ^ 2) (c*g ω)

end Mf.Optimization.PoissonClippedSGD
