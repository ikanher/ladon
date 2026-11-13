import Mf.DP.GaussianProfile
import Mf.DP.GaussianCore
import Mf.DP.ImportedRandomizedCertificate
import Mf.DP.TradeoffFunction

namespace Mf
namespace DP

noncomputable section

open MeasureTheory ProbabilityTheory

/-!
Gaussian differential privacy bridge.

This module packages the scalar Gaussian tradeoff/profile object that appears
throughout the local `mu-dp` theory and connects it to the existing
Gaussian-profile theorems already formalized in `GaussianCore`.

Literature anchors:
- `paper/theory/mu-dp/fDP/GDP.tex`
- `paper/theory/mu-dp/CLT/composition.tex`
- `paper/theory/gaussian-analysis/arxiv.tex`
-/

/-- Named theorem-facing GDP object. -/
structure GaussianDP where
  μ : ℝ

namespace GaussianDP

/-- Privacy-profile view of the GDP object. -/
def profile (G : GaussianDP) : PrivacyProfile :=
  ⟨gdpProfile G.μ⟩

/--
Squared-parameter sum for a heterogeneous finite family of GDP parameters.

This is the exact `sqrt (∑ i, μ_i^2)` composition parameter recorded in the GDP
literature. The repository does not yet prove the full generic composition
theorem transporting coordinate GDP inputs to the exact `PLDPair.compFamily`
comparison surface; this helper packages the target parameter cleanly for that
later theorem.
-/
def compFamilyMuSq {n : ℕ} (μ : Fin n → ℝ) : ℝ :=
  ∑ i, (μ i) ^ 2

/--
Theorem-facing heterogeneous GDP family object with the literature-backed
`sqrt (∑ i, μ_i^2)` parameter.

Current honest boundary:
- this packages the canonical composed GDP candidate from the literature,
- the repository now has an exact lower tradeoff-side composition surface in
  `TradeoffCompositionSurface.lean`,
- but the generic theorem proving that a coordinate GDP family composes to this
  object has not yet landed in the Lean DP layer,
- and the repository still has no abstract tensor-product operator on
  represented tradeoff functions exposing the GDP composition theorem directly
  at the `f`-DP layer.
-/
def compFamily {n : ℕ} (μ : Fin n → ℝ) : GaussianDP :=
  ⟨Real.sqrt (compFamilyMuSq μ)⟩

@[simp] theorem compFamily_muSq {n : ℕ} (μ : Fin n → ℝ) :
    compFamilyMuSq μ = ∑ i, (μ i) ^ 2 := rfl

@[simp] theorem compFamily_mu {n : ℕ} (μ : Fin n → ℝ) :
    (compFamily μ).μ = Real.sqrt (compFamilyMuSq μ) := rfl

theorem compFamilyMuSq_nonneg {n : ℕ} (μ : Fin n → ℝ) :
    0 ≤ compFamilyMuSq μ := by
  exact Finset.sum_nonneg (fun i _ => sq_nonneg (μ i))

/--
Theorem-facing privacy-profile view of the canonical heterogeneous GDP
composition candidate.

This is the strongest exact reusable GDP-layer profile surface currently
available before the missing tensor-product composition theorem lands.
-/
def compFamilyProfile {n : ℕ} (μ : Fin n → ℝ) : PrivacyProfile :=
  (compFamily μ).profile

@[simp] theorem compFamilyProfile_eval {n : ℕ} (μ : Fin n → ℝ) (ε : ℝ) :
    (compFamilyProfile μ).eval ε =
      gdpProfile (Real.sqrt (compFamilyMuSq μ)) ε := by
  simp [compFamilyProfile, profile, compFamily]

/-- Privacy-object view of the GDP object. -/
def toPrivacyObject (G : GaussianDP) : PrivacyObject :=
  PrivacyObject.ofProfile (gdpProfile G.μ)

/-- Tradeoff-function view extracted from the GDP profile at fixed `ε`. -/
def tradeoffAt (G : GaussianDP) (ε : ℝ) : TradeoffFunction :=
  (G.toPrivacyObject).tradeoffAt ε

/--
Theorem-facing tradeoff witness extracted from the canonical heterogeneous GDP
composition candidate at fixed `ε`.

Current honest boundary:
- this packages the exact GDP-layer target that the literature says the
  heterogeneous composition theorem should realize,
- but it is not yet backed by a generic theorem deriving it from coordinate GDP
  inputs.
-/
def compFamilyTradeoffAt {n : ℕ} (μ : Fin n → ℝ) (ε : ℝ) : TradeoffFunction :=
  (compFamily μ).tradeoffAt ε

