import Mf.Optimization.PoissonClippedSGD.PrivacyTranscript
import Mf.Optimization.PoissonClippedSGD.GaussianReleaseLaw
import Mf.DP.AdaptiveSeedTranscript

/-!
# Equality with the Gaussian SGD process

Independent Bernoulli masks and raw Gaussian coordinates realize the
canonical noisy-sum transcript. Normalizing these same seeds gives the
Gaussian product-history recursion in Algorithm. The final-state pushforward
identity closes this process-law bridge without a supplied law premise.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory ProbabilityTheory
noncomputable section
namespace PrivacyData
variable {n d : ℕ}

/-- Independent mask and raw clipped-sum Gaussian noise. -/
def seedLaw (data : PrivacyData n d) : Measure (AugmentedRelease n d) :=
  (SDE.poissonMaskLaw (Record := Fin n) data.q data.q_le_one).prod
    (SDE.centeredGaussianVectorLaw (Coord := Fin d)
      (SDE.standardClippingVariance data.clipping data.multiplier))

instance (data : PrivacyData n d) : IsProbabilityMeasure data.seedLaw := by
  unfold seedLaw
  infer_instance

def seedRelease (data : PrivacyData n d) (A : Finset (Fin n)) (t : ℕ)
    (z : SumHistory d t × AugmentedRelease n d) : SumRelease d :=
  SDE.euclideanPoissonMaskedClippedSum data.clipping
    (data.rawGradient (data.state t z.1)) A z.2.1 + z.2.2

theorem seedRelease_measurable (data : PrivacyData n d) (A : Finset (Fin n)) (t : ℕ) :
    Measurable (data.seedRelease A t) := by
  have hm : Measurable fun p : SumHistory d t × (Fin n → Bool) =>
      SDE.euclideanPoissonMaskedClippedSum data.clipping
        (data.rawGradient (data.state t p.1)) A p.2 := by
    apply measurable_from_prod_countable_left
    intro mask
    dsimp only
    unfold SDE.euclideanPoissonMaskedClippedSum Mf.DP.l2ClippedFinsetSum
    apply Finset.measurable_fun_sum
    intro i _
    exact (Mf.DP.measurable_l2VectorClip data.clipping).comp
      (f := fun h => data.rawGradient (data.state t h) i)
      ((data.rawGradient_measurable i).comp (data.state_measurable t))
  exact (hm.comp (f := fun z : SumHistory d t × AugmentedRelease n d =>
    (z.1, z.2.1)) (measurable_fst.prodMk (measurable_fst.comp measurable_snd))).add
    (measurable_snd.comp measurable_snd)

theorem seedRelease_law (data : PrivacyData n d) (A : Finset (Fin n))
    (t : ℕ) (h : SumHistory d t) :
    data.seedLaw.map (fun z => data.seedRelease A t (h, z)) = data.stepKernel A t h := by
  rw [data.stepKernel_eq_exact]
  change SDE.euclideanSampledGaussianSumRelease data.clipping data.multiplier
    (data.rawGradient (data.state t h)) A data.q data.q_le_one = _
  exact SDE.euclideanSampledGaussianSumRelease_eq_exact _ _
    (mul_ne_zero data.multiplier_pos.ne' data.clipping_pos.ne') _ _ _ _

def seedTranscript (data : PrivacyData n d) (A : Finset (Fin n)) :=
  Mf.DP.SeedTranscript.encode (data.seedRelease A)

theorem seedTranscript_measurable (data : PrivacyData n d) (A : Finset (Fin n)) (t : ℕ) :
    Measurable (data.seedTranscript A t) :=
  Mf.DP.SeedTranscript.encode_measurable _ (data.seedRelease_measurable A) t

theorem seedTranscript_law (data : PrivacyData n d) (A : Finset (Fin n)) (t : ℕ) :
    (Measure.pi fun _ : Fin t => data.seedLaw).map (data.seedTranscript A t) =
      data.transcriptLaw A t := by
  have h := Mf.DP.SeedTranscript.encode_law data.seedLaw (data.stepKernel A)
    (fun _ => inferInstance)
    (data.seedRelease A) (data.seedRelease_measurable A) (data.seedRelease_law A) t
  have heq : ∀ t, Mf.DP.SeedTranscript.transcriptLaw (data.stepKernel A) t =
      data.transcriptLaw A t := by
    intro t
    induction t with
    | zero => rfl
    | succ t ih =>
        exact congrArg (fun μ => μ ⊗ₘ data.stepKernel A t) ih
  exact h.trans (heq t)

/-- Mask and normalized noise in exactly the units of `gaussianStepLaw`. -/
def normalizedSeed (data : PrivacyData n d) (z : AugmentedRelease n d) :=
  (z.1, Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) z.2))

theorem normalizedSeed_measurable (data : PrivacyData n d) :
    Measurable data.normalizedSeed :=
  measurable_fst.prodMk (Mf.DP.measurable_toEuclidean.comp
    ((SDE.averageRelease_measurable _).comp measurable_snd))

