import Mf.DP.Profile.HockeyStickCore
import Mf.DP.RealizableGaussianOneStep

namespace Mf
namespace DP

open scoped BigOperators

noncomputable section

/-!
Concrete PLD-pair profile evidence rows.

This module sits above `Profile.HockeyStickCore`: it turns density-level
hockey-stick algebra into reusable `concretePLDPair` profile upper certificates
without owning finite-window geometry or Route A/BIS-specific sampler laws.
-/

private lemma measurable_hockeyStickKernel_local (ε : ℝ) :
    Measurable (fun y : ℝ => max (1 - Real.exp ε * Real.exp (-y)) 0) := by
  fun_prop

/--
Local source-space identity for the hockey-stick/profile functional under a
shared base measure and a log-density-ratio map.
-/
theorem expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) (f g : α → ℝ) (ε : ℝ)
    (hf_meas : Measurable f) (hg_meas : Measurable g)
    (hf_pos : ∀ a, 0 < f a) (hg_pos : ∀ a, 0 < g a) :
    expHockeyStickLaw ε ((densityMeasure μ f).map (forwardLossValue f g))
      =
    ∫ x, sourceHockeyStickGapIntegrand ε f g x ∂μ := by
  unfold expHockeyStickLaw hockeyStickLaw
  rw [MeasureTheory.integral_map
    (hφ := (measurable_forwardLossValue hf_meas hg_meas).aemeasurable)
    (hfm := (measurable_hockeyStickKernel_local ε).aestronglyMeasurable)]
  unfold densityMeasure
  rw [integral_withDensity_eq_integral_toReal_smul
    (μ := μ)
    (f_meas := by
      change Measurable fun x => ENNReal.ofReal (f x)
      fun_prop)
    (hf_lt_top := Filter.Eventually.of_forall fun x => by simp)]
  apply MeasureTheory.integral_congr_ae
  exact Filter.Eventually.of_forall fun x => by
    unfold sourceHockeyStickGapIntegrand forwardLossValue
    have hf_nonneg : 0 ≤ f x := le_of_lt (hf_pos x)
    have hf_ne : f x ≠ 0 := ne_of_gt (hf_pos x)
    have hg_ne : g x ≠ 0 := ne_of_gt (hg_pos x)
    have hfg_pos : 0 < f x / g x := div_pos (hf_pos x) (hg_pos x)
    simp [hf_nonneg]
    rw [mul_max_of_nonneg _ _ hf_nonneg]
    have hexp :
        Real.exp (-Real.log (f x / g x)) = g x / f x := by
      rw [Real.exp_neg, Real.exp_log hfg_pos]
      field_simp [hf_ne, hg_ne]
    rw [hexp]
    have hcalc :
        f x * (1 - Real.exp ε * (g x / f x)) = f x - Real.exp ε * g x := by
      field_simp [hf_ne]
    simp [hcalc]

/--
Concrete density-pair profiles are antitone in epsilon.

