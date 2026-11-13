import Mf.DP.ApproxDPWeakLimit

/-!
# Exact law-level binary accounting

This module defines the paper-facing binary accounting profile directly as a
supremum over measurable events.  It proves that profile thresholds are
exactly the two ordered approximate-DP law inequalities, and records the
measurable-bijection and event-distance transport facts used later in the
paper.  No numerical accountant or divergence upper bound is involved.
-/

open MeasureTheory Set

namespace Mf.DP

noncomputable section

/-- The exact ordered hockey-stick profile of two laws, expressed in `ENNReal`. -/
def eventHockeyStickProfile
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : Measure Y) (epsilon : Real) : ENNReal :=
  ⨆ s : {s : Set Y // MeasurableSet s},
    mu s.1 - ENNReal.ofReal (Real.exp epsilon) * nu s.1

/-- An ordered event inequality with an `ENNReal` coefficient and slack. -/
def OrderedENNRealLawPair
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : Measure Y) (coefficient slack : ENNReal) : Prop :=
  ∀ s, MeasurableSet s → mu s ≤ coefficient * nu s + slack

/-- The event supremum has the expected threshold characterization in `ENNReal`. -/
theorem eventHockeyStickProfile_le_iff_orderedENNRealLawPair
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : Measure Y) (epsilon : Real) (slack : ENNReal) :
    eventHockeyStickProfile mu nu epsilon ≤ slack ↔
      OrderedENNRealLawPair mu nu (ENNReal.ofReal (Real.exp epsilon)) slack := by
  rw [eventHockeyStickProfile, iSup_le_iff]
  constructor
  · intro h s hs
    have h' := h ⟨s, hs⟩
    rw [tsub_le_iff_right] at h'
    simpa [add_comm] using h'
  · intro h s
    rw [tsub_le_iff_right]
    simpa [OrderedENNRealLawPair, add_comm] using h s.1 s.2

/-- Thresholding the event supremum is exactly the ordered approximate-DP law inequality. -/
theorem eventHockeyStickProfile_le_iff_orderedApproxDPLawPair
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : ProbabilityMeasure Y) (epsilon delta : Real) :
    eventHockeyStickProfile (mu : Measure Y) (nu : Measure Y) epsilon ≤
        ENNReal.ofReal delta ↔
      OrderedApproxDPLawPair mu nu epsilon delta := by
  rw [eventHockeyStickProfile, iSup_le_iff]
  constructor
  · intro h s hs
    have h' := h ⟨s, hs⟩
    rw [tsub_le_iff_right] at h'
    simpa [add_comm] using h'
  · intro h s
    rw [tsub_le_iff_right]
    simpa [add_comm] using h s.1 s.2

/-- Exact two-sided accounting oracle for a binary pair of probability laws. -/
def binaryAccountingProfile
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : ProbabilityMeasure Y) (epsilon : Real) : ENNReal :=
  max
    (eventHockeyStickProfile (mu : Measure Y) (nu : Measure Y) epsilon)
    (eventHockeyStickProfile (nu : Measure Y) (mu : Measure Y) epsilon)

/-- A law compared with itself has zero profile at nonnegative privacy budget. -/
theorem binaryAccountingProfile_self_eq_zero
    {Y : Type*} [MeasurableSpace Y] (mu : ProbabilityMeasure Y)
    (epsilon : Real) (hepsilon : 0 ≤ epsilon) :
    binaryAccountingProfile mu mu epsilon = 0 := by
  have hordered : OrderedENNRealLawPair (mu : Measure Y) (mu : Measure Y)
      (ENNReal.ofReal (Real.exp epsilon)) 0 := by
    intro s hs
    simp only [add_zero]
    have hcoefficient : 1 ≤ ENNReal.ofReal (Real.exp epsilon) := by
      simpa using ENNReal.ofReal_le_ofReal (Real.one_le_exp hepsilon)
    calc
      (mu : Measure Y) s = 1 * (mu : Measure Y) s := by simp
      _ ≤ ENNReal.ofReal (Real.exp epsilon) * (mu : Measure Y) s :=
        mul_le_mul_of_nonneg_right hcoefficient (by exact bot_le)
  have hprofile : eventHockeyStickProfile (mu : Measure Y) (mu : Measure Y)
      epsilon = 0 := by
    apply le_antisymm
    · exact
        (eventHockeyStickProfile_le_iff_orderedENNRealLawPair _ _ _ _).2 hordered
    · exact bot_le
  simp [binaryAccountingProfile, hprofile]

