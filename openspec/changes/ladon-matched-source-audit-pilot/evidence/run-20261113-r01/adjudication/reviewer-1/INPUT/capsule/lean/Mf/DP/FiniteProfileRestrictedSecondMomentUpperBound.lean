import Mf.DP.FiniteMeasurePositivePartSecondMoment
import Mf.DP.LikelihoodRatioHockeyStick

/-!
# Restricted second-moment bounds for a likelihood-ratio profile

This module keeps the profile split generic.  Outside a measurable retained
set, the positive likelihood residual is bounded by the likelihood itself.
Inside the retained set, the finite-measure positive-part inequality preserves
the retained reference mass in the Cauchy--Schwarz factor.
-/

open MeasureTheory Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- A likelihood-ratio hockey-stick profile is the real positive-part integral,
embedded into `ENNReal`. -/
theorem eventHockeyStickProfile_withDensity_forward_eq_ofReal_integral_positivePart
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (epsilon : Real) :
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        (reference : Measure X) epsilon =
      ENNReal.ofReal
        (∫ sample, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X)) := by
  rw [eventHockeyStickProfile_withDensity_forward reference ratio hRatio
    hRatioNonnegative epsilon]
  have hpositiveIntegrable : Integrable
      (fun sample => max (ratio sample - Real.exp epsilon) 0)
      (reference : Measure X) :=
    (hRatioIntegrable.sub (integrable_const _)).pos_part
  have hnonnegative : ∀ᵐ sample ∂(reference : Measure X),
      0 ≤ max (ratio sample - Real.exp epsilon) 0 :=
    ae_of_all _ fun sample => le_max_right _ _
  rw [ofReal_integral_eq_lintegral_ofReal hpositiveIntegrable hnonnegative]
  apply lintegral_congr
  intro sample
  by_cases h : 0 ≤ ratio sample - Real.exp epsilon
  · rw [max_eq_left h]
  · have h' : ratio sample - Real.exp epsilon ≤ 0 := le_of_not_ge h
    rw [max_eq_right h']
    simp [ENNReal.ofReal_of_nonpos h']

/-- Split a likelihood-ratio profile at a measurable retained set and control
the retained residual by its centered second moment. -/
theorem eventHockeyStickProfile_withDensity_forward_le_restrictedSecondMoment
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (retained : Set X) (hRetained : MeasurableSet retained)
    (epsilon : Real)
    (hCenteredSquare : Integrable
      (fun sample => (ratio sample - Real.exp epsilon) ^ 2)
      ((reference : Measure X).restrict retained)) :
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        (reference : Measure X) epsilon ≤
      ENNReal.ofReal
        ((∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X)) +
          (Real.sqrt
              (((reference : Measure X).restrict retained).real Set.univ *
                ∫ sample in retained,
                  (ratio sample - Real.exp epsilon) ^ 2
                    ∂(reference : Measure X)) +
            (∫ sample in retained, ratio sample ∂(reference : Measure X)) -
              Real.exp epsilon *
                ((reference : Measure X).restrict retained).real Set.univ) / 2) := by
  rw [eventHockeyStickProfile_withDensity_forward_eq_ofReal_integral_positivePart
    reference ratio hRatio hRatioNonnegative hRatioIntegrable epsilon]
  apply ENNReal.ofReal_le_ofReal
  have hpositiveIntegrable : Integrable
      (fun sample => max (ratio sample - Real.exp epsilon) 0)
      (reference : Measure X) :=
    (hRatioIntegrable.sub (integrable_const _)).pos_part
  have houtside :
      (∫ sample in retainedᶜ, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X)) ≤
        ∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X) := by
    apply integral_mono_ae
    · exact hpositiveIntegrable.integrableOn
    · exact hRatioIntegrable.integrableOn
    · filter_upwards with sample
      by_cases h : ratio sample - Real.exp epsilon ≤ 0
      · simp [max_eq_right h, hRatioNonnegative sample]
      · rw [max_eq_left (le_of_not_ge h)]
        linarith [Real.exp_pos epsilon]
  letI : IsFiniteMeasure ((reference : Measure X).restrict retained) := by
    infer_instance
  have hinside := integral_positivePart_le_of_integrable_sq
    ((reference : Measure X).restrict retained) ratio (Real.exp epsilon)
    hRatio.aestronglyMeasurable hCenteredSquare
  calc
    (∫ sample, max (ratio sample - Real.exp epsilon) 0
        ∂(reference : Measure X)) =
        (∫ sample in retained, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X)) +
        ∫ sample in retainedᶜ, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X) :=
      (MeasureTheory.integral_add_compl hRetained hpositiveIntegrable).symm
    _ ≤ (Real.sqrt
              (((reference : Measure X).restrict retained).real Set.univ *
                ∫ sample in retained,
                  (ratio sample - Real.exp epsilon) ^ 2
                    ∂(reference : Measure X)) +
            (∫ sample in retained, ratio sample ∂(reference : Measure X)) -
              Real.exp epsilon *
                ((reference : Measure X).restrict retained).real Set.univ) / 2 +
          (∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X)) :=
      add_le_add hinside houtside
    _ = (∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X)) +
        (Real.sqrt
              (((reference : Measure X).restrict retained).real Set.univ *
                ∫ sample in retained,
                  (ratio sample - Real.exp epsilon) ^ 2
                    ∂(reference : Measure X)) +
            (∫ sample in retained, ratio sample ∂(reference : Measure X)) -
              Real.exp epsilon *
                ((reference : Measure X).restrict retained).real Set.univ) / 2 :=
      add_comm _ _

