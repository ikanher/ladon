import Mf.DP.LawAccountingOracle

/-!
# Event witnesses for finite hockey-stick profiles

This module exposes the elementary witness direction of the exact event
supremum.  A supplied measurable event gives a lower bound; no maximizing
event or optimality claim is introduced.
-/

open MeasureTheory Set

namespace Mf.DP

noncomputable section

theorem eventHockeyStickProfile_ge_measurableEvent
    {Y : Type*} [MeasurableSpace Y]
    (mu nu : Measure Y) (epsilon : Real)
    (event : Set Y) (hEvent : MeasurableSet event) :
    mu event - ENNReal.ofReal (Real.exp epsilon) * nu event ≤
      eventHockeyStickProfile mu nu epsilon := by
  exact le_iSup
    (fun s : {s : Set Y // MeasurableSet s} ↦
      mu s.1 - ENNReal.ofReal (Real.exp epsilon) * nu s.1)
    ⟨event, hEvent⟩

end

end Mf.DP
