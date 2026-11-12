import Mf.DP.PoissonSampledGaussianRenyiEnvelope
import Mf.Optimization.PoissonClippedSGD.OptionalPrivacy
import Mf.Optimization.SDE.DPAdamPublicRenyiOrderSelection

/-!
# A public finite calibration for clipped SGD

The existing public integer-order selector depends only on epsilon and delta.
The full-Gaussian envelope spends half of epsilon on the finite transcript RDP
cost and half on conversion to delta. The resulting multiplier is conservative
and deliberately discards sampling amplification. It is distinct from the raw
GDP prescription.
-/

namespace Mf.Optimization.PoissonClippedSGD
open Mf.DP SDE MeasureTheory
noncomputable section
/-- Both directions in the sharp pair-local adapter use this same step cost;
this corollary bounds it by an ordinary Gaussian cost for every q in [0,1]. -/
theorem sampledGaussianSharpStepRho_le_fullGaussian
    (order : ℕ) (q : NNReal) (hq : q ≤ 1) (sigma : ℝ) (horder : 2 ≤ order)
    (hsigma : 0 < sigma) :
    euclideanSampledGaussianSharpStepRho order q sigma ≤
      (order : ℝ) / (2 * sigma ^ 2) := by
  have hz : 0 ≤ 1 / sigma ^ 2 := by positivity
  have hforward := sampledGaussianForwardRho_le_fullGaussian
    order (q : ℝ) (1 / sigma ^ 2) horder q.2 (by exact_mod_cast hq) hz
  unfold euclideanSampledGaussianSharpStepRho
  rw [max_le_iff]
  constructor
  · positivity
  · calc
      sampledGaussianForwardRho order (q : ℝ) (1 / sigma ^ 2) ≤
          (order : ℝ) * (1 / sigma ^ 2) / 2 := hforward
      _ = (order : ℝ) / (2 * sigma ^ 2) := by ring

/-- Public scalar calibration: if the usual RDP conversion lane consumes at
most half of epsilon, this finite Gaussian envelope consumes the other half.
No mechanism-law premise is hidden here. -/
theorem finiteSharpGaussianCalibration
    (steps order : ℕ) (q : NNReal) (hq : q ≤ 1) (epsilon deltaLane : ℝ)
    (hsteps : 0 < steps) (horder : 2 ≤ order)
    (hepsilon : 0 < epsilon) (_hdeltaLane : 0 ≤ deltaLane)
    (hdeltaBudget : deltaLane ≤ epsilon / 2) :
    (steps : ℝ) * euclideanSampledGaussianSharpStepRho order q
        (Real.sqrt ((steps : ℝ) * (order : ℝ) / epsilon)) + deltaLane ≤
      epsilon := by
  have hstepsR : 0 < (steps : ℝ) := by exact_mod_cast hsteps
  have horderR : 0 < (order : ℝ) := by
    have : (2 : ℝ) ≤ order := by exact_mod_cast horder
    linarith
  have hnoiseSq : 0 < (steps : ℝ) * (order : ℝ) / epsilon := by
    positivity
  have hnoise : 0 < Real.sqrt ((steps : ℝ) * (order : ℝ) / epsilon) :=
    Real.sqrt_pos.2 hnoiseSq
  have hsquare : (Real.sqrt ((steps : ℝ) * (order : ℝ) / epsilon)) ^ 2 =
      (steps : ℝ) * (order : ℝ) / epsilon :=
    Real.sq_sqrt hnoiseSq.le
  have hstep := sampledGaussianSharpStepRho_le_fullGaussian
    order q hq _ horder hnoise
  have htotal : (steps : ℝ) * euclideanSampledGaussianSharpStepRho order q
      (Real.sqrt ((steps : ℝ) * (order : ℝ) / epsilon)) ≤ epsilon / 2 := by
    calc
      _ ≤ (steps : ℝ) *
          ((order : ℝ) /
            (2 * (Real.sqrt ((steps : ℝ) * (order : ℝ) / epsilon)) ^ 2)) :=
        mul_le_mul_of_nonneg_left hstep hstepsR.le
      _ = epsilon / 2 := by
        rw [hsquare]
        field_simp [ne_of_gt hstepsR, ne_of_gt horderR, ne_of_gt hepsilon]
  linarith

