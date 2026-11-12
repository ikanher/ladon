import Mf.Optimization.PoissonClippedSGD.PrivacyLaw

/-!
# Noise units for the Poisson clipped-SGD run

Raw multiplier squared `V` gives coordinate variance `C²V/(qN)²` and total
Euclidean RMS energy `d*C²V/(qN)²`. These identities are independent of the
privacy predicate used to calibrate that multiplier.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD

/-- The calibrated raw multiplier gives this exact normalized total noise energy. -/
theorem normalizedSumNoise_sqrt_sq (n d : ℕ) (q C V : ℝ) (hV : 0 ≤ V) :
    (normalizedSumNoise n d q C (Real.sqrt V)) ^ 2 =
      C ^ 2 * d * V / (q * n) ^ 2 := by
  simp only [normalizedSumNoise, mul_pow, div_pow,
    Real.sq_sqrt hV, Real.sq_sqrt (Nat.cast_nonneg d)]
  ring

namespace PrivacyData
variable {n d : ℕ}

/-- The actual normalized RMS noise is positive for positive population and dimension. -/
theorem normalizedSumNoise_pos (data : PrivacyData n d) (hn : 0 < n) (hd : 0 < d) :
    0 < normalizedSumNoise n d data.q data.clipping data.multiplier := by
  have hq : (0 : ℝ) < data.q := by exact_mod_cast data.q_pos
  have hC := data.clipping_pos
  have hm := data.multiplier_pos
  unfold normalizedSumNoise
  positivity

end PrivacyData
end Mf.Optimization.PoissonClippedSGD
