import Mf.Optimization.PoissonClippedSGD.PrivateConvergence
import Mf.Optimization.SDE.DPAdamFixedBetaFirstPrinciplesExactPrivacyCalibration

/-!
# Public finite calibration retaining sampling amplification

The finite small-step bound from `PoissonSampledGaussianRenyiSmallStep` and the
exact factorial-moment identity reused from the existing finite calibration
owner give rho_m <= m q²/nu² when nu² >= m(m-1)/2. The explicit variance floor
discharges that condition. The smaller of this valid calibration and the full
Gaussian fallback remains valid for both privacy directions at every q in (0,1].
The rule depends only on public q,T,epsilon,delta and is distinct from raw GDP.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory SDE
noncomputable section

/-- The finite small-step estimate retains the sampling-rate square. Its
validity domain is produced by the squared-noise floor below. -/
theorem sampledGaussianSharpStepRho_le_amplified
    (order : ℕ) (q : NNReal) (hq : q ≤ 1) (nu : ℝ)
    (hm : 2 ≤ order) (hnu : 0 < nu)
    (hfloor : (order : ℝ) * ((order : ℝ) - 1) / 2 ≤ nu ^ 2) :
    euclideanSampledGaussianSharpStepRho order q nu ≤
      (order : ℝ) * (q : ℝ) ^ 2 / nu ^ 2 := by
  have hadm : Mf.DP.SampledGaussianSmallStepAdmissible order 1 nu := by
    refine ⟨by norm_num, hnu, ?_⟩
    simp only [one_mul]
    apply (div_le_one₀ (by positivity : 0 < 2 * nu ^ 2)).2
    nlinarith
  have hrho := Mf.DP.sampledGaussianForwardRho_smallStep_le
    (q := (q : ℝ)) (h := 1) (kappa := nu)
    order hm q.2 (by exact_mod_cast hq) hadm
  rw [DPAdamFixedBetaFirstPrinciplesExactPrivacyCalibration.sampledGaussianSmallStepMomentRate_eq
    order (q : ℝ) nu hm, one_mul] at hrho
  have hmR : (2 : ℝ) ≤ order := by exact_mod_cast hm
  have hden : (order : ℝ) - 1 ≠ 0 := by linarith
  have hrho' : Mf.DP.sampledGaussianForwardRho order q (1 / nu ^ 2) ≤
      (order : ℝ) * (q : ℝ) ^ 2 / nu ^ 2 := by
    convert hrho using 1
    field_simp [hden]
  exact max_le (by positivity) hrho'

/-- Sum-noise variance sufficient for finite amplification, including its validity floor. -/
def amplifiedPrivacyVariance (T order : ℕ) (q epsilon : ℝ) : ℝ :=
  max (2 * q ^ 2 * ((T : ℝ) * order / epsilon))
    ((order : ℝ) * ((order : ℝ) - 1) / 2)

/-- Public smaller choice between two valid finite-calibration variances. -/
def hybridPrivacyVariance (T order : ℕ) (q epsilon : ℝ) : ℝ :=
  min ((T : ℝ) * order / epsilon) (amplifiedPrivacyVariance T order q epsilon)

/-- Finite public multiplier retaining amplification when it improves the baseline. -/
def hybridPrivacyMultiplier (T : ℕ) (q epsilon delta : ℝ) : ℝ :=
  Real.sqrt (hybridPrivacyVariance T (finitePrivacyOrder epsilon delta) q epsilon)

theorem hybridPrivacyVariance_pos {T order : ℕ} {q epsilon : ℝ}
    (hT : 0 < T) (hm : 2 ≤ order) (heps : 0 < epsilon) :
    0 < hybridPrivacyVariance T order q epsilon := by
  have hmR : (2 : ℝ) ≤ order := by exact_mod_cast hm
  have hB : 0 < (T : ℝ) * order / epsilon := by positivity
  have hsub : 0 < (order : ℝ) - 1 := by linarith
  have hF : 0 < (order : ℝ) * ((order : ℝ) - 1) / 2 := by positivity
  exact lt_min hB (lt_of_lt_of_le hF (le_max_right _ _))

theorem hybridPrivacyMultiplier_pos {T : ℕ} {q epsilon delta : ℝ}
    (hT : 0 < T) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1) :
    0 < hybridPrivacyMultiplier T q epsilon delta := by
  exact Real.sqrt_pos.2 (hybridPrivacyVariance_pos hT
    (DPAdamPublicRenyiOrderSelection.publicRenyiOrder_ge_two heps hdelta hdelt) heps)

