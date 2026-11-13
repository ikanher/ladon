import Mf.DP.VectorClipping
import Mathlib.Analysis.InnerProductSpace.PiL2

namespace Mf
namespace DP

noncomputable section

open scoped BigOperators ENNReal

/-!
# Explicit finite-coordinate Euclidean clipping

Raw function spaces carry Mathlib's Pi sup norm.  This module defines the
privacy-facing `L2` norm through `EuclideanSpace` and never relies on that
ambient Pi norm for clipping or sensitivity.
-/

/-- Canonical Euclidean representation of a finite real coordinate vector. -/
def toEuclidean {ι : Type*} [Fintype ι] (x : ι → ℝ) :
    EuclideanSpace ℝ ι :=
  WithLp.toLp 2 x

/-- Explicit Euclidean `L2` norm on a raw finite coordinate function. -/
def l2Norm {ι : Type*} [Fintype ι] (x : ι → ℝ) : ℝ :=
  ‖toEuclidean x‖

@[simp] theorem l2Norm_zero {ι : Type*} [Fintype ι] :
    l2Norm (0 : ι → ℝ) = 0 := by
  simp [l2Norm, toEuclidean]

theorem l2Norm_nonneg {ι : Type*} [Fintype ι] (x : ι → ℝ) :
    0 ≤ l2Norm x :=
  norm_nonneg _

theorem l2Norm_eq_zero {ι : Type*} [Fintype ι] (x : ι → ℝ) :
    l2Norm x = 0 ↔ x = 0 := by
  simp [l2Norm, toEuclidean]

@[simp] theorem l2Norm_neg {ι : Type*} [Fintype ι] (x : ι → ℝ) :
    l2Norm (-x) = l2Norm x := by
  simp [l2Norm, toEuclidean]

theorem l2Norm_smul {ι : Type*} [Fintype ι] (a : ℝ) (x : ι → ℝ) :
    l2Norm (a • x) = |a| * l2Norm x := by
  simp [l2Norm, toEuclidean, norm_smul, Real.norm_eq_abs]

theorem l2Norm_add_le {ι : Type*} [Fintype ι] (x y : ι → ℝ) :
    l2Norm (x + y) ≤ l2Norm x + l2Norm y := by
  simpa [l2Norm, toEuclidean] using
    (norm_add_le (toEuclidean x) (toEuclidean y))

/-- Sum-of-squares formula for the explicit Euclidean norm. -/
theorem l2Norm_sq {ι : Type*} [Fintype ι] (x : ι → ℝ) :
    l2Norm x ^ 2 = ∑ i, x i ^ 2 := by
  simpa [l2Norm, toEuclidean] using
    (EuclideanSpace.real_norm_sq_eq (toEuclidean x))

theorem measurable_toEuclidean {ι : Type*} [Fintype ι] :
    Measurable (toEuclidean : (ι → ℝ) → EuclideanSpace ℝ ι) :=
  (MeasurableEquiv.toLp 2 (ι → ℝ)).measurable

theorem measurable_l2Norm {ι : Type*} [Fintype ι] :
    Measurable (l2Norm : (ι → ℝ) → ℝ) :=
  measurable_norm.comp measurable_toEuclidean

/-- Euclidean clipping on raw coordinates. -/
def l2VectorClip {ι : Type*} [Fintype ι]
    (C : ℝ) (x : ι → ℝ) : ι → ℝ :=
  if l2Norm x ≤ C then x else (C / l2Norm x) • x

theorem measurable_l2VectorClip {ι : Type*} [Fintype ι] (C : ℝ) :
    Measurable (l2VectorClip C : (ι → ℝ) → (ι → ℝ)) := by
  have hs : MeasurableSet {x : ι → ℝ | l2Norm x ≤ C} :=
    measurableSet_le measurable_l2Norm measurable_const
  have hscaled : Measurable fun x : ι → ℝ => (C / l2Norm x) • x := by
    refine measurable_pi_lambda _ fun i => ?_
    exact (measurable_const.div measurable_l2Norm).mul (measurable_pi_apply i)
  change Measurable
    ({x : ι → ℝ | l2Norm x ≤ C}.piecewise id
      (fun x => (C / l2Norm x) • x))
  exact Measurable.piecewise hs measurable_id hscaled

