import Mf.DP.GaussianDP

namespace Mf
namespace DP

noncomputable section

/-!
`f`-DP subsampling operator surface.

This module opens the first theorem-facing subsampling operator layer for the
tradeoff-function surface. The local `mu-dp` literature defines the
`p`-sampling operator by

`C_p(f) = min { f_p, f_p⁻¹ }**`,

where `f_p = p f + (1 - p) Id`. The present Lean surface exposes the named
ingredients `Id`, `f_p`, the left-continuous inverse, and the first
symmetrized lower-envelope operator. Later changes can refine this to the full
convexified `C_p` without changing the outer API.

Literature anchors:
- `paper/theory/mu-dp/subsample.tex`
- `paper/theory/mu-dp/fDP/tradeoff.tex`
- `paper/theory/mu-dp/appendices/property.tex`
-/

namespace TradeoffFunction

/-- The clipped unit interval on which the theorem-facing convexification acts. -/
def unitInterval : Set ℝ := Set.Icc (0 : ℝ) 1

/-- Perfect privacy tradeoff, denoted `Id` in the paper. -/
def ideal : TradeoffFunction where
  eval := fun α => 1 - α
  unit_bddBelow := by
    refine ⟨0, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hα1 : (α : ℝ) ≤ 1 := α.2.2
    linarith
  unit_bddAbove := by
    refine ⟨1, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hα0 : 0 ≤ (α : ℝ) := α.2.1
    linarith

/-- The convex combination `f_p = p f + (1 - p) Id`. -/
def withIdentityWeight (p : ℝ) (T : TradeoffFunction) : TradeoffFunction where
  eval := fun α => p * T.eval α + (1 - p) * (ideal.eval α)
  unit_bddBelow := by
    rcases T.unit_bddBelow with ⟨mT, hmT⟩
    rcases T.unit_bddAbove with ⟨MT, hMT⟩
    refine ⟨-(|p| * max |mT| |MT| + |1 - p|), ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hT_lower : mT ≤ T.eval α := hmT ⟨α, rfl⟩
    have hT_upper : T.eval α ≤ MT := hMT ⟨α, rfl⟩
    have hTabs : |T.eval α| ≤ max |mT| |MT| := by
      refine abs_le.mpr ?_
      constructor
      · have hmAbs : -max |mT| |MT| ≤ mT := by
          have hmax : |mT| ≤ max |mT| |MT| := le_max_left _ _
          nlinarith [neg_abs_le mT, hmax]
        exact le_trans hmAbs hT_lower
      · have hMAbs : MT ≤ max |mT| |MT| := by
          have hM1 : MT ≤ |MT| := by exact le_abs_self MT
          exact le_trans hM1 (le_max_right _ _)
        exact le_trans hT_upper hMAbs
    have hIdeal_nonneg : 0 ≤ ideal.eval α := by
      have hα1 : (α : ℝ) ≤ 1 := α.2.2
      simpa [ideal] using sub_nonneg.mpr hα1
    have hIdealAbs : |ideal.eval α| ≤ 1 := by
      have hIdeal_le_one : ideal.eval α ≤ 1 := by
        have hα0 : 0 ≤ (α : ℝ) := α.2.1
        simpa [ideal] using sub_le_self 1 hα0
      exact abs_le.mpr ⟨by nlinarith, hIdeal_le_one⟩
    have hAbs :
        |p * T.eval α + (1 - p) * ideal.eval α|
          ≤ |p| * max |mT| |MT| + |1 - p| := by
      calc
        |p * T.eval α + (1 - p) * ideal.eval α|
            ≤ |p * T.eval α| + |(1 - p) * ideal.eval α| := by
              exact abs_add_le _ _
        _ = |p| * |T.eval α| + |1 - p| * |ideal.eval α| := by
              rw [abs_mul, abs_mul]
        _ ≤ |p| * max |mT| |MT| + |1 - p| * 1 := by
              gcongr
        _ = |p| * max |mT| |MT| + |1 - p| := by ring
    have hAbsNonneg : 0 ≤ |p| * max |mT| |MT| + |1 - p| := by positivity
    exact (abs_le.mp (by simpa [hAbsNonneg] using hAbs)).1
  unit_bddAbove := by
    rcases T.unit_bddBelow with ⟨mT, hmT⟩
    rcases T.unit_bddAbove with ⟨MT, hMT⟩
    refine ⟨|p| * max |mT| |MT| + |1 - p|, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hT_lower : mT ≤ T.eval α := hmT ⟨α, rfl⟩
    have hT_upper : T.eval α ≤ MT := hMT ⟨α, rfl⟩
    have hTabs : |T.eval α| ≤ max |mT| |MT| := by
      refine abs_le.mpr ?_
      constructor
      · have hmAbs : -max |mT| |MT| ≤ mT := by
          have hmax : |mT| ≤ max |mT| |MT| := le_max_left _ _
          nlinarith [neg_abs_le mT, hmax]
        exact le_trans hmAbs hT_lower
      · have hMAbs : MT ≤ max |mT| |MT| := by
          have hM1 : MT ≤ |MT| := by exact le_abs_self MT
          exact le_trans hM1 (le_max_right _ _)
        exact le_trans hT_upper hMAbs
    have hIdeal_nonneg : 0 ≤ ideal.eval α := by
      have hα1 : (α : ℝ) ≤ 1 := α.2.2
      simpa [ideal] using sub_nonneg.mpr hα1
    have hIdealAbs : |ideal.eval α| ≤ 1 := by
      have hIdeal_le_one : ideal.eval α ≤ 1 := by
        have hα0 : 0 ≤ (α : ℝ) := α.2.1
        simpa [ideal] using sub_le_self 1 hα0
      exact abs_le.mpr ⟨by nlinarith, hIdeal_le_one⟩
    have hAbs :
        |p * T.eval α + (1 - p) * ideal.eval α|
          ≤ |p| * max |mT| |MT| + |1 - p| := by
      calc
        |p * T.eval α + (1 - p) * ideal.eval α|
            ≤ |p * T.eval α| + |(1 - p) * ideal.eval α| := by
              exact abs_add_le _ _
        _ = |p| * |T.eval α| + |1 - p| * |ideal.eval α| := by
              rw [abs_mul, abs_mul]
        _ ≤ |p| * max |mT| |MT| + |1 - p| * 1 := by
              gcongr
        _ = |p| * max |mT| |MT| + |1 - p| := by ring
    have hAbsNonneg : 0 ≤ |p| * max |mT| |MT| + |1 - p| := by positivity
    exact (abs_le.mp (by simpa [hAbsNonneg] using hAbs)).2

