import Mf.Optimization.PoissonClippedSGD.MomentumQuadraticTracking
import Mf.Optimization.FixedSubsetClippedSGD.MomentumReferenceBounds
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumUniformIndex

/-!
# Useful corrected-momentum bound for the protected Poisson experiment

The retuned step is 1/5. The actual zero-start corrected stream is compared
with its exact clipped-mean reference on all histories. The output index is
independent and uniform among the 49 pre-update iterates.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.MomentumQuadraticApplication
open MeasureTheory
open Mf.Optimization.FiniteMemoryAdam
open Mf.Optimization.FiniteMemoryAdam.CorrectedColumns
open Mf.Optimization.FiniteMemoryAdam.QuadraticReachability
open MomentumQuadraticModel
open Mf.Optimization.FixedSubsetClippedSGD.QuadraticApplication
open PoissonClippedSGD.QuadraticApplication
open Mf.Optimization.FixedSubsetClippedSGD.MomentumQuadraticModel hiding state state_memLp quadratic_tracking_position_bound quadratic_tracking_storage_bound
open scoped BigOperators
set_option maxRecDepth 65536

/-- Joint position error is the actual state minus the exact reference. -/
theorem tracking_error_position (t : ℕ) (ω : Trajectory.History 100000 (Fin 50000 → Bool) t) :
    (trackingError (1/5) (9/10) samplingProbability (2/5) quadraticRecordGradient initialPoint t ω t).1 =
      (MomentumQuadraticModel.state t ω t).1 - (reference t).1 := by
  have hf : (fun x (_ : Unit) => clippedMean (2/5) (fun r => quadraticRecordGradient r x)) =
      (fun x (_ : Unit) => mean x) := by
    funext x u
    unfold mean
    rfl
  simp only [trackingError, momentumTrackingError, MomentumQuadraticModel.state, momentumState,
    reference]
  rw [hf]

/-- A slightly rounded tracking radius leaves a strict useful final margin. -/
theorem tracking_energy_budget :
    2*(2023/500:ℝ)*centeredVariance < (29/625)^2 := by
  unfold centeredVariance totalNoise
  rw [count_variance_factor, Real.sq_sqrt (by positivity)]
  norm_num [coordinateNoise]

/-- Expected distance from the exact deterministic reference, under each actual prefix law. -/
theorem expected_tracking_norm_le (t : ℕ) (ht : t ≤ 48) :
    (∫ ω, ‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) ≤ (29/625:ℝ) := by
  haveI : IsProbabilityMeasure
      (gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) := by
    unfold gaussianHistoryLaw Trajectory.historyLaw
    infer_instance
  have hm := momentumState_measurable (1/5) (9/10) samplingProbability (2/5) (by norm_num)
    quadraticRecordGradient quadraticRecordGradient_measurable initialPoint t t
  have he := (state_memLp t t).1.sub (memLp_const (reference t).1)
  have hp : Measurable (fun ω => ‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖^2) := by
    exact (hm.sub measurable_const).norm.pow_const 2
  have h := integral_sqrt_le (fun ω => ‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖^2) hp
    (fun _ => sq_nonneg _) (he.integrable_norm_pow (by norm_num : 2 ≠ 0))
  simp only [Real.sqrt_sq (norm_nonneg _)] at h
  have hb := quadratic_tracking_position_bound t ht
  simp_rw [tracking_error_position] at hb
  have hsq : Real.sqrt (∫ ω, ‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖^2
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) ≤ (29/625:ℝ) := by
    apply (Real.sqrt_le_iff).2
    exact ⟨by norm_num, hb.trans tracking_energy_budget.le⟩
  exact h.trans hsq

