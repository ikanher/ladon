import Mf.DP.SampledGaussianOneStepCalculus

/-!
# Range of the one-step sampled Gaussian profile

Continuity, strict antitonicity, corrected endpoint limits, and the exact
positive-noise range `(0, q)`.
-/

open Set Filter

namespace Mf.DP

noncomputable section

private theorem oneStepSampledGaussianPsi_eq_scaledGaussian
    {epsilon q sigma : Real}
    (hepsilon : 0 ≤ epsilon) (hq : 0 < q) (hsigma : 0 < sigma) :
    oneStepSampledGaussianPsi epsilon q sigma =
      q * Training.scalarGaussianSigmaProfile 1
        (oneStepSampledGaussianLogRatio epsilon q) sigma := by
  simpa using
    (oneStepSampledGaussianPsi_eq_rate_mul_scalarGaussianSigmaProfile
      epsilon q 1 sigma hepsilon hq zero_lt_one hsigma)

/-- The scalar profile is continuous at every positive noise value. -/
theorem oneStepSampledGaussianPsi_continuousOn_positive
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon) (hq : 0 < q) :
    ContinuousOn (oneStepSampledGaussianPsi epsilon q) (Ioi 0) := by
  have hcontinuous : ContinuousOn
      (fun sigma : Real => q * Training.scalarGaussianSigmaProfile 1
        (oneStepSampledGaussianLogRatio epsilon q) sigma) (Ioi 0) :=
    continuousOn_const.mul
      (Training.continuousOn_scalarGaussianSigmaProfile_pos zero_lt_one
        (oneStepSampledGaussianLogRatio epsilon q))
  apply hcontinuous.congr
  intro sigma hsigma
  exact oneStepSampledGaussianPsi_eq_scaledGaussian hepsilon hq hsigma

/-- The scalar profile is strictly decreasing in positive noise. -/
theorem oneStepSampledGaussianPsi_strictAntiOn_positive
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon) (hq : 0 < q) :
    StrictAntiOn (oneStepSampledGaussianPsi epsilon q) (Ioi 0) := by
  intro left hleft right hright hlt
  rw [oneStepSampledGaussianPsi_eq_scaledGaussian hepsilon hq hleft,
    oneStepSampledGaussianPsi_eq_scaledGaussian hepsilon hq hright]
  exact mul_lt_mul_of_pos_left
    (Training.strictAntiOn_scalarGaussianSigmaProfile_pos zero_lt_one
      (oneStepSampledGaussianLogRatio epsilon q) hleft hright hlt) hq

/-- At vanishing positive noise, the scalar profile tends to the sampling rate `q`. -/
theorem oneStepSampledGaussianPsi_tendsto_nhdsWithin_zero
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon) (hq : 0 < q) :
    Tendsto (oneStepSampledGaussianPsi epsilon q)
      (nhdsWithin 0 (Ioi 0)) (nhds q) := by
  have hscaled :=
    (Training.tendsto_scalarGaussianSigmaProfile_nhdsWithin_zero_one
      zero_lt_one (oneStepSampledGaussianLogRatio epsilon q)).const_mul q
  have hfinal := hscaled.congr' (by
    filter_upwards [self_mem_nhdsWithin] with sigma hsigma
    exact (oneStepSampledGaussianPsi_eq_scaledGaussian hepsilon hq hsigma).symm)
  simpa using hfinal

private theorem oneStepSampledGaussianPsi_tendsto_atTop_zero_of_pos_epsilon
    (epsilon q : Real) (hepsilon : 0 < epsilon) (hq : 0 < q) :
    Tendsto (oneStepSampledGaussianPsi epsilon q) atTop (nhds 0) := by
  have hlog : 0 < oneStepSampledGaussianLogRatio epsilon q :=
    oneStepSampledGaussianLogRatio_pos epsilon q hepsilon hq
  have hlinear : Tendsto
      (fun sigma : Real => -sigma * oneStepSampledGaussianLogRatio epsilon q)
      atTop atBot := by
    simpa [mul_comm] using
      tendsto_id.const_mul_atTop_of_neg (neg_lt_zero.mpr hlog)
  have hsmall : Tendsto (fun sigma : Real => 1 / (2 * sigma)) atTop (nhds 0) := by
    convert Filter.tendsto_id.const_div_atTop (1 / 2 : Real) using 1 <;>
      simp [div_eq_mul_inv, mul_comm]
  have hplus : Tendsto
      (oneStepSampledGaussianPsiArgPlus epsilon q) atTop atBot := by
    convert hlinear.atBot_add hsmall using 1 <;>
      simp [oneStepSampledGaussianPsiArgPlus]
  have hminus : Tendsto
      (oneStepSampledGaussianPsiArgMinus epsilon q) atTop atBot := by
    convert hlinear.atBot_add hsmall.neg using 1 <;>
      simp [oneStepSampledGaussianPsiArgMinus, sub_eq_add_neg]
  have hcdfBot : Tendsto stdNormalCDFReal atBot (nhds 0) := by
    simpa [stdNormalCDFReal, stdNormalMeasure] using
      (ProbabilityTheory.tendsto_cdf_atBot (μ := stdNormalMeasure))
  have hfirst := (hcdfBot.comp hplus).const_mul q
  have hsecond := (hcdfBot.comp hminus).const_mul
    (oneStepSampledGaussianH epsilon q)
  simpa [oneStepSampledGaussianPsi] using hfirst.sub hsecond