@[simp] theorem compFamilyTradeoffAt_eval {n : ℕ} (μ : Fin n → ℝ) (ε α : ℝ) :
    (compFamilyTradeoffAt μ ε).eval α =
      1 - gdpProfile (Real.sqrt (compFamilyMuSq μ)) ε - Real.exp ε * α := by
  simp [compFamilyTradeoffAt, tradeoffAt, toPrivacyObject, compFamily]

@[simp] theorem profile_eval (G : GaussianDP) (ε : ℝ) :
    G.profile.eval ε = gdpProfile G.μ ε := rfl

@[simp] theorem toPrivacyObject_profile_eval (G : GaussianDP) (ε : ℝ) :
    G.toPrivacyObject.profile.eval ε = gdpProfile G.μ ε := rfl

@[simp] theorem tradeoffAt_eval (G : GaussianDP) (ε α : ℝ) :
    (G.tradeoffAt ε).eval α = 1 - gdpProfile G.μ ε - Real.exp ε * α := by
  rfl

end GaussianDP

@[simp] theorem gdpProfile_eq
    (μ ε : ℝ) :
    gdpProfile μ ε
      = stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
          - Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε) := by
  simp [gdpProfile, analyticGaussianExpr, privacyLossArgPlus, privacyLossArgMinus,
    gdpProfileCDFPlusArg, gdpProfileCDFMinusArg]

