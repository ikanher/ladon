import Main

example : ¬ (∀ x : Int, x ≤ 9 → x = 4) := by
  intro h
  have hx := h 9 (by decide)
  norm_num at hx
