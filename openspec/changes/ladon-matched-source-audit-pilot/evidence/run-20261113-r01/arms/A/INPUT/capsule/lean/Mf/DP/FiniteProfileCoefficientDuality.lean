import Mf.DP.LikelihoodRatioHockeyStick

/-!
# Coefficient duality for density hockey-stick profiles

The profile is represented in `ENNReal`, so the signed constant `1 - alpha`
must be handled in a real-valued identity before re-embedding with
`ENNReal.ofReal`.  Direct `ENNReal` subtraction would be incorrect when
`alpha > 1`.
-/

open MeasureTheory Set

namespace Mf.DP

noncomputable section

set_option autoImplicit false

def realHockeyStickProfileWithDensity
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real) (coefficient : Real) : Real :=
  ∫ sample, max (ratio sample - coefficient) 0 ∂(reference : Measure X)

def realHockeyStickReverseProfileWithDensity
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real) (coefficient : Real) : Real :=
  ∫ sample, max (1 - coefficient⁻¹ * ratio sample) 0 ∂(reference : Measure X)

theorem realHockeyStickProfileWithDensity_nonneg
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real) (coefficient : Real) :
    0 ≤ realHockeyStickProfileWithDensity reference ratio coefficient := by
  unfold realHockeyStickProfileWithDensity
  exact integral_nonneg fun sample => le_max_right _ _

theorem realHockeyStickReverseProfileWithDensity_nonneg
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real) (coefficient : Real) :
    0 ≤ realHockeyStickReverseProfileWithDensity reference ratio coefficient := by
  unfold realHockeyStickReverseProfileWithDensity
  exact integral_nonneg fun sample => le_max_right _ _

theorem eventHockeyStickProfile_withDensity_forward_eq_ofReal_realProfile
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (epsilon : Real) :
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        (reference : Measure X) epsilon =
      ENNReal.ofReal
        (realHockeyStickProfileWithDensity reference ratio (Real.exp epsilon)) := by
  rw [eventHockeyStickProfile_withDensity_forward reference ratio hRatio
    hRatioNonnegative epsilon]
  change (∫⁻ sample, ENNReal.ofReal (ratio sample - Real.exp epsilon)
      ∂(reference : Measure X)) =
    ENNReal.ofReal (∫ sample, max (ratio sample - Real.exp epsilon) 0
      ∂(reference : Measure X))
  have hpositive : Integrable (fun sample => max (ratio sample - Real.exp epsilon) 0)
      (reference : Measure X) :=
    (hRatioIntegrable.sub (integrable_const _)).pos_part
  rw [ofReal_integral_eq_lintegral_ofReal hpositive
    (ae_of_all _ fun sample => le_max_right _ _)]
  apply lintegral_congr
  intro sample
  rw [ENNReal.ofReal_max,
    ENNReal.ofReal_sub (ratio sample) (Real.exp_pos epsilon).le]
  simpa using (max_eq_left (bot_le : (0 : ENNReal) ≤ _)).symm