private theorem gaussianPDFReal_zero_mul_exp_tilt
    (variance x : ℝ)
    (hvariance : 0 < variance) :
    gaussianPDFReal 0 (show NNReal from ⟨variance, hvariance.le⟩) x *
        Real.exp (x - variance / 2) =
      gaussianPDFReal variance (show NNReal from ⟨variance, hvariance.le⟩) x := by
  rw [gaussianPDFReal_def, gaussianPDFReal_def]
  rw [mul_assoc, ← Real.exp_add]
  congr 1
  congr 1
  change -(x - 0) ^ 2 / (2 * variance) + (x - variance / 2) =
    -(x - variance) ^ 2 / (2 * variance)
  field_simp [hvariance.ne']
  ring

private theorem reverseGaussianHinge_eq_indicator
    (variance epsilon x : ℝ) :
    max (1 - Real.exp epsilon * Real.exp (x - variance / 2)) 0 =
      Set.indicator (Set.Iic (variance / 2 - epsilon))
        (fun y : ℝ =>
          1 - Real.exp epsilon * Real.exp (y - variance / 2)) x := by
  by_cases hx : x ≤ variance / 2 - epsilon
  · simp only [Set.indicator_apply, Set.mem_Iic, hx, if_pos]
    rw [max_eq_left]
    have hexp :
        Real.exp epsilon * Real.exp (x - variance / 2) ≤ 1 := by
      rw [← Real.exp_add, ← Real.exp_zero]
      exact Real.exp_le_exp.mpr (by linarith)
    linarith
  · simp only [Set.indicator_apply, Set.mem_Iic, hx, if_false]
    rw [max_eq_right]
    have hexp :
        1 ≤ Real.exp epsilon * Real.exp (x - variance / 2) := by
      rw [← Real.exp_add, ← Real.exp_zero]
      exact Real.exp_le_exp.mpr (by linarith)
    linarith

private theorem gaussianReal_eq_centered_withDensity_exp_tilt
    (variance : ℝ)
    (hvariance : 0 < variance) :
    gaussianReal variance ⟨variance, hvariance.le⟩ =
      (gaussianReal 0 ⟨variance, hvariance.le⟩).withDensity
        (fun x => ENNReal.ofReal (Real.exp (x - variance / 2))) := by
  let v : NNReal := ⟨variance, hvariance.le⟩
  have hv : v ≠ 0 := by
    intro hv
    have hzero : (v : ℝ) = 0 := by rw [hv]; rfl
    change variance = 0 at hzero
    exact hvariance.ne' hzero
  rw [gaussianReal_of_var_ne_zero variance hv,
    gaussianReal_of_var_ne_zero 0 hv]
  rw [← MeasureTheory.withDensity_mul volume (measurable_gaussianPDF 0 v)]
  · congr 1
    funext x
    unfold gaussianPDF
    rw [Pi.mul_apply, ← ENNReal.ofReal_mul (gaussianPDFReal_nonneg 0 v x)]
    congr 1
    simpa [v] using
      (gaussianPDFReal_zero_mul_exp_tilt variance x hvariance).symm
  · exact Measurable.ennreal_ofReal (by fun_prop)

private theorem integral_exp_tilt_Iic_eq_shifted_real
    (variance epsilon : ℝ)
    (hvariance : 0 < variance) :
    (∫ x in Set.Iic (variance / 2 - epsilon),
        Real.exp (x - variance / 2)
          ∂gaussianReal 0 ⟨variance, hvariance.le⟩) =
      (gaussianReal variance ⟨variance, hvariance.le⟩).real
        (Set.Iic (variance / 2 - epsilon)) := by
  let q : Measure ℝ := gaussianReal 0 ⟨variance, hvariance.le⟩
  let p : Measure ℝ := gaussianReal variance ⟨variance, hvariance.le⟩
  let f : ℝ → ENNReal :=
    fun x => ENNReal.ofReal (Real.exp (x - variance / 2))
  let A : Set ℝ := Set.Iic (variance / 2 - epsilon)
  have hA : MeasurableSet A := measurableSet_Iic
  have hf : Measurable f := by
    exact Measurable.ennreal_ofReal (by fun_prop)
  have hmeasure : p = q.withDensity f := by
    simpa [p, q, f] using
      gaussianReal_eq_centered_withDensity_exp_tilt variance hvariance
  calc
    (∫ x in A, Real.exp (x - variance / 2) ∂q) =
        ∫ x, A.indicator (fun y => Real.exp (y - variance / 2)) x ∂q := by
          rw [MeasureTheory.integral_indicator hA]
    _ = ∫ x, A.indicator (fun _ => (1 : ℝ)) x ∂(q.withDensity f) := by
      rw [integral_withDensity_eq_integral_toReal_smul hf]
      · apply MeasureTheory.integral_congr_ae
        filter_upwards with x
        by_cases hx : x ∈ A
        · simp only [Set.indicator_of_mem hx]
          rw [ENNReal.toReal_ofReal (Real.exp_pos _).le]
          simp [smul_eq_mul]
        · simp [Set.indicator_of_notMem hx]
      · exact Filter.Eventually.of_forall fun x => by simp [f]
    _ = ∫ x, A.indicator (fun _ => (1 : ℝ)) x ∂p := by rw [← hmeasure]
    _ = p.real A := by
      rw [MeasureTheory.integral_indicator hA]
      simp [MeasureTheory.Measure.real]

/--
The reverse positive-part expectation of a one-dimensional centered Gaussian
exponential tilt is exactly the scalar GDP profile.  The strict variance
hypothesis excludes the singular zero-variance boundary, where the analytic
formula defining `gdpProfile` uses division by its first argument.
-/
theorem scalarGaussianReversePositivePartIntegral_eq_gdpProfile
    (variance epsilon : ℝ)
    (hvariance : 0 < variance) :
    (∫ x,
      max (1 - Real.exp epsilon * Real.exp (x - variance / 2)) 0
        ∂gaussianReal 0 ⟨variance, hvariance.le⟩) =
      gdpProfile (Real.sqrt variance) epsilon := by
  let q : Measure ℝ := gaussianReal 0 ⟨variance, hvariance.le⟩
  let p : Measure ℝ :=
    gaussianReal variance ⟨variance, hvariance.le⟩
  letI : IsProbabilityMeasure q := by
    change IsProbabilityMeasure
      (gaussianReal 0 (show NNReal from ⟨variance, hvariance.le⟩))
    infer_instance
  letI : IsFiniteMeasure q := inferInstance
  let A : Set ℝ := Set.Iic (variance / 2 - epsilon)
  have hA : MeasurableSet A := measurableSet_Iic
  have hconst : Integrable (fun _ : ℝ => (1 : ℝ)) (q.restrict A) :=
    integrable_const 1
  have hweighted :
      Integrable
        (fun x : ℝ =>
          Real.exp epsilon * Real.exp (x - variance / 2))
        (q.restrict A) := by
    have hbase :=
      ProbabilityTheory.integrable_exp_mul_gaussianReal
        (μ := 0) (v := ⟨variance, hvariance.le⟩) 1
    have hmul := hbase.const_mul (Real.exp (epsilon - variance / 2))
    have hfull :
        Integrable
          (fun x : ℝ =>
            Real.exp epsilon * Real.exp (x - variance / 2)) q := by
      convert hmul using 1
      funext x
      rw [← Real.exp_add, ← Real.exp_add]
      congr 1
      ring
    exact hfull.restrict
  have hsplit :
    (∫ x,
        max (1 - Real.exp epsilon * Real.exp (x - variance / 2)) 0 ∂q) =
        q.real A - Real.exp epsilon * p.real A := by
    dsimp [q, p, A]
    rw [show
        (fun x : ℝ =>
          max (1 - Real.exp epsilon * Real.exp (x - variance / 2)) 0) =
        A.indicator
          (fun x =>
            1 - Real.exp epsilon * Real.exp (x - variance / 2)) by
      funext x
      exact reverseGaussianHinge_eq_indicator variance epsilon x]
    rw [MeasureTheory.integral_indicator hA]
    rw [MeasureTheory.integral_sub hconst hweighted]
    rw [MeasureTheory.integral_const, MeasureTheory.integral_const_mul]
    rw [integral_exp_tilt_Iic_eq_shifted_real variance epsilon hvariance]
    simp [q, p, A, MeasureTheory.Measure.real]
  rw [hsplit]
  let standardDeviation : ℝ := Real.sqrt variance
  have hstandardDeviation : 0 < standardDeviation :=
    Real.sqrt_pos.2 hvariance
  have hstandardDeviation_sq : standardDeviation ^ 2 = variance :=
    Real.sq_sqrt hvariance.le
  have hv :
      (⟨variance, hvariance.le⟩ : NNReal) =
        ⟨standardDeviation ^ 2, sq_nonneg standardDeviation⟩ := by
    apply NNReal.eq
    exact hstandardDeviation_sq.symm
  have hq := gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
    0 standardDeviation (variance / 2 - epsilon) hstandardDeviation
  have hp := gaussianReal_apply_Iic_eq_stdNormalMeasure_affine
    variance standardDeviation (variance / 2 - epsilon)
      hstandardDeviation
  have hqReal := congrArg ENNReal.toReal hq
  have hpReal := congrArg ENNReal.toReal hp
  have hplus :
      ((variance / 2 - epsilon - 0) / standardDeviation) =
        standardDeviation / 2 - epsilon / standardDeviation := by
    rw [← hstandardDeviation_sq]
    field_simp [hstandardDeviation.ne']
    ring
  have hminus :
      ((variance / 2 - epsilon - variance) / standardDeviation) =
        -standardDeviation / 2 - epsilon / standardDeviation := by
    rw [← hstandardDeviation_sq]
    field_simp [hstandardDeviation.ne']
    ring
  rw [gdpProfile_eq]
  change q.real A - Real.exp epsilon * p.real A =
    stdNormalCDFReal
        (standardDeviation / 2 - epsilon / standardDeviation) -
      Real.exp epsilon *
        stdNormalCDFReal
          (-standardDeviation / 2 - epsilon / standardDeviation)
  have hqReal' :
      q.real A =
        stdNormalMeasure.real
          (Set.Iic
            (standardDeviation / 2 - epsilon / standardDeviation)) := by
    rw [hplus] at hqReal
    simpa [q, A, hv, MeasureTheory.Measure.real] using hqReal
  have hpReal' :
      p.real A =
        stdNormalMeasure.real
          (Set.Iic
            (-standardDeviation / 2 - epsilon / standardDeviation)) := by
    rw [hminus] at hpReal
    simpa [p, A, hv, MeasureTheory.Measure.real] using hpReal
  rw [hqReal', hpReal', stdNormalCDFReal_eq_real_measure_Iic,
    stdNormalCDFReal_eq_real_measure_Iic]

/--
Theorem-facing scalar GDP/CDF interval evidence.

This is an import seam for external or future formal normal-CDF interval
arithmetic.  It does not prove numerical CDF bounds; it records the two CDF
inequalities and the final interval aggregation needed to upper-bound the GDP
profile.
-/
structure GDPProfileCDFIntervalEvidenceAt (μ ε upper : ℝ) where
  cdfPlusUpper : ℝ
  cdfMinusLower : ℝ
  cdfPlus_le_upper :
    stdNormalCDFReal (gdpProfileCDFPlusArg μ ε) ≤ cdfPlusUpper
  cdfMinus_lower_le :
    cdfMinusLower ≤ stdNormalCDFReal (gdpProfileCDFMinusArg μ ε)
  aggregate_le_upper :
    cdfPlusUpper - Real.exp ε * cdfMinusLower ≤ upper

namespace GDPProfileCDFIntervalEvidenceAt

/-- A scalar CDF interval row upper-bounds the GDP profile. -/
theorem gdpProfile_le
    {μ ε upper : ℝ}
    (row : GDPProfileCDFIntervalEvidenceAt μ ε upper) :
    gdpProfile μ ε ≤ upper := by
  rw [gdpProfile_eq]
  have hexp_nonneg : 0 ≤ Real.exp ε := le_of_lt (Real.exp_pos ε)
  have hminus :
      -(Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε))
        ≤ -(Real.exp ε * row.cdfMinusLower) := by
    exact neg_le_neg (mul_le_mul_of_nonneg_left row.cdfMinus_lower_le hexp_nonneg)
  have hsum :
      stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
          + -(Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε))
        ≤ row.cdfPlusUpper + -(Real.exp ε * row.cdfMinusLower) :=
    add_le_add row.cdfPlus_le_upper hminus
  calc
    stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
        - Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε)
        =
      stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
        + -(Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε)) := by ring
    _ ≤ row.cdfPlusUpper + -(Real.exp ε * row.cdfMinusLower) := hsum
    _ = row.cdfPlusUpper - Real.exp ε * row.cdfMinusLower := by ring
    _ ≤ upper := row.aggregate_le_upper

