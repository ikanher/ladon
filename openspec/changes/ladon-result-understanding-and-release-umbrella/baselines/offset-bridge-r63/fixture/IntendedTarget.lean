import Mf.DP.PoissonFixedEpochAsymptotics

open Filter
open scoped Topology
namespace OffsetBridge
noncomputable section
set_option autoImplicit false

/-- Intended offset component only. A placeholder here is not completion. -/
theorem fixedEpochOffsetBridge
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra : Nat =>
        sensitivity /
          (Mf.DP.poissonFixedEpochCalibratedStddev
            (Mf.DP.PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta : Real) -
          Real.sqrt (2 * Real.log ((epoch + extra : Nat) : Real)))
      atTop
      (nhds (Mf.DP.standardNormalQuantile
        (-Real.log (1 - delta) / (epoch : Real)))) := by
  sorry

#print axioms fixedEpochOffsetBridge
end OffsetBridge
