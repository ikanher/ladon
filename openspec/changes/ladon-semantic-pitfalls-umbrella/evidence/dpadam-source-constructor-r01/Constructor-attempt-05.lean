import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowExactCountSchedule
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
          have hc := hclip record
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
  kernel : ∀ noise : ℝ, 0 < noise → ∀ privateInput : Finset (Fin m),
    Measurable fun state : PrivateAdamState (Fin d) =>
      normalizedEuclideanAveragedSampledGaussianRelease C
        (noise * (q * (dataset.card : ℝ))) (q * (dataset.card : ℝ))
        (fun record => query state.1 record) privateInput q q_pos.le q_le_one

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
  releaseKernel_measurable := fun _ input => p.kernel noise (hf.trans_le hn) input

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
end
end LadonSourceConstructor
