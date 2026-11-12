import Mf.DP.EuclideanVectorClipping

namespace Mf
namespace DP

noncomputable section

open scoped BigOperators

/-!
# Regularity of explicit Euclidean clipping

The privacy sensitivity theorem only bounds the contribution of one record.
Continuous-time coefficient arguments additionally need stability of the
clipping map when its input or positive radius changes.  This module proves
those facts in the explicit `l2Norm` coordinate used by the mechanism.
-/

/-- Radial projection onto the closed Euclidean ball of radius `C`. -/
def euclideanBallClip {ι : Type*} [Fintype ι]
    (C : ℝ) (x : EuclideanSpace ℝ ι) : EuclideanSpace ℝ ι :=
  if ‖x‖ ≤ C then x else (C / ‖x‖) • x

@[simp] theorem toEuclidean_l2VectorClip {ι : Type*} [Fintype ι]
    (C : ℝ) (x : ι → ℝ) :
    toEuclidean (l2VectorClip C x) = euclideanBallClip C (toEuclidean x) := by
  simp only [l2VectorClip, euclideanBallClip, l2Norm]
  change toEuclidean
      (if ‖toEuclidean x‖ ≤ C then x
       else (C / ‖toEuclidean x‖) • x) =
    if ‖toEuclidean x‖ ≤ C then toEuclidean x
    else (C / ‖toEuclidean x‖) • toEuclidean x
  by_cases h : ‖toEuclidean x‖ ≤ C
  · rw [if_pos h, if_pos h]
  · rw [if_neg h, if_neg h]
    change WithLp.toLp (2 : ENNReal)
        ((C / ‖toEuclidean x‖) • x) =
      (C / ‖toEuclidean x‖) • toEuclidean x
    rw [WithLp.toLp_smul (p := (2 : ENNReal))]
    rfl

