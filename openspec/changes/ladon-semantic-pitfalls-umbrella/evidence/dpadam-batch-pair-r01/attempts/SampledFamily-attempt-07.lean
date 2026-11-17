import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowExactCountSchedule
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowCenteredQuadraticMean
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowNamedNonlinearLimitLaw
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowHorizonTuning
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowPrivacyReceiptAsymptotic
namespace LadonSampledFamilyAudit
open MeasureTheory Filter Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowExactCountSchedule
open DPAdamFixedBetaFastSlowQuadraticExample
open DPAdamFixedBetaFastSlowFamily
open DPAdamFixedBetaFastSlowGrowingClockMaps
noncomputable section
set_option autoImplicit false
theorem sampledQuadraticReleaseKernel_measurable (noise q : ℝ) (hq : 0 < q)
    (hq1 : q ≤ 1) (dataset : Finset (Fin 1)) :
    Measurable fun state : PrivateAdamState (Fin 1) =>
      normalizedEuclideanAveragedSampledGaussianRelease
        1 (noise * q) q (fun _ : Fin 1 => state.1) dataset
        q hq.le hq1 := by
  have hcenter : ∀ mask : Mf.DP.ParticipationTrace 1,
      Measurable fun state : PrivateAdamState (Fin 1) =>
        (euclideanClippedDatasetMixture 1
          (fun _ : Fin 1 => state.1) dataset
          q hq.le hq1).mean mask := by
    intro mask
    apply measurable_pi_lambda
    intro i
    change Measurable fun state : PrivateAdamState (Fin 1) =>
      ∑ record : Fin 1,
        if mask record then
          (if record ∈ dataset then Mf.DP.l2VectorClip 1 state.1 else 0) i
        else 0
    apply Finset.measurable_sum
    intro record _
    by_cases hm : mask record = true
    · by_cases hd : record ∈ dataset
      · have hs : Measurable
            (fun state : PrivateAdamState (Fin 1) => state.1) :=
          measurable_fst
        have hc : Measurable
            (fun state : PrivateAdamState (Fin 1) =>
              Mf.DP.l2VectorClip 1 state.1) :=
          (Mf.DP.measurable_l2VectorClip 1).comp hs
        simpa [hm, hd, Function.comp_def] using ((measurable_pi_apply i).comp hc)
      · simp [hm, hd]
    · have hf : mask record = false := Bool.eq_false_iff.mpr hm
      simp [hf]
  have hpdf :
      Measurable (Function.uncurry
        (fun state : PrivateAdamState (Fin 1) => fun y : Fin 1 → ℝ =>
          ENNReal.ofReal
            (Mf.DP.finiteMeanMixturePdfReal
              (euclideanClippedDatasetMixture 1
                (fun _ : Fin 1 => state.1) dataset
                q hq.le hq1) ((noise * q) * 1) y))) := by
    change Measurable fun z : PrivateAdamState (Fin 1) × (Fin 1 → ℝ) =>
      ENNReal.ofReal
        (Mf.DP.finiteMeanMixturePdfReal
          (euclideanClippedDatasetMixture 1
            (fun _ : Fin 1 => z.1.1) dataset
            q hq.le hq1) ((noise * q) * 1) z.2)
    apply Measurable.ennreal_ofReal
    unfold Mf.DP.finiteMeanMixturePdfReal
    apply Finset.measurable_sum
    intro mask _
    have hm : Measurable fun z : PrivateAdamState (Fin 1) × (Fin 1 → ℝ) =>
        (euclideanClippedDatasetMixture 1
          (fun _ : Fin 1 => z.1.1) dataset
          q hq.le hq1).mean mask :=
      (hcenter mask).comp measurable_fst
    have hb : Measurable fun z : PrivateAdamState (Fin 1) × (Fin 1 → ℝ) =>
        Mf.DP.bsrGaussianPdfReal ((noise * q) * 1)
          ((euclideanClippedDatasetMixture 1
            (fun _ : Fin 1 => z.1.1) dataset
            q hq.le hq1).mean mask) z.2 := by
      unfold Mf.DP.bsrGaussianPdfReal
      apply Finset.measurable_fun_prod
      intro i _
      fun_prop
    exact measurable_const.mul hb
  have hraw :
      Measurable fun state : PrivateAdamState (Fin 1) =>
        euclideanExactSampledGaussianSumRelease 1 (noise * q)
          (fun _ : Fin 1 => state.1) dataset q
          hq.le hq1 := by
    simp only [euclideanExactSampledGaussianSumRelease,
      Mf.DP.finiteMeanMixtureMeasure, Mf.DP.densityMeasure]
    exact measurable_withDensity hpdf
  unfold normalizedEuclideanAveragedSampledGaussianRelease
  exact (Measure.measurable_map (averageRelease (1 * q))
    (averageRelease_measurable (Coord := Fin 1) (1 * q))).comp hraw