The theorem is stated directly over the shared-base density representation,
without requiring a probability-measure instance for the pushed-forward PLD
law. Generated transport rows use this to consume a row proved at a rational
lower guard for a log-shifted epsilon at the exact shifted epsilon.
-/
theorem concretePLDPair_profile_antitone_of_epsilon_le
    {α : Type} [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε ε' : ℝ} (hε : ε ≤ ε') (p q : α → ℝ)
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_pos : ∀ x, 0 < p x)
    (hq_pos : ∀ x, 0 < q x)
    (hint :
      MeasureTheory.Integrable (sourceHockeyStickGapIntegrand ε p q) μ) :
    (concretePLDPair μ p q).profile ε' ≤
      (concretePLDPair μ p q).profile ε := by
  have hint' :
      MeasureTheory.Integrable (sourceHockeyStickGapIntegrand ε' p q) μ :=
    integrable_sourceHockeyStickGapIntegrand_of_epsilon_le
      hε p q hp_meas hq_meas (fun x => le_of_lt (hq_pos x)) hint
  have hpoint :
      ∀ x,
        sourceHockeyStickGapIntegrand ε' p q x ≤
          sourceHockeyStickGapIntegrand ε p q x := by
    intro x
    exact
      sourceHockeyStickGapIntegrand_antitone_epsilon
        hε p q x (le_of_lt (hq_pos x))
  rw [PLDPair.profile, PLDPair.profile]
  change
    expHockeyStickLaw ε' ((densityMeasure μ p).map (forwardLossValue p q)) ≤
      expHockeyStickLaw ε ((densityMeasure μ p).map (forwardLossValue p q))
  rw [expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
      μ p q ε' hp_meas hq_meas hp_pos hq_pos]
  rw [expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
      μ p q ε hp_meas hq_meas hp_pos hq_pos]
  exact MeasureTheory.integral_mono_ae hint' hint
    (Filter.Eventually.of_forall hpoint)

/--
Log-free conservative profile bound for a scaled common-covariance Gaussian
cell.

For a subdensity comparison, the hockey-stick gap is pointwise at most the
source subdensity, hence its profile is at most the source mass `a`.  This is a
deliberately loose smoke-proof surface for generated Route A flow tables; tight
rows should use `GDPProfileUpperEvidenceAt` instead.
-/
theorem concretePLDPair_scaled_bsrGaussianPdfReal_profile_le_sourceMass
    {n : ℕ}
    (m m' : BSROutput n)
    (σ ε a b : ℝ)
    (hσ : 0 < σ)
    (ha : 0 < a)
    (hb : 0 < b) :
    (concretePLDPair MeasureTheory.volume
      (fun y => a * bsrGaussianPdfReal σ m y)
      (fun y => b * bsrGaussianPdfReal σ m' y)).profile ε
      ≤ a := by
  let p : BSROutput n → ℝ := fun y => a * bsrGaussianPdfReal σ m y
  let q : BSROutput n → ℝ := fun y => b * bsrGaussianPdfReal σ m' y
  have hp_meas : Measurable p :=
    ((measurable_bsrGaussianPdfReal (σ := σ) (μ := m)).const_mul a)
  have hq_meas : Measurable q :=
    ((measurable_bsrGaussianPdfReal (σ := σ) (μ := m')).const_mul b)
  have hp_pos : ∀ y, 0 < p y := by
    intro y
    exact mul_pos ha (bsrGaussianPdfReal_pos (σ := σ) (μ := m) (y := y) hσ.ne')
  have hq_pos : ∀ y, 0 < q y := by
    intro y
    exact mul_pos hb (bsrGaussianPdfReal_pos (σ := σ) (μ := m') (y := y) hσ.ne')
  have hp_int : MeasureTheory.Integrable p MeasureTheory.volume :=
    (integrable_bsrGaussianPdfReal (σ := σ) (μ := m) hσ.ne').const_mul a
  have hgap_int :
      MeasureTheory.Integrable (sourceHockeyStickGapIntegrand ε p q)
        MeasureTheory.volume :=
    integrable_sourceHockeyStickGapIntegrand_scaled_bsrGaussianPdfReal
      m m' σ ε a b hσ.ne' (le_of_lt ha) (le_of_lt hb)
  have hprofile_eq :
      (concretePLDPair MeasureTheory.volume p q).profile ε
        = ∫ y, sourceHockeyStickGapIntegrand ε p q y ∂MeasureTheory.volume := by
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, p, q] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := MeasureTheory.volume)
        (f := p)
        (g := q)
        (ε := ε)
        hp_meas
        hq_meas
        hp_pos
        hq_pos
  calc
    (concretePLDPair MeasureTheory.volume p q).profile ε
        = ∫ y, sourceHockeyStickGapIntegrand ε p q y ∂MeasureTheory.volume :=
          hprofile_eq
    _ ≤ ∫ y, p y ∂MeasureTheory.volume := by
        refine MeasureTheory.integral_mono_of_nonneg ?_ hp_int ?_
        · exact Filter.Eventually.of_forall fun y =>
            sourceHockeyStickGapIntegrand_nonneg ε p q y
        · exact Filter.Eventually.of_forall fun y =>
            sourceHockeyStickGapIntegrand_le_sourceDensity ε p q
              (fun z => le_of_lt (hp_pos z))
              (fun z => le_of_lt (hq_pos z))
              y
    _ = a := by
        simpa [p] using
          integral_scaled_bsrGaussianPdfReal_eq (σ := σ) (a := a) hσ.ne' m

/--
Profile-level reference-splitting bound for a two-component source mixture.

This lifts `sourceHockeyStickGapIntegrand_source_add_le_reference_split` to
concrete PLD profiles.  It is the generic theorem-facing shape needed for
hidden-mixture routes where the source is a sum of branch subdensities but the
reference is a single density: a caller may split the reference by any
`αSplit ∈ (0,1)` and then certify the two component profiles separately.
-/
theorem concretePLDPair_profile_source_add_le_reference_split
    {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (ε αSplit : ℝ)
    (f₁ f₂ q : α → ℝ)
    (hf₁_meas : Measurable f₁)
    (hf₂_meas : Measurable f₂)
    (hq_meas : Measurable q)
    (hf₁_pos : ∀ x, 0 < f₁ x)
    (hf₂_pos : ∀ x, 0 < f₂ x)
    (hq_pos : ∀ x, 0 < q x)
    (hα_pos : 0 < αSplit)
    (hα_lt : αSplit < 1)
    (hgap₁_int :
      MeasureTheory.Integrable
        (sourceHockeyStickGapIntegrand ε f₁ (fun x => αSplit * q x)) μ)
    (hgap₂_int :
      MeasureTheory.Integrable
        (sourceHockeyStickGapIntegrand ε f₂ (fun x => (1 - αSplit) * q x)) μ) :
    (concretePLDPair μ (fun x : α => f₁ x + f₂ x) q).profile ε
      ≤
    (concretePLDPair μ f₁ (fun x => αSplit * q x)).profile ε
      + (concretePLDPair μ f₂ (fun x => (1 - αSplit) * q x)).profile ε := by
  let mixGap : α → ℝ :=
    sourceHockeyStickGapIntegrand ε (fun x : α => f₁ x + f₂ x) q
  let gap₁ : α → ℝ :=
    sourceHockeyStickGapIntegrand ε f₁ (fun x => αSplit * q x)
  let gap₂ : α → ℝ :=
    sourceHockeyStickGapIntegrand ε f₂ (fun x => (1 - αSplit) * q x)
  have hα_comp_pos : 0 < 1 - αSplit := by linarith
  have hmix_pos : ∀ x, 0 < f₁ x + f₂ x := fun x => add_pos (hf₁_pos x) (hf₂_pos x)
  have hsplit₁_pos : ∀ x, 0 < αSplit * q x := fun x =>
    mul_pos hα_pos (hq_pos x)
  have hsplit₂_pos : ∀ x, 0 < (1 - αSplit) * q x := fun x =>
    mul_pos hα_comp_pos (hq_pos x)
  have hmix_eq :
      (concretePLDPair μ (fun x : α => f₁ x + f₂ x) q).profile ε
        = ∫ x, mixGap x ∂μ := by
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, mixGap] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := fun x : α => f₁ x + f₂ x)
        (g := q)
        (ε := ε)
        (hf₁_meas.add hf₂_meas)
        hq_meas
        hmix_pos
        hq_pos
  have hgap₁_eq :
      (concretePLDPair μ f₁ (fun x => αSplit * q x)).profile ε
        = ∫ x, gap₁ x ∂μ := by
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, gap₁] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := f₁)
        (g := fun x => αSplit * q x)
        (ε := ε)
        hf₁_meas
        (hq_meas.const_mul αSplit)
        hf₁_pos
        hsplit₁_pos
  have hgap₂_eq :
      (concretePLDPair μ f₂ (fun x => (1 - αSplit) * q x)).profile ε
        = ∫ x, gap₂ x ∂μ := by
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, gap₂] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := f₂)
        (g := fun x => (1 - αSplit) * q x)
        (ε := ε)
        hf₂_meas
        (hq_meas.const_mul (1 - αSplit))
        hf₂_pos
        hsplit₂_pos
  have hsplit_int : MeasureTheory.Integrable (fun x => gap₁ x + gap₂ x) μ :=
    hgap₁_int.add hgap₂_int
  calc
    (concretePLDPair μ (fun x : α => f₁ x + f₂ x) q).profile ε
        = ∫ x, mixGap x ∂μ := hmix_eq
    _ ≤ ∫ x, gap₁ x + gap₂ x ∂μ := by
        refine MeasureTheory.integral_mono_of_nonneg ?_ hsplit_int ?_
        · exact Filter.Eventually.of_forall fun x =>
            sourceHockeyStickGapIntegrand_nonneg ε (fun x : α => f₁ x + f₂ x) q x
        · exact Filter.Eventually.of_forall fun x =>
            sourceHockeyStickGapIntegrand_source_add_le_reference_split
              ε αSplit f₁ f₂ q x
    _ = ∫ x, gap₁ x ∂μ + ∫ x, gap₂ x ∂μ := by
        rw [MeasureTheory.integral_add hgap₁_int hgap₂_int]
    _ =
        (concretePLDPair μ f₁ (fun x => αSplit * q x)).profile ε
          + (concretePLDPair μ f₂ (fun x => (1 - αSplit) * q x)).profile ε := by
        rw [hgap₁_eq, hgap₂_eq]

/--
Profile-level finite split-table subadditivity.

This lifts `sourceHockeyStickGapIntegrand_sum_le_sum` from pointwise density
algebra to concrete PLD profiles.  It is intentionally conditional on the
split densities being measurable, positive, and integrable enough for the
profile-integral bridge.  Generated transport evidence should prove the
source/reference split identities separately, then use this theorem to reduce
the aggregate profile to finitely many component-pair profile rows.
-/
theorem concretePLDPair_profile_sum_le_sum_profiles
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (ε : ℝ) (f g : ι → α → ℝ)
    (hf_meas : ∀ i, Measurable (f i))
    (hg_meas : ∀ i, Measurable (g i))
    (hf_pos : ∀ i x, 0 < f i x)
    (hg_pos : ∀ i x, 0 < g i x)
    (hfsum_pos : ∀ x, 0 < ∑ i, f i x)
    (hgsum_pos : ∀ x, 0 < ∑ i, g i x)
    (hgap_int :
      ∀ i,
        MeasureTheory.Integrable
          (sourceHockeyStickGapIntegrand ε (f i) (g i)) μ) :
    (concretePLDPair μ
        (fun x : α => ∑ i, f i x)
        (fun x : α => ∑ i, g i x)).profile ε
      ≤
    ∑ i,
      (concretePLDPair μ (f i) (g i)).profile ε := by
  let mixGap : α → ℝ :=
    sourceHockeyStickGapIntegrand ε
      (fun x : α => ∑ i, f i x)
      (fun x : α => ∑ i, g i x)
  let splitGap : ι → α → ℝ :=
    fun i => sourceHockeyStickGapIntegrand ε (f i) (g i)
  have hmix_meas :
      Measurable (fun x : α => ∑ i, f i x) := by
    exact Finset.measurable_sum _ fun i _ => hf_meas i
  have hmix_ref_meas :
      Measurable (fun x : α => ∑ i, g i x) := by
    exact Finset.measurable_sum _ fun i _ => hg_meas i
  have hmix_eq :
      (concretePLDPair μ
          (fun x : α => ∑ i, f i x)
          (fun x : α => ∑ i, g i x)).profile ε
        = ∫ x, mixGap x ∂μ := by
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, mixGap] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := fun x : α => ∑ i, f i x)
        (g := fun x : α => ∑ i, g i x)
        (ε := ε)
        hmix_meas
        hmix_ref_meas
        hfsum_pos
        hgsum_pos
  have hsplit_eq :
      ∀ i,
        (concretePLDPair μ (f i) (g i)).profile ε
          = ∫ x, splitGap i x ∂μ := by
    intro i
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, splitGap] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := f i)
        (g := g i)
        (ε := ε)
        (hf_meas i)
        (hg_meas i)
        (hf_pos i)
        (hg_pos i)
  have hsplit_int :
      MeasureTheory.Integrable (fun x : α => ∑ i, splitGap i x) μ := by
    refine MeasureTheory.integrable_finset_sum _ ?_
    intro i _hi
    exact hgap_int i
  calc
    (concretePLDPair μ
        (fun x : α => ∑ i, f i x)
        (fun x : α => ∑ i, g i x)).profile ε
        = ∫ x, mixGap x ∂μ := hmix_eq
    _ ≤ ∫ x, ∑ i, splitGap i x ∂μ := by
        refine MeasureTheory.integral_mono_of_nonneg ?_ hsplit_int ?_
        · exact Filter.Eventually.of_forall fun x =>
            sourceHockeyStickGapIntegrand_nonneg ε
              (fun x : α => ∑ i, f i x)
              (fun x : α => ∑ i, g i x)
              x
        · exact Filter.Eventually.of_forall fun x =>
            sourceHockeyStickGapIntegrand_sum_le_sum
              (Finset.univ : Finset ι) ε f g x
    _ = ∑ i, ∫ x, splitGap i x ∂μ := by
        exact MeasureTheory.integral_finset_sum _ (fun i _hi => hgap_int i)
    _ = ∑ i, (concretePLDPair μ (f i) (g i)).profile ε := by
        refine Finset.sum_congr rfl ?_
        intro i _hi
        rw [hsplit_eq i]

