import Mf.DP.SampledGaussianOneStepRange
import Mathlib.Analysis.Calculus.ImplicitContDiff

set_option maxHeartbeats 800000

open Set Filter
open scoped Topology ContDiff

namespace Mf.DP

noncomputable section

lemma contDiff_one_stdNormalCDFReal : ContDiff Real 1 stdNormalCDFReal := by
  rw [contDiff_one_iff_deriv]
  constructor
  · exact fun x => (hasDerivAt_stdNormalCDFReal x).differentiableAt
  · have hderiv : deriv stdNormalCDFReal = stdNormalPdfReal := by
      funext x
      exact (hasDerivAt_stdNormalCDFReal x).deriv
    rw [hderiv, continuous_iff_continuousAt]
    exact fun x => (hasDerivAt_stdNormalPdfReal x).continuousAt

theorem oneStepSampledGaussianPsi_existsUnique_positive_root
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta : delta ∈ Ioo 0 q) :
    ∃! sigma : Real, sigma ∈ Ioi 0 ∧
      oneStepSampledGaussianPsi epsilon q sigma = delta := by
  have hbij := oneStepSampledGaussianPsi_bijOn_positive
    epsilon q hepsilon hq hqOne
  rcases hbij.surjOn hdelta with ⟨sigma, hsigma, hsigmaEq⟩
  refine ⟨sigma, ⟨hsigma, hsigmaEq⟩, ?_⟩
  intro other hother
  exact hbij.injOn hother.1 hsigma (hother.2.trans hsigmaEq.symm)

def OneStepSampledGaussianCalibrationDomain
    (epsilon q delta : Real) : Prop :=
  0 ≤ epsilon ∧ 0 < q ∧ q ≤ 1 ∧ delta ∈ Ioo 0 q

noncomputable def oneStepSampledGaussianCalibratedStddev
    (epsilon q delta : Real) : Real := by
  classical
  exact if h : OneStepSampledGaussianCalibrationDomain epsilon q delta then
      Classical.choose
        (oneStepSampledGaussianPsi_existsUnique_positive_root
          epsilon q delta h.1 h.2.1 h.2.2.1 h.2.2.2)
    else 0

theorem oneStepSampledGaussianCalibratedStddev_pos
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta : delta ∈ Ioo 0 q) :
    0 < oneStepSampledGaussianCalibratedStddev epsilon q delta := by
  rw [oneStepSampledGaussianCalibratedStddev, dif_pos ⟨hepsilon, hq, hqOne, hdelta⟩]
  exact (Classical.choose_spec
    (oneStepSampledGaussianPsi_existsUnique_positive_root
      epsilon q delta hepsilon hq hqOne hdelta)).1.1

theorem oneStepSampledGaussianCalibratedStddev_profile_eq
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta : delta ∈ Ioo 0 q) :
    oneStepSampledGaussianPsi epsilon q
      (oneStepSampledGaussianCalibratedStddev epsilon q delta) = delta := by
  rw [oneStepSampledGaussianCalibratedStddev, dif_pos ⟨hepsilon, hq, hqOne, hdelta⟩]
  exact (Classical.choose_spec
    (oneStepSampledGaussianPsi_existsUnique_positive_root
      epsilon q delta hepsilon hq hqOne hdelta)).1.2

theorem oneStepSampledGaussianCalibratedStddev_unique
    (epsilon q delta sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta : delta ∈ Ioo 0 q)
    (hsigma : 0 < sigma)
    (hprofile : oneStepSampledGaussianPsi epsilon q sigma = delta) :
    sigma = oneStepSampledGaussianCalibratedStddev epsilon q delta := by
  exact (oneStepSampledGaussianPsi_existsUnique_positive_root
    epsilon q delta hepsilon hq hqOne hdelta).unique
      ⟨hsigma, hprofile⟩
      ⟨oneStepSampledGaussianCalibratedStddev_pos
        epsilon q delta hepsilon hq hqOne hdelta,
       oneStepSampledGaussianCalibratedStddev_profile_eq
        epsilon q delta hepsilon hq hqOne hdelta⟩

