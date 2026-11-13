import Mf.DP.ProfileAdaptiveKernelComposition

/-!
# Approximate differential privacy under joint weak limits

This file proves that an ordered event-level approximate-DP inequality is
closed under joint weak convergence of probability laws on a second-countable
metric Borel space. The proof passes through bounded continuous test functions
and then recovers measurable events from measure regularity.

This is a generic law-level closure theorem. Applying it to a limiting
mechanism still requires paired weak convergence for every ordered adjacent
dataset pair.
-/

open Filter MeasureTheory Set Topology

namespace Mf
namespace DP

noncomputable section

/-- The ordered event inequality underlying one direction of approximate DP. -/
def OrderedApproxDPLawPair
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : ProbabilityMeasure Y) (epsilon delta : Real) : Prop :=
  forall s, MeasurableSet s ->
    (mu : Measure Y) s <=
      ENNReal.ofReal (Real.exp epsilon) * (nu : Measure Y) s +
        ENNReal.ofReal delta

/-- Event-level ordered approximate DP controls every measurable `[0, 1]` test. -/
theorem OrderedApproxDPLawPair.lintegral_le
    {Y : Type*} [MeasurableSpace Y]
    {mu nu : ProbabilityMeasure Y} {epsilon delta : Real}
    (h : OrderedApproxDPLawPair mu nu epsilon delta)
    {f : Y -> ENNReal} (hf : Measurable f) (hf_le_one : forall x, f x <= 1) :
    (∫⁻ x, f x ∂(mu : Measure Y)) <=
      ENNReal.ofReal (Real.exp epsilon) * (∫⁻ x, f x ∂(nu : Measure Y)) +
        ENNReal.ofReal delta := by
  exact lintegral_le_of_event_le ENNReal.ofReal_ne_top h hf hf_le_one

/-- The ordered inequality for bounded continuous tests passes to a joint weak limit. -/
theorem orderedApproxDPLawPair_limit_lintegral_le
    {I Y : Type*}
    [PseudoMetricSpace Y] [T2Space Y] [MeasurableSpace Y] [BorelSpace Y]
    [SecondCountableTopology Y]
    {l : Filter I} [NeBot l]
    {mu nu : I -> ProbabilityMeasure Y}
    {muLimit nuLimit : ProbabilityMeasure Y}
    {epsilon delta : Real}
    (hmu : Tendsto mu l (nhds muLimit))
    (hnu : Tendsto nu l (nhds nuLimit))
    (hprivate : ∀ᶠ i in l,
      OrderedApproxDPLawPair (mu i) (nu i) epsilon delta)
    (f : BoundedContinuousFunction Y NNReal)
    (hf_le_one : forall x, f x <= 1) :
    (∫⁻ x, f x ∂(muLimit : Measure Y)) <=
      ENNReal.ofReal (Real.exp epsilon) *
          (∫⁻ x, f x ∂(nuLimit : Measure Y)) +
        ENNReal.ofReal delta := by
  have hmuIntegral :=
    (ProbabilityMeasure.tendsto_iff_forall_lintegral_tendsto.mp hmu) f
  have hnuIntegral :=
    (ProbabilityMeasure.tendsto_iff_forall_lintegral_tendsto.mp hnu) f
  have hmul : Tendsto
      (fun i => ENNReal.ofReal (Real.exp epsilon) *
        (∫⁻ x, f x ∂(nu i : Measure Y))) l
      (nhds (ENNReal.ofReal (Real.exp epsilon) *
        (∫⁻ x, f x ∂(nuLimit : Measure Y)))) :=
    ((ENNReal.continuous_const_mul ENNReal.ofReal_ne_top).tendsto
      (∫⁻ x, f x ∂(nuLimit : Measure Y))).comp hnuIntegral
  apply le_of_tendsto_of_tendsto hmuIntegral
    (hmul.add tendsto_const_nhds)
  filter_upwards [hprivate] with i hi
  apply hi.lintegral_le
  · fun_prop
  · intro x
    simpa using hf_le_one x

/-- Continuous separation transports the test inequality to a closed/open pair. -/
theorem orderedApproxDPLawPair_closed_le_open_of_limit_lintegral
    {Y : Type*}
    [PseudoMetricSpace Y] [T2Space Y] [MeasurableSpace Y] [BorelSpace Y]
    [SecondCountableTopology Y]
    {mu nu : ProbabilityMeasure Y} {epsilon delta : Real}
    (htest : forall (f : BoundedContinuousFunction Y NNReal),
      (forall x, f x <= 1) ->
      (∫⁻ x, f x ∂(mu : Measure Y)) <=
        ENNReal.ofReal (Real.exp epsilon) *
            (∫⁻ x, f x ∂(nu : Measure Y)) +
          ENNReal.ofReal delta)
    {F U : Set Y} (hF : IsClosed F) (hU : IsOpen U) (hFU : F ⊆ U) :
    (mu : Measure Y) F <=
      ENNReal.ofReal (Real.exp epsilon) * (nu : Measure Y) U +
        ENNReal.ofReal delta := by
  obtain ⟨f, hf_zero, hf_one, hf_range⟩ :=
    exists_continuous_zero_one_of_isClosed hU.isClosed_compl hF
      (disjoint_compl_left_iff_subset.mpr hFU)
  have hf_cont : Continuous f := f.continuous
  have hf_nonneg : forall x, 0 <= f x := fun x => (hf_range x).1
  have hf_le : forall x, f x <= 1 := fun x => (hf_range x).2
  let g : C(Y, NNReal) :=
    { toFun := fun x => ⟨f x, hf_nonneg x⟩
      continuous_toFun := Continuous.subtype_mk hf_cont (fun x => hf_nonneg x) }
  let test : BoundedContinuousFunction Y NNReal :=
    BoundedContinuousFunction.mkOfBound g 1 (by
      intro x y
      rw [NNReal.dist_eq]
      change |f x - f y| <= 1
      rw [abs_le]
      constructor <;> linarith [hf_nonneg x, hf_nonneg y,
        hf_le x, hf_le y])
  have hF_le_one : forall x, test x <= 1 := by
    intro x
    exact_mod_cast hf_le x
  have hFmu :
      (∫⁻ x, test x ∂(mu : Measure Y)) =
        ENNReal.ofReal (∫ x, f x ∂(mu : Measure Y)) := by
    rw [ofReal_integral_eq_lintegral_ofReal]
    · apply lintegral_congr
      intro x
      rw [ENNReal.ofReal_eq_coe_nnreal (hf_nonneg x)]
      rfl
    · exact Integrable.of_bound hf_cont.aestronglyMeasurable 1
        (ae_of_all _ fun x => by
          rw [Real.norm_eq_abs, abs_of_nonneg (hf_nonneg x)]
          exact hf_le x)
    · exact ae_of_all _ hf_nonneg
  have hFnu :
      (∫⁻ x, test x ∂(nu : Measure Y)) =
        ENNReal.ofReal (∫ x, f x ∂(nu : Measure Y)) := by
    rw [ofReal_integral_eq_lintegral_ofReal]
    · apply lintegral_congr
      intro x
      rw [ENNReal.ofReal_eq_coe_nnreal (hf_nonneg x)]
      rfl
    · exact Integrable.of_bound hf_cont.aestronglyMeasurable 1
        (ae_of_all _ fun x => by
          rw [Real.norm_eq_abs, abs_of_nonneg (hf_nonneg x)]
          exact hf_le x)
    · exact ae_of_all _ hf_nonneg
  calc
    (mu : Measure Y) F <=
        ENNReal.ofReal (∫ x, f x ∂(mu : Measure Y)) := by
      apply Integrable.measure_le_integral
      · exact Integrable.of_bound hf_cont.aestronglyMeasurable 1
          (ae_of_all _ fun x => by
            rw [Real.norm_eq_abs, abs_of_nonneg (hf_nonneg x)]
            exact hf_le x)
      · exact ae_of_all _ hf_nonneg
      · intro x hx
        simpa using (hf_one hx).ge
    _ = ∫⁻ x, test x ∂(mu : Measure Y) := hFmu.symm
    _ <= ENNReal.ofReal (Real.exp epsilon) *
          (∫⁻ x, test x ∂(nu : Measure Y)) + ENNReal.ofReal delta :=
      htest test hF_le_one
    _ = ENNReal.ofReal (Real.exp epsilon) *
          ENNReal.ofReal (∫ x, f x ∂(nu : Measure Y)) +
            ENNReal.ofReal delta := by rw [hFnu]
    _ <= ENNReal.ofReal (Real.exp epsilon) * (nu : Measure Y) U +
          ENNReal.ofReal delta := by
      gcongr
      exact integral_le_measure
        (fun x _ => hf_le x) (fun x hx => (hf_zero hx).le)