end GDPProfileCDFIntervalEvidenceAt

/--
GDP profile upper bound from CDF interval rows and a lower bound on
`exp ε`.

The orientation is important: the second CDF term is subtracted, so replacing
`exp ε` by a smaller certified value gives a larger upper envelope.
-/
theorem gdpProfile_le_of_cdf_bounds_expLower
    {μ ε cdfPlusUpper cdfMinusLower expLower upper : ℝ}
    (hplus :
      stdNormalCDFReal (gdpProfileCDFPlusArg μ ε) ≤ cdfPlusUpper)
    (hminus :
      cdfMinusLower ≤ stdNormalCDFReal (gdpProfileCDFMinusArg μ ε))
    (hminus_nonneg : 0 ≤ cdfMinusLower)
    (hexp_lower : expLower ≤ Real.exp ε)
    (haggregate : cdfPlusUpper - expLower * cdfMinusLower ≤ upper) :
    gdpProfile μ ε ≤ upper := by
  rw [gdpProfile_eq]
  have hexp_nonneg : 0 ≤ Real.exp ε := le_of_lt (Real.exp_pos ε)
  have hminus_term :
      -(Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε))
        ≤ -(Real.exp ε * cdfMinusLower) := by
    exact neg_le_neg (mul_le_mul_of_nonneg_left hminus hexp_nonneg)
  have hExpMul : expLower * cdfMinusLower ≤ Real.exp ε * cdfMinusLower :=
    mul_le_mul_of_nonneg_right hexp_lower hminus_nonneg
  have hExpTerm :
      -(Real.exp ε * cdfMinusLower) ≤ -(expLower * cdfMinusLower) := by
    exact neg_le_neg hExpMul
  have hsum :
      stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
          + -(Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε))
        ≤ cdfPlusUpper + -(expLower * cdfMinusLower) :=
    le_trans (add_le_add hplus hminus_term)
      (by
        simpa [add_comm, add_left_comm, add_assoc] using
          add_le_add_left hExpTerm cdfPlusUpper)
  calc
    stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
        - Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε)
        =
      stdNormalCDFReal (gdpProfileCDFPlusArg μ ε)
        + -(Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε)) := by ring
    _ ≤ cdfPlusUpper + -(expLower * cdfMinusLower) := hsum
    _ = cdfPlusUpper - expLower * cdfMinusLower := by ring
    _ ≤ upper := haggregate

