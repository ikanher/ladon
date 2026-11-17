import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowExactCountSchedule
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowFiniteRate
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowPrivacyReceiptAsymptotic
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowHorizonTuning
import Mf.Optimization.SDE.DPAdamClippedQueryMeasurability
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowNamedNonlinearLimitLaw
namespace LadonGeneralBridge
open Filter MeasureTheory Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowFamily DPAdamFixedBetaFastSlowGrowingClockMaps
open DPAdamFixedBetaFastSlowHighNoiseResponse
open scoped Topology
noncomputable section
set_option autoImplicit false

-- The within-row mesh limit imposes no rate on the across-row public initial points.
def withInitial {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (x : Fin d → ℝ) : FixedNoiseFastSlowFamily m d :=
  { family with
    thetaInitial := fun _ => x
    thetaLimitInitial := x
    thetaInitial_tendsto := tendsto_const_nhds
    fluctuationInitial := 0
    fluctuationInitial_tendsto := by
      convert (tendsto_const_nhds : Tendsto (fun _ : ℕ => (0 : Fin d → ℝ))
        atTop (𝓝 0)) using 1
      ext mesh i
      simp }

theorem initial_coherence {m d : ℕ} (family : ℕ → FixedNoiseFastSlowFamily m d)
    (mesh : ℕ → ℕ) (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ)
    (hx : Tendsto x atTop (𝓝 x0)) :
    Tendsto (fun n => ‖(withInitial (family n) (x n)).thetaInitial (mesh n) - x0‖)
      atTop (𝓝 0) := by
  exact tendsto_iff_norm_sub_tendsto_zero.mp hx

theorem fixed_query_mean {m d : ℕ} (data : GrowingClockData m d)
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hquery : ∀ n, (data.family n).gradientOracle = query)
    (n : ℕ) (theta : Fin d → ℝ) :
    clippedGradientMean (data.family n) theta =
      DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
        (fun record => Mf.DP.l2VectorClip data.base.clipping (query theta record))
        data.base.dataset := by
  simp only [clippedGradientMean, hquery n, data.clipping_eq n, data.dataset_eq n]

theorem fixed_query_local_mean {m d : ℕ} (data : GrowingClockData m d)
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hquery : ∀ n, (data.family n).gradientOracle = query) :
    ∀ radius : ℝ, 0 ≤ radius → ∃ meanError : ℕ → ℝ,
      (∀ n, 0 ≤ meanError n) ∧ Tendsto meanError atTop (𝓝 0) ∧
      ∀ n (theta : Fin d → ℝ), ‖theta‖ ≤ radius →
        ‖clippedGradientMean (data.family n) theta -
          DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
            (fun record => Mf.DP.l2VectorClip data.base.clipping (query theta record))
            data.base.dataset‖ ≤ meanError n := by
  intro radius hradius
  refine ⟨fun _ => 0, fun _ => le_rfl, tendsto_const_nhds, ?_⟩
  intro n theta htheta
  rw [fixed_query_mean data query hquery n theta]
  simp

#print axioms withInitial
#print axioms initial_coherence
#print axioms fixed_query_local_mean

