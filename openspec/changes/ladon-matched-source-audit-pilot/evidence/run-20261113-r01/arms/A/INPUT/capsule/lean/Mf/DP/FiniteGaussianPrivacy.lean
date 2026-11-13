import Mf.DP.StandardGaussianCore
import Mf.Probability.StandardGaussianTailBounds
import Mf.DP.GaussianApproxDP
import Mf.DP.FiniteGaussianPrivacyBasis

/-!
# Finite Gaussian-pair event privacy

The analytic Gaussian condition bounds both directed comparisons of arbitrary
finite isotropic Gaussian laws. The proof centers the mean pair, identifies
its likelihood halfspace, bounds every event using the signed-measure Hahn
comparison, and translates back to the original means. It preserves the zero
distance branch and the original positivity and nonnegative-epsilon premises.

This is the analytic Gaussian mechanism of Balle and Wang, *Improving the
Gaussian Mechanism for Differential Privacy: Analytical Calibration and
Optimal Denoising* (ICML 2018), Theorem 8; the source is retained under
`paper/theory/gaussian-analysis/`. The scalar analysis and finite probability
implementation are independent owners, with mechanism adapters downstream.
-/

namespace Mf.DP.FiniteGaussianPrivacy
open Filter Mf.Probability.FiniteGaussian Mf.DP.FiniteGaussianPrivacyBasis
open scoped BigOperators Topology
noncomputable section

def analyticGaussianCondition (Δ σ ε δ : ℝ) : Prop :=
  analyticGaussianExpr Δ σ ε ≤ δ

@[simp] theorem analyticGaussianCondition_iff
    (Δ σ ε δ : ℝ) :
    analyticGaussianCondition Δ σ ε δ ↔ analyticGaussianExpr Δ σ ε ≤ δ := by
  rfl

theorem analyticGaussianCondition_mono_delta
    {Δ σ ε δ₀ δ : ℝ}
    (h : analyticGaussianCondition Δ σ ε δ₀)
    (hδ : δ₀ ≤ δ) :
    analyticGaussianCondition Δ σ ε δ := by
  exact analyticGaussianExpr_le_of_le h hδ

theorem analyticGaussianCondition_of_le
    {Δ σ ε δ₀ δ : ℝ}
    (hδ : δ₀ ≤ δ)
    (h : analyticGaussianCondition Δ σ ε δ₀) :
    analyticGaussianCondition Δ σ ε δ := by
  exact analyticGaussianCondition_mono_delta h hδ

theorem analyticGaussianCondition_of_one_le
    {Δ σ ε δ : ℝ}
    (hδ : 1 ≤ δ) :
    analyticGaussianCondition Δ σ ε δ := by
  exact le_trans (analyticGaussianExpr_le_one Δ σ ε) hδ

theorem analyticGaussianCondition_implies_neg_exp_le_delta
    {Δ σ ε δ : ℝ}
    (h : analyticGaussianCondition Δ σ ε δ) :
    -Real.exp ε ≤ δ := by
  exact le_trans (neg_exp_le_analyticGaussianExpr Δ σ ε) h

theorem analyticGaussianCondition_iff_event_form
    (Δ σ ε δ : ℝ) :
    analyticGaussianCondition Δ σ ε δ
          ↔ stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
                - Real.exp ε
                    * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
          ≤ δ := by
  simp [analyticGaussianCondition, analyticGaussianExpr_eq_event_form]

theorem analyticGaussianCondition_iff_measure_eval_event_form
    {n : ℕ} (i : Fin n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ) :
    analyticGaussianCondition Δ σ ε δ
      ↔ (measure σ (fun _ : Fin n => Δ / 2)).real
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
          - Real.exp ε
              * (measure σ (fun _ : Fin n => -Δ / 2)).real
                  (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
        ≤ δ := by
  simpa [analyticGaussianCondition] using
    (analyticGaussianExpr_iff_measure_eval_event_form
      (i := i) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ) hσ)

