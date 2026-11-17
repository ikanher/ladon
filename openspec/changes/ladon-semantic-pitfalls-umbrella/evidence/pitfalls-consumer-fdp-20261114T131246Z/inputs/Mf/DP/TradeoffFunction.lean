import Mf.DP.PrivacyLossCore
import Mf.DP.PrivacyObjectSurface

namespace Mf
namespace DP

noncomputable section

/-!
Tradeoff-function privacy surface.

This module adds a small theorem-facing object for the hypothesis-testing side
of privacy. The goal is not to formalize the whole `f`-DP literature at once;
it is to expose a named tradeoff object and a first bridge from the existing
profile/privacy-object layer.

Literature anchors:
- `paper/theory/mu-dp/paper.tex`
- `paper/theory/mu-dp/fDP/tradeoff.tex`
- `paper/theory/dominating-pair/preliminary.tex`
-/

/-- Canonical theorem-facing tradeoff-function object. -/
structure TradeoffFunction where
  eval : ℝ → ℝ
  unit_bddBelow :
    BddBelow (Set.range fun α : Set.Icc (0 : ℝ) 1 => eval α.1)
  unit_bddAbove :
    BddAbove (Set.range fun α : Set.Icc (0 : ℝ) 1 => eval α.1)

namespace TradeoffFunction

/-- Pointwise order on tradeoff functions. -/
def PointwiseLE (lower upper : TradeoffFunction) : Prop :=
  ∀ α : ℝ, lower.eval α ≤ upper.eval α

/-- Values of a tradeoff function on the clipped unit interval. -/
def unitValueSet (T : TradeoffFunction) : Set ℝ :=
  Set.range fun α : Set.Icc (0 : ℝ) 1 => T.eval α.1

theorem unitValueSet_nonempty (T : TradeoffFunction) : (T.unitValueSet).Nonempty := by
  refine ⟨T.eval 0, ?_⟩
  refine ⟨⟨0, by norm_num, by norm_num⟩, rfl⟩

/-- Infimum of the values of a tradeoff function on `[0, 1]`. -/
def unitInf (T : TradeoffFunction) : ℝ :=
  sInf T.unitValueSet

/-- Constant theorem-facing tradeoff object. -/
def const (c : ℝ) : TradeoffFunction :=
  ⟨fun _ => c,
    ⟨c, by
      intro y hy
      rcases hy with ⟨α, rfl⟩
      simp⟩,
    ⟨c, by
      intro y hy
      rcases hy with ⟨α, rfl⟩
      simp⟩⟩

/-- Canonical constant lower witness at the unit-interval infimum. -/
def constAtUnitInf (T : TradeoffFunction) : TradeoffFunction :=
  const T.unitInf

@[simp] theorem pointwiseLE_refl (T : TradeoffFunction) :
    T.PointwiseLE T := by
  intro α
  simp

/-- Tradeoff functions are equal when their public evaluation surfaces agree. -/
theorem eq_of_eval_eq
    {T U : TradeoffFunction}
    (h : ∀ α : ℝ, T.eval α = U.eval α) :
    T = U := by
  cases T with
  | mk evalT lowerT upperT =>
    cases U with
    | mk evalU lowerU upperU =>
      have hfun : evalT = evalU := by
        funext α
        exact h α
      cases hfun
      have hlower : lowerT = lowerU := Subsingleton.elim _ _
      have hupper : upperT = upperU := Subsingleton.elim _ _
      cases hlower
      cases hupper
      rfl

/--
Linear tradeoff lower bound coming from a fixed `(ε, δ(ε))` privacy-profile
point.
-/
def ofProfileAt (P : PrivacyProfile) (ε : ℝ) : TradeoffFunction :=
  ⟨fun α => 1 - P.eval ε - Real.exp ε * α,
    ⟨1 - P.eval ε - Real.exp ε, by
      intro y hy
      rcases hy with ⟨α, rfl⟩
      have hα0 : 0 ≤ (α : ℝ) := α.2.1
      have hα1 : (α : ℝ) ≤ 1 := α.2.2
      have hExp : 0 < Real.exp ε := Real.exp_pos ε
      nlinarith⟩,
    ⟨1 - P.eval ε, by
      intro y hy
      rcases hy with ⟨α, rfl⟩
      have hα0 : 0 ≤ (α : ℝ) := α.2.1
      have hExp : 0 < Real.exp ε := Real.exp_pos ε
      nlinarith⟩⟩

/-- Linear tradeoff lower bound coming from a single event-level DP bound. -/
def ofDPEventBound (ε δ : ℝ) : TradeoffFunction :=
  ⟨fun α => 1 - δ - Real.exp ε * α,
    ⟨1 - δ - Real.exp ε, by
      intro y hy
      rcases hy with ⟨α, rfl⟩
      have hα0 : 0 ≤ (α : ℝ) := α.2.1
      have hα1 : (α : ℝ) ≤ 1 := α.2.2
      have hExp : 0 < Real.exp ε := Real.exp_pos ε
      nlinarith⟩,
    ⟨1 - δ, by
      intro y hy
      rcases hy with ⟨α, rfl⟩
      have hα0 : 0 ≤ (α : ℝ) := α.2.1
      have hExp : 0 < Real.exp ε := Real.exp_pos ε
      nlinarith⟩⟩

@[simp] theorem ofProfileAt_eval (P : PrivacyProfile) (ε α : ℝ) :
    (ofProfileAt P ε).eval α = 1 - P.eval ε - Real.exp ε * α := rfl

@[simp] theorem ofDPEventBound_eval (ε δ α : ℝ) :
    (ofDPEventBound ε δ).eval α = 1 - δ - Real.exp ε * α := rfl

