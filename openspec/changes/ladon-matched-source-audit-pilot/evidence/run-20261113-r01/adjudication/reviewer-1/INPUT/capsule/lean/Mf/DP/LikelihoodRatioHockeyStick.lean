import Mf.DP.LawAccountingOracle

/-!
# Hockey-stick profiles from a likelihood ratio

This module gives exact forward and reverse event hockey-stick profiles for a
law represented by a nonnegative real density over a probability reference.
It also provides the bounded-truncation forms used when likelihood ratios
converge in probability but are not uniformly integrable.
-/

open MeasureTheory Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- The supremum of the positive measure difference is attained on the region
where the first density dominates the second. Only local finiteness of the
second density on that region is needed. -/
theorem iSup_withDensity_tsub_withDensity_eq_lintegral_tsub
    {X : Type*} [MeasurableSpace X]
    (mu : Measure X) (f g : X → ENNReal)
    (hf : Measurable f) (hg : Measurable g)
    (hPositiveRegionFinite :
      lintegral (mu.restrict {x | g x ≤ f x}) g ≠ ⊤) :
    (⨆ s : {s : Set X // MeasurableSet s},
      mu.withDensity f s.1 - mu.withDensity g s.1) =
      ∫⁻ x, f x - g x ∂mu := by
  apply le_antisymm
  · refine iSup_le fun s ↦ ?_
    rw [withDensity_apply _ s.2, withDensity_apply _ s.2]
    calc
      (∫⁻ x in s.1, f x ∂mu) - ∫⁻ x in s.1, g x ∂mu ≤
          ∫⁻ x in s.1, f x - g x ∂mu := lintegral_sub_le g f hg
      _ ≤ ∫⁻ x, f x - g x ∂mu :=
        lintegral_mono' Measure.restrict_le_self le_rfl
  · let positiveRegion : Set X := {x | g x ≤ f x}
    have hPositiveRegion : MeasurableSet positiveRegion := measurableSet_le hg hf
    have hComplementZero :
        ∫⁻ x in positiveRegionᶜ, f x - g x ∂mu = 0 := by
      apply setLIntegral_eq_zero hPositiveRegion.compl
      intro x hx
      exact tsub_eq_zero_of_le (le_of_not_ge hx)
    have hPointwise : g ≤ᵐ[mu.restrict positiveRegion] f :=
      (ae_restrict_mem hPositiveRegion).mono fun _ hx ↦ hx
    have hRestrictFinite : lintegral (mu.restrict positiveRegion) g ≠ ⊤ := by
      simpa [positiveRegion] using hPositiveRegionFinite
    calc
      ∫⁻ x, f x - g x ∂mu = ∫⁻ x in positiveRegion, f x - g x ∂mu := by
        rw [← lintegral_add_compl (fun x ↦ f x - g x) hPositiveRegion,
          hComplementZero, add_zero]
      _ = (∫⁻ x in positiveRegion, f x ∂mu) -
          ∫⁻ x in positiveRegion, g x ∂mu :=
        lintegral_sub hg hRestrictFinite hPointwise
      _ = mu.withDensity f positiveRegion - mu.withDensity g positiveRegion := by
        rw [withDensity_apply _ hPositiveRegion, withDensity_apply _ hPositiveRegion]
      _ ≤ ⨆ s : {s : Set X // MeasurableSet s},
          mu.withDensity f s.1 - mu.withDensity g s.1 :=
        le_iSup (fun s : {s : Set X // MeasurableSet s} ↦
          mu.withDensity f s.1 - mu.withDensity g s.1)
          ⟨positiveRegion, hPositiveRegion⟩

/-- Exact forward hockey-stick profile of a nonnegative likelihood ratio. -/
theorem eventHockeyStickProfile_withDensity_forward
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (_hRatioNonnegative : ∀ x, 0 ≤ ratio x)
    (epsilon : Real) :
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x)))
        (reference : Measure X) epsilon =
      ∫⁻ x, ENNReal.ofReal (ratio x - Real.exp epsilon)
        ∂(reference : Measure X) := by
  let f : X → ENNReal := fun x ↦ ENNReal.ofReal (ratio x)
  let g : X → ENNReal := fun _ ↦ ENNReal.ofReal (Real.exp epsilon)
  have hf : Measurable f := hRatio.ennreal_ofReal
  have hg : Measurable g := measurable_const
  have hPositiveRegionFinite :
      lintegral ((reference : Measure X).restrict {x | g x ≤ f x}) g ≠ ⊤ := by
    apply ne_top_of_le_ne_top (show lintegral (reference : Measure X) g ≠ ⊤ by
      simp [g])
    exact lintegral_mono' Measure.restrict_le_self le_rfl
  calc
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x)))
        (reference : Measure X) epsilon =
        ⨆ s : {s : Set X // MeasurableSet s},
          (reference : Measure X).withDensity f s.1 -
            (reference : Measure X).withDensity g s.1 := by
      unfold eventHockeyStickProfile
      congr 1
      funext s
      simp [f, g, smul_eq_mul]
    _ = ∫⁻ x, f x - g x ∂(reference : Measure X) :=
      iSup_withDensity_tsub_withDensity_eq_lintegral_tsub
        (reference : Measure X) f g hf hg hPositiveRegionFinite
    _ = ∫⁻ x, ENNReal.ofReal (ratio x - Real.exp epsilon)
        ∂(reference : Measure X) := by
      apply lintegral_congr
      intro x
      exact (ENNReal.ofReal_sub (ratio x) (Real.exp_pos epsilon).le).symm

/-- Exact reverse hockey-stick profile of a nonnegative likelihood ratio. -/
theorem eventHockeyStickProfile_withDensity_reverse
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ x, 0 ≤ ratio x)
    (epsilon : Real) :
    eventHockeyStickProfile (reference : Measure X)
        ((reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x)))
        epsilon =
      ∫⁻ x, ENNReal.ofReal (1 - Real.exp epsilon * ratio x)
        ∂(reference : Measure X) := by
  let density : X → ENNReal := fun x ↦ ENNReal.ofReal (ratio x)
  let coefficient : ENNReal := ENNReal.ofReal (Real.exp epsilon)
  let f : X → ENNReal := fun _ ↦ 1
  let g : X → ENNReal := fun x ↦ coefficient * density x
  have hDensity : Measurable density := hRatio.ennreal_ofReal
  have hf : Measurable f := measurable_const
  have hg : Measurable g := measurable_const.mul hDensity
  have hPositiveRegionFinite :
      lintegral ((reference : Measure X).restrict {x | g x ≤ f x}) g ≠ ⊤ := by
    have hPointwise :
        g ≤ᵐ[(reference : Measure X).restrict {x | g x ≤ f x}] f :=
      (ae_restrict_mem (measurableSet_le hg hf)).mono fun _ hx ↦ hx
    apply ne_top_of_le_ne_top (show lintegral (reference : Measure X) f ≠ ⊤ by
      simp [f])
    exact (lintegral_mono_ae hPointwise).trans
      (lintegral_mono' Measure.restrict_le_self le_rfl)
  calc
    eventHockeyStickProfile (reference : Measure X)
        ((reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x)))
        epsilon =
        ⨆ s : {s : Set X // MeasurableSet s},
          (reference : Measure X).withDensity f s.1 -
            (reference : Measure X).withDensity g s.1 := by
      unfold eventHockeyStickProfile
      congr 1
      funext s
      rw [withDensity_apply _ s.2, withDensity_apply _ s.2,
        withDensity_apply _ s.2]
      simp only [f, g, density, coefficient, setLIntegral_one]
      rw [lintegral_const_mul coefficient hDensity]
    _ = ∫⁻ x, f x - g x ∂(reference : Measure X) :=
      iSup_withDensity_tsub_withDensity_eq_lintegral_tsub
        (reference : Measure X) f g hf hg hPositiveRegionFinite
    _ = ∫⁻ x, ENNReal.ofReal (1 - Real.exp epsilon * ratio x)
        ∂(reference : Measure X) := by
      apply lintegral_congr
      intro x
      rw [ENNReal.ofReal_sub 1
        (mul_nonneg (Real.exp_pos epsilon).le (hRatioNonnegative x))]
      rw [ENNReal.ofReal_mul (Real.exp_pos epsilon).le]
      simp [f, g, density, coefficient]

/-- A probability likelihood ratio has unit `lintegral`. -/
theorem likelihoodRatio_lintegral_eq_one
    {X : Type*} [MeasurableSpace X]
    (source reference : ProbabilityMeasure X) (ratio : X → Real)
    (hDensity : (source : Measure X) =
      (reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x))) :
    ∫⁻ x, ENNReal.ofReal (ratio x) ∂(reference : Measure X) = 1 := by
  calc
    ∫⁻ x, ENNReal.ofReal (ratio x) ∂(reference : Measure X) =
        ((reference : Measure X).withDensity
          (fun x ↦ ENNReal.ofReal (ratio x))) Set.univ := by
      rw [withDensity_apply _ MeasurableSet.univ]
      simp
    _ = (source : Measure X) Set.univ := by rw [← hDensity]
    _ = 1 := measure_univ

