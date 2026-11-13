import Mf.DP.SampledGaussianOutputLaws
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.Probability.Moments.Variance

/-!
# Exact moments of sampled-Gaussian output sums

This module computes the finite second moments, expectations, and variances of
the semantic source and reference output-sum laws.  The proof first establishes
the one-step Bernoulli-shift and Gaussian-convolution identities, then lifts
them through an independent finite product and the coordinate-sum map.
-/

open MeasureTheory ProbabilityTheory
open scoped BigOperators

namespace Mf.DP

noncomputable section

private theorem bernoulliShiftLaw_memLp
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1) (sensitivity : Real) :
    MemLp (fun x : Real => x) 2
      (bernoulliShiftLaw samplingRate hRate sensitivity : Measure Real) := by
  let shift : Bool → Real := fun selected => if selected then sensitivity else 0
  change MemLp (fun x : Real => x) 2
    ((PMF.map shift (PMF.bernoulli samplingRate hRate)).toMeasure)
  rw [← PMF.toMeasure_map (f := shift) (PMF.bernoulli samplingRate hRate) (by fun_prop)]
  apply (memLp_map_measure_iff (by fun_prop) (by fun_prop)).2
  apply MemLp.of_bound (by fun_prop) |sensitivity|
  filter_upwards [] with selected
  cases selected <;> simp [shift]

private theorem integral_id_bernoulliShiftLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1) (sensitivity : Real) :
    ∫ x, x ∂(bernoulliShiftLaw samplingRate hRate sensitivity : Measure Real) =
      (samplingRate : Real) * sensitivity := by
  let shift : Bool → Real := fun selected => if selected then sensitivity else 0
  change ∫ x, x ∂((PMF.map shift (PMF.bernoulli samplingRate hRate)).toMeasure) = _
  rw [← PMF.toMeasure_map (f := shift) (PMF.bernoulli samplingRate hRate) (by fun_prop),
    integral_map (by fun_prop) (by fun_prop)]
  have hshift : shift = fun b => sensitivity * cond b 1 0 := by
    funext b
    cases b <;> simp [shift]
  rw [hshift, integral_const_mul, PMF.bernoulli_expectation]
  ring

private theorem variance_id_bernoulliShiftLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1) (sensitivity : Real) :
    variance (fun x : Real => x)
      (bernoulliShiftLaw samplingRate hRate sensitivity : Measure Real) =
      (samplingRate : Real) * (1 - (samplingRate : Real)) * sensitivity ^ 2 := by
  let shift : Bool → Real := fun selected => if selected then sensitivity else 0
  have hshiftMem : MemLp shift 2 ((PMF.bernoulli samplingRate hRate).toMeasure) := by
    apply MemLp.of_bound (by fun_prop) |sensitivity|
    filter_upwards [] with selected
    cases selected <;> simp [shift]
  change variance (fun x : Real => x)
    ((PMF.map shift (PMF.bernoulli samplingRate hRate)).toMeasure) = _
  rw [← PMF.toMeasure_map (f := shift) (PMF.bernoulli samplingRate hRate) (by fun_prop)]
  change variance id (Measure.map shift (PMF.bernoulli samplingRate hRate).toMeasure) = _
  rw [variance_id_map (by fun_prop), variance_eq_sub hshiftMem]
  have hmean : ∫ b, shift b ∂(PMF.bernoulli samplingRate hRate).toMeasure =
      (samplingRate : Real) * sensitivity := by
    have hshift : shift = fun b => sensitivity * cond b 1 0 := by
      funext b
      cases b <;> simp [shift]
    rw [hshift, integral_const_mul, PMF.bernoulli_expectation]
    ring
  have hsquare : ∫ b, shift b ^ 2 ∂(PMF.bernoulli samplingRate hRate).toMeasure =
      (samplingRate : Real) * sensitivity ^ 2 := by
    have hshiftSq : (fun b => shift b ^ 2) =
        fun b => sensitivity ^ 2 * cond b 1 0 := by
      funext b
      cases b <;> simp [shift]
    rw [hshiftSq, integral_const_mul, PMF.bernoulli_expectation]
    ring
  change (∫ b, shift b ^ 2 ∂(PMF.bernoulli samplingRate hRate).toMeasure) -
    (∫ b, shift b ∂(PMF.bernoulli samplingRate hRate).toMeasure) ^ 2 = _
  rw [hmean, hsquare]
  ring

