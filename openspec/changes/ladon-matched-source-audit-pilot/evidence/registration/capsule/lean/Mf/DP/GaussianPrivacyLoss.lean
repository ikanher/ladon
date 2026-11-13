import Mathlib

namespace Mf
namespace DP

noncomputable section

/-- Standard normal measure on `ℝ` (mean `0`, variance `1`). -/
def stdNormalMeasure : MeasureTheory.Measure ℝ :=
  ProbabilityTheory.gaussianReal 0 (1 : NNReal)

instance : MeasureTheory.IsProbabilityMeasure stdNormalMeasure := by
  unfold stdNormalMeasure
  infer_instance

/-- Standard normal CDF as a real-valued function. -/
def stdNormalCDFReal (t : ℝ) : ℝ :=
  ProbabilityTheory.cdf stdNormalMeasure t

theorem stdNormalCDFReal_nonneg (t : ℝ) : 0 ≤ stdNormalCDFReal t := by
  simpa [stdNormalCDFReal, stdNormalMeasure] using
    (ProbabilityTheory.cdf_nonneg (μ := stdNormalMeasure) t)

theorem stdNormalCDFReal_le_one (t : ℝ) : stdNormalCDFReal t ≤ 1 := by
  simpa [stdNormalCDFReal, stdNormalMeasure] using
    (ProbabilityTheory.cdf_le_one (μ := stdNormalMeasure) t)

theorem stdNormalCDFReal_mono : Monotone stdNormalCDFReal := by
  change Monotone (fun t => ProbabilityTheory.cdf stdNormalMeasure t)
  exact ProbabilityTheory.monotone_cdf (μ := stdNormalMeasure)

theorem stdNormalCDFReal_eq_real_measure_Iic
    (t : ℝ) :
    stdNormalCDFReal t = stdNormalMeasure.real (Set.Iic t) := by
  simpa [stdNormalCDFReal, stdNormalMeasure] using
    (ProbabilityTheory.cdf_eq_real (μ := stdNormalMeasure) t)

theorem ofReal_stdNormalCDFReal_eq_measure_Iic
    (t : ℝ) :
    ENNReal.ofReal (stdNormalCDFReal t) = stdNormalMeasure (Set.Iic t) := by
  simpa [stdNormalCDFReal, stdNormalMeasure] using
    (ProbabilityTheory.ofReal_cdf (μ := stdNormalMeasure) t)

theorem stdNormalCDFReal_lt_one (t : ℝ) : stdNormalCDFReal t < 1 := by
  have htail : 0 < stdNormalMeasure (Set.Ioi t) := by
    rw [stdNormalMeasure, ProbabilityTheory.gaussianReal_of_var_ne_zero]
    · have hdens : Measurable fun x : ℝ =>
          ProbabilityTheory.gaussianPDF 0 (1 : NNReal) x := by
        fun_prop
      rw [MeasureTheory.withDensity_apply _ measurableSet_Ioi]
      rw [MeasureTheory.setLIntegral_pos_iff hdens]
      have hsupp : Function.support
          (fun x : ℝ => ProbabilityTheory.gaussianPDF 0 (1 : NNReal) x) =
          Set.univ := by
        ext x
        simp only [Function.mem_support, Set.mem_univ, iff_true]
        exact ne_of_gt (ProbabilityTheory.gaussianPDF_pos 0 one_ne_zero x)
      rw [hsupp, Set.univ_inter]
      simp
    · exact one_ne_zero
  have hltENN : stdNormalMeasure (Set.Iic t) < 1 := by
    have hcompl := MeasureTheory.measure_compl measurableSet_Iic
      (MeasureTheory.measure_ne_top stdNormalMeasure (Set.Iic t))
    have : 0 < stdNormalMeasure Set.univ - stdNormalMeasure (Set.Iic t) := by
      rw [← hcompl]
      simpa only [Set.compl_Iic] using htail
    rw [tsub_pos_iff_lt] at this
    simpa using this
  rw [stdNormalCDFReal_eq_real_measure_Iic]
  exact (ENNReal.toReal_lt_toReal
    (MeasureTheory.measure_ne_top stdNormalMeasure (Set.Iic t))
    ENNReal.one_ne_top).2 hltENN