def sampledFamily (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1)
    (H noise floor : ℝ) (hH : 0 < H) (hf : 0 < floor) (hn : floor ≤ noise) :
    FixedNoiseFastSlowFamily 1 1 :=
  { positiveFloorQuadraticFamily H noise floor hH hf hn with
    samplingRate := q
    samplingRate_pos := hq
    samplingRate_le_one := hq1
    effectiveBatch := q
    effectiveBatch_pos := hq
    releaseKernel_measurable := by
      intro step dataset
      exact sampledQuadraticReleaseKernel_measurable noise q hq hq1 dataset }

def sampledRegularity (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1)
    (H noise floor : ℝ) (hH : 0 < H) (hf : 0 < floor) (hn : floor ≤ noise) :
    FixedNoiseFastSlowQueryRegularity (sampledFamily q hq hq1 H noise floor hH hf hn) where
  recordConstant := fun _ => 1
  recordConstant_nonneg := by intro record hrecord; norm_num
  gradientOracle_sub_l2Norm_le := by
    intro theta theta' htheta htheta' record hrecord
    simp [sampledFamily, positiveFloorQuadraticFamily]

-- Every real q in (0,1] is supported, not merely full batch q=1.
def sampledData (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1)
    (gamma c : ℝ) (hg : 0 < gamma) (hc : 0 < c)
    (T : ℕ → ℕ) (hT : ∀ n, 0 < T n) : GrowingClockData 1 1 :=
  let original := quadraticData gamma c hg hc T hT
  { original with
    base := sampledFamily q hq hq1 _ _ _
      original.base.physicalHorizon_pos original.base.noiseFloor_pos original.base.noiseFloor_le
    baseRegularity := sampledRegularity q hq hq1 _ _ _
      original.base.physicalHorizon_pos original.base.noiseFloor_pos original.base.noiseFloor_le
    family := fun n => sampledFamily q hq hq1 _ _ _
      (original.family n).physicalHorizon_pos (original.family n).noiseFloor_pos
      (original.family n).noiseFloor_le
    regularity := fun n => sampledRegularity q hq hq1 _ _ _
      (original.family n).physicalHorizon_pos (original.family n).noiseFloor_pos
      (original.family n).noiseFloor_le
    batch_eq := by intro n; rfl
    sampling_eq := by intro n; rfl }

theorem sampledData_batch (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1)
    (gamma c : ℝ) (hg : 0 < gamma) (hc : 0 < c)
    (T : ℕ → ℕ) (hT : ∀ n, 0 < T n) :
    (sampledData q hq hq1 gamma c hg hc T hT).base.effectiveBatch =
      (sampledData q hq hq1 gamma c hg hc T hT).base.samplingRate *
        ((sampledData q hq hq1 gamma c hg hc T hT).base.dataset.card : ℝ) := by
  simp [sampledData, sampledFamily, quadraticData, positiveFloorQuadraticFamily]

theorem sampledData_eta (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1)
    (gamma c : ℝ) (hg : 0 < gamma) (hc : 0 < c)
    (T : ℕ → ℕ) (hT : ∀ n, 0 < T n) (n : ℕ) :
    (sampledData q hq hq1 gamma c hg hc T hT).eta n = c / Real.sqrt (T n : ℝ) := by
  exact quadraticData_eta_eq gamma c hg hc T hT n

#print axioms sampledData
#print axioms sampledData_batch
#print axioms sampledData_eta

open scoped Topology NNReal
open DPAdamFixedBetaFastSlowHighNoiseResponse
open DPAdamGaussianReferenceFunctionalLimit
open FiniteHorizonCovarianceBrownianPathLaw
open FiniteHorizonAdditiveLipschitzSolutionMap

variable (q : ℝ) (hq : 0 < q) (hq1 : q ≤ 1)
    (gamma c : ℝ) (hg : 0 < gamma) (hc : 0 < c)
    (T : ℕ → ℕ) (hT : ∀ n, 0 < T n) (hlim : Tendsto T atTop atTop)

theorem sampled_noise (hlim : Tendsto T atTop atTop) :
    Tendsto (sampledData q hq hq1 gamma c hg hc T hT).clock atTop atTop :=
  quadraticData_clock_tendsto gamma c hg hc T hT hlim

theorem sampled_product :
    Tendsto (fun n => (sampledData q hq hq1 gamma c hg hc T hT).eta n *
      (sampledData q hq hq1 gamma c hg hc T hT).clock n)
      atTop (𝓝 (c * Real.sqrt gamma)) :=
  quadraticData_step_noise_limit gamma c hg hc T hT

