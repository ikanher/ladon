import Mf.DP.FDPSubsampling
import Mf.DP.ProductGaussianMixtureProfileDomination
import Mf.DP.PrivacyObjectSurface

namespace Mf
namespace DP

noncomputable section

/-!
Lower exact represented surface beneath `TradeoffFunction.withIdentityWeight`.

The current generic exact subsampling layer only transports an already-exact
object through the public `subsampleTradeoffAt` / `C_p` surface. This file
lands the missing lower representation layer for the raw asymmetric `f_p`
surface:

- a represented shared-base density pair that still remembers the underlying
  base measure and densities,
- the exact `PLDPair` and privacy-object packaging induced by that data,
- and a branch-tagged Bernoulli mixture construction on `Bool × α`.

Current honest boundary:
- this file does not yet prove that the public
  `TradeoffFunction.withIdentityWeight` surface is the extracted tradeoff of the
  new branch-tagged exact object,
- so the theorem-facing hook back to the public `f_p` surface remains the next
  proof seam above this representation layer.
-/

/--
Exact represented shared-base density pair.

Unlike `PLDPair` or `PrivacyObject`, this object retains the underlying base
measure and both densities, so later exact subsampling constructions can still
speak about the neighboring laws themselves rather than only their privacy-loss
laws.
-/
structure RepresentedDensityPair (α : Type) [MeasurableSpace α] where
  baseMeasure : MeasureTheory.Measure α
  leftDensity : α → ℝ
  rightDensity : α → ℝ
  leftMeasurable : Measurable leftDensity
  rightMeasurable : Measurable rightDensity

namespace RepresentedDensityPair

open MeasureTheory

/-- Exact `PLDPair` induced by the represented shared-base density pair. -/
def toPLDPair {α : Type} [MeasurableSpace α]
    (pair : RepresentedDensityPair α) : PLDPair :=
  concretePLDPair pair.baseMeasure pair.leftDensity pair.rightDensity

/-- Privacy-object view of the represented shared-base density pair. -/
def toPrivacyObject {α : Type} [MeasurableSpace α]
    (pair : RepresentedDensityPair α) : PrivacyObject :=
  PrivacyObject.ofPLDPair pair.toPLDPair

/-- Public fixed-`ε` tradeoff witness extracted from the represented pair. -/
def tradeoffAt {α : Type} [MeasurableSpace α]
    (pair : RepresentedDensityPair α) (ε : ℝ) : TradeoffFunction :=
  pair.toPrivacyObject.tradeoffAt ε

@[simp] theorem toPLDPair_eq
    {α : Type} [MeasurableSpace α]
    (pair : RepresentedDensityPair α) :
    pair.toPLDPair =
      concretePLDPair pair.baseMeasure pair.leftDensity pair.rightDensity := rfl

@[simp] theorem toPrivacyObject_profile_eval
    {α : Type} [MeasurableSpace α]
    (pair : RepresentedDensityPair α) :
    pair.toPrivacyObject.profile.eval = pair.toPLDPair.profile := rfl

@[simp] theorem tradeoffAt_eq
    {α : Type} [MeasurableSpace α]
    (pair : RepresentedDensityPair α) (ε : ℝ) :
    pair.tradeoffAt ε = (PrivacyObject.ofPLDPair pair.toPLDPair).tradeoffAt ε := rfl