/--
Analytic Gaussian expression from Balle-Wang:
`Φ(Δ/(2σ) - εσ/Δ) - exp(ε) Φ(-Δ/(2σ) - εσ/Δ)`.
-/
def privacyLossArgPlus (Δ σ ε : ℝ) : ℝ :=
  Δ / (2 * σ) - (ε * σ) / Δ

def privacyLossArgMinus (Δ σ ε : ℝ) : ℝ :=
  -Δ / (2 * σ) - (ε * σ) / Δ

def analyticGaussianExpr (Δ σ ε : ℝ) : ℝ :=
  stdNormalCDFReal (privacyLossArgPlus Δ σ ε)
    - Real.exp ε * stdNormalCDFReal (privacyLossArgMinus Δ σ ε)

def privacyEventThresholdPlus (Δ σ ε : ℝ) : ℝ :=
  Δ / 2 + σ * privacyLossArgPlus Δ σ ε

def privacyEventThresholdMinus (Δ σ ε : ℝ) : ℝ :=
  -Δ / 2 + σ * privacyLossArgMinus Δ σ ε

theorem privacyEventThresholdPlus_eq
    (Δ σ ε : ℝ)
    (hσ : 0 < σ) :
    privacyEventThresholdPlus Δ σ ε = Δ - (ε * σ ^ 2) / Δ := by
  unfold privacyEventThresholdPlus privacyLossArgPlus
  field_simp [hσ.ne']
  ring_nf

theorem privacyEventThresholdMinus_eq
    (Δ σ ε : ℝ)
    (hσ : 0 < σ) :
    privacyEventThresholdMinus Δ σ ε = -Δ - (ε * σ ^ 2) / Δ := by
  unfold privacyEventThresholdMinus privacyLossArgMinus
  field_simp [hσ.ne']
  ring_nf

/-- Monotonicity in `δ` for the analytic Gaussian inequality target. -/
theorem analyticGaussianExpr_le_of_le
    {Δ σ ε δ₀ δ : ℝ}
    (h₀ : analyticGaussianExpr Δ σ ε ≤ δ₀)
    (hδ : δ₀ ≤ δ) :
    analyticGaussianExpr Δ σ ε ≤ δ := by
  exact le_trans h₀ hδ

theorem analyticGaussianExpr_eq
    (Δ σ ε : ℝ) :
    analyticGaussianExpr Δ σ ε
      = stdNormalCDFReal (privacyLossArgPlus Δ σ ε)
          - Real.exp ε * stdNormalCDFReal (privacyLossArgMinus Δ σ ε) := by
  rfl

@[simp] theorem privacyLossArgPlus_def
    (Δ σ ε : ℝ) :
    privacyLossArgPlus Δ σ ε = Δ / (2 * σ) - (ε * σ) / Δ := rfl

@[simp] theorem privacyLossArgMinus_def
    (Δ σ ε : ℝ) :
    privacyLossArgMinus Δ σ ε = -Δ / (2 * σ) - (ε * σ) / Δ := rfl

theorem analyticGaussianExpr_le_one
    (Δ σ ε : ℝ) :
    analyticGaussianExpr Δ σ ε ≤ 1 := by
  unfold analyticGaussianExpr
  have hsub :
      stdNormalCDFReal (privacyLossArgPlus Δ σ ε)
        - Real.exp ε * stdNormalCDFReal (privacyLossArgMinus Δ σ ε)
      ≤ stdNormalCDFReal (privacyLossArgPlus Δ σ ε) := by
    have hnonneg :
        0 ≤ Real.exp ε * stdNormalCDFReal (privacyLossArgMinus Δ σ ε) := by
      exact mul_nonneg
        (le_of_lt (Real.exp_pos ε))
        (stdNormalCDFReal_nonneg (privacyLossArgMinus Δ σ ε))
    exact sub_le_self _ hnonneg
  exact le_trans hsub (stdNormalCDFReal_le_one (privacyLossArgPlus Δ σ ε))

theorem neg_exp_le_analyticGaussianExpr
    (Δ σ ε : ℝ) :
    -Real.exp ε ≤ analyticGaussianExpr Δ σ ε := by
  unfold analyticGaussianExpr
  have hfirst : 0 ≤ stdNormalCDFReal (privacyLossArgPlus Δ σ ε) :=
    stdNormalCDFReal_nonneg (privacyLossArgPlus Δ σ ε)
  have hsecond :
      Real.exp ε * stdNormalCDFReal (privacyLossArgMinus Δ σ ε) ≤ Real.exp ε := by
    have hle : stdNormalCDFReal (privacyLossArgMinus Δ σ ε) ≤ 1 :=
      stdNormalCDFReal_le_one (privacyLossArgMinus Δ σ ε)
    simpa using mul_le_mul_of_nonneg_left hle (le_of_lt (Real.exp_pos ε))
  linarith

theorem analyticGaussianExpr_eq_event_form
    (Δ σ ε : ℝ) :
    analyticGaussianExpr Δ σ ε
      = stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
          - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε)) := by
  simp [analyticGaussianExpr, stdNormalCDFReal_eq_real_measure_Iic]

