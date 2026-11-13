import Mf.DP.SampledGaussianCalibratedStddev
import Mf.DP.Training.Common.ScalarGaussianGlobalThreshold

/-!
# Exact full-batch Gaussian accounting

This module identifies the exact law-level profile of a finite product of
common-covariance Gaussian releases.  It evaluates the likelihood-positive
halfspace directly, then connects the full-sampling product laws to the scalar
Gaussian profile used for calibration.
-/

open MeasureTheory ProbabilityTheory Set

namespace Mf.DP

noncomputable section

private lemma ofReal_measureReal_sub_mul
    {X : Type*} [MeasurableSpace X]
    (mu nu : Measure X) [IsFiniteMeasure mu] [IsFiniteMeasure nu]
    (s : Set X) (c : Real) (hc : 0 ≤ c) :
    ENNReal.ofReal (mu.real s - c * nu.real s) =
      mu s - ENNReal.ofReal c * nu s := by
  rw [ENNReal.ofReal_sub _ (mul_nonneg hc measureReal_nonneg)]
  rw [ENNReal.ofReal_mul hc]
  simp [Measure.real, ENNReal.ofReal_toReal, measure_ne_top]

/-- Exact ordered profile of a nondegenerate centered Gaussian pair. -/
theorem centeredGaussianEventHockeyStickProfile_eq_bridge
    {horizon : Nat} (d : BSROutput horizon) (noiseStddev epsilon radiusSq : Real)
    (hNoise : 0 < noiseStddev) (hRadius : 0 < radiusSq)
    (hRadiusEq : radiusSq = bsrSqDist d (fun _ => 0)) :
    eventHockeyStickProfile (bsrGaussianMeasure noiseStddev d)
        (bsrGaussianMeasure noiseStddev (fun i => -d i)) epsilon =
      ENNReal.ofReal
        (bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon) := by
  let event : Set (BSROutput horizon) :=
    posRegion (fun y => bsrGaussianDensity noiseStddev d y -
      Real.exp epsilon * bsrGaussianDensity noiseStddev (fun i => -d i) y)
  have hevent : MeasurableSet event := by
    exact measurableSet_centered_privacyLoss_posRegion d noiseStddev epsilon hNoise.ne'
  have hgap :
      (bsrGaussianMeasure noiseStddev d).real event -
          Real.exp epsilon *
            (bsrGaussianMeasure noiseStddev (fun i => -d i)).real event =
        bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon := by
    calc
      _ = stdNormalMeasure.real
              (Set.Iic (privacyLossArgPlus
                (2 * Real.sqrt radiusSq) noiseStddev epsilon)) -
            Real.exp epsilon * stdNormalMeasure.real
              (Set.Iic (privacyLossArgMinus
                (2 * Real.sqrt radiusSq) noiseStddev epsilon)) := by
          exact centered_posRegion_gap_eq_explicitEventExpr_two_sqrt
            d radiusSq noiseStddev epsilon hNoise hRadius hRadiusEq
      _ = bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon :=
        explicitEventExpr_two_sqrt_eq_bridgeProfile
          radiusSq noiseStddev epsilon hNoise hRadius
  apply le_antisymm
  · apply (eventHockeyStickProfile_le_iff_orderedENNRealLawPair _ _ _ _).2
    intro s hs
    exact gaussianPair_centered_of_posRegionGap_le d noiseStddev epsilon
      (bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon) hNoise
      (le_of_eq hgap) s hs
  · rw [← hgap]
    rw [ofReal_measureReal_sub_mul _ _ event (Real.exp epsilon)
      (le_of_lt (Real.exp_pos epsilon))]
    exact le_iSup_of_le ⟨event, hevent⟩ (le_refl _)