/-- Existing optimizer-independent public order selector, reused at the SGD boundary. -/
abbrev finitePrivacyOrder := SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder

/-- Finite conservative sum-noise multiplier; no asymptotic remainder is used. -/
def finitePrivacyMultiplier (T : ℕ) (epsilon delta : ℝ) : ℝ :=
  Real.sqrt ((T : ℝ) * (finitePrivacyOrder epsilon delta : ℝ) / epsilon)

theorem finitePrivacyMultiplier_pos {T : ℕ} {epsilon delta : ℝ}
    (hT : 0 < T) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1) :
    0 < finitePrivacyMultiplier T epsilon delta := by
  have hm := SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder_ge_two heps hdelta hdelt
  have hmR : (0 : ℝ) < finitePrivacyOrder epsilon delta := by
    have : (2 : ℝ) ≤ finitePrivacyOrder epsilon delta := by exact_mod_cast hm
    linarith
  unfold finitePrivacyMultiplier
  exact Real.sqrt_pos.2 (by positivity)

private theorem constant_adaptive_budget (rho : ℝ) :
    ∀ T, Mf.DP.adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ) * rho := by
  intro T
  induction T with
  | zero => simp
  | succ T ih => simp [Mf.DP.adaptiveRenyiBudget_succ, ih, Nat.cast_add, add_mul]

namespace PrivacyData
variable {n d : ℕ}

/-- A concrete public calibration discharges the converted finite privacy budget. -/
theorem calibrated_optionalTranscript_approxDP {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (T : ℕ) (hT : 0 < T)
    (epsilon delta : ℝ) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hnoise : data.multiplier = finitePrivacyMultiplier T epsilon delta) :
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) epsilon delta := by
  let m := finitePrivacyOrder epsilon delta
  have hm : 2 ≤ m :=
    SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder_ge_two heps hdelta hdelt
  have hden : 0 < (m : ℝ) - 1 := by
    have : (2 : ℝ) ≤ m := by exact_mod_cast hm
    linarith
  have hlane := SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder_deltaLane_le_half
    heps hdelta hdelt
  have hbudget := finiteSharpGaussianCalibration T m data.q data.q_le_one epsilon
    (Real.log (1 / delta) / ((m : ℝ) - 1)) hT hm heps (by
      apply div_nonneg
      · exact (SDE.DPAdamPublicRenyiOrderSelection.log_one_div_pos hdelta hdelt).le
      · exact hden.le) hlane
  have hcost : (T : ℝ) * SDE.euclideanSampledGaussianSharpStepRho m data.q data.multiplier +
      Real.log (1 / delta) / ((m : ℝ) - 1) ≤ epsilon := by
    simpa only [hnoise, finitePrivacyMultiplier, m] using hbudget
  have hdeltaLe : Real.exp (((m : ℝ) - 1) *
      (Mf.DP.adaptiveRenyiBudget
        (fun _ => SDE.euclideanSampledGaussianSharpStepRho m data.q data.multiplier) T -
          epsilon)) ≤ delta := by
    rw [constant_adaptive_budget]
    have hscaled := (div_le_iff₀ hden).mp
      (show Real.log (1 / delta) / ((m : ℝ) - 1) ≤ epsilon -
        (T : ℝ) * SDE.euclideanSampledGaussianSharpStepRho m data.q data.multiplier by linarith)
    have hlog : Real.log (1 / delta) = -Real.log delta := by simp
    rw [hlog] at hscaled
    calc
      _ ≤ Real.exp (Real.log delta) := Real.exp_le_exp.mpr (by nlinarith)
      _ = delta := Real.exp_log hdelta
  exact Mf.DP.approxDP_mono_delta OptionalRecordAdjacent _
    (data.optionalTranscript_approxDP g hg m hm T epsilon) hdeltaLe

end PrivacyData

end
end Mf.Optimization.PoissonClippedSGD
