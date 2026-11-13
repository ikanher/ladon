import Mf.DP.GaussianApproxDP
import Mf.DP.FiniteGaussianPrivacyBasis

/-!
# BSR compatibility for finite Gaussian mathematics

Generic probability implementations live in
`Mf.Probability.FiniteGaussianDensity`; likelihood-region and event transport
proofs live in `Mf.DP.FiniteGaussianPrivacyBasis`. This owner retains the
historical names and BSR application adapters as downstream consumers.
-/

namespace Mf.DP
noncomputable section

abbrev BSROutput := @Mf.Probability.FiniteGaussian.Vector

abbrev bsrDot := @Mf.Probability.FiniteGaussian.dot

theorem measurable_bsrDot_left :
    ∀ {n : ℕ} (u : BSROutput n),
    Measurable (fun v : BSROutput n => bsrDot u v) :=
  @Mf.Probability.FiniteGaussian.measurable_dot_left

theorem bsrDot_add_right :
    ∀ {n : ℕ} (u v w : BSROutput n),
    bsrDot u (fun i => v i + w i) = bsrDot u v + bsrDot u w :=
  @Mf.Probability.FiniteGaussian.dot_add_right

theorem bsrDot_sub_right :
    ∀ {n : ℕ} (u v w : BSROutput n),
    bsrDot u (fun i => v i - w i) = bsrDot u v - bsrDot u w :=
  @Mf.Probability.FiniteGaussian.dot_sub_right

theorem bsrDot_neg_right :
    ∀ {n : ℕ} (u v : BSROutput n),
    bsrDot u (fun i => -v i) = -bsrDot u v :=
  @Mf.Probability.FiniteGaussian.dot_neg_right

theorem bsrDot_neg_left :
    ∀ {n : ℕ} (u v : BSROutput n),
    bsrDot (fun i => -u i) v = -bsrDot u v :=
  @Mf.Probability.FiniteGaussian.dot_neg_left

theorem bsrDot_self_eq_sum_sq :
    ∀ {n : ℕ} (u : BSROutput n),
    bsrDot u u = ∑ i : Fin n, (u i) ^ 2 :=
  @Mf.Probability.FiniteGaussian.dot_self_eq_sum_sq

theorem bsrDot_self_nonneg :
    ∀ {n : ℕ} (u : BSROutput n),
    0 ≤ bsrDot u u :=
  @Mf.Probability.FiniteGaussian.dot_self_nonneg

abbrev bsrGaussianDensity := @Mf.Probability.FiniteGaussian.density

abbrev gaussianNormConst := @Mf.Probability.FiniteGaussian.normalization

private abbrev bsrGaussianVariance := @Mf.Probability.FiniteGaussian.variance

theorem bsrGaussianVariance_eq_mk :
    ∀ (σ : ℝ),
    bsrGaussianVariance σ = ⟨σ ^ 2, sq_nonneg σ⟩ :=
  @Mf.Probability.FiniteGaussian.variance_eq_mk

theorem bsrGaussianDensity_nonneg :
    ∀ {n : ℕ} (σ : ℝ) (μ y : BSROutput n),
    0 ≤ bsrGaussianDensity σ μ y :=
  @Mf.Probability.FiniteGaussian.density_nonneg

theorem bsrGaussianDensity_le_one :
    ∀ {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0) (μ y : BSROutput n),
    bsrGaussianDensity σ μ y ≤ 1 :=
  @Mf.Probability.FiniteGaussian.density_le_one

theorem bsrGaussianDensity_le_exp_neg_sqLower :
    ∀ {n : ℕ} {σ sqLower : ℝ} (hσ : σ ≠ 0) (μ y : BSROutput n)
    (hLower : sqLower ≤ ∑ i : Fin n, (y i - μ i) ^ 2),
    bsrGaussianDensity σ μ y
      ≤ Real.exp (-sqLower / (2 * σ ^ 2)) :=
  @Mf.Probability.FiniteGaussian.density_le_exp_neg_sqLower

theorem gaussianNormConst_pos :
    ∀ {σ : ℝ} (hσ : σ ≠ 0),
    0 < gaussianNormConst σ :=
  @Mf.Probability.FiniteGaussian.normalization_pos

