import Mf.Optimization.PoissonClippedSGD.ClippingBias
import Mf.Optimization.PoissonClippedSGD.FiniteMeans

/-!
# Alignment of the mean clipped gradient

The finite-vector alignment in the restricted Poisson argument retains half
the squared clipped-mean norm. This is the contribution later used to absorb
random batch-size variability. The final theorem derives all bias estimates
from the raw centered variance; its intermediate geometric lemma is private.
See `docs/poisson-clipped-sgd/TARGET.md`, Appendix A.2 correspondence.
-/

namespace Mf.Optimization.PoissonClippedSGD

noncomputable section
open Mf.DP

private theorem alignment_of_clipping_bias {d : ℕ}
    (v mu : EuclideanSpace ℝ (Fin d)) (c sigma : ℝ)
    (hc : 0 < c) (hsigma : 0 ≤ sigma) (hclip : 4 * sigma ≤ c)
    (hproj : ‖mu - euclideanBallClip c v‖ ^ 2 ≤ sigma ^ 2)
    (hsmall : ‖v‖ < c / 2 → ‖mu - v‖ ≤ 2 * sigma ^ 2 / c) :
    (1 / 4 : ℝ) * min (‖v‖ ^ 2) (c * ‖v‖) +
        (1 / 2 : ℝ) * ‖mu‖ ^ 2 - 2 * sigma ^ 4 / c ^ 2 ≤
      inner ℝ v mu := by
  let r : ℝ := ‖v‖
  have hr0 : 0 ≤ r := norm_nonneg _
  have hsigmaSq : sigma ^ 2 ≤ (c / 4) ^ 2 := by
    have : sigma ≤ c / 4 := by linarith
    nlinarith
  have hdistProj : ‖mu - euclideanBallClip c v‖ ≤ sigma := by
    have hn := norm_nonneg (mu - euclideanBallClip c v)
    nlinarith
  have hpolar : ‖mu - v‖ ^ 2 = ‖mu‖ ^ 2 -
      2 * inner ℝ v mu + r ^ 2 := by
    simpa [r, real_inner_comm] using norm_sub_sq_real mu v
  have hreduce : ‖mu - v‖ ^ 2 ≤ r ^ 2 -
      min (r ^ 2) (c * r) / 2 + 4 * sigma ^ 4 / c ^ 2 →
      (1 / 4 : ℝ) * min (r ^ 2) (c * r) +
          (1 / 2 : ℝ) * ‖mu‖ ^ 2 - 2 * sigma ^ 4 / c ^ 2 ≤
        inner ℝ v mu := by
    intro h
    have hi : inner ℝ v mu = (‖mu‖ ^ 2 + r ^ 2 - ‖mu - v‖ ^ 2) / 2 := by
      linarith [hpolar]
    rw [hi]
    field_simp [ne_of_gt hc] at h ⊢
    nlinarith [h]
  change (1 / 4 : ℝ) * min (r ^ 2) (c * r) +
      (1 / 2 : ℝ) * ‖mu‖ ^ 2 - 2 * sigma ^ 4 / c ^ 2 ≤ inner ℝ v mu
  apply hreduce
  by_cases hs : r < c / 2
  · have hmin : min (r ^ 2) (c * r) = r ^ 2 := by
      apply min_eq_left
      nlinarith
    rw [hmin]
    have hb := hsmall hs
    have hsq : (2 * sigma ^ 2 / c) ^ 2 = 4 * sigma ^ 4 / c ^ 2 := by ring
    have hbound : ‖mu - v‖ ^ 2 ≤ 4 * sigma ^ 4 / c ^ 2 := by
      rw [← hsq]
      exact (sq_le_sq₀ (norm_nonneg _) (by positivity)).2 hb
    nlinarith
  · by_cases hm : r < c
    · have hclipv : euclideanBallClip c v = v := by
        simp [euclideanBallClip, show ‖v‖ ≤ c by change r ≤ c; linarith]
      have hmin : min (r ^ 2) (c * r) = r ^ 2 := min_eq_left (by nlinarith)
      rw [hmin]
      rw [hclipv] at hproj
      have hsig : sigma ^ 2 ≤ r ^ 2 / 2 := by nlinarith [hsigmaSq]
      have hdelta : 0 ≤ 4 * sigma ^ 4 / c ^ 2 := by positivity
      nlinarith
    · have hlarge : c ≤ r := le_of_not_gt hm
      have hmin : min (r ^ 2) (c * r) = c * r := min_eq_right (by nlinarith)
      rw [hmin]
      have hradial : ‖v - euclideanBallClip c v‖ = r - c := by
        by_cases heq : r = c
        · have hv : ‖v‖ ≤ c := by change r ≤ c; exact heq.le
          simp [euclideanBallClip, hv, heq]
        · have hlt : c < ‖v‖ := lt_of_le_of_ne hlarge (Ne.symm heq)
          rw [euclideanBallClip, if_neg (not_le_of_gt hlt)]
          rw [show v - (c / ‖v‖) • v = (1 - c / ‖v‖) • v by module,
            norm_smul, Real.norm_eq_abs]
          have hvpos : 0 < ‖v‖ := lt_trans hc hlt
          have hratio : 0 ≤ 1 - c / ‖v‖ := by
            rw [sub_nonneg, div_le_one hvpos]
            exact hlt.le
          rw [abs_of_nonneg hratio]
          field_simp [hvpos.ne']
          dsimp [r]
      have hdist : ‖mu - v‖ ≤ r - c + sigma := by
        calc
          ‖mu - v‖ = ‖(mu - euclideanBallClip c v) +
              (euclideanBallClip c v - v)‖ := by congr 1; abel
          _ ≤ ‖mu - euclideanBallClip c v‖ +
              ‖euclideanBallClip c v - v‖ := norm_add_le _ _
          _ ≤ sigma + (r - c) := by
            rw [norm_sub_rev (euclideanBallClip c v) v, hradial]
            linarith
          _ = r - c + sigma := by ring
      have hdist2 : ‖mu - v‖ ^ 2 ≤ (r - c + sigma) ^ 2 :=
        (sq_le_sq₀ (norm_nonneg _) (by positivity)).2 hdist
      have hsigSq : sigma ^ 2 ≤ c ^ 2 / 16 := by nlinarith [hsigmaSq]
      have hrhs : (r - c + sigma) ^ 2 ≤ r ^ 2 - c * r / 2 := by
        nlinarith [sq_nonneg (r - c), hsigSq]
      have hdelta : 0 ≤ 4 * sigma ^ 4 / c ^ 2 := by positivity
      nlinarith

/-- Raw population variance controls clipped-gradient alignment while retaining
half the squared mean clipped-gradient norm for the Poisson descent step. -/
theorem clippedMean_alignment
    {n d : ℕ} (hn : 0 < n)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (c sigma : ℝ) (hc : 0 < c) (hsigma : 0 ≤ sigma)
    (hclip : 4 * sigma ≤ c)
    (hvariance : meanSqDeviation g (vectorMean g) ≤ sigma ^ 2) :
    (1 / 4 : ℝ) * min (‖vectorMean g‖ ^ 2) (c * ‖vectorMean g‖) +
        (1 / 2 : ℝ) * ‖clippedMean c g‖ ^ 2 - 2 * sigma ^ 4 / c ^ 2 ≤
      inner ℝ (vectorMean g) (clippedMean c g) := by
  apply alignment_of_clipping_bias _ _ c sigma hc hsigma hclip
  · exact (clippedMean_center_distance_sq_le hn c hc.le g).trans hvariance
  · intro hsmall
    exact norm_clippedMean_sub_mean_le_of_small g c sigma hc hsmall hvariance

end

end Mf.Optimization.PoissonClippedSGD