/--
Profile-level conservative finite split-table subadditivity.

This is the rounded-table variant of
`concretePLDPair_profile_sum_le_sum_profiles`: the split source sum may
upper-cover the original source, and the split reference sum may lower-cover
the original reference.  This is the preferred theorem surface when generated
transport evidence is rationalized from numerical LP output.
-/
theorem concretePLDPair_profile_le_sum_profiles_of_source_le_sum_reference_ge_sum
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (ε : ℝ) (p q : α → ℝ) (f g : ι → α → ℝ)
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hf_meas : ∀ i, Measurable (f i))
    (hg_meas : ∀ i, Measurable (g i))
    (hp_pos : ∀ x, 0 < p x)
    (hq_pos : ∀ x, 0 < q x)
    (hf_pos : ∀ i x, 0 < f i x)
    (hg_pos : ∀ i x, 0 < g i x)
    (hsource_cover : ∀ x, p x ≤ ∑ i, f i x)
    (hreference_cover : ∀ x, (∑ i, g i x) ≤ q x)
    (hgap_int :
      ∀ i,
        MeasureTheory.Integrable
          (sourceHockeyStickGapIntegrand ε (f i) (g i)) μ) :
    (concretePLDPair μ p q).profile ε
      ≤
    ∑ i,
      (concretePLDPair μ (f i) (g i)).profile ε := by
  let sourceGap : α → ℝ := sourceHockeyStickGapIntegrand ε p q
  let splitGap : ι → α → ℝ :=
    fun i => sourceHockeyStickGapIntegrand ε (f i) (g i)
  have hsource_eq :
      (concretePLDPair μ p q).profile ε
        = ∫ x, sourceGap x ∂μ := by
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, sourceGap] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := p)
        (g := q)
        (ε := ε)
        hp_meas
        hq_meas
        hp_pos
        hq_pos
  have hsplit_eq :
      ∀ i,
        (concretePLDPair μ (f i) (g i)).profile ε
          = ∫ x, splitGap i x ∂μ := by
    intro i
    simpa [PLDPair.profile, concretePLDPair, forwardLossLaw, splitGap] using
      expHockeyStickLaw_densityMeasure_map_forwardLossValue_eq_integral_gap_local
        (μ := μ)
        (f := f i)
        (g := g i)
        (ε := ε)
        (hf_meas i)
        (hg_meas i)
        (hf_pos i)
        (hg_pos i)
  have hsplit_int :
      MeasureTheory.Integrable (fun x : α => ∑ i, splitGap i x) μ := by
    refine MeasureTheory.integrable_finset_sum _ ?_
    intro i _hi
    exact hgap_int i
  calc
    (concretePLDPair μ p q).profile ε
        = ∫ x, sourceGap x ∂μ := hsource_eq
    _ ≤ ∫ x, ∑ i, splitGap i x ∂μ := by
        refine MeasureTheory.integral_mono_of_nonneg ?_ hsplit_int ?_
        · exact Filter.Eventually.of_forall fun x =>
            sourceHockeyStickGapIntegrand_nonneg ε p q x
        · exact Filter.Eventually.of_forall fun x =>
            sourceHockeyStickGapIntegrand_le_sum_of_source_le_sum_reference_ge_sum
              (Finset.univ : Finset ι) ε p q f g x
              (hsource_cover x)
              (hreference_cover x)
    _ = ∑ i, ∫ x, splitGap i x ∂μ := by
        exact MeasureTheory.integral_finset_sum _ (fun i _hi => hgap_int i)
    _ = ∑ i, (concretePLDPair μ (f i) (g i)).profile ε := by
        refine Finset.sum_congr rfl ?_
        intro i _hi
        rw [hsplit_eq i]