theorem realHockeyStickProfileWithDensity_coefficient_duality
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (hRatioIntegral : ∫ sample, ratio sample ∂(reference : Measure X) = 1)
    {coefficient : Real} (hCoefficient : 0 < coefficient) :
    realHockeyStickProfileWithDensity reference ratio coefficient =
      1 - coefficient + coefficient *
        realHockeyStickReverseProfileWithDensity reference ratio coefficient := by
  let reverse : X → Real :=
    fun sample => max (1 - coefficient⁻¹ * ratio sample) 0
  have hreverse : Integrable reverse (reference : Measure X) :=
    ((integrable_const 1).sub
      (hRatioIntegrable.const_mul coefficient⁻¹)).pos_part
  have hforward : Integrable (fun sample => max (ratio sample - coefficient) 0)
      (reference : Measure X) :=
    (hRatioIntegrable.sub (integrable_const _)).pos_part
  have hpoint : ∀ sample, max (ratio sample - coefficient) 0 =
      ratio sample - coefficient + coefficient * reverse sample := by
    intro sample
    dsimp [reverse]
    by_cases hle : coefficient ≤ ratio sample
    · rw [max_eq_left (sub_nonneg.mpr hle), max_eq_right]
      · field_simp
        ring
      · have hscale : 1 ≤ coefficient⁻¹ * ratio sample := by
          calc
            1 = coefficient⁻¹ * coefficient := by field_simp
            _ ≤ coefficient⁻¹ * ratio sample :=
              mul_le_mul_of_nonneg_left hle (inv_nonneg.mpr hCoefficient.le)
        exact sub_nonpos.mpr hscale
    · rw [max_eq_right (sub_nonpos.mpr (le_of_not_ge hle))]
      have hlt : ratio sample < coefficient := lt_of_not_ge hle
      have hscaled : coefficient⁻¹ * ratio sample < 1 := by
        rw [inv_mul_lt_iff₀ hCoefficient]
        simpa using hlt
      rw [max_eq_left (sub_nonneg.mpr hscaled.le)]
      field_simp
      ring
  unfold realHockeyStickProfileWithDensity
  unfold realHockeyStickReverseProfileWithDensity
  calc
    (∫ sample, max (ratio sample - coefficient) 0 ∂(reference : Measure X)) =
        ∫ sample, ratio sample - coefficient + coefficient * reverse sample
          ∂(reference : Measure X) :=
      integral_congr_ae (ae_of_all _ hpoint)
    _ = (∫ sample, ratio sample - coefficient ∂(reference : Measure X)) +
        ∫ sample, coefficient * reverse sample ∂(reference : Measure X) :=
      integral_add (hRatioIntegrable.sub (integrable_const coefficient))
        (hreverse.const_mul coefficient)
    _ = 1 - coefficient + coefficient *
        ∫ sample, reverse sample ∂(reference : Measure X) := by
      rw [integral_sub hRatioIntegrable (integrable_const _), integral_const,
        integral_const_mul, hRatioIntegral]
      simp [Measure.real, measure_univ]

theorem eventHockeyStickProfile_withDensity_reverse_eq_ofReal_realProfile
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    {coefficient : Real} (hCoefficient : 0 < coefficient) :
    eventHockeyStickProfile (reference : Measure X)
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        (-Real.log coefficient) =
      ENNReal.ofReal
        (realHockeyStickReverseProfileWithDensity reference ratio coefficient) := by
  rw [eventHockeyStickProfile_withDensity_reverse reference ratio hRatio
    hRatioNonnegative (-Real.log coefficient)]
  have hexp : Real.exp (-Real.log coefficient) = coefficient⁻¹ := by
    rw [Real.exp_neg, Real.exp_log hCoefficient]
  rw [hexp]
  let reverse : X → Real :=
    fun sample => max (1 - coefficient⁻¹ * ratio sample) 0
  have hreverse : Integrable reverse (reference : Measure X) :=
    ((integrable_const 1).sub
      (hRatioIntegrable.const_mul coefficient⁻¹)).pos_part
  change (∫⁻ sample, ENNReal.ofReal (1 - coefficient⁻¹ * ratio sample)
      ∂(reference : Measure X)) =
    ENNReal.ofReal (∫ sample, reverse sample ∂(reference : Measure X))
  rw [ofReal_integral_eq_lintegral_ofReal hreverse
    (ae_of_all _ fun sample => le_max_right _ _)]
  apply lintegral_congr
  intro sample
  rw [ENNReal.ofReal_max, ENNReal.ofReal_sub]
  · simpa using (max_eq_left (bot_le : (0 : ENNReal) ≤ _)).symm
  · exact mul_nonneg (inv_nonneg.mpr hCoefficient.le) (hRatioNonnegative sample)

