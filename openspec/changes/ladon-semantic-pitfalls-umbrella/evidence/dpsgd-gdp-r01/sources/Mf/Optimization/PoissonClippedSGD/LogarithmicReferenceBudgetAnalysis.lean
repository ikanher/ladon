import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceBatchSize

/-!
# Constants and privacy domination in the calibrated SGD bound

The variance comparison quantifies the error from suppressing sampling
variance: after retuning under a common cap, the nonconstant descent price
changes by at most `sqrt(1 + rho)` if sampling variance is at most `rho` times
privacy variance. The proof scales a feasible learning rate down and therefore
also applies when the cap binds.

The separate algebraic comparison retains the constants in Abadi et al.,
*Deep Learning with Differential Privacy* (2016), Theorem 1, arXiv:1607.00133.
The identities preserve its small-epsilon domain. They do not assert a finite
privacy theorem for an arbitrary chosen value of the unspecified constant.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.LogarithmicReference

private theorem capped_variance_dilation {F T L P Q cap bias k : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hP : 0 < P) (hQ : 0 < Q)
    (hcap : 0 < cap) (hk : 1 ≤ k) (hPQ : Q ≤ k ^ 2 * P) :
    stepRateD (optimalStep F T L Q cap) F T L Q bias - bias ≤
      k * (stepRateD (optimalStep F T L P cap) F T L P bias - bias) := by
  let e := optimalStep F T L P cap
  have he : 0 < e := optimalStep_pos hF hT hL hP hcap
  have hk0 : 0 < k := by linarith
  have hek : 0 < e / k := div_pos he hk0
  have hecap : e / k ≤ cap :=
    (div_le_self he.le hk).trans (optimalStep_le_cap _ _ _ _ _)
  have hmin := stepRateD_optimal (bias := bias) hF hT hL hQ hcap hek hecap
  have hlin := mul_le_mul_of_nonneg_left hPQ (show 0 ≤ 2 * (e / k) * L by positivity)
  have hrec : 4 * F / (e / k * T) = k * (4 * F / (e * T)) := by field_simp
  have hid : 2 * (e / k) * L * (k ^ 2 * P) = k * (2 * e * L * P) := by field_simp
  rw [hid] at hlin
  change stepRateD (optimalStep F T L Q cap) F T L Q bias - bias ≤
    k * (stepRateD e F T L P bias - bias)
  calc
    _ ≤ stepRateD (e / k) F T L Q bias - bias := sub_le_sub_right hmin bias
    _ ≤ _ := by unfold stepRateD; rw [hrec]; nlinarith only [hlin]

/-- If sampling variance is at most rho times privacy variance, ignoring it changes
the retuned coefficient above its clipping floor by a factor at most sqrt(1+rho).
The same positive cap is used for both minima; it may be active. -/
theorem privacy_dominated_retuned {F T L P S cap bias rho : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hP : 0 < P)
    (hS : 0 ≤ S) (hcap : 0 < cap) (hr : 0 ≤ rho) (hdom : S ≤ rho * P) :
    let pure := stepRateD (optimalStep F T L P cap) F T L P bias - bias
    let full := stepRateD (optimalStep F T L (S + P) cap) F T L (S + P) bias - bias
    pure ≤ full ∧ full ≤ Real.sqrt (1 + rho) * pure := by
  dsimp only
  have hQ : 0 < S + P := add_pos_of_nonneg_of_pos hS hP
  have he := optimalStep_pos hF hT hL hQ hcap
  constructor
  · apply sub_le_sub_right
    exact (stepRateD_optimal hF hT hL hP hcap he
      (optimalStep_le_cap _ _ _ _ _)).trans
      (stepRateD_mono_variance he.le hL.le (by linarith))
  · apply capped_variance_dilation hF hT hL hP hQ hcap
    · exact (Real.one_le_sqrt).mpr (by linarith)
    · rw [Real.sq_sqrt (by linarith : 0 ≤ 1 + rho)]
      nlinarith only [hdom]

/-- The algebraic Abadi scaling prescription, retaining its unspecified constant.
This definition alone is not a finite privacy certificate. -/
def abadiVariance (c2 q T eps δ : ℝ) : ℝ :=
  c2 ^ 2 * q ^ 2 * T * Real.log (1 / δ) / eps ^ 2

/-- At fixed updates the normalized Abadi noise loses its batch dependence. -/
theorem abadiVariance_normalized {q T : ℝ} (hq : q ≠ 0) (hT : T ≠ 0)
    (c2 eps δ : ℝ) :
    abadiVariance c2 q T eps δ / (T * q ^ 2) = c2 ^ 2 * Real.log (1 / δ) / eps ^ 2 := by
  unfold abadiVariance
  field_simp

/-- The validity restriction on epsilon cannot be discarded when varying q. -/
theorem abadi_domain_fixed_steps {eps c1 T q : ℝ} (hc : 0 < c1) (hT : 0 < T) :
    eps < c1 * q ^ 2 * T ↔ eps / (c1 * T) < q ^ 2 := by
  rw [div_lt_iff₀ (mul_pos hc hT)]
  ring_nf

/-- At exact expected passes the Abadi restriction is a lower cutoff on q. -/
theorem abadi_domain_exact_passes {eps c1 T E q : ℝ}
    (hc : 0 < c1) (hE : 0 < E) (hpasses : T * q = E) :
    eps < c1 * q ^ 2 * T ↔ eps / (c1 * E) < q := by
  rw [div_lt_iff₀ (mul_pos hc hE), ← hpasses]
  ring_nf

end Mf.Optimization.PoissonClippedSGD.LogarithmicReference
