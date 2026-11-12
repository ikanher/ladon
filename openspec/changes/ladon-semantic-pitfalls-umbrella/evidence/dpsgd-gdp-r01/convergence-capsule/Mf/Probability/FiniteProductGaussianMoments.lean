import Mf.Probability.FiniteProductGaussian
import Mathlib.Analysis.Calculus.Deriv.Polynomial
import Mathlib.Probability.Independence.Integration
import Mathlib.Probability.Moments.Covariance
import Mathlib.Probability.Moments.MGFAnalytic

/-!
# Finite product Gaussian coordinate moments

This neutral owner contains coordinate projection, integrability, and
independence facts for `FiniteProductGaussian.law`. It deliberately has no
optimizer, privacy, SDE, or adaptive-method imports.
-/

namespace Mf
namespace Probability
namespace FiniteProductGaussianMoments

open MeasureTheory ProbabilityTheory Polynomial

noncomputable section

variable {ι : Type*} [Fintype ι]

/-! ## Scalar Gaussian moments -/

/-- Quadratic exponent in the real Gaussian MGF. -/
def gaussianMGFExponent (mean variance : ℝ) : ℝ[X] :=
  C mean * X + C (variance / 2) * X ^ 2

@[simp] theorem gaussianMGFExponent_eval (mean variance t : ℝ) :
    (gaussianMGFExponent mean variance).eval t =
      mean * t + variance * t ^ 2 / 2 := by
  simp [gaussianMGFExponent]
  ring

/-- Polynomial multiplier of the `n`th Gaussian-MGF derivative. -/
def gaussianMGFDerivativePolynomial (mean variance : ℝ) : ℕ → ℝ[X]
  | 0 => 1
  | n + 1 =>
      (gaussianMGFDerivativePolynomial mean variance n).derivative +
        gaussianMGFDerivativePolynomial mean variance n *
          (C mean + C variance * X)

theorem hasDerivAt_gaussianMGFExponent (mean variance t : ℝ) :
    HasDerivAt (fun s => (gaussianMGFExponent mean variance).eval s)
      (mean + variance * t) t := by
  convert (gaussianMGFExponent mean variance).hasDerivAt t using 1
  · with_unfolding_all rfl
  · simp [gaussianMGFExponent]
    ring

theorem hasDerivAt_exp_gaussianMGFExponent (mean variance t : ℝ) :
    HasDerivAt
      (fun s => Real.exp ((gaussianMGFExponent mean variance).eval s))
      (Real.exp ((gaussianMGFExponent mean variance).eval t) *
        (mean + variance * t)) t := by
  simpa [mul_comm] using
    (hasDerivAt_gaussianMGFExponent mean variance t).exp

/-- All iterated MGF derivatives are a polynomial multiplier times the MGF. -/
theorem iteratedDeriv_exp_gaussianMGFExponent
    (mean variance : ℝ) (n : ℕ) :
    iteratedDeriv n
        (fun t => Real.exp ((gaussianMGFExponent mean variance).eval t)) =
      fun t =>
        (gaussianMGFDerivativePolynomial mean variance n).eval t *
          Real.exp ((gaussianMGFExponent mean variance).eval t) := by
  induction n with
  | zero => simp [gaussianMGFDerivativePolynomial]
  | succ n ih =>
      rw [iteratedDeriv_succ, ih]
      funext t
      have hderiv :=
        (((gaussianMGFDerivativePolynomial mean variance n).hasDerivAt t).mul
          (hasDerivAt_exp_gaussianMGFExponent mean variance t)).deriv
      convert hderiv using 1
      · with_unfolding_all rfl
      · simp [gaussianMGFDerivativePolynomial]
        ring

/-- Every raw real-Gaussian moment is the derivative polynomial evaluated at
zero. -/
theorem integral_pow_gaussianReal_eq_derivativePolynomial
    (mean : ℝ) (variance : NNReal) (n : ℕ) :
    (∫ x : ℝ, x ^ n ∂gaussianReal mean variance) =
      (gaussianMGFDerivativePolynomial mean (variance : ℝ) n).eval 0 := by
  have hmoment := iteratedDeriv_mgf_zero
    (X := fun x : ℝ => x) (μ := gaussianReal mean variance) (n := n) (by simp)
  calc
    (∫ x : ℝ, x ^ n ∂gaussianReal mean variance) =
        iteratedDeriv n (mgf (fun x : ℝ => x)
          (gaussianReal mean variance)) 0 := by
      simpa only [Pi.pow_apply] using hmoment.symm
    _ = iteratedDeriv n
        (fun t => Real.exp
          ((gaussianMGFExponent mean (variance : ℝ)).eval t)) 0 := by
      congr 2
      rw [mgf_fun_id_gaussianReal]
      funext t
      rw [gaussianMGFExponent_eval]
    _ = (gaussianMGFDerivativePolynomial mean (variance : ℝ) n).eval 0 := by
      rw [iteratedDeriv_exp_gaussianMGFExponent]
      simp