private theorem gaussianNoiseLaw_memLp
    (law : ProbabilityMeasure Real) (noiseVariance : NNReal)
    (hmem : MemLp (fun x : Real => x) 2 (law : Measure Real)) :
    MemLp (fun x : Real => x) 2 (gaussianNoiseLaw law noiseVariance : Measure Real) := by
  have hgauss : MemLp (fun x : Real => x) 2
      (ProbabilityTheory.gaussianReal 0 noiseVariance) := by
    exact (ProbabilityTheory.memLp_id_gaussianReal (p := (2 : NNReal))
      (μ := (0 : Real)) (v := noiseVariance)).ae_eq
        (Filter.Eventually.of_forall fun _ => rfl)
  change MemLp (fun x : Real => x) 2
    ((law : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 noiseVariance)
  unfold Measure.conv
  apply (memLp_map_measure_iff (by fun_prop) (by fun_prop)).2
  exact ((hmem.comp_fst (ProbabilityTheory.gaussianReal 0 noiseVariance)).add
    (hgauss.comp_snd (law : Measure Real))).ae_eq
      (Filter.Eventually.of_forall fun _ => rfl)

private theorem integral_id_gaussianNoiseLaw
    (law : ProbabilityMeasure Real) (noiseVariance : NNReal)
    (hmem : MemLp (fun x : Real => x) 2 (law : Measure Real)) :
    ∫ x, x ∂(gaussianNoiseLaw law noiseVariance : Measure Real) =
      ∫ x, x ∂(law : Measure Real) := by
  have hnoiseMem := gaussianNoiseLaw_memLp law noiseVariance hmem
  have hgauss : MemLp (fun x : Real => x) 2
      (ProbabilityTheory.gaussianReal 0 noiseVariance) := by
    exact (ProbabilityTheory.memLp_id_gaussianReal (p := (2 : NNReal))
      (μ := (0 : Real)) (v := noiseVariance)).ae_eq
        (Filter.Eventually.of_forall fun _ => rfl)
  change ∫ x, x ∂((law : Measure Real) ∗
    ProbabilityTheory.gaussianReal 0 noiseVariance) = _
  rw [integral_conv (hnoiseMem.integrable one_le_two)]
  have hinner : ∀ x : Real,
      ∫ y, x + y ∂ProbabilityTheory.gaussianReal 0 noiseVariance = x := by
    intro x
    rw [integral_add (integrable_const x) (hgauss.integrable one_le_two),
      ProbabilityTheory.integral_id_gaussianReal]
    simp
  simp_rw [hinner]

private theorem variance_id_gaussianNoiseLaw
    (law : ProbabilityMeasure Real) (noiseVariance : NNReal)
    (hmem : MemLp (fun x : Real => x) 2 (law : Measure Real)) :
    variance (fun x : Real => x) (gaussianNoiseLaw law noiseVariance : Measure Real) =
      variance (fun x : Real => x) (law : Measure Real) + (noiseVariance : Real) := by
  have hgauss : MemLp (fun x : Real => x) 2
      (ProbabilityTheory.gaussianReal 0 noiseVariance) := by
    exact (ProbabilityTheory.memLp_id_gaussianReal (p := (2 : NNReal))
      (μ := (0 : Real)) (v := noiseVariance)).ae_eq
        (Filter.Eventually.of_forall fun _ => rfl)
  change variance (fun x : Real => x)
    ((law : Measure Real) ∗ ProbabilityTheory.gaussianReal 0 noiseVariance) = _
  unfold Measure.conv
  change variance id (Measure.map (fun p : Real × Real => p.1 + p.2)
    ((law : Measure Real).prod (ProbabilityTheory.gaussianReal 0 noiseVariance))) = _
  rw [variance_id_map (by fun_prop), variance_add_prod hmem hgauss,
    ProbabilityTheory.variance_fun_id_gaussianReal]

private theorem sampledGaussianOneStepSource_memLp
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    MemLp (fun x : Real => x) 2
      (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity noiseVariance :
        Measure Real) :=
  gaussianNoiseLaw_memLp _ _ (bernoulliShiftLaw_memLp samplingRate hRate sensitivity)

private theorem integral_id_sampledGaussianOneStepSourceLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    ∫ x, x ∂(sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity
      noiseVariance : Measure Real) = (samplingRate : Real) * sensitivity := by
  rw [sampledGaussianOneStepSourceLaw,
    integral_id_gaussianNoiseLaw _ _ (bernoulliShiftLaw_memLp samplingRate hRate sensitivity),
    integral_id_bernoulliShiftLaw]

private theorem variance_id_sampledGaussianOneStepSourceLaw
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    variance (fun x : Real => x)
      (sampledGaussianOneStepSourceLaw samplingRate hRate sensitivity noiseVariance :
        Measure Real) =
      (samplingRate : Real) * (1 - (samplingRate : Real)) * sensitivity ^ 2 +
        (noiseVariance : Real) := by
  rw [sampledGaussianOneStepSourceLaw,
    variance_id_gaussianNoiseLaw _ _ (bernoulliShiftLaw_memLp samplingRate hRate sensitivity),
    variance_id_bernoulliShiftLaw]

private theorem finiteSumOutputLaw_pi_memLp
    (horizon : Nat) (law : ProbabilityMeasure Real)
    (hmem : MemLp (fun x : Real => x) 2 (law : Measure Real)) :
    MemLp (fun x : Real => x) 2
      (finiteSumOutputLaw horizon (ProbabilityMeasure.pi fun _ : Fin horizon => law) :
        Measure Real) := by
  let sumFn : (Fin horizon → Real) → Real := fun x => ∑ i, x i
  have hsumEq : sumFn = ∑ i, fun x : Fin horizon → Real => x i := by
    funext x
    simp [sumFn]
  have hsumMem : MemLp sumFn 2 (Measure.pi fun _ : Fin horizon => (law : Measure Real)) :=
    by
      rw [hsumEq]
      exact memLp_finsetSum' Finset.univ (fun i _ =>
        hmem.comp_measurePreserving (measurePreserving_eval (fun _ : Fin horizon =>
          (law : Measure Real)) i))
  change MemLp (fun x : Real => x) 2
    (Measure.map sumFn (Measure.pi fun _ : Fin horizon => (law : Measure Real)))
  exact (memLp_map_measure_iff (by fun_prop) (by fun_prop)).2
    (hsumMem.ae_eq (Filter.Eventually.of_forall fun _ => rfl))