def withInitialRegularity {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (regularity : FixedNoiseFastSlowQueryRegularity family) (x : Fin d → ℝ) :
    FixedNoiseFastSlowQueryRegularity (withInitial family x) where
  recordConstant := regularity.recordConstant
  recordConstant_nonneg := regularity.recordConstant_nonneg
  gradientOracle_sub_l2Norm_le := regularity.gradientOracle_sub_l2Norm_le

def withPublicInitial {m d : ℕ} (data : GrowingClockData m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) : GrowingClockData m d :=
  { data with
    base := withInitial data.base x0
    baseRegularity := withInitialRegularity data.base data.baseRegularity x0
    family := fun n => withInitial (data.family n) (x n)
    regularity := fun n => withInitialRegularity (data.family n) (data.regularity n) (x n) }

theorem public_initial_coherence {m d : ℕ} (data : GrowingClockData m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) (hx : Tendsto x atTop (𝓝 x0)) :
    Tendsto (fun n => ‖((withPublicInitial data x x0).family n).thetaInitial
      ((withPublicInitial data x x0).mesh n) - x0‖) atTop (𝓝 0) :=
  initial_coherence data.family data.mesh x x0 hx

-- This transformation leaves the actual schedule and release kernels' primitive data fixed.
theorem public_initial_clock {m d : ℕ} (data : GrowingClockData m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) :
    (withPublicInitial data x x0).clock = data.clock ∧
    (withPublicInitial data x x0).eta = data.eta := by exact ⟨rfl, rfl⟩

#print axioms withPublicInitial
#print axioms public_initial_coherence
#print axioms public_initial_clock

open DPAdamGaussianReferenceFunctionalLimit
open FiniteHorizonCovarianceBrownianPathLaw FiniteHorizonAdditiveLipschitzSolutionMap

theorem fixed_query_public_initial_limit {m d : ℕ} [Nonempty (Fin d)]
    (data : GrowingClockData m d)
    (hnoise : Tendsto data.clock atTop atTop) (lambda : ℝ)
    (hstep : Tendsto (fun n => data.eta n * data.clock n) atTop (𝓝 lambda))
    (hbatch : data.base.effectiveBatch = data.base.samplingRate * (data.base.dataset.card : ℝ))
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hquery : ∀ n, (data.family n).gradientOracle = query)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) (hx : Tendsto x atTop (𝓝 x0)) :
    let changed := withPublicInitial data x x0
    let mean := fun theta => DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
      (fun record => Mf.DP.l2VectorClip changed.base.clipping (query theta record))
      changed.base.dataset
    let hmean := fixed_query_local_mean changed query hquery
    Tendsto changed.literalSlowClockPathLaw atTop
      (𝓝 (ProbabilityMeasure.map
        (⟨covarianceBrownianFixedPathLaw
          (lambda • DPAdamFixedBetaGaussianResampling.covariance (d := d)
            (changed.base.firstPrinciplesAtMesh 0).betaSeparation)
          changed.base.physicalHorizon, inferInstance⟩ :
          ProbabilityMeasure (ReferenceDriverPath d changed.base.physicalHorizon))
        (solutionMap changed.base.physicalHorizon_pos.le
          (changed.calibratedSlowDrift mean) changed.inheritedSlowDriftLipschitzConstant
          (changed.calibratedSlowDrift_lipschitz_of_clippedMean
            hnoise hbatch mean hmean) x0).continuous.measurable.aemeasurable)) := by
  exact (withPublicInitial data x x0).calibratedLiteralSlowClockPathLaw_tendsto_namedCovariance
    hnoise hstep hbatch _ x0 (public_initial_coherence data x x0 hx)
    (fixed_query_local_mean (withPublicInitial data x x0) query hquery)

#print axioms fixed_query_public_initial_limit
end
end LadonGeneralBridge
namespace LadonSourceConstructor
open Filter MeasureTheory Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowFamily DPAdamFixedBetaFastSlowGrowingClockMaps
open DPAdamFiniteHorizonObjective
open scoped Topology
noncomputable section
set_option autoImplicit false

def neutralObjective (d : ℕ) : SmoothObjective d where
  value := fun _ => 0
  gradient := fun _ _ => 0
  smoothness := 0
  smoothness_nonneg := le_rfl
  value_continuous := continuous_const
  gradient_continuous := continuous_const
  taylor_remainder := by intros; simp [euclideanDot]

theorem objective_field_irrelevant {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (objective : SmoothObjective d) (mesh : ℕ) :
    ({ family with objective := objective } : FixedNoiseFastSlowFamily m d).literalParameterPathLaw mesh =
      family.literalParameterPathLaw mesh := by rfl

#print axioms objective_field_irrelevant

theorem generic_kernel {m d : ℕ} (noise C B q : ℝ) (hq : 0 < q)
    (hq1 : q ≤ 1) (dataset : Finset (Fin m))
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hclip : ∀ record, Measurable fun state : PrivateAdamState (Fin d) =>
      Mf.DP.l2VectorClip C (query state.1 record)) :
    Measurable fun state : PrivateAdamState (Fin d) =>
      normalizedEuclideanAveragedSampledGaussianRelease
        C (noise * B) B (fun record => query state.1 record) dataset q hq.le hq1 := by
  have hcenter : ∀ mask : Mf.DP.ParticipationTrace m,
      Measurable fun state : PrivateAdamState (Fin d) =>
        (euclideanClippedDatasetMixture C
          (fun record : Fin m => query state.1 record) dataset
          q hq.le hq1).mean mask := by
    intro mask
    apply measurable_pi_lambda
    intro i
    change Measurable fun state : PrivateAdamState (Fin d) =>
      ∑ record : Fin m,
        if mask record then
          (if record ∈ dataset then Mf.DP.l2VectorClip C (query state.1 record) else 0) i
        else 0
    apply Finset.measurable_sum
    intro record _
    by_cases hm : mask record = true
    · by_cases hd : record ∈ dataset
      · have hc := hclip record
        simpa [hm, hd, Function.comp_def] using ((measurable_pi_apply i).comp hc)
      · simp [hm, hd]
    · have hf : mask record = false := Bool.eq_false_iff.mpr hm
      simp [hf]
  have hpdf :
      Measurable (Function.uncurry
        (fun state : PrivateAdamState (Fin d) => fun y : Fin d → ℝ =>
          ENNReal.ofReal
            (Mf.DP.finiteMeanMixturePdfReal
              (euclideanClippedDatasetMixture C
                (fun record : Fin m => query state.1 record) dataset
                q hq.le hq1) ((noise * B) * C) y))) := by
    change Measurable fun z : PrivateAdamState (Fin d) × (Fin d → ℝ) =>
      ENNReal.ofReal
        (Mf.DP.finiteMeanMixturePdfReal
          (euclideanClippedDatasetMixture C
            (fun record : Fin m => query z.1.1 record) dataset
            q hq.le hq1) ((noise * B) * C) z.2)
    apply Measurable.ennreal_ofReal
    unfold Mf.DP.finiteMeanMixturePdfReal
    apply Finset.measurable_sum
    intro mask _
    have hm : Measurable fun z : PrivateAdamState (Fin d) × (Fin d → ℝ) =>
        (euclideanClippedDatasetMixture C
          (fun record : Fin m => query z.1.1 record) dataset
          q hq.le hq1).mean mask :=
      (hcenter mask).comp measurable_fst
    have hb : Measurable fun z : PrivateAdamState (Fin d) × (Fin d → ℝ) =>
        Mf.DP.bsrGaussianPdfReal ((noise * B) * C)
          ((euclideanClippedDatasetMixture C
            (fun record : Fin m => query z.1.1 record) dataset
            q hq.le hq1).mean mask) z.2 := by
      unfold Mf.DP.bsrGaussianPdfReal
      apply Finset.measurable_fun_prod
      intro i _
      fun_prop
    exact measurable_const.mul hb
  have hraw :
      Measurable fun state : PrivateAdamState (Fin d) =>
        euclideanExactSampledGaussianSumRelease C (noise * B)
          (fun record : Fin m => query state.1 record) dataset q
          hq.le hq1 := by
    simp only [euclideanExactSampledGaussianSumRelease,
      Mf.DP.finiteMeanMixtureMeasure, Mf.DP.densityMeasure]
    exact measurable_withDensity hpdf
  unfold normalizedEuclideanAveragedSampledGaussianRelease
  exact (Measure.measurable_map (averageRelease (C * B))
    (averageRelease_measurable (Coord := Fin d) (C * B))).comp hraw



