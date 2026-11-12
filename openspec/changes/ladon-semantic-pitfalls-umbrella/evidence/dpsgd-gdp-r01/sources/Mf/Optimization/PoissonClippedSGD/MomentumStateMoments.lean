import Mf.Optimization.PoissonClippedSGD.MomentumFreshPairing
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumFiniteLaw

/-!
# L² corrected-momentum state on Poisson/Gaussian histories

The sampled-gradient query keeps its public expected-batch-size denominator,
including for an empty mask. The zero fallback only totalizes the stream after
the finite history ends.
-/

namespace Mf.Optimization.PoissonClippedSGD

open MeasureTheory
open Mf.Optimization.FiniteMemoryAdam.CorrectedColumns
noncomputable section

def momentumState {n d : ℕ} (η β q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x₀ : EuclideanSpace ℝ (Fin d)) (T : ℕ)
    (ω : Trajectory.History d (Fin n → Bool) T) (t : ℕ) :
    EuclideanSpace ℝ (Fin d) × EuclideanSpace ℝ (Fin d) :=
  momentumStreamRun η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2) x₀
    (momentumFiniteInnovation ((fun _ => false), 0) ω) t

/-- Every finite initialized position and raw first memory is L² under the
actual Poisson/Gaussian product-history law. -/
theorem momentumState_memLp_two {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (x₀ : EuclideanSpace ℝ (Fin d)) (T t : ℕ) :
    MemLp (fun ω : Trajectory.History d (Fin n → Bool) T =>
      (momentumState η β q c g x₀ T ω t).1) 2
      (gaussianHistoryLaw n d T q hq1 s) ∧
    MemLp (fun ω : Trajectory.History d (Fin n → Bool) T =>
      (momentumState η β q c g x₀ T ω t).2) 2
      (gaussianHistoryLaw n d T q hq1 s) := by
  change MemLp _ 2 (Measure.pi (fun _ : Fin T => (maskLaw n q hq1).prod (gaussianVectorLaw d s))) ∧
    MemLp _ 2 (Measure.pi (fun _ : Fin T => (maskLaw n q hq1).prod (gaussianVectorLaw d s)))
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  exact momentumFiniteLaw_memLp_two (maskLaw n q hq1)
    (gaussianVectorLaw d s) (gaussianVectorLaw_memLp d s)
    (sampledGradient q c g) (measurable_sampledGradient q c hc g hg)
    (c / q) (norm_sampledGradient_le hn q c hq hc g)
    η β x₀ ((fun _ => false), 0) T t

/-- Globally Lipschitz true gradients of the Poisson momentum state are L²
under the same finite product law. -/
theorem momentumState_gradient_memLp_two {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (x₀ : EuclideanSpace ℝ (Fin d)) (T t : ℕ)
    (G : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (L : ℝ) (hL : 0 ≤ L)
    (hG : ∀ x y, ‖G x - G y‖ ≤ L * ‖x - y‖) :
    MemLp (fun ω : Trajectory.History d (Fin n → Bool) T =>
      G (momentumState η β q c g x₀ T ω t).1) 2
      (gaussianHistoryLaw n d T q hq1 s) := by
  change MemLp _ 2
    (Measure.pi (fun _ : Fin T => (maskLaw n q hq1).prod (gaussianVectorLaw d s)))
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  exact momentumFiniteLaw_gradient_memLp_two (maskLaw n q hq1)
    (gaussianVectorLaw d s) (gaussianVectorLaw_memLp d s)
    (sampledGradient q c g) (measurable_sampledGradient q c hc g hg)
    (c / q) (norm_sampledGradient_le hn q c hq hc g)
    η β x₀ ((fun _ => false), 0) T t G L hL hG

/-- The pre-update state on a full `t+1` history equals the state on its
independent prior tail. -/
theorem momentumState_fresh_split {n d : ℕ}
    (η β q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x₀ : EuclideanSpace ℝ (Fin d)) (t : ℕ)
    (ω : Trajectory.History d (Fin n → Bool) (t + 1)) :
    (momentumState η β q c g x₀ (t + 1) ω t).1 =
      (momentumState η β q c g x₀ t (Fin.tail ω) t).1 := by
  unfold momentumState
  rw [momentumStreamRun_on_past η β
    (fun x sample => sampledGradient q c g x sample.1 + sample.2)
    x₀ ((fun _ => false), 0) (Nat.le_succ t) ω,
    momentumPastHistory_succ_tail]

/-- Measurability of the Poisson corrected-momentum position. -/
theorem momentumState_measurable {n d : ℕ}
    (η β q c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (x₀ : EuclideanSpace ℝ (Fin d)) (T t : ℕ) :
    Measurable (fun ω : Trajectory.History d (Fin n → Bool) T =>
      (momentumState η β q c g x₀ T ω t).1) := by
  exact momentumFiniteLaw_state_measurable (sampledGradient q c g)
    (measurable_sampledGradient q c hc g hg)
    η β x₀ ((fun _ => false), 0) T t

/-- Actual own-time fresh centering for the zero-start corrected-momentum
Poisson process, including Gaussian noise on empty-mask releases. -/
theorem momentumState_own_time_pairing {n d : ℕ}
    (hn : 0 < n) (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (x₀ : EuclideanSpace ℝ (Fin d)) (t : ℕ)
    (G : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (L : ℝ) (hL : 0 ≤ L)
    (hG : ∀ x y, ‖G x - G y‖ ≤ L * ‖x - y‖) :
    (∫ ω : Trajectory.History d (Fin n → Bool) (t + 1),
      inner ℝ (G (momentumState η β q c g x₀ (t + 1) ω t).1)
        (sampledGradient q c g (momentumState η β q c g x₀ (t + 1) ω t).1
          (ω 0).1 + (ω 0).2)
      ∂gaussianHistoryLaw n d (t + 1) q hq1 s) =
    ∫ past : Trajectory.History d (Fin n → Bool) t,
      inner ℝ (G (momentumState η β q c g x₀ t past t).1)
        (clippedMean c (fun i => g i (momentumState η β q c g x₀ t past t).1))
      ∂gaussianHistoryLaw n d t q hq1 s := by
  let X : Trajectory.History d (Fin n → Bool) t → EuclideanSpace ℝ (Fin d) :=
    fun past => (momentumState η β q c g x₀ t past t).1
  have hX : Measurable X := momentumState_measurable η β q c hc g hg x₀ t t
  have hGm : MemLp (fun past => G (X past)) 2
      (gaussianHistoryLaw n d t q hq1 s) :=
    momentumState_gradient_memLp_two hn q hq0 hq1 η β c s hc g hg
      x₀ t t G L hL hG
  have hpair := momentum_fresh_pairing_of_memLp hn q hq0 hq1 c s hc g hg
    G t X hX hGm
  have heq :
      (∫ ω : Trajectory.History d (Fin n → Bool) (t + 1),
        inner ℝ (G (momentumState η β q c g x₀ (t + 1) ω t).1)
          (sampledGradient q c g (momentumState η β q c g x₀ (t + 1) ω t).1
            (ω 0).1 + (ω 0).2)
        ∂gaussianHistoryLaw n d (t + 1) q hq1 s) =
      (∫ ω : Trajectory.History d (Fin n → Bool) (t + 1),
        inner ℝ (G (X (Fin.tail ω)))
          (sampledGradient q c g (X (Fin.tail ω)) (ω 0).1 + (ω 0).2)
        ∂gaussianHistoryLaw n d (t + 1) q hq1 s) := by
    apply integral_congr_ae
    exact ae_of_all _ (fun ω => by
      change inner ℝ (G (momentumState η β q c g x₀ (t + 1) ω t).1)
        (sampledGradient q c g (momentumState η β q c g x₀ (t + 1) ω t).1
          (ω 0).1 + (ω 0).2) =
        inner ℝ (G (momentumState η β q c g x₀ t (Fin.tail ω) t).1)
          (sampledGradient q c g (momentumState η β q c g x₀ t (Fin.tail ω) t).1
            (ω 0).1 + (ω 0).2)
      rw [momentumState_fresh_split η β q c g x₀ t ω])
  exact heq.trans hpair

/-- Exact own-time release energy for the Poisson corrected-momentum
process, retaining random total-count variance. -/
theorem momentumState_own_time_energy {n d : ℕ}
    (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (η β c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (x₀ : EuclideanSpace ℝ (Fin d)) (t : ℕ) :
    (∫ ω : Trajectory.History d (Fin n → Bool) (t + 1),
      ‖sampledGradient q c g
        (momentumState η β q c g x₀ (t + 1) ω t).1
        (ω 0).1 + (ω 0).2‖ ^ 2
      ∂gaussianHistoryLaw n d (t + 1) q hq1 s) =
    ∫ past : Trajectory.History d (Fin n → Bool) t,
      ((1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) *
        ‖clippedMean c
          (fun i => g i (momentumState η β q c g x₀ t past t).1)‖ ^ 2 +
        ((1 - (q : ℝ)) / ((q : ℝ) * n)) *
          meanSqDeviation
            (fun i => Mf.DP.euclideanBallClip c
              (g i (momentumState η β q c g x₀ t past t).1))
            (clippedMean c
              (fun i => g i (momentumState η β q c g x₀ t past t).1)) + s ^ 2)
      ∂gaussianHistoryLaw n d t q hq1 s := by
  let X : Trajectory.History d (Fin n → Bool) t → EuclideanSpace ℝ (Fin d) :=
    fun past => (momentumState η β q c g x₀ t past t).1
  have hX : Measurable X := momentumState_measurable η β q c hc g hg x₀ t t
  have henergy := momentum_fresh_energy_of_measurable hn hd q hq0 hq1 c s hc
    g hg t X hX
  have heq :
      (∫ ω : Trajectory.History d (Fin n → Bool) (t + 1),
        ‖sampledGradient q c g
          (momentumState η β q c g x₀ (t + 1) ω t).1
          (ω 0).1 + (ω 0).2‖ ^ 2
        ∂gaussianHistoryLaw n d (t + 1) q hq1 s) =
      (∫ ω : Trajectory.History d (Fin n → Bool) (t + 1),
        ‖sampledGradient q c g (X (Fin.tail ω))
          (ω 0).1 + (ω 0).2‖ ^ 2
        ∂gaussianHistoryLaw n d (t + 1) q hq1 s) := by
    apply integral_congr_ae
    exact ae_of_all _ (fun ω => by
      change ‖sampledGradient q c g
        (momentumState η β q c g x₀ (t + 1) ω t).1
        (ω 0).1 + (ω 0).2‖ ^ 2 =
        ‖sampledGradient q c g
          (momentumState η β q c g x₀ t (Fin.tail ω) t).1
          (ω 0).1 + (ω 0).2‖ ^ 2
      rw [momentumState_fresh_split η β q c g x₀ t ω])
  exact heq.trans henergy

end
end Mf.Optimization.PoissonClippedSGD
