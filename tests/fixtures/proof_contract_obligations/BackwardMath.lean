import Std

/- Conditional preconditions are not converses or necessary conditions. -/
namespace BackwardMath

theorem no_converse : (False → True) ∧ ¬ (True → False) := by
  constructor
  · intro h
    exact h.elim
  · intro h
    exact h True.intro

/-- A monotone natural-valued scale which changes at index four. -/
def threshold (s : Nat) : Nat := if 4 ≤ s then 1 else 0

theorem threshold_monotone (i j : Nat) (hij : i ≤ j) : threshold i ≤ threshold j := by
  unfold threshold
  split <;> split <;> omega

/-- Loss four is valid, although the stronger loss-two precondition is false. -/
theorem sufficient_not_necessary :
    (∀ s : Nat, 1 ≤ threshold (s + 4)) ∧ ¬ (∀ s : Nat, 1 ≤ threshold (s + 2)) := by
  constructor
  · intro s
    unfold threshold
    rw [if_pos (Nat.le_add_left 4 s)]
    exact Nat.le_refl 1
  · intro h
    have hzero := h 0
    change 1 ≤ 0 at hzero
    exact Nat.not_succ_le_zero 0 hzero

end BackwardMath

#print axioms BackwardMath.no_converse
#print axioms BackwardMath.threshold_monotone
#print axioms BackwardMath.sufficient_not_necessary
