import Mf.Optimization.PoissonClippedSGD.MixtureTranscript
import Mf.Probability.FiniteHistoryEquivalence
import Mf.DP.PoissonGaussianProductProfile
/-!
# Exact product benchmark attained by an actual bounded query

One public slot and one coordinate, clipping one, constant record query one,
and multiplier sqrt(V) produce raw releases Bernoulli(q)+N(0,V). Deleting the
record produces N(0,V). Both full transcript laws are identified under an
explicit measurable equivalence, so their two-direction profile equals the
protected product benchmark at every finite horizon and epsilon.

The fixed public qN normalization remains in the state recursion; a constant
query makes the release law independent of that state. This is a bounded-query
attainment witness, not a lower-bounded optimization example. Together with
the universal common-simulator upper bound, it identifies the worst-case
full-transcript benchmark of the generic-bound proof response r01, Section 2.
-/
noncomputable section
open MeasureTheory ProbabilityTheory Mf.DP
namespace Mf.Optimization.PoissonClippedSGD
namespace ProductAttainment

def constantQueryData (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (V : NNReal) (hV : 0 < V) : PrivacyData 1 1 where
  q := q
  q_pos := hq0
  q_le_one := hq
  clipping := 1
  clipping_pos := by norm_num
  multiplier := Real.sqrt V
  multiplier_pos := Real.sqrt_pos.mpr hV
  eta := 1
  initial := 0
  gradient := fun _ _ => Mf.DP.toEuclidean (fun _ => 1)
  gradient_measurable := fun _ => measurable_const

theorem present_row (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (V : NNReal) (hV : 0 < V)
    (t : ℕ) (h : SumHistory 1 t) (z : AugmentedRelease 1 1) :
    (constantQueryData q hq hq0 V hV).seedRelease Finset.univ t (h,z) 0 =
      (if z.1 0 then 1 else 0)+z.2 0 := by
  cases hz : z.1 0 <;> simp [hz, Finset.sum_filter, PrivacyData.seedRelease, SDE.euclideanPoissonMaskedClippedSum,
    l2ClippedFinsetSum, PrivacyData.rawGradient, constantQueryData, Mf.DP.toEuclidean,
    l2VectorClip, l2Norm, EuclideanSpace.norm_eq]

theorem variance_eq (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (V : NNReal) (hV : 0 < V) :
    SDE.standardClippingVariance (constantQueryData q hq hq0 V hV).clipping
      (constantQueryData q hq hq0 V hV).multiplier = V := by
  apply Subtype.ext
  simp [constantQueryData,SDE.standardClippingVariance,Real.sq_sqrt V.coe_nonneg]

theorem seed_scalar_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (V : NNReal) (hV : 0 < V) :
    ((constantQueryData q hq hq0 V hV).seedLaw).map
      (fun z => ((if z.1 0 then (1 : ℝ) else 0),z.2 0)) =
      (bernoulliShiftLaw q hq 1 : Measure ℝ).prod (gaussianReal 0 V) := by
  have hm : (SDE.poissonMaskLaw (Record := Fin 1) q hq).map
      (fun a => if a 0 then (1 : ℝ) else 0) = (bernoulliShiftLaw q hq 1 : Measure ℝ) := by
    change _ = (PMF.map (fun b : Bool => if b then (1 : ℝ) else 0) (PMF.bernoulli q hq)).toMeasure
    rw [← PMF.toMeasure_map (f := fun b : Bool => if b then (1 : ℝ) else 0) (PMF.bernoulli q hq) (measurable_of_finite _)]
    have he := (measurePreserving_eval (μ := fun _ : Fin 1 => (PMF.bernoulli q hq).toMeasure) 0).map_eq
    rw [← he, Measure.map_map (by fun_prop) (by fun_prop)]
    rfl
  have hn : (SDE.centeredGaussianVectorLaw (Coord := Fin 1) V).map
      (fun z => z 0) = gaussianReal 0 V :=
    (measurePreserving_eval (μ := fun _ : Fin 1 => gaussianReal 0 V) 0).map_eq
  rw [PrivacyData.seedLaw,variance_eq]
  change ((SDE.poissonMaskLaw (Record := Fin 1) q hq).prod
    (SDE.centeredGaussianVectorLaw (Coord := Fin 1) V)).map
      (Prod.map (fun a => if a 0 then (1 : ℝ) else 0) (fun z => z 0)) = _
  rw [← Measure.map_prod_map _ _ (by fun_prop) (by fun_prop),hm,hn]

theorem present_row_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q) (V : NNReal) (hV : 0 < V) :
    ((constantQueryData q hq hq0 V hV).seedLaw).map
      (fun z => (if z.1 0 then (1 : ℝ) else 0)+z.2 0) =
      (sampledGaussianOneStepSourceLaw q hq 1 V : Measure ℝ) := by
  change _ = ((bernoulliShiftLaw q hq 1 : Measure ℝ).prod (gaussianReal 0 V)).map
    (fun z => z.1+z.2)
  have hm : Measurable (fun z : AugmentedRelease 1 1 =>
      ((if z.1 0 then (1 : ℝ) else 0),z.2 0)) :=
    ((measurable_of_finite (fun a : Fin 1 → Bool => if a 0 then (1 : ℝ) else 0)).comp
      measurable_fst).prodMk ((measurable_pi_apply 0).comp measurable_snd)
  rw [← seed_scalar_law q hq hq0 V hV, Measure.map_map (by fun_prop) hm]
  rfl

def scalarCoordinates (T : ℕ) (h : SumHistory 1 T) : Fin T → ℝ :=
  fun i => Mf.Probability.SeedTranscript.coordinates T h i 0

theorem scalarCoordinates_measurable (T : ℕ) : Measurable (scalarCoordinates T) := by
  apply measurable_pi_lambda
  intro i
  exact (measurable_pi_apply 0).comp ((measurable_pi_apply i).comp
    (Mf.Probability.SeedTranscript.coordinates_measurable T))

theorem scalar_coordinates_law (p : PrivacyData 1 1) (A : Finset (Fin 1))
    (f : AugmentedRelease 1 1 → ℝ) (hf : Measurable f)
    (hrow : ∀ t h z, p.seedRelease A t (h,z) 0 = f z) (T : ℕ) :
    (p.transcriptLaw A T).map (scalarCoordinates T) =
      Measure.pi (fun _ : Fin T => p.seedLaw.map f) := by
  let fv : AugmentedRelease 1 1 → SumRelease 1 := fun z _ => f z
  have hfv : Measurable fv := measurable_pi_lambda _ (fun _ => hf)
  have hr : p.seedRelease A = (fun _ z => fv z.2) := by
    funext t z k
    have hk : k = 0 := Subsingleton.elim _ _
    subst k
    exact hrow t z.1 z.2
  rw [← p.seedTranscript_law A T]
  have hc := Mf.Probability.SeedTranscript.coordinates_encode_fresh_law
    p.seedLaw hfv T
  unfold Mf.Probability.SeedTranscript.iidHistoryLaw at hc
  change ((Measure.pi (fun _ : Fin T => p.seedLaw)).map
    (Mf.Probability.SeedTranscript.encode (p.seedRelease A) T)).map _ = _
  rw [hr]
  have hcomp : scalarCoordinates T =
      (fun a : Fin T → SumRelease 1 => fun i => a i 0) ∘
        Mf.Probability.SeedTranscript.coordinates T := rfl
  rw [hcomp,← Measure.map_map (by fun_prop)
    (Mf.Probability.SeedTranscript.coordinates_measurable T),hc]
  change (Measure.pi (fun _ : Fin T => p.seedLaw.map fv)).map
    (fun a i => a i 0) = _
  rw [Measure.pi_map_pi (fun _ => (measurable_pi_apply 0).aemeasurable)]
  congr 1
  funext i
  rw [Measure.map_map (measurable_pi_apply 0) hfv]
  rfl

theorem present_transcript_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) (T : ℕ) :
    ((constantQueryData q hq hq0 V hV).transcriptLaw Finset.univ T).map (scalarCoordinates T) =
      (sampledGaussianSourceProductLaw T q hq 1 V : Measure (Fin T → ℝ)) := by
  have hf : Measurable (fun z : AugmentedRelease 1 1 =>
      (if z.1 0 then (1 : ℝ) else 0)+z.2 0) :=
    ((measurable_of_finite (fun a : Fin 1 → Bool => if a 0 then (1 : ℝ) else 0)).comp
      measurable_fst).add ((measurable_pi_apply 0).comp measurable_snd)
  rw [scalar_coordinates_law _ _ _ hf (present_row q hq hq0 V hV) T,
    present_row_law]
  rfl

theorem absent_row_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) :
    ((constantQueryData q hq hq0 V hV).seedLaw).map (fun z => z.2 0) = gaussianReal 0 V := by
  rw [PrivacyData.seedLaw,variance_eq]
  have hn := (measurePreserving_eval (μ := fun _ : Fin 1 => gaussianReal 0 V) 0).map_eq
  have hp := (measurePreserving_snd
    (μ := SDE.poissonMaskLaw (Record := Fin 1) q hq)
    (ν := SDE.centeredGaussianVectorLaw (Coord := Fin 1) V)).map_eq
  change ((SDE.poissonMaskLaw (Record := Fin 1) q hq).prod
    (SDE.centeredGaussianVectorLaw (Coord := Fin 1) V)).map
      ((fun z : SumRelease 1 => z 0) ∘ Prod.snd) = _
  rw [← Measure.map_map (measurable_pi_apply 0) measurable_snd,hp]
  exact hn

