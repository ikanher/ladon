import Mf.Optimization.FiniteMemoryAdam.CumulativeEnergyNumericalBudget
import Mf.Optimization.FiniteMemoryAdam.CumulativeEnergyUtility
import Mf.Optimization.FiniteMemoryAdam.CumulativeUsefulUtility
namespace Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy
open MeasureTheory LocalizedVector
noncomputable section
set_option maxHeartbeats 800000
theorem checked_source_energy_chain {T : ℕ} {Linf θ ρ : ℝ}
    (F : SmoothObjective 100000 (1001/1000) 3 Linf)
    (data : CenteredRecordFamily 50000 100000 θ ρ)
    (hT : 16384 ≤ T) (hθ : θ ∈ Set.Icc 0 (38/100))
    (hρ : ρ ∈ Set.Icc 0 (5/1000)) (η : ℝ) (x0 : Point 100000)
    (hη : η ≠ 0) (q : NNReal) (hq : q ≤ 1) (hqr : (q:ℝ) ∈ Set.Icc (1/4) 1)
    (σ : ℝ) (hσ : σ ∈ Set.Icc 0 ((19/10)*physicalNoise)) :
    expectedUpdateEnergy (T := T) F data η (1/100000000) x0 q hq σ ≤ 63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999) ∧
    63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999) ≤ 29/10 := by
  have hq0 : 0 < q := by exact_mod_cast (show (0:ℝ) < q by linarith [hqr.1])
  have hV0 := releaseVariance_nonneg 50000 100000 q.coe_nonneg hqr.2 σ θ ρ (1001/1000)
  have hV := releaseVariance_safe (G := 1001/1000) hqr hθ hρ (by norm_num)
    (physical_noise_window_scaled hσ)
  have hEnergy := model_expected_update_energy_le (T := T) F data (by norm_num) (by norm_num)
    hθ hρ (by norm_num) η (1/100000000) x0 hη (by norm_num) q hq hq0 σ
    (r := 64) (by norm_num)
  have hEnvelope := logEnergyBound_envelope (by omega : 0 < T) hV0 hV
  have hCap : 63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999) ≤ 29/10 := by
    have hTR : (16384:ℝ) ≤ T := by exact_mod_cast hT
    have h1 : 63*(73/10:ℝ)^2/(T:ℝ) ≤ 63*(73/10:ℝ)^2/16384 := by gcongr
    have h2 : (26:ℝ)/(T:ℝ) ≤ 26/16384 := by gcongr
    norm_num at h1 h2 ⊢
    linarith
  exact ⟨hEnergy.trans hEnvelope, hCap⟩

#print axioms checked_source_energy_chain
end
end Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy
