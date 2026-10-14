import Main

example : IsEvenValue 0 := ⟨0, rfl⟩
example : 2 ∣ 0 := ⟨0, by decide⟩
example : ¬ (0 > 0) := by decide

theorem parity_alone_does_not_imply_positive :
    ¬ (∀ n : Nat, IsEvenValue n → n > 0) := by
  intro h
  have hzero := h 0 ⟨0, rfl⟩
  exact Nat.lt_irrefl 0 hzero

theorem even_implies_divisible_by_two (n : Nat) (hEven : IsEvenValue n) : 2 ∣ n := by
  rcases hEven with ⟨k, hk⟩
  rw [hk]
  exact ⟨k, by simp [Nat.two_mul]⟩

example (n : Nat) (hEven : IsEvenValue n) (hBound : n ≥ 2) : n > 0 :=
  result n hEven hBound