/-- The forward profile is one minus the bounded truncated likelihood mass. -/
theorem eventHockeyStickProfile_eq_one_sub_integral_min
    {X : Type*} [MeasurableSpace X]
    (source reference : ProbabilityMeasure X) (ratio : X → Real)
    (epsilon : Real) (hRatio : Measurable ratio)
    (hNonnegative : ∀ x, 0 ≤ ratio x)
    (hDensity : (source : Measure X) =
      (reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x))) :
    eventHockeyStickProfile (source : Measure X) (reference : Measure X) epsilon =
      ENNReal.ofReal (1 - ∫ x, min (ratio x) (Real.exp epsilon)
        ∂(reference : Measure X)) := by
  rw [hDensity,
    eventHockeyStickProfile_withDensity_forward reference ratio hRatio hNonnegative]
  let cutoff := Real.exp epsilon
  have hmin_meas : Measurable (fun x ↦ min (ratio x) cutoff) :=
    hRatio.min measurable_const
  have hmin_nonneg : ∀ x, 0 ≤ min (ratio x) cutoff := fun x ↦
    le_min (hNonnegative x) (Real.exp_pos epsilon).le
  have hmin_integrable : Integrable (fun x ↦ min (ratio x) cutoff)
      (reference : Measure X) := by
    refine Integrable.of_bound hmin_meas.aestronglyMeasurable cutoff ?_
    filter_upwards with x
    rw [Real.norm_eq_abs, abs_of_nonneg (hmin_nonneg x)]
    exact min_le_right _ _
  have hmin_lintegral :
      ∫⁻ x, ENNReal.ofReal (min (ratio x) cutoff) ∂(reference : Measure X) =
        ENNReal.ofReal (∫ x, min (ratio x) cutoff ∂(reference : Measure X)) :=
    (ofReal_integral_eq_lintegral_ofReal hmin_integrable
      (ae_of_all _ hmin_nonneg)).symm
  have hpoint : ∀ x, ENNReal.ofReal (ratio x - cutoff) =
      ENNReal.ofReal (ratio x) - ENNReal.ofReal (min (ratio x) cutoff) := by
    intro x
    rw [ENNReal.ofReal_sub (ratio x) (Real.exp_pos epsilon).le]
    rcases le_total (ratio x) cutoff with h | h
    · rw [min_eq_left h]
      change ENNReal.ofReal (ratio x) - ENNReal.ofReal cutoff =
        ENNReal.ofReal (ratio x) - ENNReal.ofReal (ratio x)
      rw [tsub_eq_zero_of_le (ENNReal.ofReal_le_ofReal h), tsub_self]
    · rw [min_eq_right h]
  rw [show (∫⁻ x, ENNReal.ofReal (ratio x - cutoff) ∂(reference : Measure X)) =
      (∫⁻ x, ENNReal.ofReal (ratio x) ∂(reference : Measure X)) -
        ∫⁻ x, ENNReal.ofReal (min (ratio x) cutoff) ∂(reference : Measure X) by
    rw [← lintegral_sub hmin_meas.ennreal_ofReal]
    · apply lintegral_congr
      intro x
      exact hpoint x
    · rw [hmin_lintegral]
      simp
    · filter_upwards with x
      exact ENNReal.ofReal_le_ofReal (min_le_left _ _)]
  rw [likelihoodRatio_lintegral_eq_one source reference ratio hDensity,
    hmin_lintegral, ENNReal.ofReal_sub 1 (integral_nonneg hmin_nonneg)]
  simp

/-- The reverse profile is one minus the exponentially scaled likelihood
truncated at `exp (-epsilon)`. -/
theorem eventHockeyStickProfile_reverse_eq_one_sub_integral_min
    {X : Type*} [MeasurableSpace X]
    (source reference : ProbabilityMeasure X) (ratio : X → Real)
    (epsilon : Real) (hRatio : Measurable ratio)
    (hNonnegative : ∀ x, 0 ≤ ratio x)
    (hDensity : (source : Measure X) =
      (reference : Measure X).withDensity (fun x ↦ ENNReal.ofReal (ratio x))) :
    eventHockeyStickProfile (reference : Measure X) (source : Measure X) epsilon =
      ENNReal.ofReal (1 - Real.exp epsilon *
        ∫ x, min (ratio x) (Real.exp (-epsilon))
          ∂(reference : Measure X)) := by
  rw [hDensity,
    eventHockeyStickProfile_withDensity_reverse reference ratio hRatio hNonnegative]
  let a := Real.exp epsilon
  let cutoff := Real.exp (-epsilon)
  have ha : 0 < a := Real.exp_pos epsilon
  have hcutoff : 0 < cutoff := Real.exp_pos (-epsilon)
  have hac : a * cutoff = 1 := by
    dsimp [a, cutoff]
    rw [← Real.exp_add]
    simp
  let clipped : X → Real := fun x ↦ min (ratio x) cutoff
  have hclipped_meas : Measurable clipped := hRatio.min measurable_const
  have hclipped_nonneg : ∀ x, 0 ≤ clipped x := fun x ↦
    le_min (hNonnegative x) hcutoff.le
  have hclipped_integrable : Integrable clipped (reference : Measure X) := by
    refine Integrable.of_bound hclipped_meas.aestronglyMeasurable cutoff ?_
    filter_upwards with x
    rw [Real.norm_eq_abs, abs_of_nonneg (hclipped_nonneg x)]
    exact min_le_right _ _
  let positivePart : X → Real := fun x ↦ max (1 - a * ratio x) 0
  have hpositive_nonneg : ∀ x, 0 ≤ positivePart x := fun x ↦ le_max_right _ _
  have hpoint : ∀ x, positivePart x = 1 - a * clipped x := by
    intro x
    dsimp [positivePart, clipped]
    rcases le_total (ratio x) cutoff with h | h
    · rw [min_eq_left h, max_eq_left]
      nlinarith [mul_le_mul_of_nonneg_left h ha.le]
    · rw [min_eq_right h, hac, sub_self, max_eq_right]
      nlinarith [mul_le_mul_of_nonneg_left h ha.le]
  have hpositive_integrable : Integrable positivePart (reference : Measure X) := by
    refine (integrable_const 1).sub (hclipped_integrable.const_mul a) |>.congr ?_
    filter_upwards with x
    simp [hpoint]
  rw [show (∫⁻ x, ENNReal.ofReal (1 - Real.exp epsilon * ratio x)
      ∂(reference : Measure X)) =
        ENNReal.ofReal (∫ x, positivePart x ∂(reference : Measure X)) by
    rw [ofReal_integral_eq_lintegral_ofReal hpositive_integrable
      (ae_of_all _ hpositive_nonneg)]
    apply lintegral_congr
    intro x
    simp only [positivePart, a]
    rw [ENNReal.ofReal_max]
    simp]
  rw [integral_congr_ae (ae_of_all _ hpoint), integral_sub,
    integral_const, integral_const_mul]
  · simp [a, clipped, cutoff]
  · exact integrable_const 1
  · exact hclipped_integrable.const_mul a

end

end Mf.DP