/-- Safe coefficient duality for an exact density profile. The signed constant
is evaluated in `Real`, not by truncated `ENNReal` subtraction. -/
theorem eventHockeyStickProfile_withDensity_coefficient_duality
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (hRatioIntegral : ∫ sample, ratio sample ∂(reference : Measure X) = 1)
    {coefficient : Real} (hCoefficient : 0 < coefficient) :
    eventHockeyStickProfile
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        (reference : Measure X) (Real.log coefficient) =
      ENNReal.ofReal
        (1 - coefficient + coefficient *
          (eventHockeyStickProfile (reference : Measure X)
            ((reference : Measure X).withDensity
              (fun sample => ENNReal.ofReal (ratio sample)))
            (-Real.log coefficient)).toReal) := by
  have hforward := eventHockeyStickProfile_withDensity_forward_eq_ofReal_realProfile
    reference ratio hRatio hRatioNonnegative hRatioIntegrable (Real.log coefficient)
  have hreverse := eventHockeyStickProfile_withDensity_reverse_eq_ofReal_realProfile
    reference ratio hRatio hRatioNonnegative hRatioIntegrable hCoefficient
  have hreal := realHockeyStickProfileWithDensity_coefficient_duality reference ratio
    hRatioIntegrable hRatioIntegral hCoefficient
  have hforward' :
      eventHockeyStickProfile
          ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
          (reference : Measure X) (Real.log coefficient) =
        ENNReal.ofReal
          (realHockeyStickProfileWithDensity reference ratio coefficient) := by
    simpa [Real.exp_log hCoefficient] using hforward
  rw [hforward', hreverse]
  rw [ENNReal.toReal_ofReal
    (realHockeyStickReverseProfileWithDensity_nonneg reference ratio coefficient)]
  exact congrArg ENNReal.ofReal hreal

/-- Epsilon-facing reverse duality. This is the form consumed by reciprocal
forward upper bounds. -/
theorem eventHockeyStickProfile_withDensity_reverse_duality
    {X : Type*} [MeasurableSpace X]
    (reference : ProbabilityMeasure X) (ratio : X → Real)
    (hRatio : Measurable ratio) (hRatioNonnegative : ∀ sample, 0 ≤ ratio sample)
    (hRatioIntegrable : Integrable ratio (reference : Measure X))
    (hRatioIntegral : ∫ sample, ratio sample ∂(reference : Measure X) = 1)
    (epsilon : Real) :
    eventHockeyStickProfile (reference : Measure X)
        ((reference : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
        epsilon =
      ENNReal.ofReal
        (1 - Real.exp epsilon + Real.exp epsilon *
          (eventHockeyStickProfile
            ((reference : Measure X).withDensity
              (fun sample => ENNReal.ofReal (ratio sample)))
            (reference : Measure X) (-epsilon)).toReal) := by
  let reciprocalCoefficient : Real := Real.exp (-epsilon)
  have hreciprocalPositive : 0 < reciprocalCoefficient := by
    dsimp [reciprocalCoefficient]
    positivity
  have hreverse := eventHockeyStickProfile_withDensity_reverse_eq_ofReal_realProfile
    reference ratio hRatio hRatioNonnegative hRatioIntegrable hreciprocalPositive
  have hreverse' :
      eventHockeyStickProfile (reference : Measure X)
          ((reference : Measure X).withDensity
            (fun sample => ENNReal.ofReal (ratio sample))) epsilon =
        ENNReal.ofReal
          (realHockeyStickReverseProfileWithDensity reference ratio
            reciprocalCoefficient) := by
    simpa [reciprocalCoefficient] using hreverse
  have hforward := eventHockeyStickProfile_withDensity_forward_eq_ofReal_realProfile
    reference ratio hRatio hRatioNonnegative hRatioIntegrable (-epsilon)
  have hforward' :
      eventHockeyStickProfile
          ((reference : Measure X).withDensity
            (fun sample => ENNReal.ofReal (ratio sample)))
          (reference : Measure X) (-epsilon) =
        ENNReal.ofReal
          (realHockeyStickProfileWithDensity reference ratio reciprocalCoefficient) := by
    simpa [reciprocalCoefficient] using hforward
  have hreal := realHockeyStickProfileWithDensity_coefficient_duality reference ratio
    hRatioIntegrable hRatioIntegral hreciprocalPositive
  have hreciprocal : reciprocalCoefficient = (Real.exp epsilon)⁻¹ := by
    simp [reciprocalCoefficient, Real.exp_neg]
  have hsolve :
      realHockeyStickReverseProfileWithDensity reference ratio reciprocalCoefficient =
        1 - Real.exp epsilon + Real.exp epsilon *
          realHockeyStickProfileWithDensity reference ratio reciprocalCoefficient := by
    rw [hreciprocal] at hreal ⊢
    have hexpNe : Real.exp epsilon ≠ 0 := ne_of_gt (Real.exp_pos epsilon)
    field_simp [hexpNe] at hreal ⊢
    linarith
  rw [hreverse', hforward',
    ENNReal.toReal_ofReal
      (realHockeyStickProfileWithDensity_nonneg reference ratio reciprocalCoefficient)]
  exact congrArg ENNReal.ofReal hsolve

end

end Mf.DP
