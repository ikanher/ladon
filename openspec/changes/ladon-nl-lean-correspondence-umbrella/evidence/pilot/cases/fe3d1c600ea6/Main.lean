import Lean

def IsEvenValue (n : Nat) : Prop := ∃ k, n = k + k

theorem positiveFromLowerBound (n : Nat) (hBound : n ≥ 2) : n > 0 := by
  exact Nat.lt_of_lt_of_le (by decide : 0 < 2) hBound

theorem result (n : Nat) (hEven : IsEvenValue n) (hBound : n ≥ 2) : n > 0 := by
  exact positiveFromLowerBound n hBound
