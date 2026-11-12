import Mf.Optimization.PoissonClippedSGD.GaussianVectorLaw
import Mathlib.MeasureTheory.SpecificCodomains.WithLp
import Mathlib.MeasureTheory.Function.L2Space
import Mathlib.MeasureTheory.Function.LpSeminorm.Prod
import Mathlib.MeasureTheory.Integral.Prod

/-!
# Adding independent centered noise

A finite sampled drift and square-integrable centered noise have additive
means and energies under their product law. No Gaussian-specific density
calculation or bound on individual noise draws is used here.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
noncomputable section
variable {d : ℕ}

theorem integral_shift_norm_sq (ν : Measure (EuclideanSpace ℝ (Fin d)))
    [IsProbabilityMeasure ν] (hν : MemLp (fun z => z) 2 ν)
    (hmean : (∫ z, z ∂ν) = 0) (a : EuclideanSpace ℝ (Fin d)) :
    (∫ z, ‖a + z‖ ^ 2 ∂ν) = ‖a‖ ^ 2 + ∫ z, ‖z‖ ^ 2 ∂ν := by
  have hz := hν.integrable (by norm_num)
  have hz2 := hν.integrable_norm_pow (by norm_num : 2 ≠ 0)
  have hi := hz.const_inner (𝕜 := ℝ) a
  have heq : (fun z => ‖a + z‖ ^ 2) =
      (fun z => ‖a‖ ^ 2 + 2 * inner ℝ a z + ‖z‖ ^ 2) := by
    funext z
    exact norm_add_sq_real a z
  have hsum : Integrable (fun z => ‖a‖ ^ 2 + 2 * inner ℝ a z) ν :=
    (integrable_const (‖a‖ ^ 2)).add (hi.const_mul 2)
  rw [heq, integral_add hsum hz2,
    integral_add (integrable_const (‖a‖ ^ 2)) (hi.const_mul 2), integral_const,
    integral_const_mul, integral_inner hz, hmean]
  simp

theorem independent_direction_memLp {Mask : Type*} [Fintype Mask]
    [MeasurableSpace Mask] [MeasurableSingletonClass Mask]
    (μ : Measure Mask) (ν : Measure (EuclideanSpace ℝ (Fin d)))
    [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    (h : Mask → EuclideanSpace ℝ (Fin d))
    (hν : MemLp (fun z => z) 2 ν) :
    MemLp (fun p : Mask × EuclideanSpace ℝ (Fin d) => h p.1 + p.2) 2 (μ.prod ν) := by
  have hh : MemLp h 2 μ :=
    (memLp_two_iff_integrable_sq_norm (by fun_prop)).2 Integrable.of_finite
  exact (hh.comp_fst ν).add (hν.comp_snd μ)

theorem independent_direction_mean {Mask : Type*} [Fintype Mask]
    [MeasurableSpace Mask] [MeasurableSingletonClass Mask]
    (μ : Measure Mask) (ν : Measure (EuclideanSpace ℝ (Fin d)))
    [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    (h : Mask → EuclideanSpace ℝ (Fin d))
    (hν : MemLp (fun z => z) 2 ν) (hmean : (∫ z, z ∂ν) = 0) :
    (∫ p : Mask × EuclideanSpace ℝ (Fin d), h p.1 + p.2 ∂μ.prod ν) =
      ∫ m, h m ∂μ := by
  have hh : Integrable h μ := Integrable.of_finite
  have hz := hν.integrable (by norm_num)
  rw [integral_add (hh.comp_fst ν) (hz.comp_snd μ)]
  rw [integral_fun_fst, integral_fun_snd (fun z : EuclideanSpace ℝ (Fin d) => z), hmean]
  simp

theorem independent_direction_energy {Mask : Type*} [Fintype Mask]
    [MeasurableSpace Mask] [MeasurableSingletonClass Mask]
    (μ : Measure Mask) (ν : Measure (EuclideanSpace ℝ (Fin d)))
    [IsProbabilityMeasure μ] [IsProbabilityMeasure ν]
    (h : Mask → EuclideanSpace ℝ (Fin d))
    (hν : MemLp (fun z => z) 2 ν) (hmean : (∫ z, z ∂ν) = 0) :
    (∫ p : Mask × EuclideanSpace ℝ (Fin d), ‖h p.1 + p.2‖ ^ 2 ∂μ.prod ν) =
      (∫ m, ‖h m‖ ^ 2 ∂μ) + ∫ z, ‖z‖ ^ 2 ∂ν := by
  have henergy := (independent_direction_memLp μ ν h hν).integrable_norm_pow
    (by norm_num : 2 ≠ 0)
  rw [integral_prod _ henergy]
  simp_rw [integral_shift_norm_sq ν hν hmean]
  rw [integral_add Integrable.of_finite (integrable_const _)]
  simp

end
end Mf.Optimization.PoissonClippedSGD
