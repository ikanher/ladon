import Mathlib

namespace Mf
namespace DP

noncomputable section

open scoped BigOperators

/-!
# Generic norm clipping and add/remove sensitivity

This module owns optimizer-independent deterministic clipping facts.  It does
not introduce sampling, Gaussian noise, or privacy accounting.  For a raw
finite function type such as `Fin d → ℝ`, Mathlib's norm is the Pi sup norm.
Consequently this generic owner is not authority for standard Euclidean `L2`
clipping on that representation; use the dedicated Euclidean owner instead.
-/

/-- Deterministic clipping in the norm supplied by the ambient type. -/
def vectorClip {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (C : ℝ) (x : E) : E :=
  if ‖x‖ ≤ C then x else (C / ‖x‖) • x

theorem vectorClip_norm_le
    {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (C : ℝ) (x : E) (hC : 0 ≤ C) :
    ‖vectorClip C x‖ ≤ C := by
  by_cases h : ‖x‖ ≤ C
  · simp [vectorClip, h]
  · have hlt : C < ‖x‖ := lt_of_not_ge h
    have hxpos : 0 < ‖x‖ := lt_of_le_of_lt hC hlt
    rw [vectorClip, if_neg h, norm_smul, Real.norm_eq_abs,
      abs_of_nonneg (div_nonneg hC (norm_nonneg x)),
      div_mul_cancel₀ C hxpos.ne']

/-- Symmetric add/remove adjacency on finite datasets. -/
def FinsetAddRemoveAdjacent
    {Record : Type*} [DecidableEq Record]
    (left right : Finset Record) : Prop :=
  (∃ record, record ∉ left ∧ right = insert record left) ∨
  (∃ record, record ∉ right ∧ left = insert record right)

theorem finsetAddRemoveAdjacent_symm
    {Record : Type*} [DecidableEq Record]
    {left right : Finset Record}
    (h : FinsetAddRemoveAdjacent left right) :
    FinsetAddRemoveAdjacent right left := by
  rcases h with h | h
  · exact Or.inr h
  · exact Or.inl h

/-- Sum of clipped per-record contributions. -/
def clippedFinsetSum
    {Record E : Type*} [DecidableEq Record]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (C : ℝ) (gradient : Record → E) (dataset : Finset Record) : E :=
  ∑ record ∈ dataset, vectorClip C (gradient record)

theorem clippedFinsetSum_addRemove_sensitivity
    {Record E : Type*} [DecidableEq Record]
    [NormedAddCommGroup E] [NormedSpace ℝ E]
    (C : ℝ) (hC : 0 ≤ C) (gradient : Record → E)
    {left right : Finset Record}
    (hAdj : FinsetAddRemoveAdjacent left right) :
    ‖clippedFinsetSum C gradient left -
        clippedFinsetSum C gradient right‖ ≤ C := by
  rcases hAdj with ⟨record, hmem, rfl⟩ | ⟨record, hmem, rfl⟩
  · rw [clippedFinsetSum, clippedFinsetSum,
      Finset.sum_insert hmem]
    have heq :
        (∑ x ∈ left, vectorClip C (gradient x)) -
            (vectorClip C (gradient record) +
              ∑ x ∈ left, vectorClip C (gradient x)) =
          -vectorClip C (gradient record) := by
      abel
    rw [heq, norm_neg]
    exact vectorClip_norm_le C (gradient record) hC
  · rw [clippedFinsetSum, clippedFinsetSum,
      Finset.sum_insert hmem]
    have heq :
        (vectorClip C (gradient record) +
            ∑ x ∈ right, vectorClip C (gradient x)) -
          ∑ x ∈ right, vectorClip C (gradient x) =
        vectorClip C (gradient record) := by
      abel
    rw [heq]
    exact vectorClip_norm_le C (gradient record) hC

end
end DP
end Mf