/-- Lower-bound transport from a log-domain row into the `exp ε` coefficient. -/
theorem expLower_le_exp_of_log_le
    {expLower ε : ℝ}
    (hpos : 0 < expLower)
    (hlog : Real.log expLower ≤ ε) :
    expLower ≤ Real.exp ε := by
  calc
    expLower = Real.exp (Real.log expLower) := by
      exact (Real.exp_log hpos).symm
    _ ≤ Real.exp ε := Real.exp_le_exp.mpr hlog

/--
GDP profile upper bound from CDF interval rows and a log-domain lower bound on
the exponential coefficient.
-/
theorem gdpProfile_le_of_cdf_bounds_expLogLower
    {μ ε cdfPlusUpper cdfMinusLower expLower upper : ℝ}
    (hplus :
      stdNormalCDFReal (gdpProfileCDFPlusArg μ ε) ≤ cdfPlusUpper)
    (hminus :
      cdfMinusLower ≤ stdNormalCDFReal (gdpProfileCDFMinusArg μ ε))
    (hminus_nonneg : 0 ≤ cdfMinusLower)
    (hexp_pos : 0 < expLower)
    (hlog : Real.log expLower ≤ ε)
    (haggregate : cdfPlusUpper - expLower * cdfMinusLower ≤ upper) :
    gdpProfile μ ε ≤ upper :=
  gdpProfile_le_of_cdf_bounds_expLower hplus hminus hminus_nonneg
    (expLower_le_exp_of_log_le hexp_pos hlog) haggregate

/--
Theorem-facing scalar GDP/CDF row using a certified lower bound on `exp ε`.