theorem gaussianReal_unitVar_apply_Iic_eq_stdNormalMeasure_shift
    (μ t : ℝ) :
    ProbabilityTheory.gaussianReal μ (1 : NNReal) (Set.Iic t)
      = stdNormalMeasure (Set.Iic (t - μ)) := by
  have hmap :
      stdNormalMeasure.map (fun x : ℝ => x + μ)
        = ProbabilityTheory.gaussianReal μ (1 : NNReal) := by
    unfold stdNormalMeasure
    simpa [zero_add] using
      (ProbabilityTheory.gaussianReal_map_add_const (μ := 0) (v := (1 : NNReal)) μ)
  rw [← hmap, MeasureTheory.Measure.map_apply (by fun_prop) measurableSet_Iic]
  congr 1
  ext x
  simp

theorem gaussianReal_zero_apply_Iic_eq_stdNormalMeasure_div
    (σ t : ℝ)
    (hσ : 0 < σ) :
    ProbabilityTheory.gaussianReal 0 (⟨σ ^ 2, sq_nonneg σ⟩) (Set.Iic t)
      = stdNormalMeasure (Set.Iic (t / σ)) := by
  have hmap :
      stdNormalMeasure.map (fun x : ℝ => σ * x)
        = ProbabilityTheory.gaussianReal 0 (⟨σ ^ 2, sq_nonneg σ⟩) := by
    unfold stdNormalMeasure
    let varNN : NNReal := NNReal.mk (σ ^ 2) (sq_nonneg σ)
    let oneNN : NNReal := 1
    have hvar :
        varNN * oneNN = ⟨σ ^ 2, sq_nonneg σ⟩ := by
      ext
      change σ ^ 2 * (1 : ℝ) = σ ^ 2
      ring
    have hmap0 :=
      (ProbabilityTheory.gaussianReal_map_const_mul
        (μ := 0) (v := ⟨1, by positivity⟩) σ)
    change
      MeasureTheory.Measure.map (fun x : ℝ => σ * x)
          (ProbabilityTheory.gaussianReal 0 oneNN)
        = ProbabilityTheory.gaussianReal (σ * 0) (varNN * oneNN) at hmap0
    rw [hvar] at hmap0
    simpa [zero_mul, oneNN] using hmap0
  rw [← hmap, MeasureTheory.Measure.map_apply (by fun_prop) measurableSet_Iic]
  congr 1
  ext x
  constructor
  · intro hx
    have hx' : x * σ ≤ t := by simpa [mul_comm] using hx
    exact (le_div_iff₀ hσ).2 hx'
  · intro hx
    have hx' : x * σ ≤ t := (le_div_iff₀ hσ).1 hx
    simpa [mul_comm] using hx'