theorem oneStepSampledGaussianPsi_ne_zero_of_pos
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hsigma : 0 < sigma) :
    oneStepSampledGaussianPsi epsilon q sigma ≠ 0 := by
  have hmem : oneStepSampledGaussianPsi epsilon q sigma ∈ Ioo 0 q :=
    (oneStepSampledGaussianPsi_bijOn_positive
      epsilon q hepsilon hq hqOne).mapsTo hsigma
  exact ne_of_gt hmem.1

theorem oneStepSampledGaussianPsi_ne_of_target_nonpos
    (epsilon q delta sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta : delta ≤ 0) (hsigma : 0 < sigma) :
    oneStepSampledGaussianPsi epsilon q sigma ≠ delta := by
  have hmem : oneStepSampledGaussianPsi epsilon q sigma ∈ Ioo 0 q :=
    (oneStepSampledGaussianPsi_bijOn_positive
      epsilon q hepsilon hq hqOne).mapsTo hsigma
  exact ne_of_gt (lt_of_le_of_lt hdelta hmem.1)

theorem oneStepSampledGaussianPsi_ne_of_rate_le_target
    (epsilon q delta sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hqd : q ≤ delta) (hsigma : 0 < sigma) :
    oneStepSampledGaussianPsi epsilon q sigma ≠ delta := by
  have hmem : oneStepSampledGaussianPsi epsilon q sigma ∈ Ioo 0 q :=
    (oneStepSampledGaussianPsi_bijOn_positive
      epsilon q hepsilon hq hqOne).mapsTo hsigma
  exact ne_of_lt (lt_of_lt_of_le hmem.2 hqd)

theorem oneStepSampledGaussianPsi_no_positive_root_zero
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) :
    ¬ ∃ sigma : Real, 0 < sigma ∧
      oneStepSampledGaussianPsi epsilon q sigma = 0 := by
  rintro ⟨sigma, hsigma, hsigmaEq⟩
  exact oneStepSampledGaussianPsi_ne_zero_of_pos
    epsilon q sigma hepsilon hq hqOne hsigma hsigmaEq

theorem oneStepSampledGaussianPsi_no_positive_root_of_rate_le_target
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hqd : q ≤ delta) :
    ¬ ∃ sigma : Real, 0 < sigma ∧
      oneStepSampledGaussianPsi epsilon q sigma = delta := by
  rintro ⟨sigma, hsigma, hsigmaEq⟩
  exact oneStepSampledGaussianPsi_ne_of_rate_le_target
    epsilon q delta sigma hepsilon hq hqOne hqd hsigma hsigmaEq

def oneStepSampledGaussianPsiRatePartial (epsilon q sigma : Real) : Real :=
  stdNormalCDFReal (oneStepSampledGaussianPsiArgPlus epsilon q sigma) -
    stdNormalCDFReal (oneStepSampledGaussianPsiArgMinus epsilon q sigma)

def oneStepSampledGaussianPsiNoisePartial (epsilon q sigma : Real) : Real :=
  -q * stdNormalPdfReal (oneStepSampledGaussianPsiArgPlus epsilon q sigma) / sigma ^ 2

def oneStepSampledGaussianPsiRateFDeriv (epsilon q sigma : Real) : Real →L[Real] Real :=
  ContinuousLinearMap.toSpanSingleton Real
    (oneStepSampledGaussianPsiRatePartial epsilon q sigma)

def oneStepSampledGaussianPsiNoiseFDeriv (epsilon q sigma : Real) : Real →L[Real] Real :=
  ContinuousLinearMap.toSpanSingleton Real
    (oneStepSampledGaussianPsiNoisePartial epsilon q sigma)

example (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    ContDiffAt Real 1
      (fun p : Real × Real => oneStepSampledGaussianPsi epsilon p.1 p.2)
      (q, sigma) := by
  have hplus : ContDiffAt Real 1
      (fun p : Real × Real => oneStepSampledGaussianPsiArgPlus epsilon p.1 p.2)
      (q, sigma) := by
    have hh : 0 < Real.exp epsilon - 1 + q := by
      have := Real.one_le_exp hepsilon
      linarith
    have hratio : (Real.exp epsilon - 1 + q) / q ≠ 0 :=
      div_ne_zero hh.ne' hq.ne'
    unfold oneStepSampledGaussianPsiArgPlus oneStepSampledGaussianLogRatio
      oneStepSampledGaussianH
    fun_prop (disch := aesop)
  have hminus : ContDiffAt Real 1
      (fun p : Real × Real => oneStepSampledGaussianPsiArgMinus epsilon p.1 p.2)
      (q, sigma) := by
    have hh : 0 < Real.exp epsilon - 1 + q := by
      have := Real.one_le_exp hepsilon
      linarith
    have hratio : (Real.exp epsilon - 1 + q) / q ≠ 0 :=
      div_ne_zero hh.ne' hq.ne'
    unfold oneStepSampledGaussianPsiArgMinus oneStepSampledGaussianLogRatio
      oneStepSampledGaussianH
    fun_prop (disch := aesop)
  have hcdfPlus := contDiff_one_stdNormalCDFReal.contDiffAt.comp (q, sigma) hplus
  have hcdfMinus := contDiff_one_stdNormalCDFReal.contDiffAt.comp (q, sigma) hminus
  unfold oneStepSampledGaussianPsi oneStepSampledGaussianH
  fun_prop

theorem oneStepSampledGaussianPsi_eventually_hasFDerivAt_rate
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    ∀ᶠ v in 𝓝 (q, sigma),
      HasFDerivAt (fun r : Real => oneStepSampledGaussianPsi epsilon r v.2)
        (oneStepSampledGaussianPsiRateFDeriv epsilon v.1 v.2) v.1 := by
  have hqEventually : ∀ᶠ v : Real × Real in 𝓝 (q, sigma), 0 < v.1 :=
    continuousAt_fst.eventually (Ioi_mem_nhds hq)
  have hsigmaEventually : ∀ᶠ v : Real × Real in 𝓝 (q, sigma), 0 < v.2 :=
    continuousAt_snd.eventually (Ioi_mem_nhds hsigma)
  filter_upwards [hqEventually, hsigmaEventually] with v hvq hvsigma
  exact (oneStepSampledGaussianPsi_hasDerivAt_rate
    epsilon v.1 v.2 hepsilon hvq hvsigma).hasFDerivAt

theorem oneStepSampledGaussianPsi_eventually_hasFDerivAt_noise
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    ∀ᶠ v in 𝓝 (q, sigma),
      HasFDerivAt (fun s : Real => oneStepSampledGaussianPsi epsilon v.1 s)
        (oneStepSampledGaussianPsiNoiseFDeriv epsilon v.1 v.2) v.2 := by
  have hqEventually : ∀ᶠ v : Real × Real in 𝓝 (q, sigma), 0 < v.1 :=
    continuousAt_fst.eventually (Ioi_mem_nhds hq)
  have hsigmaEventually : ∀ᶠ v : Real × Real in 𝓝 (q, sigma), 0 < v.2 :=
    continuousAt_snd.eventually (Ioi_mem_nhds hsigma)
  filter_upwards [hqEventually, hsigmaEventually] with v hvq hvsigma
  exact (oneStepSampledGaussianPsi_hasDerivAt_noise
    epsilon v.1 v.2 hepsilon hvq hvsigma).hasFDerivAt

theorem oneStepSampledGaussianPsiRateFDeriv_continuousAt
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    ContinuousAt
      (Function.uncurry (oneStepSampledGaussianPsiRateFDeriv epsilon))
      (q, sigma) := by
  apply (ContinuousLinearMap.toSpanSingletonCLE
    (𝕜 := Real) (E := Real)).continuous.continuousAt.comp
  unfold oneStepSampledGaussianPsiRatePartial oneStepSampledGaussianPsiArgPlus
    oneStepSampledGaussianPsiArgMinus oneStepSampledGaussianLogRatio
    oneStepSampledGaussianH
  have hh : 0 < Real.exp epsilon - 1 + q := by
    have := Real.one_le_exp hepsilon
    linarith
  have hratio : (Real.exp epsilon - 1 + q) / q ≠ 0 :=
    div_ne_zero hh.ne' hq.ne'
  have hcdf : Continuous stdNormalCDFReal := contDiff_one_stdNormalCDFReal.continuous
  fun_prop (disch := aesop)

theorem oneStepSampledGaussianPsiNoiseFDeriv_continuousAt
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    ContinuousAt
      (Function.uncurry (oneStepSampledGaussianPsiNoiseFDeriv epsilon))
      (q, sigma) := by
  apply (ContinuousLinearMap.toSpanSingletonCLE
    (𝕜 := Real) (E := Real)).continuous.continuousAt.comp
  unfold oneStepSampledGaussianPsiNoisePartial oneStepSampledGaussianPsiArgPlus
    oneStepSampledGaussianLogRatio oneStepSampledGaussianH stdNormalPdfReal
  have hh : 0 < Real.exp epsilon - 1 + q := by
    have := Real.one_le_exp hepsilon
    linarith
  have hratio : (Real.exp epsilon - 1 + q) / q ≠ 0 :=
    div_ne_zero hh.ne' hq.ne'
  fun_prop (disch := aesop)

theorem oneStepSampledGaussianPsiNoiseFDeriv_isInvertible
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    (oneStepSampledGaussianPsiNoiseFDeriv epsilon q sigma).IsInvertible := by
  have hneg : oneStepSampledGaussianPsiNoisePartial epsilon q sigma < 0 := by
    unfold oneStepSampledGaussianPsiNoisePartial
    rw [(oneStepSampledGaussianPsi_hasDerivAt_noise
      epsilon q sigma hepsilon hq hsigma).deriv.symm]
    exact oneStepSampledGaussianPsi_deriv_noise_neg
      epsilon q sigma hepsilon hq hsigma
  let unit : Realˣ := Units.mk0
    (oneStepSampledGaussianPsiNoisePartial epsilon q sigma) hneg.ne
  let equiv : Real ≃L[Real] Real :=
    ContinuousLinearEquiv.unitsEquivAut Real unit
  refine ⟨equiv, ?_⟩
  ext x
  simp [equiv, unit, oneStepSampledGaussianPsiNoiseFDeriv,
    ContinuousLinearEquiv.unitsEquivAut_apply, mul_comm]

theorem oneStepSampledGaussianPsi_exists_local_implicit_curve
    (epsilon q sigma : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hsigma : 0 < sigma) :
    ∃ curve : Real → Real,
      curve q = sigma ∧
      (∀ᶠ r in 𝓝 q,
        oneStepSampledGaussianPsi epsilon r (curve r) =
          oneStepSampledGaussianPsi epsilon q sigma) ∧
      HasDerivAt curve
        (-(oneStepSampledGaussianPsiRatePartial epsilon q sigma) /
          oneStepSampledGaussianPsiNoisePartial epsilon q sigma) q := by
  let dfRate := oneStepSampledGaussianPsi_eventually_hasFDerivAt_rate
    epsilon q sigma hepsilon hq hsigma
  let dfNoise := oneStepSampledGaussianPsi_eventually_hasFDerivAt_noise
    epsilon q sigma hepsilon hq hsigma
  let cRate := oneStepSampledGaussianPsiRateFDeriv_continuousAt
    epsilon q sigma hepsilon hq hsigma
  let cNoise := oneStepSampledGaussianPsiNoiseFDeriv_continuousAt
    epsilon q sigma hepsilon hq hsigma
  let iNoise := oneStepSampledGaussianPsiNoiseFDeriv_isInvertible
    epsilon q sigma hepsilon hq hsigma
  let curve := implicitFunctionOfBivariate dfRate dfNoise cRate cNoise iNoise
  refine ⟨curve, ?_, ?_, ?_⟩
  · exact eq_of_tendsto_nhds
      (tendsto_implicitFunctionOfBivariate dfRate dfNoise cRate cNoise iNoise)
  · exact eventually_apply_implicitFunctionOfBivariate
      dfRate dfNoise cRate cNoise iNoise
  · have hstrict := hasStrictFDerivAt_implicitFunctionOfBivariate
      dfRate dfNoise cRate cNoise iNoise
    have hderiv := hstrict.hasFDerivAt.hasDerivAt
    convert hderiv using 1
    simp only [oneStepSampledGaussianPsiRateFDeriv,
      oneStepSampledGaussianPsiNoiseFDeriv,
      ContinuousLinearMap.neg_apply, ContinuousLinearMap.comp_apply,
      ContinuousLinearMap.toSpanSingleton_apply, smul_eq_mul]
    have hneg : oneStepSampledGaussianPsiNoisePartial epsilon q sigma < 0 := by
      unfold oneStepSampledGaussianPsiNoisePartial
      rw [(oneStepSampledGaussianPsi_hasDerivAt_noise
        epsilon q sigma hepsilon hq hsigma).deriv.symm]
      exact oneStepSampledGaussianPsi_deriv_noise_neg
        epsilon q sigma hepsilon hq hsigma
    let unit : Realˣ := Units.mk0
      (oneStepSampledGaussianPsiNoisePartial epsilon q sigma) hneg.ne
    let equiv : Real ≃L[Real] Real :=
      ContinuousLinearEquiv.unitsEquivAut Real unit
    have hmap : (equiv : Real →L[Real] Real) =
        ContinuousLinearMap.toSpanSingleton Real
          (oneStepSampledGaussianPsiNoisePartial epsilon q sigma) := by
      ext x
      simp [equiv, unit, ContinuousLinearEquiv.unitsEquivAut_apply]
    have hinv :
        (ContinuousLinearMap.toSpanSingleton Real
          (oneStepSampledGaussianPsiNoisePartial epsilon q sigma)).inverse =
          (equiv.symm : Real →L[Real] Real) := by
      rw [← hmap]
      exact ContinuousLinearMap.inverse_equiv equiv
    rw [hinv]
    simp [equiv, unit, ContinuousLinearEquiv.unitsEquivAut_apply_symm,
      div_eq_mul_inv, mul_comm]

/-- The canonical root agrees locally, within the physical-rate domain, with the IFT branch. -/
theorem oneStepSampledGaussianCalibratedStddev_hasDerivWithinAt
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta0 : 0 < delta) (hdeltaq : delta < q) :
    HasDerivWithinAt
      (fun r : Real => oneStepSampledGaussianCalibratedStddev epsilon r delta)
      (-(oneStepSampledGaussianPsiRatePartial epsilon q
          (oneStepSampledGaussianCalibratedStddev epsilon q delta)) /
        oneStepSampledGaussianPsiNoisePartial epsilon q
          (oneStepSampledGaussianCalibratedStddev epsilon q delta))
      (Ioc delta 1) q := by
  let sigma := oneStepSampledGaussianCalibratedStddev epsilon q delta
  have hsigma : 0 < sigma := oneStepSampledGaussianCalibratedStddev_pos
    epsilon q delta hepsilon hq hqOne ⟨hdelta0, hdeltaq⟩
  have hsigmaEq : oneStepSampledGaussianPsi epsilon q sigma = delta :=
    oneStepSampledGaussianCalibratedStddev_profile_eq
      epsilon q delta hepsilon hq hqOne ⟨hdelta0, hdeltaq⟩
  rcases oneStepSampledGaussianPsi_exists_local_implicit_curve
      epsilon q sigma hepsilon hq hsigma with ⟨curve, hcurveQ, hcurveEq, hcurveDeriv⟩
  have hcurvePos : ∀ᶠ r in 𝓝 q, 0 < curve r :=
    hcurveDeriv.continuousAt.eventually (Ioi_mem_nhds (hcurveQ.trans_gt hsigma))
  have hcanonical :
      (fun r : Real => curve r) =ᶠ[𝓝[Ioc delta 1] q]
        (fun r : Real => oneStepSampledGaussianCalibratedStddev epsilon r delta) := by
    filter_upwards [hcurvePos.filter_mono inf_le_left,
      hcurveEq.filter_mono inf_le_left, self_mem_nhdsWithin] with r hcurveRPos hcurveREq hr
    have hrPos : 0 < r := lt_trans hdelta0 hr.1
    exact oneStepSampledGaussianCalibratedStddev_unique
      epsilon r delta (curve r) hepsilon hrPos hr.2 ⟨hdelta0, hr.1⟩
      hcurveRPos (hcurveREq.trans hsigmaEq)
  have hwithin : HasDerivWithinAt curve
      (-(oneStepSampledGaussianPsiRatePartial epsilon q sigma) /
        oneStepSampledGaussianPsiNoisePartial epsilon q sigma)
      (Ioc delta 1) q := hcurveDeriv.hasDerivWithinAt
  apply hwithin.congr_of_eventuallyEq hcanonical.symm
  simpa [sigma] using hcurveQ.symm