/-- A binary profile threshold is exactly the pair of ordered event inequalities. -/
theorem binaryAccountingProfile_le_iff
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : ProbabilityMeasure Y) (epsilon delta : Real) :
    binaryAccountingProfile mu nu epsilon ≤ ENNReal.ofReal delta ↔
      OrderedApproxDPLawPair mu nu epsilon delta ∧
        OrderedApproxDPLawPair nu mu epsilon delta := by
  simp only [binaryAccountingProfile, max_le_iff,
    eventHockeyStickProfile_le_iff_orderedApproxDPLawPair]

/-- The exact event profile is invariant under a measurable equivalence. -/
theorem eventHockeyStickProfile_map_measurableEquiv
    {Y Z : Type*} [MeasurableSpace Y] [MeasurableSpace Z]
    (e : Y ≃ᵐ Z) (mu nu : Measure Y) (epsilon : Real) :
    eventHockeyStickProfile (Measure.map e mu) (Measure.map e nu) epsilon =
      eventHockeyStickProfile mu nu epsilon := by
  apply le_antisymm
  · rw [eventHockeyStickProfile, iSup_le_iff]
    intro s
    rw [Measure.map_apply e.measurable s.2,
      Measure.map_apply e.measurable s.2]
    exact le_iSup
      (fun t : {t : Set Y // MeasurableSet t} =>
        mu t.1 - ENNReal.ofReal (Real.exp epsilon) * nu t.1)
      ⟨e ⁻¹' s.1, e.measurable s.2⟩
  · rw [eventHockeyStickProfile, iSup_le_iff]
    intro s
    have h := le_iSup
      (fun t : {t : Set Z // MeasurableSet t} =>
        (Measure.map e mu) t.1 -
          ENNReal.ofReal (Real.exp epsilon) * (Measure.map e nu) t.1)
      ⟨e.symm ⁻¹' s.1, e.symm.measurable s.2⟩
    have hmu : (Measure.map e mu) (e.symm ⁻¹' s.1) = mu s.1 := by
      rw [Measure.map_apply e.measurable (e.symm.measurable s.2)]
      congr 1
      ext y
      simp
    have hnu : (Measure.map e nu) (e.symm ⁻¹' s.1) = nu s.1 := by
      rw [Measure.map_apply e.measurable (e.symm.measurable s.2)]
      congr 1
      ext y
      simp
    rw [hmu, hnu] at h
    exact h

/-- Measurable postprocessing cannot increase the exact ordered event profile. -/
theorem eventHockeyStickProfile_map_le
    {Y Z : Type*} [MeasurableSpace Y] [MeasurableSpace Z]
    (f : Y → Z) (hf : Measurable f) (mu nu : Measure Y) (epsilon : Real) :
    eventHockeyStickProfile (Measure.map f mu) (Measure.map f nu) epsilon ≤
      eventHockeyStickProfile mu nu epsilon := by
  rw [eventHockeyStickProfile, iSup_le_iff]
  intro s
  rw [Measure.map_apply hf s.2, Measure.map_apply hf s.2]
  exact le_iSup
    (fun t : {t : Set Y // MeasurableSet t} =>
      mu t.1 - ENNReal.ofReal (Real.exp epsilon) * nu t.1)
    ⟨f ⁻¹' s.1, hf s.2⟩

/-- The binary accounting oracle is unchanged by a measurable bijection. -/
theorem binaryAccountingProfile_map_measurableEquiv
    {Y Z : Type*} [MeasurableSpace Y] [MeasurableSpace Z]
    (e : Y ≃ᵐ Z) (mu nu : ProbabilityMeasure Y) (epsilon : Real) :
    binaryAccountingProfile
        (mu.map e.measurable.aemeasurable)
        (nu.map e.measurable.aemeasurable) epsilon =
      binaryAccountingProfile mu nu epsilon := by
  simp only [binaryAccountingProfile]
  change max
      (eventHockeyStickProfile (Measure.map e (mu : Measure Y))
        (Measure.map e (nu : Measure Y)) epsilon)
      (eventHockeyStickProfile (Measure.map e (nu : Measure Y))
        (Measure.map e (mu : Measure Y)) epsilon) = _
  rw [eventHockeyStickProfile_map_measurableEquiv,
    eventHockeyStickProfile_map_measurableEquiv]

/-- Multiplication by a positive real is the measurable equivalence used for normalization. -/
def positiveScalingEquiv (scale : Real) (hscale : 0 < scale) : Real ≃ᵐ Real :=
  (Homeomorph.mulLeft₀ scale hscale.ne').toMeasurableEquiv

/-- Positive output scaling leaves the exact binary accounting oracle unchanged. -/
theorem binaryAccountingProfile_positiveScaling
    (mu nu : ProbabilityMeasure Real) (epsilon scale : Real)
    (hscale : 0 < scale) :
    binaryAccountingProfile
        (mu.map (positiveScalingEquiv scale hscale).measurable.aemeasurable)
        (nu.map (positiveScalingEquiv scale hscale).measurable.aemeasurable)
        epsilon =
      binaryAccountingProfile mu nu epsilon :=
  binaryAccountingProfile_map_measurableEquiv
    (positiveScalingEquiv scale hscale) mu nu epsilon

/--
Dividing both output laws by a positive sensitivity preserves exact
accounting.  This is the law-level sensitivity/noise exchange used to
normalize the later Gaussian realization.
-/
theorem binaryAccountingProfile_sensitivityNoiseExchange
    (mu nu : ProbabilityMeasure Real) (epsilon sensitivity : Real)
    (hsensitivity : 0 < sensitivity) :
    binaryAccountingProfile
        (mu.map
          (positiveScalingEquiv sensitivity⁻¹
            (inv_pos.mpr hsensitivity)).measurable.aemeasurable)
        (nu.map
          (positiveScalingEquiv sensitivity⁻¹
            (inv_pos.mpr hsensitivity)).measurable.aemeasurable)
        epsilon =
      binaryAccountingProfile mu nu epsilon :=
  binaryAccountingProfile_positiveScaling mu nu epsilon sensitivity⁻¹
    (inv_pos.mpr hsensitivity)

/-- Measurable postprocessing cannot increase the exact binary accounting oracle. -/
theorem binaryAccountingProfile_map_le
    {Y Z : Type*} [MeasurableSpace Y] [MeasurableSpace Z]
    (f : Y → Z) (hf : Measurable f)
    (mu nu : ProbabilityMeasure Y) (epsilon : Real) :
    binaryAccountingProfile
        (mu.map hf.aemeasurable) (nu.map hf.aemeasurable) epsilon ≤
      binaryAccountingProfile mu nu epsilon := by
  apply max_le
  · exact (eventHockeyStickProfile_map_le f hf (mu : Measure Y)
      (nu : Measure Y) epsilon).trans (le_max_left _ _)
  · exact (eventHockeyStickProfile_map_le f hf (nu : Measure Y)
      (mu : Measure Y) epsilon).trans (le_max_right _ _)

/-- Adjoining the same independent probability law cannot increase an ordered profile. -/
theorem eventHockeyStickProfile_prod_right_le
    {X Z : Type*} [MeasurableSpace X] [MeasurableSpace Z]
    (mu nu : ProbabilityMeasure X) (rho : ProbabilityMeasure Z) (epsilon : Real) :
    eventHockeyStickProfile ((mu : Measure X).prod (rho : Measure Z))
        ((nu : Measure X).prod (rho : Measure Z)) epsilon ≤
      eventHockeyStickProfile (mu : Measure X) (nu : Measure X) epsilon := by
  apply (eventHockeyStickProfile_le_iff_orderedENNRealLawPair
    ((mu : Measure X).prod (rho : Measure Z))
    ((nu : Measure X).prod (rho : Measure Z)) epsilon
    (eventHockeyStickProfile (mu : Measure X) (nu : Measure X) epsilon)).2
  have h := (eventHockeyStickProfile_le_iff_orderedENNRealLawPair
    (mu : Measure X) (nu : Measure X) epsilon
    (eventHockeyStickProfile (mu : Measure X) (nu : Measure X) epsilon)).1 (le_refl _)
  intro event hevent
  rw [Measure.prod_apply hevent, Measure.prod_apply hevent]
  apply lintegral_le_of_event_le ENNReal.ofReal_ne_top h
    (measurable_measure_prodMk_left hevent)
  intro x
  exact (measure_mono (Set.subset_univ _)).trans_eq measure_univ

/-- Adjoining one common independent probability law cannot increase exact binary accounting. -/
theorem binaryAccountingProfile_prod_right_le
    {X Z : Type*} [MeasurableSpace X] [MeasurableSpace Z]
    (mu nu : ProbabilityMeasure X) (rho : ProbabilityMeasure Z) (epsilon : Real) :
    binaryAccountingProfile (mu.prod rho) (nu.prod rho) epsilon ≤
      binaryAccountingProfile mu nu epsilon := by
  apply max_le
  · exact (eventHockeyStickProfile_prod_right_le mu nu rho epsilon).trans
      (le_max_left _ _)
  · exact (eventHockeyStickProfile_prod_right_le nu mu rho epsilon).trans
      (le_max_right _ _)

/-- Applying one common randomized measurable map cannot increase exact binary accounting. -/
theorem binaryAccountingProfile_common_randomized_map_le
    {X Z Y : Type*} [MeasurableSpace X] [MeasurableSpace Z] [MeasurableSpace Y]
    (f : X × Z → Y) (hf : Measurable f)
    (mu nu : ProbabilityMeasure X) (rho : ProbabilityMeasure Z) (epsilon : Real) :
    binaryAccountingProfile
        ((mu.prod rho).map hf.aemeasurable)
        ((nu.prod rho).map hf.aemeasurable) epsilon ≤
      binaryAccountingProfile mu nu epsilon := by
  exact (binaryAccountingProfile_map_le f hf (mu.prod rho) (nu.prod rho) epsilon).trans
    (binaryAccountingProfile_prod_right_le mu nu rho epsilon)

/-- Adding the same independent real-valued noise to both laws cannot increase accounting. -/
theorem binaryAccountingProfile_add_common_noise_le
    (mu nu rho : ProbabilityMeasure Real) (epsilon : Real) :
    binaryAccountingProfile
        ((mu.prod rho).map (measurable_fst.add measurable_snd).aemeasurable)
        ((nu.prod rho).map (measurable_fst.add measurable_snd).aemeasurable)
        epsilon ≤ binaryAccountingProfile mu nu epsilon := by
  exact binaryAccountingProfile_common_randomized_map_le
    (fun p : Real × Real => p.1 + p.2) (measurable_fst.add measurable_snd)
    mu nu rho epsilon

/-- Ordered approximate DP itself is invariant under a measurable bijection. -/
theorem orderedApproxDPLawPair_map_measurableEquiv_iff
    {Y Z : Type*} [MeasurableSpace Y] [MeasurableSpace Z]
    (e : Y ≃ᵐ Z) (mu nu : ProbabilityMeasure Y) (epsilon delta : Real) :
    OrderedApproxDPLawPair
        (mu.map e.measurable.aemeasurable)
        (nu.map e.measurable.aemeasurable) epsilon delta ↔
      OrderedApproxDPLawPair mu nu epsilon delta := by
  constructor
  · intro h s hs
    have himage : MeasurableSet (e '' s) := e.measurableSet_image.mpr hs
    have h' := h (e '' s) himage
    simpa [OrderedApproxDPLawPair, e.map_apply] using h'
  · intro h s hs
    have hpre : MeasurableSet (e ⁻¹' s) := hs.preimage e.measurable
    have h' := h (e ⁻¹' s) hpre
    simpa [OrderedApproxDPLawPair, e.map_apply] using h'

/-- Uniform symmetric control of the masses of all measurable events. -/
def UniformEventDistance
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : Measure Y) (d : ENNReal) : Prop :=
  (∀ s, MeasurableSet s → mu s ≤ nu s + d) ∧
    ∀ s, MeasurableSet s → nu s ≤ mu s + d

namespace UniformEventDistance

/-- A measure has zero uniform event distance from itself. -/
theorem refl
    {Y : Type*} [MeasurableSpace Y] (mu : Measure Y) :
    UniformEventDistance mu mu 0 := by
  constructor <;> intro s hs <;> simp

/-- A valid uniform event-distance witness remains valid after enlarging it. -/
theorem mono
    {Y : Type*} [MeasurableSpace Y] {mu nu : Measure Y} {d e : ENNReal}
    (h : UniformEventDistance mu nu d) (hde : d ≤ e) :
    UniformEventDistance mu nu e := by
  constructor
  · intro s hs
    exact (h.1 s hs).trans (add_le_add le_rfl hde)
  · intro s hs
    exact (h.2 s hs).trans (add_le_add le_rfl hde)

/-- Uniform event distance is symmetric by definition. -/
theorem symm
    {Y : Type*} [MeasurableSpace Y] {mu nu : Measure Y} {d : ENNReal}
    (h : UniformEventDistance mu nu d) : UniformEventDistance nu mu d :=
  ⟨h.2, h.1⟩

/-- A measurable equivalence preserves uniform event distance exactly. -/
theorem map_measurableEquiv_iff
    {X Y : Type*} [MeasurableSpace X] [MeasurableSpace Y]
    (e : X ≃ᵐ Y) (mu nu : Measure X) (d : ENNReal) :
    UniformEventDistance (Measure.map e mu) (Measure.map e nu) d ↔
      UniformEventDistance mu nu d := by
  constructor
  · rintro ⟨hforward, hreverse⟩
    constructor
    · intro s hs
      have himage : MeasurableSet (e '' s) := e.measurableSet_image.mpr hs
      simpa [e.map_apply, hs] using hforward (e '' s) himage
    · intro s hs
      have himage : MeasurableSet (e '' s) := e.measurableSet_image.mpr hs
      simpa [e.map_apply, hs] using hreverse (e '' s) himage
  · rintro ⟨hforward, hreverse⟩
    constructor
    · intro s hs
      rw [Measure.map_apply e.measurable hs, Measure.map_apply e.measurable hs]
      exact hforward _ (hs.preimage e.measurable)
    · intro s hs
      rw [Measure.map_apply e.measurable hs, Measure.map_apply e.measurable hs]
      exact hreverse _ (hs.preimage e.measurable)

end UniformEventDistance

/-- The two oriented event errors needed to transport an ordered law bound. -/
theorem OrderedENNRealLawPair.transport_uniformEventDistance
    {Y : Type*} [MeasurableSpace Y]
    {mu nu mu' nu' : Measure Y} {coefficient slack d : ENNReal}
    (h : OrderedENNRealLawPair mu nu coefficient slack)
    (hmu : UniformEventDistance mu mu' d)
    (hnu : UniformEventDistance nu nu' d) :
    OrderedENNRealLawPair mu' nu' coefficient
      (slack + (1 + coefficient) * d) := by
  intro s hs
  calc
    mu' s ≤ mu s + d := hmu.2 s hs
    _ ≤ (coefficient * nu s + slack) + d := by
      gcongr
      exact h s hs
    _ ≤ coefficient * (nu' s + d) + slack + d := by
      gcongr
      exact hnu.1 s hs
    _ = coefficient * nu' s + (slack + (1 + coefficient) * d) := by
      simp [mul_add, add_comm, add_left_comm, add_assoc, mul_comm]

/-- Uniform event distance changes an ordered profile by at most the paper's factor. -/
theorem eventHockeyStickProfile_le_add_of_uniformEventDistance
    {Y : Type*} [MeasurableSpace Y]
    {mu nu mu' nu' : Measure Y} (epsilon : Real) {d : ENNReal}
    (hmu : UniformEventDistance mu mu' d)
    (hnu : UniformEventDistance nu nu' d) :
    eventHockeyStickProfile mu' nu' epsilon ≤
      eventHockeyStickProfile mu nu epsilon +
        (1 + ENNReal.ofReal (Real.exp epsilon)) * d := by
  rw [eventHockeyStickProfile_le_iff_orderedENNRealLawPair]
  exact OrderedENNRealLawPair.transport_uniformEventDistance
    ((eventHockeyStickProfile_le_iff_orderedENNRealLawPair
      mu nu epsilon (eventHockeyStickProfile mu nu epsilon)).mp le_rfl)
    hmu hnu

/-- Symmetric event control bounds the exact binary oracle in both directions. -/
theorem binaryAccountingProfile_stable_uniformEventDistance
    {Y : Type*} [MeasurableSpace Y]
    {mu nu mu' nu' : ProbabilityMeasure Y} (epsilon : Real) {d : ENNReal}
    (hmu : UniformEventDistance (mu : Measure Y) (mu' : Measure Y) d)
    (hnu : UniformEventDistance (nu : Measure Y) (nu' : Measure Y) d) :
    binaryAccountingProfile mu' nu' epsilon ≤
        binaryAccountingProfile mu nu epsilon +
          (1 + ENNReal.ofReal (Real.exp epsilon)) * d ∧
      binaryAccountingProfile mu nu epsilon ≤
        binaryAccountingProfile mu' nu' epsilon +
          (1 + ENNReal.ofReal (Real.exp epsilon)) * d := by
  constructor
  · apply max_le
    · refine (eventHockeyStickProfile_le_add_of_uniformEventDistance epsilon hmu hnu).trans ?_
      gcongr
      exact le_max_left _ _
    · refine (eventHockeyStickProfile_le_add_of_uniformEventDistance epsilon hnu hmu).trans ?_
      gcongr
      exact le_max_right _ _
  · apply max_le
    · refine (eventHockeyStickProfile_le_add_of_uniformEventDistance epsilon
        hmu.symm hnu.symm).trans ?_
      gcongr
      exact le_max_left _ _
    · refine (eventHockeyStickProfile_le_add_of_uniformEventDistance epsilon
        hnu.symm hmu.symm).trans ?_
      gcongr
      exact le_max_right _ _

/--
Uniform event errors on both laws transport ordered approximate DP.  The slack
is the paper's exact `(1 + exp epsilon) * d` factor.
-/
theorem OrderedApproxDPLawPair.transport_uniformEventDistance
    {Y : Type*} [MeasurableSpace Y]
    {mu nu mu' nu' : ProbabilityMeasure Y} {epsilon delta d : Real}
    (hdelta : 0 ≤ delta) (hd : 0 ≤ d)
    (h : OrderedApproxDPLawPair mu nu epsilon delta)
    (hmu : UniformEventDistance (mu : Measure Y) (mu' : Measure Y)
      (ENNReal.ofReal d))
    (hnu : UniformEventDistance (nu : Measure Y) (nu' : Measure Y)
      (ENNReal.ofReal d)) :
    OrderedApproxDPLawPair mu' nu' epsilon
      (delta + (1 + Real.exp epsilon) * d) := by
  intro s hs
  calc
    (mu' : Measure Y) s ≤ (mu : Measure Y) s + ENNReal.ofReal d := hmu.2 s hs
    _ ≤ (ENNReal.ofReal (Real.exp epsilon) * (nu : Measure Y) s +
          ENNReal.ofReal delta) + ENNReal.ofReal d := by
      gcongr
      exact h s hs
    _ ≤ ENNReal.ofReal (Real.exp epsilon) *
          ((nu' : Measure Y) s + ENNReal.ofReal d) +
          ENNReal.ofReal delta + ENNReal.ofReal d := by
      gcongr
      exact hnu.1 s hs
    _ = ENNReal.ofReal (Real.exp epsilon) * (nu' : Measure Y) s +
          ENNReal.ofReal (delta + (1 + Real.exp epsilon) * d) := by
      rw [ENNReal.ofReal_add hdelta
        (mul_nonneg (by positivity : 0 ≤ 1 + Real.exp epsilon) hd)]
      rw [ENNReal.ofReal_mul (by positivity : 0 ≤ 1 + Real.exp epsilon)]
      rw [ENNReal.ofReal_add (by positivity : (0 : Real) ≤ 1)
        (Real.exp_pos epsilon).le]
      simp [mul_add, add_comm, add_left_comm, add_assoc, mul_comm]

end

end Mf.DP