theorem absent_transcript_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) (T : ℕ) :
    ((constantQueryData q hq hq0 V hV).transcriptLaw ∅ T).map (scalarCoordinates T) =
      (sampledGaussianReferenceProductLaw T V : Measure (Fin T → ℝ)) := by
  have hr : ∀ t h z, (constantQueryData q hq hq0 V hV).seedRelease ∅ t (h,z) 0 = z.2 0 := by
    intros
    simp [PrivacyData.seedRelease,SDE.euclideanPoissonMaskedClippedSum,l2ClippedFinsetSum]
  rw [scalar_coordinates_law _ _ _ (by fun_prop) hr T,absent_row_law]
  rfl

def scalarEquiv (T : ℕ) : SumHistory 1 T ≃ᵐ (Fin T → ℝ) :=
  (Mf.Probability.SeedTranscript.coordinatesEquiv T).trans
    (MeasurableEquiv.piCongrRight (fun _ : Fin T => MeasurableEquiv.funUnique (Fin 1) ℝ))

theorem scalarEquiv_apply (T : ℕ) : (scalarEquiv T : SumHistory 1 T → (Fin T → ℝ)) =
    scalarCoordinates T := by
  rfl

theorem transcript_profile_eq (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) (T : ℕ) (ε : ℝ) :
    (max
      (eventHockeyStickProfile ((constantQueryData q hq hq0 V hV).transcriptLaw Finset.univ T)
        ((constantQueryData q hq hq0 V hV).transcriptLaw ∅ T) ε)
      (eventHockeyStickProfile ((constantQueryData q hq hq0 V hV).transcriptLaw ∅ T)
        ((constantQueryData q hq hq0 V hV).transcriptLaw Finset.univ T) ε)).toReal =
      PoissonGaussianProductProfile.profile T q hq V ε := by
  have hf := eventHockeyStickProfile_map_measurableEquiv (scalarEquiv T)
    ((constantQueryData q hq hq0 V hV).transcriptLaw Finset.univ T)
    ((constantQueryData q hq hq0 V hV).transcriptLaw ∅ T) ε
  have hr := eventHockeyStickProfile_map_measurableEquiv (scalarEquiv T)
    ((constantQueryData q hq hq0 V hV).transcriptLaw ∅ T)
    ((constantQueryData q hq hq0 V hV).transcriptLaw Finset.univ T) ε
  rw [scalarEquiv_apply,present_transcript_law,absent_transcript_law] at hf hr
  rw [← hf,← hr]
  rfl