/-- Each own-time expected true gradient is bounded by reference plus tracking. -/
theorem prefix_gradient_bound (t : ℕ) (ht : t ≤ 48) :
    (∫ ω, ‖meanGradient (MomentumQuadraticModel.state t ω t).1‖
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) ≤
      |(scalarReference t).1|/4 + (29/2500:ℝ) := by
  haveI : IsProbabilityMeasure
      (gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) := by
    unfold gaussianHistoryLaw Trajectory.historyLaw
    infer_instance
  have he := (state_memLp t t).1.sub (memLp_const (reference t).1)
  have hx := ((state_memLp t t).1.const_smul (1/4:ℝ)).integrable (by norm_num)
  have hpoint (ω) : ‖meanGradient (MomentumQuadraticModel.state t ω t).1‖ ≤
      (1/4:ℝ)*‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖ + (1/4:ℝ)*‖(reference t).1‖ := by
    unfold meanGradient
    rw [norm_smul, Real.norm_eq_abs, abs_of_pos (by norm_num : (0:ℝ)<1/4)]
    exact (mul_le_mul_of_nonneg_left (norm_le_norm_sub_add _ _) (by norm_num)).trans_eq
      (mul_add _ _ _)
  have h := integral_mono hx.norm
    (((he.integrable (by norm_num)).norm.const_mul (1/4:ℝ)).add (integrable_const _)) hpoint
  change (∫ ω, ‖meanGradient (MomentumQuadraticModel.state t ω t).1‖
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) ≤
    (∫ ω, (1/4:ℝ)*‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖ +
      (1/4:ℝ)*‖(reference t).1‖
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) at h
  rw [integral_add (f := fun ω => (1/4:ℝ)*‖(MomentumQuadraticModel.state t ω t).1 - (reference t).1‖)
    (g := fun _ => (1/4:ℝ)*‖(reference t).1‖)
    (((he.integrable (by norm_num)).norm).const_mul (1/4:ℝ))
    (integrable_const _), integral_const_mul] at h
  simp only [integral_const, probReal_univ, one_smul] at h
  have hr : ‖(reference t).1‖ = |(scalarReference t).1| := by
    rw [reference_eq_scalar]
    exact axis_norm _
  rw [hr] at h
  have heBound := expected_tracking_norm_le t ht
  nlinarith

/-- Full 49-step history with an independent uniform pre-update index. -/
def experimentLaw := outputLaw 50000 100000 49 samplingProbability samplingProbability_le_one totalNoise

def experimentOutput (p : Fin 49 × Trajectory.History 100000 (Fin 50000 → Bool) 49) : Point :=
  (MomentumQuadraticModel.state 49 p.2 p.1.val).1

/-- Actual positions are measurable under any finite initialized history. -/
theorem state_position_measurable (T t : ℕ) :
    Measurable (fun ω => (MomentumQuadraticModel.state T ω t).1) := by
  exact momentumState_measurable (1/5) (9/10) samplingProbability (2/5) (by norm_num)
    quadraticRecordGradient quadraticRecordGradient_measurable initialPoint T t

theorem gradient_norm_integrable (T t : ℕ) :
    Integrable (fun ω => ‖meanGradient (MomentumQuadraticModel.state T ω t).1‖)
      (gaussianHistoryLaw 50000 100000 T samplingProbability samplingProbability_le_one totalNoise) := by
  exact (((state_memLp T t).1.const_smul (1/4:ℝ)).integrable (by norm_num)).norm

/-- The full state at time t uses exactly its t chronological innovations. -/
theorem state_prefix {T t : ℕ} (ht : t ≤ T)
    (ω : Trajectory.History 100000 (Fin 50000 → Bool) T) :
    MomentumQuadraticModel.state T ω t =
      MomentumQuadraticModel.state t (momentumPastHistory ht ω) t := by
  exact @momentumState_on_past 50000 100000 (1/5) (9/10) samplingProbability (2/5)
    quadraticRecordGradient initialPoint T t ht ω

/-- Transport own-time expectation to the common output history without changing its law. -/
theorem gradient_integral_prefix {T t : ℕ} (ht : t ≤ T) :
    (∫ ω, ‖meanGradient (MomentumQuadraticModel.state T ω t).1‖
      ∂gaussianHistoryLaw 50000 100000 T samplingProbability samplingProbability_le_one totalNoise) =
    (∫ ω, ‖meanGradient (MomentumQuadraticModel.state t ω t).1‖
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) := by
  have heq : (fun ω => ‖meanGradient (MomentumQuadraticModel.state T ω t).1‖) =
      (fun ω => ‖meanGradient
        (MomentumQuadraticModel.state t (momentumPastHistory ht ω) t).1‖) := by
    funext ω
    rw [state_prefix ht]
  rw [heq]
  exact momentumFiniteLaw_integral_prefix
    (gaussianStepLaw 50000 100000 samplingProbability samplingProbability_le_one totalNoise) ht _ (gradient_norm_integrable t t)