theorem sampled_mean :
    ∀ radius : ℝ, 0 ≤ radius → ∃ meanError : ℕ → ℝ,
      (∀ n, 0 ≤ meanError n) ∧ Tendsto meanError atTop (𝓝 0) ∧
      ∀ n (theta : Fin 1 → ℝ), ‖theta‖ ≤ radius →
        ‖clippedGradientMean ((sampledData q hq hq1 gamma c hg hc T hT).family n) theta -
          Mf.DP.l2VectorClip 1 theta‖ ≤ meanError n := by
  exact (sampledData q hq hq1 gamma c hg hc T hT).centered_hmeanLocal
    (sampledData_batch q hq hq1 gamma c hg hc T hT) (by intros; rfl)

theorem sampled_initial :
    Tendsto (fun n => ‖((sampledData q hq hq1 gamma c hg hc T hT).family n).thetaInitial
      ((sampledData q hq hq1 gamma c hg hc T hT).mesh n) - (fun _ => (2 : ℝ))‖)
      atTop (𝓝 0) := by
  simpa [sampledData, sampledFamily, positiveFloorQuadraticFamily] using
    (tendsto_const_nhds : Tendsto (fun _ : ℕ => (0 : ℝ)) atTop (𝓝 0))

def sampledMap :=
  let data := sampledData q hq hq1 gamma c hg hc T hT
  solutionMap data.base.physicalHorizon_pos.le
    (data.calibratedSlowDrift (Mf.DP.l2VectorClip 1))
    data.inheritedSlowDriftLipschitzConstant
    (data.calibratedSlowDrift_lipschitz_of_clippedMean
      (sampled_noise q hq hq1 gamma c hg hc T hT hlim)
      (sampledData_batch q hq hq1 gamma c hg hc T hT)
      _ (sampled_mean q hq hq1 gamma c hg hc T hT))
    (fun _ => 2)

def sampledLimitLaw : ProbabilityMeasure (ReferenceDriverPath 1 (c / Real.sqrt gamma)) :=
  let data := sampledData q hq hq1 gamma c hg hc T hT
  ProbabilityMeasure.map
    (⟨covarianceBrownianFixedPathLaw
      ((c * Real.sqrt gamma) • DPAdamFixedBetaGaussianResampling.covariance (d := 1)
        (data.base.firstPrinciplesAtMesh 0).betaSeparation)
      data.base.physicalHorizon, inferInstance⟩ :
      ProbabilityMeasure (ReferenceDriverPath 1 data.base.physicalHorizon))
    (sampledMap q hq hq1 gamma c hg hc T hT hlim).continuous.measurable.aemeasurable

theorem sampled_convergence :
    Tendsto (sampledData q hq hq1 gamma c hg hc T hT).literalSlowClockPathLaw atTop
      (𝓝 (sampledLimitLaw q hq hq1 gamma c hg hc T hT hlim)) := by
  exact (sampledData q hq hq1 gamma c hg hc T hT).calibratedLiteralSlowClockPathLaw_tendsto_namedCovariance
    (sampled_noise q hq hq1 gamma c hg hc T hT hlim)
    (sampled_product q hq hq1 gamma c hg hc T hT)
    (sampledData_batch q hq hq1 gamma c hg hc T hT)
    _ _ (sampled_initial q hq hq1 gamma c hg hc T hT)
    (sampled_mean q hq hq1 gamma c hg hc T hT)

-- The mathematical solution depends on drift/initial/driver, not the supplied bound.
theorem solutionMap_independent_constant {E : Type*} [NormedAddCommGroup E]
    [NormedSpace ℝ E] [CompleteSpace E] [FiniteDimensional ℝ E]
    {H : ℝ} (hH : 0 ≤ H) (drift : E → E) (L M : ℝ≥0)
    (hL : LipschitzWith L drift) (hM : LipschitzWith M drift) (x : E) :
    solutionMap hH drift L hL x = solutionMap hH drift M hM x := by
  apply ContinuousMap.ext
  intro driver
  exact solutionPath_unique hH drift L hL x driver _ _
    (solutionMap_isAdditiveSolution hH drift L hL x driver)
    (solutionMap_isAdditiveSolution hH drift M hM x driver)

