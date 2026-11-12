import Mf.Optimization.PoissonClippedSGD.NormalizedMoments
import Mf.Optimization.PoissonClippedSGD.NoiseMoments
import Mf.Optimization.PoissonClippedSGD.History

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
/-!
# The concrete Gaussian Poisson-clipped algorithm

The step law is an explicit product of independent Bernoulli masks and
centered Gaussian vectors. All iterates live on one finite product history.
Direction moments and finite iterate moments are derived from these laws.
-/

noncomputable section

instance bernoulliMaskLaw_isProbability (n : ℕ) (q : NNReal) (hq1 : q ≤ 1) :
    IsProbabilityMeasure (maskLaw n q hq1) := maskLaw_isProbability n q hq1

def gaussianStepLaw (n d : ℕ) (q : NNReal) (hq1 : q ≤ 1) (s : ℝ) :
    Measure ((Fin n → Bool) × EuclideanSpace ℝ (Fin d)) :=
  (maskLaw n q hq1).prod (gaussianVectorLaw d s)

instance gaussianStepLaw_isProbability (n d : ℕ) (q : NNReal) (hq1 : q ≤ 1) (s : ℝ) :
    IsProbabilityMeasure (gaussianStepLaw n d q hq1 s) := by
  unfold gaussianStepLaw
  infer_instance

def gaussianHistoryLaw (n d T : ℕ) (q : NNReal) (hq1 : q ≤ 1) (s : ℝ) :=
  Trajectory.historyLaw (gaussianStepLaw n d q hq1 s) T

instance gaussianHistoryLaw_isProbability (n d T : ℕ) (q : NNReal) (hq1 : q ≤ 1) (s : ℝ) :
    IsProbabilityMeasure (gaussianHistoryLaw n d T q hq1 s) := by
  unfold gaussianHistoryLaw Trajectory.historyLaw
  infer_instance

def gaussianRun {n d : ℕ} (eta q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) :=
  Trajectory.run eta (sampledGradient q c g) x0 T

def gaussianIterate {n d : ℕ} (eta q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x0 : EuclideanSpace ℝ (Fin d)) (T t : ℕ) (ht : t ≤ T) :=
  Trajectory.iterateOnHistory eta (sampledGradient q c g) x0 T t ht

theorem gaussianRun_measurable {n d : ℕ} (eta q c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) :
    Measurable (gaussianRun eta q c g x0 T) :=
  Trajectory.run_measurable eta _ x0 (measurable_sampledGradient q c hc g hg) T

theorem gaussianRun_memLp {n d : ℕ} (hn : 0 < n)
    (eta c s : ℝ) (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) :
    MemLp (gaussianRun eta (q:ℝ) c g x0 T) 2 (gaussianHistoryLaw n d T q hq1 s) := by
  have hq : (0:ℝ) < q := by exact_mod_cast hq0
  apply (memLp_two_iff_integrable_sq_norm
    (gaussianRun_measurable eta q c hc g hg x0 T).aestronglyMeasurable).2
  exact (Trajectory.run_normSq_integrable (maskLaw n q hq1) (gaussianVectorLaw d s)
    eta (c/(q:ℝ)) (by positivity) (sampledGradient q c g) x0
    (measurable_sampledGradient q c hc g hg)
    (fun x m => norm_sampledGradient_le hn q c hq hc g x m)
    (gaussianVectorLaw_memLp d s).norm T).2

theorem gaussianIterate_measurable {n d : ℕ} (eta q c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) (x0 : EuclideanSpace ℝ (Fin d))
    (T t : ℕ) (ht : t ≤ T) :
    Measurable (gaussianIterate eta q c g x0 T t ht) := by
  exact (gaussianRun_measurable eta q c hc g hg x0 t).comp
    (by unfold Trajectory.suffixHistory; fun_prop : Measurable (Trajectory.suffixHistory (d := d) (Mask := Fin n → Bool) ht))

theorem gaussianIterate_memLp {n d : ℕ} (hn : 0 < n)
    (eta c s : ℝ) (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) (x0 : EuclideanSpace ℝ (Fin d))
    (T t : ℕ) (ht : t ≤ T) :
    MemLp (gaussianIterate eta (q:ℝ) c g x0 T t ht) 2
      (gaussianHistoryLaw n d T q hq1 s) :=
  (gaussianRun_memLp hn eta c s q hq0 hq1 hc g hg x0 t).comp_measurePreserving
    (Trajectory.suffixHistory_measurePreserving (gaussianStepLaw n d q hq1 s) ht)

theorem gaussian_direction_memLp {n d : ℕ} (q : NNReal) (hq1 : q ≤ 1) (c s : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    MemLp (fun p : (Fin n → Bool) × EuclideanSpace ℝ (Fin d) =>
      sampledGradient q c g x p.1 + p.2) 2 (gaussianStepLaw n d q hq1 s) :=
  independent_direction_memLp (maskLaw n q hq1) (gaussianVectorLaw d s)
    (sampledGradient q c g x) (gaussianVectorLaw_memLp d s)

theorem gaussian_direction_mean {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1) (c s : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    (∫ p, sampledGradient q c g x p.1 + p.2 ∂gaussianStepLaw n d q hq1 s) =
      clippedMean c (fun i => g i x) := by
  rw [gaussianStepLaw, independent_direction_mean _ _ _
    (gaussianVectorLaw_memLp d s) (gaussianVectorLaw_mean d s)]
  exact integral_sampledGradient q hq1 hq0 hn c g x

theorem gaussian_direction_energy {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1) (c s : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) :
    (∫ p, ‖sampledGradient q c g x p.1 + p.2‖ ^ 2 ∂gaussianStepLaw n d q hq1 s) =
      (1+(1-(q:ℝ))/((q:ℝ)*n)) * ‖clippedMean c (fun i => g i x)‖^2 +
      ((1-(q:ℝ))/((q:ℝ)*n)) * meanSqDeviation
        (fun i => Mf.DP.euclideanBallClip c (g i x)) (clippedMean c (fun i => g i x)) + s^2 := by
  rw [gaussianStepLaw, independent_direction_energy _ _ _
    (gaussianVectorLaw_memLp d s) (gaussianVectorLaw_mean d s), gaussianVectorLaw_energy hd s]
  rw [integral_norm_sq_sampledGradient q hq1 hq0 hn]

end
end Mf.Optimization.PoissonClippedSGD
