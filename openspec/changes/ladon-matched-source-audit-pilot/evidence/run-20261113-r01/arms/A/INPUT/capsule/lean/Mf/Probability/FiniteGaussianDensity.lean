import Mathlib
import Mf.Probability.FiniteProductGaussian

/-!
# Finite isotropic Gaussian geometry, densities and laws

The vector space is `Fin n → ℝ`. The law uses the existing finite product
Gaussian with a constant coordinate scale, including zero and negative scales.
Normalized PDFs are distinguished from the unnormalized exponential density.
Translation, scalar projection and midpoint identities belong to this
probability owner; privacy comparisons and application adapters are downstream.
-/

namespace Mf.Probability.FiniteGaussian
open scoped BigOperators
noncomputable section

abbrev Vector (n : ℕ) := Fin n → ℝ

def dot {n : ℕ} (u v : Vector n) : ℝ :=
  ∑ i : Fin n, u i * v i

lemma measurable_dot_left {n : ℕ} (u : Vector n) :
    Measurable (fun v : Vector n => dot u v) := by
  have hcont : Continuous (fun v : Vector n => dot u v) := by
    unfold dot
    continuity
  exact hcont.measurable

lemma dot_add_right {n : ℕ} (u v w : Vector n) :
    dot u (fun i => v i + w i) = dot u v + dot u w := by
  unfold dot
  simp [mul_add, Finset.sum_add_distrib]

lemma dot_sub_right {n : ℕ} (u v w : Vector n) :
    dot u (fun i => v i - w i) = dot u v - dot u w := by
  unfold dot
  simp [sub_eq_add_neg, Finset.sum_add_distrib, mul_add]

lemma dot_neg_right {n : ℕ} (u v : Vector n) :
    dot u (fun i => -v i) = -dot u v := by
  unfold dot
  simp

lemma dot_neg_left {n : ℕ} (u v : Vector n) :
    dot (fun i => -u i) v = -dot u v := by
  unfold dot
  simp

lemma dot_self_eq_sum_sq {n : ℕ} (u : Vector n) :
    dot u u = ∑ i : Fin n, (u i) ^ 2 := by
  unfold dot
  refine Finset.sum_congr rfl ?_
  intro i hi
  ring

lemma dot_self_nonneg {n : ℕ} (u : Vector n) :
    0 ≤ dot u u := by
  rw [dot_self_eq_sum_sq]
  exact Finset.sum_nonneg (fun i _ => sq_nonneg (u i))

def density
    {n : ℕ} (σ : ℝ) (μ y : Vector n) : ℝ :=
  Real.exp (-(∑ i : Fin n, (y i - μ i) ^ 2) / (2 * σ ^ 2))

def normalization (σ : ℝ) : ℝ :=
  (Real.sqrt (2 * Real.pi * σ ^ 2))⁻¹

def variance (σ : ℝ) : NNReal :=
  ⟨σ ^ 2, sq_nonneg σ⟩

theorem variance_eq_mk (σ : ℝ) :
    variance σ = ⟨σ ^ 2, sq_nonneg σ⟩ := rfl

theorem density_nonneg
    {n : ℕ} (σ : ℝ) (μ y : Vector n) :
    0 ≤ density σ μ y := by
  unfold density
  exact le_of_lt (Real.exp_pos _)

theorem density_le_one
    {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0) (μ y : Vector n) :
    density σ μ y ≤ 1 := by
  unfold density
  have hsum_nonneg : 0 ≤ ∑ i : Fin n, (y i - μ i) ^ 2 :=
    Finset.sum_nonneg fun i _ => sq_nonneg (y i - μ i)
  have hden_pos : 0 < 2 * σ ^ 2 := by
    positivity
  have harg_nonpos :
      -((∑ i : Fin n, (y i - μ i) ^ 2)) / (2 * σ ^ 2) ≤ 0 :=
    div_nonpos_of_nonpos_of_nonneg (neg_nonpos.mpr hsum_nonneg)
      hden_pos.le
  exact Real.exp_le_one_iff.mpr harg_nonpos

theorem density_le_exp_neg_sqLower
    {n : ℕ} {σ sqLower : ℝ} (hσ : σ ≠ 0) (μ y : Vector n)
    (hLower : sqLower ≤ ∑ i : Fin n, (y i - μ i) ^ 2) :
    density σ μ y
      ≤ Real.exp (-sqLower / (2 * σ ^ 2)) := by
  unfold density
  have hden_pos : 0 < 2 * σ ^ 2 := by
    positivity
  have hneg :
      -(∑ i : Fin n, (y i - μ i) ^ 2) ≤ -sqLower :=
    neg_le_neg hLower
  have harg :
      -(∑ i : Fin n, (y i - μ i) ^ 2) / (2 * σ ^ 2)
        ≤ -sqLower / (2 * σ ^ 2) :=
    div_le_div_of_nonneg_right hneg hden_pos.le
  exact Real.exp_le_exp.mpr harg

lemma normalization_pos {σ : ℝ} (hσ : σ ≠ 0) :
    0 < normalization σ := by
  unfold normalization
  have hσ2 : 0 < σ ^ 2 := sq_pos_of_ne_zero hσ
  have hmul : 0 < 2 * Real.pi * σ ^ 2 := by
    have hpi : 0 < Real.pi := Real.pi_pos
    positivity
  have hsqrt : 0 < Real.sqrt (2 * Real.pi * σ ^ 2) := Real.sqrt_pos.2 hmul
  exact inv_pos.2 hsqrt

lemma normalization_pow_pos {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0) :
    0 < (normalization σ) ^ n := by
  exact pow_pos (normalization_pos hσ) _

lemma gaussianPDFReal_eq_normConst_mul_exp
    (σ μ x : ℝ) :
    ProbabilityTheory.gaussianPDFReal μ (variance σ) x
      =
        normalization σ
          * Real.exp (-(x - μ) ^ 2 / (2 * σ ^ 2)) := by
  rw [ProbabilityTheory.gaussianPDFReal_def]
  rfl

def pdfReal
    {n : ℕ} (σ : ℝ) (μ y : Vector n) : ℝ :=
  ∏ i : Fin n,
    ProbabilityTheory.gaussianPDFReal (μ i) (variance σ) (y i)

