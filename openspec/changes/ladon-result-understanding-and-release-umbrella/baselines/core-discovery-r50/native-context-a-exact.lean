import Mf.DP.PoissonFixedEpochCenterGapPropagation

example : ∀ (point : Mf.DP.PoissonFixedEpochPoint) (h : ℝ) (boundary : ℝ) (query : ℝ) (hNonFull : point.epoch < point.horizon) (hh : 0 < h) (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query) (hBoundaryGap : 0 ≤ Mf.DP.fixedEpochCenterGap point h boundary), 0 < Mf.DP.fixedEpochCenterGap point h query := by
  intro point h boundary query hNonFull hh hBoundaryNonneg hBoundaryQuery hBoundaryGap
  exact?