theorem hybridPrivacyMultiplier_sq {T : ℕ} {q epsilon delta : ℝ}
    (hT : 0 < T) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1) :
    hybridPrivacyMultiplier T q epsilon delta ^ 2 =
      hybridPrivacyVariance T (finitePrivacyOrder epsilon delta) q epsilon :=
  Real.sq_sqrt (hybridPrivacyVariance_pos hT
    (DPAdamPublicRenyiOrderSelection.publicRenyiOrder_ge_two heps hdelta hdelt) heps).le

theorem hybridPrivacyVariance_le_baseline (T order : ℕ) (q epsilon : ℝ) :
    hybridPrivacyVariance T order q epsilon ≤ (T : ℝ) * order / epsilon :=
  min_le_left _ _

/-- Full sampling selects the existing conservative variance exactly. -/
theorem hybridPrivacyVariance_fullSampling (T order : ℕ) {epsilon : ℝ}
    (heps : 0 < epsilon) :
    hybridPrivacyVariance T order 1 epsilon = (T : ℝ) * order / epsilon := by
  have hB : 0 ≤ (T : ℝ) * order / epsilon := by positivity
  unfold hybridPrivacyVariance amplifiedPrivacyVariance
  apply min_eq_left
  calc
    _ ≤ 2 * (1 : ℝ) ^ 2 * ((T : ℝ) * order / epsilon) := by nlinarith
    _ ≤ _ := le_max_left _ _