/--
Left-continuous inverse surface for a theorem-facing tradeoff object.

This is the paper's `f⁻¹` surface. At this layer we expose the inverse as a
named helper rather than proving the full tradeoff-function validity theorem.
-/
def leftInverseSet (T : TradeoffFunction) (α : ℝ) : Set ℝ :=
  {t : ℝ | 0 ≤ t ∧ t ≤ 1 ∧ T.eval t ≤ α} ∪ {1}

/-- Left-continuous inverse on the clipped tradeoff domain `[0, 1]`. -/
def leftContinuousInverse (T : TradeoffFunction) : TradeoffFunction where
  eval := fun α => sInf (leftInverseSet T α)
  unit_bddBelow := by
    refine ⟨0, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hNonempty : ({t : ℝ | 0 ≤ t ∧ t ≤ 1 ∧ T.eval t ≤ α.1} ∪ {1}).Nonempty := ⟨1, Or.inr rfl⟩
    refine le_csInf hNonempty ?_
    intro t ht
    rcases ht with ht | rfl
    · exact ht.1
    · norm_num
  unit_bddAbove := by
    refine ⟨1, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hBdd : BddBelow ({t : ℝ | 0 ≤ t ∧ t ≤ 1 ∧ T.eval t ≤ α.1} ∪ {1}) := by
      refine ⟨0, ?_⟩
      intro t ht
      rcases ht with ht | rfl
      · exact ht.1
      · norm_num
    have hOne : 1 ∈ ({t : ℝ | 0 ≤ t ∧ t ≤ 1 ∧ T.eval t ≤ α.1} ∪ {1}) := Or.inr rfl
    exact csInf_le hBdd hOne

/-- Convex lower-bound witness on the theorem-facing unit interval. -/
def IsConvexLowerBoundOnUnit (upper lower : TradeoffFunction) : Prop :=
  ConvexOn ℝ unitInterval lower.eval ∧
    ∀ ⦃α : ℝ⦄, α ∈ unitInterval → lower.eval α ≤ upper.eval α

