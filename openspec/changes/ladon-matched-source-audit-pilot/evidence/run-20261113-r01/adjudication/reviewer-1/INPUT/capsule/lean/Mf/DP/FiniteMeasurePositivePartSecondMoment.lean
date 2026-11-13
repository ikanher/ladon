import Mathlib.MeasureTheory.Function.L2Space
import Mathlib.MeasureTheory.Integral.MeanInequalities

/-!
# Positive-part bounds under a finite measure

This owner bounds the integral of a positive part by the zeroth, first, and
second moments under the same finite measure.  Applying it to a restricted
measure preserves the restricted mass instead of introducing a zero-extension
penalty outside the retained event.
-/

open MeasureTheory

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- Finite-measure Cauchy--Schwarz in a form that keeps the total mass. -/
theorem integral_abs_le_sqrt_measureReal_mul_integral_sq
    {X : Type*} [MeasurableSpace X]
    (measure : Measure X) [IsFiniteMeasure measure]
    (value : X → Real)
    (hvalue : AEStronglyMeasurable value measure)
    (hsquare : Integrable (fun sample => value sample ^ 2) measure) :
    (∫ sample, |value sample| ∂measure) ≤
      Real.sqrt (measure.real Set.univ * ∫ sample, value sample ^ 2 ∂measure) := by
  have hone : MemLp (fun _ : X => (1 : Real)) 2 measure :=
    (memLp_two_iff_integrable_sq
      stronglyMeasurable_const.aestronglyMeasurable).2 (integrable_const _)
  have habs : MemLp (fun sample => |value sample|) 2 measure :=
    (memLp_two_iff_integrable_sq hvalue.norm).2
      (by simpa [sq_abs] using hsquare)
  have hholder := integral_mul_le_Lp_mul_Lq_of_nonneg
    (μ := measure) (p := (2 : Real)) (q := (2 : Real))
    Real.HolderConjugate.two_two
    (ae_of_all measure fun _ : X => show 0 ≤ (1 : Real) by norm_num)
    (ae_of_all measure fun sample => abs_nonneg (value sample))
    (by simpa using hone) (by simpa using habs)
  rw [Real.sqrt_mul measureReal_nonneg]
  simpa [Real.sqrt_eq_rpow, sq_abs] using hholder

/-- The coefficient-level positive-part second-moment bound under an arbitrary
finite measure.  The square term is centered at the supplied coefficient. -/
theorem integral_positivePart_le_of_integrable_sq
    {X : Type*} [MeasurableSpace X]
    (measure : Measure X) [IsFiniteMeasure measure]
    (value : X → Real) (coefficient : Real)
    (hvalue : AEStronglyMeasurable value measure)
    (hsquare : Integrable (fun sample => (value sample - coefficient) ^ 2) measure) :
    (∫ sample, max (value sample - coefficient) 0 ∂measure) ≤
      (Real.sqrt (measure.real Set.univ *
          ∫ sample, (value sample - coefficient) ^ 2 ∂measure) +
        (∫ sample, value sample ∂measure) -
          coefficient * measure.real Set.univ) / 2 := by
  let residual : X → Real := fun sample => value sample - coefficient
  have hresidual : AEStronglyMeasurable residual measure :=
    hvalue.sub stronglyMeasurable_const.aestronglyMeasurable
  have hresidualLp : MemLp residual 2 measure :=
    (memLp_two_iff_integrable_sq hresidual).2 hsquare
  have hresidualIntegrable : Integrable residual measure :=
    hresidualLp.integrable (by norm_num)
  have hvalueIntegrable : Integrable value measure := by
    simpa [residual, sub_eq_add_neg] using
      hresidualIntegrable.add (integrable_const coefficient)
  have habs := integral_abs_le_sqrt_measureReal_mul_integral_sq
    measure residual hresidual hsquare
  have hpoint : (fun sample => max (value sample - coefficient) 0) =
      fun sample => (|residual sample| + residual sample) / 2 := by
    funext sample
    by_cases hnonneg : 0 ≤ residual sample
    · rw [max_eq_left]
      · rw [abs_of_nonneg hnonneg]
        ring
      · exact hnonneg
    · have hnonpos : residual sample ≤ 0 := le_of_not_ge hnonneg
      rw [max_eq_right hnonpos, abs_of_nonpos hnonpos]
      ring
  have habsIntegrable : Integrable (fun sample => |residual sample|) measure := by
    simpa [Real.norm_eq_abs] using hresidualIntegrable.norm
  rw [hpoint, integral_div, integral_add habsIntegrable hresidualIntegrable]
  rw [show (∫ sample, residual sample ∂measure) =
      (∫ sample, value sample ∂measure) - coefficient * measure.real Set.univ by
    dsimp [residual]
    rw [integral_sub hvalueIntegrable (integrable_const coefficient), integral_const]
    simp [smul_eq_mul, mul_comm]]
  have habs' : (∫ sample, |residual sample| ∂measure) ≤
      Real.sqrt (measure.real Set.univ *
        ∫ sample, (value sample - coefficient) ^ 2 ∂measure) := by
    simpa [residual] using habs
  linarith

/-- Expanding a square under a finite measure retains the total mass in the
constant term. -/
theorem integral_sub_const_sq_eq
    {X : Type*} [MeasurableSpace X]
    (measure : Measure X) [IsFiniteMeasure measure]
    (value : X → Real) (coefficient : Real)
    (hvalue : Integrable value measure)
    (hvalueSquare : Integrable (fun sample => value sample ^ 2) measure) :
    (∫ sample, (value sample - coefficient) ^ 2 ∂measure) =
    (∫ sample, value sample ^ 2 ∂measure) -
        2 * coefficient * (∫ sample, value sample ∂measure) +
        coefficient ^ 2 * measure.real Set.univ := by
  have hlinear : Integrable (fun sample => 2 * coefficient * value sample) measure :=
    hvalue.const_mul _
  have hconstant : Integrable (fun _ : X => coefficient ^ 2) measure :=
    integrable_const _
  rw [show (fun sample => (value sample - coefficient) ^ 2) = fun sample =>
      value sample ^ 2 - 2 * coefficient * value sample + coefficient ^ 2 by
    funext sample
    ring]
  change (∫ sample,
      ((fun x => value x ^ 2) - (fun x => 2 * coefficient * value x)) sample +
        (fun _ : X => coefficient ^ 2) sample ∂measure) = _
  rw [integral_add (hvalueSquare.sub hlinear) hconstant]
  simp only [Pi.sub_apply]
  rw [integral_sub hvalueSquare hlinear, integral_const_mul, integral_const]
  simp [smul_eq_mul, mul_comm]

/-- The centered square integral is nonnegative. -/
theorem integral_sub_const_sq_nonneg
    {X : Type*} [MeasurableSpace X]
    (measure : Measure X) (value : X → Real) (coefficient : Real) :
    0 ≤ ∫ sample, (value sample - coefficient) ^ 2 ∂measure :=
  integral_nonneg fun _ => sq_nonneg _

end

end Mf.DP
