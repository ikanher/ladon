import Mathlib

namespace Mf
namespace DP

noncomputable section

open scoped BigOperators

/--
Positive region of a real-valued function; this is the maximizing event in the
privacy-loss argument.
-/
def posRegion {α : Type} (f : α → ℝ) : Set α := {x | 0 ≤ f x}

theorem integral_restrict_le_integral_posRegion
    {α : Type}
    [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {f : α → ℝ}
    (hf_meas : Measurable f)
    (hf_int : MeasureTheory.Integrable f μ)
    (s : Set α)
    (hs : MeasurableSet s) :
    (∫ x in s, f x ∂μ) ≤ ∫ x in posRegion f, f x ∂μ := by
  simpa [posRegion] using
    (MeasureTheory.setIntegral_le_nonneg hs hf_meas.stronglyMeasurable hf_int)

/--
One direction of the privacy-loss characterization:
if the privacy-loss integral on its positive region is bounded by `δ`, then every
measurable event satisfies the corresponding DP inequality.
-/
theorem dp_event_bound_of_privacyLossSet
    {α : Type}
    [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    (p q : α → ℝ)
    (ε δ : ℝ)
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_int : MeasureTheory.Integrable p μ)
    (hq_int : MeasureTheory.Integrable q μ)
    (hpos :
      (∫ x in posRegion (fun x => p x - Real.exp ε * q x),
          (p x - Real.exp ε * q x) ∂μ) ≤ δ) :
    ∀ s, MeasurableSet s →
      (∫ x in s, p x ∂μ) ≤ Real.exp ε * (∫ x in s, q x ∂μ) + δ := by
  intro s hs
  have hmain :
      (∫ x in s, (p x - Real.exp ε * q x) ∂μ)
        ≤ ∫ x in posRegion (fun x => p x - Real.exp ε * q x),
            (p x - Real.exp ε * q x) ∂μ := by
    refine integral_restrict_le_integral_posRegion ?_ ?_ s hs
    · fun_prop
    · exact (hp_int.sub (hq_int.const_mul (Real.exp ε)))
  have hsub :
      (∫ x in s, p x ∂μ) - Real.exp ε * (∫ x in s, q x ∂μ)
        ≤ δ := by
    have hp_int_s : MeasureTheory.Integrable p (μ.restrict s) := hp_int.restrict
    have hq_int_s : MeasureTheory.Integrable q (μ.restrict s) := hq_int.restrict
    have hrewrite :
        (∫ x in s, (p x - Real.exp ε * q x) ∂μ)
          = (∫ x in s, p x ∂μ) - Real.exp ε * (∫ x in s, q x ∂μ) := by
      rw [MeasureTheory.integral_sub hp_int_s (hq_int_s.const_mul (Real.exp ε))]
      rw [MeasureTheory.integral_const_mul]
    exact (hrewrite ▸ le_trans hmain hpos)
  linarith

theorem privacyLossSet_bound_of_dp_event_bound
    {α : Type}
    [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    (p q : α → ℝ)
    (ε δ : ℝ)
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_int : MeasureTheory.Integrable p μ)
    (hq_int : MeasureTheory.Integrable q μ)
    (hDP :
      ∀ s, MeasurableSet s →
        (∫ x in s, p x ∂μ) ≤ Real.exp ε * (∫ x in s, q x ∂μ) + δ) :
    (∫ x in posRegion (fun x => p x - Real.exp ε * q x),
        (p x - Real.exp ε * q x) ∂μ) ≤ δ := by
  have hs : MeasurableSet (posRegion (fun x => p x - Real.exp ε * q x)) := by
    change MeasurableSet {x | 0 ≤ p x - Real.exp ε * q x}
    exact (MeasureTheory.stronglyMeasurable_const :
        MeasureTheory.StronglyMeasurable (fun _ : α => (0 : ℝ))).measurableSet_le
      (Measurable.sub hp_meas (Measurable.const_mul hq_meas (Real.exp ε))).stronglyMeasurable
  have hspec := hDP (posRegion (fun x => p x - Real.exp ε * q x)) hs
  let E : Set α := posRegion (fun x => p x - Real.exp ε * q x)
  have hp_int_s : MeasureTheory.Integrable p (μ.restrict E) := hp_int.restrict
  have hq_int_s : MeasureTheory.Integrable q (μ.restrict E) := hq_int.restrict
  have hrewrite :
      (∫ x in E, (p x - Real.exp ε * q x) ∂μ)
        = (∫ x in E, p x ∂μ) - Real.exp ε * (∫ x in E, q x ∂μ) := by
    rw [MeasureTheory.integral_sub hp_int_s (hq_int_s.const_mul (Real.exp ε))]
    rw [MeasureTheory.integral_const_mul]
  linarith [hrewrite, hspec]

theorem privacyLossSet_bound_iff_dp_event_bound
    {α : Type}
    [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    (p q : α → ℝ)
    (ε δ : ℝ)
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_int : MeasureTheory.Integrable p μ)
    (hq_int : MeasureTheory.Integrable q μ) :
    (∫ x in posRegion (fun x => p x - Real.exp ε * q x),
        (p x - Real.exp ε * q x) ∂μ) ≤ δ
      ↔ ∀ s, MeasurableSet s →
          (∫ x in s, p x ∂μ) ≤ Real.exp ε * (∫ x in s, q x ∂μ) + δ := by
  constructor
  · intro h
    exact dp_event_bound_of_privacyLossSet p q ε δ hp_meas hq_meas hp_int hq_int h
  · intro h
    exact privacyLossSet_bound_of_dp_event_bound p q ε δ hp_meas hq_meas hp_int hq_int h

end
end DP
end Mf
