import Mf.Optimization.PoissonClippedSGD.Algorithm
import Mf.Optimization.SDE.DPAdamEuclideanAveragedReleaseMechanism

/-!
# Exact normalization of the noisy clipped sum

A raw clipped-sum noise coordinate has standard deviation C nu. Dividing by
the public expected batch qN gives the existing SGD Gaussian law with total
scale C sqrt(d) nu/(qN). The identities here concern complete laws and the
actual Euclidean clipping map, rather than only their second moments.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory ProbabilityTheory
noncomputable section

/-- Total Gaussian scale corresponding to clipped-sum multiplier nu. -/
def normalizedSumNoise (n d : ℕ) (q c nu : ℝ) : ℝ :=
  c * Real.sqrt (d : ℝ) / (q * n) * nu

theorem averaged_gaussian_coordinate_law (n d : ℕ) (q c nu : ℝ) (hd : 0 < d) :
    (SDE.centeredGaussianVectorLaw (Coord := Fin d)
      (SDE.standardClippingVariance c nu)).map (SDE.averageRelease (q * n)) =
      gaussianCoordinateLaw d (normalizedSumNoise n d q c nu) := by
  unfold SDE.centeredGaussianVectorLaw gaussianCoordinateLaw
    Mf.Probability.FiniteProductGaussian.law SDE.averageRelease
  rw [Measure.pi_map_pi (f := fun (_ : Fin d) (y : ℝ) => y / (q * n))
    (hf := fun _ => (measurable_id.div_const _).aemeasurable)]
  congr 1
  funext i
  rw [ProbabilityTheory.gaussianReal_map_div_const]
  simp only [zero_div]
  congr 1
  apply Subtype.ext
  change (nu * c) ^ 2 / (q * n) ^ 2 =
    (normalizedSumNoise n d q c nu / Real.sqrt (d : ℝ)) ^ 2
  rw [normalizedSumNoise, normalized_noise_coordinate_scale n d q c nu hd]
  ring

/-- Restricted gradients keep public population normalization on every dataset. -/
def restrictedGradient {n d : ℕ}
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (A : Finset (Fin n)) : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d) :=
  fun i x => if i ∈ A then g i x else 0

theorem normalized_clipped_sum_eq_sampledGradient {n d : ℕ} (q c : ℝ)
    (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (A : Finset (Fin n)) (x : EuclideanSpace ℝ (Fin d)) (mask : Fin n → Bool) :
    Mf.DP.toEuclidean (SDE.averageRelease (q * n)
      (SDE.euclideanPoissonMaskedClippedSum c (fun i k => g i x k) A mask)) =
      sampledGradient q c (restrictedGradient g A) x mask := by
  classical
  have hclip (i : Fin n) : Mf.DP.toEuclidean (Mf.DP.l2VectorClip c (fun k => g i x k)) =
      Mf.DP.euclideanBallClip c (g i x) := by
    simpa [Mf.DP.toEuclidean] using
      (Mf.DP.toEuclidean_l2VectorClip c (fun k => g i x k))
  have hsum : Mf.DP.toEuclidean
      (SDE.euclideanPoissonMaskedClippedSum c (fun i k => g i x k) A mask) =
      ∑ i, if mask i then Mf.DP.euclideanBallClip c (restrictedGradient g A i x) else 0 := by
    unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
    simp only [Mf.DP.toEuclidean, WithLp.toLp_sum]
    rw [Finset.sum_filter]
    calc
      _ = ∑ i ∈ A, if mask i then Mf.DP.euclideanBallClip c (g i x) else 0 := by
        apply Finset.sum_congr rfl
        intro i _
        split_ifs <;> simp_all [Mf.DP.toEuclidean]
      _ = _ := by
        calc
          _ = ∑ i ∈ A, if mask i then
              Mf.DP.euclideanBallClip c (restrictedGradient g A i x) else 0 := by
            apply Finset.sum_congr rfl
            intro i hi
            simp only [restrictedGradient, if_pos hi]
          _ = _ := Finset.sum_subset (Finset.subset_univ A) (by
            intro i _ hi
            simp [restrictedGradient, hi, Mf.DP.euclideanBallClip, hc])
  have hnorm (z : Fin d → ℝ) : SDE.averageRelease (q * n) z = (q * n)⁻¹ • z := by
    ext k
    simp [SDE.averageRelease, div_eq_mul_inv, mul_comm]
  rw [hnorm]
  change Mf.DP.toEuclidean ((q * n)⁻¹ •
    SDE.euclideanPoissonMaskedClippedSum c (fun i k => g i x k) A mask) = _
  change (q * n)⁻¹ • Mf.DP.toEuclidean
    (SDE.euclideanPoissonMaskedClippedSum c (fun i k => g i x k) A mask) = _
  rw [hsum]
  rfl

end
end Mf.Optimization.PoissonClippedSGD
