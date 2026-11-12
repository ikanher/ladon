import Mf.Optimization.PoissonClippedSGD.MomentumStateMoments
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumClippedObservables

/-!
# Poisson corrected momentum on a common history horizon

The own-time Poisson pairing and exact release energy are transported to the
same full product law. The energy retains the sampled-total fluctuation in its
coefficient of the clipped population mean.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open Mf.Optimization.FiniteMemoryAdam.CorrectedColumns
noncomputable section
set_option maxHeartbeats 800000

def momentumRelease {n d : ℕ} (η β : ℝ) (q : NNReal) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d)
    (x₀ : MomentumVector d) (T : ℕ)
    (ω : Trajectory.History d (Fin n → Bool) T) (t : ℕ) : MomentumVector d :=
  momentumStreamRelease η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2) x₀
    (momentumFiniteInnovation ((fun _ => false), 0) ω) t

theorem momentumRelease_own_time {n d : ℕ} (η β : ℝ) (q : NNReal) (c : ℝ)
    (g : Fin n → MomentumVector d → MomentumVector d)
    (x₀ : MomentumVector d) (t : ℕ)
    (ω : Trajectory.History d (Fin n → Bool) (t + 1)) :
    momentumRelease η β q c g x₀ (t + 1) ω t =
      sampledGradient q c g (momentumState η β q c g x₀ (t + 1) ω t).1
        (ω 0).1 + (ω 0).2 := by
  simp [momentumRelease, momentumStreamRelease, momentumState, momentumFiniteInnovation]

theorem momentumRelease_memLp_two {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (x₀ : MomentumVector d) (T t : ℕ) :
    MemLp (fun ω => momentumRelease η β q c g x₀ T ω t) 2
      (gaussianHistoryLaw n d T q hq1 s) := by
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  exact momentumFiniteLaw_release_memLp_two (maskLaw n q hq1) (gaussianVectorLaw d s)
    (gaussianVectorLaw_memLp d s) (sampledGradient q c g)
    (measurable_sampledGradient q c hc g hg) (c / q)
    (norm_sampledGradient_le hn q c hq hc g) η β x₀ ((fun _ => false), 0) T t

theorem momentumState_full_horizon_pairing {n d : ℕ}
    (hn : 0 < n) (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (x₀ : MomentumVector d) (T t : ℕ) (ht : t < T)
    (G : MomentumVector d → MomentumVector d) (L : ℝ) (hL : 0 ≤ L)
    (hG : ∀ x y, ‖G x - G y‖ ≤ L * ‖x - y‖) :
    (∫ ω, inner ℝ (G (momentumState η β q c g x₀ T ω t).1)
      (momentumRelease η β q c g x₀ T ω t) ∂gaussianHistoryLaw n d T q hq1 s) =
    ∫ ω, inner ℝ (G (momentumState η β q c g x₀ T ω t).1)
      (clippedMean c (fun i => g i (momentumState η β q c g x₀ T ω t).1))
      ∂gaussianHistoryLaw n d T q hq1 s := by
  have hleft := momentumFiniteLaw_integral_state_release
    ((maskLaw n q hq1).prod (gaussianVectorLaw d s)) η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2) x₀
    ((fun _ => false), 0) ht (fun x y => inner ℝ (G x) y)
    (Mf.Optimization.FiniteMemoryAdam.StabilizerBudget.integrable_inner_of_memLp
      (momentumState_gradient_memLp_two hn q hq0 hq1 η β c s hc g hg x₀
        (t + 1) t G L hL hG)
      (momentumRelease_memLp_two hn q hq0 hq1 η β c s hc g hg x₀ (t + 1) t))
  have hm := clippedMean_comp_memLp_two
    (gaussianHistoryLaw n d t q hq1 s) hn c hc g hg
    (fun ω => (momentumState η β q c g x₀ t ω t).1)
    (momentumState_measurable η β q c hc g hg x₀ t t)
  have hright := momentumFiniteLaw_integral_state
    ((maskLaw n q hq1).prod (gaussianVectorLaw d s)) η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2) x₀
    ((fun _ => false), 0) ht.le
    (fun state => inner ℝ (G state.1) (clippedMean c (fun i => g i state.1)))
    (Mf.Optimization.FiniteMemoryAdam.StabilizerBudget.integrable_inner_of_memLp
      (momentumState_gradient_memLp_two hn q hq0 hq1 η β c s hc g hg x₀
        t t G L hL hG) hm)
  change (∫ ω, inner ℝ (G (momentumState η β q c g x₀ T ω t).1)
      (momentumRelease η β q c g x₀ T ω t) ∂gaussianHistoryLaw n d T q hq1 s) =
    ∫ ω, inner ℝ (G (momentumState η β q c g x₀ (t + 1) ω t).1)
      (momentumRelease η β q c g x₀ (t + 1) ω t)
      ∂gaussianHistoryLaw n d (t + 1) q hq1 s at hleft
  rw [hleft]
  simp_rw [momentumRelease_own_time]
  rw [momentumState_own_time_pairing hn q hq0 hq1 η β c s hc g hg x₀ t G L hL hG]
  exact hright.symm