/--
Theorem-facing finite split-table profile evidence row.

This is the reusable seam for generated multi-ratio transport evidence.  The
row does not prove that runtime artifacts produced the split table.  Instead,
it requires theorem-facing split densities, exact source/reference sum
identities, component profile upper rows, and aggregate arithmetic.  Once those
fields are supplied, `toProfileUpper` converts the finite split table into a
profile upper for the original concrete PLD pair.
-/
structure ConcretePLDPairFiniteSplitProfileEvidenceAt
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (ε upper : ℝ) where
  source : α → ℝ
  reference : α → ℝ
  splitSource : ι → α → ℝ
  splitReference : ι → α → ℝ
  splitUpper : ι → ℝ
  source_eq : source = fun x => ∑ i, splitSource i x
  reference_eq : reference = fun x => ∑ i, splitReference i x
  splitSource_meas : ∀ i, Measurable (splitSource i)
  splitReference_meas : ∀ i, Measurable (splitReference i)
  splitSource_pos : ∀ i x, 0 < splitSource i x
  splitReference_pos : ∀ i x, 0 < splitReference i x
  sourceSum_pos : ∀ x, 0 < ∑ i, splitSource i x
  referenceSum_pos : ∀ x, 0 < ∑ i, splitReference i x
  splitGap_integrable :
    ∀ i,
      MeasureTheory.Integrable
        (sourceHockeyStickGapIntegrand ε (splitSource i) (splitReference i)) μ
  splitProfile_le :
    ∀ i,
      (concretePLDPair μ (splitSource i) (splitReference i)).profile ε
        ≤ splitUpper i
  aggregate_le : ∑ i, splitUpper i ≤ upper

