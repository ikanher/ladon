import Mf.DP.PoissonFixedEpochCenterGapPropagation
open Mf.DP
example : ∀ (point : PoissonFixedEpochPoint) (h boundary query : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)
    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query)
    (hBoundaryGap : 0 ≤ fixedEpochCenterGap point h boundary),
    0 < fixedEpochCenterGap point h query := by
  intro point h boundary query hNonFull hh hBoundaryNonneg hBoundaryQuery hBoundaryGap
  exact fixedEpochCenterGap_pos_of_boundary_nonneg point h boundary query
    hNonFull hh hBoundaryNonneg hBoundaryQuery hBoundaryGap
