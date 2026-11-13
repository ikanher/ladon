import Mf.DP.Training.Common.DatasetAdjacency
import Mf.DP.EuclideanVectorClipping
import Mf.DP.ProfileAdaptiveKernelComposition

namespace Mf
namespace DP
namespace Training

open MeasureTheory

noncomputable section

/--
An adaptive per-user query used by the mathematical training transcript.

The query may inspect the complete prior private-release history. Clipping is
performed by `adaptiveClippedAggregate`; it is not an oracle premise.
-/
structure AdaptiveTrainingOracle
    (Record : Type*) [DecidableEq Record]
    (T d : ℕ) where
  query :
    Fin T → AdaptiveReleaseHistory (Fin d → ℝ) → Record → Fin d → ℝ
  measurable_history :
    ∀ t record, Measurable (fun history => query t history record)

/-- Canonical public initial state for an adaptive release transcript. -/
def zeroAdaptiveReleaseHistory
    {Release : Type*} [Zero Release] : AdaptiveReleaseHistory Release :=
  0

/-- Sum of per-user contributions after explicit Euclidean clipping. -/
def adaptiveClippedAggregate
    {Record : Type*} [DecidableEq Record]
    {T d : ℕ}
    (oracle : AdaptiveTrainingOracle Record T d)
    (clippingNorm : ℝ)
    (step : Fin T)
    (history : AdaptiveReleaseHistory (Fin d → ℝ))
    (dataset : UserDataset Record) : Fin d → ℝ :=
  l2ClippedFinsetSum clippingNorm (oracle.query step history) dataset

/--
At every fixed private history, add/remove adjacency changes the clipped
aggregate by at most the clipping norm. This is the deterministic sensitivity
bridge needed by each conditional Gaussian release.
-/
theorem adaptiveClippedAggregate_userAddRemove_sensitivity
    {Record : Type*} [DecidableEq Record]
    {T d : ℕ}
    (oracle : AdaptiveTrainingOracle Record T d)
    (clippingNorm : ℝ)
    (hclipping : 0 ≤ clippingNorm)
    (step : Fin T)
    (history : AdaptiveReleaseHistory (Fin d → ℝ))
    {left right : UserDataset Record}
    (hAdj : UserAddRemoveAdj left right) :
    l2Norm
      (adaptiveClippedAggregate oracle clippingNorm step history left -
        adaptiveClippedAggregate oracle clippingNorm step history right)
      ≤ clippingNorm := by
  exact l2ClippedFinsetSum_addRemove_sensitivity
    clippingNorm hclipping (oracle.query step history) hAdj

end

end Training
end DP
end Mf
