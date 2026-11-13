import Mf.Optimization.FiniteMemoryAdam.CumulativeSupportedBiasRate
import Mathlib.Analysis.Real.Sqrt

/-!
# Full-batch zero-noise stationarity of the horizon-indexed family

The generated variance and capped exceptional budgets vanish exactly at full
batch and zero noise, even with centered heterogeneous records and active
clipping elsewhere. The constant step is selected separately for each horizon.
This limit concerns the expected pre-update average, not final iterates or a
single infinite run with a changing learning-rate schedule.
-/
namespace Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy
open Filter LocalizedVector
noncomputable section

theorem releaseVariance_full_batch_zero_noise (N d : ℕ) (θ ρ G : ℝ) :
    releaseVariance N d 1 0 θ ρ G = 0 := by simp [releaseVariance]

theorem energyBudget_full_batch_zero_noise (N d : ℕ) (θ ρ G rS rZ : ℝ) :
    energyBudget N d 1 0 θ ρ G rS rZ = 0 := by
  simp [energyBudget, Heterogeneous.samplingFourthBudget]

/-- Zero stochastic remainder is a consequence of the actual generated budgets. -/
theorem supported_bias_full_batch_zero_noise_rate {T : ℕ} {Linf θ ρ : ℝ}
    (F : SmoothObjective 100000 (1001/1000) 3 Linf)
    (data : CenteredRecordFamily 50000 100000 θ ρ)
    (hLip : ∀ x y, ‖F.gradient x-F.gradient y‖ ≤ 3*‖x-y‖)
    (hT : 16384 ≤ T) (hθ : θ ∈ Set.Icc 0 (38/100))
    (hρ : ρ ∈ Set.Icc 0 (5/1000)) (x0 : Point 100000)
    (hΔ : F.value x0-F.lower ≤ 501/1000) :
    expectedSquaredGradient (T := T) F data (horizonPhysicalStep 100000 T)
      (1/100000000) x0 1 (by norm_num) 0 ≤ 51/Real.sqrt (T:ℝ) := by
  have hu := supported_bias_physical_window_rate F data hLip hT hθ hρ x0 hΔ
    1 (by norm_num) (by norm_num) 0
    (by norm_num [physicalNoise])
  simpa only [NNReal.coe_one, releaseVariance_full_batch_zero_noise,
    energyBudget_full_batch_zero_noise, Real.sqrt_zero, mul_zero, add_zero] using hu

/-- Every horizon defines its own actual initialized run with a constant step. -/
theorem supported_bias_full_batch_zero_noise_tendsto {Linf θ ρ : ℝ}
    (F : SmoothObjective 100000 (1001/1000) 3 Linf)
    (data : CenteredRecordFamily 50000 100000 θ ρ)
    (hLip : ∀ x y, ‖F.gradient x-F.gradient y‖ ≤ 3*‖x-y‖)
    (hθ : θ ∈ Set.Icc 0 (38/100)) (hρ : ρ ∈ Set.Icc 0 (5/1000))
    (x0 : Point 100000) (hΔ : F.value x0-F.lower ≤ 501/1000) :
    Tendsto (fun T : ℕ => expectedSquaredGradient (T := T) F data
      (horizonPhysicalStep 100000 T) (1/100000000) x0 1 (by norm_num) 0)
      atTop (nhds 0) := by
  apply squeeze_zero' (Eventually.of_forall (fun T =>
    expectedSquaredGradient_nonneg F data _ _ x0 1 (by norm_num) 0))
    (g := fun T : ℕ => 51/Real.sqrt (T:ℝ))
  · filter_upwards [eventually_ge_atTop 16384] with T hT
    exact supported_bias_full_batch_zero_noise_rate F data hLip hT hθ hρ x0 hΔ
  · exact tendsto_const_nhds.div_atTop
      (Real.tendsto_sqrt_atTop.comp tendsto_natCast_atTop_atTop)

end
end Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy
