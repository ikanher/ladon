import Mf.DP.GaussianMixtureSimulation
import Mf.DP.GaussianRowSimulationCoordinates
import Mf.Optimization.PoissonClippedSGD.OptionalPrivacy
import Mf.Optimization.PoissonClippedSGD.PrivacyLaw
import Mf.Optimization.SDE.DPAdamSampledGaussianAmplifiedRDP
import Mf.Optimization.SDE.DPAdamEuclideanAveragedReleaseMechanism



/-!
# Common Poisson mixture simulator for the adaptive clipped-SGD transcript

One Markov kernel maps the independent scalar mixture product and the
independent standard Gaussian product to the present-record and deleted-record
transcripts, respectively. The kernel integrates fresh common masks and
auxiliary Gaussian vectors, keeping participation hidden. Both conditional row
laws are proved from the concrete Poisson law before iterating the encoder.

This is the mixture-law step in the corrected-profile extension to Appendix
C.4.2 of Koloskova, Hendrikx and Stich, *Revisiting Gradient Clipping* (ICML 2023).
The transcript contains raw noisy sums. State reconstruction divides by the
fixed public `qN`, so multiplier `sqrt(V)` means normalized coordinate variance
`C² V / (qN)²`. Existing density adapters retain historical compatibility names;
the reusable Gaussian simulation owners are independent of matrix mechanisms.
-/

noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.Probability.SeedTranscript

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture

variable {n d : ℕ}
abbrev Mask (n : ℕ) := Fin n → Bool
abbrev Vector (d : ℕ) := EuclideanSpace ℝ (Fin d)
abbrev InputSeed (n d : ℕ) := Mask n × (ℝ × Vector d)

/-- The common query excludes the exceptional slot. -/
def commonMean (data : PrivacyData n d) (A : Finset (Fin n)) (t : ℕ)
    (p : SumHistory d t × Mask n) : Vector d :=
  Mf.DP.toEuclidean (SDE.euclideanPoissonMaskedClippedSum data.clipping
    (data.rawGradient (data.state t p.1)) A p.2)

/-- Full clipped exceptional query, independent of its unused mask bit. -/
def clippedRecord (data : PrivacyData n d) (i : Fin n) (t : ℕ)
    (h : SumHistory d t) : Vector d :=
  Mf.DP.toEuclidean (Mf.DP.l2VectorClip data.clipping
    (data.rawGradient (data.state t h) i))

theorem commonMean_measurable (data : PrivacyData n d)
    (A : Finset (Fin n)) (t : ℕ) : Measurable (commonMean data A t) := by
  have hz : Measurable (fun p : SumHistory d t × Mask n =>
      data.seedRelease A t (p.1, (p.2, (0 : SumRelease d)))) :=
    (data.seedRelease_measurable A t).comp (by fun_prop)
  have hsum : Measurable (fun p : SumHistory d t × Mask n =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (data.rawGradient (data.state t p.1)) A p.2) := by
    simpa only [seedRelease, add_zero] using hz
  change Measurable (fun p : SumHistory d t × Mask n =>
    Mf.DP.toEuclidean (SDE.euclideanPoissonMaskedClippedSum data.clipping
      (data.rawGradient (data.state t p.1)) A p.2))
  exact Mf.DP.measurable_toEuclidean.comp hsum

theorem clippedRecord_measurable (data : PrivacyData n d) (i : Fin n) (t : ℕ) :
    Measurable (clippedRecord data i t) :=
  Mf.DP.measurable_toEuclidean.comp
    ((Mf.DP.measurable_l2VectorClip data.clipping).comp
      ((data.rawGradient_measurable i).comp (data.state_measurable t)))

theorem clippedRecord_norm_le (data : PrivacyData n d) (i : Fin n)
    (t : ℕ) (h : SumHistory d t) :
    ‖clippedRecord data i t h‖ ≤ data.clipping := by
  exact Mf.DP.l2VectorClip_norm_le data.clipping
    (data.rawGradient (data.state t h) i) data.clipping_pos.le