theorem integrable_pow_gaussianReal
    (mean : ℝ) (variance : NNReal) {n : ℕ} (hn : n ≠ 0) :
    Integrable (fun x : ℝ => x ^ n) (gaussianReal mean variance) := by
  have hLp := memLp_id_gaussianReal (μ := mean) (v := variance) (n : NNReal)
  have hnorm := hLp.integrable_norm_pow hn
  have hnorm' :
      Integrable (fun x : ℝ => ‖x ^ n‖) (gaussianReal mean variance) := by
    simpa [norm_pow] using hnorm
  exact (integrable_norm_iff
    ((continuous_id.pow n).aestronglyMeasurable)).mp hnorm'

@[simp] theorem integral_pow_one_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ∂gaussianReal mean variance) = mean := by
  simpa using integral_id_gaussianReal (μ := mean) (v := variance)

theorem integral_pow_two_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 2 ∂gaussianReal mean variance) =
      mean ^ 2 + variance := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

theorem integral_pow_three_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 3 ∂gaussianReal mean variance) =
      mean ^ 3 + 3 * mean * variance := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

theorem integral_pow_four_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 4 ∂gaussianReal mean variance) =
      mean ^ 4 + 6 * mean ^ 2 * variance + 3 * (variance : ℝ) ^ 2 := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

theorem integral_pow_five_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 5 ∂gaussianReal mean variance) =
      mean ^ 5 + 10 * mean ^ 3 * variance +
        15 * mean * (variance : ℝ) ^ 2 := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

theorem integral_pow_six_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 6 ∂gaussianReal mean variance) =
      mean ^ 6 + 15 * mean ^ 4 * variance +
        45 * mean ^ 2 * (variance : ℝ) ^ 2 +
          15 * (variance : ℝ) ^ 3 := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

theorem integral_pow_seven_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 7 ∂gaussianReal mean variance) =
      mean ^ 7 + 21 * mean ^ 5 * variance +
        105 * mean ^ 3 * (variance : ℝ) ^ 2 +
          105 * mean * (variance : ℝ) ^ 3 := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

theorem integral_pow_eight_gaussianReal (mean : ℝ) (variance : NNReal) :
    (∫ x : ℝ, x ^ 8 ∂gaussianReal mean variance) =
      mean ^ 8 + 28 * mean ^ 6 * variance +
        210 * mean ^ 4 * (variance : ℝ) ^ 2 +
          420 * mean ^ 2 * (variance : ℝ) ^ 3 +
            105 * (variance : ℝ) ^ 4 := by
  rw [integral_pow_gaussianReal_eq_derivativePolynomial]
  norm_num [gaussianMGFDerivativePolynomial]
  ring

/-- Centered even Gaussian moments through order eight. -/
theorem centered_even_moments (variance : NNReal) :
    (∫ x : ℝ, x ^ 2 ∂gaussianReal 0 variance) = variance ∧
      (∫ x : ℝ, x ^ 4 ∂gaussianReal 0 variance) =
        3 * (variance : ℝ) ^ 2 ∧
      (∫ x : ℝ, x ^ 6 ∂gaussianReal 0 variance) =
        15 * (variance : ℝ) ^ 3 ∧
      (∫ x : ℝ, x ^ 8 ∂gaussianReal 0 variance) =
        105 * (variance : ℝ) ^ 4 := by
  constructor
  · simpa using integral_pow_two_gaussianReal 0 variance
  constructor
  · simpa using integral_pow_four_gaussianReal 0 variance
  constructor
  · simpa using integral_pow_six_gaussianReal 0 variance
  · simpa using integral_pow_eight_gaussianReal 0 variance

