import Mf.Optimization.PoissonClippedSGD.MomentumTracking
import Mf.Optimization.PoissonClippedSGD.QuadraticApplication
import Mf.Optimization.FixedSubsetClippedSGD.MomentumQuadraticTracking

/-!
# Actual Poisson tracking certificate for the protected momentum experiment

The sampler-independent reference and backward coefficients come from the
fixed-subset application. Random total counts cost kappa times C², in addition
to all Gaussian coordinates, under the exact Bernoulli product law.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.MomentumQuadraticModel
open MeasureTheory
open Mf.Optimization.FiniteMemoryAdam
open Mf.Optimization.FiniteMemoryAdam.CorrectedColumns
open Mf.Optimization.FiniteMemoryAdam.QuadraticReachability
open Mf.Optimization.FixedSubsetClippedSGD.QuadraticApplication
open Mf.Optimization.FixedSubsetClippedSGD.MomentumQuadraticModel
open PoissonClippedSGD.QuadraticApplication
open scoped BigOperators
set_option maxRecDepth 65536

/-- The maintained Poisson stream, with public expected batch size and no denominator. -/
def state (T : ℕ) (ω : Trajectory.History 100000 (Fin 50000 → Bool) T) (t : ℕ) :=
  momentumState (1/5) (9/10) samplingProbability (2/5)
    quadraticRecordGradient initialPoint T ω t

theorem state_memLp (T t : ℕ) :
    MemLp (fun ω => (state T ω t).1) 2
      (gaussianHistoryLaw 50000 100000 T samplingProbability samplingProbability_le_one totalNoise) ∧
    MemLp (fun ω => (state T ω t).2) 2
      (gaussianHistoryLaw 50000 100000 T samplingProbability samplingProbability_le_one totalNoise) := by
  exact momentumState_memLp_two (by norm_num) samplingProbability samplingProbability_pos
    samplingProbability_le_one (1/5) (9/10) (2/5) totalNoise (by norm_num)
    quadraticRecordGradient quadraticRecordGradient_measurable initialPoint T t

/-- The exact Gaussian/Poisson centered-variance allowance. -/
def centeredVariance : ℝ :=
  ((1-(samplingProbability:ℝ))/((samplingProbability:ℝ)*50000))*(2/5)^2 + totalNoise^2

theorem centeredVariance_nonneg : 0 ≤ centeredVariance := by
  unfold centeredVariance
  rw [count_variance_factor]
  positivity

/-- Every actual initialized prefix consumes all its corrected storage gates. -/
theorem quadratic_tracking_storage_bound (t : ℕ) (ht : t ≤ 48) :
    (∫ ω, MomentumTracking.storage (trackingBridge t)
      (trackingError (1/5) (9/10) samplingProbability (2/5) quadraticRecordGradient initialPoint t ω t).1
      (trackingError (1/5) (9/10) samplingProbability (2/5) quadraticRecordGradient initialPoint t ω t).2
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) ≤
      ∑ j ∈ Finset.range t, trackingCharge j * centeredVariance := by
  apply tracking_storage_bound (n := 50000) (d := 100000)
    (by norm_num) (by norm_num) samplingProbability samplingProbability_pos samplingProbability_le_one
    (1/5) (9/10) (2/5) totalNoise (by norm_num) (by norm_num) (by norm_num)
    quadraticRecordGradient quadraticRecordGradient_measurable
    (1/4) (by norm_num) clipped_field_cocoercive initialPoint trackingBridge 48
    trackingBridge_nonneg trackingBridge_rec
    (fun j hj => MomentumTracking.Weights.gamma_pos ⟨j, hj⟩) ?_ t ht
  intro j hj
  have h := MomentumTracking.Weights.storage_gate ⟨j, hj⟩
  simpa only [MomentumTracking.Weights.gamma, ← trackingBridge_eq, Fin.val_succ] using h

/-- Global unconditional position-error bound under the exact Poisson prefix law. -/
theorem quadratic_tracking_position_bound (t : ℕ) (ht : t ≤ 48) :
    (∫ ω, ‖(trackingError (1/5) (9/10) samplingProbability (2/5) quadraticRecordGradient
      initialPoint t ω t).1‖^2
      ∂gaussianHistoryLaw 50000 100000 t samplingProbability samplingProbability_le_one totalNoise) ≤
      2*(2023/500)*centeredVariance := by
  have hpos := tracking_position_energy_le_twice_storage (n := 50000) (d := 100000)
    (by norm_num) samplingProbability samplingProbability_pos samplingProbability_le_one
    (1/5) (9/10) (2/5) totalNoise (by norm_num) quadraticRecordGradient
    quadraticRecordGradient_measurable initialPoint t t (trackingBridge t)
  have hs := quadratic_tracking_storage_bound t ht
  have hsum := trackingCharge_prefix_le t ht
  rw [← Finset.sum_mul] at hs
  exact hpos.trans ((mul_le_mul_of_nonneg_left hs (by norm_num)).trans
    (by nlinarith [mul_le_mul_of_nonneg_right hsum centeredVariance_nonneg]))

end Mf.Optimization.PoissonClippedSGD.MomentumQuadraticModel
