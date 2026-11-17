import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowNamedNonlinearLimitLaw
namespace LadonGeneralBridge
open Filter MeasureTheory Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowFamily DPAdamFixedBetaFastSlowGrowingClockMaps
open DPAdamFixedBetaFastSlowHighNoiseResponse
open scoped Topology
noncomputable section
set_option autoImplicit false

-- The within-row mesh limit imposes no rate on the across-row public initial points.
def withInitial {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (x : Fin d → ℝ) : FixedNoiseFastSlowFamily m d :=
  { family with
    thetaInitial := fun _ => x
    thetaLimitInitial := x
    thetaInitial_tendsto := tendsto_const_nhds
    fluctuationInitial := 0
    fluctuationInitial_tendsto := by
      convert (tendsto_const_nhds : Tendsto (fun _ : ℕ => (0 : Fin d → ℝ))
        atTop (𝓝 0)) using 1
      ext mesh i
      simp }

theorem initial_coherence {m d : ℕ} (family : ℕ → FixedNoiseFastSlowFamily m d)
    (mesh : ℕ → ℕ) (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ)
    (hx : Tendsto x atTop (𝓝 x0)) :
    Tendsto (fun n => ‖(withInitial (family n) (x n)).thetaInitial (mesh n) - x0‖)
      atTop (𝓝 0) := by
  exact tendsto_iff_norm_sub_tendsto_zero.mp hx

theorem fixed_query_mean {m d : ℕ} (data : GrowingClockData m d)
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hquery : ∀ n, (data.family n).gradientOracle = query)
    (n : ℕ) (theta : Fin d → ℝ) :
    clippedGradientMean (data.family n) theta =
      DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
        (fun record => Mf.DP.l2VectorClip data.base.clipping (query theta record))
        data.base.dataset := by
  simp only [clippedGradientMean, hquery n, data.clipping_eq n, data.dataset_eq n]

theorem fixed_query_local_mean {m d : ℕ} (data : GrowingClockData m d)
    (query : (Fin d → ℝ) → Fin m → (Fin d → ℝ))
    (hquery : ∀ n, (data.family n).gradientOracle = query) :
    ∀ radius : ℝ, 0 ≤ radius → ∃ meanError : ℕ → ℝ,
      (∀ n, 0 ≤ meanError n) ∧ Tendsto meanError atTop (𝓝 0) ∧
      ∀ n (theta : Fin d → ℝ), ‖theta‖ ≤ radius →
        ‖clippedGradientMean (data.family n) theta -
          DPAdamFixedBetaConcreteClippingAlignment.empiricalMean
            (fun record => Mf.DP.l2VectorClip data.base.clipping (query theta record))
            data.base.dataset‖ ≤ meanError n := by
  intro radius hradius
  refine ⟨fun _ => 0, fun _ => le_rfl, tendsto_const_nhds, ?_⟩
  intro n theta htheta
  rw [fixed_query_mean data query hquery n theta]
  simp

#print axioms withInitial
#print axioms initial_coherence
#print axioms fixed_query_local_mean

def withInitialRegularity {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (regularity : FixedNoiseFastSlowQueryRegularity family) (x : Fin d → ℝ) :
    FixedNoiseFastSlowQueryRegularity (withInitial family x) where
  recordConstant := regularity.recordConstant
  recordConstant_nonneg := regularity.recordConstant_nonneg
  gradientOracle_sub_l2Norm_le := regularity.gradientOracle_sub_l2Norm_le

def withPublicInitial {m d : ℕ} (data : GrowingClockData m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) : GrowingClockData m d :=
  { data with
    base := withInitial data.base x0
    baseRegularity := withInitialRegularity data.base data.baseRegularity x0
    family := fun n => withInitial (data.family n) (x n)
    regularity := fun n => withInitialRegularity (data.family n) (data.regularity n) (x n) }

theorem public_initial_coherence {m d : ℕ} (data : GrowingClockData m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) (hx : Tendsto x atTop (𝓝 x0)) :
    Tendsto (fun n => ‖((withPublicInitial data x x0).family n).thetaInitial
      ((withPublicInitial data x x0).mesh n) - x0‖) atTop (𝓝 0) :=
  initial_coherence data.family data.mesh x x0 hx

-- This transformation leaves the actual schedule and release kernels' primitive data fixed.
theorem public_initial_clock {m d : ℕ} (data : GrowingClockData m d)
    (x : ℕ → (Fin d → ℝ)) (x0 : Fin d → ℝ) :
    (withPublicInitial data x x0).clock = data.clock ∧
    (withPublicInitial data x x0).eta = data.eta := by exact ⟨rfl, rfl⟩

#print axioms withPublicInitial
#print axioms public_initial_coherence
#print axioms public_initial_clock
end
end LadonGeneralBridge