/-- The same restricted bound, capped by the retained likelihood mass. -/
theorem eventHockeyStickProfile_withDensity_forward_le_restrictedSecondMomentCapped
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (retained : Set X) (hRetained : MeasurableSet retained)
    (epsilon : Real)
    (hCenteredSquare : Integrable
      (fun sample => (ratio sample - Real.exp epsilon) ^ 2)
      ((reference : Measure X).restrict retained)) :
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        (reference : Measure X) epsilon ≤
      ENNReal.ofReal
        ((∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X)) +
          min (∫ sample in retained, ratio sample ∂(reference : Measure X))
            ((Real.sqrt
                (((reference : Measure X).restrict retained).real Set.univ *
                  ∫ sample in retained,
                    (ratio sample - Real.exp epsilon) ^ 2
                      ∂(reference : Measure X)) +
              (∫ sample in retained, ratio sample ∂(reference : Measure X)) -
                Real.exp epsilon *
                  ((reference : Measure X).restrict retained).real Set.univ) / 2)) := by
  rw [eventHockeyStickProfile_withDensity_forward_eq_ofReal_integral_positivePart
    reference ratio hRatio hRatioNonnegative hRatioIntegrable epsilon]
  apply ENNReal.ofReal_le_ofReal
  have hpositiveIntegrable : Integrable
      (fun sample => max (ratio sample - Real.exp epsilon) 0)
      (reference : Measure X) :=
    (hRatioIntegrable.sub (integrable_const _)).pos_part
  have hresidualLeRatio : ∀ sample,
      max (ratio sample - Real.exp epsilon) 0 ≤ ratio sample := by
    intro sample
    by_cases h : ratio sample - Real.exp epsilon ≤ 0
    · simp [max_eq_right h, hRatioNonnegative sample]
    · rw [max_eq_left (le_of_not_ge h)]
      linarith [Real.exp_pos epsilon]
  have houtside :
      (∫ sample in retainedᶜ, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X)) ≤
        ∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X) := by
    apply integral_mono_ae hpositiveIntegrable.integrableOn hRatioIntegrable.integrableOn
    exact ae_of_all _ hresidualLeRatio
  have hinsideMass :
      (∫ sample in retained, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X)) ≤
        ∫ sample in retained, ratio sample ∂(reference : Measure X) := by
    apply integral_mono_ae hpositiveIntegrable.integrableOn hRatioIntegrable.integrableOn
    exact ae_of_all _ hresidualLeRatio
  letI : IsFiniteMeasure ((reference : Measure X).restrict retained) := by
    infer_instance
  have hinsideSecond := integral_positivePart_le_of_integrable_sq
    ((reference : Measure X).restrict retained) ratio (Real.exp epsilon)
    hRatio.aestronglyMeasurable hCenteredSquare
  calc
    (∫ sample, max (ratio sample - Real.exp epsilon) 0
        ∂(reference : Measure X)) =
        (∫ sample in retained, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X)) +
        ∫ sample in retainedᶜ, max (ratio sample - Real.exp epsilon) 0
          ∂(reference : Measure X) :=
      (MeasureTheory.integral_add_compl hRetained hpositiveIntegrable).symm
    _ ≤ min (∫ sample in retained, ratio sample ∂(reference : Measure X))
          ((Real.sqrt
              (((reference : Measure X).restrict retained).real Set.univ *
                ∫ sample in retained,
                  (ratio sample - Real.exp epsilon) ^ 2
                    ∂(reference : Measure X)) +
            (∫ sample in retained, ratio sample ∂(reference : Measure X)) -
              Real.exp epsilon *
                ((reference : Measure X).restrict retained).real Set.univ) / 2) +
        (∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X)) :=
      add_le_add (le_min hinsideMass hinsideSecond) houtside
    _ = (∫ sample in retainedᶜ, ratio sample ∂(reference : Measure X)) +
        min (∫ sample in retained, ratio sample ∂(reference : Measure X))
          ((Real.sqrt
              (((reference : Measure X).restrict retained).real Set.univ *
                ∫ sample in retained,
                  (ratio sample - Real.exp epsilon) ^ 2
                    ∂(reference : Measure X)) +
            (∫ sample in retained, ratio sample ∂(reference : Measure X)) -
              Real.exp epsilon *
                ((reference : Measure X).restrict retained).real Set.univ) / 2) :=
      add_comm _ _

end

end Mf.DP