namespace ConcretePLDPairFiniteSplitProfileEvidenceAt

/--
Convert a finite split-table evidence row into the profile upper it certifies.
-/
theorem toProfileUpper
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε upper : ℝ}
    (row :
      ConcretePLDPairFiniteSplitProfileEvidenceAt
        (ι := ι) (α := α) μ ε upper) :
    (concretePLDPair μ row.source row.reference).profile ε ≤ upper := by
  rw [row.source_eq, row.reference_eq]
  calc
    (concretePLDPair μ
        (fun x : α => ∑ i, row.splitSource i x)
        (fun x : α => ∑ i, row.splitReference i x)).profile ε
        ≤
    ∑ i, (concretePLDPair μ (row.splitSource i) (row.splitReference i)).profile ε :=
      concretePLDPair_profile_sum_le_sum_profiles
        (μ := μ)
        (ε := ε)
        (f := row.splitSource)
        (g := row.splitReference)
        row.splitSource_meas
        row.splitReference_meas
        row.splitSource_pos
        row.splitReference_pos
        row.sourceSum_pos
        row.referenceSum_pos
        row.splitGap_integrable
    _ ≤ ∑ i, row.splitUpper i := by
        exact Finset.sum_le_sum fun i _hi => row.splitProfile_le i
    _ ≤ upper := row.aggregate_le

