import Mf.Optimization.PoissonClippedSGD.MomentumMomentGate
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumProgressAssembly

/-!
# General Poisson corrected-momentum progress

Actual Poisson/Gaussian moments retain the random-count contribution to mean
energy. The shared sharp progress assembly absorbs that energy only under the
sampler's explicit stepsize gate, keeping public expected-batch normalization.
-/

namespace Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
open MeasureTheory PoissonClippedSGD CorrectedColumns
noncomputable section

/-- The full Poisson progress contract, with empty batches and both noise sources. -/
theorem poisson_progress : poissonProgress := by
  intro n d a q hq0 hq η p hη hp H hH hgate
  let o := poissonObservation a q hq η p H
  haveI : IsProbabilityMeasure o.law := by
    dsimp [o, poissonObservation]
    infer_instance
  apply progress_of_moments a o hη hp hH hgate
    (poisson_moments n d a q hq0 hq η p hη.le hp H hH)
  · intro ω
    rfl
  · intro ω t
    exact momentumStream_position_corrMem η p _ a.x₀ _ t

end
end Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumContracts
