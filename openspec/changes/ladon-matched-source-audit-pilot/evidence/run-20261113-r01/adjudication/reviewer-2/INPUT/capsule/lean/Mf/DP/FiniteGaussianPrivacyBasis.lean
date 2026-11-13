import Mf.Probability.FiniteGaussianDensity
import Mf.DP.GaussianPrivacyLoss
import Mf.DP.PrivacyLossCore

/-!
# Finite Gaussian likelihood regions and event transport

Centered density comparisons reduce to a halfspace of the mean-direction
projection. Translation preserves directed event bounds. These measure-level
identities use ordinary finite Gaussian laws, without a mechanism-specific
output space or sensitivity premise.
-/

namespace Mf.DP.FiniteGaussianPrivacyBasis
open Mf.Probability.FiniteGaussian
open scoped BigOperators
noncomputable section

lemma centered_pdf_posRegion_eq_centered_density_posRegion
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    posRegion
      (fun y : Vector n =>
        pdfReal σ d y
          - Real.exp ε * pdfReal σ (-d) y)
      =
    posRegion
      (fun y : Vector n =>
        density σ d y
          - Real.exp ε * density σ (-d) y) := by
  ext y
  change
    (0 ≤
      pdfReal σ d y
        - Real.exp ε * pdfReal σ (-d) y)
      ↔
    (0 ≤
      density σ d y
        - Real.exp ε * density σ (-d) y)
  exact centered_pdf_gap_nonneg_iff (d := d) (y := y) (σ := σ) (ε := ε) hσ

lemma centered_privacyLoss_posRegion_eq_halfspace
    {n : ℕ} (d : Vector n) (σ ε : ℝ) :
    posRegion
      (fun y : Vector n =>
        density σ d y
          - Real.exp ε * density σ (fun i => -d i) y)
      = {y : Vector n | ε ≤ (2 * dot d y) / (σ ^ 2)} := by
  ext y
  simp [posRegion, sub_nonneg, density_centered_ratio_ge_iff]

lemma centered_privacyLoss_halfspace_eq_dot_ge
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    {y : Vector n | ε ≤ (2 * dot d y) / (σ ^ 2)}
      = {y : Vector n | (ε * σ ^ 2) / 2 ≤ dot d y} := by
  ext y
  have hσ2 : 0 < σ ^ 2 := sq_pos_of_ne_zero hσ
  constructor
  · intro hy
    have hy' : ε ≤ (2 * dot d y) / (σ ^ 2) := by simpa using hy
    have hmul : ε * σ ^ 2 ≤ 2 * dot d y := (le_div_iff₀ hσ2).1 hy'
    have : (ε * σ ^ 2) / 2 ≤ dot d y := by
      nlinarith
    simpa using this
  · intro hy
    have hy' : (ε * σ ^ 2) / 2 ≤ dot d y := by simpa using hy
    have hmul : ε * σ ^ 2 ≤ 2 * dot d y := by
      nlinarith [hy']
    exact (le_div_iff₀ hσ2).2 hmul

lemma centered_privacyLoss_posRegion_eq_dot_ge
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    posRegion
      (fun y : Vector n =>
        density σ d y
          - Real.exp ε * density σ (fun i => -d i) y)
      = {y : Vector n | (ε * σ ^ 2) / 2 ≤ dot d y} := by
  rw [centered_privacyLoss_posRegion_eq_halfspace]
  exact centered_privacyLoss_halfspace_eq_dot_ge d σ ε hσ

lemma measurableSet_centered_privacyLoss_posRegion
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    MeasurableSet
      (posRegion
        (fun y : Vector n =>
          density σ d y
            - Real.exp ε * density σ (fun i => -d i) y)) := by
  rw [centered_privacyLoss_posRegion_eq_dot_ge (d := d) (σ := σ) (ε := ε) hσ]
  exact measurableSet_le measurable_const (measurable_dot_left d)

def centeredDotThreshold (σ ε : ℝ) : ℝ :=
  (ε * σ ^ 2) / 2

lemma centeredDot_arg_plus
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    ((-(centeredDotThreshold σ ε) - (-r)) / (σ * Real.sqrt r))
      = Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) := by
  have hden : σ * Real.sqrt r ≠ 0 := by
    exact mul_ne_zero (ne_of_gt hσ) (Real.sqrt_pos.2 hr).ne'
  field_simp [centeredDotThreshold, hden]
  ring_nf
  have hsq : (Real.sqrt r) ^ 2 = r := by nlinarith [Real.sq_sqrt (le_of_lt hr)]
  simp [centeredDotThreshold] at *
  nlinarith [hsq]

lemma centeredDot_arg_minus
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r) :
    ((-(centeredDotThreshold σ ε) - r) / (σ * Real.sqrt r))
      = -Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) := by
  have hden : σ * Real.sqrt r ≠ 0 := by
    exact mul_ne_zero (ne_of_gt hσ) (Real.sqrt_pos.2 hr).ne'
  field_simp [centeredDotThreshold, hden]
  ring_nf
  have hsq : (Real.sqrt r) ^ 2 = r := by nlinarith [Real.sq_sqrt (le_of_lt hr)]
  simp [centeredDotThreshold] at *
  nlinarith [hsq]