lemma pdfReal_eq_posConst_mul_density
    {n : ℕ} (σ : ℝ) (μ y : Vector n) :
    pdfReal σ μ y
      =
        (normalization σ) ^ n * density σ μ y := by
  unfold pdfReal density
  simp_rw [gaussianPDFReal_eq_normConst_mul_exp]
  rw [Finset.prod_mul_distrib]
  rw [Finset.prod_const]
  have hcard : (Finset.univ : Finset (Fin n)).card = n := by
    simp
  rw [hcard]
  rw [← Real.exp_sum]
  have hsum :
      ∑ i : Fin n, (-(y i - μ i) ^ 2) / (2 * σ ^ 2)
        = -(∑ i : Fin n, (y i - μ i) ^ 2) / (2 * σ ^ 2) := by
    calc
      ∑ i : Fin n, (-(y i - μ i) ^ 2) / (2 * σ ^ 2)
          = ∑ i : Fin n, -((y i - μ i) ^ 2 / (2 * σ ^ 2)) := by
              refine Finset.sum_congr rfl ?_
              intro i _
              ring
      _ = -∑ i : Fin n, ((y i - μ i) ^ 2 / (2 * σ ^ 2)) := by
              rw [← Finset.sum_neg_distrib]
      _ = -((∑ i : Fin n, (y i - μ i) ^ 2) / (2 * σ ^ 2)) := by
              rw [Finset.sum_div]
      _ = -(∑ i : Fin n, (y i - μ i) ^ 2) / (2 * σ ^ 2) := by
              ring
  rw [hsum]

lemma pdfReal_le_normConst_pow
    {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0) (μ y : Vector n) :
    pdfReal σ μ y ≤ (normalization σ) ^ n := by
  rw [pdfReal_eq_posConst_mul_density]
  have hc_nonneg : 0 ≤ (normalization σ) ^ n :=
    le_of_lt (normalization_pow_pos (n := n) hσ)
  have hdens : density σ μ y ≤ 1 :=
    density_le_one hσ μ y
  calc
    (normalization σ) ^ n * density σ μ y
        ≤ (normalization σ) ^ n * 1 :=
          mul_le_mul_of_nonneg_left hdens hc_nonneg
    _ = (normalization σ) ^ n := by ring

lemma pdfReal_le_normConst_pow_mul_exp_neg_sqLower
    {n : ℕ} {σ sqLower : ℝ} (hσ : σ ≠ 0) (μ y : Vector n)
    (hLower : sqLower ≤ ∑ i : Fin n, (y i - μ i) ^ 2) :
    pdfReal σ μ y
      ≤ (normalization σ) ^ n * Real.exp (-sqLower / (2 * σ ^ 2)) := by
  rw [pdfReal_eq_posConst_mul_density]
  have hc_nonneg : 0 ≤ (normalization σ) ^ n :=
    le_of_lt (normalization_pow_pos (n := n) hσ)
  have hdens :
      density σ μ y
        ≤ Real.exp (-sqLower / (2 * σ ^ 2)) :=
    density_le_exp_neg_sqLower hσ μ y hLower
  exact mul_le_mul_of_nonneg_left hdens hc_nonneg

lemma centered_pdf_gap_eq_posConst_mul_centered_density_gap
    {n : ℕ} (d y : Vector n) (σ ε : ℝ) :
    pdfReal σ d y
      - Real.exp ε * pdfReal σ (-d) y
    =
    (normalization σ) ^ n *
      (density σ d y
        - Real.exp ε * density σ (-d) y) := by
  rw [pdfReal_eq_posConst_mul_density]
  rw [pdfReal_eq_posConst_mul_density]
  ring

lemma centered_pdf_gap_nonneg_iff
    {n : ℕ} (d y : Vector n) (σ ε : ℝ) (hσ : σ ≠ 0) :
    0 ≤
      pdfReal σ d y
        - Real.exp ε * pdfReal σ (-d) y
      ↔
    0 ≤
      density σ d y
        - Real.exp ε * density σ (-d) y := by
  rw [centered_pdf_gap_eq_posConst_mul_centered_density_gap]
  let c : ℝ := (normalization σ) ^ n
  have hc : 0 < c := by
    dsimp [c]
    exact normalization_pow_pos hσ
  constructor
  · intro h
    have h' :
        0 ≤ c *
          (density σ d y
            - Real.exp ε * density σ (-d) y) := by
      simpa [c] using h
    exact (mul_nonneg_iff_of_pos_left hc).mp h'
  · intro h
    have h' :
        0 ≤ c *
          (density σ d y
            - Real.exp ε * density σ (-d) y) := by
      exact mul_nonneg (le_of_lt hc) h
    simpa [c] using h'

def pdf
    {n : ℕ} (σ : ℝ) (μ y : Vector n) : ENNReal :=
  ENNReal.ofReal (pdfReal σ μ y)

theorem pdfReal_nonneg
    {n : ℕ} (σ : ℝ) (μ y : Vector n) :
    0 ≤ pdfReal σ μ y := by
  unfold pdfReal
  exact Finset.prod_nonneg (fun i _ =>
    ProbabilityTheory.gaussianPDFReal_nonneg (μ i) (variance σ) (y i))

theorem pdfReal_pos
    {n : ℕ} (σ : ℝ) (μ y : Vector n)
    (hσ : σ ≠ 0) :
    0 < pdfReal σ μ y := by
  unfold pdfReal
  have hvar : variance σ ≠ 0 := by
    intro hzero
    have hsq : (σ ^ 2 : ℝ) = 0 := by
      exact congrArg (fun x : NNReal => (x : ℝ)) hzero
    exact hσ (sq_eq_zero_iff.mp hsq)
  refine Finset.prod_pos ?_
  intro i _
  exact ProbabilityTheory.gaussianPDFReal_pos
    (μ i) (variance σ) (y i) hvar

theorem measurable_pdfReal
    {n : ℕ} (σ : ℝ) (μ : Vector n) :
    Measurable (fun y : Vector n => pdfReal σ μ y) := by
  unfold pdfReal
  exact Finset.measurable_fun_prod Finset.univ (fun i _ =>
    (ProbabilityTheory.measurable_gaussianPDFReal
      (μ i) (variance σ)).comp (measurable_pi_apply i))

theorem measurable_pdf
    {n : ℕ} (σ : ℝ) (μ : Vector n) :
    Measurable (fun y : Vector n => pdf σ μ y) := by
  unfold pdf
  exact Measurable.ennreal_ofReal (measurable_pdfReal (σ := σ) (μ := μ))

@[simp] theorem toReal_pdf
    {n : ℕ} (σ : ℝ) (μ y : Vector n) :
    (pdf σ μ y).toReal = pdfReal σ μ y := by
  unfold pdf
  rw [ENNReal.toReal_ofReal (pdfReal_nonneg _ _ _)]

theorem ofReal_pdfReal
    {n : ℕ} (σ : ℝ) (μ y : Vector n) :
    ENNReal.ofReal (pdfReal σ μ y) = pdf σ μ y := by
  rfl

