import Mf.Optimization.PoissonClippedSGD.MomentumProgressGate
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumOutputAssembly
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumBoundary

/-!
# General Poisson corrected-momentum output

The actual initialized process includes empty batches, public expected-count
normalization and fresh unbounded Gaussian noise. The symbolic output theorem
retains random-total-count energy, finite first-moment correction and the
uniform-time motion charge. The adaptive second denominator is absent.
-/

namespace Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
open MeasureTheory PoissonClippedSGD CorrectedColumns
noncomputable section

/-- The full Poisson C5 endpoint, including stationary and exact SGD reductions. -/
theorem poisson_output : poissonOutput := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro n d a q hq0 hq η p hη hp H _ hgate
    let o := poissonObservation a q hq η p H
    haveI : IsProbabilityMeasure o.law := by
      dsimp [o, poissonObservation]
      infer_instance
    have hH : 0 < H := Nat.pos_of_ne_zero (NeZero.ne H)
    apply output_of_moments_progress a o hη hp
      (poisson_moments n d a q hq0 hq η p hη.le hp H hH)
      (poisson_progress n d a q hq0 hq η p hη hp H hH hgate)
    · intro ω t
      exact momentumStream_corrected_eq_corrMem η p _ a.x₀ _ t
    · intro ω t
      exact momentumStream_position_corrMem η p _ a.x₀ _ t
  · intro n d a q hq0 hq p hp H _
    let o := poissonObservation a q hq 0 p H
    haveI : IsProbabilityMeasure o.law := by
      dsimp [o, poissonObservation]
      infer_instance
    apply stationary_output a o H
    intro ω t
    exact stream_zero_step p _ a.x₀ _ t
  · intro n d a q hq0 hq η hη H t ht ω
    exact stream_zero_momentum η _ a.x₀ ((fun _ => false), 0) H t ht ω
  · intro n d a q hq0 hq η hη H hH
    apply sharp_budget_le_sgd a hη _ hH
    unfold poissonKappa
    apply div_nonneg
    · exact sub_nonneg.mpr (by exact_mod_cast hq)
    · positivity

end
end Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