theorem normalizedSeed_law (data : PrivacyData n d) (hd : 0 < d) :
    data.seedLaw.map data.normalizedSeed = gaussianStepLaw n d data.q data.q_le_one
      (normalizedSumNoise n d data.q data.clipping data.multiplier) := by
  have hnoise := averaged_gaussian_coordinate_law n d (data.q : ℝ)
    data.clipping data.multiplier hd
  have hvec : (SDE.centeredGaussianVectorLaw (Coord := Fin d)
      (SDE.standardClippingVariance data.clipping data.multiplier)).map
        (fun z => Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) z)) =
      gaussianVectorLaw d (normalizedSumNoise n d data.q data.clipping data.multiplier) := by
    rw [gaussianVectorLaw, ← hnoise, Measure.map_map Mf.DP.measurable_toEuclidean
      (SDE.averageRelease_measurable _)]
    rfl
  change (data.seedLaw).map (Prod.map id
    (fun z => Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) z))) = _
  unfold seedLaw
  rw [← Measure.map_prod_map (f := id)
    (g := fun z => Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) z))
    _ _ measurable_id (Mf.DP.measurable_toEuclidean.comp (SDE.averageRelease_measurable _)),
    hvec, Measure.map_id]
  rfl

theorem state_seedTranscript (data : PrivacyData n d) (A : Finset (Fin n)) :
    ∀ t (ω : Fin t → AugmentedRelease n d),
      data.state t (data.seedTranscript A t ω) =
        gaussianRun data.eta data.q data.clipping (restrictedGradient data.gradient A)
          data.initial t (fun i => data.normalizedSeed (ω i)) := by
  intro t
  induction t with
  | zero => intro ω; rfl
  | succ t ih =>
    intro ω
    have hadd (a b : SumRelease d) :
        Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) (a + b)) =
        Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) a) +
        Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n) b) := by
      ext k
      simp [Mf.DP.toEuclidean, SDE.averageRelease, add_div]
    change data.state t (data.seedTranscript A t (Fin.tail ω)) - data.eta •
      Mf.DP.toEuclidean (SDE.averageRelease ((data.q : ℝ) * n)
        (data.seedRelease A t (data.seedTranscript A t (Fin.tail ω), ω 0))) = _
    unfold seedRelease
    rw [hadd]
    dsimp only [Prod.fst, Prod.snd, rawGradient]
    unfold rawGradient
    rw [normalized_clipped_sum_eq_sampledGradient (data.q : ℝ) data.clipping
      data.clipping_pos.le data.gradient A (data.state t (data.seedTranscript A t (Fin.tail ω)))
      (ω 0).1]
    rw [ih]
    rfl

/-- Complete law correspondence with the Gaussian product-history optimizer. -/
theorem finalState_law (data : PrivacyData n d) (A : Finset (Fin n)) (hd : 0 < d) (t : ℕ) :
    (data.transcriptLaw A t).map (data.state t) =
      (gaussianHistoryLaw n d t data.q data.q_le_one
        (normalizedSumNoise n d data.q data.clipping data.multiplier)).map
        (gaussianRun data.eta data.q data.clipping (restrictedGradient data.gradient A)
          data.initial t) := by
  have hpi : (Measure.pi fun _ : Fin t => data.seedLaw).map
      (fun ω i => data.normalizedSeed (ω i)) =
      gaussianHistoryLaw n d t data.q data.q_le_one
        (normalizedSumNoise n d data.q data.clipping data.multiplier) := by
    rw [Measure.pi_map_pi (f := fun _ : Fin t => data.normalizedSeed)
      (fun _ => data.normalizedSeed_measurable.aemeasurable)]
    simp only [data.normalizedSeed_law hd]
    rfl
  have hg : ∀ i, Measurable (restrictedGradient data.gradient A i) := by
    intro i
    classical
    by_cases hi : i ∈ A
    · unfold restrictedGradient
      simp only [if_pos hi]
      exact data.gradient_measurable i
    · unfold restrictedGradient
      simp only [if_neg hi]
      exact measurable_const
  have hrun := gaussianRun_measurable data.eta (data.q : ℝ) data.clipping
    data.clipping_pos.le (restrictedGradient data.gradient A) hg data.initial t
  rw [← data.seedTranscript_law A t,
    Measure.map_map (data.state_measurable t) (data.seedTranscript_measurable A t),
    ← hpi, Measure.map_map
      (f := fun (ω : Fin t → AugmentedRelease n d) (i : Fin t) => data.normalizedSeed (ω i))
      (g := gaussianRun data.eta data.q data.clipping
        (restrictedGradient data.gradient A) data.initial t)
      hrun
      (show Measurable (fun (ω : Fin t → AugmentedRelease n d) (i : Fin t) =>
        data.normalizedSeed (ω i)) from
          measurable_pi_lambda _
            (fun i => data.normalizedSeed_measurable.comp (measurable_pi_apply i)))]
  congr 1
  funext ω
  exact data.state_seedTranscript A t ω

end PrivacyData
end
end Mf.Optimization.PoissonClippedSGD