/-- Exact domain of strict reduction in sum-noise variance. -/
theorem hybridPrivacyVariance_lt_baseline_iff {T order : ℕ} {q epsilon : ℝ}
    (hT : 0 < T) (hm : 2 ≤ order) (heps : 0 < epsilon) :
    hybridPrivacyVariance T order q epsilon < (T : ℝ) * order / epsilon ↔
      2 * q ^ 2 < 1 ∧ epsilon * ((order : ℝ) - 1) < 2 * T := by
  have hmR : (2 : ℝ) ≤ order := by exact_mod_cast hm
  have hm0 : (0 : ℝ) < order := by linarith
  have hB : 0 < (T : ℝ) * order / epsilon := by positivity
  simp only [hybridPrivacyVariance, amplifiedPrivacyVariance, min_lt_iff,
    lt_self_iff_false, false_or, max_lt_iff]
  constructor
  · rintro ⟨ha, hf⟩
    constructor
    · nlinarith [mul_pos hB (by positivity : 0 < 2 * q ^ 2 + 1)]
    · have h := (lt_div_iff₀ heps).mp hf
      nlinarith [mul_pos hm0 (by positivity : 0 < epsilon)]
  · rintro ⟨hq, hT'⟩
    constructor
    · nlinarith [mul_pos hB (sub_pos.mpr hq)]
    · apply (lt_div_iff₀ heps).2
      nlinarith [mul_pos hm0 (sub_pos.mpr hT')]

/-- The explicit floor and max discharge the finite amplified cost budget. -/
theorem amplifiedPrivacyVariance_cost (T order : ℕ) (q : NNReal) (hq : q ≤ 1)
    (epsilon : ℝ) (_hT : 0 < T) (hm : 2 ≤ order) (heps : 0 < epsilon) :
    (T : ℝ) * euclideanSampledGaussianSharpStepRho order q
      (Real.sqrt (amplifiedPrivacyVariance T order q epsilon)) ≤ epsilon / 2 := by
  have hmR : (2 : ℝ) ≤ order := by exact_mod_cast hm
  have hsub : 0 < (order : ℝ) - 1 := by linarith
  have hA : 0 < amplifiedPrivacyVariance T order q epsilon := by
    exact lt_of_lt_of_le (by positivity : 0 < (order : ℝ) * ((order : ℝ) - 1) / 2)
      (le_max_right _ _)
  have hnoise : (Real.sqrt (amplifiedPrivacyVariance T order q epsilon)) ^ 2 =
      amplifiedPrivacyVariance T order q epsilon := Real.sq_sqrt hA.le
  have hfloor : (order : ℝ) * ((order : ℝ) - 1) / 2 ≤
      (Real.sqrt (amplifiedPrivacyVariance T order q epsilon)) ^ 2 := by
    rw [hnoise]
    exact le_max_right _ _
  have hstep := sampledGaussianSharpStepRho_le_amplified order q hq _ hm
    (Real.sqrt_pos.2 hA) hfloor
  have hscale : 2 * (q : ℝ) ^ 2 * ((T : ℝ) * order / epsilon) ≤
      amplifiedPrivacyVariance T order q epsilon := le_max_left _ _
  have hscale' : 2 * (q : ℝ) ^ 2 * ((T : ℝ) * order) ≤
      amplifiedPrivacyVariance T order q epsilon * epsilon := by
    apply (div_le_iff₀ heps).mp
    simpa only [mul_div_assoc] using hscale
  calc
    _ ≤ (T : ℝ) * ((order : ℝ) * (q : ℝ) ^ 2 /
      (Real.sqrt (amplifiedPrivacyVariance T order q epsilon)) ^ 2) :=
      mul_le_mul_of_nonneg_left hstep (Nat.cast_nonneg _)
    _ = (T : ℝ) * ((order : ℝ) * (q : ℝ) ^ 2) /
        amplifiedPrivacyVariance T order q epsilon := by rw [hnoise]; ring
    _ ≤ epsilon / 2 := (div_le_iff₀ hA).2 (by nlinarith)

/-- Both public candidate variances pay the same finite cost, so their
smaller choice does too. No small-step premise is left to the mechanism user. -/
theorem hybridPrivacyVariance_cost (T order : ℕ) (q : NNReal) (hq : q ≤ 1)
    (epsilon : ℝ) (hT : 0 < T) (hm : 2 ≤ order) (heps : 0 < epsilon) :
    (T : ℝ) * euclideanSampledGaussianSharpStepRho order q
      (Real.sqrt (hybridPrivacyVariance T order q epsilon)) ≤ epsilon / 2 := by
  unfold hybridPrivacyVariance
  rcases le_total ((T : ℝ) * order / epsilon)
    (amplifiedPrivacyVariance T order q epsilon) with h | h
  · rw [min_eq_left h]
    have hmR : (2 : ℝ) ≤ order := by exact_mod_cast hm
    have hm0 : (0 : ℝ) < order := by linarith
    have hB : 0 < (T : ℝ) * order / epsilon := by positivity
    have hs := sampledGaussianSharpStepRho_le_fullGaussian order q hq _ hm (Real.sqrt_pos.2 hB)
    calc
      _ ≤ (T : ℝ) * ((order : ℝ) / (2 * (Real.sqrt ((T : ℝ) * order / epsilon)) ^ 2)) :=
        mul_le_mul_of_nonneg_left hs (Nat.cast_nonneg _)
      _ = epsilon / 2 := by
        rw [Real.sq_sqrt hB.le]
        field_simp [heps.ne', hm0.ne', (Nat.cast_pos.mpr hT : (0 : ℝ) < T).ne']
  · rw [min_eq_right h]
    exact amplifiedPrivacyVariance_cost T order q hq epsilon hT hm heps

private theorem hybrid_constant_adaptive_budget (rho : ℝ) :
    ∀ T, Mf.DP.adaptiveRenyiBudget (fun _ => rho) T = (T : ℝ) * rho := by
  intro T
  induction T with
  | zero => simp
  | succ T ih => simp [Mf.DP.adaptiveRenyiBudget_succ, ih, Nat.cast_add, add_mul]

namespace PrivacyData
variable {n d : ℕ}

/-- Both directions of optional-record transcript privacy at the hybrid public noise. -/
theorem hybrid_optionalTranscript_approxDP {Record : Type} (data : PrivacyData n d)
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ r, Measurable (g r)) (T : ℕ) (hT : 0 < T)
    (epsilon delta : ℝ) (heps : 0 < epsilon) (hdelta : 0 < delta) (hdelt : delta < 1)
    (hnoise : data.multiplier = hybridPrivacyMultiplier T data.q epsilon delta) :
    Mf.DP.ApproxDP OptionalRecordAdjacent (data.optionalTranscriptLaw g hg T) epsilon delta := by
  let m := finitePrivacyOrder epsilon delta
  have hm : 2 ≤ m :=
    SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder_ge_two heps hdelta hdelt
  have hden : 0 < (m : ℝ) - 1 := by
    have : (2 : ℝ) ≤ m := by exact_mod_cast hm
    linarith
  have hlane := SDE.DPAdamPublicRenyiOrderSelection.publicRenyiOrder_deltaLane_le_half
    heps hdelta hdelt
  have hbudget := hybridPrivacyVariance_cost T m data.q data.q_le_one epsilon hT hm heps
  have hcost : (T : ℝ) * SDE.euclideanSampledGaussianSharpStepRho m data.q data.multiplier +
      Real.log (1 / delta) / ((m : ℝ) - 1) ≤ epsilon := by
    rw [hnoise]
    change (T : ℝ) * SDE.euclideanSampledGaussianSharpStepRho m data.q
      (Real.sqrt (hybridPrivacyVariance T m data.q epsilon)) +
        Real.log (1 / delta) / ((m : ℝ) - 1) ≤ epsilon
    linarith
  have hdeltaLe : Real.exp (((m : ℝ) - 1) *
      (Mf.DP.adaptiveRenyiBudget
        (fun _ => SDE.euclideanSampledGaussianSharpStepRho m data.q data.multiplier) T -
          epsilon)) ≤ delta := by
    rw [hybrid_constant_adaptive_budget]
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