/-- Exact two-sided profile of a nondegenerate centered Gaussian pair. -/
theorem centeredGaussianBinaryProfile_eq_bridge
    {horizon : Nat} (d : BSROutput horizon) (noiseStddev epsilon radiusSq : Real)
    (hNoise : 0 < noiseStddev) (hRadius : 0 < radiusSq)
    (hRadiusEq : radiusSq = bsrSqDist d (fun _ => 0)) :
    binaryAccountingProfile
        ⟨bsrGaussianMeasure noiseStddev d, by infer_instance⟩
        ⟨bsrGaussianMeasure noiseStddev (fun i => -d i), by infer_instance⟩ epsilon =
      ENNReal.ofReal
        (bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon) := by
  have hforward := centeredGaussianEventHockeyStickProfile_eq_bridge
    d noiseStddev epsilon radiusSq hNoise hRadius hRadiusEq
  have hreverse :
      eventHockeyStickProfile (bsrGaussianMeasure noiseStddev (fun i => -d i))
        (bsrGaussianMeasure noiseStddev d) epsilon =
        ENNReal.ofReal
          (bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon) := by
    let negEquiv : BSROutput horizon ≃ᵐ BSROutput horizon :=
      MeasurableEquiv.neg (BSROutput horizon)
    have hmapD : Measure.map negEquiv (bsrGaussianMeasure noiseStddev d) =
        bsrGaussianMeasure noiseStddev (fun i => -d i) := by
      change Measure.map (fun x i => -x i) (bsrGaussianMeasure noiseStddev d) = _
      exact bsrGaussianMeasure_map_neg noiseStddev d
    have hmapNegD : Measure.map negEquiv
          (bsrGaussianMeasure noiseStddev (fun i => -d i)) =
        bsrGaussianMeasure noiseStddev d := by
      change Measure.map (fun x i => -x i)
        (bsrGaussianMeasure noiseStddev (fun i => -d i)) = _
      simpa only [neg_neg] using
        bsrGaussianMeasure_map_neg noiseStddev (fun i => -d i)
    calc
      _ = eventHockeyStickProfile
          (Measure.map negEquiv
            (bsrGaussianMeasure noiseStddev (fun i => -d i)))
          (Measure.map negEquiv (bsrGaussianMeasure noiseStddev d)) epsilon := by
            exact
              (eventHockeyStickProfile_map_measurableEquiv negEquiv _ _ _).symm
      _ = eventHockeyStickProfile (bsrGaussianMeasure noiseStddev d)
          (bsrGaussianMeasure noiseStddev (fun i => -d i)) epsilon := by
            rw [hmapNegD, hmapD]
      _ = _ := hforward
  change max
      (eventHockeyStickProfile (bsrGaussianMeasure noiseStddev d)
        (bsrGaussianMeasure noiseStddev (fun i => -d i)) epsilon)
      (eventHockeyStickProfile (bsrGaussianMeasure noiseStddev (fun i => -d i))
        (bsrGaussianMeasure noiseStddev d) epsilon) = _
  rw [hforward, hreverse, max_self]

/-- At sampling rate one the Bernoulli shift is deterministic. -/
theorem sampledGaussianOneStepSourceLaw_one_eq_gaussian
    (sensitivity : Real) (noiseVariance : NNReal) :
    sampledGaussianOneStepSourceLaw 1 (by norm_num) sensitivity noiseVariance =
      ⟨gaussianReal sensitivity noiseVariance, by infer_instance⟩ := by
  apply Subtype.ext
  change (sampledGaussianOneStepSourceLaw 1 (by norm_num) sensitivity noiseVariance :
    Measure Real) = gaussianReal sensitivity noiseVariance
  rw [sampledGaussianOneStepSourceLaw_eq_gaussianMixture]
  simp [ENNReal.coe_sub]

/-- At sampling rate one the source product is a shifted Gaussian product. -/
theorem sampledGaussianSourceProductLaw_one_eq_gaussianProduct
    (horizon : Nat) (sensitivity : Real) (noiseVariance : NNReal) :
    sampledGaussianSourceProductLaw horizon 1 (by norm_num) sensitivity noiseVariance =
      ProbabilityMeasure.pi (fun _ =>
        ⟨gaussianReal sensitivity noiseVariance, by infer_instance⟩) := by
  apply Subtype.ext
  change Measure.pi (fun _ : Fin horizon =>
      (sampledGaussianOneStepSourceLaw 1 (by norm_num) sensitivity noiseVariance :
        Measure Real)) = _
  congr 1
  funext i
  exact congrArg Subtype.val
    (sampledGaussianOneStepSourceLaw_one_eq_gaussian sensitivity noiseVariance)

/-- Euclidean signal norm accumulated by a full-batch Gaussian product. -/
def fullBatchGaussianSignal (horizon : Nat) (sensitivity : Real) : Real :=
  sensitivity * Real.sqrt horizon

/-- A shifted constant-mean Gaussian product has the exact ordered scalar profile. -/
theorem bsrConstantGaussianEventHockeyStickProfile_eq_scalar
    (horizon : Nat) (sensitivity noiseStddev epsilon : Real)
    (horizon_pos : 0 < horizon) (sensitivity_pos : 0 < sensitivity)
    (noise_pos : 0 < noiseStddev) :
    eventHockeyStickProfile
        (bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => sensitivity))
        (bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => 0)) epsilon =
      ENNReal.ofReal (Training.scalarGaussianSigmaProfile
        (fullBatchGaussianSignal horizon sensitivity) epsilon noiseStddev) := by
  let d : BSROutput horizon := fun _ => sensitivity / 2
  let radiusSq : Real := (horizon : Real) * (sensitivity / 2) ^ 2
  have hradius : 0 < radiusSq := by
    dsimp [radiusSq]
    positivity
  have hradiusEq : radiusSq = bsrSqDist d (fun _ => 0) := by
    simp [radiusSq, d, bsrSqDist, Probability.FiniteGaussian.sqDist]
  let centeredSource : Measure (BSROutput horizon) :=
    bsrGaussianMeasure noiseStddev d
  let centeredReference : Measure (BSROutput horizon) :=
    bsrGaussianMeasure noiseStddev (fun i => -d i)
  let shiftEquiv : BSROutput horizon ≃ᵐ BSROutput horizon :=
    MeasurableEquiv.addRight d
  have hsourceMap : Measure.map shiftEquiv centeredSource =
      bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => sensitivity) := by
    change Measure.map (fun x : BSROutput horizon => x + d)
        (bsrGaussianMeasure noiseStddev d) = _
    rw [show (fun x : BSROutput horizon => x + d) =
        (fun x => fun i => x i + d i) by rfl]
    rw [bsrGaussianMeasure_map_add_const]
    congr 1
    funext i
    simp [d]
  have hrefMap : Measure.map shiftEquiv centeredReference =
      bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => 0) := by
    change Measure.map (fun x : BSROutput horizon => x + d)
        (bsrGaussianMeasure noiseStddev (fun i => -d i)) = _
    rw [show (fun x : BSROutput horizon => x + d) =
        (fun x => fun i => x i + d i) by rfl]
    rw [bsrGaussianMeasure_map_add_const]
    congr 1
    funext i
    simp
  calc
    _ = eventHockeyStickProfile (Measure.map shiftEquiv centeredSource)
        (Measure.map shiftEquiv centeredReference) epsilon := by
          rw [hsourceMap, hrefMap]
    _ = eventHockeyStickProfile centeredSource centeredReference epsilon :=
      eventHockeyStickProfile_map_measurableEquiv shiftEquiv _ _ epsilon
    _ = ENNReal.ofReal (bridgeProfile (Real.sqrt radiusSq / noiseStddev) epsilon) :=
      centeredGaussianEventHockeyStickProfile_eq_bridge d noiseStddev epsilon radiusSq
        noise_pos hradius hradiusEq
    _ = _ := by
      apply congrArg ENNReal.ofReal
      unfold Training.scalarGaussianSigmaProfile
      rw [gdpProfile_eq_bridgeProfile_of_ne]
      · apply congrArg (fun x => bridgeProfile x epsilon)
        have hsqrt : Real.sqrt radiusSq =
            sensitivity / 2 * Real.sqrt (horizon : Real) := by
          rw [show radiusSq = (sensitivity / 2) ^ 2 * (horizon : Real) by
            simp [radiusSq]
            ring]
          rw [Real.sqrt_mul (sq_nonneg (sensitivity / 2))]
          rw [Real.sqrt_sq (le_of_lt (div_pos sensitivity_pos (by norm_num)))]
        rw [hsqrt]
        simp [fullBatchGaussianSignal]
        field_simp
      · exact div_ne_zero
          (mul_ne_zero sensitivity_pos.ne'
            (Real.sqrt_ne_zero'.mpr (by exact_mod_cast horizon_pos)))
          noise_pos.ne'

/-- Exact ordered profile of a one-dimensional shifted Gaussian law. -/
theorem gaussianShiftEventHockeyStickProfile_eq_scalar
    (sensitivity noiseStddev epsilon : Real)
    (sensitivity_pos : 0 < sensitivity) (noise_pos : 0 < noiseStddev) :
    eventHockeyStickProfile
        (gaussianReal sensitivity ⟨noiseStddev ^ 2, sq_nonneg noiseStddev⟩)
        (gaussianReal 0 ⟨noiseStddev ^ 2, sq_nonneg noiseStddev⟩) epsilon =
      ENNReal.ofReal
        (Training.scalarGaussianSigmaProfile sensitivity epsilon noiseStddev) := by
  let source : Measure (Fin 1 → Real) :=
    bsrGaussianMeasure noiseStddev (fun _ => sensitivity)
  let reference : Measure (Fin 1 → Real) :=
    bsrGaussianMeasure noiseStddev (fun _ => 0)
  let e : (Fin 1 → Real) ≃ᵐ Real := MeasurableEquiv.funUnique (Fin 1) Real
  have heval : (e : (Fin 1 → Real) → Real) = Function.eval 0 := by
    funext sample
    simp [e, MeasurableEquiv.funUnique]
  have hsource : Measure.map e source =
      gaussianReal sensitivity ⟨noiseStddev ^ 2, sq_nonneg noiseStddev⟩ := by
    rw [Measure.map_congr (Filter.Eventually.of_forall fun sample =>
      congrFun heval sample)]
    convert bsrGaussianMeasure_map_eval
      noiseStddev (fun _ : Fin 1 => sensitivity) 0 using 1
    rw [bsrGaussianVariance_eq_mk]
  have hreference : Measure.map e reference =
      gaussianReal 0 ⟨noiseStddev ^ 2, sq_nonneg noiseStddev⟩ := by
    rw [Measure.map_congr (Filter.Eventually.of_forall fun sample =>
      congrFun heval sample)]
    convert bsrGaussianMeasure_map_eval
      noiseStddev (fun _ : Fin 1 => 0) 0 using 1
    rw [bsrGaussianVariance_eq_mk]
  calc
    _ = eventHockeyStickProfile (Measure.map e source) (Measure.map e reference)
        epsilon := by rw [hsource, hreference]
    _ = eventHockeyStickProfile source reference epsilon :=
      eventHockeyStickProfile_map_measurableEquiv e source reference epsilon
    _ = ENNReal.ofReal (Training.scalarGaussianSigmaProfile
          (fullBatchGaussianSignal 1 sensitivity) epsilon noiseStddev) := by
      exact bsrConstantGaussianEventHockeyStickProfile_eq_scalar 1 sensitivity
        noiseStddev epsilon (by norm_num) sensitivity_pos noise_pos
    _ = _ := by simp [fullBatchGaussianSignal]

/-- Reversing an equal-variance one-dimensional Gaussian shift preserves its ordered profile. -/
theorem gaussianShiftEventHockeyStickProfiles_eq
    (sensitivity : Real) (noiseVariance : NNReal) (epsilon : Real) :
    eventHockeyStickProfile
        (gaussianReal sensitivity noiseVariance)
        (gaussianReal 0 noiseVariance) epsilon =
      eventHockeyStickProfile
        (gaussianReal 0 noiseVariance)
        (gaussianReal sensitivity noiseVariance) epsilon := by
  let e : Real ≃ᵐ Real :=
    (MeasurableEquiv.neg Real).trans (MeasurableEquiv.addRight sensitivity)
  have hsource : Measure.map e
      (gaussianReal sensitivity noiseVariance) =
      gaussianReal 0 noiseVariance := by
    change Measure.map (fun x : Real => -x + sensitivity)
      (gaussianReal sensitivity noiseVariance) = _
    have hfun : (fun x : Real => -x + sensitivity) =
        (fun x => sensitivity - x) := by
      funext x
      ring
    rw [hfun, gaussianReal_map_const_sub]
    norm_num
  have hreference : Measure.map e
      (gaussianReal 0 noiseVariance) =
      gaussianReal sensitivity noiseVariance := by
    change Measure.map (fun x : Real => -x + sensitivity)
      (gaussianReal 0 noiseVariance) = _
    have hfun : (fun x : Real => -x + sensitivity) =
        (fun x => sensitivity - x) := by
      funext x
      ring
    rw [hfun, gaussianReal_map_const_sub]
    norm_num
  calc
    _ = eventHockeyStickProfile
        (Measure.map e
          (gaussianReal sensitivity noiseVariance))
        (Measure.map e
          (gaussianReal 0 noiseVariance)) epsilon :=
      (eventHockeyStickProfile_map_measurableEquiv e _ _ _).symm
    _ = _ := by rw [hsource, hreference]

/-- A shifted constant-mean Gaussian product has the exact scalar Gaussian profile. -/
theorem bsrConstantGaussianBinaryProfile_eq_scalar
    (horizon : Nat) (sensitivity noiseStddev epsilon : Real)
    (horizon_pos : 0 < horizon) (sensitivity_pos : 0 < sensitivity)
    (noise_pos : 0 < noiseStddev) :
    binaryAccountingProfile
        ⟨bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => sensitivity),
          by infer_instance⟩
        ⟨bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => 0),
          by infer_instance⟩ epsilon =
      ENNReal.ofReal (Training.scalarGaussianSigmaProfile
        (fullBatchGaussianSignal horizon sensitivity) epsilon noiseStddev) := by
  let d : BSROutput horizon := fun _ => sensitivity / 2
  let radiusSq : Real := (horizon : Real) * (sensitivity / 2) ^ 2
  have hradius : 0 < radiusSq := by
    dsimp [radiusSq]
    positivity
  have hradiusEq : radiusSq = bsrSqDist d (fun _ => 0) := by
    simp [radiusSq, d, bsrSqDist, Probability.FiniteGaussian.sqDist]
  let centeredSource : ProbabilityMeasure (BSROutput horizon) :=
    ⟨bsrGaussianMeasure noiseStddev d, by infer_instance⟩
  let centeredReference : ProbabilityMeasure (BSROutput horizon) :=
    ⟨bsrGaussianMeasure noiseStddev (fun i => -d i), by infer_instance⟩
  let shiftEquiv : BSROutput horizon ≃ᵐ BSROutput horizon :=
    MeasurableEquiv.addRight d
  have hsourceMap : centeredSource.map shiftEquiv.measurable.aemeasurable =
      ⟨bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => sensitivity),
        by infer_instance⟩ := by
    apply Subtype.ext
    change Measure.map (fun x : BSROutput horizon => x + d)
        (bsrGaussianMeasure noiseStddev d) = _
    rw [show (fun x : BSROutput horizon => x + d) =
        (fun x => fun i => x i + d i) by rfl]
    rw [bsrGaussianMeasure_map_add_const]
    congr 1
    funext i
    simp [d]
  have hrefMap : centeredReference.map shiftEquiv.measurable.aemeasurable =
      ⟨bsrGaussianMeasure noiseStddev (fun _ : Fin horizon => 0),
        by infer_instance⟩ := by
    apply Subtype.ext
    change Measure.map (fun x : BSROutput horizon => x + d)
        (bsrGaussianMeasure noiseStddev (fun i => -d i)) = _
    rw [show (fun x : BSROutput horizon => x + d) =
        (fun x => fun i => x i + d i) by rfl]
    rw [bsrGaussianMeasure_map_add_const]
    congr 1
    funext i
    simp
  have hcenter := centeredGaussianBinaryProfile_eq_bridge d noiseStddev epsilon
    radiusSq noise_pos hradius hradiusEq
  have htranslated := binaryAccountingProfile_map_measurableEquiv shiftEquiv
    centeredSource centeredReference epsilon
  rw [hsourceMap, hrefMap] at htranslated
  rw [htranslated, hcenter]
  apply congrArg ENNReal.ofReal
  unfold Training.scalarGaussianSigmaProfile
  rw [gdpProfile_eq_bridgeProfile_of_ne]
  · apply congrArg (fun x => bridgeProfile x epsilon)
    have hsqrt : Real.sqrt radiusSq =
        sensitivity / 2 * Real.sqrt (horizon : Real) := by
      rw [show radiusSq = (sensitivity / 2) ^ 2 * (horizon : Real) by
        simp [radiusSq]
        ring]
      rw [Real.sqrt_mul (sq_nonneg (sensitivity / 2))]
      rw [Real.sqrt_sq (le_of_lt (div_pos sensitivity_pos (by norm_num)))]
    rw [hsqrt]
    simp [fullBatchGaussianSignal]
    field_simp
  · exact div_ne_zero
      (mul_ne_zero sensitivity_pos.ne'
        (Real.sqrt_ne_zero'.mpr (by exact_mod_cast horizon_pos)))
      noise_pos.ne'

/-- The full-sampling product accountant is exactly the scalar Gaussian profile. -/
theorem sampledGaussianProductProfileStddev_one_eq_scalar
    (horizon : Nat) (sensitivity : Real) (noiseStddev : NNReal) (epsilon : Real)
    (horizon_pos : 0 < horizon) (sensitivity_pos : 0 < sensitivity)
    (noise_pos : 0 < noiseStddev) :
    sampledGaussianProductProfileStddev horizon 1 (by norm_num) sensitivity
        noiseStddev epsilon =
      ENNReal.ofReal (Training.scalarGaussianSigmaProfile
        (fullBatchGaussianSignal horizon sensitivity) epsilon noiseStddev) := by
  unfold sampledGaussianProductProfileStddev
  rw [sampledGaussianSourceProductLaw_one_eq_gaussianProduct]
  change binaryAccountingProfile
      ⟨bsrGaussianMeasure (noiseStddev : Real)
        (fun _ : Fin horizon => sensitivity), by infer_instance⟩
      ⟨bsrGaussianMeasure (noiseStddev : Real)
        (fun _ : Fin horizon => 0), by infer_instance⟩ epsilon = _
  exact bsrConstantGaussianBinaryProfile_eq_scalar horizon sensitivity noiseStddev epsilon
    horizon_pos sensitivity_pos (by exact_mod_cast noise_pos)

/-- Every zero-horizon sampled product profile is zero at nonnegative epsilon. -/
theorem sampledGaussianProductProfileStddev_zero_horizon
    (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (sensitivity : Real) (noiseStddev : NNReal) (epsilon : Real)
    (epsilon_nonneg : 0 ≤ epsilon) :
    sampledGaussianProductProfileStddev 0 samplingRate hRate sensitivity
      noiseStddev epsilon = 0 := by
  unfold sampledGaussianProductProfileStddev
  have hlaws : sampledGaussianSourceProductLaw 0 samplingRate hRate sensitivity
      (noiseStddev ^ 2) = sampledGaussianReferenceProductLaw 0 (noiseStddev ^ 2) := by
    apply Subtype.ext
    ext s hs
    by_cases h : s.Nonempty
    · have hsuniv : s = Set.univ := by
        apply Set.eq_univ_of_forall
        intro x
        rcases h with ⟨y, hy⟩
        simpa [Subsingleton.elim x y] using hy
      simp [hsuniv]
    · rw [Set.not_nonempty_iff_eq_empty.mp h]
      simp
  rw [hlaws]
  exact binaryAccountingProfile_self_eq_zero _ epsilon epsilon_nonneg

/-- The positive one-step scalar Gaussian calibration used at every horizon. -/
def fullBatchGaussianBaseStddev
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) : Real :=
  Training.scalarGaussianOptimalSigma sensitivity epsilon delta
    sensitivity_pos epsilon_nonneg delta_pos delta_lt_one

/-- Scalar Gaussian calibration is positively homogeneous in the sensitivity.
The dimensionless signal-to-noise ratio is therefore independent of the
chosen positive sensitivity normalization. -/
theorem fullBatchGaussianBaseStddev_scale
    (sensitivity epsilon delta : Real)
    (hSensitivity : 0 < sensitivity) (hEpsilon : 0 ≤ epsilon)
    (hDeltaPos : 0 < delta) (hDeltaLtOne : delta < 1) :
    fullBatchGaussianBaseStddev sensitivity epsilon delta hSensitivity hEpsilon
        hDeltaPos hDeltaLtOne =
      sensitivity * fullBatchGaussianBaseStddev 1 epsilon delta (by norm_num)
        hEpsilon hDeltaPos hDeltaLtOne := by
  let unitBase := fullBatchGaussianBaseStddev 1 epsilon delta (by norm_num)
    hEpsilon hDeltaPos hDeltaLtOne
  have hUnitSpec := Training.scalarGaussianOptimalSigma_spec
    (show (0 : Real) < 1 by norm_num) hEpsilon hDeltaPos hDeltaLtOne
  have hCandidatePos : 0 < sensitivity * unitBase := by
    exact mul_pos hSensitivity (by
      simpa [unitBase, fullBatchGaussianBaseStddev] using hUnitSpec.1)
  have hCandidateProfile :
      Training.scalarGaussianSigmaProfile sensitivity epsilon
          (sensitivity * unitBase) = delta := by
    unfold Training.scalarGaussianSigmaProfile
    rw [show sensitivity / (sensitivity * unitBase) = 1 / unitBase by
      field_simp [hSensitivity.ne', hCandidatePos.ne']]
    simpa [Training.scalarGaussianSigmaProfile, unitBase,
      fullBatchGaussianBaseStddev] using hUnitSpec.2
  have hUnique := Training.existsUnique_scalarGaussianSigma_profile_eq
    hSensitivity hEpsilon hDeltaPos hDeltaLtOne
  have hBaseSpec := Training.scalarGaussianOptimalSigma_spec
    hSensitivity hEpsilon hDeltaPos hDeltaLtOne
  have hEq := hUnique.unique hBaseSpec ⟨hCandidatePos, hCandidateProfile⟩
  simpa [fullBatchGaussianBaseStddev, unitBase] using hEq

/-- Exact full-batch calibration, exhibiting the square-root horizon law. -/
def fullBatchGaussianCalibratedStddev
    (horizon : Nat) (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) : NNReal :=
  ⟨fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos epsilon_nonneg
      delta_pos delta_lt_one * Real.sqrt horizon,
    mul_nonneg
      (le_of_lt (Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
        delta_pos delta_lt_one).1)
      (Real.sqrt_nonneg _)⟩

@[simp] theorem fullBatchGaussianCalibratedStddev_coe
    (horizon : Nat) (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    (fullBatchGaussianCalibratedStddev horizon sensitivity epsilon delta
        sensitivity_pos epsilon_nonneg delta_pos delta_lt_one : Real) =
      fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
        epsilon_nonneg delta_pos delta_lt_one * Real.sqrt horizon := rfl

/-- The square-root calibrated standard deviation attains the exact target profile. -/
theorem fullBatchGaussianCalibratedStddev_profile_eq
    (horizon : Nat) (sensitivity epsilon delta : Real)
    (horizon_pos : 0 < horizon)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1) :
    sampledGaussianProductProfileStddev horizon 1 (by norm_num) sensitivity
      (fullBatchGaussianCalibratedStddev horizon sensitivity epsilon delta
        sensitivity_pos epsilon_nonneg delta_pos delta_lt_one) epsilon =
      ENNReal.ofReal delta := by
  let base := fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
    epsilon_nonneg delta_pos delta_lt_one
  have hbase : 0 < base :=
    (Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
      delta_pos delta_lt_one).1
  have hsqrt : 0 < Real.sqrt (horizon : Real) :=
    Real.sqrt_pos.2 (by exact_mod_cast horizon_pos)
  have hnoise : 0 < fullBatchGaussianCalibratedStddev horizon sensitivity epsilon delta
      sensitivity_pos epsilon_nonneg delta_pos delta_lt_one := by
    exact_mod_cast mul_pos hbase hsqrt
  rw [sampledGaussianProductProfileStddev_one_eq_scalar horizon sensitivity _ epsilon
    horizon_pos sensitivity_pos hnoise]
  apply congrArg ENNReal.ofReal
  have hspec := (Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
    delta_pos delta_lt_one).2
  change Training.scalarGaussianSigmaProfile
      (sensitivity * Real.sqrt horizon) epsilon (base * Real.sqrt horizon) = delta
  unfold Training.scalarGaussianSigmaProfile
  rw [show sensitivity * Real.sqrt horizon / (base * Real.sqrt horizon) =
      sensitivity / base by field_simp]
  simpa [Training.scalarGaussianSigmaProfile, base, fullBatchGaussianBaseStddev]
    using hspec

/-- The positive full-batch standard deviation attaining `delta` is unique. -/
theorem fullBatchGaussianCalibratedStddev_unique
    (horizon : Nat) (sensitivity epsilon delta : Real)
    (horizon_pos : 0 < horizon)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta) (delta_lt_one : delta < 1)
    (noiseStddev : NNReal) (noise_pos : 0 < noiseStddev)
    (hprofile : sampledGaussianProductProfileStddev horizon 1 (by norm_num)
      sensitivity noiseStddev epsilon = ENNReal.ofReal delta) :
    noiseStddev = fullBatchGaussianCalibratedStddev horizon sensitivity epsilon delta
      sensitivity_pos epsilon_nonneg delta_pos delta_lt_one := by
  rw [sampledGaussianProductProfileStddev_one_eq_scalar horizon sensitivity
    noiseStddev epsilon horizon_pos sensitivity_pos noise_pos] at hprofile
  have hscalarPos : 0 < Training.scalarGaussianSigmaProfile
      (fullBatchGaussianSignal horizon sensitivity) epsilon noiseStddev := by
    apply ENNReal.ofReal_pos.mp
    rw [hprofile]
    exact ENNReal.ofReal_pos.mpr delta_pos
  have hscalar : Training.scalarGaussianSigmaProfile
      (fullBatchGaussianSignal horizon sensitivity) epsilon noiseStddev = delta :=
    (ENNReal.ofReal_eq_ofReal_iff (le_of_lt hscalarPos) (le_of_lt delta_pos)).mp
      hprofile
  let root : Real := (noiseStddev : Real) / Real.sqrt horizon
  have hsqrt : 0 < Real.sqrt (horizon : Real) :=
    Real.sqrt_pos.2 (by exact_mod_cast horizon_pos)
  have hrootPos : 0 < root := div_pos (by exact_mod_cast noise_pos) hsqrt
  have hrootProfile : Training.scalarGaussianSigmaProfile sensitivity epsilon root = delta := by
    unfold Training.scalarGaussianSigmaProfile at hscalar ⊢
    rw [show sensitivity / root =
        fullBatchGaussianSignal horizon sensitivity / (noiseStddev : Real) by
      simp [root, fullBatchGaussianSignal]
      field_simp]
    exact hscalar
  have hbaseUnique := Training.existsUnique_scalarGaussianSigma_profile_eq
    sensitivity_pos epsilon_nonneg delta_pos delta_lt_one
  have hrootEq := hbaseUnique.unique ⟨hrootPos, hrootProfile⟩
    (Training.scalarGaussianOptimalSigma_spec sensitivity_pos epsilon_nonneg
      delta_pos delta_lt_one)
  unfold fullBatchGaussianCalibratedStddev fullBatchGaussianBaseStddev
  apply NNReal.eq
  change (noiseStddev : Real) =
    Training.scalarGaussianOptimalSigma sensitivity epsilon delta sensitivity_pos
      epsilon_nonneg delta_pos delta_lt_one * Real.sqrt horizon
  exact calc
    (noiseStddev : Real) = root * Real.sqrt horizon := by
      dsimp [root]
      field_simp
    _ = Training.scalarGaussianOptimalSigma sensitivity epsilon delta sensitivity_pos
        epsilon_nonneg delta_pos delta_lt_one * Real.sqrt horizon :=
      congrArg (fun x : Real => x * Real.sqrt horizon) hrootEq

end

end Mf.DP