theorem analyticGaussianCondition_iff_gaussianReal_event_form
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ) :
    analyticGaussianCondition Δ σ ε δ
          ↔ (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                (Set.Iic (privacyEventThresholdPlus Δ σ ε))
              - Real.exp ε
                  * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                      (Set.Iic (privacyEventThresholdMinus Δ σ ε))
            ≤ δ := by
  simp [analyticGaussianCondition, analyticGaussianExpr_eq_gaussianReal_event_form, hσ]

theorem analyticGaussianCondition_iff_gaussianReal_event_form_explicit
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ) :
    analyticGaussianCondition Δ σ ε δ
          ↔ (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                (Set.Iic (Δ - (ε * σ ^ 2) / Δ))
              - Real.exp ε
                  * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                      (Set.Iic (-Δ - (ε * σ ^ 2) / Δ))
            ≤ δ := by
  simp [analyticGaussianCondition, analyticGaussianExpr_eq_gaussianReal_event_form_explicit, hσ]

theorem explicitGaussianEventBound_iff_gaussianReal_eventBound_explicit
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ) :
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
      ↔
        (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
              (Set.Iic (Δ - (ε * σ ^ 2) / Δ))
            - Real.exp ε
                * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                    (Set.Iic (-Δ - (ε * σ ^ 2) / Δ))
          ≤ δ := by
  exact
    (analyticGaussianCondition_iff_event_form Δ σ ε δ).symm.trans
      (analyticGaussianCondition_iff_gaussianReal_event_form_explicit Δ σ ε δ hσ)

lemma privacyLossArgPlus_two_sqrt
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    privacyLossArgPlus (2 * Real.sqrt r) σ ε
      = Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) := by
  unfold privacyLossArgPlus
  have hsqrt0 : Real.sqrt r ≠ 0 := (Real.sqrt_pos.2 hr).ne'
  field_simp [hσ.ne', hsqrt0]

lemma privacyLossArgMinus_two_sqrt
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    privacyLossArgMinus (2 * Real.sqrt r) σ ε
      = -Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) := by
  unfold privacyLossArgMinus
  have hsqrt0 : Real.sqrt r ≠ 0 := (Real.sqrt_pos.2 hr).ne'
  field_simp [hσ.ne', hsqrt0]

lemma gaussianReal_event_plus_eq_stdNormal
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    (ProbabilityTheory.gaussianReal (-r)
      (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
      (Set.Iic (-(centeredDotThreshold σ ε)))
      =
    stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε)) := by
  have hs : 0 < σ * Real.sqrt r := mul_pos hσ (Real.sqrt_pos.2 hr)
  have hvar :
      (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩ : NNReal)
        = ⟨(σ * Real.sqrt r) ^ 2, sq_nonneg (σ * Real.sqrt r)⟩ := by
    apply Subtype.ext
    calc
      σ ^ 2 * r = σ ^ 2 * (Real.sqrt r) ^ 2 := by rw [Real.sq_sqrt (le_of_lt hr)]
      _ = (σ * Real.sqrt r) ^ 2 := by ring
  rw [hvar]
  have hbase :=
    gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
      (-r) (σ * Real.sqrt r) (-(centeredDotThreshold σ ε)) hs
  have hbaseReal :
      (ProbabilityTheory.gaussianReal (-r)
          (⟨(σ * Real.sqrt r) ^ 2, sq_nonneg (σ * Real.sqrt r)⟩)).real
          (Set.Iic (-(centeredDotThreshold σ ε)))
        = stdNormalMeasure.real
            (Set.Iic ((-(centeredDotThreshold σ ε) - (-r)) / (σ * Real.sqrt r))) := by
    simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hbase
  rw [hbaseReal, centeredDot_arg_plus r σ ε hσ hr]
  exact congrArg (fun t : ℝ => stdNormalMeasure.real (Set.Iic t))
    (privacyLossArgPlus_two_sqrt r σ ε hσ hr).symm

lemma gaussianReal_event_minus_eq_stdNormal
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    (ProbabilityTheory.gaussianReal r
      (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
      (Set.Iic (-(centeredDotThreshold σ ε)))
      =
    stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)) := by
  have hs : 0 < σ * Real.sqrt r := mul_pos hσ (Real.sqrt_pos.2 hr)
  have hvar :
      (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩ : NNReal)
        = ⟨(σ * Real.sqrt r) ^ 2, sq_nonneg (σ * Real.sqrt r)⟩ := by
    apply Subtype.ext
    calc
      σ ^ 2 * r = σ ^ 2 * (Real.sqrt r) ^ 2 := by rw [Real.sq_sqrt (le_of_lt hr)]
      _ = (σ * Real.sqrt r) ^ 2 := by ring
  rw [hvar]
  have hbase :=
    gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
      r (σ * Real.sqrt r) (-(centeredDotThreshold σ ε)) hs
  have hbaseReal :
      (ProbabilityTheory.gaussianReal r
          (⟨(σ * Real.sqrt r) ^ 2, sq_nonneg (σ * Real.sqrt r)⟩)).real
          (Set.Iic (-(centeredDotThreshold σ ε)))
        = stdNormalMeasure.real
            (Set.Iic ((-(centeredDotThreshold σ ε) - r) / (σ * Real.sqrt r))) := by
    simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hbase
  rw [hbaseReal, centeredDot_arg_minus r σ ε hσ hr]
  exact congrArg (fun t : ℝ => stdNormalMeasure.real (Set.Iic t))
    (privacyLossArgMinus_two_sqrt r σ ε hσ hr).symm

lemma explicitEventBound_two_sqrt_iff_centeredGaussianEventBound
    (r σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))
      ≤ δ)
      ↔
        ((ProbabilityTheory.gaussianReal (-r)
          (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
          (Set.Iic (-(centeredDotThreshold σ ε)))
          - Real.exp ε
              * (ProbabilityTheory.gaussianReal r
                (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
                (Set.Iic (-(centeredDotThreshold σ ε)))
          ≤ δ) := by
  constructor <;> intro h
  · have hplus := gaussianReal_event_plus_eq_stdNormal r σ ε hσ hr
    have hminus := gaussianReal_event_minus_eq_stdNormal r σ ε hσ hr
    simpa [hplus, hminus] using h
  · have hplus := gaussianReal_event_plus_eq_stdNormal r σ ε hσ hr
    have hminus := gaussianReal_event_minus_eq_stdNormal r σ ε hσ hr
    simpa [hplus, hminus] using h

def bridgeU (a ε : ℝ) : ℝ := a - ε / (2 * a)

def bridgeV (a ε : ℝ) : ℝ := -a - ε / (2 * a)

def bridgeProfile (a ε : ℝ) : ℝ :=
  stdNormalCDFReal (bridgeU a ε) - Real.exp ε * stdNormalCDFReal (bridgeV a ε)

lemma bridgeV_sq_sub_bridgeU_sq
    (a ε : ℝ)
    (ha : a ≠ 0) :
    (bridgeV a ε) ^ 2 - (bridgeU a ε) ^ 2 = 2 * ε := by
  unfold bridgeU bridgeV
  field_simp [ha]
  ring

lemma exp_eps_mul_stdNormalPdf_bridgeV_eq_stdNormalPdf_bridgeU
    (a ε : ℝ)
    (ha : a ≠ 0) :
    Real.exp ε * stdNormalPdfReal (bridgeV a ε) = stdNormalPdfReal (bridgeU a ε) := by
  have hsq : (bridgeV a ε) ^ 2 = (bridgeU a ε) ^ 2 + 2 * ε := by
    linarith [bridgeV_sq_sub_bridgeU_sq a ε ha]
  unfold stdNormalPdfReal
  have hden : Real.sqrt (2 * Real.pi) ≠ 0 := by
    positivity
  field_simp [hden]
  have hmul :
      Real.exp ε * Real.exp (-(bridgeV a ε ^ 2 / 2))
        = Real.exp (ε + (-(bridgeV a ε ^ 2 / 2))) := by
    simpa using (Real.exp_add ε (-(bridgeV a ε ^ 2 / 2))).symm
  rw [hmul]
  calc
    Real.exp (ε + (-(bridgeV a ε ^ 2 / 2)))
      = Real.exp (ε - ((bridgeV a ε) ^ 2) / 2) := by rfl
    _ = Real.exp (ε - (((bridgeU a ε) ^ 2 + 2 * ε) / 2)) := by
          rw [hsq]
    _ = Real.exp (-(bridgeU a ε ^ 2 / 2)) := by
          congr 1
          ring


local instance (priority := 10000) gaussianRealDerivativeModule : Module ℝ ℝ :=
  RCLike.toInnerProductSpaceReal.toModule

lemma hasDerivAt_bridgeU (ε x : ℝ) (hx : x ≠ 0) :
    HasDerivAt (fun a : ℝ => bridgeU a ε) (1 + ε / (2 * x ^ 2)) x := by
  unfold bridgeU
  have hInv : HasDerivAt (fun a : ℝ => a⁻¹) (-(x ^ 2)⁻¹) x := hasDerivAt_inv hx
  have hScaled : HasDerivAt (fun a : ℝ => (ε / 2) * a⁻¹) ((ε / 2) * (-(x ^ 2)⁻¹)) x :=
    hInv.const_mul (ε / 2)
  have hMain : HasDerivAt (fun a : ℝ => a - (ε / 2) * a⁻¹) (1 - ((ε / 2) * (-(x ^ 2)⁻¹))) x :=
    (hasDerivAt_id x).sub hScaled
  have hderiv : 1 - ((ε / 2) * (-(x ^ 2)⁻¹)) = 1 + ε / (2 * x ^ 2) := by
    field_simp [hx]
    ring
  simpa [div_eq_mul_inv, mul_assoc, mul_left_comm, mul_comm, hderiv] using hMain

lemma hasDerivAt_bridgeV (ε x : ℝ) (hx : x ≠ 0) :
    HasDerivAt (fun a : ℝ => bridgeV a ε) (-1 + ε / (2 * x ^ 2)) x := by
  unfold bridgeV
  have hInv : HasDerivAt (fun a : ℝ => a⁻¹) (-(x ^ 2)⁻¹) x := hasDerivAt_inv hx
  have hScaled : HasDerivAt (fun a : ℝ => (ε / 2) * a⁻¹) ((ε / 2) * (-(x ^ 2)⁻¹)) x :=
    hInv.const_mul (ε / 2)
  have hMain : HasDerivAt (fun a : ℝ => -a - (ε / 2) * a⁻¹) (-1 - ((ε / 2) * (-(x ^ 2)⁻¹))) x := by
    exact (hasDerivAt_id x).neg.sub hScaled
  have hderiv : -1 - ((ε / 2) * (-(x ^ 2)⁻¹)) = -1 + ε / (2 * x ^ 2) := by
    field_simp [hx]
    ring
  simpa [div_eq_mul_inv, mul_assoc, mul_left_comm, mul_comm, hderiv] using hMain

lemma hasDerivAt_bridgeProfile (ε x : ℝ) (hx : x ≠ 0) :
    HasDerivAt (fun a : ℝ => bridgeProfile a ε) (2 * stdNormalPdfReal (bridgeU x ε)) x := by
  have hU : HasDerivAt (fun a : ℝ => bridgeU a ε) (1 + ε / (2 * x ^ 2)) x :=
    hasDerivAt_bridgeU ε x hx
  have hV : HasDerivAt (fun a : ℝ => bridgeV a ε) (-1 + ε / (2 * x ^ 2)) x :=
    hasDerivAt_bridgeV ε x hx
  have hCDFU : HasDerivAt (fun a : ℝ => stdNormalCDFReal (bridgeU a ε))
      (stdNormalPdfReal (bridgeU x ε) * (1 + ε / (2 * x ^ 2))) x := by
    exact (hasDerivAt_stdNormalCDFReal (bridgeU x ε)).comp x hU
  have hCDFV : HasDerivAt (fun a : ℝ => stdNormalCDFReal (bridgeV a ε))
      (stdNormalPdfReal (bridgeV x ε) * (-1 + ε / (2 * x ^ 2))) x := by
    exact (hasDerivAt_stdNormalCDFReal (bridgeV x ε)).comp x hV
  have hScaledV : HasDerivAt (fun a : ℝ => Real.exp ε * stdNormalCDFReal (bridgeV a ε))
      (Real.exp ε * (stdNormalPdfReal (bridgeV x ε) * (-1 + ε / (2 * x ^ 2)))) x := by
    exact hCDFV.const_mul (Real.exp ε)
  have hMain : HasDerivAt (fun a : ℝ => bridgeProfile a ε)
      (stdNormalPdfReal (bridgeU x ε) * (1 + ε / (2 * x ^ 2))
        - Real.exp ε * (stdNormalPdfReal (bridgeV x ε) * (-1 + ε / (2 * x ^ 2)))) x := by
    unfold bridgeProfile
    exact hCDFU.sub hScaledV
  have hpdf : Real.exp ε * stdNormalPdfReal (bridgeV x ε) = stdNormalPdfReal (bridgeU x ε) :=
    exp_eps_mul_stdNormalPdf_bridgeV_eq_stdNormalPdf_bridgeU x ε hx
  have hpdf' :
      Real.exp ε * (stdNormalPdfReal (bridgeV x ε) * (-1 + ε / (2 * x ^ 2)))
        = stdNormalPdfReal (bridgeU x ε) * (-1 + ε / (2 * x ^ 2)) := by
    calc
      Real.exp ε * (stdNormalPdfReal (bridgeV x ε) * (-1 + ε / (2 * x ^ 2)))
          = (Real.exp ε * stdNormalPdfReal (bridgeV x ε)) * (-1 + ε / (2 * x ^ 2)) := by ring
      _ = stdNormalPdfReal (bridgeU x ε) * (-1 + ε / (2 * x ^ 2)) := by rw [hpdf]
  have hderiv :
      stdNormalPdfReal (bridgeU x ε) * (1 + ε / (2 * x ^ 2))
        - Real.exp ε * (stdNormalPdfReal (bridgeV x ε) * (-1 + ε / (2 * x ^ 2)))
      = 2 * stdNormalPdfReal (bridgeU x ε) := by
    rw [hpdf']
    ring
  simpa [hderiv] using hMain

lemma deriv_bridgeProfile (ε x : ℝ) (hx : x ≠ 0) :
    deriv (fun a : ℝ => bridgeProfile a ε) x = 2 * stdNormalPdfReal (bridgeU x ε) := by
  exact (hasDerivAt_bridgeProfile ε x hx).deriv

theorem strictMonoOn_bridgeProfile (ε : ℝ) :
    StrictMonoOn (fun a : ℝ => bridgeProfile a ε) (Set.Ioi 0) := by
  refine strictMonoOn_of_deriv_pos (hD := convex_Ioi (0 : ℝ)) ?hcont ?hderiv
  · intro x hx
    exact (hasDerivAt_bridgeProfile ε x (ne_of_gt hx)).continuousAt.continuousWithinAt
  · intro x hx
    have hint : interior (Set.Ioi (0 : ℝ)) = Set.Ioi (0 : ℝ) := interior_Ioi
    have hx0 : 0 < x := by simpa [hint] using hx
    have hderivEq : deriv (fun a : ℝ => bridgeProfile a ε) x = 2 * stdNormalPdfReal (bridgeU x ε) :=
      deriv_bridgeProfile ε x (ne_of_gt hx0)
    rw [hderivEq]
    have hpdfPos : 0 < stdNormalPdfReal (bridgeU x ε) := stdNormalPdfReal_pos (bridgeU x ε)
    positivity

lemma privacyLossArgPlus_eq_bridgeU
    (Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hΔ : Δ ≠ 0) :
    privacyLossArgPlus Δ σ ε = bridgeU (Δ / (2 * σ)) ε := by
  unfold privacyLossArgPlus bridgeU
  field_simp [hσ.ne', hΔ]

lemma privacyLossArgMinus_eq_bridgeV
    (Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hΔ : Δ ≠ 0) :
    privacyLossArgMinus Δ σ ε = bridgeV (Δ / (2 * σ)) ε := by
  unfold privacyLossArgMinus bridgeV
  field_simp [hσ.ne', hΔ]

lemma explicitEventExpr_eq_bridgeProfile
    (Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hΔ : Δ ≠ 0) :
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε)))
      = bridgeProfile (Δ / (2 * σ)) ε := by
  rw [privacyLossArgPlus_eq_bridgeU Δ σ ε hσ hΔ]
  rw [privacyLossArgMinus_eq_bridgeV Δ σ ε hσ hΔ]
  simp [bridgeProfile, stdNormalCDFReal_eq_real_measure_Iic]

lemma explicitEventExpr_two_sqrt_eq_bridgeProfile
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
      = bridgeProfile (Real.sqrt r / σ) ε := by
  rw [privacyLossArgPlus_two_sqrt r σ ε hσ hr]
  rw [privacyLossArgMinus_two_sqrt r σ ε hσ hr]
  rw [bridgeProfile, stdNormalCDFReal_eq_real_measure_Iic, stdNormalCDFReal_eq_real_measure_Iic]
  have hsqrt_ne : Real.sqrt r ≠ 0 := (Real.sqrt_pos.2 hr).ne'
  have hU :
      Real.sqrt r / σ - ε * σ / (2 * Real.sqrt r)
        = bridgeU (Real.sqrt r / σ) ε := by
    unfold bridgeU
    field_simp [hσ.ne', hsqrt_ne]
  have hV :
      -Real.sqrt r / σ - ε * σ / (2 * Real.sqrt r)
        = bridgeV (Real.sqrt r / σ) ε := by
    unfold bridgeV
    field_simp [hσ.ne', hsqrt_ne]
  simp [hU, hV]

lemma explicitEventExpr_two_sqrt_le_of_le
    (r Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r)
    (hΔ : 0 < Δ)
    (hrad : r ≤ (Δ / 2) ^ 2) :
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
    ≤
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))) := by
  have ha_pos : 0 < Real.sqrt r / σ := by
    exact div_pos (Real.sqrt_pos.2 hr) hσ
  have hb_pos : 0 < Δ / (2 * σ) := by
    have hden : 0 < 2 * σ := by nlinarith
    exact div_pos hΔ hden
  have hsqrt_le : Real.sqrt r ≤ Δ / 2 := by
    have hnonneg : 0 ≤ Δ / 2 := by linarith
    exact (Real.sqrt_le_iff).2 ⟨hnonneg, by simpa [pow_two] using hrad⟩
  have ha_le : Real.sqrt r / σ ≤ Δ / (2 * σ) := by
    have hdiv : Real.sqrt r / σ ≤ (Δ / 2) / σ := by
      exact mul_le_mul_of_nonneg_right hsqrt_le (le_of_lt (inv_pos.mpr hσ))
    simpa [div_eq_mul_inv, mul_assoc, mul_left_comm, mul_comm] using hdiv
  have hmono :
      bridgeProfile (Real.sqrt r / σ) ε ≤ bridgeProfile (Δ / (2 * σ)) ε := by
    exact (strictMonoOn_bridgeProfile ε).monotoneOn (by exact ha_pos) (by exact hb_pos) ha_le
  have hleft := explicitEventExpr_two_sqrt_eq_bridgeProfile r σ ε hσ hr
  have hright := explicitEventExpr_eq_bridgeProfile Δ σ ε hσ (ne_of_gt hΔ)
  calc
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
        = bridgeProfile (Real.sqrt r / σ) ε := hleft
    _ ≤ bridgeProfile (Δ / (2 * σ)) ε := hmono
    _ = (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))) := by
          exact hright.symm

lemma explicitEventExpr_two_sqrt_le_of_le_nonneg
    (r Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r)
    (hΔ0 : 0 ≤ Δ)
    (hrad : r ≤ (Δ / 2) ^ 2) :
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
    ≤
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))) := by
  have hΔ : 0 < Δ := by
    by_contra hnot
    have hΔle : Δ ≤ 0 := le_of_not_gt hnot
    have hΔeq : Δ = 0 := le_antisymm hΔle hΔ0
    have hpow0 : (Δ / 2) ^ 2 = 0 := by simp [hΔeq]
    have hrle0 : r ≤ 0 := by simpa [hpow0] using hrad
    exact (not_le_of_gt hr) hrle0
  exact explicitEventExpr_two_sqrt_le_of_le r Δ σ ε hσ hr hΔ hrad

