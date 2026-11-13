import Mf.DP.Training.Common.ScalarGaussianSigmaProfile
import Mf.DP.GaussianProfileLinearBound

namespace Mf
namespace DP
namespace Training

noncomputable section

/-!
# Attained scalar Gaussian sigma threshold

For positive signal, nonnegative epsilon, and `0 < delta < 1`, continuity,
strict decrease, the small-noise limit, and a constructive large-noise upper
point give a unique positive scale where the exact scalar profile equals
delta.
-/

/-- A positive sigma with profile strictly above every nonvacuous delta exists. -/
theorem exists_scalarGaussianSigma_profile_gt
    {signal epsilon delta : ℝ}
    (hsignal : 0 < signal)
    (hdelta_lt : delta < 1) :
    ∃ sigma, 0 < sigma ∧
      delta < scalarGaussianSigmaProfile signal epsilon sigma := by
  have hlimit :=
    tendsto_scalarGaussianSigmaProfile_nhdsWithin_zero_one hsignal epsilon
  have habove :
      ∀ᶠ sigma in nhdsWithin 0 (Set.Ioi 0),
        delta < scalarGaussianSigmaProfile signal epsilon sigma :=
    hlimit (Ioi_mem_nhds hdelta_lt)
  have hpositive :
      ∀ᶠ sigma : ℝ in nhdsWithin 0 (Set.Ioi 0), 0 < sigma := by
    exact self_mem_nhdsWithin
  exact (habove.and hpositive).exists |>.imp fun sigma h =>
    ⟨h.2, h.1⟩

/-- The explicit scale `signal / delta` has scalar profile at most delta. -/
theorem scalarGaussianSigmaProfile_le_delta_at_signal_div_delta
    {signal epsilon delta : ℝ}
    (hsignal : 0 < signal)
    (hepsilon : 0 ≤ epsilon)
    (hdelta : 0 < delta) :
    scalarGaussianSigmaProfile signal epsilon (signal / delta) ≤ delta := by
  have hsigma : 0 < signal / delta := div_pos hsignal hdelta
  have hratio : signal / (signal / delta) = delta := by
    field_simp [ne_of_gt hsignal, ne_of_gt hdelta]
  unfold scalarGaussianSigmaProfile
  rw [hratio]
  exact (gdpProfile_le_mu_div_two (le_of_lt hdelta) hepsilon).trans (by linarith)