/-- Raw sum output; no mask or selector appears in the release. -/
def rawRow (data : PrivacyData n d) (A : Finset (Fin n)) (i : Fin n)
    (t : ℕ) (p : SumHistory d t × InputSeed n d) : SumRelease d :=
  fun k => Mf.DP.GaussianRowSimulation.simulate data.clipping
    (data.multiplier * data.clipping)
    (commonMean data A t (p.1,p.2.1)) (clippedRecord data i t p.1) p.2.2 k

theorem rawRow_measurable (data : PrivacyData n d)
    (A : Finset (Fin n)) (i : Fin n) (t : ℕ) : Measurable (rawRow data A i t) := by
  have hm : Measurable (fun p : SumHistory d t × InputSeed n d =>
      commonMean data A t (p.1,p.2.1)) :=
    (commonMean_measurable data A t).comp (by fun_prop)
  have hw : Measurable (fun p : SumHistory d t × InputSeed n d =>
      clippedRecord data i t p.1) :=
    (clippedRecord_measurable data i t).comp measurable_fst
  have hs : Measurable (fun p : SumHistory d t × InputSeed n d =>
      Mf.DP.GaussianRowSimulation.simulate data.clipping
        (data.multiplier * data.clipping)
        (commonMean data A t (p.1,p.2.1))
        (clippedRecord data i t p.1) p.2.2) :=
    (Mf.DP.GaussianRowSimulation.measurable_simulate data.clipping_pos _).comp
      ((hm.prodMk hw).prodMk (by fun_prop))
  exact (MeasurableEquiv.toLp 2 (Fin d → ℝ)).symm.measurable.comp hs

def maskLaw (data : PrivacyData n d) : Measure (Mask n) :=
  SDE.poissonMaskLaw data.q data.q_le_one

instance (data : PrivacyData n d) : IsProbabilityMeasure (maskLaw data) := by
  unfold maskLaw
  infer_instance

/-- The same input-independent completion kernel serves both ordered laws. -/
def commonKernel (data : PrivacyData n d) (A : Finset (Fin n)) (i : Fin n) (T : ℕ) :
    Kernel (Fin T → ℝ) (SumHistory d T) :=
  Mf.DP.GaussianMixtureSimulation.encodedInputKernel
    (maskLaw data) (rawRow data A i) T

theorem commonKernel_isMarkov (data : PrivacyData n d)
    (A : Finset (Fin n)) (i : Fin n) (T : ℕ) :
    IsMarkovKernel (commonKernel data A i T) := by
  apply Mf.Probability.seedKernel_isMarkov
  exact (encode_measurable _ (rawRow_measurable data A i) T).comp
    (Mf.DP.GaussianAdaptiveSimulation.combine_measurable T)

/-- Structural induction helper; its concrete row premise must be supplied
by the actual base/hidden marginal producer, never by a privacy hypothesis. -/
theorem bind_commonKernel_of_rows (data : PrivacyData n d)
    (A B : Finset (Fin n)) (i : Fin n)
    (ν : Measure ℝ) [IsProbabilityMeasure ν]
    (hrows : ∀ t h,
      ((maskLaw data).prod (ν.prod (stdGaussian (Vector d)))).map
          (fun z => rawRow data A i t (h,z)) = data.stepKernel B t h)
    (T : ℕ) :
    (iidHistoryLaw ν T).bind (commonKernel data A i T) =
      data.transcriptLaw B T := by
  rw [commonKernel,
    Mf.DP.GaussianMixtureSimulation.bind_encodedInputKernel
      (maskLaw data) (rawRow data A i) (rawRow_measurable data A i) ν T]
  have h := encode_law
    ((maskLaw data).prod (ν.prod (stdGaussian (Vector d))))
    (data.stepKernel B) (fun _ => inferInstance)
    (rawRow data A i) (rawRow_measurable data A i) hrows T
  have heq : ∀ t, Mf.Probability.SeedTranscript.transcriptLaw
      (data.stepKernel B) t = data.transcriptLaw B t := by
    intro t
    induction t with
    | zero => rfl
    | succ t ih => exact congrArg (fun μ => μ ⊗ₘ data.stepKernel B t) ih
  exact h.trans (heq T)