/-- Values attained at `α` by convex lower bounds of `upper` on `[0,1]`. -/
def convexLowerValueSet (upper : TradeoffFunction) (α : ℝ) : Set ℝ :=
  {r : ℝ | ∃ lower : TradeoffFunction, IsConvexLowerBoundOnUnit upper lower ∧ lower.eval α = r}

theorem constAtUnitInf_isConvexLowerBoundOnUnit (upper : TradeoffFunction) :
    IsConvexLowerBoundOnUnit upper (TradeoffFunction.constAtUnitInf upper) := by
  constructor
  · simpa [TradeoffFunction.constAtUnitInf, TradeoffFunction.const, unitInterval] using
      (convexOn_const upper.unitInf (convex_Icc (0 : ℝ) 1))
  · intro α hα
    dsimp [TradeoffFunction.constAtUnitInf, TradeoffFunction.const, TradeoffFunction.unitInf]
    have hBdd : BddBelow upper.unitValueSet := upper.unit_bddBelow
    have hMem : upper.eval α ∈ upper.unitValueSet := ⟨⟨α, hα⟩, rfl⟩
    exact csInf_le hBdd hMem

/-- Greatest convex lower-envelope surface on the clipped unit interval. -/
def convexifiedLowerEnvelope (upper : TradeoffFunction) : TradeoffFunction where
  eval := fun α => by
    classical
    exact if hα : α ∈ unitInterval then
      sSup (convexLowerValueSet upper α)
    else
      upper.eval α
  unit_bddBelow := by
    classical
    refine ⟨upper.unitInf, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hα : (α : ℝ) ∈ unitInterval := α.2
    change upper.unitInf ≤
      (if h : (α : ℝ) ∈ unitInterval then sSup (convexLowerValueSet upper α) else upper.eval α)
    rw [dif_pos hα]
    have hBddAbove : BddAbove (convexLowerValueSet upper α) := by
      refine ⟨upper.eval α, ?_⟩
      intro r hr
      rcases hr with ⟨lower, hlower, rfl⟩
      exact hlower.2 hα
    have hConst :
        upper.unitInf ∈ convexLowerValueSet upper α := by
      refine ⟨TradeoffFunction.constAtUnitInf upper,
        constAtUnitInf_isConvexLowerBoundOnUnit upper, ?_⟩
      rfl
    exact le_csSup hBddAbove hConst
  unit_bddAbove := by
    classical
    rcases upper.unit_bddAbove with ⟨M, hM⟩
    refine ⟨M, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hα : (α : ℝ) ∈ unitInterval := α.2
    change
      (if h : (α : ℝ) ∈ unitInterval then sSup (convexLowerValueSet upper α) else upper.eval α) ≤ M
    rw [dif_pos hα]
    have hBddAbove : BddAbove (convexLowerValueSet upper α) := by
      refine ⟨upper.eval α, ?_⟩
      intro r hr
      rcases hr with ⟨lower, hlower, rfl⟩
      exact hlower.2 hα
    have hConst :
        upper.unitInf ∈ convexLowerValueSet upper α := by
      refine ⟨TradeoffFunction.constAtUnitInf upper,
        constAtUnitInf_isConvexLowerBoundOnUnit upper, ?_⟩
      rfl
    have hNonempty : (convexLowerValueSet upper α).Nonempty := by
      refine ⟨upper.unitInf, ?_⟩
      exact hConst
    have : sSup (convexLowerValueSet upper α) ≤ upper.eval α := by
      refine csSup_le hNonempty ?_
      intro r hr
      rcases hr with ⟨lower, hlower, rfl⟩
      exact hlower.2 hα
    exact le_trans this (hM ⟨α, rfl⟩)

/--
First symmetrized lower-envelope layer for the paper's `C_p` transform.

This exposes the paper's `min { f_p, f_p⁻¹ }` surface. A later change can add
the convexification step on top of the same API.
-/
def rawPSamplingOperator (p : ℝ) (T : TradeoffFunction) : TradeoffFunction where
  eval := fun α =>
    let weighted := withIdentityWeight p T
    min (weighted.eval α) ((leftContinuousInverse weighted).eval α)
  unit_bddBelow := by
    let weighted := withIdentityWeight p T
    rcases weighted.unit_bddBelow with ⟨mW, hmW⟩
    rcases (leftContinuousInverse weighted).unit_bddBelow with ⟨mI, hmI⟩
    refine ⟨min mW mI, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hWeighted : mW ≤ weighted.eval α := hmW ⟨α, rfl⟩
    have hInverse : mI ≤ (leftContinuousInverse weighted).eval α := hmI ⟨α, rfl⟩
    exact min_le_min hWeighted hInverse
  unit_bddAbove := by
    let weighted := withIdentityWeight p T
    rcases weighted.unit_bddAbove with ⟨MW, hMW⟩
    rcases (leftContinuousInverse weighted).unit_bddAbove with ⟨MI, hMI⟩
    refine ⟨max MW MI, ?_⟩
    intro y hy
    rcases hy with ⟨α, rfl⟩
    have hWeighted : weighted.eval α ≤ MW := hMW ⟨α, rfl⟩
    exact le_trans (min_le_left _ _) (le_trans hWeighted (le_max_left _ _))