@[simp] theorem l2VectorClip_zero {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 ≤ C) :
    l2VectorClip C (0 : ι → ℝ) = 0 := by
  simp [l2VectorClip, hC]

@[simp] theorem l2VectorClip_neg {ι : Type*} [Fintype ι]
    (C : ℝ) (x : ι → ℝ) :
    l2VectorClip C (-x) = -l2VectorClip C x := by
  unfold l2VectorClip
  rw [l2Norm_neg]
  split_ifs <;> simp [smul_neg]

theorem l2VectorClip_eq_self {ι : Type*} [Fintype ι]
    (C : ℝ) (x : ι → ℝ) (hx : l2Norm x ≤ C) :
    l2VectorClip C x = x := by
  simp [l2VectorClip, hx]

theorem l2VectorClip_norm_le {ι : Type*} [Fintype ι]
    (C : ℝ) (x : ι → ℝ) (hC : 0 ≤ C) :
    l2Norm (l2VectorClip C x) ≤ C := by
  by_cases h : l2Norm x ≤ C
  · simpa [l2VectorClip, h]
  · have hlt : C < l2Norm x := lt_of_not_ge h
    have hxpos : 0 < l2Norm x := lt_of_le_of_lt hC hlt
    rw [l2VectorClip, if_neg h, l2Norm_smul, abs_of_nonneg
      (div_nonneg hC (l2Norm_nonneg x)), div_mul_cancel₀ C hxpos.ne']

/-- Finite sum of explicitly Euclidean-clipped contributions. -/
def l2ClippedFinsetSum
    {Record ι : Type*} [DecidableEq Record] [Fintype ι]
    (C : ℝ) (gradient : Record → (ι → ℝ)) (dataset : Finset Record) : ι → ℝ :=
  ∑ record ∈ dataset, l2VectorClip C (gradient record)

theorem l2ClippedFinsetSum_addRemove_sensitivity
    {Record ι : Type*} [DecidableEq Record] [Fintype ι]
    (C : ℝ) (hC : 0 ≤ C) (gradient : Record → (ι → ℝ))
    {left right : Finset Record}
    (hAdj : FinsetAddRemoveAdjacent left right) :
    l2Norm (l2ClippedFinsetSum C gradient left -
      l2ClippedFinsetSum C gradient right) ≤ C := by
  rcases hAdj with ⟨record, hmem, rfl⟩ | ⟨record, hmem, rfl⟩
  · rw [l2ClippedFinsetSum, l2ClippedFinsetSum, Finset.sum_insert hmem]
    have heq :
        (∑ x ∈ left, l2VectorClip C (gradient x)) -
            (l2VectorClip C (gradient record) +
              ∑ x ∈ left, l2VectorClip C (gradient x)) =
          -l2VectorClip C (gradient record) := by
      abel
    rw [heq, l2Norm_neg]
    exact l2VectorClip_norm_le C (gradient record) hC
  · rw [l2ClippedFinsetSum, l2ClippedFinsetSum, Finset.sum_insert hmem]
    have heq :
        (l2VectorClip C (gradient record) +
            ∑ x ∈ right, l2VectorClip C (gradient x)) -
          ∑ x ∈ right, l2VectorClip C (gradient x) =
        l2VectorClip C (gradient record) := by
      abel
    rw [heq]
    exact l2VectorClip_norm_le C (gradient record) hC

/-- The generic Pi norm is not a Euclidean norm: `(1,1)` has sup norm one but
Euclidean squared norm two. -/
theorem piNorm_ne_l2Norm_finTwo :
    ‖(fun _ : Fin 2 => (1 : ℝ))‖ ≠
      l2Norm (fun _ : Fin 2 => (1 : ℝ)) := by
  intro h
  have hsup : ‖(fun _ : Fin 2 => (1 : ℝ))‖ = 1 := by simp
  have hl2sq := l2Norm_sq (fun _ : Fin 2 => (1 : ℝ))
  rw [hsup] at h
  rw [← h] at hl2sq
  norm_num at hl2sq

end
end DP
end Mf