theorem gaussianNormConst_pow_pos :
    ∀ {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0),
    0 < (gaussianNormConst σ) ^ n :=
  @Mf.Probability.FiniteGaussian.normalization_pow_pos

theorem gaussianPDFReal_eq_normConst_mul_exp :
    ∀ (σ μ x : ℝ),
    ProbabilityTheory.gaussianPDFReal μ (bsrGaussianVariance σ) x
      =
        gaussianNormConst σ
          * Real.exp (-(x - μ) ^ 2 / (2 * σ ^ 2)) :=
  @Mf.Probability.FiniteGaussian.gaussianPDFReal_eq_normConst_mul_exp

abbrev bsrGaussianPdfReal := @Mf.Probability.FiniteGaussian.pdfReal

theorem bsrGaussianPdfReal_eq_posConst_mul_bsrGaussianDensity :
    ∀ {n : ℕ} (σ : ℝ) (μ y : BSROutput n),
    bsrGaussianPdfReal σ μ y
      =
        (gaussianNormConst σ) ^ n * bsrGaussianDensity σ μ y :=
  @Mf.Probability.FiniteGaussian.pdfReal_eq_posConst_mul_density

theorem bsrGaussianPdfReal_le_normConst_pow :
    ∀ {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0) (μ y : BSROutput n),
    bsrGaussianPdfReal σ μ y ≤ (gaussianNormConst σ) ^ n :=
  @Mf.Probability.FiniteGaussian.pdfReal_le_normConst_pow

theorem bsrGaussianPdfReal_le_normConst_pow_mul_exp_neg_sqLower :
    ∀ {n : ℕ} {σ sqLower : ℝ} (hσ : σ ≠ 0) (μ y : BSROutput n)
    (hLower : sqLower ≤ ∑ i : Fin n, (y i - μ i) ^ 2),
    bsrGaussianPdfReal σ μ y
      ≤ (gaussianNormConst σ) ^ n * Real.exp (-sqLower / (2 * σ ^ 2)) :=
  @Mf.Probability.FiniteGaussian.pdfReal_le_normConst_pow_mul_exp_neg_sqLower

theorem centered_pdf_gap_eq_posConst_mul_centered_density_gap :
    ∀ {n : ℕ} (d y : BSROutput n) (σ ε : ℝ),
    bsrGaussianPdfReal σ d y
      - Real.exp ε * bsrGaussianPdfReal σ (-d) y
    =
    (gaussianNormConst σ) ^ n *
      (bsrGaussianDensity σ d y
        - Real.exp ε * bsrGaussianDensity σ (-d) y) :=
  @Mf.Probability.FiniteGaussian.centered_pdf_gap_eq_posConst_mul_centered_density_gap

theorem centered_pdf_gap_nonneg_iff :
    ∀ {n : ℕ} (d y : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    0 ≤
      bsrGaussianPdfReal σ d y
        - Real.exp ε * bsrGaussianPdfReal σ (-d) y
      ↔
    0 ≤
      bsrGaussianDensity σ d y
        - Real.exp ε * bsrGaussianDensity σ (-d) y :=
  @Mf.Probability.FiniteGaussian.centered_pdf_gap_nonneg_iff

theorem centered_pdf_posRegion_eq_centered_density_posRegion :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    posRegion
      (fun y : BSROutput n =>
        bsrGaussianPdfReal σ d y
          - Real.exp ε * bsrGaussianPdfReal σ (-d) y)
      =
    posRegion
      (fun y : BSROutput n =>
        bsrGaussianDensity σ d y
          - Real.exp ε * bsrGaussianDensity σ (-d) y) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centered_pdf_posRegion_eq_centered_density_posRegion

abbrev bsrGaussianPdf := @Mf.Probability.FiniteGaussian.pdf

theorem bsrGaussianPdfReal_nonneg :
    ∀ {n : ℕ} (σ : ℝ) (μ y : BSROutput n),
    0 ≤ bsrGaussianPdfReal σ μ y :=
  @Mf.Probability.FiniteGaussian.pdfReal_nonneg

theorem bsrGaussianPdfReal_pos :
    ∀ {n : ℕ} (σ : ℝ) (μ y : BSROutput n)
    (hσ : σ ≠ 0),
    0 < bsrGaussianPdfReal σ μ y :=
  @Mf.Probability.FiniteGaussian.pdfReal_pos

theorem measurable_bsrGaussianPdfReal :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n),
    Measurable (fun y : BSROutput n => bsrGaussianPdfReal σ μ y) :=
  @Mf.Probability.FiniteGaussian.measurable_pdfReal