/-- The ideal branch is any represented pair with identical left/right densities. -/
def idealOfDensity {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (dens : α → ℝ)
    (hdens : Measurable dens) : RepresentedDensityPair α where
  baseMeasure := μ
  leftDensity := dens
  rightDensity := dens
  leftMeasurable := hdens
  rightMeasurable := hdens

@[simp] theorem idealOfDensity_left_eq_right
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (dens : α → ℝ)
    (hdens : Measurable dens) :
    (idealOfDensity μ dens hdens).leftDensity =
      (idealOfDensity μ dens hdens).rightDensity := rfl

/-- Counting × base measure used by the branch-tagged exact raw subsampling surface. -/
def branchBaseMeasure {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) : MeasureTheory.Measure (Bool × α) :=
  MeasureTheory.Measure.count.prod μ

/-- Left density for the branch-tagged raw exact subsampling surface. -/
def withIdentityWeightLeftDensity {α : Type} [MeasurableSpace α]
    (w : ℝ)
    (common left : α → ℝ) : Bool × α → ℝ :=
  fun z => if z.1 then w * left z.2 else (1 - w) * common z.2

/-- Right density for the branch-tagged raw exact subsampling surface. -/
def withIdentityWeightRightDensity {α : Type} [MeasurableSpace α]
    (w : ℝ)
    (common right : α → ℝ) : Bool × α → ℝ :=
  fun z => if z.1 then w * right z.2 else (1 - w) * common z.2

theorem measurable_withIdentityWeightLeftDensity
    {α : Type} [MeasurableSpace α]
    (w : ℝ)
    {common left : α → ℝ}
    (hcommon : Measurable common)
    (hleft : Measurable left) :
    Measurable (withIdentityWeightLeftDensity w common left) := by
  classical
  have hset : MeasurableSet {z : Bool × α | z.1 = true} := by
    exact measurable_fst (measurableSet_singleton true)
  refine Measurable.piecewise ?_ ?_ ?_
  · exact hset
  · exact measurable_const.mul (hleft.comp measurable_snd)
  · exact measurable_const.mul (hcommon.comp measurable_snd)

theorem measurable_withIdentityWeightRightDensity
    {α : Type} [MeasurableSpace α]
    (w : ℝ)
    {common right : α → ℝ}
    (hcommon : Measurable common)
    (hright : Measurable right) :
    Measurable (withIdentityWeightRightDensity w common right) := by
  classical
  have hset : MeasurableSet {z : Bool × α | z.1 = true} := by
    exact measurable_fst (measurableSet_singleton true)
  refine Measurable.piecewise ?_ ?_ ?_
  · exact hset
  · exact measurable_const.mul (hright.comp measurable_snd)
  · exact measurable_const.mul (hcommon.comp measurable_snd)

/--
Branch-tagged exact represented density pair beneath the raw asymmetric `f_p`
surface.

The `true` branch carries the active neighboring densities; the `false` branch
carries a common density on both sides.
-/
def withIdentityWeightBranchPair {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (w : ℝ)
    (common left right : α → ℝ)
    (hcommon : Measurable common)
    (hleft : Measurable left)
    (hright : Measurable right) :
    RepresentedDensityPair (Bool × α) where
  baseMeasure := branchBaseMeasure μ
  leftDensity := withIdentityWeightLeftDensity w common left
  rightDensity := withIdentityWeightRightDensity w common right
  leftMeasurable := measurable_withIdentityWeightLeftDensity w hcommon hleft
  rightMeasurable := measurable_withIdentityWeightRightDensity w hcommon hright

@[simp] theorem withIdentityWeightBranchPair_baseMeasure
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (w : ℝ)
    (common left right : α → ℝ)
    (hcommon : Measurable common)
    (hleft : Measurable left)
    (hright : Measurable right) :
    (withIdentityWeightBranchPair μ w common left right hcommon hleft hright).baseMeasure =
      branchBaseMeasure μ := rfl

@[simp] theorem withIdentityWeightBranchPair_leftDensity
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (w : ℝ)
    (common left right : α → ℝ)
    (hcommon : Measurable common)
    (hleft : Measurable left)
    (hright : Measurable right) :
    (withIdentityWeightBranchPair μ w common left right hcommon hleft hright).leftDensity =
      withIdentityWeightLeftDensity w common left := rfl

@[simp] theorem withIdentityWeightBranchPair_rightDensity
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (w : ℝ)
    (common left right : α → ℝ)
    (hcommon : Measurable common)
    (hleft : Measurable left)
    (hright : Measurable right) :
    (withIdentityWeightBranchPair μ w common left right hcommon hleft hright).rightDensity =
      withIdentityWeightRightDensity w common right := rfl

/--
On the common branch, the left and right densities agree exactly.

This is the exact lower representation of the ideal branch that later proofs
must connect back to the public `Id` witness.
-/
theorem withIdentityWeightBranchPair_common_branch_eq
    {α : Type} [MeasurableSpace α]
    (w : ℝ)
    {common left right : α → ℝ}
    (z : Bool × α)
    (hz : z.1 = false) :
    withIdentityWeightLeftDensity w common left z =
      withIdentityWeightRightDensity w common right z := by
  simp [withIdentityWeightLeftDensity, withIdentityWeightRightDensity, hz]

/--
On the active branch, the branch-tagged pair reduces to the weighted active
neighboring densities.
-/
theorem withIdentityWeightBranchPair_active_branch_eq
    {α : Type} [MeasurableSpace α]
    (w : ℝ)
    {common left right : α → ℝ}
    (z : Bool × α)
    (hz : z.1 = true) :
    withIdentityWeightLeftDensity w common left z = w * left z.2 ∧
      withIdentityWeightRightDensity w common right z = w * right z.2 := by
  simp [withIdentityWeightLeftDensity, withIdentityWeightRightDensity, hz]

/--
The branch-tagged represented object packages immediately to an exact
`PLDPair`.
-/
@[simp] theorem withIdentityWeightBranchPair_toPLDPair_eq
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (w : ℝ)
    (common left right : α → ℝ)
    (hcommon : Measurable common)
    (hleft : Measurable left)
    (hright : Measurable right) :
    (withIdentityWeightBranchPair μ w common left right hcommon hleft hright).toPLDPair =
      concretePLDPair
        (branchBaseMeasure μ)
        (withIdentityWeightLeftDensity w common left)
        (withIdentityWeightRightDensity w common right) := rfl

/--
The branch-tagged represented object packages immediately to a privacy object.
-/
@[simp] theorem withIdentityWeightBranchPair_toPrivacyObject_eq
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (w : ℝ)
    (common left right : α → ℝ)
    (hcommon : Measurable common)
    (hleft : Measurable left)
    (hright : Measurable right) :
    (withIdentityWeightBranchPair μ w common left right hcommon hleft hright).toPrivacyObject =
      PrivacyObject.ofPLDPair
        (concretePLDPair
          (branchBaseMeasure μ)
          (withIdentityWeightLeftDensity w common left)
          (withIdentityWeightRightDensity w common right)) := rfl

/--
Concrete shared-base profile identity restated on the theorem-facing surface.

This is the exact packaging hook later branch constructions use to compare a
represented density pair against a public `tradeoffAt` witness at fixed `ε`.
-/
theorem concretePLDPair_profile_eq_sourceHockeyStickIntegral
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (p q : α → ℝ)
    (ε : ℝ)
    (hp : Measurable p)
    (hq : Measurable q)
    (hpp : ∀ x, 0 < p x)
    (hqq : ∀ x, 0 < q x) :
    (concretePLDPair μ p q).profile ε =
      ∫ x, sourceHockeyStickGapIntegrand ε p q x ∂ μ := by
  rw [PLDPair.profile, concretePLDPair, forwardLossLaw]
  simpa using
    expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
      (μ := μ) (f := p) (g := q) (ε := ε) hp hq hpp hqq

private theorem integrable_sourceHockeyStickGapIntegrand_of_integrable
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (p q : α → ℝ)
    (ε : ℝ)
    (hp : Measurable p)
    (hq : Measurable q)
    (hp_int : Integrable p μ)
    (hq_int : Integrable q μ)
    (hpp : ∀ x, 0 < p x)
    (hqq : ∀ x, 0 < q x) :
    Integrable (sourceHockeyStickGapIntegrand ε p q) μ := by
  let upper : α → ℝ := fun x => p x + Real.exp ε * q x
  have hupper : Integrable upper μ := hp_int.add (hq_int.const_mul (Real.exp ε))
  refine Integrable.mono' hupper ?_ ?_
  · refine Measurable.aestronglyMeasurable ?_
    unfold sourceHockeyStickGapIntegrand
    fun_prop
  · exact Filter.Eventually.of_forall fun x => by
      have hnonneg : 0 ≤ sourceHockeyStickGapIntegrand ε p q x := by
        unfold sourceHockeyStickGapIntegrand
        exact le_max_right _ _
      simp only [Real.norm_eq_abs, abs_of_nonneg hnonneg]
      unfold upper sourceHockeyStickGapIntegrand
      by_cases hgap : p x - Real.exp ε * q x ≤ 0
      · rw [max_eq_right hgap]
        have hp_nonneg : 0 ≤ p x := le_of_lt (hpp x)
        have hq_nonneg : 0 ≤ q x := le_of_lt (hqq x)
        positivity
      · rw [max_eq_left (le_of_lt (lt_of_not_ge hgap))]
        have hq_nonneg : 0 ≤ q x := le_of_lt (hqq x)
        have hterm : -(Real.exp ε * q x) ≤ Real.exp ε * q x := by
          nlinarith [Real.exp_pos ε, hq_nonneg]
        linarith

private theorem integrable_branchWeightedSourceGap
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    [SFinite μ]
    (w : ℝ)
    (g : α → ℝ)
    (hg : Measurable g)
    (hg_int : Integrable g μ) :
    Integrable (fun z : Bool × α => if z.1 then w * g z.2 else 0) (branchBaseMeasure μ) := by
  have hsm :
      AEStronglyMeasurable (fun z : Bool × α => if z.1 then w * g z.2 else 0)
        (branchBaseMeasure μ) := by
    refine Measurable.aestronglyMeasurable ?_
    have hset : MeasurableSet {z : Bool × α | z.1 = true} := by
      exact measurable_fst (measurableSet_singleton true)
    refine Measurable.piecewise hset ?_ ?_
    · exact (measurable_const.mul (hg.comp measurable_snd))
    · exact measurable_const
  rw [branchBaseMeasure, MeasureTheory.integrable_prod_iff' hsm]
  constructor
  · simp
  · simpa using (hg_int.const_mul w).norm

/--
When the common branch is the right density itself, the exact represented
branch-tagged object scales the active privacy profile by `w`.

This is the first honest realization hook from the represented lower
subsampling object back to a theorem-facing public privacy quantity.
-/
theorem withIdentityWeightBranchPair_profile_eq_weight_mul_of_common_eq_right
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    [SFinite μ]
    (w ε : ℝ)
    (p q : α → ℝ)
    (hp : Measurable p)
    (hq : Measurable q)
    (hp_int : Integrable p μ)
    (hq_int : Integrable q μ)
    (hpp : ∀ x, 0 < p x)
    (hqq : ∀ x, 0 < q x)
    (hw0 : 0 < w)
    (hw1 : w < 1)
    (hε : 0 ≤ ε) :
    ((withIdentityWeightBranchPair μ w q p q hq hp hq).toPLDPair).profile ε =
      w * (concretePLDPair μ p q).profile ε := by
  have hleft_pos : ∀ z : Bool × α, 0 < withIdentityWeightLeftDensity w q p z := by
    intro z
    by_cases hz : z.1 = true
    · simp [withIdentityWeightLeftDensity, hz, hw0, hpp z.2]
    · have hz' : z.1 = false := by
        cases hbool : z.1 with
        | false => simpa using hbool
        | true => exact False.elim (hz hbool)
      have h1w : 0 < 1 - w := by linarith
      simpa [withIdentityWeightLeftDensity, hz'] using mul_pos h1w (hqq z.2)
  have hright_pos : ∀ z : Bool × α, 0 < withIdentityWeightRightDensity w q q z := by
    intro z
    by_cases hz : z.1 = true
    · simp [withIdentityWeightRightDensity, hz, hw0, hqq z.2]
    · have hz' : z.1 = false := by
        cases hbool : z.1 with
        | false => simpa using hbool
        | true => exact False.elim (hz hbool)
      have h1w : 0 < 1 - w := by linarith
      simpa [withIdentityWeightRightDensity, hz'] using mul_pos h1w (hqq z.2)
  have hactive_gap_int :
      Integrable (sourceHockeyStickGapIntegrand ε p q) μ :=
    integrable_sourceHockeyStickGapIntegrand_of_integrable
      μ p q ε hp hq hp_int hq_int hpp hqq
  rw [withIdentityWeightBranchPair_toPLDPair_eq]
  rw [concretePLDPair_profile_eq_sourceHockeyStickIntegral
    (μ := branchBaseMeasure μ)
    (p := withIdentityWeightLeftDensity w q p)
    (q := withIdentityWeightRightDensity w q q)
    (ε := ε)
    (hp := measurable_withIdentityWeightLeftDensity w hq hp)
    (hq := measurable_withIdentityWeightRightDensity w hq hq)
    (hpp := hleft_pos)
    (hqq := hright_pos)]
  rw [concretePLDPair_profile_eq_sourceHockeyStickIntegral
    (μ := μ) (p := p) (q := q) (ε := ε) hp hq hpp hqq]
  have hgap_eq :
      ∀ z : Bool × α,
        sourceHockeyStickGapIntegrand ε
            (withIdentityWeightLeftDensity w q p)
            (withIdentityWeightRightDensity w q q) z
          =
        if z.1 then w * sourceHockeyStickGapIntegrand ε p q z.2 else 0 := by
    intro z
    by_cases hz : z.1 = true
    · rw [sourceHockeyStickGapIntegrand]
      unfold sourceHockeyStickGapIntegrand
      simp [withIdentityWeightLeftDensity, withIdentityWeightRightDensity, hz]
      have hw_nonneg : 0 ≤ w := le_of_lt hw0
      rw [show w * p z.2 - Real.exp ε * (w * q z.2) =
          w * (p z.2 - Real.exp ε * q z.2) by ring]
      rw [mul_max_of_nonneg _ _ hw_nonneg, mul_zero]
    · have hz' : z.1 = false := by
        cases hbool : z.1 with
        | false => simpa using hbool
        | true => exact False.elim (hz hbool)
      rw [sourceHockeyStickGapIntegrand]
      have h1w_nonneg : 0 ≤ 1 - w := by linarith
      have hq_nonneg : 0 ≤ q z.2 := le_of_lt (hqq z.2)
      have hexp_ge_one : 1 ≤ Real.exp ε := Real.one_le_exp_iff.mpr hε
      have hOneMinus : 1 - Real.exp ε ≤ 0 := by nlinarith
      have hfalse_le :
          (1 - w) * q z.2 - Real.exp ε * ((1 - w) * q z.2) ≤ 0 := by
        calc
          (1 - w) * q z.2 - Real.exp ε * ((1 - w) * q z.2)
            = ((1 - w) * q z.2) * (1 - Real.exp ε) := by ring
          _ ≤ 0 := mul_nonpos_of_nonneg_of_nonpos
            (mul_nonneg h1w_nonneg hq_nonneg) hOneMinus
      simp [withIdentityWeightLeftDensity, withIdentityWeightRightDensity, hz', max_eq_right hfalse_le]
  have hbranch_int :
      ∫ z : Bool × α,
          sourceHockeyStickGapIntegrand ε
            (withIdentityWeightLeftDensity w q p)
            (withIdentityWeightRightDensity w q q) z
          ∂ branchBaseMeasure μ
        =
      w * ∫ x, sourceHockeyStickGapIntegrand ε p q x ∂ μ := by
    calc
      ∫ z : Bool × α,
          sourceHockeyStickGapIntegrand ε
            (withIdentityWeightLeftDensity w q p)
            (withIdentityWeightRightDensity w q q) z
          ∂ branchBaseMeasure μ
        =
      ∫ z : Bool × α, (if z.1 then w * sourceHockeyStickGapIntegrand ε p q z.2 else 0)
          ∂ branchBaseMeasure μ := by
            refine integral_congr_ae ?_
            exact Filter.Eventually.of_forall hgap_eq
      _ =
      ∫ b : Bool, ∫ x, (if b then w * sourceHockeyStickGapIntegrand ε p q x else 0) ∂ μ
          ∂ MeasureTheory.Measure.count := by
            rw [branchBaseMeasure, MeasureTheory.integral_prod]
            exact integrable_branchWeightedSourceGap μ w
              (sourceHockeyStickGapIntegrand ε p q)
              (by
                unfold sourceHockeyStickGapIntegrand
                fun_prop)
              hactive_gap_int
      _ = w * ∫ x, sourceHockeyStickGapIntegrand ε p q x ∂ μ := by
            simp
            simpa using
              (MeasureTheory.integral_const_mul w
                (f := fun x => sourceHockeyStickGapIntegrand ε p q x))
  exact hbranch_int

/--
At fixed `ε`, the represented branch-tagged exact object yields the expected
linear tradeoff witness with profile `w * δ_active(ε)`.
-/
theorem withIdentityWeightBranchPair_tradeoffAt_eval_eq_weight_mul_profile_of_common_eq_right
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    [SFinite μ]
    (w ε a : ℝ)
    (p q : α → ℝ)
    (hp : Measurable p)
    (hq : Measurable q)
    (hp_int : Integrable p μ)
    (hq_int : Integrable q μ)
    (hpp : ∀ x, 0 < p x)
    (hqq : ∀ x, 0 < q x)
    (hw0 : 0 < w)
    (hw1 : w < 1)
    (hε : 0 ≤ ε) :
    ((withIdentityWeightBranchPair μ w q p q hq hp hq).tradeoffAt ε).eval a =
      1 - w * (concretePLDPair μ p q).profile ε - Real.exp ε * a := by
  rw [tradeoffAt_eq, PrivacyObject.tradeoffAt_eval, PrivacyObject.ofPLDPair_profile_eval]
  rw [withIdentityWeightBranchPair_profile_eq_weight_mul_of_common_eq_right
    (μ := μ) (w := w) (ε := ε) (p := p) (q := q)
    hp hq hp_int hq_int hpp hqq hw0 hw1 hε]

/--
On the natural `α >= 0` tradeoff window, the represented branch-tagged exact
object stays below the public weighted branch `f_p` built from the active
privacy object.

This is the current honest dominance hook back to the public
`TradeoffFunction.withIdentityWeight` surface. It does not claim equality of
the two public witnesses, because the represented branch object and the public
`withIdentityWeight` operator have different affine slopes in `α`.
-/
theorem withIdentityWeightBranchPair_tradeoffAt_eval_le_withIdentityWeight_of_common_eq_right
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    [SFinite μ]
    (w ε a : ℝ)
    (p q : α → ℝ)
    (hp : Measurable p)
    (hq : Measurable q)
    (hp_int : Integrable p μ)
    (hq_int : Integrable q μ)
    (hpp : ∀ x, 0 < p x)
    (hqq : ∀ x, 0 < q x)
    (hw0 : 0 < w)
    (hw1 : w < 1)
    (hε : 0 ≤ ε)
    (ha0 : 0 ≤ a) :
    ((withIdentityWeightBranchPair μ w q p q hq hp hq).tradeoffAt ε).eval a ≤
      (TradeoffFunction.withIdentityWeight w
        ((PrivacyObject.ofPLDPair (concretePLDPair μ p q)).tradeoffAt ε)).eval a := by
  rw [withIdentityWeightBranchPair_tradeoffAt_eval_eq_weight_mul_profile_of_common_eq_right
    (μ := μ) (w := w) (ε := ε) (a := a) (p := p) (q := q)
    hp hq hp_int hq_int hpp hqq hw0 hw1 hε]
  rw [TradeoffFunction.withIdentityWeight_eval, PrivacyObject.tradeoffAt_eval,
    PrivacyObject.ofPLDPair_profile_eval]
  have hw_le : w ≤ 1 := le_of_lt hw1
  have hexp_ge_one : 1 ≤ Real.exp ε := Real.one_le_exp_iff.mpr hε
  have hcoeff_le : 1 + w * (Real.exp ε - 1) ≤ Real.exp ε := by
    nlinarith
  have hmul_le : (1 + w * (Real.exp ε - 1)) * a ≤ Real.exp ε * a := by
    exact mul_le_mul_of_nonneg_right hcoeff_le ha0
  ring_nf
  linarith

/--
Unit-interval wrapper for the represented-to-public weighted-branch dominance
hook.
-/
theorem withIdentityWeightBranchPair_tradeoffAt_eval_le_withIdentityWeight_of_common_eq_right_of_mem_unitInterval
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    [SFinite μ]
    (w ε a : ℝ)
    (p q : α → ℝ)
    (hp : Measurable p)
    (hq : Measurable q)
    (hp_int : Integrable p μ)
    (hq_int : Integrable q μ)
    (hpp : ∀ x, 0 < p x)
    (hqq : ∀ x, 0 < q x)
    (hw0 : 0 < w)
    (hw1 : w < 1)
    (hε : 0 ≤ ε)
    (ha : a ∈ TradeoffFunction.unitInterval) :
    ((withIdentityWeightBranchPair μ w q p q hq hp hq).tradeoffAt ε).eval a ≤
      (TradeoffFunction.withIdentityWeight w
        ((PrivacyObject.ofPLDPair (concretePLDPair μ p q)).tradeoffAt ε)).eval a := by
  exact withIdentityWeightBranchPair_tradeoffAt_eval_le_withIdentityWeight_of_common_eq_right
    μ w ε a p q hp hq hp_int hq_int hpp hqq hw0 hw1 hε ha.1

end RepresentedDensityPair

end
end DP
end Mf