This is the proof-carrying shape for sharp generated rows whose arithmetic is
performed with an outward lower enclosure of the exponential coefficient.  The
orientation is deliberate: the exponential term is subtracted in the GDP
profile formula, so `expLower ≤ exp ε` is the safe coefficient direction.
-/
structure GDPProfileCDFExpLowerEvidenceAt (μ ε upper : ℝ) where
  cdfPlusUpper : ℝ
  cdfMinusLower : ℝ
  expLower : ℝ
  cdfPlus_le_upper :
    stdNormalCDFReal (gdpProfileCDFPlusArg μ ε) ≤ cdfPlusUpper
  cdfMinus_lower_le :
    cdfMinusLower ≤ stdNormalCDFReal (gdpProfileCDFMinusArg μ ε)
  cdfMinusLower_nonneg : 0 ≤ cdfMinusLower
  expLower_le_exp : expLower ≤ Real.exp ε
  aggregate_le_upper :
    cdfPlusUpper - expLower * cdfMinusLower ≤ upper

namespace GDPProfileCDFExpLowerEvidenceAt

/-- An exp-lower scalar CDF interval row upper-bounds the GDP profile. -/
theorem gdpProfile_le
    {μ ε upper : ℝ}
    (row : GDPProfileCDFExpLowerEvidenceAt μ ε upper) :
    gdpProfile μ ε ≤ upper :=
  gdpProfile_le_of_cdf_bounds_expLower row.cdfPlus_le_upper
    row.cdfMinus_lower_le row.cdfMinusLower_nonneg row.expLower_le_exp
    row.aggregate_le_upper

end GDPProfileCDFExpLowerEvidenceAt

/--
Theorem-facing scalar GDP profile upper evidence.

This is the generic scalar-row seam for count-bucket certificates.  It hides
how the scalar row was proved: interval CDF evidence, exp-lower CDF evidence,
zero-signal rows, Mills rows, and future checker-dispatched row classes all
only need to supply the mathematical fact `gdpProfile μ ε ≤ upper`.
-/
structure GDPProfileUpperEvidenceAt (μ ε upper : ℝ) where
  profile_le : gdpProfile μ ε ≤ upper

namespace GDPProfileUpperEvidenceAt

/-- Package exact scalar GDP profile upper evidence from any proof. -/
def ofProfileLe
    {μ ε upper : ℝ}
    (h : gdpProfile μ ε ≤ upper) :
    GDPProfileUpperEvidenceAt μ ε upper where
  profile_le := h

/-- Interval-CDF rows are scalar GDP profile upper evidence. -/
def ofInterval
    {μ ε upper : ℝ}
    (row : GDPProfileCDFIntervalEvidenceAt μ ε upper) :
    GDPProfileUpperEvidenceAt μ ε upper where
  profile_le := row.gdpProfile_le

/-- Exp-lower CDF rows are scalar GDP profile upper evidence. -/
def ofExpLower
    {μ ε upper : ℝ}
    (row : GDPProfileCDFExpLowerEvidenceAt μ ε upper) :
    GDPProfileUpperEvidenceAt μ ε upper where
  profile_le := row.gdpProfile_le

/--
Aggregate transport for scalar rows whose CDF bounds are proved through
separate certified product intervals.

If `plusProduct` is a certified upper-bound expression for the plus CDF,
`minusProduct` is a certified lower-bound expression for the minus CDF, and a
numeric backend proves wider theorem-facing bounds `plusUpper` and
`minusLower`, then it is enough to prove the aggregate inequality using those
wider bounds.  This isolates the numeric PDF/product interval backend from the
GDP algebra.
-/
theorem aggregate_le_of_product_interval_bounds
    {plusProduct minusProduct plusUpper minusLower expLower upper : ℝ}
    (hplus : plusProduct ≤ plusUpper)
    (hminus : minusLower ≤ minusProduct)
    (hexpLower_nonneg : 0 ≤ expLower)
    (haggregate : plusUpper - expLower * minusLower ≤ upper) :
    plusProduct - expLower * minusProduct ≤ upper := by
  have hmul :
      expLower * minusLower ≤ expLower * minusProduct :=
    mul_le_mul_of_nonneg_left hminus hexpLower_nonneg
  have hsum :
      plusProduct + -(expLower * minusProduct)
        ≤ plusUpper + -(expLower * minusLower) :=
    add_le_add hplus (neg_le_neg hmul)
  have htarget :
      plusProduct - expLower * minusProduct
        ≤ plusUpper - expLower * minusLower := by
    linarith
  exact le_trans htarget haggregate

end GDPProfileUpperEvidenceAt

/--
Fully Lean-owned conservative scalar CDF interval row.

