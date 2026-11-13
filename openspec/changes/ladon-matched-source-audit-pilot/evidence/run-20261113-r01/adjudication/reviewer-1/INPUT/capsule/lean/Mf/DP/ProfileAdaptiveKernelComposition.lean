import Mf.DP.GaussianApproxDP
import Mathlib.MeasureTheory.Integral.Layercake
import Mathlib.Probability.Kernel.Basic

namespace Mf
namespace DP

open MeasureTheory ProbabilityTheory

noncomputable section

/-!
# Adaptive finite-horizon kernel composition

This module constructs transcript laws for release kernels whose next row may
depend measurably on all prior releases.  It is the measure-level foundation
needed by finite-horizon private optimizers.  In particular, these laws are
`Measure.bind` chains, not products of fixed one-step mechanisms.

The first block below is mechanism semantics only.  Privacy composition is
proved against these exact laws later in this module.
-/

/-- A fixed ambient history stores the releases written before the current
step.  Coordinates at or after the current step are ignored.  Using one ambient
type avoids dependent measurable-space transports between successive finite
prefixes. -/
abbrev AdaptiveReleaseHistory (Release : Type*) := ℕ → Release

/-- Replace coordinate `step` of a release history. -/
def writeRelease {Release : Type*} (step : ℕ)
    (p : AdaptiveReleaseHistory Release × Release) :
    AdaptiveReleaseHistory Release :=
  fun i => if i = step then p.2 else p.1 i

theorem measurable_writeRelease
    {Release : Type*} [MeasurableSpace Release] (step : ℕ) :
    Measurable (writeRelease (Release := Release) step) := by
  apply measurable_pi_lambda
  intro i
  by_cases h : i = step
  · simpa [writeRelease, h] using
      (measurable_snd : Measurable
        (fun p : AdaptiveReleaseHistory Release × Release => p.2))
  · have hfst : Measurable
        (fun p : AdaptiveReleaseHistory Release × Release => p.1) :=
      measurable_fst
    simpa [writeRelease, h, Function.comp_def] using
      (measurable_pi_apply i).comp hfst

/-- A dataset-indexed family of Markov release kernels.  At step `n`, the row
may inspect the complete ambient history; downstream instantiations prove that
only the prefix before `n` is used. -/
structure AdaptiveReleaseKernelFamily
    (Dataset Release : Type*) [MeasurableSpace Release] where
  stepKernel : ℕ → Dataset →
    Kernel (AdaptiveReleaseHistory Release) Release
  stepKernel_isMarkov :
    ∀ n dataset, IsMarkovKernel (stepKernel n dataset)

namespace AdaptiveReleaseKernelFamily

variable {Dataset Release : Type*} [MeasurableSpace Release]

/-- One transition of the ambient history: sample the next private release and
write it at the current coordinate. -/
def historyAdvanceKernel
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (n : ℕ) (dataset : Dataset) :
    Kernel (AdaptiveReleaseHistory Release)
      (AdaptiveReleaseHistory Release) :=
  ((Kernel.id.prod (family.stepKernel n dataset)).map
    (writeRelease (Release := Release) n))

instance historyAdvanceKernel_isMarkov
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (n : ℕ) (dataset : Dataset) :
    IsMarkovKernel (family.historyAdvanceKernel n dataset) := by
  unfold historyAdvanceKernel
  letI : IsMarkovKernel
      (family.stepKernel n dataset) := family.stepKernel_isMarkov n dataset
  letI : IsMarkovKernel
      (Kernel.id : Kernel (AdaptiveReleaseHistory Release)
        (AdaptiveReleaseHistory Release)) := inferInstance
  letI : IsMarkovKernel
      (Kernel.id.prod (family.stepKernel n dataset)) := inferInstance
  exact Kernel.IsMarkovKernel.map _ (measurable_writeRelease n)

/-- At a fixed history, advancing the transcript is exactly measurable
postprocessing of the next release by writing it at the public step index. -/
theorem historyAdvanceKernel_apply_eq_map
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (n : ℕ) (dataset : Dataset)
    (history : AdaptiveReleaseHistory Release) :
    family.historyAdvanceKernel n dataset history =
      (family.stepKernel n dataset history).map
        (fun release => writeRelease n (history, release)) := by
  letI : IsMarkovKernel (family.stepKernel n dataset) :=
    family.stepKernel_isMarkov n dataset
  have hwrite : Measurable fun release => writeRelease n (history, release) :=
    (measurable_writeRelease n).comp
      (measurable_const.prodMk measurable_id)
  apply Measure.ext
  intro s hs
  rw [historyAdvanceKernel, Kernel.map_apply _ (measurable_writeRelease n),
    Measure.map_apply (measurable_writeRelease n) hs,
    Kernel.id_prod_apply' _ _ ((measurable_writeRelease n) hs),
    Measure.map_apply hwrite hs]
  rfl

