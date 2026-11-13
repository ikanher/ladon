import Mathlib
import Mf.DP.GaussianPrivacyLoss
import Mf.DP.PrivacyLossCore

namespace Mf
namespace DP

open scoped BigOperators

noncomputable section

/--
Event-level approximate-DP contract over output measures.

This is the predicate that matches the analytic Gaussian mechanism statement
from the paper. We keep the existing pointwise-density predicate below for
backward compatibility while migrating downstream theorems.
-/
def ApproxDP
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    (ε δ : ℝ) : Prop :=
  ∀ x x', adj x x' → ∀ s, MeasurableSet s →
    mech x s ≤ ENNReal.ofReal (Real.exp ε) * mech x' s + ENNReal.ofReal δ

/--
Pointwise approximate-DP style contract over output densities.
-/
def PointwiseApproxDP
    {X Y : Type}
    (adj : X → X → Prop)
    (dens : X → Y → ℝ)
    (ε δ : ℝ) : Prop :=
  ∀ x x', adj x x' → ∀ y, dens x y ≤ Real.exp ε * dens x' y + δ

/--
Backward-compatibility alias retained while downstream files migrate from
pointwise-density obligations to `ApproxDP`.
-/
abbrev PointwiseApproxDPCompat
    {X Y : Type}
    (adj : X → X → Prop)
    (dens : X → Y → ℝ)
    (ε δ : ℝ) : Prop :=
  PointwiseApproxDP adj dens ε δ