private theorem finiteSumOutputLaw_pi_integral
    (horizon : Nat) (law : ProbabilityMeasure Real)
    (hmem : MemLp (fun x : Real => x) 2 (law : Measure Real)) :
    ∫ x, x ∂(finiteSumOutputLaw horizon (ProbabilityMeasure.pi fun _ : Fin horizon => law) :
      Measure Real) =
      (horizon : Real) * ∫ x, x ∂(law : Measure Real) := by
  let sumFn : (Fin horizon → Real) → Real := fun x => ∑ i, x i
  have hsumEq : sumFn = ∑ i, fun x : Fin horizon → Real => x i := by
    funext x
    simp [sumFn]
  have hcoordMem : ∀ i : Fin horizon,
      MemLp (fun x : Fin horizon → Real => x i) 2
        (Measure.pi fun _ : Fin horizon => (law : Measure Real)) := fun i =>
    hmem.comp_measurePreserving (measurePreserving_eval (fun _ : Fin horizon =>
      (law : Measure Real)) i)
  change ∫ x, x ∂(Measure.map sumFn
    (Measure.pi fun _ : Fin horizon => (law : Measure Real))) = _
  rw [integral_map (by fun_prop) (by fun_prop)]
  rw [integral_finsetSum Finset.univ (fun i _ => (hcoordMem i).integrable one_le_two)]
  have hcoordIntegral : ∀ i : Fin horizon,
      ∫ x, x i ∂(Measure.pi fun _ : Fin horizon => (law : Measure Real)) =
        ∫ x, x ∂(law : Measure Real) := by
    intro i
    have hpres := measurePreserving_eval (fun _ : Fin horizon =>
      (law : Measure Real)) i
    calc
      ∫ x, x i ∂(Measure.pi fun _ : Fin horizon => (law : Measure Real)) =
          ∫ y, y ∂(Measure.map (Function.eval i)
            (Measure.pi fun _ : Fin horizon => (law : Measure Real))) := by
        rw [integral_map hpres.aemeasurable (by fun_prop)]
      _ = ∫ y, y ∂(law : Measure Real) := by rw [hpres.map_eq]
  simp_rw [hcoordIntegral]
  simp

private theorem finiteSumOutputLaw_pi_variance
    (horizon : Nat) (law : ProbabilityMeasure Real)
    (hmem : MemLp (fun x : Real => x) 2 (law : Measure Real)) :
    variance (fun x : Real => x)
      (finiteSumOutputLaw horizon (ProbabilityMeasure.pi fun _ : Fin horizon => law) :
        Measure Real) =
      (horizon : Real) * variance (fun x : Real => x) (law : Measure Real) := by
  let sumFn : (Fin horizon → Real) → Real := fun x => ∑ i, x i
  have hsumEq : sumFn = ∑ i, fun x : Fin horizon → Real => x i := by
    funext x
    simp [sumFn]
  change variance (fun x : Real => x)
    (Measure.map sumFn (Measure.pi fun _ : Fin horizon => (law : Measure Real))) = _
  change variance id (Measure.map sumFn
    (Measure.pi fun _ : Fin horizon => (law : Measure Real))) = _
  rw [variance_id_map (by fun_prop)]
  rw [hsumEq]
  rw [variance_sum_pi (fun _ => hmem)]
  simp