lemma pdfReal_piFinSuccAbove_symm
    {n : ℕ} (σ : ℝ) (μ : Vector (n + 1)) :
    let e : Vector (n + 1) ≃ᵐ (ℝ × Vector n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    ∀ z : ℝ × Vector n,
      pdfReal σ μ (e.symm z)
        = ProbabilityTheory.gaussianPDFReal (μ 0) (variance σ) z.1
            * pdfReal σ (fun i : Fin n => μ i.succ) z.2 := by
  intro e z
  rcases z with ⟨z0, zt⟩
  unfold pdfReal
  rw [Fin.prod_univ_succ]
  simp [e, MeasurableEquiv.piFinSuccAbove]

lemma pdf_piFinSuccAbove_symm
    {n : ℕ} (σ : ℝ) (μ : Vector (n + 1)) :
    let e : Vector (n + 1) ≃ᵐ (ℝ × Vector n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    ∀ z : ℝ × Vector n,
      pdf σ μ (e.symm z)
        = ProbabilityTheory.gaussianPDF (μ 0) (variance σ) z.1
            * pdf σ (fun i : Fin n => μ i.succ) z.2 := by
  intro e z
  rcases z with ⟨z0, zt⟩
  unfold pdf
  rw [pdfReal_piFinSuccAbove_symm (σ := σ) (μ := μ) (z := (z0, zt))]
  rw [ProbabilityTheory.gaussianPDF_def]
  rw [ENNReal.ofReal_mul (ProbabilityTheory.gaussianPDFReal_nonneg _ _ _)]

lemma density_centered_expDiff
    {n : ℕ} (σ : ℝ) (d y : Vector n) :
    (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
      - (-(∑ i : Fin n, (y i + d i) ^ 2) / (2 * σ ^ 2))
      = (2 * dot d y) / (σ ^ 2) := by
  unfold dot
  have hsum :
      (∑ i : Fin n, (y i + d i) ^ 2) - (∑ i : Fin n, (y i - d i) ^ 2)
        = 4 * ∑ i : Fin n, d i * y i := by
    calc
      (∑ i : Fin n, (y i + d i) ^ 2) - (∑ i : Fin n, (y i - d i) ^ 2)
          = ∑ i : Fin n, ((y i + d i) ^ 2 - (y i - d i) ^ 2) := by
            rw [Finset.sum_sub_distrib]
      _ = ∑ i : Fin n, (4 * (d i * y i)) := by
            refine Finset.sum_congr rfl ?_
            intro i _
            ring
      _ = 4 * ∑ i : Fin n, d i * y i := by
            rw [Finset.mul_sum]
  calc
    (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
        - (-(∑ i : Fin n, (y i + d i) ^ 2) / (2 * σ ^ 2))
      = ((∑ i : Fin n, (y i + d i) ^ 2) - (∑ i : Fin n, (y i - d i) ^ 2)) / (2 * σ ^ 2) := by
          ring
    _ = (4 * ∑ i : Fin n, d i * y i) / (2 * σ ^ 2) := by rw [hsum]
    _ = (2 * ∑ i : Fin n, d i * y i) / (σ ^ 2) := by ring
    _ = (2 * dot d y) / (σ ^ 2) := by rfl

lemma density_centered_ratio_ge_iff
    {n : ℕ} (d y : Vector n) (σ ε : ℝ)
    :
    density σ d y
      ≥ Real.exp ε * density σ (fun i => -d i) y
      ↔ ε ≤ (2 * dot d y) / (σ ^ 2) := by
  unfold density
  constructor
  · intro hge
    have hlog :
        Real.log (Real.exp ε * Real.exp (-(∑ i : Fin n, (y i - -d i) ^ 2) / (2 * σ ^ 2)))
          ≤ Real.log (Real.exp (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))) := by
      exact Real.log_le_log (by positivity) hge
    have hlin :
        ε + (-(∑ i : Fin n, (y i - -d i) ^ 2) / (2 * σ ^ 2))
          ≤ (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2)) := by
      simpa [Real.log_mul, Real.log_exp, add_comm, add_left_comm, add_assoc] using hlog
    have hdiff :
        ε ≤
          (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
            - (-(∑ i : Fin n, (y i - -d i) ^ 2) / (2 * σ ^ 2)) := by
      linarith
    have hdiff' :
        ε ≤
          (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
            - (-(∑ i : Fin n, (y i + d i) ^ 2) / (2 * σ ^ 2)) := by
      simpa [sub_eq_add_neg] using hdiff
    calc
      ε ≤
          (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
            - (-(∑ i : Fin n, (y i + d i) ^ 2) / (2 * σ ^ 2)) := hdiff'
      _ = (2 * dot d y) / (σ ^ 2) := by
            simpa using density_centered_expDiff (σ := σ) (d := d) (y := y)
  · intro hle
    have hdiff :
        (-(∑ i : Fin n, (y i - -d i) ^ 2) / (2 * σ ^ 2)) + ε
          ≤ (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2)) := by
      have hrewrite :
          (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2))
            - (-(∑ i : Fin n, (y i - -d i) ^ 2) / (2 * σ ^ 2))
            = (2 * dot d y) / (σ ^ 2) := by
        simpa [sub_eq_add_neg] using
          density_centered_expDiff (σ := σ) (d := d) (y := y)
      linarith [hle, hrewrite]
    have hexp :
        Real.exp (ε + (-(∑ i : Fin n, (y i - -d i) ^ 2) / (2 * σ ^ 2)))
          ≤ Real.exp (-(∑ i : Fin n, (y i - d i) ^ 2) / (2 * σ ^ 2)) := by
      exact Real.exp_le_exp.mpr (by simpa [add_comm] using hdiff)
    simpa [Real.exp_add, mul_comm, mul_left_comm, mul_assoc] using hexp

lemma density_centered_sub_nonneg_iff
    {n : ℕ} (d y : Vector n) (σ ε : ℝ) :
    0 ≤ density σ d y
          - Real.exp ε * density σ (fun i => -d i) y
      ↔ ε ≤ (2 * dot d y) / (σ ^ 2) := by
  have hmul_nonneg :
      0 ≤ Real.exp ε * density σ (fun i => -d i) y := by
    exact mul_nonneg (le_of_lt (Real.exp_pos ε))
      (density_nonneg σ (fun i => -d i) y)
  constructor
  · intro h
    have hge :
        density σ d y
          ≥ Real.exp ε * density σ (fun i => -d i) y := by
      linarith
    exact (density_centered_ratio_ge_iff (d := d) (y := y) (σ := σ) (ε := ε)).1 hge
  · intro h
    have hge :
        density σ d y
          ≥ Real.exp ε * density σ (fun i => -d i) y :=
      (density_centered_ratio_ge_iff (d := d) (y := y) (σ := σ) (ε := ε)).2 h
    linarith

def densityENN
    {n : ℕ} (σ : ℝ) (μ y : Vector n) : ENNReal :=
  ENNReal.ofReal (density σ μ y)

def measure
    {n : ℕ} (σ : ℝ) (μ : Vector n) :
    MeasureTheory.Measure (Vector n) :=
  FiniteProductGaussian.law μ (fun _ => σ)

/-- The isotropic law is exactly its coordinate Gaussian product at every real scale. -/
theorem measure_eq_pi {n : ℕ} (σ : ℝ) (μ : Vector n) :
    measure σ μ = MeasureTheory.Measure.pi (fun i =>
      ProbabilityTheory.gaussianReal (μ i) (variance σ)) := rfl

lemma variance_ne_zero (σ : ℝ) (hσ : σ ≠ 0) :
    variance σ ≠ 0 := by
  intro h
  apply hσ
  have h' : (σ ^ 2 : ℝ) = 0 := by
    exact congrArg (fun t : NNReal => (t : ℝ)) h
  nlinarith

theorem measure_eq_pi_withDensity
    {n : ℕ} (σ : ℝ) (μ : Vector n) (hσ : σ ≠ 0) :
    measure σ μ
      = MeasureTheory.Measure.pi (fun i : Fin n =>
          MeasureTheory.volume.withDensity
            (ProbabilityTheory.gaussianPDF (μ i) (variance σ))) := by
  simp only [measure_eq_pi]
  have hvar : variance σ ≠ 0 :=
    variance_ne_zero σ hσ
  congr
  funext i
  exact ProbabilityTheory.gaussianReal_of_var_ne_zero (μ i) hvar

instance measure_isProbability
    {n : ℕ} (σ : ℝ) (μ : Vector n) :
    MeasureTheory.IsProbabilityMeasure (measure σ μ) := by
  simp only [measure_eq_pi]
  infer_instance

theorem measure_map_eval
    {n : ℕ} (σ : ℝ) (μ : Vector n) (i : Fin n) :
    (measure σ μ).map (Function.eval i)
      = ProbabilityTheory.gaussianReal (μ i) (variance σ) := by
  simp only [measure_eq_pi]
  rw [MeasureTheory.Measure.pi_map_eval]
  simp

theorem measure_map_piFinSuccAbove
    {n : ℕ} (σ : ℝ) (μ : Vector (n + 1)) :
    let e : Vector (n + 1) ≃ᵐ (ℝ × Vector n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    (measure σ μ).map e
      =
        (ProbabilityTheory.gaussianReal (μ 0) (variance σ)).prod
          (measure σ (fun i : Fin n => μ i.succ)) := by
  intro e
  unfold e
  simp only [measure_eq_pi]
  simpa using (MeasureTheory.measurePreserving_piFinSuccAbove
    (μ := fun i : Fin (n + 1) =>
        ProbabilityTheory.gaussianReal (μ i) (variance σ))
    0).map_eq

theorem pdfMeasure_map_piFinSuccAbove
    {n : ℕ} (σ : ℝ) (μ : Vector (n + 1)) :
    let e : Vector (n + 1) ≃ᵐ (ℝ × Vector n) :=
      MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
    ((MeasureTheory.volume.withDensity (pdf σ μ)).map e)
      =
        (MeasureTheory.volume.withDensity
          (ProbabilityTheory.gaussianPDF (μ 0) (variance σ))).prod
          (MeasureTheory.volume.withDensity
            (pdf σ (fun i : Fin n => μ i.succ))) := by
  intro e
  refine MeasureTheory.Measure.ext fun s hs => ?_
  rw [MeasureTheory.Measure.map_apply e.measurable hs]
  rw [MeasureTheory.withDensity_apply' _ _]
  have hmp :=
    MeasureTheory.volume_preserving_piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
  have htransport :
      ∫⁻ a in e ⁻¹' s, pdf σ μ a ∂MeasureTheory.volume
        = ∫⁻ z in s, pdf σ μ (e.symm z) ∂MeasureTheory.volume := by
    have h0 :=
      hmp.setLIntegral_comp_preimage_emb
        e.measurableEmbedding
        (f := fun z : ℝ × Vector n => pdf σ μ (e.symm z))
        (s := s)
    have hleft :
        ∫⁻ a in e ⁻¹' s, pdf σ μ a ∂MeasureTheory.volume
          =
        ∫⁻ a in e ⁻¹' s,
          pdf σ μ
            ((Fin.consEquiv (fun _ : Fin (n + 1) => ℝ)) (a 0, Fin.tail a))
          ∂MeasureTheory.volume := by
      refine MeasureTheory.lintegral_congr_ae ?_
      filter_upwards with a
      simp [Fin.consEquiv, Fin.cons_self_tail]
    calc
      ∫⁻ a in e ⁻¹' s, pdf σ μ a ∂MeasureTheory.volume
        =
          ∫⁻ a in e ⁻¹' s,
            pdf σ μ ((Fin.consEquiv (fun _ : Fin (n + 1) => ℝ)) (a 0, Fin.tail a))
            ∂MeasureTheory.volume := hleft
      _ = ∫⁻ z in s, pdf σ μ (e.symm z) ∂MeasureTheory.volume := by
            simpa [Vector, e, MeasurableEquiv.piFinSuccAbove] using h0
  rw [htransport]
  have hsplit :
      (fun z : ℝ × Vector n => pdf σ μ (e.symm z))
        =
      (fun z : ℝ × Vector n =>
        ProbabilityTheory.gaussianPDF (μ 0) (variance σ) z.1
          * pdf σ (fun i : Fin n => μ i.succ) z.2) := by
    funext z
    exact pdf_piFinSuccAbove_symm (σ := σ) (μ := μ) (z := z)
  rw [hsplit]
  rw [MeasureTheory.Measure.volume_eq_prod]
  rw [← MeasureTheory.withDensity_apply' _ s]
  rw [← MeasureTheory.prod_withDensity
    (ProbabilityTheory.measurable_gaussianPDF (μ 0) (variance σ))
    (measurable_pdf (σ := σ) (μ := fun i : Fin n => μ i.succ))]

theorem measure_eq_withDensity_pdf
    {n : ℕ} (σ : ℝ) (μ : Vector n) (hσ : σ ≠ 0) :
    measure σ μ = MeasureTheory.volume.withDensity (pdf σ μ) := by
  induction n with
  | zero =>
      have hleft :
          measure σ μ = MeasureTheory.Measure.dirac (fun i : Fin 0 => nomatch i) := by
        simpa only [measure_eq_pi] using
          (MeasureTheory.Measure.pi_of_empty
            (fun i : Fin 0 =>
              ProbabilityTheory.gaussianReal (μ i) (variance σ))
            (fun i : Fin 0 => nomatch i))
      have hpdf : pdf σ μ = (fun _ : Vector 0 => 1) := by
        funext y
        simp [pdf, pdfReal]
      rw [hleft, hpdf]
      have hwd :
          (MeasureTheory.volume : MeasureTheory.Measure (Vector 0)).withDensity
              (fun _ => (1 : ENNReal))
            = MeasureTheory.volume := by
        exact
          MeasureTheory.withDensity_one
            (μ := (MeasureTheory.volume : MeasureTheory.Measure (Vector 0)))
      rw [hwd]
      simpa using
        (MeasureTheory.Measure.volume_pi_eq_dirac
          (α := fun _ : Fin 0 => ℝ) (x := fun i => nomatch i)).symm
  | succ n ih =>
      let e : Vector (n + 1) ≃ᵐ (ℝ × Vector n) :=
        MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
      apply (e.map_measurableEquiv_injective)
      rw [measure_map_piFinSuccAbove (σ := σ) (μ := μ)]
      rw [pdfMeasure_map_piFinSuccAbove (σ := σ) (μ := μ)]
      rw [ProbabilityTheory.gaussianReal_of_var_ne_zero (μ 0) (variance_ne_zero σ hσ)]
      rw [ih (μ := fun i : Fin n => μ i.succ)]

theorem integrable_pdfReal
    {n : ℕ} (σ : ℝ) (μ : Vector n) (hσ : σ ≠ 0) :
    MeasureTheory.Integrable (fun y : Vector n => pdfReal σ μ y)
      MeasureTheory.volume := by
  have hlin :
      ∫⁻ y, pdf σ μ y ∂MeasureTheory.volume = 1 := by
    calc
      ∫⁻ y, pdf σ μ y ∂MeasureTheory.volume
          = (MeasureTheory.volume.withDensity (pdf σ μ)) Set.univ := by
              rw [MeasureTheory.withDensity_apply _ MeasurableSet.univ]
              simp
      _ = measure σ μ Set.univ := by
              rw [← measure_eq_withDensity_pdf (σ := σ) (μ := μ) hσ]
      _ = 1 := MeasureTheory.IsProbabilityMeasure.measure_univ
  have hfin : (∫⁻ y, pdf σ μ y ∂MeasureTheory.volume) ≠ ⊤ := by
    rw [hlin]
    simp
  have hbase :=
    MeasureTheory.integrable_toReal_of_lintegral_ne_top
      (measurable_pdf (σ := σ) (μ := μ)).aemeasurable
      hfin
  simpa [toReal_pdf] using hbase

theorem measure_apply_eval_preimage
    {n : ℕ} (σ : ℝ) (μ : Vector n) (i : Fin n) (s : Set ℝ)
    (hs : MeasurableSet s) :
    measure σ μ (Function.eval i ⁻¹' s)
      = ProbabilityTheory.gaussianReal (μ i) (variance σ) s := by
  have hmap := measure_map_eval (σ := σ) (μ := μ) i
  rw [← hmap]
  exact (MeasureTheory.Measure.map_apply (by fun_prop) hs).symm

theorem measure_apply_eval_preimage_Iic
    {n : ℕ} (σ : ℝ) (μ : Vector n) (i : Fin n) (t : ℝ) :
    measure σ μ (Function.eval i ⁻¹' Set.Iic t)
      = ProbabilityTheory.gaussianReal (μ i) (variance σ) (Set.Iic t) := by
  simpa using
    measure_apply_eval_preimage (σ := σ) (μ := μ) i (Set.Iic t) measurableSet_Iic

theorem measure_map_apply_Ici_eq_map_neg_apply_Iic
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (f : α → ℝ)
    (hf : Measurable f)
    (t : ℝ) :
    (μ.map f) (Set.Ici t)
      = (μ.map (fun x => -f x)) (Set.Iic (-t)) := by
  have hmap :
      (μ.map f).map (fun y : ℝ => -y)
        = μ.map (fun x => -f x) := by
    rw [MeasureTheory.Measure.map_map (by fun_prop) hf]
    rfl
  have hpre : (fun y : ℝ => -y) ⁻¹' Set.Iic (-t) = Set.Ici t := by
    ext y
    simp
  calc
    (μ.map f) (Set.Ici t)
      = ((μ.map f).map (fun y : ℝ => -y)) (Set.Iic (-t)) := by
          rw [MeasureTheory.Measure.map_apply (by fun_prop) measurableSet_Iic, hpre]
    _ = (μ.map (fun x => -f x)) (Set.Iic (-t)) := by rw [hmap]

theorem measure_map_add_const
    {n : ℕ} (σ : ℝ) (μ c : Vector n) :
    (measure σ μ).map (fun x : Vector n => fun i => x i + c i)
      = measure σ (fun i => μ i + c i) := by
  simp only [measure_eq_pi]
  rw [MeasureTheory.Measure.pi_map_pi
      (μ := fun i : Fin n => ProbabilityTheory.gaussianReal (μ i) (variance σ))
      (f := fun i : Fin n => fun x : ℝ => x + c i)
      (hf := fun i => (continuous_add_right (c i)).measurable.aemeasurable)]
  refine MeasureTheory.Measure.pi_eq ?_
  intro s hs
  simp [ProbabilityTheory.gaussianReal_map_add_const]

theorem measure_map_sub_const
    {n : ℕ} (σ : ℝ) (μ c : Vector n) :
    (measure σ μ).map (fun x : Vector n => fun i => x i - c i)
      = measure σ (fun i => μ i - c i) := by
  simpa [sub_eq_add_neg] using
    measure_map_add_const (σ := σ) (μ := μ) (c := fun i => -c i)

theorem measure_map_neg
    {n : ℕ} (σ : ℝ) (μ : Vector n) :
    (measure σ μ).map (fun x : Vector n => fun i => -x i)
      = measure σ (fun i => -μ i) := by
  simp only [measure_eq_pi]
  rw [MeasureTheory.Measure.pi_map_pi
      (μ := fun i : Fin n => ProbabilityTheory.gaussianReal (μ i) (variance σ))
      (f := fun _i : Fin n => fun x : ℝ => -x)
      (hf := fun _ => measurable_neg.aemeasurable)]
  refine MeasureTheory.Measure.pi_eq ?_
  intro s hs
  simp [ProbabilityTheory.gaussianReal_map_neg]

theorem measure_map_dot_add_const
    {n : ℕ} (σ : ℝ) (μ c d : Vector n) :
    (measure σ (fun i => μ i + c i)).map (fun y : Vector n => dot d y)
      =
        ((measure σ μ).map (fun y : Vector n => dot d y)).map
          (fun t : ℝ => t + dot d c) := by
  have hmeasDot : Measurable (fun y : Vector n => dot d y) := measurable_dot_left d
  have hmeasShift : Measurable (fun t : ℝ => t + dot d c) := by
    fun_prop
  have hmap :
      (measure σ (fun i => μ i + c i)).map (fun y : Vector n => dot d y)
        =
          (measure σ μ).map (fun x : Vector n => dot d (fun i => x i + c i)) := by
    rw [← measure_map_add_const (σ := σ) (μ := μ) (c := c)]
    rw [MeasureTheory.Measure.map_map hmeasDot (by fun_prop)]
    rfl
  have hdot :
      (fun x : Vector n => dot d (fun i => x i + c i))
        = fun x : Vector n => dot d x + dot d c := by
    funext x
    simpa using dot_add_right d x c
  rw [hmap, hdot]
  rw [MeasureTheory.Measure.map_map hmeasShift hmeasDot]
  rfl

theorem measure_map_dot_eq_centered_map_shift
    {n : ℕ} (σ : ℝ) (μ d : Vector n) :
    (measure σ μ).map (fun y : Vector n => dot d y)
      =
        ((measure σ (fun _ => (0 : ℝ))).map (fun y : Vector n => dot d y)).map
          (fun t : ℝ => t + dot d μ) := by
  simpa [zero_add] using
    (measure_map_dot_add_const
      (σ := σ) (μ := (fun _ => (0 : ℝ))) (c := μ) (d := d))

theorem measure_map_neg_dot_eq_centered_map_shift
    {n : ℕ} (σ : ℝ) (μ d : Vector n) :
    (measure σ μ).map (fun y : Vector n => -dot d y)
      =
        ((measure σ (fun _ => (0 : ℝ))).map (fun y : Vector n => -dot d y)).map
          (fun t : ℝ => t - dot d μ) := by
  have h1 :
      (measure σ μ).map (fun y : Vector n => -dot d y)
        =
          (measure σ μ).map (fun y : Vector n => dot (fun i => -d i) y) := by
    congr 1
    funext y
    simpa using (dot_neg_left d y).symm
  have h2 :
      ((measure σ (fun _ => (0 : ℝ))).map (fun y : Vector n => -dot d y))
        =
          ((measure σ (fun _ => (0 : ℝ))).map
            (fun y : Vector n => dot (fun i => -d i) y)) := by
    congr 1
    funext y
    simpa using (dot_neg_left d y).symm
  rw [h1, h2]
  have hbase :=
    measure_map_dot_eq_centered_map_shift
      (σ := σ) (μ := μ) (d := (fun i => -d i))
  refine hbase.trans ?_
  congr 2
  funext t
  have hdot : dot (fun i => -d i) μ = -dot d μ := dot_neg_left d μ
  rw [hdot]
  ring

theorem measure_map_neg_dot_negMean_eq_centered_map_shift
    {n : ℕ} (σ : ℝ) (d : Vector n) :
    (measure σ (fun i => -d i)).map (fun y : Vector n => -dot d y)
      =
        ((measure σ (fun _ => (0 : ℝ))).map (fun y : Vector n => -dot d y)).map
          (fun t : ℝ => t + dot d d) := by
  have hbase :=
    measure_map_neg_dot_eq_centered_map_shift
      (σ := σ) (μ := (fun i => -d i)) (d := d)
  refine hbase.trans ?_
  congr 2
  funext t
  have hdot : dot d (fun i => -d i) = -dot d d := dot_neg_right d d
  rw [hdot]
  ring

theorem measure_map_neg_dot_centered_eq_gaussianReal_sumSq
    {n : ℕ} (σ : ℝ) (d : Vector n) :
    ((measure σ (fun _ : Fin n => (0 : ℝ))).map (fun y : Vector n => -dot d y))
      = ProbabilityTheory.gaussianReal 0
          (⟨σ ^ 2 * (∑ i : Fin n, (d i) ^ 2),
            mul_nonneg (sq_nonneg σ) (Finset.sum_nonneg (fun i _ => sq_nonneg (d i)))⟩) := by
  induction n with
  | zero =>
      have hconst : (fun y : Vector 0 => -dot d y) = fun _ => (0 : ℝ) := by
        funext y
        unfold dot
        simp
      rw [hconst, MeasureTheory.Measure.map_const]
      have hprob : (measure σ (fun _ : Fin 0 => (0 : ℝ))) Set.univ = 1 := by
        simp
      rw [hprob, one_smul]
      have hvar0 :
          (⟨σ ^ 2 * (∑ i : Fin 0, (d i) ^ 2),
            mul_nonneg (sq_nonneg σ) (Finset.sum_nonneg (fun i _ => sq_nonneg (d i)))⟩ : NNReal)
            = 0 := by
        ext
        change σ ^ 2 * (∑ i : Fin 0, (d i) ^ 2) = (0 : ℝ)
        simp
      rw [hvar0]
      exact (ProbabilityTheory.gaussianReal_zero_var (0 : ℝ)).symm
  | succ n ih =>
      let e : Vector (n + 1) ≃ᵐ (ℝ × Vector n) :=
        MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0
      let dTail : Vector n := fun i => d i.succ
      let μ0 : MeasureTheory.Measure ℝ :=
        ProbabilityTheory.gaussianReal 0 (variance σ)
      let μTail : MeasureTheory.Measure (Vector n) :=
        measure σ (fun _ : Fin n => (0 : ℝ))
      have hsplit :
          (measure σ (fun _ : Fin (n + 1) => (0 : ℝ))).map e = μ0.prod μTail := by
        unfold μ0 μTail e
        simp only [measure_eq_pi]
        simpa using (MeasureTheory.measurePreserving_piFinSuccAbove
          (μ := fun _ : Fin (n + 1) =>
            ProbabilityTheory.gaussianReal (0 : ℝ) (variance σ))
          0).map_eq
      have hcomp :
          ((measure σ (fun _ : Fin (n + 1) => (0 : ℝ))).map
            (fun y : Vector (n + 1) => -dot d y))
            = ((μ0.prod μTail).map
                (fun z : ℝ × Vector n => -dot d (e.symm z))) := by
        rw [← hsplit]
        have hmeasComp : Measurable (fun z : ℝ × Vector n => -dot d (e.symm z)) := by
          exact (measurable_dot_left d).neg.comp e.symm.measurable
        rw [MeasureTheory.Measure.map_map hmeasComp (by fun_prop)]
        congr 1
        funext y
        exact
          congrArg (fun t : Vector (n + 1) => -dot d t)
            (e.symm_apply_apply y).symm
      let X : ℝ × Vector n → ℝ := fun z => -d 0 * z.1
      let Y : ℝ × Vector n → ℝ := fun z => -dot dTail z.2
      have hXY :
          (fun z : ℝ × Vector n => -dot d (e.symm z)) = X + Y := by
        funext z
        rcases z with ⟨z0, zt⟩
        dsimp [X, Y, dTail]
        have hdot :
            dot d (e.symm (z0, zt)) = d 0 * z0 + dot (fun i : Fin n => d i.succ) zt := by
          unfold e dot
          rw [Fin.sum_univ_succ]
          simp [MeasurableEquiv.piFinSuccAbove]
        linarith
      have hXmap :
          (μ0.prod μTail).map X
            = ProbabilityTheory.gaussianReal 0
                (NNReal.mk ((-d 0) ^ 2) (sq_nonneg (-d 0)) *
                  variance σ) := by
        unfold X
        change MeasureTheory.Measure.map ((fun x : ℝ => -d 0 * x) ∘ Prod.fst) (μ0.prod μTail) = _
        rw [← MeasureTheory.Measure.map_map (by fun_prop) measurable_fst]
        rw [MeasureTheory.Measure.map_fst_prod]
        simp [μTail]
        simpa [μ0] using
          (ProbabilityTheory.gaussianReal_map_const_mul
            (μ := 0) (v := variance σ) (-d 0))
      have hYmap :
          (μ0.prod μTail).map Y
            = ProbabilityTheory.gaussianReal 0
                (⟨σ ^ 2 * (∑ i : Fin n, (dTail i) ^ 2),
                  mul_nonneg (sq_nonneg σ)
                    (Finset.sum_nonneg (fun i _ => sq_nonneg (dTail i)))⟩) := by
        unfold Y
        change
          MeasureTheory.Measure.map
              ((fun y : Vector n => -dot dTail y) ∘ Prod.snd)
              (μ0.prod μTail) = _
        have hneg : Measurable (fun y : Vector n => -dot dTail y) := by
          convert (measurable_dot_left dTail).neg using 1
          funext y
          rfl
        rw [← MeasureTheory.Measure.map_map hneg measurable_snd]
        rw [MeasureTheory.Measure.map_snd_prod]
        simp [μ0]
        simpa [μTail] using ih (d := dTail)
      have hIndep : ProbabilityTheory.IndepFun X Y (μ0.prod μTail) := by
        unfold X Y
        have hneg : Measurable (fun y : Vector n => -dot dTail y) := by
          convert (measurable_dot_left dTail).neg using 1
          funext y
          rfl
        simpa using (ProbabilityTheory.indepFun_prod
          (μ := μ0) (ν := μTail)
          (X := fun x : ℝ => -d 0 * x)
          (Y := fun y : Vector n => -dot dTail y)
          (by fun_prop) hneg)
      have hsum :=
        ProbabilityTheory.gaussianReal_add_gaussianReal_of_indepFun
          (hXY := hIndep) (hX := hXmap) (hY := hYmap)
      have hsum' :
          (μ0.prod μTail).map (fun z : ℝ × Vector n => -dot d (e.symm z))
            = ProbabilityTheory.gaussianReal 0
                ((NNReal.mk ((-d 0) ^ 2) (sq_nonneg (-d 0)) * variance σ)
                  + ⟨σ ^ 2 * (∑ i : Fin n, (dTail i) ^ 2),
                      mul_nonneg (sq_nonneg σ)
                        (Finset.sum_nonneg (fun i _ => sq_nonneg (dTail i)))⟩) := by
        simpa [hXY] using hsum
      rw [hcomp, hsum']
      congr 2
      apply Subtype.ext
      let prodNN : NNReal :=
        NNReal.mk ((-d 0) ^ 2) (sq_nonneg (-d 0)) *
          (variance σ)
      let tailNN : NNReal :=
        ⟨σ ^ 2 * ∑ i : Fin n, (dTail i) ^ 2,
          mul_nonneg (sq_nonneg σ)
            (Finset.sum_nonneg (fun i _ => sq_nonneg (dTail i)))⟩
      have hprod :
          (↑prodNN : ℝ)
            = d 0 ^ 2 * σ ^ 2 := by
        dsimp [prodNN]
        change (-d 0) ^ 2 * σ ^ 2 = d 0 ^ 2 * σ ^ 2
        ring
      have htail :
          (↑tailNN : ℝ)
            = σ ^ 2 * ∑ i : Fin n, (dTail i) ^ 2 := rfl
      have hleft :
          (↑(prodNN + tailNN) : ℝ)
            = d 0 ^ 2 * σ ^ 2 + σ ^ 2 * ∑ i : Fin n, (dTail i) ^ 2 := by
        change (↑prodNN : ℝ) + (↑tailNN : ℝ)
          = d 0 ^ 2 * σ ^ 2 + σ ^ 2 * ∑ i : Fin n, (dTail i) ^ 2
        rw [hprod, htail]
      have hcomm :
          d 0 ^ 2 * σ ^ 2 + σ ^ 2 * (∑ i : Fin n, (dTail i) ^ 2)
            = σ ^ 2 * d 0 ^ 2 + σ ^ 2 * ∑ x : Fin n, d x.succ ^ 2 := by
        dsimp [dTail]
        ring
      have htarget :
          (↑(⟨σ ^ 2 * ∑ i : Fin (n + 1), d i ^ 2,
              mul_nonneg (sq_nonneg σ)
                (Finset.sum_nonneg (fun i _ => sq_nonneg (d i)))⟩ : NNReal) : ℝ)
            = σ ^ 2 * ∑ i : Fin (n + 1), d i ^ 2 := rfl
      have hright :
          σ ^ 2 * (∑ i : Fin (n + 1), d i ^ 2)
            = σ ^ 2 * d 0 ^ 2 + σ ^ 2 * ∑ x : Fin n, d x.succ ^ 2 := by
        rw [Fin.sum_univ_succ]
        ring
      change (↑(prodNN + tailNN) : ℝ)
        = (↑(⟨σ ^ 2 * ∑ i : Fin (n + 1), d i ^ 2,
            mul_nonneg (sq_nonneg σ)
              (Finset.sum_nonneg (fun i _ => sq_nonneg (d i)))⟩ : NNReal) : ℝ)
      nlinarith [hleft, hcomm, htarget, hright]

theorem measure_map_neg_dot_centered_eq_gaussianReal
    {n : ℕ} (σ : ℝ) (d : Vector n) :
    ((measure σ (fun _ : Fin n => (0 : ℝ))).map (fun y : Vector n => -dot d y))
      = ProbabilityTheory.gaussianReal 0
          (⟨σ ^ 2 * dot d d,
            mul_nonneg (sq_nonneg σ) (dot_self_nonneg d)⟩) := by
  simpa [dot_self_eq_sum_sq] using
    measure_map_neg_dot_centered_eq_gaussianReal_sumSq (σ := σ) (d := d)

theorem measure_map_neg_dot_eq_gaussianReal
    {n : ℕ} (σ : ℝ) (μ d : Vector n) :
    (measure σ μ).map (fun y : Vector n => -dot d y)
      = ProbabilityTheory.gaussianReal (-dot d μ)
          (⟨σ ^ 2 * dot d d,
            mul_nonneg (sq_nonneg σ) (dot_self_nonneg d)⟩) := by
  rw [measure_map_neg_dot_eq_centered_map_shift (σ := σ) (μ := μ) (d := d)]
  rw [measure_map_neg_dot_centered_eq_gaussianReal (σ := σ) (d := d)]
  simpa [sub_eq_add_neg] using
    (ProbabilityTheory.gaussianReal_map_sub_const
      (μ := 0)
      (v := ⟨σ ^ 2 * dot d d, mul_nonneg (sq_nonneg σ) (dot_self_nonneg d)⟩)
      (dot d μ))

theorem measure_map_neg_dot_negMean_eq_gaussianReal
    {n : ℕ} (σ : ℝ) (d : Vector n) :
    (measure σ (fun i => -d i)).map (fun y : Vector n => -dot d y)
      = ProbabilityTheory.gaussianReal (dot d d)
          (⟨σ ^ 2 * dot d d,
            mul_nonneg (sq_nonneg σ) (dot_self_nonneg d)⟩) := by
  rw [measure_map_neg_dot_eq_gaussianReal (σ := σ) (μ := (fun i => -d i)) (d := d)]
  have hdot : dot d (fun i => -d i) = -dot d d := dot_neg_right d d
  rw [hdot]
  simp

def sqDist {n : ℕ} (u v : Vector n) : ℝ :=
  ∑ i : Fin n, (u i - v i) ^ 2

lemma sqDist_symm {n : ℕ} (u v : Vector n) :
    sqDist u v = sqDist v u := by
  unfold sqDist
  refine Finset.sum_congr rfl ?_
  intro i hi
  ring

lemma sqDist_scale
    {n : ℕ} (a : ℝ) (u v : Vector n) :
    sqDist (fun i => a * u i) (fun i => a * v i) = a ^ 2 * sqDist u v := by
  unfold sqDist
  calc
    (∑ i : Fin n, (a * u i - a * v i) ^ 2)
      = ∑ i : Fin n, (a ^ 2) * (u i - v i) ^ 2 := by
          refine Finset.sum_congr rfl ?_
          intro i hi
          ring
    _ = a ^ 2 * (∑ i : Fin n, (u i - v i) ^ 2) := by
          rw [← Finset.mul_sum]
    _ = a ^ 2 * sqDist u v := by rfl

def midpoint {n : ℕ} (u v : Vector n) : Vector n :=
  fun i => (u i + v i) / 2

def halfDiff {n : ℕ} (u v : Vector n) : Vector n :=
  fun i => (u i - v i) / 2

lemma sqDist_nonneg
    {n : ℕ} (u v : Vector n) :
    0 ≤ sqDist u v := by
  unfold sqDist
  exact Finset.sum_nonneg (fun i _ => sq_nonneg (u i - v i))

lemma sqDist_eq_zero_iff
    {n : ℕ} (u v : Vector n) :
    sqDist u v = 0 ↔ u = v := by
  constructor
  · intro h
    funext i
    have hnonneg : ∀ j : Fin n, 0 ≤ (u j - v j) ^ 2 := fun j => sq_nonneg (u j - v j)
    have hi :
        (u i - v i) ^ 2 ≤ sqDist u v := by
      unfold sqDist
      exact Finset.single_le_sum (fun j _ => hnonneg j) (Finset.mem_univ i)
    have hsqi : (u i - v i) ^ 2 = 0 := by
      have hle0 : (u i - v i) ^ 2 ≤ 0 := by simpa [h] using hi
      exact le_antisymm hle0 (sq_nonneg (u i - v i))
    have hsub : u i - v i = 0 := by
      exact sq_eq_zero_iff.mp hsqi
    linarith
  · intro h
    subst h
    unfold sqDist
    simp

lemma dot_self_eq_sqDist_zero
    {n : ℕ} (u : Vector n) :
    dot u u = sqDist u (fun _ => (0 : ℝ)) := by
  rw [dot_self_eq_sum_sq]
  unfold sqDist
  refine Finset.sum_congr rfl ?_
  intro i hi
  ring

def radius {n : ℕ} (u v : Vector n) : ℝ :=
  Real.sqrt (sqDist u v)

lemma radius_nonneg
    {n : ℕ} (u v : Vector n) :
    0 ≤ radius u v := by
  unfold radius
  exact Real.sqrt_nonneg _

lemma radius_sq
    {n : ℕ} (u v : Vector n) :
    (radius u v) ^ 2 = sqDist u v := by
  unfold radius
  simpa [pow_two] using Real.sq_sqrt (sqDist_nonneg u v)

lemma sqDist_le_iff_radius_le
    {n : ℕ} (u v : Vector n) (r : ℝ) (hr : 0 ≤ r) :
    sqDist u v ≤ r ^ 2 ↔ radius u v ≤ r := by
  constructor
  · intro h
    unfold radius
    exact (Real.sqrt_le_iff).2 ⟨hr, by simpa [pow_two] using h⟩
  · intro h
    have hsq : (radius u v) ^ 2 ≤ r ^ 2 := by
      nlinarith [h, radius_nonneg u v, hr]
    simpa [radius_sq] using hsq

theorem midpoint_add_halfDiff
    {n : ℕ} (u v : Vector n) :
    (fun i => midpoint u v i + halfDiff u v i) = u := by
  funext i
  unfold midpoint halfDiff
  ring

theorem midpoint_sub_halfDiff
    {n : ℕ} (u v : Vector n) :
    (fun i => midpoint u v i - halfDiff u v i) = v := by
  funext i
  unfold midpoint halfDiff
  ring

theorem sqDist_eq_four_mul_halfDiff
    {n : ℕ} (u v : Vector n) :
    sqDist u v = 4 * sqDist (halfDiff u v) (fun _ => (0 : ℝ)) := by
  unfold sqDist halfDiff
  calc
    (∑ i : Fin n, (u i - v i) ^ 2)
      = ∑ i : Fin n, 4 * (((u i - v i) / 2 - 0) ^ 2) := by
          refine Finset.sum_congr rfl ?_
          intro i hi
          ring
    _ = 4 * (∑ i : Fin n, (((u i - v i) / 2 - 0) ^ 2)) := by
          rw [← Finset.mul_sum]
    _ = 4 * sqDist (halfDiff u v) (fun _ => (0 : ℝ)) := by rfl

end
end Mf.Probability.FiniteGaussian
