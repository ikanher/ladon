import Mathlib.Analysis.Calculus.Gradient.Basic
import Mathlib.Analysis.Calculus.Deriv.MeanValue
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Analysis.Calculus.Deriv.Pow

/-!
# Descent from a Lipschitz gradient

Global gradient Lipschitz continuity gives the quadratic upper estimate used
in Appendix A of `docs/poisson-clipped-sgd/TARGET.md`. The proof differentiates
a corrected line segment; the descent estimate is derived, not assumed.
-/

noncomputable section

namespace Mf.Optimization.PoissonClippedSGD

open InnerProductSpace

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]

def descentPath (x h : E) (t : ℝ) : E := t • h + x

theorem smooth_descent_from_gradient_lipschitz
    (f : E → ℝ) (grad : E → E) (L : ℝ)
    (_hL0 : 0 ≤ L)
    (hf : ∀ x, HasGradientAt f (grad x) x)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (x y : E) :
    f y ≤ f x + inner ℝ (grad x) (y-x) + (L/2) * ‖y-x‖^2 := by
  let h : E := y-x
  let phi : ℝ → ℝ :=
    (f ∘ descentPath x h - (fun t : ℝ => t * inner ℝ (grad x) h)) -
      (fun t : ℝ => ((L / 2) * ‖h‖ ^ 2) * t ^ 2)
  have hpath : ∀ t, HasDerivAt (descentPath x h) h t := by
    intro t
    have hp := (hasDerivAt_id t).smul_const h
    have hp' : HasDerivAt (fun s : ℝ => s • h + x) h t := by
      simpa only [id_eq, one_smul] using hp.add_const x
    change HasDerivAt (fun s : ℝ => s • h + x) h t
    exact hp' 
  have hderiv : ∀ t, HasDerivAt phi
      (inner ℝ (grad (descentPath x h t) - grad x) h -
        ((L / 2) * ‖h‖ ^ 2) * (2 * t)) t := by
    intro t
    have hcomp : HasDerivAt (f ∘ descentPath x h)
        (((InnerProductSpace.toDual ℝ E) (grad (descentPath x h t))) h) t := by
      exact (hf (descentPath x h t)).hasFDerivAt.comp_hasDerivAt t (hpath t)
    have hinner : ((InnerProductSpace.toDual ℝ E) (grad (descentPath x h t))) h =
        inner ℝ (grad (descentPath x h t)) h := by
      simp [InnerProductSpace.toDual, InnerProductSpace.toDualMap, innerSL_apply_apply]
    have hlinear : HasDerivAt (fun s : ℝ => s * inner ℝ (grad x) h)
        (inner ℝ (grad x) h) t := by
      simpa using (hasDerivAt_id t).mul_const (inner ℝ (grad x) h)
    have hquad : HasDerivAt
        (fun s : ℝ => ((L / 2) * ‖h‖ ^ 2) * s ^ 2)
        (((L / 2) * ‖h‖ ^ 2) * (2*t)) t := by
      have hp' : HasDerivAt (fun s : ℝ => s ^ 2) (2*t) t := by
        simpa using hasDerivAt_pow 2 t
      exact hp'.const_mul ((L / 2) * ‖h‖ ^ 2)
    have hsub := hcomp.sub hlinear
    have hsub' := hsub.sub hquad
    simpa [phi, hinner, inner_sub_left] using hsub'
  have hcont : ContinuousOn phi (Set.Icc (0:ℝ) 1) := by
    apply continuousOn_of_forall_continuousAt
    intro t ht
    exact (hderiv t).continuousAt
  have hderiv_nonpos : ∀ t ∈ interior (Set.Icc (0:ℝ) 1),
      (inner ℝ (grad (descentPath x h t) - grad x) h -
        ((L / 2) * ‖h‖ ^ 2) * (2*t)) ≤ 0 := by
    intro t ht
    rw [interior_Icc] at ht
    have ht0 : 0 ≤ t := ht.1.le
    have hnorm : ‖descentPath x h t - x‖ = t * ‖h‖ := by
      simp [descentPath, norm_smul, abs_of_nonneg ht0]
    have hgrad := hL (descentPath x h t) x
    have hinnerBound := real_inner_le_norm (grad (descentPath x h t) - grad x) h
    have hprod : ‖grad (descentPath x h t) - grad x‖ * ‖h‖ ≤
        L * t * ‖h‖ ^ 2 := by
      rw [hnorm] at hgrad
      have hmul := mul_le_mul_of_nonneg_right hgrad (norm_nonneg h)
      calc
        _ ≤ L * (t * ‖h‖) * ‖h‖ := hmul
        _ = L * t * ‖h‖ ^ 2 := by ring
    have hcoeff : ((L / 2) * ‖h‖ ^ 2) * (2*t) = L * t * ‖h‖ ^ 2 := by ring
    linarith [hinnerBound, hprod, hcoeff]
  have hanti := antitoneOn_of_hasDerivWithinAt_nonpos (convex_Icc (0:ℝ) 1)
    hcont (fun t ht => (hderiv t).hasDerivWithinAt) hderiv_nonpos
  have h01 := hanti (show (0:ℝ) ∈ Set.Icc 0 1 by simp)
    (show (1:ℝ) ∈ Set.Icc 0 1 by simp) (by norm_num)
  have hphi : phi 1 ≤ phi 0 := h01
  dsimp [phi, descentPath, h] at hphi
  have hy : (1:ℝ) • (y-x) + x = y := by module
  rw [hy] at hphi
  simp at hphi
  linarith [hphi]

end Mf.Optimization.PoissonClippedSGD
