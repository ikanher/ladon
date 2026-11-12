import Mf.Optimization.PoissonClippedSGD.AmplifiedCalibration

/-!
# Amplified finite private clipped-SGD convergence

The public hybrid calibration pays the same finite privacy budget as the
Gaussian fallback while retaining q-squared amplification when its finite
validity floor permits it. The existing Gaussian law and convergence theorem
consume the identical multiplier. At a fixed public admissible step, the
stationarity upper bound is no larger than the conservative baseline.

The fixed-slot objective, hidden masks, add/remove adjacency and public qN
normalizer are those of `PrivateConvergence`. Utility concerns the average
pre-update expected gradient norm, not the final iterate or achieved ordering.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
noncomputable section

private theorem normalizedSumNoise_sq_factor (n d : ℕ) (q c nu : ℝ) :
    normalizedSumNoise n d q c nu ^ 2 =
      (c ^ 2 * d / (q * n) ^ 2) * nu ^ 2 := by
  simp only [normalizedSumNoise, mul_pow, div_pow, Real.sq_sqrt (Nat.cast_nonneg d)]

/-- The same public normalization preserves the hybrid variance improvement. -/
theorem hybridNoise_sq_le_baseline (n d T : ℕ) (q c epsilon delta : ℝ)
    (hT : 0 < T) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1) :
    normalizedSumNoise n d q c (hybridPrivacyMultiplier T q epsilon delta) ^ 2 ≤
      normalizedSumNoise n d q c (finitePrivacyMultiplier T epsilon delta) ^ 2 := by
  rw [normalizedSumNoise_sq_factor, normalizedSumNoise_sq_factor,
    hybridPrivacyMultiplier_sq hT heps hdelta hdelt]
  have hB : 0 ≤ (T : ℝ) * (finitePrivacyOrder epsilon delta : ℝ) / epsilon := by
    positivity
  rw [finitePrivacyMultiplier, Real.sq_sqrt hB]
  exact mul_le_mul_of_nonneg_left (hybridPrivacyVariance_le_baseline _ _ _ _) (by positivity)

/-- Exact strict-improvement domain for the actual normalized Gaussian variance. -/
theorem hybridNoise_sq_lt_baseline_iff {n d T : ℕ} {q c epsilon delta : ℝ}
    (hn : 0 < n) (hd : 0 < d) (hT : 0 < T) (hq : 0 < q) (hc : 0 < c)
    (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1) :
    normalizedSumNoise n d q c (hybridPrivacyMultiplier T q epsilon delta) ^ 2 <
      normalizedSumNoise n d q c (finitePrivacyMultiplier T epsilon delta) ^ 2 ↔
      2 * q ^ 2 < 1 ∧
        epsilon * ((finitePrivacyOrder epsilon delta : ℝ) - 1) < 2 * T := by
  rw [normalizedSumNoise_sq_factor, normalizedSumNoise_sq_factor,
    hybridPrivacyMultiplier_sq hT heps hdelta hdelt]
  have hB : 0 ≤ (T : ℝ) * (finitePrivacyOrder epsilon delta : ℝ) / epsilon := by
    positivity
  rw [finitePrivacyMultiplier, Real.sq_sqrt hB]
  have hcoef : 0 < c ^ 2 * d / (q * n) ^ 2 := by positivity
  rw [mul_lt_mul_iff_right₀ hcoef]
  exact hybridPrivacyVariance_lt_baseline_iff hT
    (SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder_ge_two heps hdelta hdelt) heps

/-- Smaller variance gives a no-larger stationarity upper bound at a common
public step. This does not compare achieved utility of two runs. -/
theorem hybridUpper_le_baseline (n d T : ℕ) (q c epsilon delta eta L kappa sigma gap : ℝ)
    (hT : 0 < T) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hc : 0 ≤ c) (heta : 0 ≤ eta) (hL : 0 ≤ L) :
    stationarityUpper c (poissonRateD eta L kappa sigma
      (normalizedSumNoise n d q c (hybridPrivacyMultiplier T q epsilon delta)) gap T c) ≤
    stationarityUpper c (poissonRateD eta L kappa sigma
      (normalizedSumNoise n d q c (finitePrivacyMultiplier T epsilon delta)) gap T c) := by
  apply stationarityUpper_mono hc
  have hvar := hybridNoise_sq_le_baseline n d T q c epsilon delta hT heps hdelta hdelt
  have hmul := mul_le_mul_of_nonneg_left hvar (show 0 ≤ 2 * eta * L by positivity)
  unfold poissonRateD
  nlinarith

namespace PrivacyData
variable {n d : ℕ}

