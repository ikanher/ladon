import Mf.Probability.FiniteProductGaussianMoments
import Mf.DP.EuclideanVectorClipping
import Mathlib.MeasureTheory.SpecificCodomains.WithLp

/-!
# Gaussian gradient-noise energy

The parameter `sigmaDP` is the root-mean-square Euclidean norm after averaging
and before multiplication by the learning rate. Independent Gaussian coordinates
have scale `sigmaDP / sqrt d`. These moment calculations admit zero scale;
no almost-sure bound on the draws is assumed.
-/

namespace Mf.Optimization.PoissonClippedSGD

open MeasureTheory
open scoped BigOperators
noncomputable section

/-- Independent centered coordinates with total Euclidean noise scale sigmaDP. -/
def gaussianCoordinateLaw (d : ℕ) (sigmaDP : ℝ) : Measure (Fin d → ℝ) :=
  Mf.Probability.FiniteProductGaussian.law (fun _ => 0)
    (fun _ => sigmaDP / Real.sqrt (d : ℝ))

instance gaussianCoordinateLaw_isProbabilityMeasure (d : ℕ) (sigmaDP : ℝ) :
    IsProbabilityMeasure (gaussianCoordinateLaw d sigmaDP) := by
  unfold gaussianCoordinateLaw
  infer_instance

theorem gaussianVector_integrable (d : ℕ) (sigmaDP : ℝ) :
    Integrable (Mf.DP.toEuclidean (ι := Fin d)) (gaussianCoordinateLaw d sigmaDP) := by
  rw [MeasureTheory.integrable_piLp_iff]
  intro i
  have h := Mf.Probability.FiniteProductGaussianMoments.eval_memLp
    (fun _ : Fin d => 0) (fun _ => sigmaDP / Real.sqrt (d : ℝ)) i (1 : NNReal)
  simpa [Mf.DP.toEuclidean, gaussianCoordinateLaw] using h.integrable (by norm_num)

/-- The Euclidean gradient-noise vector is centered. -/
theorem integral_gaussianVector (d : ℕ) (sigmaDP : ℝ) :
    (∫ z, Mf.DP.toEuclidean z ∂gaussianCoordinateLaw d sigmaDP) = 0 := by
  have hf := gaussianVector_integrable d sigmaDP
  ext i
  rw [← PiLp.proj_apply (𝕜 := ℝ) 2 (fun _ : Fin d => ℝ) i
    (∫ z, Mf.DP.toEuclidean z ∂gaussianCoordinateLaw d sigmaDP)]
  rw [← (PiLp.proj (𝕜 := ℝ) 2 (fun _ : Fin d => ℝ) i).integral_comp_comm hf]
  change (∫ z : Fin d → ℝ, z i ∂gaussianCoordinateLaw d sigmaDP) = 0
  exact Mf.Probability.FiniteProductGaussianMoments.integral_eval_eq_mean _ _ i

private theorem gaussianCoordinate_sq_integrable (d : ℕ) (sigmaDP : ℝ) (i : Fin d) :
    Integrable (fun z : Fin d → ℝ => (z i) ^ 2) (gaussianCoordinateLaw d sigmaDP) := by
  have h := Mf.Probability.FiniteProductGaussianMoments.eval_memLp
    (fun _ : Fin d => 0) (fun _ => sigmaDP / Real.sqrt (d : ℝ)) i (2 : NNReal)
  simpa [gaussianCoordinateLaw, Real.norm_eq_abs, sq_abs] using
    h.integrable_norm_pow (by norm_num : 2 ≠ 0)

theorem gaussianNormSq_integrable (d : ℕ) (sigmaDP : ℝ) :
    Integrable (fun z => ‖Mf.DP.toEuclidean z‖ ^ 2)
      (gaussianCoordinateLaw d sigmaDP) := by
  have hsum : Integrable (fun z : Fin d → ℝ => ∑ i, (z i) ^ 2)
      (gaussianCoordinateLaw d sigmaDP) :=
    integrable_finsetSum _ (fun i _ => gaussianCoordinate_sq_integrable d sigmaDP i)
  simpa [Mf.DP.toEuclidean, EuclideanSpace.norm_sq_eq] using hsum

/-- Summing coordinate second moments gives exactly sigmaDP squared. -/
theorem integral_gaussianNormSq {d : ℕ} (hd : 0 < d) (sigmaDP : ℝ) :
    (∫ z, ‖Mf.DP.toEuclidean z‖ ^ 2 ∂gaussianCoordinateLaw d sigmaDP) = sigmaDP ^ 2 := by
  calc
    _ = ∫ z : Fin d → ℝ, ∑ i, (z i) ^ 2 ∂gaussianCoordinateLaw d sigmaDP := by
      congr 1
      funext z
      simp [Mf.DP.toEuclidean, EuclideanSpace.norm_sq_eq]
    _ = ∑ i, ∫ z : Fin d → ℝ, (z i) ^ 2 ∂gaussianCoordinateLaw d sigmaDP := by
      rw [integral_finsetSum]
      exact fun i _ => gaussianCoordinate_sq_integrable d sigmaDP i
    _ = ∑ _i : Fin d, (sigmaDP / Real.sqrt (d : ℝ)) ^ 2 := by
      apply Finset.sum_congr rfl
      intro i _
      simpa [gaussianCoordinateLaw] using
        Mf.Probability.FiniteProductGaussianMoments.integral_eval_pow_two
          (fun _ : Fin d => 0) (fun _ => sigmaDP / Real.sqrt (d : ℝ)) i
    _ = sigmaDP ^ 2 := by
      rw [Finset.sum_const, Finset.card_fin, div_pow, Real.sq_sqrt (by positivity)]
      rw [← Nat.cast_smul_eq_nsmul ℝ d (sigmaDP ^ 2 / (d : ℝ))]
      simp only [smul_eq_mul]
      have hdR : (d : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hd)
      field_simp [hdR]

end

end Mf.Optimization.PoissonClippedSGD