end ConcretePLDPairFiniteSplitProfileEvidenceAt

/--
Theorem-facing conservative finite split-table profile evidence row.

Use this when generated rational transport evidence deliberately rounds source
split masses upward and reference split masses downward.  The source/reference
cover inequalities replace exact split identities, and `toProfileUpper`
transports the resulting conservative table to a profile upper.
-/
structure ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    (μ : MeasureTheory.Measure α)
    (ε upper : ℝ) where
  source : α → ℝ
  reference : α → ℝ
  splitSource : ι → α → ℝ
  splitReference : ι → α → ℝ
  splitUpper : ι → ℝ
  source_meas : Measurable source
  reference_meas : Measurable reference
  splitSource_meas : ∀ i, Measurable (splitSource i)
  splitReference_meas : ∀ i, Measurable (splitReference i)
  source_pos : ∀ x, 0 < source x
  reference_pos : ∀ x, 0 < reference x
  splitSource_pos : ∀ i x, 0 < splitSource i x
  splitReference_pos : ∀ i x, 0 < splitReference i x
  source_le_splitSum : ∀ x, source x ≤ ∑ i, splitSource i x
  splitReferenceSum_le_reference : ∀ x, (∑ i, splitReference i x) ≤ reference x
  splitGap_integrable :
    ∀ i,
      MeasureTheory.Integrable
        (sourceHockeyStickGapIntegrand ε (splitSource i) (splitReference i)) μ
  splitProfile_le :
    ∀ i,
      (concretePLDPair μ (splitSource i) (splitReference i)).profile ε
        ≤ splitUpper i
  aggregate_le : ∑ i, splitUpper i ≤ upper

namespace ConcretePLDPairFiniteSplitCoverProfileEvidenceAt

/--
Convert a conservative finite split-table evidence row into its profile upper.
-/
theorem toProfileUpper
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε upper : ℝ}
    (row :
      ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
        (ι := ι) (α := α) μ ε upper) :
    (concretePLDPair μ row.source row.reference).profile ε ≤ upper := by
  calc
    (concretePLDPair μ row.source row.reference).profile ε
        ≤
    ∑ i,
      (concretePLDPair μ (row.splitSource i) (row.splitReference i)).profile ε :=
      concretePLDPair_profile_le_sum_profiles_of_source_le_sum_reference_ge_sum
        (μ := μ)
        (ε := ε)
        (p := row.source)
        (q := row.reference)
        (f := row.splitSource)
        (g := row.splitReference)
        row.source_meas
        row.reference_meas
        row.splitSource_meas
        row.splitReference_meas
        row.source_pos
        row.reference_pos
        row.splitSource_pos
        row.splitReference_pos
        row.source_le_splitSum
        row.splitReferenceSum_le_reference
        row.splitGap_integrable
    _ ≤ ∑ i, row.splitUpper i := by
        exact Finset.sum_le_sum fun i _hi => row.splitProfile_le i
    _ ≤ upper := row.aggregate_le

/--
Consume a conservative split-cover row at any larger epsilon.