private theorem oneStepSampledGaussianPsi_tendsto_atTop_zero_of_epsilon_zero
    (q : Real) (hq : 0 < q) :
    Tendsto (oneStepSampledGaussianPsi 0 q) atTop (nhds 0) := by
  have hlog : oneStepSampledGaussianLogRatio 0 q = 0 := by
    unfold oneStepSampledGaussianLogRatio oneStepSampledGaussianH
    rw [Real.exp_zero]
    rw [show (1 - 1 + q) / q = 1 by field_simp [hq.ne']; ring]
    exact Real.log_one
  have hsmall : Tendsto (fun sigma : Real => 1 / (2 * sigma)) atTop (nhds 0) := by
    convert Filter.tendsto_id.const_div_atTop (1 / 2 : Real) using 1 <;>
      simp [div_eq_mul_inv, mul_comm]
  have hcdf : Tendsto
      (fun sigma : Real => stdNormalCDFReal (1 / (2 * sigma)))
      atTop (nhds (stdNormalCDFReal 0)) :=
    (hasDerivAt_stdNormalCDFReal 0).continuousAt.tendsto.comp hsmall
  have hcdfNeg : Tendsto
      (fun sigma : Real => stdNormalCDFReal (-(1 / (2 * sigma))))
      atTop (nhds (stdNormalCDFReal 0)) := by
    have hsmallNeg : Tendsto (fun sigma : Real => -(1 / (2 * sigma)))
        atTop (nhds 0) := by
      convert hsmall.neg using 1 <;> simp
    exact (hasDerivAt_stdNormalCDFReal 0).continuousAt.tendsto.comp hsmallNeg
  have hdiff := hcdf.const_mul q |>.sub (hcdfNeg.const_mul q)
  convert hdiff using 1
  · funext sigma
    simp [oneStepSampledGaussianPsi, oneStepSampledGaussianPsiArgPlus,
      oneStepSampledGaussianPsiArgMinus, oneStepSampledGaussianH, hlog]
  · ring

/-- At infinite noise, the scalar profile tends to zero, including when `epsilon = 0`. -/
theorem oneStepSampledGaussianPsi_tendsto_atTop_zero
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon) (hq : 0 < q) :
    Tendsto (oneStepSampledGaussianPsi epsilon q) atTop (nhds 0) := by
  rcases hepsilon.eq_or_lt with rfl | hepsilon
  · exact oneStepSampledGaussianPsi_tendsto_atTop_zero_of_epsilon_zero q hq
  · exact oneStepSampledGaussianPsi_tendsto_atTop_zero_of_pos_epsilon
      epsilon q hepsilon hq

private theorem strictAnti_image_Ioi_eq_Ioo
    (f : Real → Real) (q : Real)
    (hcontinuous : ContinuousOn f (Ioi 0))
    (hanti : StrictAntiOn f (Ioi 0))
    (hzero : Tendsto f (nhdsWithin 0 (Ioi 0)) (nhds q))
    (htop : Tendsto f atTop (nhds 0)) :
    f '' Ioi 0 = Ioo 0 q := by
  apply Set.Subset.antisymm
  · rintro _ ⟨x, hx, rfl⟩
    change 0 < x at hx
    constructor
    · have hnextPos : x + 1 ∈ Ioi (0 : Real) := by
        change 0 < x + 1
        linarith
      have hnext_lt : f (x + 1) < f x :=
        hanti (show x ∈ Ioi 0 by exact hx) hnextPos (by linarith)
      by_contra hnot
      have hnext_neg : f (x + 1) < 0 :=
        lt_of_lt_of_le hnext_lt (le_of_not_gt hnot)
      have habove : ∀ᶠ z in atTop, f (x + 1) < f z :=
        htop (Ioi_mem_nhds hnext_neg)
      have hbelow : ∀ᶠ z in atTop, f z < f (x + 1) := by
        filter_upwards [Ioi_mem_atTop (x + 1)] with z hz
        change x + 1 < z at hz
        exact hanti hnextPos (show z ∈ Ioi 0 by change 0 < z; linarith) hz
      rcases (habove.and hbelow).exists with ⟨z, hzAbove, hzBelow⟩
      exact lt_asymm hzAbove hzBelow
    · let y : Real := x / 2
      have hyPos : y ∈ Ioi (0 : Real) := by
        change 0 < y
        dsimp [y]
        linarith
      have hyLt : y < x := by dsimp [y]; linarith
      have hx_lt_fy : f x < f y :=
        hanti hyPos (show x ∈ Ioi 0 by exact hx) hyLt
      by_contra hnot
      have hq_lt_fy : q < f y :=
        lt_of_le_of_lt (le_of_not_gt hnot) hx_lt_fy
      have hbelow : ∀ᶠ z in nhdsWithin 0 (Ioi 0), f z < f y :=
        hzero (Iio_mem_nhds hq_lt_fy)
      have habove : ∀ᶠ z in nhdsWithin 0 (Ioi 0), f y < f z := by
        have hltY : ∀ᶠ z in nhdsWithin 0 (Ioi 0), z ∈ Iio y :=
          Filter.Eventually.filter_mono inf_le_left
            (Iio_mem_nhds (show 0 < y from hyPos))
        filter_upwards [self_mem_nhdsWithin, hltY] with z hzPos hzLt
        exact hanti hzPos hyPos hzLt
      letI : (nhdsWithin (0 : Real) (Ioi 0)).NeBot := nhdsGT_neBot 0
      rcases (hbelow.and habove).exists with ⟨z, hzBelow, hzAbove⟩
      exact lt_asymm hzBelow hzAbove
  · intro value hvalue
    exact isPreconnected_Ioi.intermediate_value_Ioo
      (show atTop ≤ Filter.principal (Ioi (0 : Real)) by
        rw [le_principal_iff]
        exact Ioi_mem_atTop 0)
      (show nhdsWithin (0 : Real) (Ioi 0) ≤ Filter.principal (Ioi 0) by
        rw [le_principal_iff]
        exact self_mem_nhdsWithin)
      hcontinuous htop hzero hvalue

/-- Positive noise realizes exactly the open interval `(0, q)`. -/
theorem oneStepSampledGaussianPsi_image_positive
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (_hqOne : q ≤ 1) :
    oneStepSampledGaussianPsi epsilon q '' Ioi 0 = Ioo 0 q := by
  exact strictAnti_image_Ioi_eq_Ioo
    (oneStepSampledGaussianPsi epsilon q) q
    (oneStepSampledGaussianPsi_continuousOn_positive epsilon q hepsilon hq)
    (oneStepSampledGaussianPsi_strictAntiOn_positive epsilon q hepsilon hq)
    (oneStepSampledGaussianPsi_tendsto_nhdsWithin_zero epsilon q hepsilon hq)
    (oneStepSampledGaussianPsi_tendsto_atTop_zero epsilon q hepsilon hq)

/-- The scalar profile is a bijection from positive noise onto `(0, q)`. -/
theorem oneStepSampledGaussianPsi_bijOn_positive
    (epsilon q : Real) (hepsilon : 0 ≤ epsilon)
    (hq : 0 < q) (hqOne : q ≤ 1) :
    Set.BijOn (oneStepSampledGaussianPsi epsilon q) (Ioi 0) (Ioo 0 q) := by
  have himage := oneStepSampledGaussianPsi_image_positive
    epsilon q hepsilon hq hqOne
  refine ⟨?_,
    (oneStepSampledGaussianPsi_strictAntiOn_positive
      epsilon q hepsilon hq).injOn, ?_⟩
  · intro sigma hsigma
    rw [← himage]
    exact ⟨sigma, hsigma, rfl⟩
  · intro value hvalue
    rw [← himage] at hvalue
    rcases hvalue with ⟨sigma, hsigma, hsigmaValue⟩
    exact ⟨sigma, hsigma, hsigmaValue⟩

end


end Mf.DP