/-- Bounded continuous test control implies the full measurable-event inequality. -/
theorem orderedApproxDPLawPair_of_limit_lintegral
    {Y : Type*}
    [PseudoMetricSpace Y] [T2Space Y] [MeasurableSpace Y] [BorelSpace Y]
    [SecondCountableTopology Y]
    {mu nu : ProbabilityMeasure Y} {epsilon delta : Real}
    (htest : forall (f : BoundedContinuousFunction Y NNReal),
      (forall x, f x <= 1) ->
      (∫⁻ x, f x ∂(mu : Measure Y)) <=
        ENNReal.ofReal (Real.exp epsilon) *
            (∫⁻ x, f x ∂(nu : Measure Y)) +
          ENNReal.ofReal delta) :
    OrderedApproxDPLawPair mu nu epsilon delta := by
  intro A hA
  rw [hA.measure_eq_iSup_isClosed_of_ne_top (by simp : (mu : Measure Y) A ≠ ⊤)]
  simp only [iSup_le_iff]
  intro F hFA hF
  rw [Set.measure_eq_iInf_isOpen A (nu : Measure Y)]
  have hc0 : ENNReal.ofReal (Real.exp epsilon) ≠ 0 := by
    exact ENNReal.ofReal_ne_zero_iff.mpr (Real.exp_pos epsilon)
  have hctop : ENNReal.ofReal (Real.exp epsilon) ≠ ⊤ :=
    ENNReal.ofReal_ne_top
  simp_rw [ENNReal.mul_iInf_of_ne hc0 hctop, ENNReal.iInf_add]
  refine le_iInf fun U => le_iInf fun hAU => le_iInf fun hU => ?_
  exact orderedApproxDPLawPair_closed_le_open_of_limit_lintegral
    htest hF hU (hFA.trans hAU)

/-- Ordered approximate DP is closed under joint weak convergence of both laws. -/
theorem orderedApproxDPLawPair_closed_under_joint_weak_convergence
    {I Y : Type*}
    [PseudoMetricSpace Y] [T2Space Y] [MeasurableSpace Y] [BorelSpace Y]
    [SecondCountableTopology Y]
    {l : Filter I} [NeBot l]
    {mu nu : I -> ProbabilityMeasure Y}
    {muLimit nuLimit : ProbabilityMeasure Y}
    {epsilon delta : Real}
    (_hdelta : 0 <= delta)
    (hmu : Tendsto mu l (nhds muLimit))
    (hnu : Tendsto nu l (nhds nuLimit))
    (hprivate : ∀ᶠ i in l,
      OrderedApproxDPLawPair (mu i) (nu i) epsilon delta) :
    OrderedApproxDPLawPair muLimit nuLimit epsilon delta := by
  apply orderedApproxDPLawPair_of_limit_lintegral
  intro f hf
  exact orderedApproxDPLawPair_limit_lintegral_le
    hmu hnu hprivate f hf

end

end DP
end Mf