def query (_ : Unit) (_ : EuclideanSpace ℝ (Fin 1)) : EuclideanSpace ℝ (Fin 1) :=
  Mf.DP.toEuclidean (fun _ => 1)

theorem query_measurable : ∀ r, Measurable (query r) := fun _ => measurable_const

theorem query_norm (r : Unit) (x : EuclideanSpace ℝ (Fin 1)) : ‖query r x‖ = 1 := by
  simp [query,Mf.DP.toEuclidean,EuclideanSpace.norm_eq]

def present : Fin 1 → Option Unit := fun _ => some ()
def absent : Fin 1 → Option Unit := fun _ => none

theorem datasets_adjacent : OneRecordDeletion present absent := by
  refine ⟨0,(),rfl,rfl,?_⟩
  intro j hj
  exact False.elim (hj (Subsingleton.elim _ _))

theorem optional_present_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) (T : ℕ) :
    (constantQueryData q hq hq0 V hV).optionalTranscriptLaw query query_measurable T present =
      (constantQueryData q hq hq0 V hV).transcriptLaw Finset.univ T := rfl

theorem optional_absent_law (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) (T : ℕ) :
    (constantQueryData q hq hq0 V hV).optionalTranscriptLaw query query_measurable T absent =
      (constantQueryData q hq hq0 V hV).transcriptLaw ∅ T := by
  apply (constantQueryData q hq hq0 V hV).transcriptLaw_withQueries_eq
    (fun _ _ => 0) (fun _ _ => Mf.DP.toEuclidean (fun _ => 1))
    (fun _ => measurable_const) (fun _ => measurable_const) Finset.univ ∅ _ T
  intro x mask
  ext k
  simp [SDE.euclideanPoissonMaskedClippedSum,l2ClippedFinsetSum,l2VectorClip,l2Norm,
    Mf.DP.toEuclidean, constantQueryData, EuclideanSpace.norm_eq]

theorem optional_transcript_profile_eq (q : NNReal) (hq : q ≤ 1) (hq0 : 0 < q)
    (V : NNReal) (hV : 0 < V) (T : ℕ) (ε : ℝ) :
    (max
      (eventHockeyStickProfile
        ((constantQueryData q hq hq0 V hV).optionalTranscriptLaw query query_measurable T present)
        ((constantQueryData q hq hq0 V hV).optionalTranscriptLaw query query_measurable T absent) ε)
      (eventHockeyStickProfile
        ((constantQueryData q hq hq0 V hV).optionalTranscriptLaw query query_measurable T absent)
        ((constantQueryData q hq hq0 V hV).optionalTranscriptLaw query query_measurable T present) ε)).toReal =
      PoissonGaussianProductProfile.profile T q hq V ε := by
  rw [optional_present_law,optional_absent_law]
  exact transcript_profile_eq q hq hq0 V hV T ε
end ProductAttainment
end Mf.Optimization.PoissonClippedSGD