lemma centered_posRegion_gap_eq_explicitEventExpr_two_sqrt
    {n : ℕ}
    (d : Vector n)
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r)
    (hrEq : r = sqDist d (fun _ => (0 : ℝ))) :
    (measure σ d).real
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      - Real.exp ε
          * (measure σ (fun i => -d i)).real
              (posRegion
                (fun y : Vector n =>
                  density σ d y
                    - Real.exp ε * density σ (fun i => -d i) y))
    =
      (stdNormalMeasure.real
          (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
        - Real.exp ε
            * stdNormalMeasure.real
                (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))) := by
  have hσ0 : σ ≠ 0 := ne_of_gt hσ
  have hdot : dot d d = r := by
    calc
      dot d d = sqDist d (fun _ => (0 : ℝ)) := dot_self_eq_sqDist_zero d
      _ = r := by simp [hrEq]
  have hleft :
      (measure σ d).real
          (posRegion
            (fun y : Vector n =>
              density σ d y
                - Real.exp ε * density σ (fun i => -d i) y))
        =
          (ProbabilityTheory.gaussianReal (-r)
            (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
            (Set.Iic (-(centeredDotThreshold σ ε))) := by
    have hbase :=
      measure_apply_centered_privacyLoss_posRegion_eq_gaussianReal_event
        (d := d) (σ := σ) (ε := ε) hσ0
    have hreal := congrArg ENNReal.toReal (by simpa [hdot] using hbase)
    simpa [MeasureTheory.Measure.real] using hreal
  have hright :
      (measure σ (fun i => -d i)).real
          (posRegion
            (fun y : Vector n =>
              density σ d y
                - Real.exp ε * density σ (fun i => -d i) y))
        =
          (ProbabilityTheory.gaussianReal r
            (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
            (Set.Iic (-(centeredDotThreshold σ ε))) := by
    have hbase :=
      measure_apply_centered_privacyLoss_posRegion_negMean_eq_gaussianReal_event
        (d := d) (σ := σ) (ε := ε) hσ0
    have hreal := congrArg ENNReal.toReal (by simpa [hdot] using hbase)
    simpa [MeasureTheory.Measure.real] using hreal
  have hcenteredEq :
      (ProbabilityTheory.gaussianReal (-r)
          (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
          (Set.Iic (-(centeredDotThreshold σ ε)))
        - Real.exp ε
            * (ProbabilityTheory.gaussianReal r
              (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
              (Set.Iic (-(centeredDotThreshold σ ε)))
      =
        (stdNormalMeasure.real
            (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
          - Real.exp ε
              * stdNormalMeasure.real
                  (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))) := by
    have hplus := gaussianReal_event_plus_eq_stdNormal r σ ε hσ hr
    have hminus := gaussianReal_event_minus_eq_stdNormal r σ ε hσ hr
    simp [hplus, hminus]
  calc
    (measure σ d).real
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      - Real.exp ε
          * (measure σ (fun i => -d i)).real
              (posRegion
                (fun y : Vector n =>
                  density σ d y
                    - Real.exp ε * density σ (fun i => -d i) y))
        =
          (ProbabilityTheory.gaussianReal (-r)
            (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
            (Set.Iic (-(centeredDotThreshold σ ε)))
            - Real.exp ε
                * (ProbabilityTheory.gaussianReal r
                  (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
                  (Set.Iic (-(centeredDotThreshold σ ε))) := by
            rw [hleft, hright]
    _ =
      (stdNormalMeasure.real
          (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
        - Real.exp ε
            * stdNormalMeasure.real
                (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))) :=
      hcenteredEq

lemma explicitEventExpr_at_centerRadius_le_of_explicitBound
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ r : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hrEq : r = sqDist d (fun _ => (0 : ℝ)))
    (hr : 0 < r)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ) :
    stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))
      ≤ δ := by
  have hrad : r ≤ (Δ / 2) ^ 2 := by simpa [hrEq] using hdist
  have htransfer :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))
      ≤
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε)) :=
    explicitEventExpr_two_sqrt_le_of_le_nonneg r Δ σ ε hσ hr hΔ0 hrad
  exact le_trans htransfer hExplicit

lemma centered_posRegion_gap_le_of_explicitBound_of_posRadius
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ r : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hrEq : r = sqDist d (fun _ => (0 : ℝ)))
    (hr : 0 < r)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ) :
    (measure σ d).real
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      - Real.exp ε
          * (measure σ (fun i => -d i)).real
              (posRegion
                (fun y : Vector n =>
                  density σ d y
                    - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ := by
  have hEq :=
    centered_posRegion_gap_eq_explicitEventExpr_two_sqrt
      (d := d) (r := r) (σ := σ) (ε := ε) hσ hr hrEq
  have hAtR :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))
      ≤ δ :=
    explicitEventExpr_at_centerRadius_le_of_explicitBound
      (d := d) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ) (r := r)
      hσ hΔ0 hrEq hr hdist hExplicit
  simpa [hEq] using hAtR

lemma centered_posRegion_gap_le_of_explicitBound_of_posDist
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hpos : 0 < sqDist d (fun _ => (0 : ℝ))) :
    (measure σ d).real
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      - Real.exp ε
          * (measure σ (fun i => -d i)).real
              (posRegion
                (fun y : Vector n =>
                  density σ d y
                    - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ := by
  exact
    centered_posRegion_gap_le_of_explicitBound_of_posRadius
      (d := d)
      (Δ := Δ) (σ := σ) (ε := ε) (δ := δ)
      (r := sqDist d (fun _ => (0 : ℝ)))
      hσ hΔ0 rfl hpos hdist hExplicit

lemma centered_posRegion_gap_le_of_privacyLossEventBound_of_posDist
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hEvent :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hpos : 0 < sqDist d (fun _ => (0 : ℝ))) :
    (measure σ d).real
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      - Real.exp ε
          * (measure σ (fun i => -d i)).real
              (posRegion
                (fun y : Vector n =>
                  density σ d y
                    - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ := by
  exact centered_posRegion_gap_le_of_explicitBound_of_posDist
    (d := d) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ)
    hσ hΔ0 hdist hEvent hpos

lemma centered_posRegion_gap_le_of_analyticGaussianCondition_of_posDist
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hAnalytic : analyticGaussianCondition Δ σ ε δ)
    (hpos : 0 < sqDist d (fun _ => (0 : ℝ))) :
    (measure σ d).real
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      - Real.exp ε
          * (measure σ (fun i => -d i)).real
              (posRegion
                (fun y : Vector n =>
                  density σ d y
                    - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ := by
  have hEvent :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ := by
    exact (analyticGaussianCondition_iff_event_form Δ σ ε δ).1 hAnalytic
  exact centered_posRegion_gap_le_of_privacyLossEventBound_of_posDist
    (d := d) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ)
    hσ hΔ0 hdist hEvent hpos

lemma signedMeasure_le_of_hahn_cap
    {α : Type*}
    [MeasurableSpace α]
    (s : MeasureTheory.SignedMeasure α)
    (i : Set α)
    (δ : ℝ)
    (hi : MeasurableSet i)
    (hpos : ∀ ⦃j : Set α⦄, MeasurableSet j → j ⊆ i → 0 ≤ s j)
    (hneg : ∀ ⦃j : Set α⦄, MeasurableSet j → j ⊆ iᶜ → s j ≤ 0)
    (hcap : s i ≤ δ) :
    ∀ t, MeasurableSet t → s t ≤ δ := by
  intro t ht
  have hti_meas : MeasurableSet (t ∩ i) := ht.inter hi
  have htic_meas : MeasurableSet (t ∩ iᶜ) := ht.inter hi.compl
  have hti_nonpos_comp : s (t ∩ iᶜ) ≤ 0 := by
    exact hneg htic_meas Set.inter_subset_right
  have hti_le_i : s (t ∩ i) ≤ s i := by
    have hdiff_nonneg : 0 ≤ s (i \ t) := by
      exact hpos (hi.diff ht) Set.diff_subset
    have hi_decomp :
        s (i ∩ t) + s (i \ t) = s i := by
      have hbase : s (i ∩ t) + s (i \ (i ∩ t)) = s i := by
        exact s.of_add_of_diff (hi.inter ht) hi Set.inter_subset_left
      have hdiff_eq : i \ (i ∩ t) = i \ t := by
        ext x
        simp
      simpa [hdiff_eq] using hbase
    have hswap : s (i ∩ t) = s (t ∩ i) := by simp [Set.inter_comm]
    rw [hswap] at hi_decomp
    linarith
  have ht_decomp : s (t ∩ i) + s (t ∩ iᶜ) = s t := by
    have hbase : s (t ∩ i) + s (t \ (t ∩ i)) = s t := by
      exact s.of_add_of_diff hti_meas ht Set.inter_subset_left
    have hdiff_eq : t \ (t ∩ i) = t ∩ iᶜ := by
      ext x
      simp
    simpa [hdiff_eq] using hbase
  linarith [hcap, hti_le_i, hti_nonpos_comp, ht_decomp]

lemma measure_event_le_of_signed_gap_le
    {α : Type*}
    [MeasurableSpace α]
    (μ ν : MeasureTheory.Measure α)
    [MeasureTheory.IsFiniteMeasure μ]
    [MeasureTheory.IsFiniteMeasure ν]
    (ε δ : ℝ)
    {t : Set α}
    (hgap : (μ.real t - Real.exp ε * ν.real t) ≤ δ) :
    μ t ≤ ENNReal.ofReal (Real.exp ε) * ν t + ENNReal.ofReal δ := by
  have hμ_apply : μ t = ENNReal.ofReal (μ.real t) := by
    simp [MeasureTheory.Measure.real, ENNReal.ofReal_toReal]
  have hν_apply : ν t = ENNReal.ofReal (ν.real t) := by
    simp [MeasureTheory.Measure.real, ENNReal.ofReal_toReal]
  have h_nonneg_mul : 0 ≤ Real.exp ε * ν.real t := by
    exact mul_nonneg (le_of_lt (Real.exp_pos ε)) (by
      exact ENNReal.toReal_nonneg)
  have hreal : μ.real t ≤ Real.exp ε * ν.real t + δ := by linarith
  have h_ofReal :
      ENNReal.ofReal (μ.real t) ≤ ENNReal.ofReal (Real.exp ε * ν.real t + δ) := by
    exact ENNReal.ofReal_le_ofReal hreal
  have hsplit :
      ENNReal.ofReal (Real.exp ε * ν.real t + δ)
        ≤ ENNReal.ofReal (Real.exp ε * ν.real t) + ENNReal.ofReal δ := by
    exact ENNReal.ofReal_add_le
  calc
    μ t = ENNReal.ofReal (μ.real t) := hμ_apply
    _ ≤ ENNReal.ofReal (Real.exp ε * ν.real t + δ) := h_ofReal
    _ ≤ ENNReal.ofReal (Real.exp ε * ν.real t) + ENNReal.ofReal δ := hsplit
    _ = ENNReal.ofReal (Real.exp ε) * ENNReal.ofReal (ν.real t) + ENNReal.ofReal δ := by
          rw [ENNReal.ofReal_mul (le_of_lt (Real.exp_pos ε))]
    _ = ENNReal.ofReal (Real.exp ε) * ν t + ENNReal.ofReal δ := by
          rw [hν_apply]

lemma centered_signed_gap_eq
    {n : ℕ}
    (d : Vector n)
    (σ ε : ℝ)
    (s : Set (Vector n))
    (hs : MeasurableSet s) :
    let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩
    ((measure σ d).toSignedMeasure
      - ((c • measure σ (fun i => -d i)).toSignedMeasure)) s
    =
    (measure σ d).real s
        - Real.exp ε * (measure σ (fun i => -d i)).real s := by
  dsimp
  letI : MeasureTheory.IsFiniteMeasure (measure σ d) := inferInstance
  letI : MeasureTheory.IsFiniteMeasure (measure σ (fun i => -d i)) := inferInstance
  let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩
  letI : MeasureTheory.IsFiniteMeasure ((ENNReal.ofNNReal c) • measure σ (fun i => -d i)) :=
    MeasureTheory.Measure.smul_finite _ (by simp)
  letI : MeasureTheory.IsFiniteMeasure (c • measure σ (fun i => -d i)) := inferInstance
  calc
    ((measure σ d).toSignedMeasure
      - ((let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩;
          c • measure σ (fun i => -d i)).toSignedMeasure)) s
      =
      (measure σ d).real s
        - ((let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩;
            c • measure σ (fun i => -d i)).real s) := by
          rw [MeasureTheory.Measure.toSignedMeasure_sub_apply
            (μ := measure σ d)
            (ν := (let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩;
              c • measure σ (fun i => -d i)))
            hs]
    _ =
      (measure σ d).real s
        - Real.exp ε * (measure σ (fun i => -d i)).real s := by
          rw [MeasureTheory.measureReal_nnreal_smul_apply
            (⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩ : NNReal)]
          rfl

lemma gaussianPair_centered_eventApproxDP_of_posRegion_hahn_cap
    {n : ℕ}
    (d : Vector n)
    (σ ε δ : ℝ)
    (hpos :
      ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
        j ⊆ posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y) →
        0 ≤ (measure σ d).real j
          - Real.exp ε * (measure σ (fun i => -d i)).real j)
    (hneg :
      ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
        j ⊆ (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))ᶜ →
        (measure σ d).real j
          - Real.exp ε * (measure σ (fun i => -d i)).real j ≤ 0)
    (hcap :
      (measure σ d).real
          (posRegion
            (fun y : Vector n =>
              density σ d y
                - Real.exp ε * density σ (fun i => -d i) y))
        - Real.exp ε
            * (measure σ (fun i => -d i)).real
                (posRegion
                  (fun y : Vector n =>
                    density σ d y
                      - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ) :
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  intro s hs
  let E : Set (Vector n) :=
    posRegion
      (fun y : Vector n =>
        density σ d y
          - Real.exp ε * density σ (fun i => -d i) y)
  let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩
  let sgap : MeasureTheory.SignedMeasure (Vector n) :=
    (measure σ d).toSignedMeasure
      - ((c • measure σ (fun i => -d i)).toSignedMeasure)
  have hEmeas : MeasurableSet E := by
    unfold E
    change MeasurableSet {y : Vector n |
      0 ≤ density σ d y
        - Real.exp ε * density σ (fun i => -d i) y}
    refine measurableSet_le measurable_const ?_
    have hmeasD : Measurable (fun y : Vector n => density σ d y) := by
      unfold density
      fun_prop
    have hmeasN : Measurable (fun y : Vector n => density σ (fun i => -d i) y) := by
      unfold density
      fun_prop
    exact hmeasD.sub (hmeasN.const_mul (Real.exp ε))
  have hcap_sgap : sgap E ≤ δ := by
    have hEq :
        sgap E
          =
            (measure σ d).real E
              - Real.exp ε * (measure σ (fun i => -d i)).real E := by
      unfold sgap c
      simpa using centered_signed_gap_eq d σ ε E hEmeas
    calc
      sgap E
          =
            (measure σ d).real E
              - Real.exp ε * (measure σ (fun i => -d i)).real E := hEq
      _ ≤ δ := by simpa [E] using hcap
  have hs_sgap :
      sgap s ≤ δ := by
    refine signedMeasure_le_of_hahn_cap sgap E δ hEmeas ?_ ?_ hcap_sgap s hs
    · intro j hj hjE
      have h := hpos hj (by simpa [E] using hjE)
      have hEq :
          sgap j
            =
              (measure σ d).real j
                - Real.exp ε * (measure σ (fun i => -d i)).real j := by
        unfold sgap c
        simpa using centered_signed_gap_eq d σ ε j hj
      calc
        0 ≤ (measure σ d).real j
              - Real.exp ε * (measure σ (fun i => -d i)).real j := h
        _ = sgap j := by simp [hEq]
    · intro j hj hjEc
      have h := hneg hj (by simpa [E] using hjEc)
      have hEq :
          sgap j
            =
              (measure σ d).real j
                - Real.exp ε * (measure σ (fun i => -d i)).real j := by
        unfold sgap c
        simpa using centered_signed_gap_eq d σ ε j hj
      calc
        sgap j =
            (measure σ d).real j
              - Real.exp ε * (measure σ (fun i => -d i)).real j := hEq
        _ ≤ 0 := h
  have hsgapEq : sgap s =
      (measure σ d).real s
        - Real.exp ε * (measure σ (fun i => -d i)).real s := by
    simpa [sgap, c] using centered_signed_gap_eq d σ ε s hs
  have hgap :
      (measure σ d).real s
        - Real.exp ε * (measure σ (fun i => -d i)).real s ≤ δ := by
    simpa [hsgapEq] using hs_sgap
  exact measure_event_le_of_signed_gap_le
    (μ := measure σ d)
    (ν := measure σ (fun i => -d i))
    ε δ hgap

theorem gaussianPair_centered_of_explicitGaussianEventBound_of_posDist_of_hahn
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hposDist : 0 < sqDist d (fun _ => (0 : ℝ)))
    (hpos :
      ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
        j ⊆ posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y) →
        0 ≤ (measure σ d).real j
          - Real.exp ε * (measure σ (fun i => -d i)).real j)
    (hneg :
      ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
        j ⊆ (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))ᶜ →
        (measure σ d).real j
          - Real.exp ε * (measure σ (fun i => -d i)).real j ≤ 0) :
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  have hcap :
      (measure σ d).real
          (posRegion
            (fun y : Vector n =>
              density σ d y
                - Real.exp ε * density σ (fun i => -d i) y))
        - Real.exp ε
            * (measure σ (fun i => -d i)).real
                (posRegion
                  (fun y : Vector n =>
                    density σ d y
                      - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ := by
    exact centered_posRegion_gap_le_of_explicitBound_of_posDist
      (d := d) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ)
      hσ hΔ0 hdist hExplicit hposDist
  exact gaussianPair_centered_eventApproxDP_of_posRegion_hahn_cap
    (d := d) (σ := σ) (ε := ε) (δ := δ) hpos hneg hcap

theorem gaussianPair_centered_of_explicitGaussianEventBound_of_hahn_split
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hpos :
      ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
        j ⊆ posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y) →
        0 ≤ (measure σ d).real j
          - Real.exp ε * (measure σ (fun i => -d i)).real j)
    (hneg :
      ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
        j ⊆ (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))ᶜ →
        (measure σ d).real j
          - Real.exp ε * (measure σ (fun i => -d i)).real j ≤ 0)
    (hzeroEvent :
      sqDist d (fun _ => (0 : ℝ)) = 0 →
      ∀ s, MeasurableSet s →
        measure σ d s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
              + ENNReal.ofReal δ) :
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  by_cases hposDist : 0 < sqDist d (fun _ => (0 : ℝ))
  · exact gaussianPair_centered_of_explicitGaussianEventBound_of_posDist_of_hahn
      (d := d) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ)
      hσ hΔ0 hdist hExplicit hposDist hpos hneg
  · have hsq0 : sqDist d (fun _ => (0 : ℝ)) = 0 := by
      have hsq_nonneg : 0 ≤ sqDist d (fun _ => (0 : ℝ)) := sqDist_nonneg d (fun _ => (0 : ℝ))
      exact le_antisymm (le_of_not_gt hposDist) hsq_nonneg
    exact hzeroEvent hsq0

