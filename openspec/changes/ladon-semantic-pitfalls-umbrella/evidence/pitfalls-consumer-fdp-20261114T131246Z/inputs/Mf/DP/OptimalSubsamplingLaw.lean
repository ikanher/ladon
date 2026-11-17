import Mf.DP.FiniteMixtureHockeyStickConvexity
import Mf.DP.OptimalSubsamplingBISLR
import Mf.DP.Training.Common.ExactDensityPairProfile
import Mf.DP.Training.KOutOfT.SchedulePosterior

namespace Mf
namespace DP
namespace OptimalSubsampling

open MeasureTheory

noncomputable section

/-!
# Exact independent-example sampling laws

This module gives the full integer-`k` slice of the `P_{T,k}` design space from
*"Less Random, More Private: What is the Optimal Subsampling Scheme for
DP-SGD?"* (Dong and Özgür, 2026) a common exact Gaussian-mixture profile.  The
paper permits real expected counts, while this owner takes `k : ℕ` to align
with fixed-cardinality BIS.  Within that integer slice, a law constrains only
its expected participation count; fixed count and uniform marginals are
deliberately not implicit.
-/

/-- A probability law on Boolean participation subsets with expected count `k`. -/
structure IndependentExampleSamplingLaw (T k : ℕ) where
  probability : FiniteProbabilityMass (Finset (Fin T))
  expectedCardinality :
    Finset.sum Finset.univ
      (fun s => probability.mass s * (s.card : ℝ)) = (k : ℝ)

namespace IndependentExampleSamplingLaw

/-- Probability mass of a participation subset. -/
def mass {T k : ℕ} (law : IndependentExampleSamplingLaw T k) :
    Finset (Fin T) → ℝ :=
  law.probability.mass

/-- Expected-count sampling laws are determined by their probability mass functions. -/
@[ext] theorem ext
    {T k : ℕ}
    {a b : IndependentExampleSamplingLaw T k}
    (h : a.mass = b.mass) :
    a = b := by
  cases a with
  | mk ap ae =>
    cases b with
    | mk bp be =>
      change ap.mass = bp.mass at h
      have hp : ap = bp := FiniteProbabilityMass.ext h
      subst bp
      rfl

