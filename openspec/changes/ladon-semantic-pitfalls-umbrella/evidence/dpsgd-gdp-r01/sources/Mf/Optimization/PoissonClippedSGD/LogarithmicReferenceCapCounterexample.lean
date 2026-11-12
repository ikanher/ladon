import Mf.Optimization.PoissonClippedSGD.LogarithmicReferenceBatchSize

/-!
# A fixed-pass reversal caused by the learning-rate cap

For N=2, one expected pass, zero sampling-variance coefficient, and the same
positive finite Gaussian-reference privacy calibration, compare (T,q)=(2,1/2)
with (1,1). Choosing the public gap bound F=1+4P+Q, where P and Q are the two
positive variance coefficients, makes both steps hit their caps. The resulting
optimized upper bound is strictly smaller for the smaller batch.

This is a counterexample to unconditional monotonicity of the capped adaptive
convergence bound. It is separate from the older exact-accountant frozen-average
counterexamples and makes no claim about actual optimization performance.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD.LogarithmicReference

/-- Even with exact equal expected passes and positive finite private noise,
a sufficiently large public gap makes the capped bound favor the smaller batch. -/
theorem exists_fixed_passes_cap_reversal {eps δ : ℝ} (he : 0 < eps) :
    ∃ F : ℝ, 0 < F ∧
      upperBound 2 1 2 (1 / 2) 1 0 eps δ F 1 <
        upperBound 2 1 1 1 1 0 eps δ F 1 := by
  let P := totalVariance 2 1 2 (1 / 2) 1 0 eps δ
  let Q := totalVariance 2 1 1 1 1 0 eps δ
  have hP : 0 < P := totalVariance_pos (by norm_num) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) he
  have hQ : 0 < Q := totalVariance_pos (by norm_num) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) he
  let F := 1 + 4 * P + Q
  have hF : 0 < F := by dsimp [F]; positivity
  have hcapP : (2 / 3 : ℝ) ≤ Real.sqrt (2 * F / (2 * 1 * P)) := by
    apply (Real.le_sqrt (by norm_num) (by positivity)).mpr
    apply (le_div_iff₀ (by positivity : 0 < 2 * 1 * P)).mpr
    dsimp [F]
    nlinarith
  have hcapQ : (1 : ℝ) ≤ Real.sqrt (2 * F / (1 * 1 * Q)) := by
    apply (Real.le_sqrt (by norm_num) (by positivity)).mpr
    apply (le_div_iff₀ (by positivity : 0 < 1 * 1 * Q)).mpr
    dsimp [F]
    nlinarith
  have heP : learningRate 2 1 2 (1 / 2) 1 0 eps δ F 1 = 2 / 3 := by
    unfold learningRate optimalStep
    have hc : poissonStepCap 1 ((1 - (1 / 2 : ℝ)) / ((1 / 2) * 2)) = 2 / 3 := by
      norm_num [poissonStepCap]
    rw [hc]
    exact min_eq_left hcapP
  have heQ : learningRate 2 1 1 1 1 0 eps δ F 1 = 1 := by
    unfold learningRate optimalStep
    have hc : poissonStepCap 1 ((1 - (1 : ℝ)) / (1 * 2)) = 1 := by
      norm_num [poissonStepCap]
    rw [hc]
    simpa only [Nat.cast_one] using min_eq_left hcapQ
  refine ⟨F, hF, ?_⟩
  unfold upperBound
  rw [heP, heQ]
  norm_num only [Nat.cast_ofNat]
  change stationarityUpper 1 (stepRateD (2 / 3) F 2 1 P 0) <
    stationarityUpper 1 (stepRateD 1 F 1 1 Q 0)
  have hD : stepRateD (2 / 3) F 2 1 P 0 <
      stepRateD 1 F 1 1 Q 0 := by
    norm_num [stepRateD]
    dsimp [F]
    nlinarith
  unfold stationarityUpper
  simp only [div_one]
  exact add_lt_add_of_le_of_lt (Real.sqrt_le_sqrt hD.le) hD

end Mf.Optimization.PoissonClippedSGD.LogarithmicReference