/-- The actual Gaussian final iterate is private at the public hybrid noise. -/
theorem hybrid_optionalFinal_approxDP {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (hd : 0 < d) (T : ℕ) (hT : 0 < T)
    (epsilon delta : ℝ) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hnoise : data.multiplier = hybridPrivacyMultiplier T data.q epsilon delta) :
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) epsilon delta := by
  have h := Mf.DP.approxDP_postprocess_map (data.state T) (data.state_measurable T)
    (data.hybrid_optionalTranscript_approxDP g hg T hT epsilon delta heps hdelta hdelt hnoise)
  have hmech : data.optionalFinalLaw g T =
      fun D => (data.optionalTranscriptLaw g hg T D).map (data.state T) := by
    funext D
    exact data.optionalFinalLaw_eq_map g hg hd T D
  rw [hmech]
  exact h

/-- Finite privacy and average pre-update expected-gradient utility for the
same calibrated Gaussian recursion and fixed public-slot mean objective.
Empty slots have zero gradient. The final iterate is private; the utility
conclusion is an average over pre-update iterates, not a final-gradient bound. -/
theorem hybrid_private_convergence {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) (T : ℕ) (hT : 0 < T)
    (epsilon delta : ℝ) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hnoise : data.multiplier = hybridPrivacyMultiplier T data.q epsilon delta)
    (heta : 0 < data.eta) (L sigmaSG : ℝ) (hL : 0 < L) (hsg : 0 ≤ sigmaSG)
    (hclip : 4 * sigmaSG ≤ data.clipping)
    (hstep : data.eta * L * (1 + (1 - (data.q : ℝ)) / ((data.q : ℝ) * n)) ≤ 1)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (D : Fin n → Option Record)
    (fi : Fin n → EuclideanSpace ℝ (Fin d) → ℝ)
    (hfi : ∀ i x, HasGradientAt (fi i) (slotGradient g D i x) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => slotGradient g D i x) -
        vectorMean (fun i => slotGradient g D i y)‖ ≤ L * ‖x - y‖)
    (hvariance : ∀ x, meanSqDeviation (fun i => slotGradient g D i x)
      (vectorMean (fun i => slotGradient g D i x)) ≤ sigmaSG ^ 2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ finiteMeanObjective fi x) :
    let s := normalizedSumNoise n d data.q data.clipping data.multiplier
    let values : Fin T → ℝ := fun t => ∫ ω,
      ‖vectorMean (fun i => slotGradient g D i
        (gaussianIterate data.eta data.q data.clipping (slotGradient g D) data.initial
          T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T data.q data.q_le_one s
    let budget := poissonRateD data.eta L ((1 - (data.q : ℝ)) / ((data.q : ℝ) * n))
      sigmaSG s (finiteMeanObjective fi data.initial - fLower) T data.clipping
    let baseline := poissonRateD data.eta L ((1 - (data.q : ℝ)) / ((data.q : ℝ) * n))
      sigmaSG (normalizedSumNoise n d data.q data.clipping
        (finitePrivacyMultiplier T epsilon delta))
      (finiteMeanObjective fi data.initial - fLower) T data.clipping
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) epsilon delta ∧
      Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) epsilon delta ∧
      (T : ℝ)⁻¹ * ∑ t, values t ≤ stationarityUpper data.clipping budget ∧
      stationarityUpper data.clipping budget ≤ stationarityUpper data.clipping baseline ∧
      ∃ t : Fin T, values t ≤ stationarityUpper data.clipping budget := by
  dsimp only
  have hgrad : ∀ i, Measurable (slotGradient g D i) :=
    (data.withSlots g hg D).gradient_measurable
  have hs : 0 ≤ normalizedSumNoise n d data.q data.clipping data.multiplier := by
    unfold normalizedSumNoise
    have hc := data.clipping_pos
    have hnu := data.multiplier_pos
    positivity
  have h := finite_sum_gaussian_convergence hn hd data.q data.q_pos data.q_le_one
    data.eta L data.clipping sigmaSG
    (normalizedSumNoise n d data.q data.clipping data.multiplier)
    heta hL data.clipping_pos hsg hs hclip hstep
    (slotGradient g D) hgrad fi hfi hLip hvariance fLower hlower data.initial T hT
  dsimp only at h
  obtain ⟨t, ht⟩ := h.2.2.2
  refine ⟨data.hybrid_optionalTranscript_approxDP g hg T hT epsilon delta
      heps hdelta hdelt hnoise,
    data.hybrid_optionalFinal_approxDP g hg hd T hT epsilon delta
      heps hdelta hdelt hnoise, h.1, ?_, t, ht.trans h.1⟩
  rw [hnoise]
  exact hybridUpper_le_baseline n d T data.q data.clipping epsilon delta data.eta L
    ((1 - (data.q : ℝ)) / ((data.q : ℝ) * n)) sigmaSG
    (finiteMeanObjective fi data.initial - fLower)
    hT heps hdelta hdelt data.clipping_pos.le heta.le hL.le

end PrivacyData
end
end Mf.Optimization.PoissonClippedSGD
