import Mf.DP.PLDRandomAllocation

namespace Mf
namespace DP

noncomputable section

/-!
Canonical privacy-object surface.

This module introduces a small theorem-facing bridge between two privacy
representations already used in the repo:

- raw privacy-profile functions `ℝ → ℝ`
- `PLDPair` objects, viewed through their induced hockey-stick profile

The intent is not to fully unify every privacy notion at once. Instead, this
provides a stable profile-first surface that later branches can extend toward
tradeoff-function or `f`-DP style objects.

Literature anchors:
- `paper/theory/dominating-pair/main_results.tex` `thm:composition`
- `paper/theory/prv/arxiv_version.tex`
- `paper/theory/mu-dp/paper.tex`
-/

/-- Canonical theorem-facing privacy profile object. -/
structure PrivacyProfile where
  eval : ℝ → ℝ

namespace PrivacyProfile

/-- Shifted/additive upper bound relation between privacy profiles. -/
def LeShiftedAdd (upper lower : PrivacyProfile) (α β : ℝ) : Prop :=
  ∀ ε : ℝ, lower.eval ε ≤ upper.eval (ε - α) + β

@[simp] theorem leShiftedAdd_zero_zero_iff
    {upper lower : PrivacyProfile} :
    upper.LeShiftedAdd lower 0 0 ↔ ∀ ε : ℝ, lower.eval ε ≤ upper.eval ε := by
  constructor
  · intro h ε
    simpa using h ε
  · intro h ε
    simpa using h ε

@[simp] theorem leShiftedAdd_refl (P : PrivacyProfile) :
    P.LeShiftedAdd P 0 0 := by
  intro ε
  simp

/-- Transitivity for shifted/additive profile domination.

If `middle` dominates `lower` with shift/slack `(α₁, β₁)` and `upper`
dominates `middle` with `(α₂, β₂)`, then `upper` dominates `lower` with the
sum of the shifts and slacks. -/
theorem LeShiftedAdd.trans
    {upper middle lower : PrivacyProfile}
    {α₁ β₁ α₂ β₂ : ℝ}
    (hUpper : upper.LeShiftedAdd middle α₂ β₂)
    (hMiddle : middle.LeShiftedAdd lower α₁ β₁) :
    upper.LeShiftedAdd lower (α₁ + α₂) (β₁ + β₂) := by
  intro ε
  have h₁ := hMiddle ε
  have h₂ := hUpper (ε - α₁)
  calc
    lower.eval ε
        ≤ middle.eval (ε - α₁) + β₁ := h₁
    _ ≤ (upper.eval ((ε - α₁) - α₂) + β₂) + β₁ :=
          by linarith
    _ = upper.eval (ε - (α₁ + α₂)) + (β₁ + β₂) := by
          ring_nf

end PrivacyProfile

/--
Canonical theorem-facing privacy object.

The first supported payloads are:
- profile-native objects, via `ofProfile`
- PLD-backed objects, via `ofPLDPair`
-/
structure PrivacyObject where
  profile : PrivacyProfile

namespace PrivacyObject

/-- Build a privacy object directly from a profile function. -/
def ofProfile (f : ℝ → ℝ) : PrivacyObject :=
  ⟨⟨f⟩⟩

/-- Build a privacy object from a `PLDPair` using its induced profile. -/
def ofPLDPair (L : PLDPair) : PrivacyObject :=
  ofProfile L.profile

@[simp] theorem ofProfile_profile_eval (f : ℝ → ℝ) :
    (ofProfile f).profile.eval = f := rfl

@[simp] theorem ofPLDPair_profile_eval (L : PLDPair) :
    (ofPLDPair L).profile.eval = L.profile := rfl

/-- Reusable lifted comparison relation on canonical privacy objects. -/
def LeShiftedAdd (upper lower : PrivacyObject) (α β : ℝ) : Prop :=
  upper.profile.LeShiftedAdd lower.profile α β

@[simp] theorem leShiftedAdd_refl (P : PrivacyObject) :
    P.LeShiftedAdd P 0 0 := by
  exact PrivacyProfile.leShiftedAdd_refl P.profile

/-- Transitivity for shifted/additive privacy-object domination. -/
theorem LeShiftedAdd.trans
    {upper middle lower : PrivacyObject}
    {α₁ β₁ α₂ β₂ : ℝ}
    (hUpper : upper.LeShiftedAdd middle α₂ β₂)
    (hMiddle : middle.LeShiftedAdd lower α₁ β₁) :
    upper.LeShiftedAdd lower (α₁ + α₂) (β₁ + β₂) := by
  exact PrivacyProfile.LeShiftedAdd.trans hUpper hMiddle

end PrivacyObject

namespace PLDPair

/--
First reusable transport theorem on the canonical privacy-object surface.

This repackages the existing realization-to-profile theorem in a form that no
longer commits the consumer to speaking directly in terms of `PLDPair`.
-/
theorem ApproxRealizationDominates.toPrivacyObject_leShiftedAdd
    {U L : PLDPair} {α β : ℝ}
    [MeasureTheory.IsFiniteMeasure U.forward] [MeasureTheory.IsFiniteMeasure L.forward]
    (h : U.ApproxRealizationDominates α β L)
    (hβ : 0 ≤ β) :
    (PrivacyObject.ofPLDPair U).LeShiftedAdd (PrivacyObject.ofPLDPair L) α β := by
  intro ε
  simpa [PrivacyObject.LeShiftedAdd, PrivacyObject.ofPLDPair, PrivacyObject.ofProfile,
    PrivacyProfile.LeShiftedAdd] using
    (PLDPair.ApproxRealizationDominates.profile_le (U := U) (L := L) (α := α) (β := β)
      (ε := ε) h hβ)

/--
Concrete consumer theorem: the exact random-allocation profile inequality is
available directly on the canonical privacy-object surface.
-/
theorem concreteRandomAllocation_toPrivacyObject_le_transforms
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p))) :
    (PrivacyObject.ofPLDPair (randomAllocationTransforms (concretePLDPair μ p q) t)).LeShiftedAdd
      (PrivacyObject.ofPLDPair (concreteRandomAllocationPLDPair (t := t) μ p q)) 0 0 := by
  intro ε
  simpa [PrivacyObject.LeShiftedAdd, PrivacyObject.ofPLDPair, PrivacyObject.ofProfile,
    PrivacyProfile.LeShiftedAdd] using
    (concreteRandomAllocation_profile_le_transforms
      (μ := μ) (p := p) (q := q)
      hp_meas hq_meas hp_pos hq_pos hσmap hσadd ε)

end PLDPair

end
end DP
end Mf
