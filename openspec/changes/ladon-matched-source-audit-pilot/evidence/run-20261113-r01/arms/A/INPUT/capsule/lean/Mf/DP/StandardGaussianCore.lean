import Mf.DP.GaussianPrivacyLoss

namespace Mf
namespace DP

open Filter

open scoped BigOperators Topology

noncomputable section

/-!
# Standard Gaussian Scalar Core

BSR-free scalar standard-normal facts used by DP and SDE proofs.  This module
owns ordinary one-dimensional standard-normal CDF/PDF facts and affine
Gaussian interval identities without importing the BSR correlated-noise
surface.
-/

/--
Abstract standard-normal CDF symbol used to encode analytic Gaussian and
DP-Sign scalar sign identities.
-/
def stdNormalCDF (t : ℝ) : ℝ :=
  stdNormalCDFReal t

@[simp] theorem stdNormalCDF_eq_stdNormalCDFReal (t : ℝ) :
    stdNormalCDF t = stdNormalCDFReal t := rfl

/-- The standard normal law is symmetric under negation. -/
theorem stdNormalMeasure_map_neg :
    stdNormalMeasure.map (fun x : ℝ => -x) = stdNormalMeasure := by
  unfold stdNormalMeasure
  simpa using
    (ProbabilityTheory.gaussianReal_map_neg
      (μ := (0 : ℝ)) (v := (1 : NNReal)))