/-- The exact scalar profile crosses delta at a unique positive sigma. -/
theorem existsUnique_scalarGaussianSigma_profile_eq
    {signal epsilon delta : ℝ}
    (hsignal : 0 < signal)
    (hepsilon : 0 ≤ epsilon)
    (hdelta : 0 < delta)
    (hdelta_lt : delta < 1) :
    ∃! sigma, 0 < sigma ∧
      scalarGaussianSigmaProfile signal epsilon sigma = delta := by
  rcases exists_scalarGaussianSigma_profile_gt hsignal hdelta_lt with
    ⟨low, hlow_pos, hlow_profile⟩
  let high : ℝ := signal / delta
  have hhigh_pos : 0 < high := div_pos hsignal hdelta
  have hhigh_profile :
      scalarGaussianSigmaProfile signal epsilon high ≤ delta := by
    exact scalarGaussianSigmaProfile_le_delta_at_signal_div_delta
      hsignal hepsilon hdelta
  have hlow_high : low ≤ high := by
    by_contra hnot
    have hhigh_low : high < low := lt_of_not_ge hnot
    have hstrict := strictAntiOn_scalarGaussianSigmaProfile_pos hsignal epsilon
      hhigh_pos hlow_pos hhigh_low
    linarith
  have hcontinuous :
      ContinuousOn (scalarGaussianSigmaProfile signal epsilon)
        (Set.Icc low high) :=
    (continuousOn_scalarGaussianSigmaProfile_pos hsignal epsilon).mono fun sigma hsigma =>
      lt_of_lt_of_le hlow_pos hsigma.1
  have hdelta_mem :
      delta ∈ Set.Icc
        (scalarGaussianSigmaProfile signal epsilon high)
        (scalarGaussianSigmaProfile signal epsilon low) :=
    ⟨hhigh_profile, le_of_lt hlow_profile⟩
  rcases (intermediate_value_Icc' hlow_high hcontinuous hdelta_mem) with
    ⟨sigma, hsigmaIcc, hsigma_profile⟩
  refine ⟨sigma, ⟨lt_of_lt_of_le hlow_pos hsigmaIcc.1, hsigma_profile⟩, ?_⟩
  intro other hother
  by_contra hne
  rcases lt_or_gt_of_ne hne with hlt | hgt
  · have hstrict := strictAntiOn_scalarGaussianSigmaProfile_pos hsignal epsilon
      hother.1 (lt_of_lt_of_le hlow_pos hsigmaIcc.1) hlt
    rw [hother.2, hsigma_profile] at hstrict
    exact (lt_irrefl delta) hstrict
  · have hstrict := strictAntiOn_scalarGaussianSigmaProfile_pos hsignal epsilon
      (lt_of_lt_of_le hlow_pos hsigmaIcc.1) hother.1 hgt
    rw [hsigma_profile, hother.2] at hstrict
    exact (lt_irrefl delta) hstrict

/-- The unique positive scalar Gaussian scale whose exact profile equals delta. -/
def scalarGaussianOptimalSigma
    (signal epsilon delta : ℝ)
    (hsignal : 0 < signal)
    (hepsilon : 0 ≤ epsilon)
    (hdelta : 0 < delta)
    (hdelta_lt : delta < 1) : ℝ :=
  Classical.choose
    (existsUnique_scalarGaussianSigma_profile_eq
      hsignal hepsilon hdelta hdelta_lt)

theorem scalarGaussianOptimalSigma_spec
    {signal epsilon delta : ℝ}
    (hsignal : 0 < signal)
    (hepsilon : 0 ≤ epsilon)
    (hdelta : 0 < delta)
    (hdelta_lt : delta < 1) :
    0 < scalarGaussianOptimalSigma signal epsilon delta
        hsignal hepsilon hdelta hdelta_lt ∧
      scalarGaussianSigmaProfile signal epsilon
          (scalarGaussianOptimalSigma signal epsilon delta
            hsignal hepsilon hdelta hdelta_lt) = delta :=
  (Classical.choose_spec
    (existsUnique_scalarGaussianSigma_profile_eq
      hsignal hepsilon hdelta hdelta_lt)).1

/-- Scalar profile feasibility is exactly the upper ray from the optimum. -/
theorem scalarGaussianOptimalSigma_isGlobalThreshold
    {signal epsilon delta : ℝ}
    (hsignal : 0 < signal)
    (hepsilon : 0 ≤ epsilon)
    (hdelta : 0 < delta)
    (hdelta_lt : delta < 1) :
    IsGlobalSigmaThreshold
      (fun sigma => 0 < sigma ∧
        scalarGaussianSigmaProfile signal epsilon sigma ≤ delta)
      (scalarGaussianOptimalSigma signal epsilon delta
        hsignal hepsilon hdelta hdelta_lt) := by
  let optimal := scalarGaussianOptimalSigma signal epsilon delta
    hsignal hepsilon hdelta hdelta_lt
  have hspec := scalarGaussianOptimalSigma_spec
    hsignal hepsilon hdelta hdelta_lt
  refine ⟨hspec.1, ⟨hspec.1, le_of_eq hspec.2⟩, ?_⟩
  intro sigma hsigma
  constructor
  · intro hprivate
    by_contra hnot
    have hlt : sigma < optimal := lt_of_not_ge hnot
    have hstrict := strictAntiOn_scalarGaussianSigmaProfile_pos hsignal epsilon
      hsigma hspec.1 hlt
    rw [hspec.2] at hstrict
    exact (not_lt_of_ge hprivate.2) hstrict
  · intro hle
    refine ⟨hsigma, ?_⟩
    exact ((strictAntiOn_scalarGaussianSigmaProfile_pos hsignal epsilon).antitoneOn
      hspec.1 hsigma hle).trans_eq hspec.2

end

end Training
end DP
end Mf
