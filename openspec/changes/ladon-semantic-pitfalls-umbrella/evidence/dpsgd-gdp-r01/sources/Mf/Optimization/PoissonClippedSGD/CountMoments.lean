import Mf.Optimization.FinitePoissonSign.GaussianResponse
import Mf.Optimization.PoissonClippedSGD.Mechanism
import Mf.DP.PoissonParticipationCenteredMoments

/-!
# Exact moments of the normalized Poisson mask count

The actual independent inclusion law has the finite binomial count moments.
The clipped query norm is bounded by the realized count times the clipping
radius divided by the public expected batch size. Combining these facts gives
query moment bounds at every fixed state, without a lower bound on `q*n`.

The fourth count polynomial uses real falling factors, so populations below
four and empty masks are included. No coordinate independence is assumed for
the sampled vector.
-/

set_option autoImplicit false
noncomputable section
open MeasureTheory
open scoped BigOperators
namespace Mf.Optimization.PoissonClippedSGD

/-- Exact raw moments under the maintained finite independent mask law. -/
theorem integral_count_pow (n k : ℕ) (q : NNReal) (hq : q ≤ 1) :
    (∫ mask, (Mf.DP.participationCount mask : ℝ)^k
      ∂SDE.poissonMaskLaw (Record := Fin n) q hq) =
        Mf.DP.poissonParticipationCountMoment n k q := by
  rw [FinitePoissonSign.integral_poissonMaskLaw_eq_sum]
  rfl

theorem integral_count_sq (n : ℕ) (q : NNReal) (hq : q ≤ 1) :
    (∫ mask, (Mf.DP.participationCount mask : ℝ)^2
      ∂SDE.poissonMaskLaw (Record := Fin n) q hq) =
        (n : ℝ)*q+(n : ℝ)*((n : ℝ)-1)*(q : ℝ)^2 := by
  rw [integral_count_pow, Mf.DP.poissonParticipationCountMoment_two]

theorem integral_count_four (n : ℕ) (q : NNReal) (hq : q ≤ 1) :
    (∫ mask, (Mf.DP.participationCount mask : ℝ)^4
      ∂SDE.poissonMaskLaw (Record := Fin n) q hq) =
        (n : ℝ)*q+7*(n : ℝ)*((n : ℝ)-1)*(q : ℝ)^2+
        6*(n : ℝ)*((n : ℝ)-1)*((n : ℝ)-2)*(q : ℝ)^3+
        (n : ℝ)*((n : ℝ)-1)*((n : ℝ)-2)*((n : ℝ)-3)*(q : ℝ)^4 := by
  rw [integral_count_pow, Mf.DP.poissonParticipationCountMoment_four]

/-- Clipping retains the realized count, including empty samples. -/
theorem norm_sampledGradient_le_count {n d : ℕ} (hn : 0 < n)
    (q c : ℝ) (hq : 0 < q) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) (mask : Fin n → Bool) :
    ‖sampledGradient q c g x mask‖ ≤ c*(Mf.DP.participationCount mask : ℝ)/(q*n) := by
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hsum : (∑ i, if mask i then c else 0) = c*(Mf.DP.participationCount mask : ℝ) := by
    simp only [Mf.DP.participationCount, Nat.cast_sum, Nat.cast_ite, Nat.cast_one,
      Nat.cast_zero, Finset.mul_sum, mul_ite, mul_one, mul_zero]
  rw [sampledGradient, norm_smul, Real.norm_eq_abs, abs_of_nonneg (by positivity)]
  calc
    _ ≤ (q*n)⁻¹ * ∑ i, ‖if mask i then Mf.DP.euclideanBallClip c (g i x) else 0‖ :=
      mul_le_mul_of_nonneg_left (norm_sum_le _ _) (by positivity)
    _ ≤ (q*n)⁻¹ * ∑ i, if mask i then c else 0 := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      apply Finset.sum_le_sum
      intro i _
      split_ifs
      · exact Mf.DP.euclideanBallClip_mem_closedBall c hc _
      · simp
    _ = _ := by rw [hsum]; ring

/-- Normalized finite-mask count moment for the public divisor `q*n`. -/
def normalizedCountMoment (n k : ℕ) (q : ℝ) : ℝ :=
  Mf.DP.poissonParticipationCountMoment n k q / (q*n)^k

/-- The normalized second moment is valid even below one expected inclusion. -/
theorem normalizedCountMoment_two {n : ℕ} (hn : 0 < n) {q : ℝ} (hq : 0 < q) :
    normalizedCountMoment n 2 q = 1+(1-q)/(q*n) := by
  have hnR : (n : ℝ) ≠ 0 := by exact_mod_cast hn.ne'
  unfold normalizedCountMoment
  rw [Mf.DP.poissonParticipationCountMoment_two]
  field_simp
  ring

/-- Explicit fourth normalized count moment, including populations below four. -/
theorem normalizedCountMoment_four (n : ℕ) (q : ℝ) :
    normalizedCountMoment n 4 q =
      ((n : ℝ)*q+7*(n : ℝ)*((n : ℝ)-1)*q^2+
        6*(n : ℝ)*((n : ℝ)-1)*((n : ℝ)-2)*q^3+
        (n : ℝ)*((n : ℝ)-1)*((n : ℝ)-2)*((n : ℝ)-3)*q^4)/(q*n)^4 := by
  rw [normalizedCountMoment, Mf.DP.poissonParticipationCountMoment_four]

/-- Count-sensitive query moments retain the exact binomial law. -/
theorem integral_sampledGradient_norm_pow_le {n d : ℕ} (hn : 0 < n)
    (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (c : ℝ) (hc : 0 ≤ c)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x : EuclideanSpace ℝ (Fin d)) (k : ℕ) :
    (∫ mask, ‖sampledGradient q c g x mask‖^k
      ∂SDE.poissonMaskLaw (Record := Fin n) q hq) ≤ c^k*normalizedCountMoment n k q := by
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hqR : (0 : ℝ) < q := by exact_mod_cast hq0
  have hp (mask : Fin n → Bool) : ‖sampledGradient q c g x mask‖^k ≤
      (c/(q*n))^k*(Mf.DP.participationCount mask : ℝ)^k := by
    calc
      _ ≤ (c*(Mf.DP.participationCount mask : ℝ)/(q*n))^k :=
        pow_le_pow_left₀ (norm_nonneg _) (norm_sampledGradient_le_count hn q c hqR hc g x mask) k
      _ = _ := by rw [← mul_pow]; congr 1; ring
  calc
    _ ≤ ∫ mask, (c/(q*n))^k*(Mf.DP.participationCount mask : ℝ)^k
        ∂SDE.poissonMaskLaw (Record := Fin n) q hq :=
      integral_mono Integrable.of_finite Integrable.of_finite hp
    _ = _ := by
      rw [integral_const_mul, integral_count_pow]
      simp [normalizedCountMoment, div_pow]
      ring

end Mf.Optimization.PoissonClippedSGD
