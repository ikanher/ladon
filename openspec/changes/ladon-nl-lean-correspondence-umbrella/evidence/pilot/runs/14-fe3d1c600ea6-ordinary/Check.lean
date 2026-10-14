import Main

example : IsEvenValue 0 := ⟨0, by rfl⟩
example : ¬ (0 > 0) := by decide

theorem no_even_implies_positive : ¬ (∀ n : Nat, IsEvenValue n → n > 0) := by
  intro h
  have h0 := h 0 (⟨0, by rfl⟩)
  exact Nat.lt_irrefl 0 h0

theorem endpoint_from_bound (n : Nat) (hBound : n ≥ 2) : n > 0 :=
  positiveFromLowerBound n hBound

#print result
#print positiveFromLowerBound
