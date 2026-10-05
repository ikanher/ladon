import Mf.DP.PoissonFixedEpochCenterGapPropagation

theorem preflightTwo (point : Mf.DP.PoissonFixedEpochPoint) (h boundary query : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)
    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query) :
    0 < Mf.DP.fixedEpochCenterGap point h query := by
  apply?

#print axioms preflightTwo
