import Lean

theorem arithmeticEvaluation (x y : Int) : x + y = y + x := by
  omega

theorem result (x y : Int) : x + y = y + x := by
  exact arithmeticEvaluation x y
