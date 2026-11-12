import Mf.Optimization.PoissonClippedSGD.Basic

/-!
# The per-record clipped and normalized update

Each Boolean coordinate selects a record independently in the sampling law.
This owner defines the deterministic map applied to a mask and noise vector.
The normalizer is qn, including for empty masks, and eta multiplies the sum of
the sampled gradient and post-averaging Gaussian noise.
-/

namespace Mf.Optimization.PoissonClippedSGD

noncomputable section
open scoped BigOperators

/-- Per-record clipping followed by deterministic expected-batch normalization. -/
def sampledGradient {n d : ℕ} (q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) (mask : Fin n → Bool) :
    EuclideanSpace ℝ (Fin d) :=
  (q * (n : ℝ))⁻¹ • ∑ i, if mask i then Mf.DP.euclideanBallClip c (g i x) else 0

/-- Noise is in gradient units, inside the learning-rate multiplication. -/
def sampledUpdate {n d : ℕ} (eta q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d))
    (sample : (Fin n → Bool) × EuclideanSpace ℝ (Fin d)) :
    EuclideanSpace ℝ (Fin d) :=
  x - eta • (sampledGradient q c g x sample.1 + sample.2)

/-- Sampling never makes the normalized clipped vector larger than c/q. -/
theorem norm_sampledGradient_le {n d : ℕ} (hn : 0 < n)
    (q c : ℝ) (hq : 0 < q) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) (mask : Fin n → Bool) :
    ‖sampledGradient q c g x mask‖ ≤ c / q := by
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  rw [sampledGradient, norm_smul, Real.norm_eq_abs, abs_of_nonneg (by positivity)]
  calc
    _ ≤ (q * (n : ℝ))⁻¹ * ∑ i, ‖if mask i then Mf.DP.euclideanBallClip c (g i x) else 0‖ :=
      mul_le_mul_of_nonneg_left (norm_sum_le _ _) (by positivity)
    _ ≤ (q * (n : ℝ))⁻¹ * ∑ _i : Fin n, c := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      apply Finset.sum_le_sum
      intro i _
      split_ifs
      · exact Mf.DP.euclideanBallClip_mem_closedBall c hc _
      · simpa using hc
    _ = c / q := by
      simp only [Finset.sum_const, Finset.card_fin, nsmul_eq_mul]
      field_simp

theorem measurable_sampledGradient {n d : ℕ} (q c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) :
    Measurable (fun p : EuclideanSpace ℝ (Fin d) × (Fin n → Bool) =>
      sampledGradient q c g p.1 p.2) := by
  have hclip : Measurable (Mf.DP.euclideanBallClip (ι := Fin d) c) :=
    (Mf.DP.continuous_euclideanBallClip_comp continuous_const continuous_id
      (fun _ => hc)).measurable
  unfold sampledGradient
  have hsum : Measurable (fun p : EuclideanSpace ℝ (Fin d) × (Fin n → Bool) =>
      ∑ i, if p.2 i then Mf.DP.euclideanBallClip c (g i p.1) else 0) := by
    apply Finset.measurable_sum
    intro i _
    exact Measurable.ite
      (measurableSet_eq_fun ((measurable_pi_apply i).comp measurable_snd) measurable_const)
      (hclip.comp ((hg i).comp measurable_fst)) measurable_const
  exact hsum.const_smul ((q * (n : ℝ))⁻¹)

theorem measurable_sampledUpdate {n d : ℕ} (eta q c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) :
    Measurable (fun p : EuclideanSpace ℝ (Fin d) ×
        ((Fin n → Bool) × EuclideanSpace ℝ (Fin d)) =>
      sampledUpdate eta q c g p.1 p.2) := by
  have hsample : Measurable (fun p : EuclideanSpace ℝ (Fin d) ×
      ((Fin n → Bool) × EuclideanSpace ℝ (Fin d)) =>
      sampledGradient q c g p.1 p.2.1) :=
    (measurable_sampledGradient q c hc g hg).comp
      (measurable_fst.prodMk measurable_snd.fst)
  exact measurable_fst.sub ((hsample.add measurable_snd.snd).const_smul eta)

end

end Mf.Optimization.PoissonClippedSGD
