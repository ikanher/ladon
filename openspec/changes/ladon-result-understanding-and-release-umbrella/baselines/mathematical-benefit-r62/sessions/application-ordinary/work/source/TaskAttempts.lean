import Mf.DP.PoissonFixedEpochCenterGapPropagation

namespace TaskAttempts

 theorem taskOne
    (point : Mf.DP.PoissonFixedEpochPoint) (h boundary query : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)
    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query)
    (hBoundaryGap : 0 ≤ Mf.DP.fixedEpochCenterGap point h boundary) :
    0 < Mf.DP.fixedEpochCenterGap point h query := by
  exact Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg point h boundary query
    hNonFull hh hBoundaryNonneg hBoundaryQuery hBoundaryGap

#print axioms taskOne

example
    (point : Mf.DP.PoissonFixedEpochPoint) (h boundary query : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)
    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query) :
    0 ≤ Mf.DP.fixedEpochCenterGap point h boundary →
    0 < Mf.DP.fixedEpochCenterGap point h query := by
  intro hBoundaryGap
  exact Mf.DP.fixedEpochCenterGap_pos_of_boundary_nonneg point h boundary query
    hNonFull hh hBoundaryNonneg hBoundaryQuery hBoundaryGap

end TaskAttempts