/--
Named theorem-facing `p`-sampling operator surface.

At the current layer this coincides with `rawPSamplingOperator`; later
convexification work can refine the implementation behind this name.
-/
def pSamplingOperator (p : ℝ) (T : TradeoffFunction) : TradeoffFunction :=
  convexifiedLowerEnvelope (rawPSamplingOperator p T)

@[simp] theorem ideal_eval (α : ℝ) :
    ideal.eval α = 1 - α := rfl

@[simp] theorem withIdentityWeight_eval (p α : ℝ) (T : TradeoffFunction) :
    (withIdentityWeight p T).eval α = p * T.eval α + (1 - p) * (1 - α) := rfl

@[simp] theorem withIdentityWeight_zero (T : TradeoffFunction) :
    withIdentityWeight 0 T = ideal := by
  cases T
  simp [withIdentityWeight, ideal]

@[simp] theorem withIdentityWeight_one (T : TradeoffFunction) :
    withIdentityWeight 1 T = T := by
  cases T
  simp [withIdentityWeight]

@[simp] theorem leftContinuousInverse_eval (T : TradeoffFunction) (α : ℝ) :
    (leftContinuousInverse T).eval α = sInf (leftInverseSet T α) := rfl

@[simp] theorem rawPSamplingOperator_eval (p α : ℝ) (T : TradeoffFunction) :
    (rawPSamplingOperator p T).eval α =
      min ((withIdentityWeight p T).eval α)
        ((leftContinuousInverse (withIdentityWeight p T)).eval α) := rfl

@[simp] theorem pSamplingOperator_eval (p α : ℝ) (T : TradeoffFunction) :
    (pSamplingOperator p T).eval α =
      by
        classical
        exact
      if α ∈ unitInterval then
        sSup (convexLowerValueSet (rawPSamplingOperator p T) α)
      else
        min ((withIdentityWeight p T).eval α)
          ((leftContinuousInverse (withIdentityWeight p T)).eval α) := by
  classical
  rfl

theorem pointwiseLE_trans
    {A B C : TradeoffFunction}
    (hAB : A.PointwiseLE B)
    (hBC : B.PointwiseLE C) :
    A.PointwiseLE C := by
  intro α
  exact le_trans (hAB α) (hBC α)

/--
Taking the convex combination with `Id` preserves pointwise order for
nonnegative sampling ratios.
-/
theorem withIdentityWeight_mono
    {p : ℝ}
    (hp : 0 ≤ p)
    {T U : TradeoffFunction}
    (hTU : T.PointwiseLE U) :
    (withIdentityWeight p T).PointwiseLE (withIdentityWeight p U) := by
  intro α
  have hα : T.eval α ≤ U.eval α := hTU α
  dsimp [withIdentityWeight]
  nlinarith

/--
Pointwise order lifts to the left-continuous inverse surface.

This is the order fact used in the local subsampling discussion:
larger tradeoff lower bounds have larger inverse lower bounds as well.
-/
theorem leftContinuousInverse_mono
    {T U : TradeoffFunction}
    (hTU : T.PointwiseLE U) :
    (leftContinuousInverse T).PointwiseLE (leftContinuousInverse U) := by
  intro α
  dsimp [leftContinuousInverse]
  have hsubset : leftInverseSet U α ⊆ leftInverseSet T α := by
    intro t ht
    rcases ht with ht | rfl
    · exact Or.inl ⟨ht.1, ht.2.1, le_trans (hTU t) ht.2.2⟩
    · exact Or.inr rfl
  have hT_bdd : BddBelow (leftInverseSet T α) := by
    refine ⟨0, ?_⟩
    intro t ht
    rcases ht with ht | rfl
    · exact ht.1
    · norm_num
  have hU_nonempty : (leftInverseSet U α).Nonempty := ⟨1, Or.inr rfl⟩
  refine le_csInf hU_nonempty ?_
  intro t ht
  exact csInf_le hT_bdd (hsubset ht)