theorem euclideanBallClip_mem_closedBall {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 ≤ C) (x : EuclideanSpace ℝ ι) :
    ‖euclideanBallClip C x‖ ≤ C := by
  by_cases hx : ‖x‖ ≤ C
  · simp [euclideanBallClip, hx]
  · have hC_lt : C < ‖x‖ := lt_of_not_ge hx
    have hx_pos : 0 < ‖x‖ := lt_of_le_of_lt hC hC_lt
    rw [euclideanBallClip, if_neg hx, norm_smul, Real.norm_eq_abs,
      abs_of_nonneg (div_nonneg hC (norm_nonneg x)), div_mul_cancel₀ C hx_pos.ne']

/-- Characterization of radial clipping as a convex projection. -/
theorem real_inner_sub_euclideanBallClip_clip_sub_nonpos
    {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 ≤ C) (x z : EuclideanSpace ℝ ι)
    (hz : ‖z‖ ≤ C) :
    inner ℝ (x - euclideanBallClip C x) (z - euclideanBallClip C x) ≤ 0 := by
  by_cases hx : ‖x‖ ≤ C
  · simp [euclideanBallClip, hx]
  · have hC_lt : C < ‖x‖ := lt_of_not_ge hx
    have hx_pos : 0 < ‖x‖ := lt_of_le_of_lt hC hC_lt
    have hinner : inner ℝ x z ≤ ‖x‖ * C := by
      calc
        inner ℝ x z ≤ ‖x‖ * ‖z‖ := real_inner_le_norm x z
        _ ≤ ‖x‖ * C := mul_le_mul_of_nonneg_left hz (norm_nonneg x)
    rw [euclideanBallClip, if_neg hx]
    have hfactor : 0 ≤ 1 - C / ‖x‖ := by
      rw [sub_nonneg, div_le_one hx_pos]
      exact hC_lt.le
    have hscale : 0 ≤ C / ‖x‖ := div_nonneg hC (norm_nonneg x)
    have heq :
        inner ℝ (x - (C / ‖x‖) • x) (z - (C / ‖x‖) • x) =
          (1 - C / ‖x‖) * (inner ℝ x z - ‖x‖ * C) := by
      simp only [inner_sub_left, inner_sub_right, real_inner_smul_left,
        real_inner_smul_right, real_inner_self_eq_norm_sq, norm_smul,
        Real.norm_eq_abs, abs_of_nonneg hscale]
      field_simp [hx_pos.ne']
    rw [heq]
    exact mul_nonpos_of_nonneg_of_nonpos hfactor (sub_nonpos.mpr hinner)

/-- Radial projection onto a Euclidean ball is nonexpansive. -/
theorem euclideanBallClip_nonexpansive {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 ≤ C) (x y : EuclideanSpace ℝ ι) :
    ‖euclideanBallClip C x - euclideanBallClip C y‖ ≤ ‖x - y‖ := by
  let px := euclideanBallClip C x
  let py := euclideanBallClip C y
  have hpx : ‖px‖ ≤ C := euclideanBallClip_mem_closedBall C hC x
  have hpy : ‖py‖ ≤ C := euclideanBallClip_mem_closedBall C hC y
  have hxy := real_inner_sub_euclideanBallClip_clip_sub_nonpos C hC x py hpy
  have hyx := real_inner_sub_euclideanBallClip_clip_sub_nonpos C hC y px hpx
  change inner ℝ (x - px) (py - px) ≤ 0 at hxy
  change inner ℝ (y - py) (px - py) ≤ 0 at hyx
  change ‖px - py‖ ≤ ‖x - y‖
  by_cases hd : px - py = 0
  · rw [hd, norm_zero]
    exact norm_nonneg _
  · have hinner_lower : ‖px - py‖ ^ 2 ≤ inner ℝ (px - py) (x - y) := by
      have hdecomp : x - y = (px - py) + (x - px) - (y - py) := by abel
      have hxy' : 0 ≤ inner ℝ (px - py) (x - px) := by
        rw [real_inner_comm]
        have h := hxy
        have hneg : py - px = -(px - py) := by abel
        rw [hneg, inner_neg_right] at h
        linarith
      have hyx' : inner ℝ (px - py) (y - py) ≤ 0 := by
        rw [real_inner_comm]
        exact hyx
      have hcalc :
          inner ℝ (px - py) (x - y) =
            inner ℝ (px - py) (px - py) +
              inner ℝ (px - py) (x - px) -
              inner ℝ (px - py) (y - py) := by
        rw [hdecomp, inner_sub_right, inner_add_right]
      calc
        ‖px - py‖ ^ 2 = inner ℝ (px - py) (px - py) :=
          (real_inner_self_eq_norm_sq _).symm
        _ ≤ inner ℝ (px - py) (x - y) := by
          rw [hcalc]
          linarith
    have hinner_upper : inner ℝ (px - py) (x - y) ≤ ‖px - py‖ * ‖x - y‖ :=
      real_inner_le_norm _ _
    have hnorm_pos : 0 < ‖px - py‖ := norm_pos_iff.mpr hd
    have hmul : ‖px - py‖ * ‖px - py‖ ≤ ‖px - py‖ * ‖x - y‖ := by
      rw [← pow_two]
      exact hinner_lower.trans hinner_upper
    exact le_of_mul_le_mul_left hmul hnorm_pos

theorem euclideanBallClip_radius_le_of_le {ι : Type*} [Fintype ι]
    (C D : ℝ) (hC : 0 ≤ C) (hCD : C ≤ D) (x : EuclideanSpace ℝ ι) :
    ‖euclideanBallClip C x - euclideanBallClip D x‖ ≤ |C - D| := by
  have hD : 0 ≤ D := hC.trans hCD
  by_cases hxC : ‖x‖ ≤ C
  · have hxD : ‖x‖ ≤ D := hxC.trans hCD
    simp [euclideanBallClip, hxC, hxD]
  · have hCx : C < ‖x‖ := lt_of_not_ge hxC
    have hx_pos : 0 < ‖x‖ := lt_of_le_of_lt hC hCx
    by_cases hxD : ‖x‖ ≤ D
    · have hclipC : euclideanBallClip C x = (C / ‖x‖) • x := by
        simp [euclideanBallClip, hxC]
      have hclipD : euclideanBallClip D x = x := by
        simp [euclideanBallClip, hxD]
      rw [hclipC, hclipD]
      rw [show (C / ‖x‖) • x - x = (C / ‖x‖ - 1) • x by module,
        norm_smul, Real.norm_eq_abs]
      have hratio : C / ‖x‖ ≤ 1 := (div_le_one hx_pos).mpr hCx.le
      rw [abs_of_nonpos (sub_nonpos.mpr hratio)]
      have hcalc : (1 - C / ‖x‖) * ‖x‖ = ‖x‖ - C := by
        field_simp [hx_pos.ne']
      rw [show -(C / ‖x‖ - 1) = 1 - C / ‖x‖ by ring, hcalc,
        abs_of_nonpos (sub_nonpos.mpr hCD)]
      linarith
    · have hDx : D < ‖x‖ := lt_of_not_ge hxD
      have hclipC : euclideanBallClip C x = (C / ‖x‖) • x := by
        simp [euclideanBallClip, hxC]
      have hclipD : euclideanBallClip D x = (D / ‖x‖) • x := by
        simp [euclideanBallClip, hxD]
      rw [hclipC, hclipD, ← sub_smul, norm_smul, Real.norm_eq_abs]
      have hquot : C / ‖x‖ - D / ‖x‖ ≤ 0 := by
        exact sub_nonpos.mpr (div_le_div_of_nonneg_right hCD (norm_nonneg x))
      rw [abs_of_nonpos hquot, abs_of_nonpos (sub_nonpos.mpr hCD)]
      field_simp [hx_pos.ne']
      rfl

theorem euclideanBallClip_radius_le {ι : Type*} [Fintype ι]
    (C D : ℝ) (hC : 0 ≤ C) (hD : 0 ≤ D) (x : EuclideanSpace ℝ ι) :
    ‖euclideanBallClip C x - euclideanBallClip D x‖ ≤ |C - D| := by
  rcases le_total C D with hCD | hDC
  · exact euclideanBallClip_radius_le_of_le C D hC hCD x
  · have h := euclideanBallClip_radius_le_of_le D C hD hDC x
    rw [norm_sub_rev, abs_sub_comm]
    exact h

/-- Joint input/radius stability on nonnegative radii. -/
theorem euclideanBallClip_joint_le {ι : Type*} [Fintype ι]
    (C D : ℝ) (hC : 0 ≤ C) (hD : 0 ≤ D)
    (x y : EuclideanSpace ℝ ι) :
    ‖euclideanBallClip C x - euclideanBallClip D y‖ ≤ ‖x - y‖ + |C - D| := by
  calc
    ‖euclideanBallClip C x - euclideanBallClip D y‖ =
        ‖(euclideanBallClip C x - euclideanBallClip C y) +
          (euclideanBallClip C y - euclideanBallClip D y)‖ := by
      congr 1
      abel
    _ ≤
        ‖euclideanBallClip C x - euclideanBallClip C y‖ +
          ‖euclideanBallClip C y - euclideanBallClip D y‖ := by
      exact norm_add_le _ _
    _ ≤ ‖x - y‖ + |C - D| := add_le_add
      (euclideanBallClip_nonexpansive C hC x y)
      (euclideanBallClip_radius_le C D hC hD y)

theorem euclideanBallClip_lipschitzOn_nonnegative {ι : Type*} [Fintype ι] :
    LipschitzOnWith 2
      (fun p : ℝ × EuclideanSpace ℝ ι => euclideanBallClip p.1 p.2)
      {p | 0 ≤ p.1} := by
  rw [lipschitzOnWith_iff_dist_le_mul]
  intro p hp q hq
  rw [dist_eq_norm, Prod.dist_eq, Real.dist_eq]
  calc
    ‖euclideanBallClip p.1 p.2 - euclideanBallClip q.1 q.2‖ ≤
        ‖p.2 - q.2‖ + |p.1 - q.1| :=
      euclideanBallClip_joint_le p.1 q.1 hp hq p.2 q.2
    _ ≤ 2 * max |p.1 - q.1| ‖p.2 - q.2‖ := by
      have h1 : |p.1 - q.1| ≤ max |p.1 - q.1| ‖p.2 - q.2‖ := le_max_left _ _
      have h2 : ‖p.2 - q.2‖ ≤ max |p.1 - q.1| ‖p.2 - q.2‖ := le_max_right _ _
      linarith

theorem euclideanBallClip_continuousOn_nonnegative {ι : Type*} [Fintype ι] :
    ContinuousOn
      (fun p : ℝ × EuclideanSpace ℝ ι => euclideanBallClip p.1 p.2)
      {p | 0 ≤ p.1} :=
  euclideanBallClip_lipschitzOn_nonnegative.continuousOn

theorem continuous_euclideanBallClip_comp
    {T ι : Type*} [TopologicalSpace T] [Fintype ι]
    {C : T → ℝ} {x : T → EuclideanSpace ℝ ι}
    (hC : Continuous C) (hx : Continuous x) (hC_nonneg : ∀ t, 0 ≤ C t) :
    Continuous fun t => euclideanBallClip (C t) (x t) := by
  have hp : Continuous fun t => (C t, x t) := hC.prodMk hx
  convert euclideanBallClip_continuousOn_nonnegative.comp_continuous hp
      (fun t => hC_nonneg t) using 1
  rfl

theorem measurable_euclideanBallClip_comp
    {T ι : Type*} [TopologicalSpace T] [MeasurableSpace T]
    [OpensMeasurableSpace T] [Fintype ι]
    {C : T → ℝ} {x : T → EuclideanSpace ℝ ι}
    (hC : Continuous C) (hx : Continuous x) (hC_nonneg : ∀ t, 0 ≤ C t) :
    Measurable fun t => euclideanBallClip (C t) (x t) :=
  (continuous_euclideanBallClip_comp hC hx hC_nonneg).measurable

/-- Explicit Euclidean clipping is nonexpansive in `l2Norm`. -/
theorem l2Norm_l2VectorClip_sub_l2VectorClip_le
    {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 ≤ C) (x y : ι → ℝ) :
    l2Norm (l2VectorClip C x - l2VectorClip C y) ≤ l2Norm (x - y) := by
  change ‖toEuclidean (l2VectorClip C x - l2VectorClip C y)‖ ≤
    ‖toEuclidean (x - y)‖
  rw [show toEuclidean (l2VectorClip C x - l2VectorClip C y) =
      toEuclidean (l2VectorClip C x) - toEuclidean (l2VectorClip C y) by rfl,
    show toEuclidean (x - y) = toEuclidean x - toEuclidean y by rfl,
    toEuclidean_l2VectorClip, toEuclidean_l2VectorClip]
  exact euclideanBallClip_nonexpansive C hC (toEuclidean x) (toEuclidean y)

/-- The normalized clipped vector lies in the Euclidean unit ball. -/
theorem normalizedL2VectorClip_norm_le_one
    {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 < C) (x : ι → ℝ) :
    l2Norm ((C⁻¹) • l2VectorClip C x) ≤ 1 := by
  rw [l2Norm_smul, abs_of_pos (inv_pos.mpr hC)]
  calc
    C⁻¹ * l2Norm (l2VectorClip C x) ≤ C⁻¹ * C :=
      mul_le_mul_of_nonneg_left (l2VectorClip_norm_le C x hC.le)
        (inv_nonneg.mpr hC.le)
    _ = 1 := inv_mul_cancel₀ hC.ne'

/-- Input stability of normalized clipping at a fixed positive radius. -/
theorem normalizedL2VectorClip_sub_le
    {ι : Type*} [Fintype ι]
    (C : ℝ) (hC : 0 < C) (x y : ι → ℝ) :
    l2Norm ((C⁻¹) • l2VectorClip C x - (C⁻¹) • l2VectorClip C y) ≤
      C⁻¹ * l2Norm (x - y) := by
  rw [← smul_sub, l2Norm_smul, abs_of_pos (inv_pos.mpr hC)]
  exact mul_le_mul_of_nonneg_left
    (l2Norm_l2VectorClip_sub_l2VectorClip_le C hC.le x y)
    (inv_nonneg.mpr hC.le)

theorem abs_inv_sub_inv_mul_right
    (C D : ℝ) (hC : 0 < C) (hD : 0 < D) :
    |C⁻¹ - D⁻¹| * D = C⁻¹ * |C - D| := by
  rw [inv_sub_inv hC.ne' hD.ne', abs_div, abs_mul,
    abs_of_pos hC, abs_of_pos hD, abs_sub_comm]
  field_simp [hC.ne', hD.ne']

/-- Joint normalized-clip comparison before replacing positive radii by a
common floor. -/
theorem normalizedL2VectorClip_joint_le_explicit
    {ι : Type*} [Fintype ι]
    (C D : ℝ) (hC : 0 < C) (hD : 0 < D) (x y : ι → ℝ) :
    l2Norm ((C⁻¹) • l2VectorClip C x - (D⁻¹) • l2VectorClip D y) ≤
      C⁻¹ * l2Norm (x - y) + C⁻¹ * |C - D| +
        |C⁻¹ - D⁻¹| * D := by
  have htri (a b c : ι → ℝ) :
      l2Norm (a - c) ≤ l2Norm (a - b) + l2Norm (b - c) := by
    have heq : a - c = (a - b) + (b - c) := by abel
    rw [heq]
    exact l2Norm_add_le _ _
  have hinput := normalizedL2VectorClip_sub_le C hC x y
  have hradius :
      l2Norm (l2VectorClip C y - l2VectorClip D y) ≤ |C - D| := by
    change ‖toEuclidean (l2VectorClip C y - l2VectorClip D y)‖ ≤ |C - D|
    rw [show toEuclidean (l2VectorClip C y - l2VectorClip D y) =
      toEuclidean (l2VectorClip C y) - toEuclidean (l2VectorClip D y) by rfl,
      toEuclidean_l2VectorClip, toEuclidean_l2VectorClip]
    exact euclideanBallClip_radius_le C D hC.le hD.le (toEuclidean y)
  have hscaledRadius :
      l2Norm ((C⁻¹) • l2VectorClip C y - (C⁻¹) • l2VectorClip D y) ≤
        C⁻¹ * |C - D| := by
    rw [← smul_sub, l2Norm_smul, abs_of_pos (inv_pos.mpr hC)]
    exact mul_le_mul_of_nonneg_left hradius (inv_nonneg.mpr hC.le)
  have hinvChange :
      l2Norm ((C⁻¹) • l2VectorClip D y - (D⁻¹) • l2VectorClip D y) ≤
        |C⁻¹ - D⁻¹| * D := by
    rw [← sub_smul, l2Norm_smul]
    exact mul_le_mul_of_nonneg_left (l2VectorClip_norm_le D y hD.le)
      (abs_nonneg _)
  calc
    l2Norm ((C⁻¹) • l2VectorClip C x - (D⁻¹) • l2VectorClip D y) ≤
        l2Norm ((C⁻¹) • l2VectorClip C x - (C⁻¹) • l2VectorClip C y) +
          l2Norm ((C⁻¹) • l2VectorClip C y - (D⁻¹) • l2VectorClip D y) :=
      htri _ _ _
    _ ≤ l2Norm ((C⁻¹) • l2VectorClip C x - (C⁻¹) • l2VectorClip C y) +
        (l2Norm ((C⁻¹) • l2VectorClip C y - (C⁻¹) • l2VectorClip D y) +
          l2Norm ((C⁻¹) • l2VectorClip D y - (D⁻¹) • l2VectorClip D y)) :=
      add_le_add_right (htri
        ((C⁻¹) • l2VectorClip C y)
        ((C⁻¹) • l2VectorClip D y)
        ((D⁻¹) • l2VectorClip D y)) _
    _ ≤ C⁻¹ * l2Norm (x - y) +
        (C⁻¹ * |C - D| + |C⁻¹ - D⁻¹| * D) :=
      add_le_add hinput (add_le_add hscaledRadius hinvChange)
    _ = C⁻¹ * l2Norm (x - y) + C⁻¹ * |C - D| +
        |C⁻¹ - D⁻¹| * D := by ring

/-- Joint normalized-clip stability with an explicit positive radius floor. -/
theorem normalizedL2VectorClip_joint_le_floor
    {ι : Type*} [Fintype ι]
    (cmin C D : ℝ) (hcmin : 0 < cmin)
    (hC : cmin ≤ C) (hD : cmin ≤ D) (x y : ι → ℝ) :
    l2Norm ((C⁻¹) • l2VectorClip C x - (D⁻¹) • l2VectorClip D y) ≤
      cmin⁻¹ * (l2Norm (x - y) + 2 * |C - D|) := by
  have hCpos : 0 < C := lt_of_lt_of_le hcmin hC
  have hDpos : 0 < D := lt_of_lt_of_le hcmin hD
  have hinv : C⁻¹ ≤ cmin⁻¹ := inv_anti₀ hcmin hC
  have h := normalizedL2VectorClip_joint_le_explicit C D hCpos hDpos x y
  rw [abs_inv_sub_inv_mul_right C D hCpos hDpos] at h
  calc
    l2Norm ((C⁻¹) • l2VectorClip C x - (D⁻¹) • l2VectorClip D y) ≤
        C⁻¹ * l2Norm (x - y) + C⁻¹ * |C - D| + C⁻¹ * |C - D| := h
    _ ≤ cmin⁻¹ * l2Norm (x - y) + cmin⁻¹ * |C - D| +
          cmin⁻¹ * |C - D| := by
      have h1 := mul_le_mul_of_nonneg_right hinv (l2Norm_nonneg (x - y))
      have h2 := mul_le_mul_of_nonneg_right hinv (abs_nonneg (C - D))
      linarith
    _ = cmin⁻¹ * (l2Norm (x - y) + 2 * |C - D|) := by ring

/-- Regression guard: the regularity theorems are about the explicit
Euclidean norm, not the ambient Pi/sup norm. -/
theorem euclideanClippingRegularity_piNormRegression :
    ‖(fun _ : Fin 2 => (1 : ℝ))‖ ≠
      l2Norm (fun _ : Fin 2 => (1 : ℝ)) :=
  piNorm_ne_l2Norm_finTwo

/-- Concrete normalized-clip check in two Euclidean coordinates. -/
theorem normalizedL2VectorClip_finTwo_regression :
    l2Norm (((2 : ℝ)⁻¹) •
      l2VectorClip 2 (fun _ : Fin 2 => (3 : ℝ))) ≤ 1 := by
  exact normalizedL2VectorClip_norm_le_one 2 (by norm_num)
    (fun _ : Fin 2 => (3 : ℝ))

end
end DP
end Mf