This is useful for generated Route A rows whose component arithmetic is emitted
at a rational lower guard for a shifted epsilon, while the theorem-facing
Route A facade uses the exact logarithmic shifted epsilon expression.
-/
theorem toProfileUpper_of_epsilon_le
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε ε' upper : ℝ}
    (row :
      ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
        (ι := ι) (α := α) μ ε upper)
    (hε : ε ≤ ε') :
    (concretePLDPair μ row.source row.reference).profile ε' ≤ upper := by
  have hsplitGap_integrable' :
      ∀ i,
        MeasureTheory.Integrable
          (sourceHockeyStickGapIntegrand ε'
            (row.splitSource i) (row.splitReference i)) μ := by
    intro i
    exact
      integrable_sourceHockeyStickGapIntegrand_of_epsilon_le
        hε
        (row.splitSource i)
        (row.splitReference i)
        (row.splitSource_meas i)
        (row.splitReference_meas i)
        (fun x => le_of_lt (row.splitReference_pos i x))
        (row.splitGap_integrable i)
  calc
    (concretePLDPair μ row.source row.reference).profile ε'
        ≤
    ∑ i,
      (concretePLDPair μ (row.splitSource i) (row.splitReference i)).profile ε' :=
      concretePLDPair_profile_le_sum_profiles_of_source_le_sum_reference_ge_sum
        (μ := μ)
        (ε := ε')
        (p := row.source)
        (q := row.reference)
        (f := row.splitSource)
        (g := row.splitReference)
        row.source_meas
        row.reference_meas
        row.splitSource_meas
        row.splitReference_meas
        row.source_pos
        row.reference_pos
        row.splitSource_pos
        row.splitReference_pos
        row.source_le_splitSum
        row.splitReferenceSum_le_reference
        hsplitGap_integrable'
    _ ≤ ∑ i, row.splitUpper i := by
        exact Finset.sum_le_sum fun i _hi => by
          exact le_trans
            (concretePLDPair_profile_antitone_of_epsilon_le
              hε
              (row.splitSource i)
              (row.splitReference i)
              (row.splitSource_meas i)
              (row.splitReference_meas i)
              (row.splitSource_pos i)
              (row.splitReference_pos i)
              (row.splitGap_integrable i))
            (row.splitProfile_le i)
    _ ≤ upper := row.aggregate_le

/--
Consume a conservative split-cover row for an externally supplied density pair.

This is the domination form of `toProfileUpper`: if the target source density is
pointwise below the row source and the row reference density is pointwise below
the target reference, then the row's split-cover upper also bounds the target
profile.  It is useful when generated transport evidence is easier to prove as
safe domination than as exact density equality.
-/
theorem toProfileUpper_of_source_le_reference_ge
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε upper : ℝ}
    {p q : α → ℝ}
    (row :
      ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
        (ι := ι) (α := α) μ ε upper)
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_pos : ∀ x, 0 < p x)
    (hq_pos : ∀ x, 0 < q x)
    (hsource : ∀ x, p x ≤ row.source x)
    (hreference : ∀ x, row.reference x ≤ q x) :
    (concretePLDPair μ p q).profile ε ≤ upper := by
  calc
    (concretePLDPair μ p q).profile ε
        ≤
    ∑ i,
      (concretePLDPair μ (row.splitSource i) (row.splitReference i)).profile ε :=
      concretePLDPair_profile_le_sum_profiles_of_source_le_sum_reference_ge_sum
        (μ := μ)
        (ε := ε)
        (p := p)
        (q := q)
        (f := row.splitSource)
        (g := row.splitReference)
        hp_meas
        hq_meas
        row.splitSource_meas
        row.splitReference_meas
        hp_pos
        hq_pos
        row.splitSource_pos
        row.splitReference_pos
        (fun x => le_trans (hsource x) (row.source_le_splitSum x))
        (fun x => le_trans (row.splitReferenceSum_le_reference x) (hreference x))
        row.splitGap_integrable
    _ ≤ ∑ i, row.splitUpper i := by
        exact Finset.sum_le_sum fun i _hi => row.splitProfile_le i
    _ ≤ upper := row.aggregate_le

/--
Domination form of `toProfileUpper_of_epsilon_le`.