/--
Monotonic lifting: if a mechanism satisfies pointwise `(ε₀,δ)` and `ε₀ ≤ ε`,
then it also satisfies pointwise `(ε,δ)` (assuming nonnegative densities).
-/
theorem pointwiseApproxDP_mono_epsilon
    {X Y : Type}
    (adj : X → X → Prop)
    (dens : X → Y → ℝ)
    {ε₀ ε δ : ℝ}
    (hDP : PointwiseApproxDP adj dens ε₀ δ)
    (hε : ε₀ ≤ ε)
    (hdens_nonneg : ∀ x y, 0 ≤ dens x y) :
    PointwiseApproxDP adj dens ε δ := by
  intro x x' hAdj y
  have hbase := hDP x x' hAdj y
  have hexp : Real.exp ε₀ ≤ Real.exp ε := by
    exact Real.exp_le_exp.mpr hε
  have hmul : Real.exp ε₀ * dens x' y ≤ Real.exp ε * dens x' y := by
    exact mul_le_mul_of_nonneg_right hexp (hdens_nonneg x' y)
  have hadd : Real.exp ε₀ * dens x' y + δ ≤ Real.exp ε * dens x' y + δ := by
    simpa [add_comm, add_left_comm, add_assoc] using add_le_add_left hmul δ
  exact le_trans hbase hadd

/--
Monotonic lifting for event-level approximate-DP.
-/
theorem approxDP_mono_epsilon
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    {ε₀ ε δ : ℝ}
    (hDP : ApproxDP adj mech ε₀ δ)
    (hε : ε₀ ≤ ε) :
    ApproxDP adj mech ε δ := by
  intro x x' hAdj s hs
  have hbase := hDP x x' hAdj s hs
  have hexp : Real.exp ε₀ ≤ Real.exp ε := by
    exact Real.exp_le_exp.mpr hε
  have hmul :
      ENNReal.ofReal (Real.exp ε₀) * mech x' s
        ≤ ENNReal.ofReal (Real.exp ε) * mech x' s := by
    exact mul_le_mul_of_nonneg_right
      (ENNReal.ofReal_le_ofReal hexp)
      (by simp)
  have hadd :
      ENNReal.ofReal (Real.exp ε₀) * mech x' s + ENNReal.ofReal δ
        ≤ ENNReal.ofReal (Real.exp ε) * mech x' s + ENNReal.ofReal δ := by
    exact add_le_add hmul le_rfl
  exact le_trans hbase hadd

/--
Monotonic lifting for event-level approximate-DP along the additive failure
budget.
-/
theorem approxDP_mono_delta
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    {ε δ₀ δ : ℝ}
    (hDP : ApproxDP adj mech ε δ₀)
    (hδ : δ₀ ≤ δ) :
    ApproxDP adj mech ε δ := by
  intro x x' hAdj s hs
  have hbase := hDP x x' hAdj s hs
  have hdelta :
      ENNReal.ofReal δ₀ ≤ ENNReal.ofReal δ :=
    ENNReal.ofReal_le_ofReal hδ
  exact le_trans hbase (add_le_add_right hdelta _)

/--
Monotonic lifting for event-level approximate-DP along adjacency inclusion.

If a mechanism is private for a larger adjacency relation `adj₀`, then it is
private for any subrelation `adj`.
-/
theorem approxDP_mono_adj
    {X Y : Type}
    [MeasurableSpace Y]
    {adj adj₀ : X → X → Prop}
    (mech : X → MeasureTheory.Measure Y)
    {ε δ : ℝ}
    (hsub : ∀ x x', adj x x' → adj₀ x x')
    (hDP : ApproxDP adj₀ mech ε δ) :
    ApproxDP adj mech ε δ := by
  intro x x' hAdj s hs
  exact hDP x x' (hsub x x' hAdj) s hs

theorem approxDP_of_one_le_delta
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (mech : X → MeasureTheory.Measure Y)
    (hprob : ∀ x, MeasureTheory.IsProbabilityMeasure (mech x))
    {ε δ : ℝ}
    (hδ : 1 ≤ δ) :
    ApproxDP adj mech ε δ := by
  intro x x' _ s hs
  have h_univ : mech x Set.univ = 1 := (hprob x).measure_univ
  have hxs_le_one : mech x s ≤ 1 := by
    calc
      mech x s ≤ mech x Set.univ := MeasureTheory.measure_mono (Set.subset_univ s)
      _ = 1 := h_univ
  have hone_le_delta : (1 : ENNReal) ≤ ENNReal.ofReal δ := by
    simpa using (ENNReal.ofReal_le_ofReal hδ)
  have hdelta_le_rhs :
      ENNReal.ofReal δ
        ≤ ENNReal.ofReal (Real.exp ε) * mech x' s + ENNReal.ofReal δ := by
    exact le_add_of_nonneg_left (by simp)
  exact le_trans (le_trans hxs_le_one hone_le_delta) hdelta_le_rhs

theorem approxDP_of_withDensity_privacyLossSet_bound
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (μ : MeasureTheory.Measure Y)
    (dens : X → Y → ℝ)
    {ε δ : ℝ}
    (hδ : 0 ≤ δ)
    (hmeas : ∀ x, Measurable (dens x))
    (hint : ∀ x, MeasureTheory.Integrable (dens x) μ)
    (hnonneg : ∀ x y, 0 ≤ dens x y)
    (hPL :
      ∀ x x', adj x x' →
        (∫ y in posRegion (fun y => dens x y - Real.exp ε * dens x' y),
            (dens x y - Real.exp ε * dens x' y) ∂μ) ≤ δ) :
    ApproxDP
      adj
      (fun x => μ.withDensity (fun y => ENNReal.ofReal (dens x y)))
      ε
      δ := by
  intro x x' hAdj s hs
  have hdpReal :=
    dp_event_bound_of_privacyLossSet
      (p := dens x) (q := dens x') ε δ
      (hp_meas := hmeas x) (hq_meas := hmeas x')
      (hp_int := hint x) (hq_int := hint x')
      (hpos := hPL x x' hAdj)
      s hs
  have hx_int_s : MeasureTheory.Integrable (dens x) (μ.restrict s) := (hint x).restrict
  have hx'_int_s : MeasureTheory.Integrable (dens x') (μ.restrict s) := (hint x').restrict
  have hx_nonneg_s : 0 ≤ᵐ[μ.restrict s] dens x := by
    exact Filter.Eventually.of_forall (fun y => hnonneg x y)
  have hx'_nonneg_s : 0 ≤ᵐ[μ.restrict s] dens x' := by
    exact Filter.Eventually.of_forall (fun y => hnonneg x' y)
  have hx_apply :
      (μ.withDensity (fun y => ENNReal.ofReal (dens x y))) s
        = ENNReal.ofReal (∫ y in s, dens x y ∂μ) := by
    rw [MeasureTheory.withDensity_apply _ hs]
    simpa using
      (MeasureTheory.ofReal_integral_eq_lintegral_ofReal hx_int_s hx_nonneg_s).symm
  have hx'_apply :
      (μ.withDensity (fun y => ENNReal.ofReal (dens x' y))) s
        = ENNReal.ofReal (∫ y in s, dens x' y ∂μ) := by
    rw [MeasureTheory.withDensity_apply _ hs]
    simpa using
      (MeasureTheory.ofReal_integral_eq_lintegral_ofReal hx'_int_s hx'_nonneg_s).symm
  have hIq_nonneg : 0 ≤ ∫ y in s, dens x' y ∂μ := by
    exact MeasureTheory.setIntegral_nonneg hs (fun y _ => hnonneg x' y)
  have hrhs :
      ENNReal.ofReal (Real.exp ε * (∫ y in s, dens x' y ∂μ) + δ)
        = ENNReal.ofReal (Real.exp ε)
            * (μ.withDensity (fun y => ENNReal.ofReal (dens x' y))) s
            + ENNReal.ofReal δ := by
    rw [hx'_apply]
    rw [ENNReal.ofReal_add (mul_nonneg (le_of_lt (Real.exp_pos ε)) hIq_nonneg) hδ]
    rw [ENNReal.ofReal_mul (le_of_lt (Real.exp_pos ε))]
  have hdpENN :
      ENNReal.ofReal (∫ y in s, dens x y ∂μ)
        ≤ ENNReal.ofReal (Real.exp ε * (∫ y in s, dens x' y ∂μ) + δ) := by
    exact ENNReal.ofReal_le_ofReal hdpReal
  calc
    (μ.withDensity (fun y => ENNReal.ofReal (dens x y))) s
      = ENNReal.ofReal (∫ y in s, dens x y ∂μ) := hx_apply
    _ ≤ ENNReal.ofReal (Real.exp ε * (∫ y in s, dens x' y ∂μ) + δ) := hdpENN
    _ = ENNReal.ofReal (Real.exp ε)
          * (μ.withDensity (fun y => ENNReal.ofReal (dens x' y))) s
          + ENNReal.ofReal δ := hrhs

/--
Reusable package for event-level `ApproxDP` over a with-density measure family.

This records the exact stronger hypotheses needed by the generic event proof.
In particular, a bare pointwise density inequality is not enough on its own:
the route goes through a privacy-loss-set integral bound.
-/
structure WithDensityPrivacyLossBoundPackage
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (μ : MeasureTheory.Measure Y)
    (dens : X → Y → ℝ)
    (ε δ : ℝ) where
  delta_nonneg : 0 ≤ δ
  measurable : ∀ x, Measurable (dens x)
  integrable : ∀ x, MeasureTheory.Integrable (dens x) μ
  nonneg : ∀ x y, 0 ≤ dens x y
  privacyLossSet_bound :
    ∀ x x', adj x x' →
      (∫ y in posRegion (fun y => dens x y - Real.exp ε * dens x' y),
          (dens x y - Real.exp ε * dens x' y) ∂μ) ≤ δ

/--
Package-form event-level bridge for with-density measure families.

This is the generic theorem that downstream `BNB`-style density families should
consume when they can supply the stronger privacy-loss-set integral bound.
-/
theorem approxDP_of_withDensity_privacyLossBoundPackage
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (μ : MeasureTheory.Measure Y)
    (dens : X → Y → ℝ)
    {ε δ : ℝ}
    (pkg :
      WithDensityPrivacyLossBoundPackage
        (X := X) (Y := Y) adj μ dens ε δ) :
    ApproxDP
      adj
      (fun x => μ.withDensity (fun y => ENNReal.ofReal (dens x y)))
      ε
      δ := by
  exact approxDP_of_withDensity_privacyLossSet_bound
    adj μ dens
    pkg.delta_nonneg
    pkg.measurable
    pkg.integrable
    pkg.nonneg
    pkg.privacyLossSet_bound

/--
Build the with-density privacy-loss package from a pure pointwise density
comparison.

This theorem is intentionally restricted to the pure pointwise case
`dens x y <= exp ε * dens x' y`.  The additive pointwise predicate
`dens x y <= exp ε * dens x' y + δ` is not enough to integrate over arbitrary
events without additional finite-measure control.  In the pure case, the
privacy-loss-set gap is pointwise zero on its positive region, so every
privacy-loss-set integral is bounded by any nonnegative target `δ`.
-/
theorem withDensityPrivacyLossBoundPackage_of_purePointwise
    {X Y : Type}
    [MeasurableSpace Y]
    (adj : X → X → Prop)
    (μ : MeasureTheory.Measure Y)
    (dens : X → Y → ℝ)
    {ε δ : ℝ}
    (hδ : 0 ≤ δ)
    (hmeas : ∀ x, Measurable (dens x))
    (hint : ∀ x, MeasureTheory.Integrable (dens x) μ)
    (hnonneg : ∀ x y, 0 ≤ dens x y)
    (hpure :
      ∀ x x', adj x x' →
        ∀ y, dens x y ≤ Real.exp ε * dens x' y) :
    WithDensityPrivacyLossBoundPackage adj μ dens ε δ where
  delta_nonneg := hδ
  measurable := hmeas
  integrable := hint
  nonneg := hnonneg
  privacyLossSet_bound := by
    intro x x' hAdj
    let gap : Y → ℝ := fun y => dens x y - Real.exp ε * dens x' y
    let s : Set Y := posRegion gap
    have hs : MeasurableSet s := by
      change MeasurableSet {y | 0 ≤ dens x y - Real.exp ε * dens x' y}
      exact measurableSet_le measurable_const
        ((hmeas x).sub ((hmeas x').const_mul (Real.exp ε)))
    have hgap_zero_on_s :
        ∀ y, y ∈ s → gap y = 0 := by
      intro y hy
      have hle : gap y ≤ 0 := by
        exact sub_nonpos.mpr (hpure x x' hAdj y)
      have hge : 0 ≤ gap y := hy
      exact le_antisymm hle hge
    have hindicator :
        Set.indicator s gap = fun _ : Y => 0 := by
      funext y
      by_cases hy : y ∈ s
      · simp [hy, hgap_zero_on_s y hy]
      · simp [hy]
    calc
      (∫ y in s, gap y ∂μ)
          = ∫ y, Set.indicator s gap y ∂μ := by
              rw [MeasureTheory.integral_indicator hs]
      _ = ∫ _y : Y, (0 : ℝ) ∂μ := by rw [hindicator]
      _ = 0 := by simp
      _ ≤ δ := hδ

end

end DP
end Mf
