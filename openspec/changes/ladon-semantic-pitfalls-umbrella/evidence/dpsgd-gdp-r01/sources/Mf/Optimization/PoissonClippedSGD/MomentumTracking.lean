import Mf.Optimization.PoissonClippedSGD.MomentumStateMoments
import Mf.Optimization.PoissonClippedSGD.MomentumTrackingStep
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumTrackingDynamics
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumTrackingHistory

/-!
# Actual Poisson momentum tracking histories

The error compares the maintained corrected optimizer with the exact population
clipped-mean stream. Its finite-history storage is integrable. Splitting off
the newest draw connects the actual recursion to the fresh-kernel bound.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open Mf.Optimization.FiniteMemoryAdam
open Mf.Optimization.FiniteMemoryAdam.CorrectedColumns

/-- Joint corrected state on a long history equals the state on its own chronological prefix. -/
theorem momentumState_on_past {n d : ℕ} (η β : ℝ) (π : ℝ) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d) (x₀ : MomentumVector d)
    {T t : ℕ} (ht : t ≤ T) (ω : Trajectory.History d (Fin n → Bool) T) :
    momentumState η β π c g x₀ T ω t =
      momentumState η β π c g x₀ t (momentumPastHistory ht ω) t := by
  unfold momentumState
  exact momentumStreamRun_on_past η β _ x₀ ((fun _ => false), 0) ht ω

/-- Joint error against the deterministic clipped-mean reference. -/
def trackingError {n d : ℕ} (η β : ℝ) (π : ℝ) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d) (x₀ : MomentumVector d)
    (T : ℕ) (ω : Trajectory.History d (Fin n → Bool) T) (t : ℕ) :=
  momentumTrackingError η β (fun x p => sampledGradient π c g x p.1 + p.2)
    (fun x => clippedMean c (fun i => g i x)) x₀
    (momentumFiniteInnovation ((fun _ => false), 0) ω) t

/-- Both errors are L², with no restriction on clipping phases or Gaussian draws. -/
theorem trackingError_memLp {n d : ℕ} (hn : 0 < n) (π : NNReal) (hπ0 : 0 < π) (hπ1 : π ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (x₀ : MomentumVector d) (T t : ℕ) :
    MemLp (fun ω => (trackingError η β π c g x₀ T ω t).1) 2
      (gaussianHistoryLaw n d T π hπ1 s) ∧
    MemLp (fun ω => (trackingError η β π c g x₀ T ω t).2) 2
      (gaussianHistoryLaw n d T π hπ1 s) := by
  haveI : IsProbabilityMeasure (gaussianHistoryLaw n d T π hπ1 s) := by
    unfold gaussianHistoryLaw Trajectory.historyLaw
    infer_instance
  let r := momentumStreamRun η β
    (fun x (_ : Unit) => clippedMean c (fun i => g i x)) x₀ (fun _ => ()) t
  have hactual := momentumState_memLp_two hn π hπ0 hπ1 η β c s hc g hg x₀ T t
  constructor
  · exact hactual.1.sub (memLp_const r.1)
  · have heq : (fun ω => (trackingError η β π c g x₀ T ω t).2) =
        (-η) • ((1-β^t)⁻¹ • (fun ω => (momentumState η β π c g x₀ T ω t).2)) -
          (fun _ => momentumVelocity η β t r.2) := by
      funext ω
      simp only [trackingError, momentumTrackingError, momentumVelocity,
        correctedFirstVector_eq_smul, momentumState, r, Pi.smul_apply, Pi.sub_apply]
    rw [heq]
    exact ((hactual.2.const_smul ((1-β^t)⁻¹)).const_smul (-η)).sub (memLp_const _)

/-- Every time-dependent quadratic storage has a genuine finite integral. -/
theorem tracking_storage_integrable {n d : ℕ} (hn : 0 < n) (π : NNReal) (hπ0 : 0 < π) (hπ1 : π ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (x₀ : MomentumVector d) (T t : ℕ) (b : ℝ) :
    Integrable (fun ω => MomentumTracking.storage b
      (trackingError η β π c g x₀ T ω t).1
      (trackingError η β π c g x₀ T ω t).2) (gaussianHistoryLaw n d T π hπ1 s) := by
  have he := trackingError_memLp hn π hπ0 hπ1 η β c s hc g hg x₀ T t
  exact ((he.1.add (he.2.const_smul b)).integrable_norm_pow (by norm_num)).add
    ((he.2.integrable_norm_pow (by norm_num : 2 ≠ 0)).const_mul (b^2))

/-- The joint pre-update error depends only on the independent past tail. -/
theorem trackingError_fresh_split {n d : ℕ} (η β : ℝ) (π : ℝ) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d) (x₀ : MomentumVector d)
    (t : ℕ) (ω : Trajectory.History d (Fin n → Bool) (t+1)) :
    trackingError η β π c g x₀ (t+1) ω t =
      trackingError η β π c g x₀ t (Fin.tail ω) t := by
  exact momentumTrackingError_fresh_split η β _ _ x₀ ((fun _ => false), 0) t ω

/-- Exact velocity error after exposing the newest sample. -/
theorem trackingError_velocity_fresh {n d : ℕ}
    (η β : ℝ) (hβ : 0 ≤ β) (hβ1 : β < 1) (π : ℝ) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d) (x₀ : MomentumVector d)
    (t : ℕ) (past : Trajectory.History d (Fin n → Bool) t)
    (sample : (Fin n → Bool) × MomentumVector d) :
    (trackingError η β π c g x₀ (t+1) (Fin.cons sample past) (t+1)).2 =
      carryWeight β t • (trackingError η β π c g x₀ t past t).2 -
        (η*freshWeight β t) •
          (sampledGradient π c g (momentumState η β π c g x₀ t past t).1 sample.1 + sample.2 -
            clippedMean c (fun i => g i
              (momentumStreamRun η β
                (fun x (_ : Unit) => clippedMean c (fun i => g i x))
                x₀ (fun _ => ()) t).1)) := by
  unfold trackingError
  rw [momentumTrackingError_velocity_succ η β hβ hβ1,
    momentumTrackingError_fresh_split,
    momentumStreamRelease_fresh_split]
  simp only [Fin.tail_cons, Fin.cons_zero, momentumState]