This combines the two safe relaxations used by Route A generated rows: the
target source/reference pair may be pointwise dominated by the row
source/reference pair, and the target epsilon may be larger than the row
epsilon.
-/
theorem toProfileUpper_of_source_le_reference_ge_of_epsilon_le
    {ι α : Type} [Fintype ι] [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε ε' upper : ℝ}
    {p q : α → ℝ}
    (row :
      ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
        (ι := ι) (α := α) μ ε upper)
    (hε : ε ≤ ε')
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_pos : ∀ x, 0 < p x)
    (hq_pos : ∀ x, 0 < q x)
    (hsource : ∀ x, p x ≤ row.source x)
    (hreference : ∀ x, row.reference x ≤ q x) :
    (concretePLDPair μ p q).profile ε' ≤ upper := by
  have hsplitGap_integrable' :
      ∀ i,
        MeasureTheory.Integrable
          (sourceHockeyStickGapIntegrand ε'
            (row.splitSource i) (row.splitReference i)) μ := by
    intro i
    exact
      integrable_sourceHockeyStickGapIntegrand_of_epsilon_le
        hε
        (row.splitSource i)
        (row.splitReference i)
        (row.splitSource_meas i)
        (row.splitReference_meas i)
        (fun x => le_of_lt (row.splitReference_pos i x))
        (row.splitGap_integrable i)
  calc
    (concretePLDPair μ p q).profile ε'
        ≤
    ∑ i,
      (concretePLDPair μ (row.splitSource i) (row.splitReference i)).profile ε' :=
      concretePLDPair_profile_le_sum_profiles_of_source_le_sum_reference_ge_sum
        (μ := μ)
        (ε := ε')
        (p := p)
        (q := q)
        (f := row.splitSource)
        (g := row.splitReference)
        hp_meas
        hq_meas
        row.splitSource_meas
        row.splitReference_meas
        hp_pos
        hq_pos
        row.splitSource_pos
        row.splitReference_pos
        (fun x => le_trans (hsource x) (row.source_le_splitSum x))
        (fun x => le_trans (row.splitReferenceSum_le_reference x) (hreference x))
        hsplitGap_integrable'
    _ ≤ ∑ i, row.splitUpper i := by
        exact Finset.sum_le_sum fun i _hi => by
          exact le_trans
            (concretePLDPair_profile_antitone_of_epsilon_le
              hε
              (row.splitSource i)
              (row.splitReference i)
              (row.splitSource_meas i)
              (row.splitReference_meas i)
              (row.splitSource_pos i)
              (row.splitReference_pos i)
              (row.splitGap_integrable i))
            (row.splitProfile_le i)
    _ ≤ upper := row.aggregate_le

end ConcretePLDPairFiniteSplitCoverProfileEvidenceAt

namespace ConcretePLDPairFiniteSplitCoverProfileEvidenceAt

/--
Single-cell finite split-cover evidence from an already proved profile upper.

This is the sharp single-component constructor.  Unlike `conservativeSingle`,
it does not use the loose `profile <= 1` fallback; generated rows can feed a
scaled Gaussian/GDP component theorem directly through `hprofile`.
-/
def single
    {α : Type} [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε upper : ℝ} {p q : α → ℝ}
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_pos : ∀ x, 0 < p x)
    (hq_pos : ∀ x, 0 < q x)
    (hgap_int :
      MeasureTheory.Integrable (sourceHockeyStickGapIntegrand ε p q) μ)
    (hprofile : (concretePLDPair μ p q).profile ε ≤ upper) :
    ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
      (ι := PUnit) (α := α) μ ε upper where
  source := p
  reference := q
  splitSource := fun _ => p
  splitReference := fun _ => q
  splitUpper := fun _ => upper
  source_meas := hp_meas
  reference_meas := hq_meas
  splitSource_meas := by
    intro _
    exact hp_meas
  splitReference_meas := by
    intro _
    exact hq_meas
  source_pos := hp_pos
  reference_pos := hq_pos
  splitSource_pos := by
    intro _ x
    exact hp_pos x
  splitReference_pos := by
    intro _ x
    exact hq_pos x
  source_le_splitSum := by
    intro x
    simp
  splitReferenceSum_le_reference := by
    intro x
    simp
  splitGap_integrable := by
    intro _
    exact hgap_int
  splitProfile_le := by
    intro _
    exact hprofile
  aggregate_le := by
    simp

/--
Single-cell conservative finite split-cover evidence for probability source
densities.

This constructor is intentionally loose: it uses one split cell identical to
the source/reference pair and the generic probability-law bound
`profile <= 1`.  It is useful as a Lean smoke surface for split-cover plumbing;
sharp generated rows should supply smaller `splitUpper` values instead.
-/
def conservativeSingle
    {α : Type} [MeasurableSpace α]
    {μ : MeasureTheory.Measure α}
    {ε : ℝ} {p q : α → ℝ}
    (hp_meas : Measurable p)
    (hq_meas : Measurable q)
    (hp_pos : ∀ x, 0 < p x)
    (hq_pos : ∀ x, 0 < q x)
    (hgap_int :
      MeasureTheory.Integrable (sourceHockeyStickGapIntegrand ε p q) μ)
    [MeasureTheory.IsProbabilityMeasure (densityMeasure μ p)] :
    ConcretePLDPairFiniteSplitCoverProfileEvidenceAt
      (ι := PUnit) (α := α) μ ε 1 where
  source := p
  reference := q
  splitSource := fun _ => p
  splitReference := fun _ => q
  splitUpper := fun _ => 1
  source_meas := hp_meas
  reference_meas := hq_meas
  splitSource_meas := by
    intro _
    exact hp_meas
  splitReference_meas := by
    intro _
    exact hq_meas
  source_pos := hp_pos
  reference_pos := hq_pos
  splitSource_pos := by
    intro _ x
    exact hp_pos x
  splitReference_pos := by
    intro _ x
    exact hq_pos x
  source_le_splitSum := by
    intro x
    simp
  splitReferenceSum_le_reference := by
    intro x
    simp
  splitGap_integrable := by
    intro _
    exact hgap_int
  splitProfile_le := by
    intro _
    have hmapProb :
        MeasureTheory.IsProbabilityMeasure
          ((densityMeasure μ p).map (forwardLossValue p q)) :=
      MeasureTheory.Measure.isProbabilityMeasure_map
        ((measurable_forwardLossValue hp_meas hq_meas).aemeasurable)
    haveI :
        MeasureTheory.IsProbabilityMeasure
          (concretePLDPair μ p q).forward := by
      simpa [concretePLDPair, forwardLossLaw] using hmapProb
    simpa using
      PLDPair.profile_le_one_of_forward_probability
        (concretePLDPair μ p q) ε
  aggregate_le := by
    simp

end ConcretePLDPairFiniteSplitCoverProfileEvidenceAt

end
end DP
end Mf