theorem measurable_bsrGaussianPdf :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n),
    Measurable (fun y : BSROutput n => bsrGaussianPdf σ μ y) :=
  @Mf.Probability.FiniteGaussian.measurable_pdf

@[simp] theorem toReal_bsrGaussianPdf :
    ∀ {n : ℕ} (σ : ℝ) (μ y : BSROutput n),
    (bsrGaussianPdf σ μ y).toReal = bsrGaussianPdfReal σ μ y :=
  @Mf.Probability.FiniteGaussian.toReal_pdf

theorem ofReal_bsrGaussianPdfReal :
    ∀ {n : ℕ} (σ : ℝ) (μ y : BSROutput n),
    ENNReal.ofReal (bsrGaussianPdfReal σ μ y) = bsrGaussianPdf σ μ y :=
  @Mf.Probability.FiniteGaussian.ofReal_pdfReal

theorem bsrGaussianPdfReal_piFinSuccAbove_symm :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput (n + 1)),
    let e : BSROutput (n + 1) ≃ᵐ (ℝ × BSROutput n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    ∀ z : ℝ × BSROutput n,
      bsrGaussianPdfReal σ μ (e.symm z)
        = ProbabilityTheory.gaussianPDFReal (μ 0) (bsrGaussianVariance σ) z.1
            * bsrGaussianPdfReal σ (fun i : Fin n => μ i.succ) z.2 :=
  @Mf.Probability.FiniteGaussian.pdfReal_piFinSuccAbove_symm

theorem bsrGaussianPdf_piFinSuccAbove_symm :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput (n + 1)),
    let e : BSROutput (n + 1) ≃ᵐ (ℝ × BSROutput n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    ∀ z : ℝ × BSROutput n,
      bsrGaussianPdf σ μ (e.symm z)
        = ProbabilityTheory.gaussianPDF (μ 0) (bsrGaussianVariance σ) z.1
            * bsrGaussianPdf σ (fun i : Fin n => μ i.succ) z.2 :=
  @Mf.Probability.FiniteGaussian.pdf_piFinSuccAbove_symm

theorem bsrGaussianDensity_centered_expDiff :
    ∀ {n : ℕ} (σ : ℝ) (d y : BSROutput n),
    (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
      - (-(∑ i : Fin n, (y i + d i) ^ 2) / (2 * σ ^ 2))
      = (2 * bsrDot d y) / (σ ^ 2) :=
  @Mf.Probability.FiniteGaussian.density_centered_expDiff

theorem bsrGaussianDensity_centered_ratio_ge_iff :
    ∀ {n : ℕ} (d y : BSROutput n) (σ ε : ℝ),
    bsrGaussianDensity σ d y
      ≥ Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y
      ↔ ε ≤ (2 * bsrDot d y) / (σ ^ 2) :=
  @Mf.Probability.FiniteGaussian.density_centered_ratio_ge_iff

theorem bsrGaussianDensity_centered_sub_nonneg_iff :
    ∀ {n : ℕ} (d y : BSROutput n) (σ ε : ℝ),
    0 ≤ bsrGaussianDensity σ d y
          - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y
      ↔ ε ≤ (2 * bsrDot d y) / (σ ^ 2) :=
  @Mf.Probability.FiniteGaussian.density_centered_sub_nonneg_iff

theorem centered_privacyLoss_posRegion_eq_halfspace :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ),
    posRegion
      (fun y : BSROutput n =>
        bsrGaussianDensity σ d y
          - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y)
      = {y : BSROutput n | ε ≤ (2 * bsrDot d y) / (σ ^ 2)} :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centered_privacyLoss_posRegion_eq_halfspace

theorem centered_privacyLoss_halfspace_eq_dot_ge :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    {y : BSROutput n | ε ≤ (2 * bsrDot d y) / (σ ^ 2)}
      = {y : BSROutput n | (ε * σ ^ 2) / 2 ≤ bsrDot d y} :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centered_privacyLoss_halfspace_eq_dot_ge

theorem centered_privacyLoss_posRegion_eq_dot_ge :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    posRegion
      (fun y : BSROutput n =>
        bsrGaussianDensity σ d y
          - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y)
      = {y : BSROutput n | (ε * σ ^ 2) / 2 ≤ bsrDot d y} :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centered_privacyLoss_posRegion_eq_dot_ge

theorem measurableSet_centered_privacyLoss_posRegion :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    MeasurableSet
      (posRegion
        (fun y : BSROutput n =>
          bsrGaussianDensity σ d y
            - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y)) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measurableSet_centered_privacyLoss_posRegion

abbrev centeredDotThreshold := @Mf.DP.FiniteGaussianPrivacyBasis.centeredDotThreshold

theorem centeredDot_arg_plus :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    ((-(centeredDotThreshold σ ε) - (-r)) / (σ * Real.sqrt r))
      = Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centeredDot_arg_plus

theorem centeredDot_arg_minus :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    ((-(centeredDotThreshold σ ε) - r) / (σ * Real.sqrt r))
      = -Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centeredDot_arg_minus

theorem centered_privacyLoss_posRegion_eq_dot_preimage :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    posRegion
      (fun y : BSROutput n =>
        bsrGaussianDensity σ d y
          - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y)
      = (fun y : BSROutput n => bsrDot d y) ⁻¹' Set.Ici (centeredDotThreshold σ ε) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.centered_privacyLoss_posRegion_eq_dot_preimage

abbrev bsrGaussianDensityENN := @Mf.Probability.FiniteGaussian.densityENN

abbrev bsrGaussianMeasure := @Mf.Probability.FiniteGaussian.measure

theorem bsrGaussianVariance_ne_zero :
    ∀ (σ : ℝ) (hσ : σ ≠ 0),
    bsrGaussianVariance σ ≠ 0 :=
  @Mf.Probability.FiniteGaussian.variance_ne_zero

theorem bsrGaussianMeasure_eq_pi_withDensity :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ μ
      = MeasureTheory.Measure.pi (fun i : Fin n =>
          MeasureTheory.volume.withDensity
            (ProbabilityTheory.gaussianPDF (μ i) (bsrGaussianVariance σ))) :=
  @Mf.Probability.FiniteGaussian.measure_eq_pi_withDensity

instance bsrGaussianMeasure_isProbability :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n),
    MeasureTheory.IsProbabilityMeasure (bsrGaussianMeasure σ μ) :=
  @Mf.Probability.FiniteGaussian.measure_isProbability