/-- Exact position error after exposing the newest sample. -/
theorem trackingError_position_fresh {n d : ℕ} (η β : ℝ) (π : ℝ) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d) (x₀ : MomentumVector d)
    (t : ℕ) (past : Trajectory.History d (Fin n → Bool) t)
    (sample : (Fin n → Bool) × MomentumVector d) :
    (trackingError η β π c g x₀ (t+1) (Fin.cons sample past) (t+1)).1 =
      (trackingError η β π c g x₀ t past t).1 +
      (trackingError η β π c g x₀ (t+1) (Fin.cons sample past) (t+1)).2 := by
  unfold trackingError
  rw [momentumTrackingError_position_succ, momentumTrackingError_fresh_split]
  simp only [Fin.tail_cons]

/-- The actual independent sample supplies the full conditional tracking step. -/
theorem tracking_storage_fresh_le {n d : ℕ}
    (hn : 0 < n) (hd : 0 < d) (π : NNReal) (hπ0 : 0 < π) (hπ1 : π ≤ 1)
    (η β c s : ℝ) (hβ : 0 ≤ β) (hβ1 : β < 1) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d)
    (L : ℝ) (hL : 0 < L)
    (hco : ∀ x y, ‖clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)‖^2 ≤
      L*inner ℝ (x-y) (clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)))
    (x₀ : MomentumVector d) (t : ℕ) (b : ℝ) (hb : 0 ≤ b) (hγ : 0 < η*freshWeight β t)
    (hgate : (η*freshWeight β t)*L*(1+b)*((1+b)^2+b^2) ≤ 1+2*b)
    (past : Trajectory.History d (Fin n → Bool) t) :
    (∫ sample, MomentumTracking.storage b
      (trackingError η β π c g x₀ (t+1) (Fin.cons sample past) (t+1)).1
      (trackingError η β π c g x₀ (t+1) (Fin.cons sample past) (t+1)).2
      ∂gaussianStepLaw n d π hπ1 s) ≤
      MomentumTracking.storage (carryWeight β t*(1+b))
        (trackingError η β π c g x₀ t past t).1
        (trackingError η β π c g x₀ t past t).2 +
      (η*freshWeight β t)^2*((1+b)^2+b^2)*(((1-(π:ℝ))/((π:ℝ)*n))*c^2+s^2) := by
  simp_rw [trackingError_position_fresh, trackingError_velocity_fresh η β hβ hβ1]
  exact momentum_fresh_tracking_step_le hn hd π hπ0 hπ1 c s hc g
    (carryWeight β t) (η*freshWeight β t) L b hγ hL hb hgate
    (momentumState η β π c g x₀ t past t).1
    (momentumStreamRun η β (fun x (_ : Unit) => clippedMean c (fun i => g i x))
      x₀ (fun _ => ()) t).1
    (trackingError η β π c g x₀ t past t).2 (hco _ _)