/-- Closed-form implicit derivative of the canonical physical one-step calibration. -/
theorem oneStepSampledGaussianCalibratedStddev_hasDerivWithinAt_formula
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) (hdelta0 : 0 < delta) (hdeltaq : delta < q) :
    HasDerivWithinAt
      (fun r : Real => oneStepSampledGaussianCalibratedStddev epsilon r delta)
      (((oneStepSampledGaussianCalibratedStddev epsilon q delta) ^ 2 /
          (q * stdNormalPdfReal (oneStepSampledGaussianPsiArgPlus epsilon q
            (oneStepSampledGaussianCalibratedStddev epsilon q delta)))) *
        oneStepSampledGaussianPsiRatePartial epsilon q
          (oneStepSampledGaussianCalibratedStddev epsilon q delta))
      (Ioc delta 1) q := by
  let sigma := oneStepSampledGaussianCalibratedStddev epsilon q delta
  have hsigma : 0 < sigma := oneStepSampledGaussianCalibratedStddev_pos
    epsilon q delta hepsilon hq hqOne ⟨hdelta0, hdeltaq⟩
  convert oneStepSampledGaussianCalibratedStddev_hasDerivWithinAt
    epsilon q delta hepsilon hq hqOne hdelta0 hdeltaq using 1
  unfold oneStepSampledGaussianPsiNoisePartial
  have hpdf : stdNormalPdfReal (oneStepSampledGaussianPsiArgPlus epsilon q sigma) ≠ 0 :=
    (stdNormalPdfReal_pos _).ne'
  change sigma ^ 2 /
      (q * stdNormalPdfReal (oneStepSampledGaussianPsiArgPlus epsilon q sigma)) *
        oneStepSampledGaussianPsiRatePartial epsilon q sigma =
    -oneStepSampledGaussianPsiRatePartial epsilon q sigma /
      (-q * stdNormalPdfReal (oneStepSampledGaussianPsiArgPlus epsilon q sigma) /
        sigma ^ 2)
  field_simp [hq.ne', hsigma.ne', hpdf]

/-- On the interior sampling-rate domain, the canonical calibration has the ordinary derivative. -/
theorem oneStepSampledGaussianCalibratedStddev_hasDerivAt_formula
    (epsilon q delta : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q < 1) (hdelta0 : 0 < delta) (hdeltaq : delta < q) :
    HasDerivAt
      (fun r : Real => oneStepSampledGaussianCalibratedStddev epsilon r delta)
      (((oneStepSampledGaussianCalibratedStddev epsilon q delta) ^ 2 /
          (q * stdNormalPdfReal (oneStepSampledGaussianPsiArgPlus epsilon q
            (oneStepSampledGaussianCalibratedStddev epsilon q delta)))) *
        oneStepSampledGaussianPsiRatePartial epsilon q
          (oneStepSampledGaussianCalibratedStddev epsilon q delta)) q :=
  (oneStepSampledGaussianCalibratedStddev_hasDerivWithinAt_formula
    epsilon q delta hepsilon hq hqOne.le hdelta0 hdeltaq).hasDerivAt
      (Ioc_mem_nhds hdeltaq hqOne)

end
end Mf.DP
