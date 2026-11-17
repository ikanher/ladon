import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowExactCountSchedule
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowCenteredQuadraticMean
import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowNamedNonlinearLimitLaw
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
end
end LadonSampledFamilyAudit