/-- The exact finite-step transcript-state law. -/
def transcriptMeasure
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release) :
    ℕ → Dataset → Measure (AdaptiveReleaseHistory Release)
  | 0, _ => Measure.dirac initialHistory
  | n + 1, dataset =>
      (family.transcriptMeasure initialHistory n dataset).bind
        (family.historyAdvanceKernel n dataset)

@[simp] theorem transcriptMeasure_zero
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (dataset : Dataset) :
    family.transcriptMeasure initialHistory 0 dataset =
      Measure.dirac initialHistory := rfl

@[simp] theorem transcriptMeasure_succ
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (n : ℕ) (dataset : Dataset) :
    family.transcriptMeasure initialHistory (n + 1) dataset =
      (family.transcriptMeasure initialHistory n dataset).bind
        (family.historyAdvanceKernel n dataset) := rfl

theorem transcriptMeasure_isProbability
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (n : ℕ) (dataset : Dataset) :
    IsProbabilityMeasure (family.transcriptMeasure initialHistory n dataset) := by
  induction n with
  | zero =>
      dsimp [transcriptMeasure]
      infer_instance
  | succ n ih =>
      rw [transcriptMeasure_succ]
      letI : IsProbabilityMeasure
          (family.transcriptMeasure initialHistory n dataset) := ih
      infer_instance

/-- The zero-step transcript law is independent of the dataset. -/
theorem transcriptMeasure_zero_dataset_independent
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (left right : Dataset) :
    family.transcriptMeasure initialHistory 0 left =
      family.transcriptMeasure initialHistory 0 right := rfl

/-- The next-state law really is a bind against a history-dependent kernel.
This is the rewrite used by adaptive composition; it intentionally does not
state a product-measure equality. -/
theorem transcriptMeasure_succ_eq_bind
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (n : ℕ) (dataset : Dataset) :
    family.transcriptMeasure initialHistory (n + 1) dataset =
      (family.transcriptMeasure initialHistory n dataset).bind
        (family.historyAdvanceKernel n dataset) := rfl

end AdaptiveReleaseKernelFamily

/-! ## Event bounds integrated against continuation probabilities -/

/-- Event-level domination extends to measurable continuation probabilities.

