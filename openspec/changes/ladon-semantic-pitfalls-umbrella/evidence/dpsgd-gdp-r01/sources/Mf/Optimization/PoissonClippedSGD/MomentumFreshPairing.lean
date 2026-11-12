import Mf.Optimization.PoissonClippedSGD.Algorithm
import Mf.Optimization.FiniteMemoryAdam.AdaptedReleaseIntegrability

/-!
# Fresh Poisson pairing for a carried-memory process

The previous state may depend on the entire prior history. The fresh
Bernoulli mask and Gaussian are independent of it, including when the sampled
batch is empty. The query is always normalized by the public expected batch
size already encoded in `sampledGradient`.
-/

namespace Mf.Optimization.PoissonClippedSGD

open MeasureTheory
noncomputable section

/-- Own-time fresh centering on the exact Poisson/Gaussian product history.
Product-law integrability remains a premise until the concrete corrected-
momentum process is connected. -/
theorem momentum_fresh_pairing
    {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (c s : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (G : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (T : ℕ)
    (X : Trajectory.History d (Fin n → Bool) T → EuclideanSpace ℝ (Fin d))
    (hPair : Integrable
      (fun p : Trajectory.Step d (Fin n → Bool) ×
          Trajectory.History d (Fin n → Bool) T =>
        inner ℝ (G (X p.2))
          (sampledGradient q c g (X p.2) p.1.1 + p.1.2))
      ((gaussianStepLaw n d q hq1 s).prod
        (gaussianHistoryLaw n d T q hq1 s))) :
    (∫ ω : Trajectory.History d (Fin n → Bool) (T + 1),
      inner ℝ (G (X (Fin.tail ω)))
        (sampledGradient q c g (X (Fin.tail ω)) (ω 0).1 + (ω 0).2)
      ∂gaussianHistoryLaw n d (T + 1) q hq1 s) =
    ∫ past : Trajectory.History d (Fin n → Bool) T,
      inner ℝ (G (X past)) (clippedMean c (fun i => g i (X past)))
      ∂gaussianHistoryLaw n d T q hq1 s := by
  let ν := gaussianStepLaw n d q hq1 s
  let μ := gaussianHistoryLaw n d T q hq1 s
  let Φ : Trajectory.Step d (Fin n → Bool) ×
      Trajectory.History d (Fin n → Bool) T → ℝ :=
    fun p => inner ℝ (G (X p.2))
      (sampledGradient q c g (X p.2) p.1.1 + p.1.2)
  have hsplit := Trajectory.history_split (d := d) (Mask := Fin n → Bool) ν T
  have htransport :
      (∫ ω : Trajectory.History d (Fin n → Bool) (T + 1),
        Φ (ω 0, Fin.tail ω) ∂gaussianHistoryLaw n d (T + 1) q hq1 s) =
      ∫ p, Φ p ∂ν.prod μ := by
    exact hsplit.integral_comp
      (Trajectory.history_split_measurableEmbedding
        (d := d) (Mask := Fin n → Bool) T) Φ
  have hpoint (past : Trajectory.History d (Fin n → Bool) T) :
      (∫ sample : Trajectory.Step d (Fin n → Bool),
        inner ℝ (G (X past))
          (sampledGradient q c g (X past) sample.1 + sample.2) ∂ν) =
      inner ℝ (G (X past)) (clippedMean c (fun i => g i (X past))) := by
    have hY : Integrable
        (fun sample : Trajectory.Step d (Fin n → Bool) =>
          sampledGradient q c g (X past) sample.1 + sample.2) ν :=
      (gaussian_direction_memLp q hq1 c s g (X past)).integrable (by norm_num)
    rw [integral_inner hY,
      gaussian_direction_mean hn q hq0 hq1 c s g (X past)]
  calc
    _ = ∫ p, Φ p ∂ν.prod μ := htransport
    _ = ∫ past, ∫ sample, Φ (sample, past) ∂ν ∂μ :=
      integral_prod_symm _ hPair
    _ = _ := by
      apply integral_congr_ae
      exact ae_of_all _ hpoint

/-- Fresh Poisson centering with pairing integrability generated from L² of
the predictable gradient and measurability of its state. -/
theorem momentum_fresh_pairing_of_memLp
    {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (G : EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (T : ℕ)
    (X : Trajectory.History d (Fin n → Bool) T → EuclideanSpace ℝ (Fin d))
    (hX : Measurable X)
    (hG : MemLp (fun past => G (X past)) 2
      (gaussianHistoryLaw n d T q hq1 s)) :
    (∫ ω : Trajectory.History d (Fin n → Bool) (T + 1),
      inner ℝ (G (X (Fin.tail ω)))
        (sampledGradient q c g (X (Fin.tail ω)) (ω 0).1 + (ω 0).2)
      ∂gaussianHistoryLaw n d (T + 1) q hq1 s) =
    ∫ past : Trajectory.History d (Fin n → Bool) T,
      inner ℝ (G (X past)) (clippedMean c (fun i => g i (X past)))
      ∂gaussianHistoryLaw n d T q hq1 s := by
  apply momentum_fresh_pairing hn q hq0 hq1 c s g G T X
  change Integrable
    (fun p : Trajectory.Step d (Fin n → Bool) ×
        Trajectory.History d (Fin n → Bool) T =>
      inner ℝ (G (X p.2))
        (sampledGradient q c g (X p.2) p.1.1 + p.1.2))
    (((maskLaw n q hq1).prod (gaussianVectorLaw d s)).prod
      (gaussianHistoryLaw n d T q hq1 s))
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  exact Mf.Optimization.FiniteMemoryAdam.adapted_release_pair_integrable
    (maskLaw n q hq1) (gaussianVectorLaw d s)
    (gaussianHistoryLaw n d T q hq1 s)
    (gaussianVectorLaw_memLp d s) (sampledGradient q c g)
    (measurable_sampledGradient q c hc g hg) (c / q)
    (norm_sampledGradient_le hn q c hq hc g) X hX
    (fun past => G (X past)) hG

/-- Exact release energy after a fresh Poisson mask and Gaussian. The
count-fluctuation coefficient on the clipped mean is retained. -/
theorem momentum_fresh_energy
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (c s : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (T : ℕ)
    (X : Trajectory.History d (Fin n → Bool) T → EuclideanSpace ℝ (Fin d))
    (hEnergy : Integrable
      (fun p : Trajectory.Step d (Fin n → Bool) ×
          Trajectory.History d (Fin n → Bool) T =>
        ‖sampledGradient q c g (X p.2) p.1.1 + p.1.2‖ ^ 2)
      ((gaussianStepLaw n d q hq1 s).prod
        (gaussianHistoryLaw n d T q hq1 s))) :
    (∫ ω : Trajectory.History d (Fin n → Bool) (T + 1),
      ‖sampledGradient q c g (X (Fin.tail ω)) (ω 0).1 + (ω 0).2‖ ^ 2
      ∂gaussianHistoryLaw n d (T + 1) q hq1 s) =
    ∫ past : Trajectory.History d (Fin n → Bool) T,
      ((1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) *
        ‖clippedMean c (fun i => g i (X past))‖ ^ 2 +
        ((1 - (q : ℝ)) / ((q : ℝ) * n)) *
          meanSqDeviation
            (fun i => Mf.DP.euclideanBallClip c (g i (X past)))
            (clippedMean c (fun i => g i (X past))) + s ^ 2)
      ∂gaussianHistoryLaw n d T q hq1 s := by
  let ν := gaussianStepLaw n d q hq1 s
  let μ := gaussianHistoryLaw n d T q hq1 s
  let Φ : Trajectory.Step d (Fin n → Bool) ×
      Trajectory.History d (Fin n → Bool) T → ℝ :=
    fun p => ‖sampledGradient q c g (X p.2) p.1.1 + p.1.2‖ ^ 2
  have hsplit := Trajectory.history_split (d := d) (Mask := Fin n → Bool) ν T
  have htransport :
      (∫ ω : Trajectory.History d (Fin n → Bool) (T + 1),
        Φ (ω 0, Fin.tail ω) ∂gaussianHistoryLaw n d (T + 1) q hq1 s) =
      ∫ p, Φ p ∂ν.prod μ := by
    exact hsplit.integral_comp
      (Trajectory.history_split_measurableEmbedding
        (d := d) (Mask := Fin n → Bool) T) Φ
  calc
    _ = ∫ p, Φ p ∂ν.prod μ := htransport
    _ = ∫ past, ∫ sample, Φ (sample, past) ∂ν ∂μ :=
      integral_prod_symm _ hEnergy
    _ = _ := by
      apply integral_congr_ae
      exact ae_of_all _ (fun past =>
        gaussian_direction_energy hn hd q hq0 hq1 c s g (X past))

/-- The exact adapted Poisson energy identity with integrability generated
from a measurable clipped query and the Gaussian L² law. -/
theorem momentum_fresh_energy_of_measurable
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (c s : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (T : ℕ)
    (X : Trajectory.History d (Fin n → Bool) T → EuclideanSpace ℝ (Fin d))
    (hX : Measurable X) :
    (∫ ω : Trajectory.History d (Fin n → Bool) (T + 1),
      ‖sampledGradient q c g (X (Fin.tail ω)) (ω 0).1 + (ω 0).2‖ ^ 2
      ∂gaussianHistoryLaw n d (T + 1) q hq1 s) =
    ∫ past : Trajectory.History d (Fin n → Bool) T,
      ((1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) *
        ‖clippedMean c (fun i => g i (X past))‖ ^ 2 +
        ((1 - (q : ℝ)) / ((q : ℝ) * n)) *
          meanSqDeviation
            (fun i => Mf.DP.euclideanBallClip c (g i (X past)))
            (clippedMean c (fun i => g i (X past))) + s ^ 2)
      ∂gaussianHistoryLaw n d T q hq1 s := by
  apply momentum_fresh_energy hn hd q hq0 hq1 c s g T X
  change Integrable
    (fun p : Trajectory.Step d (Fin n → Bool) ×
        Trajectory.History d (Fin n → Bool) T =>
      ‖sampledGradient q c g (X p.2) p.1.1 + p.1.2‖ ^ 2)
    (((maskLaw n q hq1).prod (gaussianVectorLaw d s)).prod
      (gaussianHistoryLaw n d T q hq1 s))
  have hq : (0 : ℝ) < q := by exact_mod_cast hq0
  exact Mf.Optimization.FiniteMemoryAdam.adapted_release_energy_integrable
    (maskLaw n q hq1) (gaussianVectorLaw d s)
    (gaussianHistoryLaw n d T q hq1 s)
    (gaussianVectorLaw_memLp d s) (sampledGradient q c g)
    (measurable_sampledGradient q c hc g hg) (c / q)
    (norm_sampledGradient_le hn q c hq hc g) X hX

end
end Mf.Optimization.PoissonClippedSGD