theorem gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
    (μ σ t : ℝ)
    (hσ : 0 < σ) :
    ProbabilityTheory.gaussianReal μ (⟨σ ^ 2, sq_nonneg σ⟩) (Set.Iic t)
      = stdNormalMeasure (Set.Iic ((t - μ) / σ)) := by
  have hshift :
      (ProbabilityTheory.gaussianReal 0 (⟨σ ^ 2, sq_nonneg σ⟩)).map (fun x : ℝ => x + μ)
        = ProbabilityTheory.gaussianReal μ (⟨σ ^ 2, sq_nonneg σ⟩) := by
    simpa [zero_add] using
      (ProbabilityTheory.gaussianReal_map_add_const (μ := 0) (v := ⟨σ ^ 2, sq_nonneg σ⟩) μ)
  rw [← hshift, MeasureTheory.Measure.map_apply (by fun_prop) measurableSet_Iic]
  have hpre : (fun x : ℝ => x + μ) ⁻¹' Set.Iic t = Set.Iic (t - μ) := by
    ext x
    simp
  rw [hpre, gaussianReal_zero_apply_Iic_eq_stdNormalMeasure_div σ (t - μ) hσ]

theorem stdNormalMeasure_real_eq_gaussianReal_real_event_plus
    (Δ σ ε : ℝ)
    (hσ : 0 < σ) :
    stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      = (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
          (Set.Iic (privacyEventThresholdPlus Δ σ ε)) := by
  have hplus :=
    gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
      (μ := Δ / 2) (σ := σ) (t := privacyEventThresholdPlus Δ σ ε) hσ
  have hplusReal :
      (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
          (Set.Iic (privacyEventThresholdPlus Δ σ ε))
        = stdNormalMeasure.real
            (Set.Iic (((privacyEventThresholdPlus Δ σ ε) - Δ / 2) / σ)) := by
    simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hplus
  have harg :
      ((privacyEventThresholdPlus Δ σ ε) - Δ / 2) / σ
        = privacyLossArgPlus Δ σ ε := by
    unfold privacyEventThresholdPlus
    field_simp [hσ.ne']
    ring
  rw [hplusReal, harg]

theorem stdNormalMeasure_real_eq_gaussianReal_real_event_minus
    (Δ σ ε : ℝ)
    (hσ : 0 < σ) :
    stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      = (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
          (Set.Iic (privacyEventThresholdMinus Δ σ ε)) := by
  have hminus :=
    gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
      (μ := -Δ / 2) (σ := σ) (t := privacyEventThresholdMinus Δ σ ε) hσ
  have hminusReal :
      (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
          (Set.Iic (privacyEventThresholdMinus Δ σ ε))
        = stdNormalMeasure.real
            (Set.Iic (((privacyEventThresholdMinus Δ σ ε) - (-Δ / 2)) / σ)) := by
    simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hminus
  have harg :
      ((privacyEventThresholdMinus Δ σ ε) - (-Δ / 2)) / σ
        = privacyLossArgMinus Δ σ ε := by
    unfold privacyEventThresholdMinus
    field_simp [hσ.ne']
    ring
  rw [hminusReal, harg]

theorem analyticGaussianExpr_eq_gaussianReal_event_form
    (Δ σ ε : ℝ)
    (hσ : 0 < σ) :
    analyticGaussianExpr Δ σ ε
      = (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
          (Set.Iic (privacyEventThresholdPlus Δ σ ε))
        - Real.exp ε
            * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                (Set.Iic (privacyEventThresholdMinus Δ σ ε)) := by
  rw [analyticGaussianExpr_eq_event_form]
  rw [stdNormalMeasure_real_eq_gaussianReal_real_event_plus Δ σ ε hσ]
  rw [stdNormalMeasure_real_eq_gaussianReal_real_event_minus Δ σ ε hσ]

theorem analyticGaussianExpr_eq_gaussianReal_event_form_explicit
    (Δ σ ε : ℝ)
    (hσ : 0 < σ) :
    analyticGaussianExpr Δ σ ε
      = (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
          (Set.Iic (Δ - (ε * σ ^ 2) / Δ))
        - Real.exp ε
            * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                (Set.Iic (-Δ - (ε * σ ^ 2) / Δ)) := by
  rw [analyticGaussianExpr_eq_gaussianReal_event_form Δ σ ε hσ]
  rw [privacyEventThresholdPlus_eq Δ σ ε hσ, privacyEventThresholdMinus_eq Δ σ ε hσ]

end
end DP
end Mf