/-- The convexified lower envelope stays below its source surface. -/
theorem convexifiedLowerEnvelope_le
    (T : TradeoffFunction) :
    (convexifiedLowerEnvelope T).PointwiseLE T := by
  intro α
  by_cases hα : α ∈ unitInterval
  · classical
    have hEval :
        (convexifiedLowerEnvelope T).eval α =
          if h : α ∈ unitInterval then sSup (convexLowerValueSet T α) else T.eval α := rfl
    rw [hEval]
    have hIf :
        (if h : α ∈ unitInterval then sSup (convexLowerValueSet T α) else T.eval α) =
          sSup (convexLowerValueSet T α) := by
      simp [hα]
    rw [hIf]
    have hBddAbove : BddAbove (convexLowerValueSet T α) := by
      refine ⟨T.eval α, ?_⟩
      intro r hr
      rcases hr with ⟨lower, hlower, rfl⟩
      exact hlower.2 hα
    have hNonempty : (convexLowerValueSet T α).Nonempty := by
      refine ⟨T.unitInf, ?_⟩
      refine ⟨TradeoffFunction.constAtUnitInf T, constAtUnitInf_isConvexLowerBoundOnUnit T, rfl⟩
    refine csSup_le hNonempty ?_
    intro r hr
    rcases hr with ⟨lower, hlower, rfl⟩
    exact hlower.2 hα
  · classical
    simp [convexifiedLowerEnvelope, hα]

/-- Pointwise order lifts through the convexified lower-envelope surface. -/
theorem convexifiedLowerEnvelope_mono
    {T U : TradeoffFunction}
    (hTU : T.PointwiseLE U) :
    (convexifiedLowerEnvelope T).PointwiseLE (convexifiedLowerEnvelope U) := by
  intro α
  by_cases hα : α ∈ unitInterval
  · classical
    have hEvalT :
        (convexifiedLowerEnvelope T).eval α =
          if h : α ∈ unitInterval then sSup (convexLowerValueSet T α) else T.eval α := rfl
    have hEvalU :
        (convexifiedLowerEnvelope U).eval α =
          if h : α ∈ unitInterval then sSup (convexLowerValueSet U α) else U.eval α := rfl
    rw [hEvalT]
    have hIfT :
        (if h : α ∈ unitInterval then sSup (convexLowerValueSet T α) else T.eval α) =
          sSup (convexLowerValueSet T α) := by
      simp [hα]
    rw [hIfT]
    rw [hEvalU]
    have hIfU :
        (if h : α ∈ unitInterval then sSup (convexLowerValueSet U α) else U.eval α) =
          sSup (convexLowerValueSet U α) := by
      simp [hα]
    rw [hIfU]
    have hT_nonempty : (convexLowerValueSet T α).Nonempty := by
      refine ⟨T.unitInf, ?_⟩
      refine ⟨TradeoffFunction.constAtUnitInf T,
        constAtUnitInf_isConvexLowerBoundOnUnit T, rfl⟩
    have hU_nonempty : (convexLowerValueSet U α).Nonempty := by
      refine ⟨U.unitInf, ?_⟩
      refine ⟨TradeoffFunction.constAtUnitInf U,
        constAtUnitInf_isConvexLowerBoundOnUnit U, rfl⟩
    have hU_bddAbove : BddAbove (convexLowerValueSet U α) := by
      refine ⟨U.eval α, ?_⟩
      intro r hr
      rcases hr with ⟨lower, hlower, rfl⟩
      exact hlower.2 hα
    refine csSup_le hT_nonempty ?_
    intro r hr
    rcases hr with ⟨lower, hlower, rfl⟩
    exact le_csSup hU_bddAbove ⟨lower, ⟨hlower.1, fun β hβ => le_trans (hlower.2 hβ) (hTU β)⟩, rfl⟩
  · classical
    simp [convexifiedLowerEnvelope, hα, hTU α]

/--
The first symmetrized lower-envelope layer is monotone in the source tradeoff
function.
-/
theorem rawPSamplingOperator_mono
    {p : ℝ}
    (hp : 0 ≤ p)
    {T U : TradeoffFunction}
    (hTU : T.PointwiseLE U) :
    (rawPSamplingOperator p T).PointwiseLE (rawPSamplingOperator p U) := by
  intro α
  refine min_le_min ?_ ?_
  · exact withIdentityWeight_mono hp hTU α
  · exact leftContinuousInverse_mono (withIdentityWeight_mono hp hTU) α