/-- Every prefix pays only its accumulated centered-variance injections. -/
theorem tracking_storage_bound {n d : ℕ}
    (hn : 0 < n) (hd : 0 < d) (π : NNReal) (hπ0 : 0 < π) (hπ1 : π ≤ 1)
    (η β c s : ℝ) (hβ : 0 ≤ β) (hβ1 : β < 1) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (L : ℝ) (hL : 0 < L)
    (hco : ∀ x y, ‖clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)‖ ^ 2 ≤
      L * inner ℝ (x-y) (clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)))
    (x₀ : MomentumVector d) (bridge : ℕ → ℝ) (T : ℕ)
    (hb : ∀ t, t ≤ T → 0 ≤ bridge t)
    (hbridge : ∀ t, t < T → bridge t = carryWeight β t * (1 + bridge (t+1)))
    (hγ : ∀ t, t < T → 0 < η * freshWeight β t)
    (hgate : ∀ t, t < T → (η * freshWeight β t) * L * (1 + bridge (t+1)) *
      ((1 + bridge (t+1)) ^ 2 + bridge (t+1) ^ 2) ≤ 1 + 2 * bridge (t+1)) :
    ∀ t, t ≤ T → (∫ ω, MomentumTracking.storage (bridge t)
      (trackingError η β π c g x₀ t ω t).1
      (trackingError η β π c g x₀ t ω t).2 ∂gaussianHistoryLaw n d t π hπ1 s) ≤
      ∑ j ∈ Finset.range t, (η * freshWeight β j) ^ 2 *
        ((1 + bridge (j+1)) ^ 2 + bridge (j+1) ^ 2) *
        (((1-(π:ℝ))/((π:ℝ)*n))*c^2+s^2) := by
  let ν := gaussianStepLaw n d π hπ1 s
  let S := fun t (ω : Trajectory.History d (Fin n → Bool) t) =>
    MomentumTracking.storage (bridge t)
      (trackingError η β π c g x₀ t ω t).1 (trackingError η β π c g x₀ t ω t).2
  have hS : ∀ t, Integrable (S t) (Trajectory.historyLaw ν t) := by
    intro t
    exact tracking_storage_integrable hn π hπ0 hπ1 η β c s hc g hg x₀ t t (bridge t)
  have hz : ∀ ω, S 0 ω = 0 := by
    intro ω
    dsimp only [S, trackingError]
    rw [momentumTrackingError_zero]
    simp [MomentumTracking.storage]
  apply MomentumTracking.history_storage_bound ν S hS hz _ T
  intro t ht past
  have h := tracking_storage_fresh_le hn hd π hπ0 hπ1 η β c s hβ hβ1 hc
    g L hL hco x₀ t (bridge (t+1)) (hb (t+1) (by omega)) (hγ t ht)
    (hgate t ht) past
  simpa only [S, ν, ← hbridge t ht] using h

/-- The same global argument bounds the actual position error at every prefix. -/
theorem tracking_position_energy_le_twice_storage {n d : ℕ} (hn : 0 < n) (π : NNReal) (hπ0 : 0 < π) (hπ1 : π ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (x₀ : MomentumVector d) (T t : ℕ) (b : ℝ) :
    (∫ ω, ‖(trackingError η β π c g x₀ T ω t).1‖ ^ 2 ∂gaussianHistoryLaw n d T π hπ1 s) ≤
      2 * (∫ ω, MomentumTracking.storage b
        (trackingError η β π c g x₀ T ω t).1
        (trackingError η β π c g x₀ T ω t).2 ∂gaussianHistoryLaw n d T π hπ1 s) := by
  rw [← integral_const_mul]
  exact integral_mono
    ((trackingError_memLp hn π hπ0 hπ1 η β c s hc g hg x₀ T t).1.integrable_norm_pow (by norm_num))
    ((tracking_storage_integrable hn π hπ0 hπ1 η β c s hc g hg x₀ T t b).const_mul 2)
    (fun _ => MomentumTracking.position_sq_le_storage _ _ _)

end Mf.Optimization.PoissonClippedSGD
