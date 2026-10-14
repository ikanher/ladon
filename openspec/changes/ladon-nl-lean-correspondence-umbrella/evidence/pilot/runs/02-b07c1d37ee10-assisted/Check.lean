import Main

example : ¬ (∀ x : Int, x ≤ 9 → x = 4) := by
  intro h
  have hx := h 9 (by decide)
  have hn : (9 : Int) ≠ 4 := by decide
  exact hn hx