theorem sampledMap_eq (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1)
    (T' : ℕ → ℕ) (hT' : ∀ n, 0 < T' n) (hlim' : Tendsto T' atTop atTop) :
    sampledMap q hq hq1 gamma c hg hc T hT hlim =
      sampledMap q' hq' hq1' gamma c hg hc T' hT' hlim' := by
  apply solutionMap_independent_constant

theorem sampledLimitLaw_eq (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1)
    (T' : ℕ → ℕ) (hT' : ∀ n, 0 < T' n) (hlim' : Tendsto T' atTop atTop) :
    sampledLimitLaw q hq hq1 gamma c hg hc T hT hlim =
      sampledLimitLaw q' hq' hq1' gamma c hg hc T' hT' hlim' := by
  unfold sampledLimitLaw
  simp only [sampledMap_eq q hq hq1 gamma c hg hc T hT hlim q' hq' hq1' T' hT' hlim']
  rfl

#print axioms sampled_convergence
#print axioms sampledLimitLaw_eq

open DPAdamFixedBetaFastSlowPrivacyScaleCalibration
open DPAdamFixedBetaFastSlowHorizonTuning
open DPAdamFixedBetaFastSlowPrivacyReceiptAsymptotic
open DPAdamFixedBetaFastSlowSlowClockPrivacy

theorem sampled_selected_scale (order : ℕ) (delta epsilon slack : ℝ)
    (hgap : receiptConversion order delta < epsilon)
    (hgamma : gamma = (1 + slack) * (order : ℝ) /
      (2 * (epsilon - receiptConversion order delta))) :
    selectedPrivacyScale (sampledData q hq hq1 gamma c hg hc T hT)
      order delta epsilon slack = c * Real.sqrt gamma := by
  rw [selectedPrivacyScale_eq_horizon_mul_privacySlope,
    privacySlope_eq_card_formula _ _ _ _ _
      (sampledData_batch q hq hq1 gamma c hg hc T hT) hgap]
  have hcard : (sampledData q hq hq1 gamma c hg hc T hT).base.dataset.card = 1 := by
    simp [sampledData, sampledFamily, quadraticData, positiveFloorQuadraticFamily]
  rw [hcard]
  change c / Real.sqrt gamma *
    ((1 + slack) * (order : ℝ) / (2 * (1 : ℝ)^2 *
      (epsilon - receiptConversion order delta))) = _
  simp only [one_pow, mul_one]
  rw [← hgamma]
  have hs := (Real.sqrt_pos.2 hg).ne'
  field_simp
  rw [Real.sq_sqrt hg.le]

include hlim in
theorem sampled_privacy (order : ℕ) (ho : 2 ≤ order)
    (delta : ℝ) (hd : 0 < delta) (hd1 : delta < 1) (epsilon slack : ℝ)
    (hgap : receiptConversion order delta < epsilon) (hs : 0 < slack)
    (hgamma : gamma = (1 + slack) * (order : ℝ) /
      (2 * (epsilon - receiptConversion order delta))) :
    ∀ᶠ n in atTop, Mf.DP.ApproxDP Mf.DP.FinsetAddRemoveAdjacent
      (slowClockPathMechanismAtRow (sampledData q hq hq1 gamma c hg hc T hT) n)
      epsilon delta := by
  have heq := sampled_selected_scale q hq hq1 gamma c hg hc T hT
    order delta epsilon slack hgap hgamma
  apply eventually_slowClockPath_approxDP_of_receiptLimit_lt _
    (sampled_noise q hq hq1 gamma c hg hc T hT hlim)
    (mul_pos hc (Real.sqrt_pos.2 hg))
    (sampled_product q hq hq1 gamma c hg hc T hT)
    order ho delta hd hd1 epsilon
  have hm := selectedPrivacyScale_receipt_margin
    (sampledData q hq hq1 gamma c hg hc T hT)
    order ho delta epsilon slack hgap hs
  rwa [heq] at hm

-- Both actual path laws converge to one named law; no equality premise is supplied.
include hlim in
theorem paired_convergence (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1)
    (T' : ℕ → ℕ) (hT' : ∀ n, 0 < T' n) (hlim' : Tendsto T' atTop atTop) :
    ∃ law : ProbabilityMeasure (ReferenceDriverPath 1 (c / Real.sqrt gamma)),
      Tendsto (sampledData q hq hq1 gamma c hg hc T hT).literalSlowClockPathLaw
        atTop (𝓝 law) ∧
      Tendsto (sampledData q' hq' hq1' gamma c hg hc T' hT').literalSlowClockPathLaw
        atTop (𝓝 law) := by
  refine ⟨_, sampled_convergence q hq hq1 gamma c hg hc T hT hlim, ?_⟩
  rw [sampledLimitLaw_eq q hq hq1 gamma c hg hc T hT hlim q' hq' hq1' T' hT' hlim']
  exact sampled_convergence q' hq' hq1' gamma c hg hc T' hT' hlim'

#print axioms paired_convergence
#print axioms sampled_privacy
end
end LadonSampledFamilyAudit