/-- Centered odd Gaussian moments through order seven vanish. -/
theorem centered_odd_moments (variance : NNReal) :
    (∫ x : ℝ, x ∂gaussianReal 0 variance) = 0 ∧
      (∫ x : ℝ, x ^ 3 ∂gaussianReal 0 variance) = 0 ∧
      (∫ x : ℝ, x ^ 5 ∂gaussianReal 0 variance) = 0 ∧
      (∫ x : ℝ, x ^ 7 ∂gaussianReal 0 variance) = 0 := by
  constructor
  · simpa using integral_pow_one_gaussianReal 0 variance
  constructor
  · simpa using integral_pow_three_gaussianReal 0 variance
  constructor
  · simpa using integral_pow_five_gaussianReal 0 variance
  · simpa using integral_pow_seven_gaussianReal 0 variance

/-- Nonnegative variance corresponding to one coordinate scale. -/
abbrev coordinateVariance (scale : ι → ℝ) (i : ι) : NNReal :=
  FiniteProductGaussian.variance scale i

@[simp] theorem coe_coordinateVariance (scale : ι → ℝ) (i : ι) :
    (coordinateVariance scale i : ℝ) = scale i ^ 2 :=
  rfl

/-- A coordinate projection has the corresponding scalar Gaussian law. -/
theorem law_map_eval (mean scale : ι → ℝ) (i : ι) :
    (FiniteProductGaussian.law mean scale).map (Function.eval i) =
      gaussianReal (mean i) (coordinateVariance scale i) := by
  exact FiniteProductGaussian.law_map_eval mean scale i

/-- Every coordinate projection belongs to every finite Gaussian `L^p`. -/
theorem eval_memLp (mean scale : ι → ℝ) (i : ι) (p : NNReal) :
    MemLp (fun y : ι → ℝ => y i) p
      (FiniteProductGaussian.law mean scale) := by
  exact
    (memLp_id_gaussianReal
      (μ := mean i) (v := coordinateVariance scale i) p).comp_measurePreserving
      (measurePreserving_eval
        (μ := fun k : ι => gaussianReal (mean k)
          (coordinateVariance scale k)) i)

/-- The integral of a coordinate projection is its Gaussian mean parameter. -/
theorem integral_eval_eq_mean (mean scale : ι → ℝ) (i : ι) :
    (∫ y, y i ∂FiniteProductGaussian.law mean scale) = mean i := by
  rw [← integral_id_gaussianReal
    (μ := mean i) (v := coordinateVariance scale i)]
  rw [← law_map_eval mean scale i]
  exact
    (integral_map
      ((measurable_pi_apply i : Measurable (fun y : ι → ℝ => y i)).aemeasurable)
      aestronglyMeasurable_id).symm

/-- Distinct coordinate projections are independent. -/
theorem eval_indepFun
    (mean scale : ι → ℝ) {i j : ι} (hij : i ≠ j) :
    (fun y : ι → ℝ => y i) ⟂ᵢ[FiniteProductGaussian.law mean scale]
      (fun y : ι → ℝ => y j) := by
  unfold FiniteProductGaussian.law
  have hIndep :
      iIndepFun
        (fun k (y : ι → ℝ) => (id : ℝ → ℝ) (y k))
        (Measure.pi fun k : ι =>
          gaussianReal (mean k) (coordinateVariance scale k)) := by
    exact
      iIndepFun_pi
        (X := fun _ : ι => (id : ℝ → ℝ))
        (μ := fun k : ι =>
          gaussianReal (mean k) (coordinateVariance scale k))
        (fun _ => aemeasurable_id)
  simpa [Function.eval, coordinateVariance] using hIndep.indepFun hij

/-- Distinct coordinate raw cross moments factor into their means. -/
theorem integral_eval_mul_eval_eq_mul_mean
    (mean scale : ι → ℝ) {i j : ι} (hij : i ≠ j) :
    (∫ y, y i * y j ∂FiniteProductGaussian.law mean scale) =
      mean i * mean j := by
  calc
    (∫ y, y i * y j ∂FiniteProductGaussian.law mean scale) =
        (∫ y, y i ∂FiniteProductGaussian.law mean scale) *
          (∫ y, y j ∂FiniteProductGaussian.law mean scale) := by
      exact (eval_indepFun mean scale hij).integral_fun_mul_eq_mul_integral
        ((measurable_pi_apply i : Measurable (fun y : ι → ℝ => y i))
          |>.aestronglyMeasurable)
        ((measurable_pi_apply j : Measurable (fun y : ι → ℝ => y j))
          |>.aestronglyMeasurable)
    _ = mean i * mean j := by
      rw [integral_eval_eq_mean, integral_eval_eq_mean]

/-! ## Coordinate powers -/

