import Mf.DP.PoissonFixedEpochCenterGapPropagation

theorem preflightOne (point : Mf.DP.PoissonFixedEpochPoint) (h boundary query : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)
    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query)
    (hBoundaryGap : 0 ≤ Mf.DP.fixedEpochCenterGap point h boundary) :
    0 < Mf.DP.fixedEpochCenterGap point h query := by
  exact?

#print axioms preflightOne