theorem centered_privacyLoss_posRegion_eq_dot_preimage
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    posRegion
      (fun y : Vector n =>
        density σ d y
          - Real.exp ε * density σ (fun i => -d i) y)
      = (fun y : Vector n => dot d y) ⁻¹' Set.Ici (centeredDotThreshold σ ε) := by
  rw [centered_privacyLoss_posRegion_eq_dot_ge (d := d) (σ := σ) (ε := ε) hσ]
  ext y
  simp [centeredDotThreshold]

theorem measure_apply_eval_preimage_Iic_eq_stdNormal
    {n : ℕ} (σ : ℝ) (μ : Vector n) (i : Fin n) (t : ℝ)
    (hσ : 0 < σ) :
    measure σ μ (Function.eval i ⁻¹' Set.Iic t)
      = stdNormalMeasure (Set.Iic ((t - μ i) / σ)) := by
  rw [measure_apply_eval_preimage_Iic (σ := σ) (μ := μ) (i := i) (t := t)]
  exact gaussianReal_apply_Iic_eq_stdNormalMeasure_affine (μ i) σ t hσ

theorem measure_apply_centered_privacyLoss_posRegion
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    measure σ d
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      =
        ((measure σ d).map (fun y : Vector n => dot d y))
          (Set.Ici (centeredDotThreshold σ ε)) := by
  let f : Vector n → ℝ := fun y => dot d y
  have hmeas : Measurable f := measurable_dot_left d
  rw [centered_privacyLoss_posRegion_eq_dot_preimage (d := d) (σ := σ) (ε := ε) hσ]
  rw [← MeasureTheory.Measure.map_apply hmeas measurableSet_Ici]

theorem measure_apply_centered_privacyLoss_posRegion_Iic
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    measure σ d
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      =
        ((measure σ d).map (fun y : Vector n => -dot d y))
          (Set.Iic (-(centeredDotThreshold σ ε))) := by
  rw [measure_apply_centered_privacyLoss_posRegion (d := d) (σ := σ) (ε := ε) hσ]
  exact measure_map_apply_Ici_eq_map_neg_apply_Iic
    (μ := measure σ d)
    (f := fun y : Vector n => dot d y)
    (hf := measurable_dot_left d)
    (t := centeredDotThreshold σ ε)

theorem measure_apply_centered_privacyLoss_posRegion_Iic_of_mean
    {n : ℕ} (μ d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    measure σ μ
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      =
        ((measure σ μ).map (fun y : Vector n => -dot d y))
          (Set.Iic (-(centeredDotThreshold σ ε))) := by
  let f : Vector n → ℝ := fun y => dot d y
  have hmeas : Measurable f := measurable_dot_left d
  rw [centered_privacyLoss_posRegion_eq_dot_preimage (d := d) (σ := σ) (ε := ε) hσ]
  rw [← MeasureTheory.Measure.map_apply hmeas measurableSet_Ici]
  exact measure_map_apply_Ici_eq_map_neg_apply_Iic
    (μ := measure σ μ)
    (f := f)
    (hf := hmeas)
    (t := centeredDotThreshold σ ε)

theorem measure_apply_centered_privacyLoss_posRegion_eq_gaussianReal_event
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    measure σ d
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      =
        (ProbabilityTheory.gaussianReal (-(dot d d))
          (⟨σ ^ 2 * dot d d,
            mul_nonneg (sq_nonneg σ) (dot_self_nonneg d)⟩))
          (Set.Iic (-(centeredDotThreshold σ ε))) := by
  rw [measure_apply_centered_privacyLoss_posRegion_Iic (d := d) (σ := σ) (ε := ε) hσ]
  rw [measure_map_neg_dot_eq_gaussianReal (σ := σ) (μ := d) (d := d)]

theorem measure_apply_centered_privacyLoss_posRegion_negMean_eq_gaussianReal_event
    {n : ℕ} (d : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    measure σ (fun i => -d i)
        (posRegion
          (fun y : Vector n =>
            density σ d y
              - Real.exp ε * density σ (fun i => -d i) y))
      =
        (ProbabilityTheory.gaussianReal (dot d d)
          (⟨σ ^ 2 * dot d d,
            mul_nonneg (sq_nonneg σ) (dot_self_nonneg d)⟩))
          (Set.Iic (-(centeredDotThreshold σ ε))) := by
  rw [measure_apply_centered_privacyLoss_posRegion_Iic_of_mean
      (μ := (fun i => -d i)) (d := d) (σ := σ) (ε := ε) hσ]
  rw [measure_map_neg_dot_negMean_eq_gaussianReal (σ := σ) (d := d)]

theorem gaussianPair_eventApproxDP_transport_add_const
    {n : ℕ}
    (σ ε δ : ℝ)
    (μ μ' c : Vector n)
    (hpair :
      ∀ s, MeasurableSet s →
        measure σ μ s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ μ' s + ENNReal.ofReal δ) :
    ∀ s, MeasurableSet s →
      measure σ (fun i => μ i + c i) s
        ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => μ' i + c i) s
            + ENNReal.ofReal δ := by
  intro s hs
  let T : Vector n → Vector n := fun x i => x i + c i
  have hTmeas : Measurable T := by
    fun_prop
  have hs_pre : MeasurableSet (T ⁻¹' s) := hs.preimage hTmeas
  have hbase := hpair (T ⁻¹' s) hs_pre
  have hleft :
      measure σ (fun i => μ i + c i) s
        = measure σ μ (T ⁻¹' s) := by
    rw [← measure_map_add_const (σ := σ) (μ := μ) (c := c)]
    rw [MeasureTheory.Measure.map_apply hTmeas hs]
  have hright :
      measure σ (fun i => μ' i + c i) s
        = measure σ μ' (T ⁻¹' s) := by
    rw [← measure_map_add_const (σ := σ) (μ := μ') (c := c)]
    rw [MeasureTheory.Measure.map_apply hTmeas hs]
  rw [hleft, hright]
  exact hbase

theorem analyticGaussianExpr_iff_measure_eval_event_form
    {n : ℕ} (i : Fin n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ) :
    analyticGaussianExpr Δ σ ε ≤ δ
      ↔ (measure σ (fun _ : Fin n => Δ / 2)).real
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
          - Real.exp ε
              * (measure σ (fun _ : Fin n => -Δ / 2)).real
                  (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
        ≤ δ := by
  have hplus :
      (measure σ (fun _ : Fin n => Δ / 2)).real
          (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
        = stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε)) := by
    have hplusENN :
        measure σ (fun _ : Fin n => Δ / 2)
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
          = stdNormalMeasure
              (Set.Iic
                ((privacyEventThresholdPlus Δ σ ε - (Δ / 2)) / σ)) := by
      simpa using
        measure_apply_eval_preimage_Iic_eq_stdNormal
          (σ := σ) (μ := (fun _ : Fin n => Δ / 2))
          (i := i) (t := privacyEventThresholdPlus Δ σ ε) hσ
    have harg :
        ((privacyEventThresholdPlus Δ σ ε - (Δ / 2)) / σ)
          = privacyLossArgPlus Δ σ ε := by
      unfold privacyEventThresholdPlus
      field_simp [hσ.ne']
      ring
    have hplusRealRaw :
        (measure σ (fun _ : Fin n => Δ / 2)).real
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
          = stdNormalMeasure.real
              (Set.Iic ((privacyEventThresholdPlus Δ σ ε - (Δ / 2)) / σ)) := by
      simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hplusENN
    rw [hplusRealRaw, harg]
  have hminus :
      (measure σ (fun _ : Fin n => -Δ / 2)).real
          (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
        = stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε)) := by
    have hminusENN :
        measure σ (fun _ : Fin n => -Δ / 2)
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
          = stdNormalMeasure
              (Set.Iic
                ((privacyEventThresholdMinus Δ σ ε - (-Δ / 2)) / σ)) := by
      simpa using
        measure_apply_eval_preimage_Iic_eq_stdNormal
          (σ := σ) (μ := (fun _ : Fin n => -Δ / 2))
          (i := i) (t := privacyEventThresholdMinus Δ σ ε) hσ
    have harg :
        ((privacyEventThresholdMinus Δ σ ε - (-Δ / 2)) / σ)
          = privacyLossArgMinus Δ σ ε := by
      unfold privacyEventThresholdMinus
      field_simp [hσ.ne']
      ring
    have hminusRealRaw :
        (measure σ (fun _ : Fin n => -Δ / 2)).real
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
          = stdNormalMeasure.real
              (Set.Iic ((privacyEventThresholdMinus Δ σ ε - (-Δ / 2)) / σ)) := by
      simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hminusENN
    rw [hminusRealRaw, harg]
  rw [analyticGaussianExpr_eq_event_form]
  rw [hplus, hminus]

theorem gaussianPair_eventApproxDP_of_centered
    {n : ℕ}
    (σ ε δ : ℝ)
    (d : Vector n)
    (hcenter :
      ∀ s, MeasurableSet s →
        measure σ d s
          ≤ ENNReal.ofReal (Real.exp ε) * measure σ (fun i => -d i) s
              + ENNReal.ofReal δ) :
    ∀ s, MeasurableSet s →
      measure σ (fun i => midpoint d (fun j => -d j) i + d i) s
        ≤ ENNReal.ofReal (Real.exp ε)
            * measure σ (fun i => midpoint d (fun j => -d j) i - d i) s
            + ENNReal.ofReal δ := by
  intro s hs
  simpa [Mf.Probability.FiniteGaussian.midpoint] using hcenter s hs

end
end Mf.DP.FiniteGaussianPrivacyBasis