theorem momentumState_full_horizon_energy {n d : ℕ}
    (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → MomentumVector d → MomentumVector d) (hg : ∀ i, Measurable (g i))
    (x₀ : MomentumVector d) (T t : ℕ) (ht : t < T) :
    (∫ ω, ‖momentumRelease η β q c g x₀ T ω t‖ ^ 2
      ∂gaussianHistoryLaw n d T q hq1 s) =
    ∫ ω, ((1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) *
      ‖clippedMean c (fun i => g i (momentumState η β q c g x₀ T ω t).1)‖ ^ 2 +
      ((1 - (q : ℝ)) / ((q : ℝ) * n)) *
        meanSqDeviation
          (fun i => Mf.DP.euclideanBallClip c
            (g i (momentumState η β q c g x₀ T ω t).1))
          (clippedMean c (fun i => g i (momentumState η β q c g x₀ T ω t).1)) + s ^ 2)
      ∂gaussianHistoryLaw n d T q hq1 s := by
  have hleft := momentumFiniteLaw_integral_state_release
    ((maskLaw n q hq1).prod (gaussianVectorLaw d s)) η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2) x₀
    ((fun _ => false), 0) ht (fun _ y => ‖y‖ ^ 2)
    ((momentumRelease_memLp_two hn q hq0 hq1 η β c s hc g hg x₀ (t + 1) t).integrable_norm_pow
      (by norm_num : 2 ≠ 0))
  have hint := clippedEnergy_comp_integrable (gaussianHistoryLaw n d t q hq1 s)
    hn c hc g hg (fun ω => (momentumState η β q c g x₀ t ω t).1)
    (momentumState_measurable η β q c hc g hg x₀ t t)
    (1 + (1 - (q : ℝ)) / ((q : ℝ) * n))
    ((1 - (q : ℝ)) / ((q : ℝ) * n)) s
  have hright := momentumFiniteLaw_integral_state
    ((maskLaw n q hq1).prod (gaussianVectorLaw d s)) η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2) x₀
    ((fun _ => false), 0) ht.le
    (fun state => (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) *
      ‖clippedMean c (fun i => g i state.1)‖ ^ 2 +
      ((1 - (q : ℝ)) / ((q : ℝ) * n)) *
        meanSqDeviation (fun i => Mf.DP.euclideanBallClip c (g i state.1))
          (clippedMean c (fun i => g i state.1)) + s ^ 2) hint
  change (∫ ω, ‖momentumRelease η β q c g x₀ T ω t‖ ^ 2
      ∂gaussianHistoryLaw n d T q hq1 s) =
    ∫ ω, ‖momentumRelease η β q c g x₀ (t + 1) ω t‖ ^ 2
      ∂gaussianHistoryLaw n d (t + 1) q hq1 s at hleft
  rw [hleft]
  simp_rw [momentumRelease_own_time]
  rw [momentumState_own_time_energy hn hd q hq0 hq1 η β c s hc g hg x₀ t]
  exact hright.symm

end
end Mf.Optimization.PoissonClippedSGD