theorem pSamplingOperator_mono
    {p : ℝ}
    (hp : 0 ≤ p)
    {T U : TradeoffFunction}
    (hTU : T.PointwiseLE U) :
    (pSamplingOperator p T).PointwiseLE (pSamplingOperator p U) := by
  exact convexifiedLowerEnvelope_mono (rawPSamplingOperator_mono hp hTU)

/--
The refined `p`-sampling operator stays below the raw symmetrized lower-envelope
surface.
-/
theorem pSamplingOperator_le_raw
    (p : ℝ)
    (T : TradeoffFunction) :
    (pSamplingOperator p T).PointwiseLE (rawPSamplingOperator p T) := by
  simpa [pSamplingOperator] using
    (convexifiedLowerEnvelope_le (rawPSamplingOperator p T))

/--
The current `p`-sampling operator surface lies below the weighted tradeoff
envelope `f_p`.
-/
theorem pSamplingOperator_le_withIdentityWeight
    (p : ℝ)
    (T : TradeoffFunction) :
    (pSamplingOperator p T).PointwiseLE (withIdentityWeight p T) := by
  exact pointwiseLE_trans (pSamplingOperator_le_raw p T) (fun α => min_le_left _ _)

/--
The current `p`-sampling operator surface also lies below the inverse-side
weighted envelope.
-/
theorem pSamplingOperator_le_inverseWeighted
    (p : ℝ)
    (T : TradeoffFunction) :
    (pSamplingOperator p T).PointwiseLE
      (leftContinuousInverse (withIdentityWeight p T)) := by
  exact pointwiseLE_trans (pSamplingOperator_le_raw p T) (fun α => min_le_right _ _)

/--
At sampling ratio `p = 0`, the current operator surface stays below perfect
privacy.
-/
theorem pSamplingOperator_zero_le_ideal
    (T : TradeoffFunction) :
    (pSamplingOperator 0 T).PointwiseLE ideal := by
  have hbase := pSamplingOperator_le_withIdentityWeight 0 T
  simpa using hbase

/--
At sampling ratio `p = 1`, the current operator surface stays below the
original tradeoff object.
-/
theorem pSamplingOperator_one_le_self
    (T : TradeoffFunction) :
    (pSamplingOperator 1 T).PointwiseLE T := by
  have hbase := pSamplingOperator_le_withIdentityWeight 1 T
  simpa using hbase

end TradeoffFunction

namespace PrivacyObject

/--
Canonical application of the tradeoff-side `p`-sampling operator to a privacy
object at fixed `ε`.
-/
def subsampleTradeoffAt (P : PrivacyObject) (p ε : ℝ) : TradeoffFunction :=
  TradeoffFunction.pSamplingOperator p (P.tradeoffAt ε)

/--
Zero-shift tradeoff comparison transports through the first `p`-sampling
operator surface.
-/
theorem subsampleTradeoffAt_of_leShiftedAdd_zero_zero
    {U L : PrivacyObject}
    (h : U.LeShiftedAdd L 0 0)
    {p : ℝ}
    (hp : 0 ≤ p)
    (ε : ℝ) :
    (U.subsampleTradeoffAt p ε).PointwiseLE (L.subsampleTradeoffAt p ε) := by
  exact TradeoffFunction.pSamplingOperator_mono hp
    (PrivacyObject.tradeoffAt_of_leShiftedAdd_zero_zero h ε)

theorem subsampleTradeoffAt_le_weighted
    (P : PrivacyObject)
    (p ε : ℝ) :
    (P.subsampleTradeoffAt p ε).PointwiseLE
      (TradeoffFunction.withIdentityWeight p (P.tradeoffAt ε)) := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_le_withIdentityWeight p (P.tradeoffAt ε)

theorem subsampleTradeoffAt_le_inverseWeighted
    (P : PrivacyObject)
    (p ε : ℝ) :
    (P.subsampleTradeoffAt p ε).PointwiseLE
      (TradeoffFunction.leftContinuousInverse
        (TradeoffFunction.withIdentityWeight p (P.tradeoffAt ε))) := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_le_inverseWeighted p (P.tradeoffAt ε)

