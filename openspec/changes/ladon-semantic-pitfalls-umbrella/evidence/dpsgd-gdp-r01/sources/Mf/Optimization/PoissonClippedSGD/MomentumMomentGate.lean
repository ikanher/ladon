import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
import Mf.Optimization.PoissonClippedSGD.MomentumHorizonMoments

/-!
# Common-horizon moments for corrected momentum with Poisson sampling

This theorem discharges the full Poisson moment contract under the actual
initialized process law, including the empty and random batch counts.
It keeps the exact corrected first memory and total Gaussian RMS convention.
-/

namespace Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
open MeasureTheory PoissonClippedSGD FixedSubsetClippedSGD CorrectedColumns
noncomputable section
set_option maxHeartbeats 800000

/-- The Poisson C5 moment gate, for every positive population and horizon. -/
theorem poisson_moments : poissonMoments := by
  intro n d a q hq0 hq1 η p hη hp H hH
  intro t ht
  let μ := (poissonObservation a q hq1 η p H).law
  haveI : IsProbabilityMeasure μ := by
    dsimp [μ, poissonObservation]
    infer_instance
  let X := (poissonObservation a q hq1 η p H).X t
  let Y := (poissonObservation a q hq1 η p H).Y t
  have hX : Measurable X := by
    exact momentumState_measurable η p q a.C a.hC.le a.g a.measurable_g a.x₀ H t
  have hY : Measurable Y := by
    have hQ := measurable_sampledGradient q a.C a.hC.le a.g a.measurable_g
    have hI := momentumFiniteInnovation_measurable
      ((fun _ : Fin n => false), (0 : V d)) H t
    change Measurable (fun ω =>
      sampledGradient q a.C a.g (X ω)
        (momentumFiniteInnovation ((fun _ : Fin n => false), (0 : V d)) ω t).1 +
        (momentumFiniteInnovation ((fun _ : Fin n => false), (0 : V d)) ω t).2)
    exact (hQ.comp (hX.prodMk hI.fst)).add hI.snd
  have hXLp : MemLp X 2 μ := by
    exact (momentumState_memLp_two a.hn q hq0 hq1 η p a.C a.τ a.hC.le a.g a.measurable_g a.x₀ H t).1
  have hYLp : MemLp Y 2 μ := by
    exact momentumRelease_memLp_two a.hn q hq0 hq1 η p a.C a.τ a.hC.le a.g a.measurable_g a.x₀ H t
  have hGLp : MemLp (fun ω => a.G (X ω)) 2 μ := by
    exact momentumState_gradient_memLp_two a.hn q hq0 hq1 η p a.C a.τ a.hC.le a.g a.measurable_g
      a.x₀ H t a.G a.L a.hL a.lipschitz
  have hMeanLp : MemLp (fun ω => a.mean (X ω)) 2 μ := by
    exact clippedMean_comp_memLp_two μ a.hn a.C a.hC.le a.g a.measurable_g X hX
  have hPair : Integrable (fun ω => inner ℝ (a.G (X ω)) (Y ω)) μ := by
    exact StabilizerBudget.integrable_inner_of_memLp hGLp hYLp
  have hMeanPair : Integrable (fun ω => inner ℝ (a.G (X ω)) (a.mean (X ω))) μ := by
    exact StabilizerBudget.integrable_inner_of_memLp hGLp hMeanLp
  have hVar : Integrable (fun ω => a.clippedVariance (X ω)) μ := by
    have h := clippedEnergy_comp_integrable μ a.hn a.C a.hC.le a.g
      a.measurable_g X hX 0 1 0
    simpa [Model.clippedVariance, Model.mean] using h
  have hPairEq : (∫ ω, inner ℝ (a.G (X ω)) (Y ω) ∂μ) =
      (∫ ω, inner ℝ (a.G (X ω)) (a.mean (X ω)) ∂μ) := by
    exact momentumState_full_horizon_pairing a.hn q hq0 hq1 η p a.C a.τ a.hC.le
      a.g a.measurable_g a.x₀ H t ht a.G a.L a.hL a.lipschitz
  have hκ : 0 ≤ poissonKappa n q := by
    unfold poissonKappa
    apply div_nonneg
    · exact sub_nonneg.mpr (by exact_mod_cast hq1)
    · positivity
  have hEnergy : (∫ ω, ‖Y ω‖ ^ 2 ∂μ) =
      (1 + poissonKappa n q) * (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) +
      poissonKappa n q * (∫ ω, a.clippedVariance (X ω) ∂μ) + a.τ ^ 2 := by
    have h := momentumState_full_horizon_energy a.hn a.hd q hq0 hq1 η p a.C a.τ
      a.hC.le a.g a.measurable_g a.x₀ H t ht
    have hκeq : (1 - (q : ℝ)) / ((q : ℝ) * n) = poissonKappa n q := by
      unfold poissonKappa
      rw [mul_comm (q : ℝ) (n : ℝ)]
    simp only [hκeq] at h
    change (∫ ω, ‖Y ω‖ ^ 2 ∂μ) =
      ∫ ω, (1 + poissonKappa n q) * ‖a.mean (X ω)‖ ^ 2 +
        poissonKappa n q * a.clippedVariance (X ω) + a.τ ^ 2 ∂μ at h
    have hm2 : Integrable (fun ω => ‖a.mean (X ω)‖ ^ 2) μ :=
      hMeanLp.integrable_norm_pow (by norm_num : 2 ≠ 0)
    have hsum := integral_add (hm2.const_mul (1 + poissonKappa n q))
      (hVar.const_mul (poissonKappa n q))
    have htotal := integral_add
      ((hm2.const_mul (1 + poissonKappa n q)).add
        (hVar.const_mul (poissonKappa n q))) (integrable_const (a.τ ^ 2))
    have htotal' :
        (∫ ω, (1 + poissonKappa n q) * ‖a.mean (X ω)‖ ^ 2 + poissonKappa n q *
          a.clippedVariance (X ω) + a.τ ^ 2 ∂μ) =
        (∫ ω, (1 + poissonKappa n q) * ‖a.mean (X ω)‖ ^ 2 + poissonKappa n q *
          a.clippedVariance (X ω) ∂μ) + a.τ ^ 2 := by
      simpa only [Pi.add_apply, integral_const, probReal_univ, one_smul] using htotal
    calc
      _ = ∫ ω, (1 + poissonKappa n q) * ‖a.mean (X ω)‖ ^ 2 + poissonKappa n q *
        a.clippedVariance (X ω) + a.τ ^ 2 ∂μ := h
      _ = _ := by
        rw [htotal', hsum, integral_const_mul, integral_const_mul]
  have hEnergyBound : (∫ ω, ‖Y ω‖ ^ 2 ∂μ) ≤
      (1 + poissonKappa n q) * (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) +
        a.noise (poissonKappa n q) := by
    have hVarBound : (∫ ω, a.clippedVariance (X ω) ∂μ) ≤ a.s ^ 2 := by
      have hv := integral_mono hVar (integrable_const (a.s ^ 2)) (fun ω =>
        (clippedMean_variance_le a.hn a.C a.hC.le (fun i => a.g i (X ω))).trans
          (a.variance (X ω)))
      simpa using hv
    rw [hEnergy]
    dsimp [Model.noise]
    nlinarith [mul_le_mul_of_nonneg_left hVarBound hκ]
  have hFinal : (1 + poissonKappa n q) *
      (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) + a.noise (poissonKappa n q) ≤
      a.energy (poissonKappa n q) (1 + poissonKappa n q) := by
    have hm2 := hMeanLp.integrable_norm_pow (by norm_num : 2 ≠ 0)
    have hbnd : (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) ≤ a.C ^ 2 := by
      have hv := integral_mono hm2 (integrable_const (a.C ^ 2)) (fun ω =>
        pow_le_pow_left₀ (norm_nonneg _) (StabilizerBudget.clipped_mean_norm_le
          a.hn a.C a.hC.le (fun i => a.g i (X ω))) 2)
      simpa using hv
    have hχ : 0 ≤ 1 + poissonKappa n q := by linarith
    dsimp [Model.energy]
    nlinarith [mul_le_mul_of_nonneg_left hbnd hχ]
  simpa only [] using
    (show Measurable X ∧ Measurable Y ∧ MemLp X 2 μ ∧ MemLp Y 2 μ ∧
      MemLp (fun ω => a.G (X ω)) 2 μ ∧ MemLp (fun ω => a.mean (X ω)) 2 μ ∧
      Integrable (fun ω => inner ℝ (a.G (X ω)) (Y ω)) μ ∧
      Integrable (fun ω => inner ℝ (a.G (X ω)) (a.mean (X ω))) μ ∧
      Integrable (fun ω => a.clippedVariance (X ω)) μ ∧
      (∫ ω, inner ℝ (a.G (X ω)) (Y ω) ∂μ) =
        (∫ ω, inner ℝ (a.G (X ω)) (a.mean (X ω)) ∂μ) ∧
      (∫ ω, ‖Y ω‖ ^ 2 ∂μ) =
        (1 + poissonKappa n q) * (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) +
        poissonKappa n q * (∫ ω, a.clippedVariance (X ω) ∂μ) + a.τ ^ 2 ∧
      (∫ ω, ‖Y ω‖ ^ 2 ∂μ) ≤
        (1 + poissonKappa n q) * (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) +
        a.noise (poissonKappa n q) ∧
      (1 + poissonKappa n q) * (∫ ω, ‖a.mean (X ω)‖ ^ 2 ∂μ) +
        a.noise (poissonKappa n q) ≤
        a.energy (poissonKappa n q) (1 + poissonKappa n q) from
      ⟨hX, hY, hXLp, hYLp, hGLp, hMeanLp, hPair, hMeanPair,
        hVar, hPairEq, hEnergy, hEnergyBound, hFinal⟩)

end
end Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