theorem centered_posRegion_hahn_nonneg_of_pos
    {n : ℕ}
    (d : Vector n)
    (σ ε : ℝ) :
    0 < σ →
    ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
      j ⊆ posRegion
        (fun y : Vector n =>
          density σ d y
            - Real.exp ε * density σ (fun i => -d i) y) →
      0 ≤ (measure σ d).real j
        - Real.exp ε * (measure σ (fun i => -d i)).real j := by
  intro hσ j hj hsub
  have hσ0 : σ ≠ 0 := ne_of_gt hσ
  have hpdf_int :
      MeasureTheory.Integrable (fun y : Vector n => pdfReal σ d y)
        MeasureTheory.volume :=
    integrable_pdfReal (σ := σ) (μ := d) hσ0
  have hpdf_neg_int :
      MeasureTheory.Integrable (fun y : Vector n => pdfReal σ (fun i => -d i) y)
        MeasureTheory.volume :=
    integrable_pdfReal (σ := σ) (μ := fun i => -d i) hσ0
  have hpdf_apply :
      (measure σ d).real j
        = ∫ y in j, pdfReal σ d y ∂MeasureTheory.volume := by
    rw [measure_eq_withDensity_pdf (σ := σ) (μ := d) hσ0]
    rw [MeasureTheory.Measure.real, MeasureTheory.withDensity_apply _ hj]
    have hA :
        ∫⁻ y in j, pdf σ d y ∂MeasureTheory.volume
          = ENNReal.ofReal (∫ y in j, pdfReal σ d y ∂MeasureTheory.volume) := by
      simpa [pdf] using
        (MeasureTheory.ofReal_integral_eq_lintegral_ofReal
          (hpdf_int.restrict)
          (Filter.Eventually.of_forall (fun y => pdfReal_nonneg _ _ _))).symm
    rw [hA]
    exact ENNReal.toReal_ofReal
      (MeasureTheory.setIntegral_nonneg hj (fun y _ => pdfReal_nonneg _ _ _))
  have hpdf_neg_apply :
      (measure σ (fun i => -d i)).real j
        = ∫ y in j, pdfReal σ (fun i => -d i) y ∂MeasureTheory.volume := by
    rw [measure_eq_withDensity_pdf (σ := σ) (μ := fun i => -d i) hσ0]
    rw [MeasureTheory.Measure.real, MeasureTheory.withDensity_apply _ hj]
    have hA :
        ∫⁻ y in j, pdf σ (fun i => -d i) y ∂MeasureTheory.volume
          = ENNReal.ofReal
              (∫ y in j, pdfReal σ (fun i => -d i) y ∂MeasureTheory.volume) := by
      simpa [pdf] using
        (MeasureTheory.ofReal_integral_eq_lintegral_ofReal
          (hpdf_neg_int.restrict)
          (Filter.Eventually.of_forall (fun y => pdfReal_nonneg _ _ _))).symm
    rw [hA]
    exact ENNReal.toReal_ofReal
      (MeasureTheory.setIntegral_nonneg hj (fun y _ => pdfReal_nonneg _ _ _))
  have hsub_pdf :
      j ⊆ posRegion
        (fun y : Vector n =>
          pdfReal σ d y
            - Real.exp ε * pdfReal σ (fun i => -d i) y) := by
    let Epdf : Set (Vector n) :=
      posRegion
        (fun y : Vector n =>
          pdfReal σ d y
            - Real.exp ε * pdfReal σ (fun i => -d i) y)
    let Edens : Set (Vector n) :=
      posRegion
        (fun y : Vector n =>
          density σ d y
            - Real.exp ε * density σ (fun i => -d i) y)
    have hEq : Epdf = Edens := centered_pdf_posRegion_eq_centered_density_posRegion
      (d := d) (σ := σ) (ε := ε) hσ0
    intro y hy
    have hy' := hsub hy
    simpa [hEq, Epdf, Edens] using (show y ∈ Edens from hy')
  have hint_nonneg :
      0 ≤ ∫ y in j,
        (pdfReal σ d y
          - Real.exp ε * pdfReal σ (fun i => -d i) y) ∂MeasureTheory.volume := by
    refine MeasureTheory.setIntegral_nonneg hj ?_
    intro y hy
    exact hsub_pdf hy
  have hrewrite :
      (∫ y in j,
          (pdfReal σ d y
            - Real.exp ε * pdfReal σ (fun i => -d i) y) ∂MeasureTheory.volume)
        =
      (∫ y in j, pdfReal σ d y ∂MeasureTheory.volume)
        - Real.exp ε
            * (∫ y in j, pdfReal σ (fun i => -d i) y ∂MeasureTheory.volume) := by
    rw [MeasureTheory.integral_sub (hpdf_int.restrict) ((hpdf_neg_int.restrict).const_mul _)]
    rw [MeasureTheory.integral_const_mul]
  calc
    0 ≤ ∫ y in j,
      (pdfReal σ d y
        - Real.exp ε * pdfReal σ (fun i => -d i) y) ∂MeasureTheory.volume := hint_nonneg
    _ =
      (measure σ d).real j
        - Real.exp ε * (measure σ (fun i => -d i)).real j := by
          rw [hrewrite, ← hpdf_apply, ← hpdf_neg_apply]

theorem centered_posRegion_hahn_nonpos_compl
    {n : ℕ}
    (d : Vector n)
    (σ ε : ℝ) :
    0 < σ →
    ∀ ⦃j : Set (Vector n)⦄, MeasurableSet j →
      j ⊆ (posRegion
        (fun y : Vector n =>
          density σ d y
            - Real.exp ε * density σ (fun i => -d i) y))ᶜ →
      (measure σ d).real j
        - Real.exp ε * (measure σ (fun i => -d i)).real j ≤ 0 := by
  intro hσ j hj hsubset
  have hsubset' :
      j ⊆
        posRegion
          (fun y : Vector n =>
            density σ (fun i => -d i) y
              - Real.exp (-ε) * density σ (fun i => -(-d i)) y) := by
    intro y hy
    have hyc : y ∈ (posRegion
        (fun y : Vector n =>
          density σ d y
            - Real.exp ε * density σ (fun i => -d i) y))ᶜ := hsubset hy
    have hlt :
        density σ d y
          - Real.exp ε * density σ (fun i => -d i) y < 0 := by
      exact lt_of_not_ge hyc
    have hle :
        density σ d y
          ≤ Real.exp ε * density σ (fun i => -d i) y := by
      linarith
    have hdiv :
        density σ d y / Real.exp ε
          ≤ density σ (fun i => -d i) y := by
      exact (div_le_iff₀ (Real.exp_pos ε)).2 (by simpa [mul_comm] using hle)
    have hrew :
        Real.exp (-ε) * density σ d y
          = density σ d y / Real.exp ε := by
      rw [Real.exp_neg]
      field_simp [Real.exp_ne_zero ε]
    change 0 ≤
      density σ (fun i => -d i) y
        - Real.exp (-ε) * density σ (fun i => -(-d i)) y
    simp only [neg_neg, sub_nonneg]
    rw [hrew]
    linarith
  have hswap :
      0 ≤ (measure σ (fun i => -d i)).real j
            - Real.exp (-ε) * (measure σ (fun i => -(-d i))).real j := by
    exact centered_posRegion_hahn_nonneg_of_pos
      (d := (fun i => -d i)) (σ := σ) (ε := -ε) hσ hj hsubset'
  have hswap' :
      0 ≤ (measure σ (fun i => -d i)).real j
            - Real.exp (-ε) * (measure σ d).real j := by
    simpa using hswap
  have hmul :
      0 ≤ Real.exp ε
        * ((measure σ (fun i => -d i)).real j
            - Real.exp (-ε) * (measure σ d).real j) := by
    exact mul_nonneg (le_of_lt (Real.exp_pos ε)) hswap'
  have hlin :
      0 ≤ Real.exp ε * (measure σ (fun i => -d i)).real j
            - (measure σ d).real j := by
    have htmp :
        Real.exp ε
          * ((measure σ (fun i => -d i)).real j
              - Real.exp (-ε) * (measure σ d).real j)
        =
        Real.exp ε * (measure σ (fun i => -d i)).real j
          - (measure σ d).real j := by
      have hexpMul :
          Real.exp ε * Real.exp (-ε) = 1 := by
        rw [Real.exp_neg]
        field_simp [Real.exp_ne_zero ε]
      rw [mul_sub]
      calc
        Real.exp ε * (measure σ (fun i => -d i)).real j
            - Real.exp ε * (Real.exp (-ε) * (measure σ d).real j)
          = Real.exp ε * (measure σ (fun i => -d i)).real j
              - (Real.exp ε * Real.exp (-ε)) * (measure σ d).real j := by ring
        _ = Real.exp ε * (measure σ (fun i => -d i)).real j
              - 1 * (measure σ d).real j := by rw [hexpMul]
        _ = Real.exp ε * (measure σ (fun i => -d i)).real j
              - (measure σ d).real j := by ring
    simpa [htmp] using hmul
  linarith

theorem gaussianPair_centered_of_posRegionGap_le
    {n : ℕ}
    (d : Vector n)
    (σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hcap :
      (measure σ d).real
          (posRegion
            (fun y : Vector n =>
              density σ d y
                - Real.exp ε * density σ (fun i => -d i) y))
        - Real.exp ε
            * (measure σ (fun i => -d i)).real
                (posRegion
                  (fun y : Vector n =>
                    density σ d y
                      - Real.exp ε * density σ (fun i => -d i) y))
      ≤ δ) :
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  exact gaussianPair_centered_eventApproxDP_of_posRegion_hahn_cap
    (d := d) (σ := σ) (ε := ε) (δ := δ)
    (centered_posRegion_hahn_nonneg_of_pos d σ ε hσ)
    (centered_posRegion_hahn_nonpos_compl d σ ε hσ)
    hcap

theorem gaussianPair_centered_of_explicitGaussianEventBound_lt_one
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ) →
    δ < 1 →
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  intro hσ hε hΔ hdist hExplicit hδlt
  by_cases hposDist : 0 < sqDist d (fun _ => (0 : ℝ))
  · have hcap :
        (measure σ d).real
            (posRegion
              (fun y : Vector n =>
                density σ d y
                  - Real.exp ε * density σ (fun i => -d i) y))
          - Real.exp ε
              * (measure σ (fun i => -d i)).real
                  (posRegion
                    (fun y : Vector n =>
                      density σ d y
                        - Real.exp ε * density σ (fun i => -d i) y))
        ≤ δ := by
      exact centered_posRegion_gap_le_of_privacyLossEventBound_of_posDist
        (d := d) (Δ := Δ) (σ := σ) (ε := ε) (δ := δ)
        hσ hΔ hdist hExplicit hposDist
    exact gaussianPair_centered_of_posRegionGap_le
      (d := d) (σ := σ) (ε := ε) (δ := δ) hσ hcap
  · have hsq0 : sqDist d (fun _ => (0 : ℝ)) = 0 := by
      have hsq_nonneg : 0 ≤ sqDist d (fun _ => (0 : ℝ)) := sqDist_nonneg d (fun _ => (0 : ℝ))
      exact le_antisymm (le_of_not_gt hposDist) hsq_nonneg
    intro s hs
    have hd0 : d = (fun _ => (0 : ℝ)) := (sqDist_eq_zero_iff _ _).mp hsq0
    subst hd0
    have hexp : (1 : ENNReal) ≤ ENNReal.ofReal (Real.exp ε) := by
      simpa using (ENNReal.ofReal_le_ofReal (show (1 : ℝ) ≤ Real.exp ε by
        simpa using (Real.one_le_exp_iff.mpr hε)))
    have hμ :
        measure σ (fun _ => (0 : ℝ)) s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun _ => (0 : ℝ)) s := by
      calc
        measure σ (fun _ => (0 : ℝ)) s
          = (1 : ENNReal) * measure σ (fun _ => (0 : ℝ)) s := by simp
        _ ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun _ => (0 : ℝ)) s := by
            exact mul_le_mul_of_nonneg_right hexp (by simp)
    have hδadd :
        ENNReal.ofReal (Real.exp ε) * measure σ (fun _ => (0 : ℝ)) s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun _ => (0 : ℝ)) s
              + ENNReal.ofReal δ := by
      exact le_add_of_nonneg_right (show 0 ≤ ENNReal.ofReal δ by simp)
    simpa using le_trans hμ hδadd