theorem subsampleTradeoffAt_zero_le_ideal
    (P : PrivacyObject)
    (ε : ℝ) :
    (P.subsampleTradeoffAt 0 ε).PointwiseLE TradeoffFunction.ideal := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_zero_le_ideal (P.tradeoffAt ε)

theorem subsampleTradeoffAt_one_le_tradeoffAt
    (P : PrivacyObject)
    (ε : ℝ) :
    (P.subsampleTradeoffAt 1 ε).PointwiseLE (P.tradeoffAt ε) := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_one_le_self (P.tradeoffAt ε)

end PrivacyObject

namespace GaussianDP

/--
Canonical GDP-side application of the first `p`-sampling operator surface.
-/
def subsampleTradeoffAt (G : GaussianDP) (p ε : ℝ) : TradeoffFunction :=
  TradeoffFunction.pSamplingOperator p (G.tradeoffAt ε)

theorem subsampleTradeoffAt_le_weighted
    (G : GaussianDP)
    (p ε : ℝ) :
    (G.subsampleTradeoffAt p ε).PointwiseLE
      (TradeoffFunction.withIdentityWeight p (G.tradeoffAt ε)) := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_le_withIdentityWeight p (G.tradeoffAt ε)

theorem subsampleTradeoffAt_le_inverseWeighted
    (G : GaussianDP)
    (p ε : ℝ) :
    (G.subsampleTradeoffAt p ε).PointwiseLE
      (TradeoffFunction.leftContinuousInverse
        (TradeoffFunction.withIdentityWeight p (G.tradeoffAt ε))) := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_le_inverseWeighted p (G.tradeoffAt ε)

/--
Pointwise closed-form upper bound for the first subsampled GDP tradeoff layer.

This is the first theorem-facing Gaussian consumer of the subsampling operator
surface: later sampled-Gaussian results can rewrite against the explicit GDP
expression without reopening the generic `TradeoffFunction` definitions.
-/
theorem subsampleTradeoffAt_eval_le_weighted
    (G : GaussianDP)
    (p ε α : ℝ) :
    (G.subsampleTradeoffAt p ε).eval α ≤
      p * (1 - gdpProfile G.μ ε - Real.exp ε * α) + (1 - p) * (1 - α) := by
  exact subsampleTradeoffAt_le_weighted G p ε α

/--
Inverse-side pointwise upper bound for the first subsampled GDP tradeoff layer.
-/
theorem subsampleTradeoffAt_eval_le_inverseWeighted
    (G : GaussianDP)
    (p ε α : ℝ) :
    (G.subsampleTradeoffAt p ε).eval α ≤
      (TradeoffFunction.leftContinuousInverse
        (TradeoffFunction.withIdentityWeight p (G.tradeoffAt ε))).eval α := by
  exact subsampleTradeoffAt_le_inverseWeighted G p ε α

theorem subsampleTradeoffAt_zero_le_ideal
    (G : GaussianDP)
    (ε : ℝ) :
    (G.subsampleTradeoffAt 0 ε).PointwiseLE TradeoffFunction.ideal := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_zero_le_ideal (G.tradeoffAt ε)

theorem subsampleTradeoffAt_one_le_tradeoffAt
    (G : GaussianDP)
    (ε : ℝ) :
    (G.subsampleTradeoffAt 1 ε).PointwiseLE (G.tradeoffAt ε) := by
  simpa [subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_one_le_self (G.tradeoffAt ε)

/--
At `p = 0`, the subsampled GDP tradeoff surface stays below the ideal
perfect-privacy tradeoff pointwise.
-/
theorem subsampleTradeoffAt_zero_eval_le_ideal
    (G : GaussianDP)
    (ε α : ℝ) :
    (G.subsampleTradeoffAt 0 ε).eval α ≤ 1 - α := by
  exact subsampleTradeoffAt_zero_le_ideal G ε α

/--
At `p = 1`, the subsampled GDP tradeoff surface stays below the original GDP
tradeoff pointwise.
-/
theorem subsampleTradeoffAt_one_eval_le_tradeoffAt
    (G : GaussianDP)
    (ε α : ℝ) :
    (G.subsampleTradeoffAt 1 ε).eval α ≤
      1 - gdpProfile G.μ ε - Real.exp ε * α := by
  exact subsampleTradeoffAt_one_le_tradeoffAt G ε α

end GaussianDP

end
end DP
end Mf