theorem mass_nonneg {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    (s : Finset (Fin T)) :
    0 ≤ law.mass s :=
  law.probability.mass_nonneg s

theorem mass_sum_eq_one {T k : ℕ} (law : IndependentExampleSamplingLaw T k) :
    Finset.sum Finset.univ law.mass = 1 :=
  law.probability.mass_sum_eq_one

theorem exists_mass_pos {T k : ℕ} (law : IndependentExampleSamplingLaw T k) :
    ∃ s, 0 < law.mass s := by
  by_contra h
  push Not at h
  have hzero : ∀ s, law.mass s = 0 := by
    intro s
    exact le_antisymm (h s) (law.mass_nonneg s)
  have hsum := law.mass_sum_eq_one
  simp [hzero] at hsum

/-- Coordinate participation marginal. -/
def marginal {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    (i : Fin T) : ℝ :=
  Finset.sum Finset.univ
    (fun s => law.mass s * if i ∈ s then (1 : ℝ) else 0)

/-- The coordinate marginals sum to the law's expected participation count. -/
theorem marginal_sum_eq_expectedCardinality
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k) :
    Finset.sum Finset.univ law.marginal = (k : ℝ) := by
  classical
  unfold marginal
  calc
    Finset.sum Finset.univ
        (fun i : Fin T =>
          Finset.sum Finset.univ
            (fun s : Finset (Fin T) =>
              law.mass s * if i ∈ s then (1 : ℝ) else 0))
        =
      Finset.sum Finset.univ
        (fun s : Finset (Fin T) =>
          Finset.sum Finset.univ
            (fun i : Fin T =>
              law.mass s * if i ∈ s then (1 : ℝ) else 0)) := by
          rw [Finset.sum_comm]
    _ =
      Finset.sum Finset.univ
        (fun s : Finset (Fin T) => law.mass s * (s.card : ℝ)) := by
          refine Finset.sum_congr rfl ?_
          intro s _hs
          rw [← Finset.mul_sum]
          simp
    _ = (k : ℝ) := law.expectedCardinality

/-- Weighted squared deviation of the participation count from its mean `k`. -/
def countDeviation {T k : ℕ} (law : IndependentExampleSamplingLaw T k) : ℝ :=
  bisWeightedCountSqDeviation Finset.univ law.mass
    (fun s : Finset (Fin T) => s.card) (k : ℝ)

end IndependentExampleSamplingLaw

/-- The exact uniform fixed-cardinality BIS law in the integer-`k` slice of `P_{T,k}`. -/
def bisSamplingLaw (T k : ℕ) (hk : k ≤ T) :
    IndependentExampleSamplingLaw T k where
  probability :=
    { mass := bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k
      mass_nonneg := bisFixedCardUniformMass_nonneg
        (Finset.univ : Finset (Fin T)) k
      mass_sum_eq_one := by
        simpa using bisFixedCardUniformMass_sum_univ_eq_one
          (Finset.univ : Finset (Fin T)) k (by simpa using hk) }
  expectedCardinality := by
    classical
    let base : Finset (Fin T) := Finset.univ
    let support : Finset (Finset (Fin T)) := base.powersetCard k
    have hsupport :
        Finset.sum Finset.univ
            (fun s : Finset (Fin T) =>
              bisFixedCardUniformMass base k s * (s.card : ℝ)) =
          Finset.sum support
            (fun s : Finset (Fin T) =>
              bisFixedCardUniformMass base k s * (s.card : ℝ)) := by
      symm
      refine Finset.sum_subset (by intro s hs; simp) ?_
      intro s _hs hnot
      simp [bisFixedCardUniformMass, support, hnot]
    rw [hsupport]
    simpa [base, support] using
      bisFixedCardUniformMass_mean_count_eq base k (by simpa [base] using hk)

/-- Every coordinate marginal of uniform fixed-cardinality BIS is `k / T`. -/
theorem bisSamplingLaw_marginal_eq_div
    {T k : ℕ} (hk : k ≤ T) (i : Fin T) :
    (bisSamplingLaw T k hk).marginal i = (k : ℝ) / (T : ℝ) := by
  classical
  unfold IndependentExampleSamplingLaw.marginal
  let base : Finset (Fin T) := Finset.univ
  let support : Finset (Finset (Fin T)) := base.powersetCard k
  have hsupport :
      Finset.sum Finset.univ
          (fun s : Finset (Fin T) =>
            bisFixedCardUniformMass base k s *
              if i ∈ s then (1 : ℝ) else 0) =
        Finset.sum support
          (fun s : Finset (Fin T) =>
            bisFixedCardUniformMass base k s *
              if i ∈ s then (1 : ℝ) else 0) := by
    symm
    refine Finset.sum_subset (by intro s hs; simp) ?_
    intro s _hs hnot
    simp [bisFixedCardUniformMass, support, hnot]
  change
    Finset.sum Finset.univ
        (fun s : Finset (Fin T) =>
          bisFixedCardUniformMass base k s *
            if i ∈ s then (1 : ℝ) else 0) =
      (k : ℝ) / (T : ℝ)
  rw [hsupport]
  simpa [bisFixedCardUniformMarginal, base, support, Finset.card_univ] using
    bisFixedCardUniformMarginal_eq_div_card base i (by simp [base]) k
      (by simpa [base, Finset.card_univ] using hk)

/-- Mass of the law supported only on the empty and full participation sets. -/
def allOrNothingMass (T k : ℕ) (s : Finset (Fin T)) : ℝ :=
  if s = ∅ then 1 - (k : ℝ) / (T : ℝ)
  else if s = Finset.univ then (k : ℝ) / (T : ℝ)
  else 0

private theorem empty_ne_univ_of_T_pos {T : ℕ} (hT : 0 < T) :
    (∅ : Finset (Fin T)) ≠ Finset.univ := by
  intro h
  let i : Fin T := ⟨0, hT⟩
  have hi : i ∈ (∅ : Finset (Fin T)) := by
    rw [h]
    simp
  simp at hi

theorem allOrNothingMass_nonneg
    {T k : ℕ} (hT : 0 < T) (hk : k ≤ T) (s : Finset (Fin T)) :
    0 ≤ allOrNothingMass T k s := by
  have hTR : (0 : ℝ) < T := by exact_mod_cast hT
  have hkR : (k : ℝ) ≤ T := by exact_mod_cast hk
  unfold allOrNothingMass
  split_ifs
  · exact sub_nonneg.mpr ((div_le_one₀ hTR).2 hkR)
  · exact div_nonneg (Nat.cast_nonneg k) hTR.le
  · exact le_rfl

private theorem allOrNothingMass_eq_indicator_sum
    {T k : ℕ} (hT : 0 < T) (s : Finset (Fin T)) :
    allOrNothingMass T k s =
      (if s = ∅ then 1 - (k : ℝ) / (T : ℝ) else 0) +
      (if s = Finset.univ then (k : ℝ) / (T : ℝ) else 0) := by
  have hne := empty_ne_univ_of_T_pos hT
  unfold allOrNothingMass
  by_cases hzero : s = ∅
  · subst s
    simp [hne]
  · by_cases hfull : s = Finset.univ
    · subst s
      simp [hne.symm]
    · simp [hzero, hfull]

theorem allOrNothingMass_sum_eq_one
    {T k : ℕ} (hT : 0 < T) :
    Finset.sum Finset.univ (allOrNothingMass T k) = 1 := by
  classical
  simp_rw [allOrNothingMass_eq_indicator_sum hT]
  rw [Finset.sum_add_distrib]
  simp

theorem allOrNothingMass_expectedCardinality
    {T k : ℕ} (hT : 0 < T) :
    Finset.sum Finset.univ
        (fun s : Finset (Fin T) => allOrNothingMass T k s * (s.card : ℝ)) =
      (k : ℝ) := by
  classical
  have hTR : (T : ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hT)
  simp_rw [allOrNothingMass_eq_indicator_sum hT]
  simp_rw [add_mul]
  rw [Finset.sum_add_distrib]
  simp [hTR]

/-- The empty/full concentrated law, admitted by the paper's family at integer `k`. -/
def allOrNothingSamplingLaw
    (T k : ℕ) (hT : 0 < T) (hk : k ≤ T) :
    IndependentExampleSamplingLaw T k where
  probability :=
    { mass := allOrNothingMass T k
      mass_nonneg := allOrNothingMass_nonneg hT hk
      mass_sum_eq_one := allOrNothingMass_sum_eq_one hT }
  expectedCardinality := allOrNothingMass_expectedCardinality hT

/-- Exact source density for a finite independent-example sampling law. -/
def samplingLawSourceDensity
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    (sigma : ℝ) (y : BSROutput T) : ℝ :=
  Finset.sum Finset.univ
    (fun s => law.mass s *
      bsrGaussianPdfReal sigma (Training.KOutOfT.scheduleScalarMean s) y)

/-- Centered Gaussian reference density shared by all laws at horizon `T`. -/
def samplingLawReferenceDensity
    (T : ℕ) (sigma : ℝ) (y : BSROutput T) : ℝ :=
  bsrGaussianPdfReal sigma (0 : BSROutput T) y

/-- The concentrated law is exactly a two-component empty/full mixture. -/
theorem allOrNothingSamplingLaw_sourceDensity_eq
    {T k : ℕ} (hT : 0 < T) (hk : k ≤ T) (sigma : ℝ) :
    samplingLawSourceDensity (allOrNothingSamplingLaw T k hT hk) sigma =
      fun y =>
        (1 - (k : ℝ) / (T : ℝ)) *
            bsrGaussianPdfReal sigma
              (Training.KOutOfT.scheduleScalarMean
                (∅ : Finset (Fin T))) y
          + ((k : ℝ) / (T : ℝ)) *
            bsrGaussianPdfReal sigma
              (Training.KOutOfT.scheduleScalarMean
                (Finset.univ : Finset (Fin T))) y := by
  classical
  funext y
  unfold samplingLawSourceDensity allOrNothingSamplingLaw
    IndependentExampleSamplingLaw.mass
  simp_rw [allOrNothingMass_eq_indicator_sum hT]
  simp_rw [add_mul]
  rw [Finset.sum_add_distrib]
  simp

/-- Exact two-sided hockey-stick profile of a sampling law. -/
def samplingLawTwoSidedProfile
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    (sigma epsilon : ℝ) : ℝ :=
  (concretePLDPair MeasureTheory.volume
    (samplingLawSourceDensity law sigma)
    (samplingLawReferenceDensity T sigma)).twoSidedProfile epsilon

/-- Exact binary source/reference mechanism of a sampling law. -/
def samplingLawMechanism
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    (sigma : ℝ) :
    Training.DensityPairSide → Measure (BSROutput T) :=
  Training.densityPairMechanism MeasureTheory.volume
    (samplingLawSourceDensity law sigma)
    (samplingLawReferenceDensity T sigma)

theorem measurable_samplingLawSourceDensity
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    (sigma : ℝ) :
    Measurable (samplingLawSourceDensity law sigma) := by
  classical
  unfold samplingLawSourceDensity
  exact Finset.measurable_sum Finset.univ fun s _ =>
    measurable_const.mul (measurable_bsrGaussianPdfReal
      (σ := sigma) (μ := Training.KOutOfT.scheduleScalarMean s))

theorem measurable_samplingLawReferenceDensity
    (T : ℕ) (sigma : ℝ) :
    Measurable (samplingLawReferenceDensity T sigma) := by
  unfold samplingLawReferenceDensity
  exact measurable_bsrGaussianPdfReal
    (σ := sigma) (μ := (0 : BSROutput T))

theorem integrable_samplingLawSourceDensity
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    {sigma : ℝ} (hsigma : sigma ≠ 0) :
    Integrable (samplingLawSourceDensity law sigma) MeasureTheory.volume := by
  classical
  unfold samplingLawSourceDensity
  exact MeasureTheory.integrable_finsetSum _ fun s _ =>
    (integrable_bsrGaussianPdfReal
      sigma (Training.KOutOfT.scheduleScalarMean s) hsigma).const_mul (law.mass s)

theorem integrable_samplingLawReferenceDensity
    (T : ℕ) {sigma : ℝ} (hsigma : sigma ≠ 0) :
    Integrable (samplingLawReferenceDensity T sigma) MeasureTheory.volume := by
  unfold samplingLawReferenceDensity
  exact integrable_bsrGaussianPdfReal sigma (0 : BSROutput T) hsigma

/-- The exact finite-mixture source density has total mass one. -/
theorem integral_samplingLawSourceDensity_eq_one
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    {sigma : ℝ} (hsigma : sigma ≠ 0) :
    ∫ y : BSROutput T,
        samplingLawSourceDensity law sigma y ∂MeasureTheory.volume = 1 := by
  classical
  unfold samplingLawSourceDensity
  rw [show
      (∫ y : BSROutput T,
          ∑ s : Finset (Fin T),
            law.mass s *
              bsrGaussianPdfReal sigma
                (Training.KOutOfT.scheduleScalarMean s) y
          ∂MeasureTheory.volume) =
        ∑ s : Finset (Fin T),
          ∫ y : BSROutput T,
            law.mass s *
              bsrGaussianPdfReal sigma
                (Training.KOutOfT.scheduleScalarMean s) y
            ∂MeasureTheory.volume by
      simpa only [Finset.sum_apply] using
        (MeasureTheory.integral_finsetSum
          (Finset.univ : Finset (Finset (Fin T)))
          (fun s _ =>
            (integrable_bsrGaussianPdfReal
              sigma (Training.KOutOfT.scheduleScalarMean s)
              hsigma).const_mul (law.mass s)))]
  simp_rw [integral_scaled_bsrGaussianPdfReal_eq hsigma]
  exact law.mass_sum_eq_one

/-- The shared centered reference density has total mass one. -/
theorem integral_samplingLawReferenceDensity_eq_one
    (T : ℕ) {sigma : ℝ} (hsigma : sigma ≠ 0) :
    ∫ y : BSROutput T,
        samplingLawReferenceDensity T sigma y ∂MeasureTheory.volume = 1 := by
  unfold samplingLawReferenceDensity
  exact integral_bsrGaussianPdfReal_eq_one hsigma (0 : BSROutput T)

/-- The source density induces a probability measure at nonzero noise. -/
theorem densityMeasure_samplingLawSourceDensity_isProbabilityMeasure
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    {sigma : ℝ} (hsigma : sigma ≠ 0) :
    IsProbabilityMeasure
      (densityMeasure MeasureTheory.volume
        (samplingLawSourceDensity law sigma)) := by
  let component : Finset (Fin T) → BSROutput T → ℝ :=
    fun s => bsrGaussianPdfReal sigma
      (Training.KOutOfT.scheduleScalarMean s)
  change IsProbabilityMeasure
    (densityMeasure MeasureTheory.volume
      (weightedDensity law.mass component))
  exact densityMeasure_weightedDensity_isProbabilityMeasure
    MeasureTheory.volume law.mass component
    law.mass_nonneg
    law.mass_sum_eq_one
    (fun s y => bsrGaussianPdfReal_nonneg sigma
      (Training.KOutOfT.scheduleScalarMean s) y)
    (fun s => measurable_bsrGaussianPdfReal
      (σ := sigma) (μ := Training.KOutOfT.scheduleScalarMean s))
    (fun s => densityMeasure_bsrGaussianPdfReal_isProbabilityMeasure
      hsigma (Training.KOutOfT.scheduleScalarMean s))

/-- The shared reference density induces a probability measure. -/
theorem densityMeasure_samplingLawReferenceDensity_isProbabilityMeasure
    (T : ℕ) {sigma : ℝ} (hsigma : sigma ≠ 0) :
    IsProbabilityMeasure
      (densityMeasure MeasureTheory.volume
        (samplingLawReferenceDensity T sigma)) := by
  unfold samplingLawReferenceDensity
  exact densityMeasure_bsrGaussianPdfReal_isProbabilityMeasure
    hsigma (0 : BSROutput T)

theorem samplingLawSourceDensity_pos
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    {sigma : ℝ} (hsigma : sigma ≠ 0) (y : BSROutput T) :
    0 < samplingLawSourceDensity law sigma y := by
  classical
  rcases law.exists_mass_pos with ⟨s, hs⟩
  have hterm :
      0 < law.mass s *
        bsrGaussianPdfReal sigma (Training.KOutOfT.scheduleScalarMean s) y :=
    mul_pos hs (bsrGaussianPdfReal_pos sigma
      (Training.KOutOfT.scheduleScalarMean s) y hsigma)
  have hle :
      law.mass s *
          bsrGaussianPdfReal sigma (Training.KOutOfT.scheduleScalarMean s) y ≤
        samplingLawSourceDensity law sigma y := by
    unfold samplingLawSourceDensity
    exact Finset.single_le_sum
      (fun u _ => mul_nonneg (law.mass_nonneg u) (bsrGaussianPdfReal_nonneg _ _ _))
      (by simp)
  exact lt_of_lt_of_le hterm hle

theorem samplingLawReferenceDensity_pos
    (T : ℕ) {sigma : ℝ} (hsigma : sigma ≠ 0) (y : BSROutput T) :
    0 < samplingLawReferenceDensity T sigma y := by
  unfold samplingLawReferenceDensity
  exact bsrGaussianPdfReal_pos sigma (0 : BSROutput T) y hsigma

/-- Exact event-level privacy/profile equivalence for every finite sampling law. -/
theorem samplingLaw_approxDP_iff_profile_le
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k)
    {sigma epsilon delta : ℝ}
    (hsigma : 0 < sigma) (hdelta : 0 ≤ delta) :
    ApproxDP Training.densityPairTwoSidedAdj
        (samplingLawMechanism law sigma) epsilon delta ↔
      samplingLawTwoSidedProfile law sigma epsilon ≤ delta := by
  exact Training.densityPair_approxDP_iff_twoSidedProfile_le
    MeasureTheory.volume
    (samplingLawSourceDensity law sigma)
    (samplingLawReferenceDensity T sigma)
    hdelta
    (measurable_samplingLawSourceDensity law sigma)
    (measurable_samplingLawReferenceDensity T sigma)
    (integrable_samplingLawSourceDensity law hsigma.ne')
    (integrable_samplingLawReferenceDensity T hsigma.ne')
    (samplingLawSourceDensity_pos law hsigma.ne')
    (samplingLawReferenceDensity_pos T hsigma.ne')

theorem bisSamplingLaw_sourceDensity_eq
    {t k : ℕ} (hk : k ≤ t + 1) (sigma : ℝ) :
    samplingLawSourceDensity (bisSamplingLaw (t + 1) k hk) sigma =
      (Training.KOutOfT.unitShiftCoordinateGaussianCfg t k hk).density sigma
        KOutOfTBISSide.source := by
  funext y
  simpa [samplingLawSourceDensity, bisSamplingLaw,
    IndependentExampleSamplingLaw.mass,
    Training.KOutOfT.fixedCardinalityScheduleMass] using
    Training.KOutOfT.fixedCardinalityScalarMixtureRealDensity_eq_kOutOfTBarDensity
      t k sigma y

theorem bisSamplingLaw_referenceDensity_eq
    {t k : ℕ} (hk : k ≤ t + 1) (sigma : ℝ) :
    samplingLawReferenceDensity (t + 1) sigma =
      (Training.KOutOfT.unitShiftCoordinateGaussianCfg t k hk).density sigma
        KOutOfTBISSide.reference := by
  funext y
  symm
  exact Training.KOutOfT.registeredReferenceDensity_eq_bsrGaussianPdfReal_zero
    t sigma y

/-- The common-law BIS profile is exactly the existing exact k-out-of-T profile. -/
theorem bisSamplingLaw_profile_eq_existing
    {t k : ℕ} (hk : k ≤ t + 1) (sigma epsilon : ℝ) :
    samplingLawTwoSidedProfile (bisSamplingLaw (t + 1) k hk) sigma epsilon =
      (Training.KOutOfT.unitShiftCoordinateGaussianCfg t k hk).twoSidedProfile
        sigma epsilon := by
  unfold samplingLawTwoSidedProfile
    KOutOfTBISCoordinateGaussianCfg.twoSidedProfile
    KOutOfTBISCoordinateGaussianCfg.pldPair
    exactKOutOfTRandomAllocationPLDPair
  rw [bisSamplingLaw_sourceDensity_eq hk sigma,
    bisSamplingLaw_referenceDensity_eq hk sigma]
  rfl

/-- Count deviation is always nonnegative, while fixed-cardinality BIS attains zero. -/
theorem bis_countDeviation_minimal
    {T k : ℕ} (hk : k ≤ T) (law : IndependentExampleSamplingLaw T k) :
    0 ≤ law.countDeviation ∧
      (bisSamplingLaw T k hk).countDeviation = 0 := by
  constructor
  · exact bisWeightedCountSqDeviation_nonneg
      Finset.univ law.mass (fun s : Finset (Fin T) => s.card) (k : ℝ)
      (fun s _ => law.mass_nonneg s)
  · unfold IndependentExampleSamplingLaw.countDeviation
    unfold bisWeightedCountSqDeviation
    apply Finset.sum_eq_zero
    intro s _hs
    by_cases hcard : s.card = k
    · simp [hcard]
    · have hnot :
          s ∉ (Finset.univ : Finset (Fin T)).powersetCard k := by
        simp [hcard]
      simp [bisSamplingLaw, IndependentExampleSamplingLaw.mass,
        bisFixedCardUniformMass, hnot]

/--
Zero count deviation characterizes fixed cardinality on the positive-mass
support.  It does not characterize the uniform distribution on that support.
-/
theorem countDeviation_eq_zero_iff_positive_mass_card_eq
    {T k : ℕ} (law : IndependentExampleSamplingLaw T k) :
    law.countDeviation = 0 ↔
      ∀ s : Finset (Fin T), 0 < law.mass s → s.card = k := by
  unfold IndependentExampleSamplingLaw.countDeviation
  rw [bisWeightedCountSqDeviation_eq_zero_iff_positive_mass_count_eq_nat
    (s := Finset.univ)
    (mass := law.mass)
    (count := fun s : Finset (Fin T) => s.card)
    (target := k)
    (fun s _ => law.mass_nonneg s)]
  simp only [Finset.mem_univ, true_implies]

end

end OptimalSubsampling
end DP
end Mf