This is the proof-carrying fallback row used when no sharp CDF interval row has
been formalized yet: the plus CDF is bounded by `1`, the minus CDF is bounded
below by `0`, and the aggregate upper is therefore `1`.
-/
def conservativeGDPProfileCDFIntervalEvidenceAt
    (μ ε : ℝ) :
    GDPProfileCDFIntervalEvidenceAt μ ε 1 where
  cdfPlusUpper := 1
  cdfMinusLower := 0
  cdfPlus_le_upper := stdNormalCDFReal_le_one _
  cdfMinus_lower_le := stdNormalCDFReal_nonneg _
  aggregate_le_upper := by
    simp

/-- Soundness of the conservative proof-carrying scalar CDF interval row. -/
theorem conservativeGDPProfileCDFIntervalEvidenceAt_gdpProfile_le
    (μ ε : ℝ) :
    gdpProfile μ ε ≤ 1 :=
  (conservativeGDPProfileCDFIntervalEvidenceAt μ ε).gdpProfile_le

/--
Conservative scalar fallback: every GDP profile value is at most `1`.

This uses only the elementary CDF range facts already available in
`GaussianCore`.  It is intentionally loose, but it gives count-bucket
certificates a fully formal emergency route when no audited numerical CDF
interval row is available.
-/
theorem gdpProfile_le_one (μ ε : ℝ) :
    gdpProfile μ ε ≤ 1 := by
  rw [gdpProfile_eq]
  have hplus : stdNormalCDFReal (gdpProfileCDFPlusArg μ ε) ≤ 1 :=
    stdNormalCDFReal_le_one _
  have hminus_nonneg :
      0 ≤ Real.exp ε * stdNormalCDFReal (gdpProfileCDFMinusArg μ ε) :=
    mul_nonneg (le_of_lt (Real.exp_pos ε))
      (stdNormalCDFReal_nonneg _)
  linarith

/--
Zero signal has nonpositive GDP profile at nonnegative privacy parameter.

This is the sharp theorem-facing scalar row used by count-bucket certificates
for buckets whose signal-to-noise upper is exactly zero.  It avoids routing
those rows through imported CDF arithmetic.
-/
theorem gdpProfile_zero_le_zero_of_nonneg_epsilon
    {ε : ℝ}
    (hε : 0 ≤ ε) :
    gdpProfile 0 ε ≤ 0 := by
  rw [gdpProfile_eq]
  simp only [gdpProfileCDFPlusArg, gdpProfileCDFMinusArg, zero_div, div_zero,
    neg_zero, sub_zero]
  have hcdf_nonneg : 0 ≤ stdNormalCDFReal 0 := stdNormalCDFReal_nonneg 0
  have hexp_ge : 1 ≤ Real.exp ε := Real.one_le_exp hε
  have hmul : stdNormalCDFReal 0 ≤ Real.exp ε * stdNormalCDFReal 0 :=
    by simpa [one_mul] using mul_le_mul_of_nonneg_right hexp_ge hcdf_nonneg
  linarith

/--
Zero-signal GDP rows inherit any nonnegative upper.

This is the proof-facing surface for generated mixed-authority count-bucket
rows with `signal_to_noise_upper = 0`.
-/
theorem gdpProfile_zero_le_of_nonneg_epsilon_of_nonneg_upper
    {ε upper : ℝ}
    (hε : 0 ≤ ε)
    (hupper : 0 ≤ upper) :
    gdpProfile 0 ε ≤ upper :=
  le_trans (gdpProfile_zero_le_zero_of_nonneg_epsilon hε) hupper

namespace GDPProfileUpperEvidenceAt

/--
Package deterministic scalar GDP profile evidence as the generic imported-row
facade.

The imported row's target cutoff is the same `upper` carried by the scalar
evidence, so `upper_le_target` is reflexive.  Metadata strings are audit labels
only; theorem authority is exactly `row.profile_le`.
-/
def toImportedCertificateRowAt
    {μ ε upper : ℝ}
    (row : GDPProfileUpperEvidenceAt μ ε upper)
    (routeKind routeTarget certificateKind : String) :
    ImportedCertificateRowAt (gdpProfile μ ε) upper where
  routeKind := routeKind
  routeTarget := routeTarget
  certificateKind := certificateKind
  upper := upper
  upper_valid := row.profile_le
  upper_le_target := le_rfl

/-- Zero-signal rows are scalar GDP profile upper evidence for any nonnegative upper. -/
def ofZeroSignal
    {ε upper : ℝ}
    (hε : 0 ≤ ε)
    (hupper : 0 ≤ upper) :
    GDPProfileUpperEvidenceAt 0 ε upper where
  profile_le := gdpProfile_zero_le_of_nonneg_epsilon_of_nonneg_upper hε hupper

