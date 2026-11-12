import Mf.Optimization.PoissonClippedSGD.FiniteMeans

/-!
# Cocoercivity of finite clipped means with common scalar curvature

The projection variational inequality yields firm nonexpansiveness of the
actual radial clipping map. Averaging preserves cocoercivity when every raw
record has the same scalar Hessian. This applies globally through clipping
transitions, without a lower clipping-gain assumption.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open Mf.DP
open scoped BigOperators

/-- Firm nonexpansiveness derived directly from the maintained projection
variational inequality. -/
theorem euclideanBallClip_firm_nonexpansive {d : ℕ}
    (c : ℝ) (hc : 0 ≤ c) (u v : EuclideanSpace ℝ (Fin d)) :
    inner ℝ (euclideanBallClip c u - euclideanBallClip c v) (u - v) ≥
      ‖euclideanBallClip c u - euclideanBallClip c v‖ ^ 2 := by
  let pu := euclideanBallClip c u
  let pv := euclideanBallClip c v
  have hpu := euclideanBallClip_mem_closedBall c hc u
  have hpv := euclideanBallClip_mem_closedBall c hc v
  have hu := real_inner_sub_euclideanBallClip_clip_sub_nonpos c hc u pv hpv
  have hv := real_inner_sub_euclideanBallClip_clip_sub_nonpos c hc v pu hpu
  change inner ℝ (u - pu) (pv - pu) ≤ 0 at hu
  change inner ℝ (v - pv) (pu - pv) ≤ 0 at hv
  have hu' : 0 ≤ inner ℝ (pu - pv) (u - pu) := by
    rw [real_inner_comm]
    have h := hu
    rw [show pv - pu = -(pu - pv) by abel, inner_neg_right] at h
    linarith
  have hv' : inner ℝ (pu - pv) (v - pv) ≤ 0 := by
    rw [real_inner_comm]
    exact hv
  have hdecomp : u - v = (pu - pv) + (u - pu) - (v - pv) := by abel
  have hcalc : inner ℝ (pu - pv) (u - v) =
      ‖pu - pv‖ ^ 2 + inner ℝ (pu - pv) (u - pu) -
        inner ℝ (pu - pv) (v - pv) := by
    rw [hdecomp, inner_sub_right, inner_add_right,
      real_inner_self_eq_norm_sq]
  change inner ℝ (pu - pv) (u - v) ≥ ‖pu - pv‖ ^ 2
  rw [hcalc]
  linarith

/-- The finite clipped mean of common-curvature affine records is cocoercive. -/
theorem clippedMean_affine_scaled_cocoercive {n d : ℕ} (hn : 0 < n)
    (L c : ℝ) (hc : 0 ≤ c)
    (a : Fin n → EuclideanSpace ℝ (Fin d)) (x y : EuclideanSpace ℝ (Fin d)) :
    ‖clippedMean c (fun i => L • x + a i) -
        clippedMean c (fun i => L • y + a i)‖ ^ 2 ≤
      L * inner ℝ (x - y)
        (clippedMean c (fun i => L • x + a i) -
          clippedMean c (fun i => L • y + a i)) := by
  let delta := fun i => euclideanBallClip c (L • x + a i) -
    euclideanBallClip c (L • y + a i)
  have hpoint (i : Fin n) : ‖delta i‖ ^ 2 ≤ L * inner ℝ (x-y) (delta i) := by
    have hp := euclideanBallClip_firm_nonexpansive c hc (L • x + a i) (L • y + a i)
    have he : (L • x + a i) - (L • y + a i) = L • (x-y) := by module
    rw [he, real_inner_smul_right] at hp
    simpa only [delta, real_inner_comm] using hp
  have hmean : clippedMean c (fun i => L • x + a i) -
      clippedMean c (fun i => L • y + a i) = vectorMean delta := by
    exact (vectorMean_sub _ _).symm
  rw [hmean]
  calc
    ‖vectorMean delta‖ ^ 2 ≤ (n : ℝ)⁻¹ * ∑ i, ‖delta i‖ ^ 2 :=
      norm_vectorMean_sq_le hn delta
    _ ≤ (n : ℝ)⁻¹ * ∑ i, L * inner ℝ (x-y) (delta i) := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      exact Finset.sum_le_sum (fun i _ => hpoint i)
    _ = L * inner ℝ (x-y) (vectorMean delta) := by
      simp only [vectorMean, real_inner_smul_right, inner_sum, ← Finset.mul_sum]
      ring

/-- Record-difference form avoids rewriting entire finite record functions. -/
theorem clippedMean_cocoercive_of_record_difference {n d : ℕ} (hn : 0 < n)
    (L c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x y : EuclideanSpace ℝ (Fin d))
    (hdiff : ∀ i, g i x - g i y = L • (x-y)) :
    ‖clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)‖ ^ 2 ≤
      L * inner ℝ (x-y) (clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y)) := by
  let delta := fun i => euclideanBallClip c (g i x) - euclideanBallClip c (g i y)
  have hpoint (i : Fin n) : ‖delta i‖ ^ 2 ≤ L * inner ℝ (x-y) (delta i) := by
    have hp := euclideanBallClip_firm_nonexpansive c hc (g i x) (g i y)
    rw [hdiff i, real_inner_smul_right] at hp
    simpa only [delta, real_inner_comm] using hp
  have hmean : clippedMean c (fun i => g i x) - clippedMean c (fun i => g i y) =
      vectorMean delta := (vectorMean_sub _ _).symm
  rw [hmean]
  calc
    ‖vectorMean delta‖ ^ 2 ≤ (n:ℝ)⁻¹ * ∑ i, ‖delta i‖ ^ 2 := norm_vectorMean_sq_le hn delta
    _ ≤ (n:ℝ)⁻¹ * ∑ i, L * inner ℝ (x-y) (delta i) := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      exact Finset.sum_le_sum (fun i _ => hpoint i)
    _ = L * inner ℝ (x-y) (vectorMean delta) := by
      simp only [vectorMean, real_inner_smul_right, inner_sum, ← Finset.mul_sum]
      ring

/-- The usual divided form for strictly positive common scalar curvature. -/
theorem clippedMean_affine_cocoercive {n d : ℕ} (hn : 0 < n)
    (L c : ℝ) (hL : 0 < L) (hc : 0 ≤ c)
    (a : Fin n → EuclideanSpace ℝ (Fin d)) (x y : EuclideanSpace ℝ (Fin d)) :
    ‖clippedMean c (fun i => L • x + a i) -
        clippedMean c (fun i => L • y + a i)‖ ^ 2 / L ≤
      inner ℝ (x - y) (clippedMean c (fun i => L • x + a i) -
        clippedMean c (fun i => L • y + a i)) := by
  apply (div_le_iff₀ hL).2
  simpa only [mul_comm] using clippedMean_affine_scaled_cocoercive hn L c hc a x y

end Mf.Optimization.PoissonClippedSGD
