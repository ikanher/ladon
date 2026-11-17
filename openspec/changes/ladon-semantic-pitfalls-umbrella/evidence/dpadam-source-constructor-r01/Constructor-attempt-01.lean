import Mf.Optimization.SDE.DPAdamFixedBetaFastSlowExactCountSchedule
namespace LadonSourceConstructor
open Filter MeasureTheory Mf.Optimization.SDE
open DPAdamFixedBetaFastSlowFamily DPAdamFixedBetaFastSlowGrowingClockMaps
open DPAdamFiniteHorizonObjective
open scoped Topology
noncomputable section
set_option autoImplicit false

def neutralObjective (d : ℕ) : SmoothObjective d where
  value := fun _ => 0
  gradient := fun _ _ => 0
  smoothness := 0
  smoothness_nonneg := le_rfl
  value_continuous := continuous_const
  gradient_continuous := continuous_const
  taylor_remainder := by intros; simp [euclideanDot]

theorem objective_field_irrelevant {m d : ℕ} (family : FixedNoiseFastSlowFamily m d)
    (objective : SmoothObjective d) (mesh : ℕ) :
    ({ family with objective := objective } : FixedNoiseFastSlowFamily m d).literalParameterPathLaw mesh =
      family.literalParameterPathLaw mesh := by rfl

#print axioms objective_field_irrelevant
end
end LadonSourceConstructor
