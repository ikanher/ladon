import Mf.Optimization.PoissonClippedSGD.Alignment
import Mf.Optimization.PoissonClippedSGD.Smoothness
import Mathlib.MeasureTheory.Function.L2Space

open MeasureTheory

/-!
# Expected descent with clipping and Poisson sampling

The smoothness estimate is integrated using explicit direction moments.
Clipping alignment retains the mean-square term until the stepsize condition
makes its coefficient nonpositive. Moment and integrability premises here are
intermediate interfaces, discharged by the concrete Gaussian step adapter.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD

variable {E Ω : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [CompleteSpace E] [MeasurableSpace Ω]

theorem expected_smooth_descent
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (f : E → ℝ) (grad : E → E) (L eta : ℝ) (hL0 : 0 ≤ L)
    (hf : ∀ x, HasGradientAt (fun y : E => f y) (grad x) x)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (x : E) (Y : Ω → E) (hY : MemLp Y 2 μ)
    (hnext : Integrable (fun w => f (x - eta • Y w)) μ)
    (m : E) (hm : (∫ w, Y w ∂μ) = m)
    (energy : ℝ) (henergy : (∫ w, ‖Y w‖ ^ 2 ∂μ) = energy) :
    (∫ w, f (x - eta • Y w) ∂μ) ≤
      f x - eta * inner ℝ (grad x) m + (L * eta ^ 2 / 2) * energy := by
  have hY1 : Integrable Y μ :=
    memLp_one_iff_integrable.mp (hY.mono_exponent (by norm_num))
  have hY2 : Integrable (fun w => ‖Y w‖ ^ 2) μ :=
    (memLp_two_iff_integrable_sq_norm hY.aestronglyMeasurable).mp hY
  have hinner : Integrable (fun w => inner ℝ (grad x) (Y w)) μ := by
    have hh : Integrable (fun w => inner ℝ (Y w) (grad x)) μ := hY1.inner_const (grad x)
    exact hh.congr (Filter.Eventually.of_forall fun w => (real_inner_comm (Y w) (grad x)).symm)
  have hlin : (∫ w, inner ℝ (grad x) (Y w) ∂μ) = inner ℝ (grad x) m := by
    let ℓ : E →L[ℝ] ℝ := InnerProductSpace.toDual ℝ E (grad x)
    have hc := ContinuousLinearMap.integral_comp_comm ℓ hY1
    rw [hm] at hc
    simpa [ℓ, InnerProductSpace.toDual, InnerProductSpace.toDualMap,
      innerSL_apply_apply] using hc
  have hbound (w : Ω) : f (x - eta • Y w) ≤
      f x - eta * inner ℝ (grad x) (Y w) + (L * eta ^ 2 / 2) * ‖Y w‖ ^ 2 := by
    have hs := smooth_descent_from_gradient_lipschitz
      (fun y : E => f y) grad L hL0 hf hL x (x - eta • Y w)
    have hdiff : (x - eta • Y w) - x = -eta • Y w := by module
    rw [hdiff] at hs
    have hs' : f (x - eta • Y w) ≤ f x - eta * inner ℝ (grad x) (Y w) +
        (L / 2) * (|eta| * ‖Y w‖) ^ 2 := by
      have hs0 := hs
      simp only [inner_smul_right, norm_smul, Real.norm_eq_abs, abs_neg] at hs0
      nlinarith [hs0]
    calc
      _ ≤ f x - eta * inner ℝ (grad x) (Y w) +
          (L / 2) * (|eta| * ‖Y w‖) ^ 2 := hs'
      _ = f x - eta * inner ℝ (grad x) (Y w) +
          (L * eta ^ 2 / 2) * ‖Y w‖ ^ 2 := by rw [mul_pow, sq_abs]; ring
  have hrhs : Integrable
      (fun w => f x - eta * inner ℝ (grad x) (Y w) +
        (L * eta ^ 2 / 2) * ‖Y w‖ ^ 2) μ := by
    exact (integrable_const _).sub (hinner.const_mul _)|>.add (hY2.const_mul _)
  have hint := integral_mono_ae hnext hrhs (Filter.Eventually.of_forall hbound)
  have hparts : (∫ w, f x - eta * inner ℝ (grad x) (Y w) +
      (L * eta ^ 2 / 2) * ‖Y w‖ ^ 2 ∂μ) =
      f x - eta * inner ℝ (grad x) m + (L * eta ^ 2 / 2) * energy := by
    calc
      _ = (∫ w, f x - eta * inner ℝ (grad x) (Y w) ∂μ) +
          ∫ w, (L * eta ^ 2 / 2) * ‖Y w‖ ^ 2 ∂μ := by
            exact integral_add (integrable_const _ |>.sub (hinner.const_mul _))
              (hY2.const_mul _)
      _ = (f x - eta * inner ℝ (grad x) m) + (L * eta ^ 2 / 2) * energy := by
            rw [integral_sub (integrable_const _) (hinner.const_mul _)]
            rw [integral_const]
            have hμ : μ.real Set.univ = 1 := by simp
            rw [hμ, one_smul]
            rw [integral_const_mul, hlin]
            have he : (∫ w, (L * eta ^ 2 / 2) * ‖Y w‖ ^ 2 ∂μ) =
                (L * eta ^ 2 / 2) * energy := by
              rw [integral_const_mul, henergy]
            rw [he]
  rw [hparts] at hint
  exact hint


/-- Alignment absorbs the mean-square term in Poisson second moments and leaves
only the finite-population variance and independent additive noise energy. -/
theorem expected_aligned_step_bound
    {d n : ℕ} (hn : 0 < n)
    (μlaw : Measure Ω) [IsProbabilityMeasure μlaw]
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (grad : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (L eta : ℝ) (hL0 : 0 ≤ L) (hf : ∀ x, HasGradientAt f (grad x) x)
    (hL : ∀ x y, ‖grad x - grad y‖ ≤ L * ‖x-y‖)
    (x : EuclideanSpace ℝ (Fin d))
    (Y : Ω → EuclideanSpace ℝ (Fin d))
    (hY : MemLp Y 2 μlaw)
    (hnext : Integrable (fun w => f (x - eta • Y w)) μlaw)
    (g : Fin n → EuclideanSpace ℝ (Fin d)) (hgradx : grad x = vectorMean g)
    (sigma c q : ℝ)
    (hsigma : 0 ≤ sigma) (hc : 0 < c) (hclip : 4 * sigma ≤ c)
    (hvariance : meanSqDeviation g (vectorMean g) ≤ sigma ^ 2)
    (hq0 : 0 < q) (hq1 : q ≤ 1)
    (kappa : ℝ) (hkappa : kappa = (1-q)/(q*(n:ℝ)))
    (heta : 0 ≤ eta) (hstep : eta * L * (1+kappa) ≤ 1)
    (s2 : ℝ) (hs2 : 0 ≤ s2)
    (hmean : (∫ w, Y w ∂μlaw) = clippedMean c g)
    (henergy : (∫ w, ‖Y w‖ ^ 2 ∂μlaw) =
      (1+kappa) * ‖clippedMean c g‖ ^ 2 +
        kappa * meanSqDeviation (fun i => Mf.DP.euclideanBallClip c (g i))
          (clippedMean c g) + s2) :
    (∫ w, f (x - eta • Y w) ∂μlaw) ≤
      f x - eta/4 * clippedProgress c ‖grad x‖ +
        2*eta*sigma^4/c^2 + L*eta^2/2*(kappa*sigma^2+s2) := by
  have hqN : 0 ≤ kappa := by
    rw [hkappa]
    positivity
  have halign := clippedMean_alignment hn g c sigma hc hsigma hclip hvariance
  have hdes := expected_smooth_descent μlaw f grad L eta hL0 hf hL x Y hY hnext
    (clippedMean c g) hmean
    ((1+kappa) * ‖clippedMean c g‖ ^ 2 +
      kappa * meanSqDeviation (fun i => Mf.DP.euclideanBallClip c (g i))
        (clippedMean c g) + s2) henergy
  have hV : meanSqDeviation (fun i => Mf.DP.euclideanBallClip c (g i))
      (clippedMean c g) ≤ sigma ^ 2 :=
    (clippedMean_variance_le hn c hc.le g).trans hvariance
  have hcoef : 0 ≤ 1 - eta * L * (1+kappa) := by linarith
  have hmu : 0 ≤ ‖clippedMean c g‖ ^ 2 := sq_nonneg _
  rw [hgradx] at hdes ⊢
  unfold clippedProgress
  have halignEta := mul_le_mul_of_nonneg_left halign heta
  have hvarscale : 0 ≤ L * eta ^ 2 / 2 * kappa := by positivity
  have hvarTerm := mul_le_mul_of_nonneg_left hV hvarscale
  have hmuTerm : (L * eta ^ 2 / 2) * (1+kappa) *
      ‖clippedMean c g‖ ^ 2 ≤ eta / 2 * ‖clippedMean c g‖ ^ 2 := by
    have hstep' := mul_le_mul_of_nonneg_right hstep (by positivity : 0 ≤ eta / 2 * ‖clippedMean c g‖ ^ 2)
    nlinarith
  ring_nf at hdes halignEta hvarTerm hmuTerm ⊢
  linarith [hdes, halignEta, hvarTerm, hmuTerm]

end Mf.Optimization.PoissonClippedSGD