/-- The standard normal CDF takes value `1/2` at `0`. -/
theorem stdNormalCDFReal_zero : stdNormalCDFReal 0 = 1 / 2 := by
  have hsymm :
      stdNormalMeasure (Set.Iic (0 : ℝ)) = stdNormalMeasure (Set.Ici (0 : ℝ)) := by
    calc
      stdNormalMeasure (Set.Iic (0 : ℝ))
          = (stdNormalMeasure.map (fun x : ℝ => -x)) (Set.Iic (0 : ℝ)) := by
              rw [stdNormalMeasure_map_neg]
      _ = stdNormalMeasure ((fun x : ℝ => -x) ⁻¹' Set.Iic (0 : ℝ)) := by
            rw [MeasureTheory.Measure.map_apply (by fun_prop) measurableSet_Iic]
      _ = stdNormalMeasure (Set.Ici (0 : ℝ)) := by
            congr 1
            ext x
            simp
  letI : MeasureTheory.NullSingletonClass stdNormalMeasure := by
    unfold stdNormalMeasure
    exact ProbabilityTheory.nullSingletonClass_gaussianReal
      (μ := (0 : ℝ)) (v := (1 : NNReal)) (by norm_num)
  have hIci_eq_Ioi :
      stdNormalMeasure (Set.Ici (0 : ℝ)) = stdNormalMeasure (Set.Ioi (0 : ℝ)) := by
    have hrestrict :
        stdNormalMeasure.restrict (Set.Ioi (0 : ℝ))
          = stdNormalMeasure.restrict (Set.Ici (0 : ℝ)) := by
      simpa using
        (MeasureTheory.restrict_Ioi_eq_restrict_Ici
          (μ := stdNormalMeasure) (a := (0 : ℝ)))
    simpa using congrArg (fun ν : MeasureTheory.Measure ℝ => ν Set.univ) hrestrict.symm
  have hsplit :
      stdNormalMeasure.real (Set.Iic (0 : ℝ))
        + stdNormalMeasure.real (Set.Ioi (0 : ℝ)) = 1 := by
    simpa using
      (MeasureTheory.probReal_add_probReal_compl
        (μ := stdNormalMeasure) (s := Set.Iic (0 : ℝ)) measurableSet_Iic)
  have hEqReal :
      stdNormalMeasure.real (Set.Iic (0 : ℝ))
        = stdNormalMeasure.real (Set.Ioi (0 : ℝ)) := by
    have hEqMeasure :
        stdNormalMeasure (Set.Iic (0 : ℝ)) = stdNormalMeasure (Set.Ioi (0 : ℝ)) :=
      hsymm.trans hIci_eq_Ioi
    simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hEqMeasure
  have hhalf :
      stdNormalMeasure.real (Set.Iic (0 : ℝ)) = 1 / 2 := by
    linarith
  simpa [stdNormalCDFReal_eq_real_measure_Iic] using hhalf

/-- Symmetry of the standard normal CDF: `Phi(-s) = 1 - Phi(s)`. -/
theorem stdNormalCDFReal_neg (s : ℝ) :
    stdNormalCDFReal (-s) = 1 - stdNormalCDFReal s := by
  letI : MeasureTheory.NullSingletonClass stdNormalMeasure := by
    unfold stdNormalMeasure
    exact ProbabilityTheory.nullSingletonClass_gaussianReal
      (μ := (0 : ℝ)) (v := (1 : NNReal)) (by norm_num)
  have hsymm :
      stdNormalMeasure (Set.Iic (-s)) = stdNormalMeasure (Set.Ici s) := by
    calc
      stdNormalMeasure (Set.Iic (-s))
          = (stdNormalMeasure.map (fun x : ℝ => -x)) (Set.Iic (-s)) := by
              rw [stdNormalMeasure_map_neg]
      _ = stdNormalMeasure ((fun x : ℝ => -x) ⁻¹' Set.Iic (-s)) := by
            rw [MeasureTheory.Measure.map_apply (by fun_prop) measurableSet_Iic]
      _ = stdNormalMeasure (Set.Ici s) := by
            congr 1
            ext x
            simp
  have hIci_eq_Ioi :
      stdNormalMeasure (Set.Ici s) = stdNormalMeasure (Set.Ioi s) := by
    have hrestrict :
        stdNormalMeasure.restrict (Set.Ioi s)
          = stdNormalMeasure.restrict (Set.Ici s) := by
      simpa using
        (MeasureTheory.restrict_Ioi_eq_restrict_Ici
          (μ := stdNormalMeasure) (a := s))
    simpa using congrArg (fun ν : MeasureTheory.Measure ℝ => ν Set.univ) hrestrict.symm
  have hEqReal :
      stdNormalMeasure.real (Set.Iic (-s))
        = stdNormalMeasure.real (Set.Ioi s) := by
    have hEqMeasure :
        stdNormalMeasure (Set.Iic (-s)) = stdNormalMeasure (Set.Ioi s) :=
      hsymm.trans hIci_eq_Ioi
    simpa [MeasureTheory.Measure.real] using congrArg ENNReal.toReal hEqMeasure
  have hsplit :
      stdNormalMeasure.real (Set.Iic s)
        + stdNormalMeasure.real (Set.Ioi s) = 1 := by
    simpa using
      (MeasureTheory.probReal_add_probReal_compl
        (μ := stdNormalMeasure) (s := Set.Iic s) measurableSet_Iic)
  have hgoal :
      stdNormalMeasure.real (Set.Iic (-s))
        = 1 - stdNormalMeasure.real (Set.Iic s) := by
    linarith
  simpa [stdNormalCDFReal_eq_real_measure_Iic] using hgoal

/-- Closed-form standard normal density. -/
def stdNormalPdfReal (x : ℝ) : ℝ :=
  Real.exp (-(x ^ 2) / 2) / Real.sqrt (2 * Real.pi)

lemma stdNormalPdfReal_pos (x : ℝ) : 0 < stdNormalPdfReal x := by
  unfold stdNormalPdfReal
  positivity

/-- Measure-theoretic standard normal density wrapper. -/
noncomputable def stdPdf (x : ℝ) : ℝ :=
  ProbabilityTheory.gaussianPDFReal 0 (1 : NNReal) x

lemma stdPdf_eq_stdNormalPdfReal (x : ℝ) : stdPdf x = stdNormalPdfReal x := by
  unfold stdPdf stdNormalPdfReal
  rw [ProbabilityTheory.gaussianPDFReal_def]
  change (Real.sqrt (2 * Real.pi * (1 : ℝ)))⁻¹
      * Real.exp (-(x - 0) ^ 2 / (2 * (1 : ℝ)))
    = Real.exp (-(x ^ 2) / 2) / Real.sqrt (2 * Real.pi)
  ring_nf

/-- The standard normal density is an even function. -/
theorem stdPdf_neg (x : ℝ) : stdPdf (-x) = stdPdf x := by
  rw [stdPdf_eq_stdNormalPdfReal, stdPdf_eq_stdNormalPdfReal]
  unfold stdNormalPdfReal
  congr 1
  ring_nf

/-- The closed-form standard normal density is an even function. -/
theorem stdNormalPdfReal_neg (x : ℝ) :
    stdNormalPdfReal (-x) = stdNormalPdfReal x := by
  unfold stdNormalPdfReal
  congr 1
  ring_nf

/-- The standard normal density depends only on `|x|`. -/
theorem stdPdf_abs (x : ℝ) : stdPdf |x| = stdPdf x := by
  rcases le_total 0 x with hx | hx
  · rw [abs_of_nonneg hx]
  · rw [abs_of_nonpos hx, stdPdf_neg]

/-- Derivative of the closed-form standard normal density. -/
theorem hasDerivAt_stdNormalPdfReal (t : ℝ) :
    HasDerivAt stdNormalPdfReal (-t * stdNormalPdfReal t) t := by
  unfold stdNormalPdfReal
  have hsq : HasDerivAt (fun x : ℝ => x ^ 2) (2 * t) t := by
    simpa using (hasDerivAt_pow 2 t)
  have harg : HasDerivAt (fun x : ℝ => -(x ^ 2 / 2)) (-t) t := by
    simpa [div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using
      (hsq.const_mul (-(1 / 2 : ℝ)))
  have hexp :
      HasDerivAt (fun x : ℝ => Real.exp (-(x ^ 2 / 2)))
        (Real.exp (-(t ^ 2 / 2)) * (-t)) t := by
    exact (Real.hasDerivAt_exp _).comp t harg
  have hmul := hexp.const_mul (Real.sqrt (2 * Real.pi))⁻¹
  simpa [stdNormalPdfReal, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using hmul

/-- Derivative of the measure-theoretic standard normal density wrapper. -/
theorem hasDerivAt_stdPdf (t : ℝ) :
    HasDerivAt stdPdf (-t * stdPdf t) t := by
  rw [show stdPdf = stdNormalPdfReal by
    funext x
    exact stdPdf_eq_stdNormalPdfReal x]
  exact hasDerivAt_stdNormalPdfReal t

set_option linter.unnecessarySimpa false in
/-- The closed-form standard normal density tends to `0` at `+∞`. -/
theorem tendsto_stdNormalPdfReal_atTop_zero :
    Tendsto stdNormalPdfReal atTop (𝓝 0) := by
  unfold stdNormalPdfReal
  have hpow : Tendsto (fun x : ℝ => x ^ 2) atTop atTop := by
    simpa using
      (tendsto_pow_atTop_atTop_of_one_lt (one_lt_two : (1 : ℝ) < 2))
  have hhalf : Tendsto (fun x : ℝ => x ^ 2 / 2) atTop atTop := by
    simpa [div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using
      (Tendsto.atTop_mul_const (r := (1 / 2 : ℝ)) (by positivity) hpow)
  have hexp : Tendsto (fun x : ℝ => Real.exp (-(x ^ 2 / 2))) atTop (𝓝 0) := by
    simpa [Function.comp_def] using
      (Real.tendsto_exp_neg_atTop_nhds_zero.comp hhalf)
  have hdiv := hexp.div_const (Real.sqrt (2 * Real.pi))
  have hzero : (0 : ℝ) / Real.sqrt (2 * Real.pi) = 0 := by ring
  rw [hzero] at hdiv
  simpa [stdNormalPdfReal, div_eq_mul_inv, Function.comp_def,
    mul_comm, mul_left_comm, mul_assoc] using hdiv

/-- The measure-theoretic standard normal density wrapper tends to `0` at `+∞`. -/
theorem tendsto_stdPdf_atTop_zero :
    Tendsto stdPdf atTop (𝓝 0) := by
  rw [show stdPdf = stdNormalPdfReal by
    funext x
    exact stdPdf_eq_stdNormalPdfReal x]
  exact tendsto_stdNormalPdfReal_atTop_zero

lemma stdNormalCDFReal_eq_integral_Iic (t : ℝ) :
    stdNormalCDFReal t = ∫ x in Set.Iic t, stdPdf x := by
  rw [stdNormalCDFReal_eq_real_measure_Iic]
  have hv : ((1 : NNReal) ≠ 0) := by
    norm_num
  have happly :
      stdNormalMeasure (Set.Iic t) = ENNReal.ofReal (∫ x in Set.Iic t, stdPdf x) := by
    simpa [stdNormalMeasure, stdPdf] using
      (ProbabilityTheory.gaussianReal_apply_eq_integral
        (μ := 0) (v := (1 : NNReal)) hv (Set.Iic t))
  have hreal := congrArg ENNReal.toReal happly
  have hreal' :
      stdNormalMeasure.real (Set.Iic t) = (ENNReal.ofReal (∫ x in Set.Iic t, stdPdf x)).toReal := by
    simpa [MeasureTheory.Measure.real] using hreal
  have hint_nonneg : 0 ≤ ∫ x in Set.Iic t, stdPdf x := by
    exact MeasureTheory.integral_nonneg (fun _ => by
      simp [stdPdf, ProbabilityTheory.gaussianPDFReal_nonneg])
  calc
    stdNormalMeasure.real (Set.Iic t)
      = (ENNReal.ofReal (∫ x in Set.Iic t, stdPdf x)).toReal := hreal'
    _ = ∫ x in Set.Iic t, stdPdf x := by
      simp [ENNReal.toReal_ofReal hint_nonneg]

lemma stdNormalCDFReal_sub_zero_eq_intervalIntegral (t : ℝ) :
    stdNormalCDFReal t - stdNormalCDFReal 0 = ∫ x in (0 : ℝ)..t, stdPdf x := by
  have hInt : MeasureTheory.Integrable stdPdf MeasureTheory.volume := by
    change MeasureTheory.Integrable
      (ProbabilityTheory.gaussianPDFReal 0 (1 : NNReal)) MeasureTheory.volume
    exact ProbabilityTheory.integrable_gaussianPDFReal 0 (1 : NNReal)
  have hIic0 : MeasureTheory.IntegrableOn stdPdf (Set.Iic (0 : ℝ)) MeasureTheory.volume :=
    hInt.integrableOn
  have hIict : MeasureTheory.IntegrableOn stdPdf (Set.Iic t) MeasureTheory.volume :=
    hInt.integrableOn
  have hsub := intervalIntegral.integral_Iic_sub_Iic (f := stdPdf) (μ := MeasureTheory.volume)
    (a := (0 : ℝ)) (b := t) hIic0 hIict
  calc
    stdNormalCDFReal t - stdNormalCDFReal 0
      = (∫ x in Set.Iic t, stdPdf x) - (∫ x in Set.Iic (0 : ℝ), stdPdf x) := by
          rw [stdNormalCDFReal_eq_integral_Iic, stdNormalCDFReal_eq_integral_Iic]
    _ = ∫ x in (0 : ℝ)..t, stdPdf x := hsub

lemma stdNormalCDFReal_eq_zero_add_intervalIntegral (t : ℝ) :
    stdNormalCDFReal t = stdNormalCDFReal 0 + ∫ x in (0 : ℝ)..t, stdPdf x := by
  have h := stdNormalCDFReal_sub_zero_eq_intervalIntegral t
  linarith

lemma hasDerivAt_stdNormalCDFReal (t : ℝ) :
    HasDerivAt stdNormalCDFReal (stdNormalPdfReal t) t := by
  have hInt : IntervalIntegrable stdPdf MeasureTheory.volume (0 : ℝ) t := by
    have h : MeasureTheory.Integrable stdPdf MeasureTheory.volume := by
      change MeasureTheory.Integrable
        (ProbabilityTheory.gaussianPDFReal 0 (1 : NNReal)) MeasureTheory.volume
      exact ProbabilityTheory.integrable_gaussianPDFReal 0 (1 : NNReal)
    exact h.intervalIntegrable
  have hMeas0 : Measurable stdPdf := by
    change Measurable (ProbabilityTheory.gaussianPDFReal 0 (1 : NNReal))
    exact ProbabilityTheory.measurable_gaussianPDFReal 0 (1 : NNReal)
  have hMeas : StronglyMeasurableAtFilter stdPdf (nhds t) MeasureTheory.volume := by
    exact hMeas0.stronglyMeasurable.stronglyMeasurableAtFilter
  have hCont : ContinuousAt stdPdf t := by
    exact (show Continuous stdPdf by
      unfold stdPdf
      simp [ProbabilityTheory.gaussianPDFReal]
      continuity).continuousAt
  have hDerivInt : HasDerivAt (fun u : ℝ => ∫ x in (0 : ℝ)..u, stdPdf x) (stdPdf t) t := by
    simpa using intervalIntegral.integral_hasDerivAt_right (a := (0 : ℝ)) (b := t)
      (f := stdPdf) hInt hMeas hCont
  have hEqFun :
      stdNormalCDFReal = (fun u : ℝ => stdNormalCDFReal 0 + ∫ x in (0 : ℝ)..u, stdPdf x) := by
    funext u
    simpa using stdNormalCDFReal_eq_zero_add_intervalIntegral u
  rw [hEqFun]
  simpa [stdPdf_eq_stdNormalPdfReal] using (hDerivInt.const_add (stdNormalCDFReal 0))

/-- The real standard-normal CDF is strictly increasing. -/
theorem strictMono_stdNormalCDFReal : StrictMono stdNormalCDFReal :=
  strictMono_of_hasDerivAt_pos hasDerivAt_stdNormalCDFReal stdNormalPdfReal_pos

end

end DP
end Mf
