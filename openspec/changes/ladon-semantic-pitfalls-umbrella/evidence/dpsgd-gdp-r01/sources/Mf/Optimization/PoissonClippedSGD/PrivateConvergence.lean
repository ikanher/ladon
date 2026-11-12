import Mf.Optimization.PoissonClippedSGD.FinalLaw
import Mf.Optimization.PoissonClippedSGD.PrivacyCalibration
import Mf.Optimization.PoissonClippedSGD.Conclusions
import Mf.Optimization.PoissonClippedSGD.GDPFormula

/-!
# Finite private convergence of Poisson clipped SGD

The public multiplier is calibrated by the exact finite RDP envelope.
`optionalFinalLaw` is the existing independent Gaussian product-history run,
identified with measurable postprocessing of the hidden-sampling transcript.
The convergence theorem supplies average pre-update expected gradient norm at
this same noise, and does not claim a final-iterate gradient bound.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators
noncomputable section
/-- Explicit total noise energy at the conservative finite calibration. -/
theorem finitePrivacyNoise_sq (n d T : ℕ) (q c epsilon delta : ℝ)
    (heps : 0 < epsilon) :
    (normalizedSumNoise n d q c (finitePrivacyMultiplier T epsilon delta)) ^ 2 =
      c ^ 2 * d * T * (finitePrivacyOrder epsilon delta : ℝ) /
        (epsilon * (q * n) ^ 2) := by
  have hscale : 0 ≤ (T : ℝ) * (finitePrivacyOrder epsilon delta : ℝ) / epsilon := by
    positivity
  simp only [normalizedSumNoise, finitePrivacyMultiplier, mul_pow, div_pow,
    Real.sq_sqrt hscale, Real.sq_sqrt (Nat.cast_nonneg d)]
  ring

namespace PrivacyData
variable {n d : ℕ}

/-- Privacy after measurable final-iterate postprocessing of the transcript. -/
theorem calibrated_optionalFinal_approxDP {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (hd : 0 < d) (T : ℕ) (hT : 0 < T)
    (epsilon delta : ℝ) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hnoise : data.multiplier = finitePrivacyMultiplier T epsilon delta) :
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) epsilon delta := by
  have h := Mf.DP.approxDP_postprocess_map (data.state T) (data.state_measurable T)
    (data.calibrated_optionalTranscript_approxDP g hg T hT epsilon delta heps hdelta hdelt hnoise)
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
theorem finite_private_convergence {Record : Type} (data : PrivacyData n d)
    (hn : 0 < n) (hd : 0 < d) (T : ℕ) (hT : 0 < T)
    (epsilon delta : ℝ) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hnoise : data.multiplier = finitePrivacyMultiplier T epsilon delta)
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
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) epsilon delta ∧
      Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalFinalLaw g T) epsilon delta ∧
      (T : ℝ)⁻¹ * ∑ t, values t ≤ stationarityUpper data.clipping budget ∧
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
  exact ⟨data.calibrated_optionalTranscript_approxDP g hg T hT epsilon delta
      heps hdelta hdelt hnoise,
    data.calibrated_optionalFinal_approxDP g hg hd T hT epsilon delta
      heps hdelta hdelt hnoise, h.1, t, ht.trans h.1⟩

end PrivacyData
end
end Mf.Optimization.PoissonClippedSGD