structure Primitives (m d : ℕ) where
  dimensionPos : 0 < d
  beta : DPAdamMomentRatioInvariant.BetaSeparation
  beta1_pos : 0 < beta.beta1
  eps : ℝ
  C : ℝ
  q : ℝ
  eps_pos : 0 < eps
  C_pos : 0 < C
  q_pos : 0 < q
  q_le_one : q ≤ 1
  dataset : Finset (Fin m)
  dataset_nonempty : 0 < dataset.card
  query : (Fin d → ℝ) → Fin m → (Fin d → ℝ)
  recordConstant : Fin m → ℝ
  recordConstant_nonneg : ∀ r ∈ dataset, 0 ≤ recordConstant r
  query_lipschitz : ∀ theta theta' r, r ∈ dataset →
    Mf.DP.l2Norm (query theta r - query theta' r) ≤
      recordConstant r * Mf.DP.l2Norm (theta-theta')
  clipped_measurable : ∀ record, Measurable fun state : PrivateAdamState (Fin d) =>
    Mf.DP.l2VectorClip C (query state.1 record)

def row {m d : ℕ} (p : Primitives m d) (H noise floor : ℝ)
    (hH : 0 < H) (hf : 0 < floor) (hn : floor ≤ noise) (x : Fin d → ℝ) :
    FixedNoiseFastSlowFamily m d where
  dimensionPos := p.dimensionPos
  physicalHorizon := H
  physicalHorizon_pos := hH
  beta1 := p.beta.beta1
  beta2 := p.beta.beta2
  epsAdam := p.eps
  beta1_pos := p.beta1_pos
  beta1_lt_one := p.beta.beta1_lt_one
  beta2_nonneg := p.beta.beta2_pos.le
  beta2_lt_one := p.beta.beta2_lt_one
  beta1_sq_lt_beta2 := p.beta.beta1_sq_lt_beta2
  epsAdam_pos := p.eps_pos
  clipping := p.C
  clipping_pos := p.C_pos
  samplingRate := p.q
  samplingRate_pos := p.q_pos
  samplingRate_le_one := p.q_le_one
  effectiveBatch := p.q * (p.dataset.card : ℝ)
  effectiveBatch_pos := mul_pos p.q_pos (by exact_mod_cast p.dataset_nonempty)
  normalizedNoise := noise
  noiseFloor := floor
  noiseFloor_pos := hf
  noiseFloor_le := hn
  dataset := p.dataset
  objective := neutralObjective d
  gradientOracle := p.query
  thetaInitial := fun _ => x
  thetaLimitInitial := x
  thetaInitial_tendsto := tendsto_const_nhds
  fluctuationInitial := 0
  fluctuationInitial_tendsto := by
    convert (tendsto_const_nhds : Tendsto (fun _ : ℕ => (0 : Fin d → ℝ)) atTop (𝓝 0)) using 1
    ext mesh i
    simp
  coefficientDomain := Set.univ
  coefficientDomain_eq_univ := rfl
  releaseKernel_measurable := fun _ input => generic_kernel noise p.C
    (p.q * (p.dataset.card : ℝ)) p.q p.q_pos p.q_le_one input p.query p.clipped_measurable

def regularity {m d : ℕ} (p : Primitives m d) (H noise floor : ℝ)
    (hH : 0 < H) (hf : 0 < floor) (hn : floor ≤ noise) (x : Fin d → ℝ) :
    FixedNoiseFastSlowQueryRegularity (row p H noise floor hH hf hn x) where
  recordConstant := p.recordConstant
  recordConstant_nonneg := p.recordConstant_nonneg
  gradientOracle_sub_l2Norm_le := by
    intros theta theta' _ _ r hr
    exact p.query_lipschitz theta theta' r hr

open DPAdamFixedBetaFastSlowExactCountSchedule
def sourceData {m d : ℕ} (p : Primitives m d) (x : ℕ → (Fin d → ℝ))
    (x0 : Fin d → ℝ) (γ c : ℝ) (hγ : 0 < γ) (hc : 0 < c)
    (T : Nat → Nat) (hT : ∀ n, 0 < T n) : GrowingClockData m d where
  base := row p (c / Real.sqrt γ) (Real.sqrt γ)
    (Real.sqrt γ) (div_pos hc (Real.sqrt_pos.2 hγ))
    (Real.sqrt_pos.2 hγ) le_rfl x0
  baseRegularity := regularity p (c / Real.sqrt γ)
    (Real.sqrt γ) (Real.sqrt γ) (div_pos hc (Real.sqrt_pos.2 hγ))
    (Real.sqrt_pos.2 hγ) le_rfl x0
  family := fun n =>
    row p
      (c * Real.sqrt (T n : ℝ))
      (Real.sqrt (γ * (T n : ℝ))) (Real.sqrt γ)
      (mul_pos hc (Real.sqrt_pos.2 (by exact_mod_cast hT n)))
      (Real.sqrt_pos.2 hγ)
      (by
        have hn : (1 : ℝ) ≤ (T n : ℝ) := by exact_mod_cast (hT n)
        have hs := Real.sqrt_le_sqrt (mul_le_mul_of_nonneg_left hn hγ.le)
        simpa only [mul_one] using hs) (x n)
  regularity := fun n =>
    regularity p
      (c * Real.sqrt (T n : ℝ))
      (Real.sqrt (γ * (T n : ℝ))) (Real.sqrt γ)
      (mul_pos hc (Real.sqrt_pos.2 (by exact_mod_cast hT n)))
      (Real.sqrt_pos.2 hγ)
      (by
        have hn : (1 : ℝ) ≤ (T n : ℝ) := by exact_mod_cast (hT n)
        have hs := Real.sqrt_le_sqrt (mul_le_mul_of_nonneg_left hn hγ.le)
        simpa only [mul_one] using hs) (x n)
  mesh := fun n => T n - 1
  scale := fun n => scale (T n : ℝ)
  scale_one_le := by
    intro n
    apply scale_one_le
    have hn : (1 : ℝ) ≤ (T n : ℝ) := by exact_mod_cast (hT n)
    exact hn
  noise_eq := by
    intro n
    change Real.sqrt (γ * (T n : ℝ)) =
      scale (T n : ℝ) * Real.sqrt γ
    simpa only [mul_comm] using
      (scale_mul_baseNoise_eq_clock hγ (show 0 < (T n : ℝ) by exact_mod_cast hT n)).symm
  beta1_eq := by intro n; rfl
  beta2_eq := by intro n; rfl
  eps_eq := by intro n; rfl
  batch_eq := by intro n; rfl
  clipping_eq := by intro n; rfl
  sampling_eq := by intro n; rfl
  floor_eq := by intro n; rfl
  dataset_eq := by intro n; rfl
  records_eq := by intro n; rfl
  horizon_growing := by
    intro n
    change c * Real.sqrt (T n : ℝ) =
      Real.sqrt (γ * (T n : ℝ)) * (c / Real.sqrt γ)
    rw [Real.sqrt_mul hγ.le]
    have hsqrtγ : Real.sqrt γ ≠ 0 := (Real.sqrt_pos.2 hγ).ne'
    field_simp


theorem source_batch {m d : ℕ} (p : Primitives m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ)
    (gamma c : ℝ) (hg : 0 < gamma) (hc : 0 < c)
    (T : ℕ → ℕ) (hT : ∀ n, 0 < T n) :
    (sourceData p x x0 gamma c hg hc T hT).base.effectiveBatch =
      p.q * (p.dataset.card : ℝ) := rfl

#print axioms sourceData
#print axioms source_batch

-- A single source release family supplies clipped-query measurability for all records;
-- the generic kernel then rebuilds releases at every new positive sampling probability.
theorem source_clipped_measurable {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (record : Fin m) : Measurable fun state : PrivateAdamState (Fin d) =>
    Mf.DP.l2VectorClip family.clipping (family.gradientOracle state.1 record) := by
  exact (family.releaseDataAtMesh 0).clippedGradient_measurable 0 family.samplingRate_pos record

#print axioms generic_kernel
#print axioms source_clipped_measurable
end
end LadonSourceConstructor
namespace LadonSourceConstructor
open Filter MeasureTheory Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowGrowingClockMaps DPAdamFixedBetaFastSlowHighNoiseResponse
open DPAdamGaussianReferenceFunctionalLimit FiniteHorizonCovarianceBrownianPathLaw
open FiniteHorizonAdditiveLipschitzSolutionMap LadonGeneralBridge
open scoped Topology NNReal
noncomputable section
set_option autoImplicit false
variable {m d : ℕ} [Nonempty (Fin d)]
variable (p : Primitives m d) (gamma c : ℝ) (hg : 0 < gamma) (hc : 0 < c)
variable (T : ℕ → ℕ) (hT : ∀ n, 0 < T n) (hlim : Tendsto T atTop atTop)
variable (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) (hx : Tendsto x atTop (𝓝 x0))

theorem noise_limit (hlim : Tendsto T atTop atTop) :
    Tendsto (sourceData p x x0 gamma c hg hc T hT).clock atTop atTop :=
  DPAdamFixedBetaFastSlowExactCountSchedule.quadraticData_clock_tendsto gamma c hg hc T hT hlim

theorem step_limit :
    Tendsto (fun n => (sourceData p x x0 gamma c hg hc T hT).eta n *
      (sourceData p x x0 gamma c hg hc T hT).clock n) atTop (𝓝 (c * Real.sqrt gamma)) :=
  DPAdamFixedBetaFastSlowExactCountSchedule.quadraticData_step_noise_limit gamma c hg hc T hT

def sourceMap :=
  let data := sourceData p x x0 gamma c hg hc T hT
  let mean := fun theta => DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
    (fun r => Mf.DP.l2VectorClip p.C (p.query theta r)) p.dataset
  solutionMap data.base.physicalHorizon_pos.le
    (data.calibratedSlowDrift mean) data.inheritedSlowDriftLipschitzConstant
    (data.calibratedSlowDrift_lipschitz_of_clippedMean
      (noise_limit p gamma c hg hc T hT x x0 hlim) rfl mean
      (fixed_query_local_mean data p.query (by intro n; rfl))) x0

def sourceLaw : ProbabilityMeasure (ReferenceDriverPath d (c / Real.sqrt gamma)) :=
  let data := sourceData p x x0 gamma c hg hc T hT
  ProbabilityMeasure.map
    (⟨covarianceBrownianFixedPathLaw
      ((c * Real.sqrt gamma) • DPAdamFixedBetaGaussianResampling.covariance (d := d)
        (data.base.firstPrinciplesAtMesh 0).betaSeparation) data.base.physicalHorizon,
        inferInstance⟩ : ProbabilityMeasure (ReferenceDriverPath d data.base.physicalHorizon))
    (sourceMap p gamma c hg hc T hT hlim x x0).continuous.measurable.aemeasurable

include hx hlim in
theorem source_convergence :
    Tendsto (sourceData p x x0 gamma c hg hc T hT).literalSlowClockPathLaw atTop
      (𝓝 (sourceLaw p gamma c hg hc T hT hlim x x0)) := by
  apply (sourceData p x x0 gamma c hg hc T hT).calibratedLiteralSlowClockPathLaw_tendsto_namedCovariance
    (noise_limit p gamma c hg hc T hT x x0 hlim)
    (step_limit p gamma c hg hc T hT x x0) rfl _ x0
    (tendsto_iff_norm_sub_tendsto_zero.mp hx)
    (fixed_query_local_mean _ p.query (by intro n; rfl))

#print axioms source_convergence

def resample (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1) : Primitives m d :=
  { p with q := q', q_pos := hq', q_le_one := hq1' }

theorem solutionMap_independent_constant {E : Type*} [NormedAddCommGroup E]
    [NormedSpace ℝ E] [CompleteSpace E] [FiniteDimensional ℝ E]
    {H : ℝ} (hH : 0 ≤ H) (drift : E → E) (L M : ℝ≥0)
    (hL : LipschitzWith L drift) (hM : LipschitzWith M drift) (initial : E) :
    solutionMap hH drift L hL initial = solutionMap hH drift M hM initial := by
  apply ContinuousMap.ext
  intro driver
  exact solutionPath_unique hH drift L hL initial driver _ _
    (solutionMap_isAdditiveSolution hH drift L hL initial driver)
    (solutionMap_isAdditiveSolution hH drift M hM initial driver)

theorem sourceMap_resample (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1)
    (T' : ℕ → ℕ) (hT' : ∀ n, 0 < T' n) (hlim' : Tendsto T' atTop atTop) :
    sourceMap p gamma c hg hc T hT hlim x x0 =
      sourceMap (resample p q' hq' hq1') gamma c hg hc T' hT' hlim' x x0 := by
  apply solutionMap_independent_constant

theorem sourceLaw_resample (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1)
    (T' : ℕ → ℕ) (hT' : ∀ n, 0 < T' n) (hlim' : Tendsto T' atTop atTop) :
    sourceLaw p gamma c hg hc T hT hlim x x0 =
      sourceLaw (resample p q' hq' hq1') gamma c hg hc T' hT' hlim' x x0 := by
  unfold sourceLaw
  simp only [sourceMap_resample p gamma c hg hc T hT hlim x x0 q' hq' hq1' T' hT' hlim']
  rfl

include hx hlim in
theorem paired_source_convergence (q' : ℝ) (hq' : 0 < q') (hq1' : q' ≤ 1)
    (T' : ℕ → ℕ) (hT' : ∀ n, 0 < T' n) (hlim' : Tendsto T' atTop atTop) :
    ∃ law : ProbabilityMeasure (ReferenceDriverPath d (c / Real.sqrt gamma)),
      Tendsto (sourceData p x x0 gamma c hg hc T hT).literalSlowClockPathLaw atTop (𝓝 law) ∧
      Tendsto (sourceData (resample p q' hq' hq1') x x0 gamma c hg hc T' hT').literalSlowClockPathLaw
        atTop (𝓝 law) := by
  refine ⟨_, source_convergence p gamma c hg hc T hT hlim x x0 hx, ?_⟩
  rw [sourceLaw_resample p gamma c hg hc T hT hlim x x0 q' hq' hq1' T' hT' hlim']
  exact source_convergence _ gamma c hg hc T' hT' hlim' x x0 hx

#print axioms paired_source_convergence

-- Derive the constructor's measurability input from the source's kernel assumption
-- at just one run, before changing q or the noise schedule.
theorem clipped_measurable_of_one_release {m d : ℕ}
    (C sigma B q : ℝ) (hC : 0 < C) (hsigma : 0 < sigma) (hB : 0 < B)
    (hq : 0 < q) (hq1 : q ≤ 1)
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hkernel : ∀ input : Finset (Fin m), Measurable fun state : PrivateAdamState (Fin d) =>
      normalizedEuclideanAveragedSampledGaussianRelease C sigma B
        (fun record => query state.1 record) input q hq.le hq1)
    (record : Fin m) :
    Measurable fun state : PrivateAdamState (Fin d) =>
      Mf.DP.l2VectorClip C (query state.1 record) := by
  apply measurable_pi_lambda
  intro a
  let kernel : ProbabilityTheory.Kernel (PrivateAdamState (Fin d)) (Fin d → ℝ) :=
    ⟨fun state => normalizedEuclideanAveragedSampledGaussianRelease C sigma B
      (fun r => query state.1 r) {record} q hq.le hq1, hkernel {record}⟩
  have hmean : StronglyMeasurable fun state : PrivateAdamState (Fin d) =>
      ∫ y : Fin d → ℝ, y a ∂kernel state :=
    (measurable_pi_apply a).stronglyMeasurable.integral_kernel (κ := kernel)
  have hscaled := hmean.const_mul ((C * B) / q)
  apply StronglyMeasurable.measurable
  convert hscaled using 1
  funext state
  change Mf.DP.l2VectorClip C (query state.1 record) a =
    (C * B) / q * (∫ y : Fin d → ℝ, y a
      ∂normalizedEuclideanAveragedSampledGaussianRelease C sigma B
        (fun r => query state.1 r) {record} q hq.le hq1)
  rw [normalizedEuclideanAveragedSampledGaussianRelease_singleton_integral_eval
    C sigma B hC hsigma hB (fun r => query state.1 r) record q hq.le hq1 a]
  field_simp [ne_of_gt hq, ne_of_gt hC, ne_of_gt hB]

#print axioms clipped_measurable_of_one_release

instance record_nonempty (p : Primitives m d) : Nonempty {r // r ∈ p.dataset} := by
  obtain ⟨r, hr⟩ := Finset.card_pos.mp p.dataset_nonempty
  exact ⟨⟨r, hr⟩⟩

theorem mean_bridge (theta : Fin d → ℝ) :
    FiniteHorizonEmpiricalClippedObjective.meanClippedGradient p.C
      (fun r : {r // r ∈ p.dataset} => p.query theta r) =
      DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
        (fun r => Mf.DP.l2VectorClip p.C (p.query theta r)) p.dataset := by
  ext i
  simp [FiniteHorizonEmpiricalClippedObjective.meanClippedGradient,
    DPAdamFixedBetaConcreteClippingAlignment.empiricalMean, Finset.sum_apply, Finset.sum_attach]

#print axioms mean_bridge

open FiniteHorizonEmpiricalClippedObjective FiniteHorizonEmpiricalClippedRate
open FiniteDimensionalItoDiffusionGenerator
open DPAdamFixedBetaResponseCoefficientContinuity

include hlim hx in
theorem source_finite_rate
    (f : (Fin d → ℝ) → ℝ) (hf : ContDiff ℝ 2 f)
    (dispersion hessian lower : ℝ) (hsmall : dispersion ≤ p.C / 2) (hH : 0 ≤ hessian)
    (hlower : ∀ z, lower ≤ f z)
    (hgradient : ∀ z i, fderiv ℝ f z (coordinateVector i) =
      (meanGradient (fun r : {r // r ∈ p.dataset} => p.query z r)) i)
    (hdisp : ∀ z, gradientDispersion (fun r : {r // r ∈ p.dataset} => p.query z r) ≤ dispersion)
    (hhess : ∀ z v, hessianBilinear f z v v ≤ hessian * ∑ i, (v i)^2) :
    let data := sourceData p x x0 gamma c hg hc T hT
    let gain := zeroResponseCoefficient (data.base.firstPrinciplesAtMesh 0).betaSeparation / p.C
    ∀ tolerance : ℝ, 0 < tolerance → ∀ᶠ n in atTop,
      (∫ history, data.retainedNodeAverage n
        (fun z => clippedGradientPenalty p.C
          (meanGradient (fun r : {r // r ∈ p.dataset} => p.query z r))) history
        ∂(data.family n).transcriptMeasureAtMesh (data.mesh n)) ≤
      2 * (f x0 - lower) / (gain * data.base.physicalHorizon) + dispersion^2 +
        hessian * Matrix.trace ((c * Real.sqrt gamma) •
          DPAdamFixedBetaGaussianResampling.covariance (d := d)
            (data.base.firstPrinciplesAtMesh 0).betaSeparation) / gain + tolerance := by
  let data := sourceData p x x0 gamma c hg hc T hT
  have hmean := fixed_query_local_mean data p.query (by intro n; rfl)
  have result := DPAdamFixedBetaFastSlowFiniteRate.empiricalClippedPenalty_finiteIterate_rate
    (ι := {r // r ∈ p.dataset}) data
    (noise_limit p gamma c hg hc T hT x x0 hlim)
    (step_limit p gamma c hg hc T hT x x0) rfl
    f hf (fun z r => p.query z r) dispersion hessian lower hsmall hH hlower
    hgradient hdisp hhess x0 (tendsto_iff_norm_sub_tendsto_zero.mp hx)
    (by simpa only [show data.base.clipping = p.C from rfl, show data.base.dataset = p.dataset from rfl, mean_bridge p] using hmean)
  exact result.2.2.2.2.2

open DPAdamFixedBetaFastSlowPrivacyScaleCalibration DPAdamFixedBetaFastSlowHorizonTuning
open DPAdamFixedBetaFastSlowPrivacyReceiptAsymptotic DPAdamFixedBetaFastSlowSlowClockPrivacy

include hlim in
theorem source_privacy
    (order : ℕ) (ho : 2 ≤ order) (delta : ℝ) (hd : 0 < delta) (hd1 : delta < 1)
    (epsilon slack : ℝ) (hgap : receiptConversion order delta < epsilon) (hs : 0 < slack)
    (hgamma : gamma = (1+slack) * (order : ℝ) /
      (2 * (p.dataset.card : ℝ)^2 * (epsilon - receiptConversion order delta))) :
    ∀ᶠ n in atTop, Mf.DP.ApproxDP Mf.DP.FinsetAddRemoveAdjacent
      (slowClockPathMechanismAtRow (sourceData p x x0 gamma c hg hc T hT) n) epsilon delta := by
  let data := sourceData p x x0 gamma c hg hc T hT
  have heq : selectedPrivacyScale data order delta epsilon slack = c * Real.sqrt gamma := by
    rw [selectedPrivacyScale_eq_horizon_mul_privacySlope,
      privacySlope_eq_card_formula _ _ _ _ _ rfl hgap]
    change c / Real.sqrt gamma *
      ((1+slack) * (order : ℝ) / (2 * (p.dataset.card : ℝ)^2 *
        (epsilon-receiptConversion order delta))) = _
    rw [← hgamma]
    field_simp [(Real.sqrt_pos.2 hg).ne']
    rw [Real.sq_sqrt hg.le]
  apply eventually_slowClockPath_approxDP_of_receiptLimit_lt data
    (noise_limit p gamma c hg hc T hT x x0 hlim) (mul_pos hc (Real.sqrt_pos.2 hg))
    (step_limit p gamma c hg hc T hT x x0) order ho delta hd hd1 epsilon
  have hm := selectedPrivacyScale_receipt_margin data order ho delta epsilon slack hgap hs
  rwa [heq] at hm

#print axioms source_finite_rate
#print axioms source_privacy
end
end LadonSourceConstructor