/-- The actual independent-uniform output has a finite expected true-gradient norm. -/
theorem output_norm_integrable :
    Integrable (fun p => ‖meanGradient (experimentOutput p)‖) experimentLaw := by
  have hm : Measurable experimentOutput := by
    apply measurable_from_prod_countable_right
    intro t
    exact state_position_measurable 49 t.val
  have hg : Measurable (meanGradient (d := 100000)) := by
    unfold meanGradient
    fun_prop
  change Integrable _ ((PMF.uniformOfFintype (Fin 49)).toMeasure.prod
    (gaussianHistoryLaw 50000 100000 49 samplingProbability samplingProbability_le_one totalNoise))
  apply (integrable_prod_iff (hg.comp hm).norm.aestronglyMeasurable).mpr
  exact ⟨ae_of_all _ (fun t => gradient_norm_integrable 49 t.val), Integrable.of_finite⟩

/-- Uniform output equals the average over the declared pre-update window. -/
theorem output_integral_average :
    (∫ p, ‖meanGradient (experimentOutput p)‖ ∂experimentLaw) =
      (49:ℝ)⁻¹ * ∑ t : Fin 49,
        ∫ ω, ‖meanGradient (MomentumQuadraticModel.state 49 ω t.val).1‖
          ∂gaussianHistoryLaw 50000 100000 49 samplingProbability samplingProbability_le_one totalNoise := by
  apply independent_uniform_index_integral
    (gaussianHistoryLaw 50000 100000 49 samplingProbability samplingProbability_le_one totalNoise) 49
    (fun t ω => ‖meanGradient (MomentumQuadraticModel.state 49 ω t.val).1‖)
  · intro t
    have hg : Measurable (meanGradient (d := 100000)) := by
      unfold meanGradient
      fun_prop
    exact (hg.comp (state_position_measurable 49 t.val)).norm
  · intro t
    exact gradient_norm_integrable 49 t.val

/-- Complete useful expected true-gradient bound for the actual corrected momentum mechanism. -/
theorem expected_norm_lt :
    (∫ p, ‖meanGradient (experimentOutput p)‖ ∂experimentLaw) < (26/125:ℝ) := by
  rw [output_integral_average]
  have hsum : (∑ t : Fin 49,
      ∫ ω, ‖meanGradient (MomentumQuadraticModel.state 49 ω t.val).1‖
        ∂gaussianHistoryLaw 50000 100000 49 samplingProbability samplingProbability_le_one totalNoise) ≤
      ∑ t : Fin 49, (|(scalarReference t.val).1|/4 + (29/2500:ℝ)) := by
    apply Finset.sum_le_sum
    intro t _
    rw [gradient_integral_prefix t.isLt.le]
    exact prefix_gradient_bound t.val (by omega)
  have h := mul_le_mul_of_nonneg_left hsum (show (0:ℝ) ≤ 49⁻¹ by norm_num)
  have hsumEq : (49:ℝ)⁻¹ * (∑ t : Fin 49, (|(scalarReference t.val).1|/4 + (29/2500:ℝ))) =
      (∑ t : Fin 49, |(scalarReference t.val).1|)/(4*49) + 29/2500 := by
    rw [Finset.sum_add_distrib, ← Finset.sum_div]
    simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    ring
  rw [hsumEq] at h
  have href := scalar_reference_average_lt
  linarith

/-- The useful endpoint strictly improves on the initialized true-gradient norm. -/
theorem expected_norm_improves_initial :
    (∫ p, ‖meanGradient (experimentOutput p)‖ ∂experimentLaw) < ‖meanGradient initialPoint‖ := by
  have h0 : (26/125:ℝ) < ‖meanGradient initialPoint‖ := by
    rw [meanGradient, norm_smul, Real.norm_eq_abs, abs_of_pos (by norm_num : (0:ℝ)<1/4)]
    have hi := initial_norm_sq
    have hn := norm_nonneg initialPoint
    nlinarith
  exact expected_norm_lt.trans h0

end Mf.Optimization.PoissonClippedSGD.MomentumQuadraticApplication