/--
Smaller profile values yield larger linear tradeoff lower bounds at a fixed
privacy parameter.
-/
theorem ofProfileAt_anti_mono
    {P Q : PrivacyProfile}
    (hPQ : ∀ ε : ℝ, P.eval ε ≤ Q.eval ε)
    (ε : ℝ) :
    (ofProfileAt Q ε).PointwiseLE (ofProfileAt P ε) := by
  intro α
  have hε : P.eval ε ≤ Q.eval ε := hPQ ε
  dsimp [ofProfileAt]
  linarith

/--
On the current public fixed-`ε` surface, pointwise comparison of two
`ofProfileAt` witnesses is equivalent to comparing the underlying profile
values at that same `ε`.

This is a useful proof-boundary fact: `ofProfileAt` is a linear witness
extracted from one profile point, not a full represented tensor-product
tradeoff object.
-/
theorem ofProfileAt_pointwiseLE_iff
    {P Q : PrivacyProfile}
    (ε : ℝ) :
    (ofProfileAt P ε).PointwiseLE (ofProfileAt Q ε) ↔
      Q.eval ε ≤ P.eval ε := by
  constructor
  · intro h
    have h0 := h 0
    simp [ofProfileAt] at h0
    linarith
  · intro hPQ α
    simp [ofProfileAt]
    linarith

/--
An event-level `(ε, δ)` bound implies the corresponding linear tradeoff lower
bound for every measurable test event.
-/
theorem dp_event_bound_yields_tradeoff_lower
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
      (ofDPEventBound ε δ).eval (∫ x in s, q x ∂μ) ≤ 1 - ∫ x in s, p x ∂μ := by
  intro s hs
  have hDP :=
    dp_event_bound_of_privacyLossSet p q ε δ hp_meas hq_meas hp_int hq_int hpos s hs
  change 1 - δ - Real.exp ε * (∫ x in s, q x ∂μ) ≤ 1 - ∫ x in s, p x ∂μ
  linarith

end TradeoffFunction

namespace PrivacyObject

/-- Canonical linear tradeoff witness extracted from a privacy object at `ε`. -/
def tradeoffAt (P : PrivacyObject) (ε : ℝ) : TradeoffFunction :=
  TradeoffFunction.ofProfileAt P.profile ε

@[simp] theorem tradeoffAt_eval (P : PrivacyObject) (ε α : ℝ) :
    (P.tradeoffAt ε).eval α = 1 - P.profile.eval ε - Real.exp ε * α := rfl

/--
Zero-shift profile comparison transports to pointwise comparison of the linear
tradeoff witnesses extracted at the same `ε`.
-/
theorem tradeoffAt_of_leShiftedAdd_zero_zero
    {U L : PrivacyObject}
    (h : U.LeShiftedAdd L 0 0)
    (ε : ℝ) :
    (U.tradeoffAt ε).PointwiseLE (L.tradeoffAt ε) := by
  apply TradeoffFunction.ofProfileAt_anti_mono
  intro ε'
  exact (PrivacyProfile.leShiftedAdd_zero_zero_iff.mp h) ε'

/--
On the current public fixed-`ε` surface, pointwise comparison of extracted
tradeoff witnesses is equivalent to comparing the underlying profile values at
that same `ε`.
-/
theorem tradeoffAt_pointwiseLE_iff
    {U L : PrivacyObject}
    (ε : ℝ) :
    (U.tradeoffAt ε).PointwiseLE (L.tradeoffAt ε) ↔
      L.profile.eval ε ≤ U.profile.eval ε := by
  simpa [tradeoffAt] using
    (TradeoffFunction.ofProfileAt_pointwiseLE_iff
      (P := U.profile) (Q := L.profile) ε)

end PrivacyObject

namespace PLDPair

/--
Exact equality of neighboring `PLDPair`s transports immediately to the public
privacy-object comparison surface.
-/
theorem toPrivacyObject_leShiftedAdd_zero_zero_of_eq
    {U L : PLDPair}
    (h : U = L) :
    (PrivacyObject.ofPLDPair U).LeShiftedAdd (PrivacyObject.ofPLDPair L) 0 0 := by
  cases h
  exact PrivacyObject.leShiftedAdd_refl (PrivacyObject.ofPLDPair U)

/--
Exact equality of neighboring `PLDPair`s transports immediately to pointwise
comparison of the extracted tradeoff witnesses.
-/
theorem toTradeoffAt_pointwiseLE_of_eq
    {U L : PLDPair}
    (h : U = L) (ε : ℝ) :
    ((PrivacyObject.ofPLDPair U).tradeoffAt ε).PointwiseLE
      ((PrivacyObject.ofPLDPair L).tradeoffAt ε) := by
  exact PrivacyObject.tradeoffAt_of_leShiftedAdd_zero_zero
    (PLDPair.toPrivacyObject_leShiftedAdd_zero_zero_of_eq h) ε

/--
Concrete profile-side consumer restated on the tradeoff-function surface at a
fixed `ε`.
-/
theorem concreteRandomAllocation_toTradeoffAt_le_transforms
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    ((PrivacyObject.ofPLDPair
      (randomAllocationTransforms (concretePLDPair μ p q) t)).tradeoffAt ε).PointwiseLE
      ((PrivacyObject.ofPLDPair
        (concreteRandomAllocationPLDPair (t := t) μ p q)).tradeoffAt ε) := by
  exact PrivacyObject.tradeoffAt_of_leShiftedAdd_zero_zero
    (PLDPair.concreteRandomAllocation_toPrivacyObject_le_transforms
      (μ := μ) (p := p) (q := q)
      hp_meas hq_meas hp_pos hq_pos hσmap hσadd)
    ε

end PLDPair

end
end DP
end Mf