/-- Every coordinate power integral under a finite product Gaussian is the
corresponding scalar Gaussian power integral. -/
theorem integral_eval_pow_eq_scalar
    (mean scale : ι → ℝ) (i : ι) (n : ℕ) :
    (∫ y, (y i) ^ n ∂FiniteProductGaussian.law mean scale) =
      ∫ x : ℝ, x ^ n ∂gaussianReal (mean i)
        (coordinateVariance scale i) := by
  rw [← law_map_eval mean scale i]
  exact (integral_map
    ((measurable_pi_apply i :
      Measurable (fun y : ι → ℝ => y i)).aemeasurable)
    ((continuous_id.pow n).aestronglyMeasurable)).symm

theorem integral_eval_pow_eq_derivativePolynomial
    (mean scale : ι → ℝ) (i : ι) (n : ℕ) :
    (∫ y, (y i) ^ n ∂FiniteProductGaussian.law mean scale) =
      (gaussianMGFDerivativePolynomial (mean i) (scale i ^ 2) n).eval 0 := by
  rw [integral_eval_pow_eq_scalar,
    integral_pow_gaussianReal_eq_derivativePolynomial]
  simp

/-- Distinct coordinate powers remain independent. -/
theorem eval_pow_indepFun
    (mean scale : ι → ℝ) {i j : ι} (hij : i ≠ j) (p q : ℕ) :
    (fun y : ι → ℝ => (y i) ^ p) ⟂ᵢ[FiniteProductGaussian.law mean scale]
      (fun y : ι → ℝ => (y j) ^ q) := by
  have hpow := (eval_indepFun mean scale hij).comp
    (φ := fun x : ℝ => x ^ p) (ψ := fun x : ℝ => x ^ q)
    (measurable_id.pow_const p)
    (measurable_id.pow_const q)
  simpa [Function.comp_def] using hpow

/-- Mixed powers of distinct coordinates factor into scalar moments. -/
theorem integral_eval_pow_mul_eval_pow_eq
    (mean scale : ι → ℝ) {i j : ι} (hij : i ≠ j) (p q : ℕ) :
    (∫ y, (y i) ^ p * (y j) ^ q
      ∂FiniteProductGaussian.law mean scale) =
      (∫ x : ℝ, x ^ p ∂gaussianReal (mean i)
        (coordinateVariance scale i)) *
      (∫ x : ℝ, x ^ q ∂gaussianReal (mean j)
        (coordinateVariance scale j)) := by
  calc
    (∫ y, (y i) ^ p * (y j) ^ q
        ∂FiniteProductGaussian.law mean scale) =
        (∫ y, (y i) ^ p ∂FiniteProductGaussian.law mean scale) *
          (∫ y, (y j) ^ q ∂FiniteProductGaussian.law mean scale) := by
      exact (eval_pow_indepFun mean scale hij p q)
        |>.integral_fun_mul_eq_mul_integral
          ((measurable_pi_apply i).pow measurable_const
            |>.aestronglyMeasurable)
          ((measurable_pi_apply j).pow measurable_const
            |>.aestronglyMeasurable)
    _ = _ := by
      rw [integral_eval_pow_eq_scalar, integral_eval_pow_eq_scalar]

theorem integral_eval_pow_two (mean scale : ι → ℝ) (i : ι) :
    (∫ y, (y i) ^ 2 ∂FiniteProductGaussian.law mean scale) =
      mean i ^ 2 + scale i ^ 2 := by
  rw [integral_eval_pow_eq_scalar, integral_pow_two_gaussianReal]
  simp

theorem integral_eval_pow_four (mean scale : ι → ℝ) (i : ι) :
    (∫ y, (y i) ^ 4 ∂FiniteProductGaussian.law mean scale) =
      mean i ^ 4 + 6 * mean i ^ 2 * scale i ^ 2 +
        3 * scale i ^ 4 := by
  rw [integral_eval_pow_eq_scalar, integral_pow_four_gaussianReal]
  simp
  ring

theorem integral_eval_pow_eight (mean scale : ι → ℝ) (i : ι) :
    (∫ y, (y i) ^ 8 ∂FiniteProductGaussian.law mean scale) =
      mean i ^ 8 + 28 * mean i ^ 6 * scale i ^ 2 +
        210 * mean i ^ 4 * scale i ^ 4 +
          420 * mean i ^ 2 * scale i ^ 6 + 105 * scale i ^ 8 := by
  rw [integral_eval_pow_eq_scalar, integral_pow_eight_gaussianReal]
  simp
  ring

end

end FiniteProductGaussianMoments
end Probability
end Mf