theorem sampledGaussianOutputSumSource_memLp
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    MemLp (fun x : Real => x) 2
      (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
        sensitivity noiseVariance : Measure Real) := by
  rw [sampledGaussianOutputSumSourceLaw, sampledGaussianSourceProductLaw]
  exact finiteSumOutputLaw_pi_memLp _ _
    (sampledGaussianOneStepSource_memLp samplingRate hRate sensitivity noiseVariance)

theorem integral_id_sampledGaussianOutputSumSourceLaw
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    ∫ x, x ∂(sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
      sensitivity noiseVariance : Measure Real) =
      (samplingRate : Real) * sensitivity * (horizon : Real) := by
  rw [sampledGaussianOutputSumSourceLaw, sampledGaussianSourceProductLaw,
    finiteSumOutputLaw_pi_integral _ _
      (sampledGaussianOneStepSource_memLp samplingRate hRate sensitivity noiseVariance),
    integral_id_sampledGaussianOneStepSourceLaw]
  ring

theorem variance_id_sampledGaussianOutputSumSourceLaw
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseVariance : NNReal) :
    variance (fun x : Real => x)
      (sampledGaussianOutputSumSourceLaw horizon samplingRate hRate
        sensitivity noiseVariance : Measure Real) =
      (horizon : Real) *
        ((samplingRate : Real) * (1 - (samplingRate : Real)) * sensitivity ^ 2 +
          (noiseVariance : Real)) := by
  rw [sampledGaussianOutputSumSourceLaw, sampledGaussianSourceProductLaw,
    finiteSumOutputLaw_pi_variance _ _
      (sampledGaussianOneStepSource_memLp samplingRate hRate sensitivity noiseVariance),
    variance_id_sampledGaussianOneStepSourceLaw]

theorem sampledGaussianOutputSumReference_memLp
    (horizon : Nat) (noiseVariance : NNReal) :
    MemLp (fun x : Real => x) 2
      (sampledGaussianOutputSumReferenceLaw horizon noiseVariance : Measure Real) := by
  have href : MemLp (fun x : Real => x) 2
      (sampledGaussianOneStepReferenceLaw noiseVariance : Measure Real) := by
    exact (ProbabilityTheory.memLp_id_gaussianReal (p := (2 : NNReal))
      (μ := (0 : Real)) (v := noiseVariance)).ae_eq
        (Filter.Eventually.of_forall fun _ => rfl)
  rw [sampledGaussianOutputSumReferenceLaw, sampledGaussianReferenceProductLaw]
  exact finiteSumOutputLaw_pi_memLp _ _ href

theorem integral_id_sampledGaussianOutputSumReferenceLaw
    (horizon : Nat) (noiseVariance : NNReal) :
    ∫ x, x ∂(sampledGaussianOutputSumReferenceLaw horizon noiseVariance : Measure Real) = 0 := by
  have href : MemLp (fun x : Real => x) 2
      (sampledGaussianOneStepReferenceLaw noiseVariance : Measure Real) := by
    exact (ProbabilityTheory.memLp_id_gaussianReal (p := (2 : NNReal))
      (μ := (0 : Real)) (v := noiseVariance)).ae_eq
        (Filter.Eventually.of_forall fun _ => rfl)
  rw [sampledGaussianOutputSumReferenceLaw, sampledGaussianReferenceProductLaw,
    finiteSumOutputLaw_pi_integral _ _ href]
  simp [sampledGaussianOneStepReferenceLaw,
    ProbabilityTheory.integral_id_gaussianReal]

theorem variance_id_sampledGaussianOutputSumReferenceLaw
    (horizon : Nat) (noiseVariance : NNReal) :
    variance (fun x : Real => x)
      (sampledGaussianOutputSumReferenceLaw horizon noiseVariance : Measure Real) =
      (horizon : Real) * (noiseVariance : Real) := by
  have href : MemLp (fun x : Real => x) 2
      (sampledGaussianOneStepReferenceLaw noiseVariance : Measure Real) := by
    exact (ProbabilityTheory.memLp_id_gaussianReal (p := (2 : NNReal))
      (μ := (0 : Real)) (v := noiseVariance)).ae_eq
        (Filter.Eventually.of_forall fun _ => rfl)
  rw [sampledGaussianOutputSumReferenceLaw, sampledGaussianReferenceProductLaw,
    finiteSumOutputLaw_pi_variance _ _ href]
  simp [sampledGaussianOneStepReferenceLaw,
    ProbabilityTheory.variance_fun_id_gaussianReal]

end

end Mf.DP