The additive constant is charged once, not once per value of a simple-function
approximation.  The proof uses the layer-cake representation and the fact that
the integrand is bounded by one. -/
theorem lintegral_le_of_event_le
    {A : Type*} [MeasurableSpace A]
    {μ ν : Measure A} {a d : ENNReal}
    (ha : a ≠ ⊤)
    (hEvent : ∀ s, MeasurableSet s → μ s ≤ a * ν s + d)
    {f : A → ENNReal} (hf : Measurable f)
    (hf_le_one : ∀ x, f x ≤ 1) :
    (∫⁻ x, f x ∂μ) ≤ a * (∫⁻ x, f x ∂ν) + d := by
  let g : A → ℝ := fun x => (f x).toReal
  have hg : Measurable g := hf.ennreal_toReal
  have hfinite : ∀ x, f x ≠ ⊤ := by
    intro x htop
    have h := hf_le_one x
    simp [htop] at h
  have hfg : ∀ x, ENNReal.ofReal (g x) = f x := by
    intro x
    exact ENNReal.ofReal_toReal (hfinite x)
  have hg_nonneg : ∀ x, 0 ≤ g x := fun x => ENNReal.toReal_nonneg
  have hg_le_one : ∀ x, g x ≤ 1 := by
    intro x
    rw [← ENNReal.toReal_one]
    exact (ENNReal.toReal_le_toReal (hfinite x) (by simp)).2 (hf_le_one x)
  have hset (t : ℝ) : MeasurableSet {x : A | t < g x} :=
    measurableSet_lt measurable_const hg
  have hlayer_mu :
      (∫⁻ x, f x ∂μ) =
        ∫⁻ t in Set.Ioi (0 : ℝ), μ {x : A | t < g x} := by
    calc
      (∫⁻ x, f x ∂μ) = ∫⁻ x, ENNReal.ofReal (g x) ∂μ := by
        apply lintegral_congr
        intro x
        exact (hfg x).symm
      _ = ∫⁻ t in Set.Ioi (0 : ℝ), μ {x : A | t < g x} :=
        lintegral_eq_lintegral_meas_lt μ
          (Filter.Eventually.of_forall hg_nonneg) hg.aemeasurable
  have hlayer_nu :
      (∫⁻ x, f x ∂ν) =
        ∫⁻ t in Set.Ioi (0 : ℝ), ν {x : A | t < g x} := by
    calc
      (∫⁻ x, f x ∂ν) = ∫⁻ x, ENNReal.ofReal (g x) ∂ν := by
        apply lintegral_congr
        intro x
        exact (hfg x).symm
      _ = ∫⁻ t in Set.Ioi (0 : ℝ), ν {x : A | t < g x} :=
        lintegral_eq_lintegral_meas_lt ν
          (Filter.Eventually.of_forall hg_nonneg) hg.aemeasurable
  rw [hlayer_mu, hlayer_nu]
  let slack : ℝ → ENNReal :=
    Set.Iic (1 : ℝ) |>.indicator (fun _ => d)
  have hslack_meas : Measurable slack :=
    measurable_const.indicator measurableSet_Iic
  calc
    (∫⁻ t in Set.Ioi (0 : ℝ), μ {x : A | t < g x})
        ≤ ∫⁻ t in Set.Ioi (0 : ℝ),
            (a * ν {x : A | t < g x} + slack t) := by
          apply lintegral_mono_ae
          filter_upwards [ae_restrict_mem measurableSet_Ioi] with t ht
          by_cases ht1 : t ≤ 1
          · have hmem : t ∈ Set.Iic (1 : ℝ) := ht1
            simpa [slack, hmem] using
              hEvent {x : A | t < g x} (hset t)
          · have hempty : {x : A | t < g x} = ∅ := by
              ext x
              simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
              exact not_lt_of_ge (le_trans (hg_le_one x) (le_of_not_ge ht1))
            have hnotmem : t ∉ Set.Iic (1 : ℝ) := ht1
            simp [hempty, slack, hnotmem]
    _ = (∫⁻ t in Set.Ioi (0 : ℝ), a * ν {x : A | t < g x}) +
          ∫⁻ t in Set.Ioi (0 : ℝ), slack t := by
          rw [lintegral_add_right]
          exact hslack_meas
    _ ≤ a * (∫⁻ t in Set.Ioi (0 : ℝ), ν {x : A | t < g x}) + d := by
          apply add_le_add
          · exact le_of_eq (lintegral_const_mul' a _ ha)
          · rw [show ∫⁻ t in Set.Ioi (0 : ℝ), slack t =
                d * volume (Set.Iic (1 : ℝ) ∩ Set.Ioi (0 : ℝ)) by
                  simp [slack, lintegral_indicator,
                    Measure.restrict_apply]]
            have hseteq :
                Set.Iic (1 : ℝ) ∩ Set.Ioi (0 : ℝ) = Set.Ioc 0 1 := by
              ext t
              simp [and_comm]
            rw [hseteq, Real.volume_Ioc]
            simp

/-- `ApproxDP` in event form controls every measurable continuation
probability. -/
theorem ApproxDP.lintegral_le
    {Dataset A : Type} [MeasurableSpace A]
    {adj : Dataset → Dataset → Prop} {mech : Dataset → Measure A}
    {ε δ : ℝ} (hDP : ApproxDP adj mech ε δ)
    {left right : Dataset} (hAdj : adj left right)
    {f : A → ENNReal} (hf : Measurable f)
    (hf_le_one : ∀ x, f x ≤ 1) :
    (∫⁻ x, f x ∂mech left) ≤
      ENNReal.ofReal (Real.exp ε) * (∫⁻ x, f x ∂mech right) +
        ENNReal.ofReal δ := by
  exact lintegral_le_of_event_le
    ENNReal.ofReal_ne_top
    (fun s hs => hDP left right hAdj s hs) hf hf_le_one

/-- A dataset-independent mechanism is pure DP for every adjacency relation. -/
theorem approxDP_of_dataset_independent
    {Dataset A : Type} [MeasurableSpace A]
    (adj : Dataset → Dataset → Prop) (mech : Dataset → Measure A)
    (hsame : ∀ left right, mech left = mech right) :
    ApproxDP adj mech 0 0 := by
  intro left right _ s _
  rw [hsame left right]
  simp

/-- Two-step adaptive composition derived directly from the event-level
`ApproxDP` predicate.

The event-only calculation charges the second-step slack after multiplication
by the first likelihood factor.  The sharper standard `delta₁ + delta₂`
composition requires the privacy-loss/profile argument developed in the next
layer; this theorem is the honest basic fallback and a key sanity check for the
history-dependent mechanism semantics. -/
theorem approxDP_bind_adaptive_weighted
    {Dataset A B : Type} [MeasurableSpace A] [MeasurableSpace B]
    {adj : Dataset → Dataset → Prop}
    (baseMech : Dataset → Measure A)
    (next : Dataset → Kernel A B)
    (hbaseProb : ∀ dataset, IsProbabilityMeasure (baseMech dataset))
    (hnextMarkov : ∀ dataset, IsMarkovKernel (next dataset))
    {ε₁ δ₁ ε₂ δ₂ : ℝ}
    (hδ₁ : 0 ≤ δ₁) (hδ₂ : 0 ≤ δ₂)
    (hPrefix : ApproxDP adj baseMech ε₁ δ₁)
    (hNext : ∀ history,
      ApproxDP adj (fun dataset => next dataset history) ε₂ δ₂) :
    ApproxDP adj
      (fun dataset => (baseMech dataset).bind (next dataset))
      (ε₁ + ε₂) (δ₁ + Real.exp ε₁ * δ₂) := by
  intro left right hAdj s hs
  letI : IsMarkovKernel (next left) := hnextMarkov left
  letI : IsMarkovKernel (next right) := hnextMarkov right
  letI : IsProbabilityMeasure (baseMech right) := hbaseProb right
  rw [Measure.bind_apply hs (next left).aemeasurable,
    Measure.bind_apply hs (next right).aemeasurable]
  have hleft_meas : Measurable fun history => next left history s :=
    (next left).measurable_coe hs
  have hright_meas : Measurable fun history => next right history s :=
    (next right).measurable_coe hs
  have hleft_le_one : ∀ history, next left history s ≤ 1 := by
    intro history
    calc
      next left history s ≤ next left history Set.univ :=
        measure_mono (Set.subset_univ s)
      _ = 1 := measure_univ
  have houter := hPrefix.lintegral_le hAdj hleft_meas hleft_le_one
  have hinner :
      (∫⁻ history, next left history s ∂baseMech right) ≤
        ENNReal.ofReal (Real.exp ε₂) *
            (∫⁻ history, next right history s ∂baseMech right) +
          ENNReal.ofReal δ₂ := by
    calc
      (∫⁻ history, next left history s ∂baseMech right)
          ≤ ∫⁻ history,
              (ENNReal.ofReal (Real.exp ε₂) * next right history s +
                ENNReal.ofReal δ₂) ∂baseMech right := by
            apply lintegral_mono
            intro history
            exact hNext history left right hAdj s hs
      _ = ENNReal.ofReal (Real.exp ε₂) *
              (∫⁻ history, next right history s ∂baseMech right) +
            ENNReal.ofReal δ₂ := by
            rw [lintegral_add_right _ measurable_const,
              lintegral_const_mul _ hright_meas,
              lintegral_const]
            simp
  calc
    (∫⁻ history, next left history s ∂baseMech left)
        ≤ ENNReal.ofReal (Real.exp ε₁) *
            (∫⁻ history, next left history s ∂baseMech right) +
          ENNReal.ofReal δ₁ := houter
    _ ≤ ENNReal.ofReal (Real.exp ε₁) *
          (ENNReal.ofReal (Real.exp ε₂) *
              (∫⁻ history, next right history s ∂baseMech right) +
          ENNReal.ofReal δ₂) + ENNReal.ofReal δ₁ := by
          exact add_le_add
            (by
              simpa [mul_comm] using
                (mul_le_mul_left hinner (ENNReal.ofReal (Real.exp ε₁)))) le_rfl
    _ = ENNReal.ofReal (Real.exp (ε₁ + ε₂)) *
          (∫⁻ history, next right history s ∂baseMech right) +
        ENNReal.ofReal (δ₁ + Real.exp ε₁ * δ₂) := by
          rw [Real.exp_add,
            ENNReal.ofReal_mul (Real.exp_pos ε₁).le,
            ENNReal.ofReal_add hδ₁
              (mul_nonneg (Real.exp_pos ε₁).le hδ₂),
            ENNReal.ofReal_mul (Real.exp_pos ε₁).le]
          rw [mul_add]
          ac_rfl

/-- Cumulative epsilon for the first `n` adaptive releases. -/
def adaptiveEpsilonBudget (ε : ℕ → ℝ) : ℕ → ℝ
  | 0 => 0
  | n + 1 => adaptiveEpsilonBudget ε n + ε n

/-- The event-only fallback delta recurrence.  The sharper unweighted sum is
proved through privacy-loss/profile composition rather than asserted here. -/
def adaptiveWeightedDeltaBudget (ε δ : ℕ → ℝ) : ℕ → ℝ
  | 0 => 0
  | n + 1 =>
      adaptiveWeightedDeltaBudget ε δ n +
        Real.exp (adaptiveEpsilonBudget ε n) * δ n

@[simp] theorem adaptiveEpsilonBudget_zero (ε : ℕ → ℝ) :
    adaptiveEpsilonBudget ε 0 = 0 := rfl

@[simp] theorem adaptiveEpsilonBudget_succ (ε : ℕ → ℝ) (n : ℕ) :
    adaptiveEpsilonBudget ε (n + 1) =
      adaptiveEpsilonBudget ε n + ε n := rfl

@[simp] theorem adaptiveWeightedDeltaBudget_zero
    (ε δ : ℕ → ℝ) :
    adaptiveWeightedDeltaBudget ε δ 0 = 0 := rfl

@[simp] theorem adaptiveWeightedDeltaBudget_succ
    (ε δ : ℕ → ℝ) (n : ℕ) :
    adaptiveWeightedDeltaBudget ε δ (n + 1) =
      adaptiveWeightedDeltaBudget ε δ n +
        Real.exp (adaptiveEpsilonBudget ε n) * δ n := rfl

theorem adaptiveWeightedDeltaBudget_nonneg
    (ε δ : ℕ → ℝ) (hδ : ∀ n, 0 ≤ δ n) :
    ∀ n, 0 ≤ adaptiveWeightedDeltaBudget ε δ n := by
  intro n
  induction n with
  | zero => simp
  | succ n ih =>
      simp only [adaptiveWeightedDeltaBudget_succ]
      exact add_nonneg ih (mul_nonneg (Real.exp_pos _).le (hδ n))

@[simp] theorem adaptiveWeightedDeltaBudget_zero_schedule
    (ε : ℕ → ℝ) :
    ∀ n, adaptiveWeightedDeltaBudget ε (fun _ => 0) n = 0 := by
  intro n
  induction n with
  | zero => rfl
  | succ n ih => simp [adaptiveWeightedDeltaBudget_succ, ih]

namespace AdaptiveReleaseKernelFamily

variable {Dataset Release : Type} [MeasurableSpace Release]

/-- Finite-horizon adaptive composition available from the event-level
`ApproxDP` API alone.  It is useful as an independently checked fallback and as
the zero-delta composition theorem.  Profile composition later improves the
delta budget to the standard unweighted sum. -/
theorem transcriptApproxDP_weighted
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (adj : Dataset → Dataset → Prop)
    (ε δ : ℕ → ℝ)
    (hδ : ∀ n, 0 ≤ δ n)
    (hStep : ∀ n history,
      ApproxDP adj
        (fun dataset => family.historyAdvanceKernel n dataset history)
        (ε n) (δ n)) :
    ∀ n, ApproxDP adj
      (family.transcriptMeasure initialHistory n)
      (adaptiveEpsilonBudget ε n) (adaptiveWeightedDeltaBudget ε δ n) := by
  intro n
  induction n with
  | zero =>
      intro left right _ s _
      simp [transcriptMeasure]
  | succ n ih =>
      rw [adaptiveEpsilonBudget_succ, adaptiveWeightedDeltaBudget_succ]
      exact approxDP_bind_adaptive_weighted
        (baseMech := family.transcriptMeasure initialHistory n)
        (next := fun dataset => family.historyAdvanceKernel n dataset)
        (hbaseProb := fun dataset =>
          family.transcriptMeasure_isProbability initialHistory n dataset)
        (hnextMarkov := fun dataset => inferInstance)
        (hδ₁ := adaptiveWeightedDeltaBudget_nonneg ε δ hδ n)
        (hδ₂ := hδ n)
        ih (hStep n)

/-- Pure conditional DP composes with the ordinary sum of epsilons and zero
delta, even for history-dependent release kernels. -/
theorem transcriptApproxDP_pure
    (family : AdaptiveReleaseKernelFamily Dataset Release)
    (initialHistory : AdaptiveReleaseHistory Release)
    (adj : Dataset → Dataset → Prop)
    (ε : ℕ → ℝ)
    (hStep : ∀ n history,
      ApproxDP adj
        (fun dataset => family.historyAdvanceKernel n dataset history)
        (ε n) 0) :
    ∀ n, ApproxDP adj
      (family.transcriptMeasure initialHistory n)
      (adaptiveEpsilonBudget ε n) 0 := by
  intro n
  simpa using
    family.transcriptApproxDP_weighted initialHistory adj ε (fun _ => 0)
      (fun _ => le_rfl) hStep n

end AdaptiveReleaseKernelFamily

/-! ## A genuinely history-dependent regression example -/

section HistoryDependentExample

/-- The public initial ambient transcript used by the regression example. -/
def falseHistory : AdaptiveReleaseHistory Bool := fun _ => false

/-- The first release is `true`; every later release repeats the first private
release.  Thus the second row genuinely depends on history even though it is
independent of the dataset. -/
def branchingReleaseKernel (n : ℕ) :
    Kernel (AdaptiveReleaseHistory Bool) Bool :=
  if n = 0 then
    Kernel.deterministic (fun _ => true) measurable_const
  else
    Kernel.deterministic (fun history => history 0) (measurable_pi_apply 0)

instance branchingReleaseKernel_isMarkov (n : ℕ) :
    IsMarkovKernel (branchingReleaseKernel n) := by
  unfold branchingReleaseKernel
  split <;> infer_instance

def branchingAdaptiveFamily : AdaptiveReleaseKernelFamily Unit Bool where
  stepKernel := fun n _ => branchingReleaseKernel n
  stepKernel_isMarkov := fun n _ => branchingReleaseKernel_isMarkov n

theorem branchingAdaptiveFamily_step_pure
    (n : ℕ) (history : AdaptiveReleaseHistory Bool) :
    ApproxDP (fun _ _ : Unit => True)
      (fun dataset =>
        branchingAdaptiveFamily.historyAdvanceKernel n dataset history)
      0 0 := by
  apply approxDP_of_dataset_independent
  intro left right
  cases left
  cases right
  rfl

theorem branchingAdaptiveFamily_zeroStep_pure :
    ApproxDP (fun _ _ : Unit => True)
      (branchingAdaptiveFamily.transcriptMeasure falseHistory 0) 0 0 := by
  simpa using
    branchingAdaptiveFamily.transcriptApproxDP_pure falseHistory
      (fun _ _ : Unit => True) (fun _ => 0)
      branchingAdaptiveFamily_step_pure 0

theorem branchingAdaptiveFamily_oneStep_pure :
    ApproxDP (fun _ _ : Unit => True)
      (branchingAdaptiveFamily.transcriptMeasure falseHistory 1) 0 0 := by
  simpa using
    branchingAdaptiveFamily.transcriptApproxDP_pure falseHistory
      (fun _ _ : Unit => True) (fun _ => 0)
      branchingAdaptiveFamily_step_pure 1

/-- The genuinely adaptive two-step example elaborates through the recursive
bind law without any imported privacy certificate. -/
theorem branchingAdaptiveFamily_twoStep_pure :
    ApproxDP (fun _ _ : Unit => True)
      (branchingAdaptiveFamily.transcriptMeasure falseHistory 2) 0 0 := by
  simpa using
    branchingAdaptiveFamily.transcriptApproxDP_pure falseHistory
      (fun _ _ : Unit => True) (fun _ => 0)
      branchingAdaptiveFamily_step_pure 2

def historyWithFirst (value : Bool) : AdaptiveReleaseHistory Bool :=
  fun i => if i = 0 then value else false

/-- The second row is not a fixed release law: changing the first history
coordinate changes the next measure.  Consequently a product of fixed rows is
not definitionally or propositionally the adaptive transcript mechanism. -/
theorem branching_second_row_not_fixed :
    branchingReleaseKernel 1 (historyWithFirst false) ≠
      branchingReleaseKernel 1 (historyWithFirst true) := by
  intro heq
  have happ := congrArg (fun μ : Measure Bool => μ {true}) heq
  simp [branchingReleaseKernel] at happ
  rw [Kernel.deterministic_apply, Kernel.deterministic_apply] at happ
  simp [historyWithFirst] at happ

end HistoryDependentExample

end
end DP
end Mf