theorem gaussianPair_centered_of_explicitGaussianEventBound_lt_one_of_pos
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ) →
    δ < 1 →
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤
          ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  intro hσ hε hΔ hdist hExplicit hδlt
  exact gaussianPair_centered_of_explicitGaussianEventBound_lt_one
    d Δ σ ε δ hσ hε hΔ hdist hExplicit hδlt

theorem gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤
          ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  intro hσ hε hΔ hdist hAnalytic hδlt
  have hexplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ := by
    exact (analyticGaussianCondition_iff_event_form Δ σ ε δ).1 hAnalytic
  exact gaussianPair_centered_of_explicitGaussianEventBound_lt_one
    d Δ σ ε δ hσ hε hΔ hdist hexplicit hδlt

theorem gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one_of_pos
    {n : ℕ}
    (d : Vector n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      measure σ d s
        ≤
          ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
            + ENNReal.ofReal δ := by
  intro hσ hε hΔ hdist hAnalytic hδlt
  have hexplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ := by
    exact (analyticGaussianCondition_iff_event_form Δ σ ε δ).1 hAnalytic
  exact
    gaussianPair_centered_of_explicitGaussianEventBound_lt_one_of_pos
      d Δ σ ε δ hσ hε hΔ hdist hexplicit hδlt

theorem gaussianPair_eventApproxDP_of_analyticCondition_lt_one
    {n : ℕ}
    (μ μ' : Vector n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    sqDist μ μ' ≤ Δ ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      measure σ μ s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ μ' s + ENNReal.ofReal δ := by
  intro hσ hε hΔ hdist hAnalytic hδlt
  let d : Vector n := halfDiff μ μ'
  let m : Vector n := Mf.Probability.FiniteGaussian.midpoint μ μ'
  have hsq : sqDist μ μ' = 4 * sqDist d (fun _ => (0 : ℝ)) := by
    simpa [d] using sqDist_eq_four_mul_halfDiff μ μ'
  have hmul : sqDist d (fun _ => (0 : ℝ)) * 4 ≤ Δ ^ 2 := by
    simpa [hsq, mul_comm] using hdist
  have hcenterDist_div : sqDist d (fun _ => (0 : ℝ)) ≤ Δ ^ 2 / 4 := by
    exact (le_div_iff₀ (by norm_num : (0 : ℝ) < 4)).2 hmul
  have hcenterDist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 := by
    have hpow : (Δ / 2) ^ 2 = Δ ^ 2 / 4 := by ring
    simpa [hpow] using hcenterDist_div
  have hcenter :
      ∀ s, MeasurableSet s →
        measure σ d s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
              + ENNReal.ofReal δ :=
    gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one
      d Δ σ ε δ hσ hε hΔ hcenterDist hAnalytic hδlt
  have htransport :=
    gaussianPair_eventApproxDP_transport_add_const
      (σ := σ) (ε := ε) (δ := δ) (μ := d) (μ' := fun i => -d i) (c := m) hcenter
  have hμ : (fun i => d i + m i) = μ := by
    funext i
    simp [d, m, Mf.Probability.FiniteGaussian.midpoint, halfDiff]
    ring
  have hμ' : (fun i => -d i + m i) = μ' := by
    funext i
    simp [d, m, Mf.Probability.FiniteGaussian.midpoint, halfDiff]
    ring
  simpa [hμ, hμ'] using htransport

theorem gaussianPair_eventApproxDP_of_analyticCondition_lt_one_of_pos
    {n : ℕ}
    (μ μ' : Vector n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    sqDist μ μ' ≤ Δ ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      measure σ μ s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ μ' s + ENNReal.ofReal δ := by
  intro hσ hε hΔ hdist hAnalytic hδlt
  let d : Vector n := halfDiff μ μ'
  let m : Vector n := Mf.Probability.FiniteGaussian.midpoint μ μ'
  have hsq : sqDist μ μ' = 4 * sqDist d (fun _ => (0 : ℝ)) := by
    simpa [d] using sqDist_eq_four_mul_halfDiff μ μ'
  have hmul : sqDist d (fun _ => (0 : ℝ)) * 4 ≤ Δ ^ 2 := by
    simpa [hsq, mul_comm] using hdist
  have hcenterDist_div : sqDist d (fun _ => (0 : ℝ)) ≤ Δ ^ 2 / 4 := by
    exact (le_div_iff₀ (by norm_num : (0 : ℝ) < 4)).2 hmul
  have hcenterDist : sqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 := by
    have hpow : (Δ / 2) ^ 2 = Δ ^ 2 / 4 := by ring
    simpa [hpow] using hcenterDist_div
  have hcenter :
      ∀ s, MeasurableSet s →
        measure σ d s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
              + ENNReal.ofReal δ :=
    gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one_of_pos
      d Δ σ ε δ hσ hε hΔ hcenterDist hAnalytic hδlt
  have htransport :=
    gaussianPair_eventApproxDP_transport_add_const
      (σ := σ) (ε := ε) (δ := δ) (μ := d) (μ' := fun i => -d i) (c := m) hcenter
  have hμ : (fun i => d i + m i) = μ := by
    funext i
    simp [d, m, Mf.Probability.FiniteGaussian.midpoint, halfDiff]
    ring
  have hμ' : (fun i => -d i + m i) = μ' := by
    funext i
    simp [d, m, Mf.Probability.FiniteGaussian.midpoint, halfDiff]
    ring
  simpa [hμ, hμ'] using htransport

end
end Mf.DP.FiniteGaussianPrivacy