/-- Conservative fallback as generic scalar GDP profile upper evidence. -/
def conservative
    (μ ε : ℝ) :
    GDPProfileUpperEvidenceAt μ ε 1 where
  profile_le := gdpProfile_le_one μ ε

end GDPProfileUpperEvidenceAt

/--
For nonzero `μ`, the GDP profile is the `GaussianCore.bridgeProfile` at
`μ / 2`.  This exposes the derivative/monotonicity facts already proved in
`GaussianCore` without changing the public `gdpProfile` definition.
-/
theorem gdpProfile_eq_bridgeProfile_of_ne
    {μ ε : ℝ}
    (hμ : μ ≠ 0) :
    gdpProfile μ ε = bridgeProfile (μ / 2) ε := by
  have hU : μ / 2 - ε / μ = bridgeU (μ / 2) ε := by
    unfold bridgeU FiniteGaussianPrivacy.bridgeU
    field_simp [hμ]
  have hV : -μ / 2 - ε / μ = bridgeV (μ / 2) ε := by
    unfold bridgeV FiniteGaussianPrivacy.bridgeV
    field_simp [hμ]
  rw [gdpProfile_eq, bridgeProfile, FiniteGaussianPrivacy.bridgeProfile]
  simp [gdpProfileCDFPlusArg, gdpProfileCDFMinusArg, hU, hV]

/--
Monotone transport for imported/rounded scalar GDP rows.

If a producer proves/imports `gdpProfile μUpper ε ≤ δ` and the exact parameter
`μ` is nonnegative and bounded by `μUpper`, then the exact parameter inherits
the same GDP upper.  The `μ = 0` branch is discharged from the explicit GDP
formula and `0 ≤ ε`; positive `μ` uses `gdpProfile_monoOn_pos`.
-/
theorem gdpProfile_le_of_nonneg_of_le
    {μ μUpper ε δ : ℝ}
    (hε : 0 ≤ ε)
    (hμ0 : 0 ≤ μ)
    (hμ_le : μ ≤ μUpper)
    (hδ0 : 0 ≤ δ)
    (hUpper : gdpProfile μUpper ε ≤ δ) :
    gdpProfile μ ε ≤ δ := by
  by_cases hμpos : 0 < μ
  · have hUpperPos : 0 < μUpper := lt_of_lt_of_le hμpos hμ_le
    exact le_trans ((gdpProfile_monoOn_pos ε) hμpos hUpperPos hμ_le) hUpper
  · have hμle0 : μ ≤ 0 := le_of_not_gt hμpos
    have hμeq : μ = 0 := le_antisymm hμle0 hμ0
    subst μ
    exact gdpProfile_zero_le_of_nonneg_epsilon_of_nonneg_upper hε hδ0

theorem gdpProfile_eq_analyticGaussianExpr_div
    {Δ σ : ℝ}
    (hσ : 0 < σ) :
    gdpProfile (Δ / σ) = analyticGaussianExpr Δ σ := by
  funext ε
  by_cases hΔ : Δ = 0
  · subst hΔ
    simp [gdpProfile, analyticGaussianExpr, privacyLossArgPlus, privacyLossArgMinus]
  · have hσne : σ ≠ 0 := hσ.ne'
    have hΔne : Δ ≠ 0 := hΔ
    simp only [gdpProfile, analyticGaussianExpr, privacyLossArgPlus, privacyLossArgMinus]
    congr 1
    · field_simp [hσne, hΔne]
    · congr 1
      field_simp [hσne, hΔne]

theorem analyticGaussianCondition_iff_gdpProfile_le
    {Δ σ ε δ : ℝ}
    (hσ : 0 < σ) :
    analyticGaussianCondition Δ σ ε δ ↔ gdpProfile (Δ / σ) ε ≤ δ := by
  rw [analyticGaussianCondition_iff]
  rw [← congrArg (fun f => f ε) (gdpProfile_eq_analyticGaussianExpr_div hσ)]

theorem gaussianCore_approxDP_of_gdpProfile_le
    {X : Type} {n : ℕ}
    (adj : X → X → Prop)
    (mean : X → BSROutput n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    BSRMeanL2SensitivityGoal adj mean Δ →
    gdpProfile (Δ / σ) ε ≤ δ →
    ApproxDP adj (bsrOneStepMeasure mean σ) ε δ := by
  intro hσ hε hΔ hSens hGDP
  refine gaussianCore_approxDP_of_analyticCondition adj mean Δ σ ε δ hσ hε hΔ hSens ?_
  exact (analyticGaussianCondition_iff_gdpProfile_le hσ).2 hGDP

end
end DP
end Mf
