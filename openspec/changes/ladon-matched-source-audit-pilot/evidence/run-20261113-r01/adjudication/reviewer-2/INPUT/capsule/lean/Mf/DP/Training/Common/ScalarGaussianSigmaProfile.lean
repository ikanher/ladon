import Mf.DP.Training.Common.GlobalSigmaOptimality
import Mf.DP.GaussianDP

namespace Mf
namespace DP
namespace Training

noncomputable section

/-!
# Scalar Gaussian profile as a function of sigma

The signal-to-noise parameter is `signal / sigma`. For positive signal this
makes the exact scalar GDP profile continuous and strictly decreasing on the
positive sigma axis.
-/

/-- Scalar Gaussian profile at signal norm `signal` and noise scale `sigma`. -/
def scalarGaussianSigmaProfile
    (signal epsilon sigma : ℝ) : ℝ :=
  gdpProfile (signal / sigma) epsilon

/-- The positive-parameter GDP profile is strictly increasing in signal/noise. -/
theorem gdpProfile_strictMonoOn_pos
    (epsilon : ℝ) :
    StrictMonoOn (fun mu : ℝ => gdpProfile mu epsilon) (Set.Ioi 0) := by
  intro left hleft right hright hlt
  change gdpProfile left epsilon < gdpProfile right epsilon
  rw [gdpProfile_eq_bridgeProfile_of_ne (ne_of_gt hleft)]
  rw [gdpProfile_eq_bridgeProfile_of_ne (ne_of_gt hright)]
  exact strictMonoOn_bridgeProfile epsilon
    (show 0 < left / (2 : ℝ) from
      div_pos (show 0 < left from hleft) (by norm_num))
    (show 0 < right / (2 : ℝ) from
      div_pos (show 0 < right from hright) (by norm_num))
    (div_lt_div_of_pos_right hlt (by norm_num : (0 : ℝ) < 2))

/-- The GDP profile is continuous on positive signal/noise parameters. -/
theorem continuousOn_gdpProfile_pos
    (epsilon : ℝ) :
    ContinuousOn (fun mu : ℝ => gdpProfile mu epsilon) (Set.Ioi 0) := by
  have hbridge :
      ContinuousOn (fun a : ℝ => bridgeProfile a epsilon) (Set.Ioi 0) := by
    intro a ha
    exact (hasDerivAt_bridgeProfile epsilon a (ne_of_gt ha)).continuousAt.continuousWithinAt
  have hhalf : ContinuousOn (fun mu : ℝ => mu / 2) (Set.Ioi 0) :=
    (continuous_id.div_const 2).continuousOn
  have hmaps : Set.MapsTo (fun mu : ℝ => mu / 2) (Set.Ioi 0) (Set.Ioi 0) := by
    intro mu hmu
    exact div_pos (show 0 < mu from hmu) (by norm_num)
  have hcomp := hbridge.comp hhalf hmaps
  apply hcomp.congr
  intro mu hmu
  change gdpProfile mu epsilon = bridgeProfile (mu / 2) epsilon
  exact gdpProfile_eq_bridgeProfile_of_ne (ne_of_gt hmu)

/-- Positive signal-to-noise is continuous as sigma varies over positive reals. -/
theorem continuousOn_signal_div_pos
    (signal : ℝ) :
    ContinuousOn (fun sigma : ℝ => signal / sigma) (Set.Ioi 0) := by
  intro sigma hsigma
  exact continuousAt_const.div continuousAt_id (ne_of_gt hsigma) |>.continuousWithinAt

/-- The exact scalar Gaussian profile is continuous in positive sigma. -/
theorem continuousOn_scalarGaussianSigmaProfile_pos
    {signal : ℝ} (hsignal : 0 < signal) (epsilon : ℝ) :
    ContinuousOn
      (scalarGaussianSigmaProfile signal epsilon)
      (Set.Ioi 0) := by
  have hmaps :
      Set.MapsTo (fun sigma : ℝ => signal / sigma)
        (Set.Ioi 0) (Set.Ioi 0) := by
    intro sigma hsigma
    exact div_pos hsignal hsigma
  exact (continuousOn_gdpProfile_pos epsilon).comp
    (continuousOn_signal_div_pos signal) hmaps

/-- For positive signal, the scalar Gaussian profile strictly decreases in sigma. -/
theorem strictAntiOn_scalarGaussianSigmaProfile_pos
    {signal : ℝ} (hsignal : 0 < signal) (epsilon : ℝ) :
    StrictAntiOn
      (scalarGaussianSigmaProfile signal epsilon)
      (Set.Ioi 0) := by
  intro left hleft right hright hlt
  apply gdpProfile_strictMonoOn_pos epsilon
    (div_pos hsignal hright)
    (div_pos hsignal hleft)
  rw [div_lt_div_iff₀ hright hleft]
  nlinarith

/-- Existing GaussianCore scaling identity in the sigma-profile notation. -/
theorem scalarGaussianSigmaProfile_eq_analyticGaussianExpr
    {signal sigma epsilon : ℝ} (hsigma : 0 < sigma) :
    scalarGaussianSigmaProfile signal epsilon sigma =
      analyticGaussianExpr signal sigma epsilon := by
  exact congrFun (gdpProfile_eq_analyticGaussianExpr_div hsigma) epsilon

/-- The exact scalar GDP profile tends to one as signal/noise tends to infinity. -/
theorem tendsto_gdpProfile_atTop_one
    (epsilon : ℝ) :
    Filter.Tendsto (fun mu : ℝ => gdpProfile mu epsilon)
      Filter.atTop (nhds 1) := by
  have hhalf :
      Filter.Tendsto (fun mu : ℝ => mu / 2) Filter.atTop Filter.atTop :=
    Filter.tendsto_id.atTop_div_const (by norm_num)
  have hdiv :
      Filter.Tendsto (fun mu : ℝ => epsilon / mu)
        Filter.atTop (nhds 0) :=
    Filter.tendsto_id.const_div_atTop epsilon
  have hplus :
      Filter.Tendsto
        (fun mu : ℝ => mu / 2 - epsilon / mu)
        Filter.atTop Filter.atTop := by
    simpa [sub_eq_add_neg] using hhalf.atTop_add hdiv.neg
  have hminusHalf :
      Filter.Tendsto (fun mu : ℝ => -(mu / 2))
        Filter.atTop Filter.atBot := by
    exact Filter.tendsto_neg_atTop_atBot.comp hhalf
  have hminus :
      Filter.Tendsto
        (fun mu : ℝ => -mu / 2 - epsilon / mu)
        Filter.atTop Filter.atBot := by
    simpa [sub_eq_add_neg, neg_div] using hminusHalf.atBot_add hdiv.neg
  have hcdfTop :
      Filter.Tendsto stdNormalCDFReal Filter.atTop (nhds 1) := by
    change Filter.Tendsto (fun x => ProbabilityTheory.cdf stdNormalMeasure x)
      Filter.atTop (nhds 1)
    exact ProbabilityTheory.tendsto_cdf_atTop stdNormalMeasure
  have hcdfBot :
      Filter.Tendsto stdNormalCDFReal Filter.atBot (nhds 0) := by
    change Filter.Tendsto (fun x => ProbabilityTheory.cdf stdNormalMeasure x)
      Filter.atBot (nhds 0)
    exact ProbabilityTheory.tendsto_cdf_atBot (μ := stdNormalMeasure)
  have hplusCDF := hcdfTop.comp hplus
  have hminusCDF := hcdfBot.comp hminus
  have hscaled :
      Filter.Tendsto
        (fun mu : ℝ => Real.exp epsilon *
          stdNormalCDFReal (-mu / 2 - epsilon / mu))
        Filter.atTop (nhds 0) := by
    simpa using hminusCDF.const_mul (Real.exp epsilon)
  have hresult := hplusCDF.sub hscaled
  simpa [gdpProfile_eq, gdpProfileCDFPlusArg,
    gdpProfileCDFMinusArg] using hresult

/-- Positive signal/noise diverges when positive sigma tends to zero from above. -/
theorem tendsto_signal_div_nhdsWithin_zero_atTop
    {signal : ℝ} (hsignal : 0 < signal) :
    Filter.Tendsto (fun sigma : ℝ => signal / sigma)
      (nhdsWithin 0 (Set.Ioi 0)) Filter.atTop := by
  simpa [div_eq_mul_inv] using
    (Filter.Tendsto.const_mul_atTop hsignal tendsto_inv_nhdsGT_zero)

/-- The scalar sigma profile tends to one as positive sigma tends to zero. -/
theorem tendsto_scalarGaussianSigmaProfile_nhdsWithin_zero_one
    {signal : ℝ} (hsignal : 0 < signal) (epsilon : ℝ) :
    Filter.Tendsto (scalarGaussianSigmaProfile signal epsilon)
      (nhdsWithin 0 (Set.Ioi 0)) (nhds 1) := by
  exact (tendsto_gdpProfile_atTop_one epsilon).comp
    (tendsto_signal_div_nhdsWithin_zero_atTop hsignal)

end

end Training
end DP
end Mf