theorem bsrGaussianMeasure_map_eval :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (i : Fin n),
    (bsrGaussianMeasure σ μ).map (Function.eval i)
      = ProbabilityTheory.gaussianReal (μ i) (bsrGaussianVariance σ) :=
  @Mf.Probability.FiniteGaussian.measure_map_eval

theorem bsrGaussianMeasure_map_piFinSuccAbove :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput (n + 1)),
    let e : BSROutput (n + 1) ≃ᵐ (ℝ × BSROutput n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    (bsrGaussianMeasure σ μ).map e
      =
        (ProbabilityTheory.gaussianReal (μ 0) (bsrGaussianVariance σ)).prod
          (bsrGaussianMeasure σ (fun i : Fin n => μ i.succ)) :=
  @Mf.Probability.FiniteGaussian.measure_map_piFinSuccAbove

theorem bsrGaussianPdfMeasure_map_piFinSuccAbove :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput (n + 1)),
    let e : BSROutput (n + 1) ≃ᵐ (ℝ × BSROutput n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    ((MeasureTheory.volume.withDensity (bsrGaussianPdf σ μ)).map e)
      =
        (MeasureTheory.volume.withDensity
          (ProbabilityTheory.gaussianPDF (μ 0) (bsrGaussianVariance σ))).prod
          (MeasureTheory.volume.withDensity
            (bsrGaussianPdf σ (fun i : Fin n => μ i.succ))) :=
  @Mf.Probability.FiniteGaussian.pdfMeasure_map_piFinSuccAbove

theorem bsrGaussianMeasure_eq_withDensity_pdf :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ μ = MeasureTheory.volume.withDensity (bsrGaussianPdf σ μ) :=
  @Mf.Probability.FiniteGaussian.measure_eq_withDensity_pdf

theorem integrable_bsrGaussianPdfReal :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (hσ : σ ≠ 0),
    MeasureTheory.Integrable (fun y : BSROutput n => bsrGaussianPdfReal σ μ y)
      MeasureTheory.volume :=
  @Mf.Probability.FiniteGaussian.integrable_pdfReal

theorem bsrGaussianMeasure_apply_eval_preimage :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (i : Fin n) (s : Set ℝ)
    (hs : MeasurableSet s),
    bsrGaussianMeasure σ μ (Function.eval i ⁻¹' s)
      = ProbabilityTheory.gaussianReal (μ i) (bsrGaussianVariance σ) s :=
  @Mf.Probability.FiniteGaussian.measure_apply_eval_preimage

theorem bsrGaussianMeasure_apply_eval_preimage_Iic :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (i : Fin n) (t : ℝ),
    bsrGaussianMeasure σ μ (Function.eval i ⁻¹' Set.Iic t)
      = ProbabilityTheory.gaussianReal (μ i) (bsrGaussianVariance σ) (Set.Iic t) :=
  @Mf.Probability.FiniteGaussian.measure_apply_eval_preimage_Iic

theorem bsrGaussianMeasure_apply_eval_preimage_Iic_eq_stdNormal :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n) (i : Fin n) (t : ℝ)
    (hσ : 0 < σ),
    bsrGaussianMeasure σ μ (Function.eval i ⁻¹' Set.Iic t)
      = stdNormalMeasure (Set.Iic ((t - μ i) / σ)) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measure_apply_eval_preimage_Iic_eq_stdNormal

theorem bsrGaussianMeasure_apply_centered_privacyLoss_posRegion :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ d
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      =
        ((bsrGaussianMeasure σ d).map (fun y : BSROutput n => bsrDot d y))
          (Set.Ici (centeredDotThreshold σ ε)) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measure_apply_centered_privacyLoss_posRegion

theorem measure_map_apply_Ici_eq_map_neg_apply_Iic :
    ∀ {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (f : α → ℝ)
    (hf : Measurable f)
    (t : ℝ),
    (μ.map f) (Set.Ici t)
      = (μ.map (fun x => -f x)) (Set.Iic (-t)) :=
  @Mf.Probability.FiniteGaussian.measure_map_apply_Ici_eq_map_neg_apply_Iic

theorem bsrGaussianMeasure_apply_centered_privacyLoss_posRegion_Iic :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ d
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      =
        ((bsrGaussianMeasure σ d).map (fun y : BSROutput n => -bsrDot d y))
          (Set.Iic (-(centeredDotThreshold σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measure_apply_centered_privacyLoss_posRegion_Iic

theorem bsrGaussianMeasure_apply_centered_privacyLoss_posRegion_Iic_of_mean :
    ∀ {n : ℕ} (μ d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ μ
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      =
        ((bsrGaussianMeasure σ μ).map (fun y : BSROutput n => -bsrDot d y))
          (Set.Iic (-(centeredDotThreshold σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measure_apply_centered_privacyLoss_posRegion_Iic_of_mean

theorem bsrGaussianMeasure_map_add_const :
    ∀ {n : ℕ} (σ : ℝ) (μ c : BSROutput n),
    (bsrGaussianMeasure σ μ).map (fun x : BSROutput n => fun i => x i + c i)
      = bsrGaussianMeasure σ (fun i => μ i + c i) :=
  @Mf.Probability.FiniteGaussian.measure_map_add_const

theorem bsrGaussianMeasure_map_sub_const :
    ∀ {n : ℕ} (σ : ℝ) (μ c : BSROutput n),
    (bsrGaussianMeasure σ μ).map (fun x : BSROutput n => fun i => x i - c i)
      = bsrGaussianMeasure σ (fun i => μ i - c i) :=
  @Mf.Probability.FiniteGaussian.measure_map_sub_const

theorem bsrGaussianMeasure_map_neg :
    ∀ {n : ℕ} (σ : ℝ) (μ : BSROutput n),
    (bsrGaussianMeasure σ μ).map (fun x : BSROutput n => fun i => -x i)
      = bsrGaussianMeasure σ (fun i => -μ i) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg

theorem bsrGaussianMeasure_map_bsrDot_add_const :
    ∀ {n : ℕ} (σ : ℝ) (μ c d : BSROutput n),
    (bsrGaussianMeasure σ (fun i => μ i + c i)).map (fun y : BSROutput n => bsrDot d y)
      =
        ((bsrGaussianMeasure σ μ).map (fun y : BSROutput n => bsrDot d y)).map
          (fun t : ℝ => t + bsrDot d c) :=
  @Mf.Probability.FiniteGaussian.measure_map_dot_add_const

theorem bsrGaussianMeasure_map_bsrDot_eq_centered_map_shift :
    ∀ {n : ℕ} (σ : ℝ) (μ d : BSROutput n),
    (bsrGaussianMeasure σ μ).map (fun y : BSROutput n => bsrDot d y)
      =
        ((bsrGaussianMeasure σ (fun _ => (0 : ℝ))).map (fun y : BSROutput n => bsrDot d y)).map
          (fun t : ℝ => t + bsrDot d μ) :=
  @Mf.Probability.FiniteGaussian.measure_map_dot_eq_centered_map_shift

theorem bsrGaussianMeasure_map_neg_bsrDot_eq_centered_map_shift :
    ∀ {n : ℕ} (σ : ℝ) (μ d : BSROutput n),
    (bsrGaussianMeasure σ μ).map (fun y : BSROutput n => -bsrDot d y)
      =
        ((bsrGaussianMeasure σ (fun _ => (0 : ℝ))).map (fun y : BSROutput n => -bsrDot d y)).map
          (fun t : ℝ => t - bsrDot d μ) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg_dot_eq_centered_map_shift

theorem bsrGaussianMeasure_map_neg_bsrDot_negMean_eq_centered_map_shift :
    ∀ {n : ℕ} (σ : ℝ) (d : BSROutput n),
    (bsrGaussianMeasure σ (fun i => -d i)).map (fun y : BSROutput n => -bsrDot d y)
      =
        ((bsrGaussianMeasure σ (fun _ => (0 : ℝ))).map (fun y : BSROutput n => -bsrDot d y)).map
          (fun t : ℝ => t + bsrDot d d) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg_dot_negMean_eq_centered_map_shift

theorem bsrGaussianMeasure_map_neg_bsrDot_centered_eq_gaussianReal_sumSq :
    ∀ {n : ℕ} (σ : ℝ) (d : BSROutput n),
    ((bsrGaussianMeasure σ (fun _ : Fin n => (0 : ℝ))).map (fun y : BSROutput n => -bsrDot d y))
      = ProbabilityTheory.gaussianReal 0
          (⟨σ ^ 2 * (∑ i : Fin n, (d i) ^ 2),
            mul_nonneg (sq_nonneg σ) (Finset.sum_nonneg (fun i _ => sq_nonneg (d i)))⟩) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg_dot_centered_eq_gaussianReal_sumSq

theorem bsrGaussianMeasure_map_neg_bsrDot_centered_eq_gaussianReal :
    ∀ {n : ℕ} (σ : ℝ) (d : BSROutput n),
    ((bsrGaussianMeasure σ (fun _ : Fin n => (0 : ℝ))).map (fun y : BSROutput n => -bsrDot d y))
      = ProbabilityTheory.gaussianReal 0
          (⟨σ ^ 2 * bsrDot d d,
            mul_nonneg (sq_nonneg σ) (bsrDot_self_nonneg d)⟩) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg_dot_centered_eq_gaussianReal

theorem bsrGaussianMeasure_map_neg_bsrDot_eq_gaussianReal :
    ∀ {n : ℕ} (σ : ℝ) (μ d : BSROutput n),
    (bsrGaussianMeasure σ μ).map (fun y : BSROutput n => -bsrDot d y)
      = ProbabilityTheory.gaussianReal (-bsrDot d μ)
          (⟨σ ^ 2 * bsrDot d d,
            mul_nonneg (sq_nonneg σ) (bsrDot_self_nonneg d)⟩) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg_dot_eq_gaussianReal

theorem bsrGaussianMeasure_map_neg_bsrDot_negMean_eq_gaussianReal :
    ∀ {n : ℕ} (σ : ℝ) (d : BSROutput n),
    (bsrGaussianMeasure σ (fun i => -d i)).map (fun y : BSROutput n => -bsrDot d y)
      = ProbabilityTheory.gaussianReal (bsrDot d d)
          (⟨σ ^ 2 * bsrDot d d,
            mul_nonneg (sq_nonneg σ) (bsrDot_self_nonneg d)⟩) :=
  @Mf.Probability.FiniteGaussian.measure_map_neg_dot_negMean_eq_gaussianReal

theorem bsrGaussianMeasure_apply_centered_privacyLoss_posRegion_eq_gaussianReal_event :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ d
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      =
        (ProbabilityTheory.gaussianReal (-(bsrDot d d))
          (⟨σ ^ 2 * bsrDot d d,
            mul_nonneg (sq_nonneg σ) (bsrDot_self_nonneg d)⟩))
          (Set.Iic (-(centeredDotThreshold σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measure_apply_centered_privacyLoss_posRegion_eq_gaussianReal_event

theorem bsrGaussianMeasure_apply_centered_privacyLoss_posRegion_negMean_eq_gaussianReal_event :
    ∀ {n : ℕ} (d : BSROutput n) (σ ε : ℝ) (hσ : σ ≠ 0),
    bsrGaussianMeasure σ (fun i => -d i)
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      =
        (ProbabilityTheory.gaussianReal (bsrDot d d)
          (⟨σ ^ 2 * bsrDot d d,
            mul_nonneg (sq_nonneg σ) (bsrDot_self_nonneg d)⟩))
          (Set.Iic (-(centeredDotThreshold σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacyBasis.measure_apply_centered_privacyLoss_posRegion_negMean_eq_gaussianReal_event

theorem gaussianPair_eventApproxDP_transport_add_const :
    ∀ {n : ℕ}
    (σ ε δ : ℝ)
    (μ μ' c : BSROutput n)
    (hpair :
      ∀ s, MeasurableSet s →
        bsrGaussianMeasure σ μ s
          ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ μ' s + ENNReal.ofReal δ),
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ (fun i => μ i + c i) s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => μ' i + c i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacyBasis.gaussianPair_eventApproxDP_transport_add_const

theorem analyticGaussianExpr_iff_bsrGaussianMeasure_eval_event_form :
    ∀ {n : ℕ} (i : Fin n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ),
    analyticGaussianExpr Δ σ ε ≤ δ
      ↔ (bsrGaussianMeasure σ (fun _ : Fin n => Δ / 2)).real
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
          - Real.exp ε
              * (bsrGaussianMeasure σ (fun _ : Fin n => -Δ / 2)).real
                  (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
        ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacyBasis.analyticGaussianExpr_iff_measure_eval_event_form

abbrev bsrSqDist := @Mf.Probability.FiniteGaussian.sqDist

theorem bsrSqDist_symm :
    ∀ {n : ℕ} (u v : BSROutput n),
    bsrSqDist u v = bsrSqDist v u :=
  @Mf.Probability.FiniteGaussian.sqDist_symm

theorem bsrSqDist_scale :
    ∀ {n : ℕ} (a : ℝ) (u v : BSROutput n),
    bsrSqDist (fun i => a * u i) (fun i => a * v i) = a ^ 2 * bsrSqDist u v :=
  @Mf.Probability.FiniteGaussian.sqDist_scale

abbrev bsrMidpoint := @Mf.Probability.FiniteGaussian.midpoint

abbrev bsrHalfDiff := @Mf.Probability.FiniteGaussian.halfDiff

theorem bsrSqDist_nonneg :
    ∀ {n : ℕ} (u v : BSROutput n),
    0 ≤ bsrSqDist u v :=
  @Mf.Probability.FiniteGaussian.sqDist_nonneg

theorem bsrSqDist_eq_zero_iff :
    ∀ {n : ℕ} (u v : BSROutput n),
    bsrSqDist u v = 0 ↔ u = v :=
  @Mf.Probability.FiniteGaussian.sqDist_eq_zero_iff

theorem bsrDot_self_eq_bsrSqDist_zero :
    ∀ {n : ℕ} (u : BSROutput n),
    bsrDot u u = bsrSqDist u (fun _ => (0 : ℝ)) :=
  @Mf.Probability.FiniteGaussian.dot_self_eq_sqDist_zero

abbrev bsrRadius := @Mf.Probability.FiniteGaussian.radius

theorem bsrRadius_nonneg :
    ∀ {n : ℕ} (u v : BSROutput n),
    0 ≤ bsrRadius u v :=
  @Mf.Probability.FiniteGaussian.radius_nonneg

theorem bsrRadius_sq :
    ∀ {n : ℕ} (u v : BSROutput n),
    (bsrRadius u v) ^ 2 = bsrSqDist u v :=
  @Mf.Probability.FiniteGaussian.radius_sq

theorem bsrSqDist_le_iff_bsrRadius_le :
    ∀ {n : ℕ} (u v : BSROutput n) (r : ℝ) (hr : 0 ≤ r),
    bsrSqDist u v ≤ r ^ 2 ↔ bsrRadius u v ≤ r :=
  @Mf.Probability.FiniteGaussian.sqDist_le_iff_radius_le

theorem bsrMidpoint_add_bsrHalfDiff :
    ∀ {n : ℕ} (u v : BSROutput n),
    (fun i => bsrMidpoint u v i + bsrHalfDiff u v i) = u :=
  @Mf.Probability.FiniteGaussian.midpoint_add_halfDiff

theorem bsrMidpoint_sub_bsrHalfDiff :
    ∀ {n : ℕ} (u v : BSROutput n),
    (fun i => bsrMidpoint u v i - bsrHalfDiff u v i) = v :=
  @Mf.Probability.FiniteGaussian.midpoint_sub_halfDiff

theorem bsrSqDist_eq_four_mul_halfDiff :
    ∀ {n : ℕ} (u v : BSROutput n),
    bsrSqDist u v = 4 * bsrSqDist (bsrHalfDiff u v) (fun _ => (0 : ℝ)) :=
  @Mf.Probability.FiniteGaussian.sqDist_eq_four_mul_halfDiff

theorem gaussianPair_eventApproxDP_of_centered :
    ∀ {n : ℕ}
    (σ ε δ : ℝ)
    (d : BSROutput n)
    (hcenter :
      ∀ s, MeasurableSet s →
        bsrGaussianMeasure σ d s
          ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
              + ENNReal.ofReal δ),
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ (fun i => bsrMidpoint d (fun j => -d j) i + d i) s
        ≤ ENNReal.ofReal (Real.exp ε)
            * bsrGaussianMeasure σ (fun i => bsrMidpoint d (fun j => -d j) i - d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacyBasis.gaussianPair_eventApproxDP_of_centered

def bsrOneStepDensity
    {X : Type} {n : ℕ}
    (mean : X → BSROutput n) (σ : ℝ) :
    X → BSROutput n → ℝ :=
  fun x y => bsrGaussianDensity σ (mean x) y

theorem bsrOneStepDensity_nonneg
    {X : Type} {n : ℕ}
    (mean : X → BSROutput n) (σ : ℝ) :
    ∀ x y, 0 ≤ bsrOneStepDensity mean σ x y := by
  intro x y
  unfold bsrOneStepDensity
  exact bsrGaussianDensity_nonneg σ (mean x) y

def bsrOneStepMeasure
    {X : Type} {n : ℕ}
    (mean : X → BSROutput n) (σ : ℝ) :
    X → MeasureTheory.Measure (BSROutput n) :=
  fun x => bsrGaussianMeasure σ (mean x)

def BSRMeanL2SensitivityGoal
    {X : Type} {n : ℕ}
    (adj : X → X → Prop)
    (mean : X → BSROutput n)
    (Δ : ℝ) : Prop :=
  ∀ x x', adj x x' → bsrSqDist (mean x) (mean x') ≤ Δ ^ 2

end
end Mf.DP
