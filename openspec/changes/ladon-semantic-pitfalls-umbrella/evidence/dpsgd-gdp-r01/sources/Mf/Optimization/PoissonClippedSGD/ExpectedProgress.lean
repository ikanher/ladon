import Mf.Optimization.PoissonClippedSGD.CoefficientComparison
import Mathlib.MeasureTheory.Function.L2Space
import Mathlib.MeasureTheory.Integral.MeanInequalities

/-!
# Expected gradient norm from clipped progress

The pointwise norm conversion is integrated using Cauchy--Schwarz for the
square-root term. Integrability is explicit, so totalized integrals do not
substitute for a finite-moment argument.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
noncomputable section
variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]

theorem integral_sqrt_le (p : Ω → ℝ) (hp : Measurable p)
    (hp0 : ∀ ω, 0 ≤ p ω) (hpi : Integrable p μ) :
    (∫ ω, Real.sqrt (p ω) ∂μ) ≤ Real.sqrt (∫ ω, p ω ∂μ) := by
  have hs : MemLp (fun ω => Real.sqrt (p ω)) 2 μ := by
    apply (memLp_two_iff_integrable_sq (by fun_prop)).2
    simpa only [Real.sq_sqrt (hp0 _)] using hpi
  have h := integral_mul_le_Lp_mul_Lq_of_nonneg
    (μ := μ) (p := (2 : ℝ)) (q := (2 : ℝ)) Real.HolderConjugate.two_two
    (ae_of_all μ (fun ω => Real.sqrt_nonneg (p ω)))
    (ae_of_all μ (fun _ => show (0:ℝ) ≤ 1 by norm_num))
    (by simpa using hs) (by simpa using (memLp_const (μ := μ) (p := 2) (1 : ℝ)))
  simp only [Real.rpow_two, Real.sq_sqrt (hp0 _), mul_one,
    integral_const, probReal_univ, smul_eq_mul] at h
  simpa [Real.sqrt_eq_rpow, one_div] using h

theorem expected_norm_from_progress (c : ℝ) (hc : 0 < c)
    (r : Ω → ℝ) (hr : Measurable r) (hr0 : ∀ ω, 0 ≤ r ω)
    (hri : Integrable r μ)
    (hpi : Integrable (fun ω => min ((r ω)^2) (c*r ω)) μ) :
    (∫ ω, r ω ∂μ) ≤
      Real.sqrt (∫ ω, min ((r ω)^2) (c*r ω) ∂μ) +
        (∫ ω, min ((r ω)^2) (c*r ω) ∂μ) / c := by
  let p : Ω → ℝ := fun ω => min ((r ω)^2) (c*r ω)
  have hp : Measurable p := by dsimp [p]; fun_prop
  have hp0 : ∀ ω, 0 ≤ p ω := fun ω => le_min (sq_nonneg _) (mul_nonneg hc.le (hr0 ω))
  have hs : MemLp (fun ω => Real.sqrt (p ω)) 2 μ := by
    apply (memLp_two_iff_integrable_sq (by fun_prop)).2
    simpa only [Real.sq_sqrt (hp0 _)] using hpi
  have hbound := integral_mono hri ((hs.integrable (by norm_num)).add (hpi.div_const c))
    (fun ω => norm_le_sqrt_min_add_min_div c (r ω) hc (hr0 ω))
  change (∫ ω, r ω ∂μ) ≤ ∫ ω, Real.sqrt (p ω) + p ω / c ∂μ at hbound
  rw [integral_add (hs.integrable (by norm_num)) (hpi.div_const c), integral_div] at hbound
  have hsqrt := integral_sqrt_le p hp hp0 hpi
  change (∫ ω, r ω ∂μ) ≤ Real.sqrt (∫ ω, p ω ∂μ) + (∫ ω, p ω ∂μ) / c
  linarith

end
end Mf.Optimization.PoissonClippedSGD