/-- Public reusable version of OptionalPrivacy's private deletion-law seam.
All other absent slots remain present in the fixed public population. -/
theorem erased_optional_law {Record : Type} (data : PrivacyData n d)
    (g : Record → Vector d → Vector d) (hg : ∀ r, Measurable (g r))
    (D D' : Fin n → Option Record) (i : Fin n)
    (hi' : D' i = none) (hrest : ∀ j, j ≠ i → D j = D' j) (T : ℕ) :
    (data.withSlots g hg D).transcriptLaw (Finset.univ.erase i) T =
      data.optionalTranscriptLaw g hg T D' := by
  classical
  apply data.transcriptLaw_withQueries_eq
  intro x mask
  unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
  rw [Finset.sum_filter, Finset.sum_filter]
  calc
    _ = ∑ j ∈ Finset.univ.erase i, if mask j then
        Mf.DP.l2VectorClip data.clipping (fun k => slotGradient g D' j x k) else 0 := by
      apply Finset.sum_congr rfl
      intro j hj
      have hji : j ≠ i := (Finset.mem_erase.mp hj).1
      simp only [slotGradient, hrest j hji]
    _ = _ := Finset.sum_subset (Finset.erase_subset i Finset.univ) (by
      intro j _ hj
      have hji : j = i := by simpa using hj
      subst j
      simp only [slotGradient, hi', Option.elim_none]
      change (if mask i then Mf.DP.l2VectorClip data.clipping (0 : Fin d → ℝ) else 0) = 0
      have hz : Mf.DP.l2VectorClip data.clipping (0 : Fin d → ℝ) = 0 := by
        simp [Mf.DP.l2VectorClip, data.clipping_pos.le]
      simp only [hz, ite_self])

end Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture



noncomputable section
open MeasureTheory ProbabilityTheory

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture

set_option backward.isDefEq.respectTransparency.types false in
theorem fixedMaskSimulator_eq_hiddenRecordMeasure_explicit {m d : ℕ}
    (C sigma : ℝ) (hC : 0 < C) (hsigma : 0 < sigma) (q : NNReal)
    (hq : q ≤ 1) (gradient : Fin m → (Fin d → ℝ))
    (commonDataset : Finset (Fin m)) (record : Fin m)
    (mask : Fin m → Bool) :
    (((((1 - q : NNReal) : ENNReal) • gaussianReal 0 1) +
      (q : ENNReal) • gaussianReal (C / (sigma * C)) 1).prod
        (stdGaussian (EuclideanSpace ℝ (Fin d)))).map
        (fun p => fun i =>
          Mf.DP.GaussianRowSimulation.simulate C (sigma * C)
            (Mf.DP.toEuclidean
              (Mf.Optimization.SDE.euclideanPoissonMaskedClippedSum
                C gradient commonDataset mask))
            (Mf.DP.toEuclidean (Mf.DP.l2VectorClip C (gradient record))) p i) =
      (Mf.Optimization.SDE.euclideanCommonMaskHiddenRecordDensity
        C sigma (q : ℝ) q.2 hq
        (mul_ne_zero hsigma.ne' hC.ne') gradient commonDataset record
        mask).measure := by
  have hw : ‖Mf.DP.toEuclidean (Mf.DP.l2VectorClip C (gradient record))‖ ≤ C := by
    simpa [Mf.DP.l2Norm, Mf.DP.toEuclidean] using
      (Mf.DP.l2VectorClip_norm_le C (gradient record) hC.le)
  rw [Mf.DP.GaussianRowSimulation.simulate_raw_mixture_law
    hC (mul_pos hsigma hC) q
    (Mf.DP.toEuclidean
      (Mf.Optimization.SDE.euclideanPoissonMaskedClippedSum
        C gradient commonDataset mask))
    (Mf.DP.toEuclidean (Mf.DP.l2VectorClip C (gradient record))) hw]
  simp only [Mf.Optimization.SDE.euclideanCommonMaskHiddenRecordDensity,
    Mf.Optimization.SDE.euclideanHiddenRecordGaussianDensity]
  rw [Mf.DP.sampledGaussianMixtureCommonBaseDensity_measure_eq]
  have hqENN : ENNReal.ofReal (q : ℝ) = (q : ENNReal) :=
    (ENNReal.coe_nnreal_eq q).symm
  have h1qENN : ENNReal.ofReal (1 - (q : ℝ)) =
      ((1 - q : NNReal) : ENNReal) := by
    calc
      ENNReal.ofReal (1 - (q : ℝ)) =
          ENNReal.ofReal (((1 - q : NNReal) : ℝ)) := by
            congr 1
            rw [NNReal.coe_sub hq, NNReal.coe_one]
      _ = ((1 - q : NNReal) : ENNReal) := (ENNReal.coe_nnreal_eq _).symm
  simp [Mf.DP.toEuclidean, hqENN, h1qENN,
    add_comm]
  rfl

end Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture



noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.Probability.SeedTranscript

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture

/-- Convert exact conditional laws under independent seeds to the public
marginal of their composition-product. -/
theorem independentSeed_map_eq_snd_compProd
    {M S R : Type*} [MeasurableSpace M] [MeasurableSpace S] [MeasurableSpace R]
    (μ : Measure M) (ν : Measure S) [SFinite μ] [SFinite ν]
    (g : M × S → R) (hg : Measurable g)
    (κ : Kernel M R) [IsSFiniteKernel κ]
    (hrow : ∀ a, ν.map (fun z => g (a,z)) = κ a) :
    (μ.prod ν).map g = (μ ⊗ₘ κ).snd := by
  have hp := Mf.Probability.map_pair_transform_eq_compProd μ ν id measurable_id
    g hg κ hrow
  calc
    _ = ((μ.prod ν).map (fun p => (p.1,g p))).snd := by
      rw [Measure.snd, Measure.map_map measurable_snd (measurable_fst.prodMk hg)]
      rfl
    _ = (μ ⊗ₘ κ).snd := by
      apply congrArg (fun ρ : Measure (M × R) => ρ.snd)
      simpa only [id_eq, Measure.map_id] using hp

variable {n d : ℕ}

theorem rawRow_zero_law (data : PrivacyData n d)
    (A : Finset (Fin n)) (i : Fin n) (t : ℕ) (h : SumHistory d t) :
    ((maskLaw data).prod ((gaussianReal 0 1).prod (stdGaussian (Vector d)))).map
        (fun z => rawRow data A i t (h,z)) = data.stepKernel A t h := by
  let gradient := data.rawGradient (data.state t h)
  let k := fun a : Mask n => SDE.euclideanCommonMaskGaussianDensity
    data.clipping data.multiplier
    (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') gradient A a
  have hk := SDE.measurable_euclideanCommonMaskGaussianDensity data.clipping
    data.multiplier (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') gradient A
  let κ := Mf.DP.commonBaseDensityKernel (volume : Measure (SumRelease d)) k hk
  have hrow (a : Mask n) :
      ((gaussianReal 0 1).prod (stdGaussian (Vector d))).map
          (fun z => rawRow data A i t (h,(a,z))) = κ a := by
    change ((gaussianReal 0 1).prod (stdGaussian (Vector d))).map
      (fun z => fun j => Mf.DP.GaussianRowSimulation.simulate data.clipping
        (data.multiplier*data.clipping) (commonMean data A t (h,a))
        (clippedRecord data i t h) z j) = (k a).measure
    rw [Mf.DP.GaussianRowSimulation.simulate_raw_law data.clipping_pos _ _ _
      (clippedRecord_norm_le data i t h) 0]
    simp only [mul_zero, zero_mul, add_zero]
    change Mf.Probability.FiniteGaussian.measure (data.multiplier*data.clipping)
      (SDE.euclideanPoissonMaskedClippedSum data.clipping gradient A a) =
        (k a).measure
    exact (Mf.DP.bsrGaussianCommonBaseDensity_measure_eq _ _ _).symm
  have hg : Measurable (fun z => rawRow data A i t (h,z)) :=
    (rawRow_measurable data A i t).comp (by fun_prop)
  rw [independentSeed_map_eq_snd_compProd (maskLaw data)
    ((gaussianReal 0 1).prod (stdGaussian (Vector d))) _ hg κ hrow]
  have hjoint : (data.canonicalStep A t h).measure = (maskLaw data) ⊗ₘ κ := by
    change (SDE.euclideanCommonMaskAugmentedBaseDensity data.clipping data.multiplier
      (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') gradient A
      data.q data.q_le_one).measure = _
    rw [SDE.euclideanCommonMaskAugmentedBaseDensity,
      Mf.DP.adaptiveJointProbabilityDensity_measure_eq_compProd,
      SDE.sampledGaussianPoissonMaskBaseDensity_measure_eq]
    rfl
  rw [← hjoint, data.stepKernel_eq_exact]
  exact SDE.euclideanCommonMaskAugmentedBaseDensity_snd_eq_exact _ _ _ _ _ _ _

theorem rawRow_mixture_law {n d : ℕ} (data : PrivacyData (n+1) d)
    (A : Finset (Fin (n+1))) (i : Fin (n+1)) (hi : i ∉ A)
    (t : ℕ) (h : SumHistory d t) :
    ((maskLaw data).prod
      ((Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
        (data.clipping/(data.multiplier*data.clipping))).prod
          (stdGaussian (Vector d)))).map
        (fun z => rawRow data A i t (h,z)) = data.stepKernel (insert i A) t h := by
  let : IsProbabilityMeasure (Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
      (data.clipping/(data.multiplier*data.clipping))) :=
    Mf.DP.GaussianMixtureSimulation.scalarMixture_isProbability data.q data.q_le_one _
  let gradient := data.rawGradient (data.state t h)
  let k := fun a : Mask (n+1) => SDE.euclideanCommonMaskHiddenRecordDensity
    data.clipping data.multiplier (data.q : ℝ) data.q.2 data.q_le_one
    (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') gradient A i a
  have hk := SDE.measurable_euclideanCommonMaskHiddenRecordDensity data.clipping
    data.multiplier (data.q : ℝ) data.q.2 data.q_le_one
    (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') gradient A i
  let κ := Mf.DP.commonBaseDensityKernel (volume : Measure (SumRelease d)) k hk
  have hrow (a : Mask (n+1)) :
      ((Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
        (data.clipping/(data.multiplier*data.clipping))).prod
          (stdGaussian (Vector d))).map
            (fun z => rawRow data A i t (h,(a,z))) = κ a := by
    exact Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture.fixedMaskSimulator_eq_hiddenRecordMeasure_explicit
      data.clipping data.multiplier data.clipping_pos data.multiplier_pos
      data.q data.q_le_one gradient A i a
  have hg : Measurable (fun z => rawRow data A i t (h,z)) :=
    (rawRow_measurable data A i t).comp (by fun_prop)
  rw [independentSeed_map_eq_snd_compProd (maskLaw data)
    ((Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
      (data.clipping/(data.multiplier*data.clipping))).prod
        (stdGaussian (Vector d))) _ hg κ hrow]
  have hjoint :
      (SDE.euclideanCommonMaskAugmentedHiddenDensity data.clipping data.multiplier
        (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') gradient A i
        data.q data.q_le_one).measure = (maskLaw data) ⊗ₘ κ := by
    rw [SDE.euclideanCommonMaskAugmentedHiddenDensity,
      Mf.DP.adaptiveJointProbabilityDensity_measure_eq_compProd,
      SDE.sampledGaussianPoissonMaskBaseDensity_measure_eq]
    rfl
  rw [← hjoint, data.stepKernel_eq_exact]
  exact SDE.euclideanCommonMaskAugmentedHiddenDensity_snd_eq_exact
    _ _ _ _ _ _ hi _ _

end Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture



noncomputable section
open MeasureTheory ProbabilityTheory
open Mf.Probability.SeedTranscript

namespace Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture

theorem commonKernel_actual_laws {n d : ℕ} (data : PrivacyData (n+1) d)
    (A : Finset (Fin (n+1))) (i : Fin (n+1)) (hi : i ∉ A) (T : ℕ) :
    IsMarkovKernel (commonKernel data A i T) ∧
    (iidHistoryLaw (Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
        (1/data.multiplier)) T).bind (commonKernel data A i T) =
      data.transcriptLaw (insert i A) T ∧
    (iidHistoryLaw (gaussianReal 0 1) T).bind (commonKernel data A i T) =
      data.transcriptLaw A T := by
  have hshift : data.clipping/(data.multiplier*data.clipping) = 1/data.multiplier := by
    field_simp [data.multiplier_pos.ne', data.clipping_pos.ne']
  let ν := Mf.DP.GaussianMixtureSimulation.scalarMixture data.q (1/data.multiplier)
  let : IsProbabilityMeasure ν :=
    Mf.DP.GaussianMixtureSimulation.scalarMixture_isProbability
      data.q data.q_le_one (1/data.multiplier)
  refine ⟨commonKernel_isMarkov data A i T, ?_, ?_⟩
  · apply bind_commonKernel_of_rows data A (insert i A) i ν
    intro t h
    simpa only [hshift] using rawRow_mixture_law data A i hi t h
  · exact bind_commonKernel_of_rows data A A i (gaussianReal 0 1)
      (rawRow_zero_law data A i) T

/-- Universal ordered optional-record pair, with raw noisy-sum output.
The same kernel serves both hypotheses for every public finite horizon. -/
theorem optionalTranscript_commonMixtureKernel {n d : ℕ} {Record : Type}
    (data : PrivacyData (n+1) d)
    (g : Record → Vector d → Vector d) (hg : ∀ r, Measurable (g r))
    (D D' : Fin (n+1) → Option Record)
    (hdel : OneRecordDeletion D D') (T : ℕ) :
    ∃ K : Kernel (Fin T → ℝ) (SumHistory d T),
      IsMarkovKernel K ∧
      (iidHistoryLaw (Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
          (1/data.multiplier)) T).bind K = data.optionalTranscriptLaw g hg T D ∧
      (iidHistoryLaw (gaussianReal 0 1) T).bind K =
        data.optionalTranscriptLaw g hg T D' := by
  classical
  rcases hdel with ⟨i,r,hi,hi',hrest⟩
  let localData := data.withSlots g hg D
  let A := Finset.univ.erase i
  have hnot : i ∉ A := Finset.notMem_erase _ _
  have h := commonKernel_actual_laws localData A i hnot T
  have hqLocal : localData.q = data.q := rfl
  have hmultLocal : localData.multiplier = data.multiplier := rfl
  rw [hqLocal, hmultLocal] at h
  refine ⟨commonKernel localData A i T, h.1, ?_, ?_⟩
  · have hinsert : insert i A = Finset.univ := by
      exact Finset.insert_erase (Finset.mem_univ i)
    simpa only [hinsert, optionalTranscriptLaw, localData] using h.2.1
  · have habsent := erased_optional_law data g hg D D' i hi' hrest T
    exact h.2.2.trans habsent

/-- Public corrected-profile parameter V uses multiplier sqrt(V).
The actual normalized noise has coordinate variance C²V/(qN)². -/
theorem optionalTranscript_commonMixtureKernel_variance {n d : ℕ} {Record : Type}
    (data : PrivacyData (n+1) d) (varianceV : ℝ) (_hV : 0 < varianceV)
    (hmult : data.multiplier = Real.sqrt varianceV)
    (g : Record → Vector d → Vector d) (hg : ∀ r, Measurable (g r))
    (D D' : Fin (n+1) → Option Record)
    (hdel : OneRecordDeletion D D') (T : ℕ) :
    ∃ K : Kernel (Fin T → ℝ) (SumHistory d T),
      IsMarkovKernel K ∧
      (iidHistoryLaw (Mf.DP.GaussianMixtureSimulation.scalarMixture data.q
          (1/Real.sqrt varianceV)) T).bind K =
        data.optionalTranscriptLaw g hg T D ∧
      (iidHistoryLaw (gaussianReal 0 1) T).bind K =
        data.optionalTranscriptLaw g hg T D' := by
  simpa only [hmult] using
    optionalTranscript_commonMixtureKernel data g hg D D' hdel T

end Mf.Optimization.PoissonClippedSGD.PrivacyData.ActualMixture
