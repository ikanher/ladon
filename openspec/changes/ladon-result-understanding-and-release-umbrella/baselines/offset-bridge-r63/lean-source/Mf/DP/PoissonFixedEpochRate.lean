import Mf.DP.FixedParticipationRate

/-!
# Discrete Poisson fixed-epoch rates

This module owns the honest finite-product parameterization for a positive
integer expected epoch count.  A point has an integer horizon `T ≥ E` and
sampling rate `q = E / T`.  The full-batch endpoint is the discrete point
`T = E`; this module does not turn it into an independent fixed-`E` limit.

The construction models independent Poisson inclusion.  It does not model
shuffled or balanced exact participation.
-/

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- One admissible point on the positive-integer fixed-epoch path. -/
structure PoissonFixedEpochPoint where
  epoch : Nat
  horizon : Nat
  epoch_pos : 0 < epoch
  epoch_le_horizon : epoch ≤ horizon

namespace PoissonFixedEpochPoint

/-- The exact Poisson rate `E / T` at an admissible fixed-epoch point. -/
def samplingRate (point : PoissonFixedEpochPoint) : NNReal :=
  (point.epoch : NNReal) / (point.horizon : NNReal)

/-- The full-batch point for a positive integer epoch count. -/
def fullBatch (epoch : Nat) (epoch_pos : 0 < epoch) : PoissonFixedEpochPoint where
  epoch := epoch
  horizon := epoch
  epoch_pos := epoch_pos
  epoch_le_horizon := le_rfl

@[simp] theorem horizon_fullBatch (epoch : Nat) (epoch_pos : 0 < epoch) :
    (fullBatch epoch epoch_pos).horizon = epoch := by
  rfl

@[simp] theorem epoch_fullBatch (epoch : Nat) (epoch_pos : 0 < epoch) :
    (fullBatch epoch epoch_pos).epoch = epoch := by
  rfl

/-- The point whose horizon is `E + extra`.  This is the canonical sequence
used by the small-rate asymptotic theorem. -/
def ofExtra (epoch : Nat) (epoch_pos : 0 < epoch) (extra : Nat) :
    PoissonFixedEpochPoint where
  epoch := epoch
  horizon := epoch + extra
  epoch_pos := epoch_pos
  epoch_le_horizon := Nat.le_add_right epoch extra

@[simp] theorem epoch_ofExtra (epoch : Nat) (epoch_pos : 0 < epoch) (extra : Nat) :
    (ofExtra epoch epoch_pos extra).epoch = epoch := by
  rfl

@[simp] theorem horizon_ofExtra (epoch : Nat) (epoch_pos : 0 < epoch) (extra : Nat) :
    (ofExtra epoch epoch_pos extra).horizon = epoch + extra := by
  rfl

theorem horizon_pos (point : PoissonFixedEpochPoint) : 0 < point.horizon :=
  lt_of_lt_of_le point.epoch_pos point.epoch_le_horizon

theorem samplingRate_pos (point : PoissonFixedEpochPoint) :
    0 < point.samplingRate := by
  unfold samplingRate
  exact div_pos (by exact_mod_cast point.epoch_pos)
    (by exact_mod_cast point.horizon_pos)

theorem samplingRate_le_one (point : PoissonFixedEpochPoint) :
    point.samplingRate ≤ 1 := by
  unfold samplingRate
  rw [div_le_one (by exact_mod_cast point.horizon_pos)]
  exact_mod_cast point.epoch_le_horizon

/-- The defining fixed-epoch identity `T q = E`, expressed over the reals. -/
theorem horizon_mul_samplingRate (point : PoissonFixedEpochPoint) :
    (point.horizon : Real) * (point.samplingRate : Real) = point.epoch := by
  unfold samplingRate
  rw [NNReal.coe_div]
  field_simp [show (point.horizon : Real) ≠ 0 by
    exact_mod_cast point.horizon_pos.ne']
  norm_num

@[simp] theorem samplingRate_fullBatch (epoch : Nat) (epoch_pos : 0 < epoch) :
    (fullBatch epoch epoch_pos).samplingRate = 1 := by
  simp [samplingRate, fullBatch, ne_of_gt epoch_pos]

theorem samplingRate_lt_one_of_epoch_lt_horizon
    (point : PoissonFixedEpochPoint) (epoch_lt_horizon : point.epoch < point.horizon) :
    point.samplingRate < 1 := by
  unfold samplingRate
  rw [div_lt_one (by exact_mod_cast point.horizon_pos)]
  exact_mod_cast epoch_lt_horizon

/-- The exact rate is one precisely at the full-batch endpoint. -/
theorem samplingRate_eq_one_iff (point : PoissonFixedEpochPoint) :
    point.samplingRate = 1 ↔ point.horizon = point.epoch := by
  constructor
  · intro rate_eq_one
    by_contra horizon_ne_epoch
    have epoch_lt_horizon : point.epoch < point.horizon :=
      lt_of_le_of_ne point.epoch_le_horizon (Ne.symm horizon_ne_epoch)
    exact (point.samplingRate_lt_one_of_epoch_lt_horizon epoch_lt_horizon).ne
      rate_eq_one
  · intro horizon_eq_epoch
    rw [samplingRate, horizon_eq_epoch]
    simp [ne_of_gt point.epoch_pos]

@[simp] theorem ofExtra_zero (epoch : Nat) (epoch_pos : 0 < epoch) :
    ofExtra epoch epoch_pos 0 = fullBatch epoch epoch_pos := by
  rfl

theorem ofExtra_one_samplingRate (epoch : Nat) (epoch_pos : 0 < epoch) :
    (ofExtra epoch epoch_pos 1).samplingRate =
      (epoch : NNReal) / (epoch + 1 : Nat) := by
  rfl

/-- The discrete exact-epoch rate is the capped fixed-participation rate; the
cap is inactive because `epoch ≤ epoch + extra`. -/
@[simp] theorem ofExtra_samplingRate_eq_cappedParticipationRate
    (epoch : Nat) (epoch_pos : 0 < epoch) (extra : Nat) :
    (ofExtra epoch epoch_pos extra).samplingRate =
      cappedParticipationRate (epoch : NNReal) (epoch + extra) := by
  unfold samplingRate cappedParticipationRate
  rw [min_eq_right]
  · rfl
  · rw [div_le_one]
    · exact_mod_cast Nat.le_add_right epoch extra
    · exact_mod_cast Nat.add_pos_left epoch_pos extra

theorem ofExtra_one_samplingRate_lt_one (epoch : Nat) (epoch_pos : 0 < epoch) :
    (ofExtra epoch epoch_pos 1).samplingRate < 1 := by
  apply samplingRate_lt_one_of_epoch_lt_horizon
  simp [ofExtra]

theorem ofExtra_one_samplingRate_pos (epoch : Nat) (epoch_pos : 0 < epoch) :
    0 < (ofExtra epoch epoch_pos 1).samplingRate :=
  samplingRate_pos _

end PoissonFixedEpochPoint

end

end Mf.DP
