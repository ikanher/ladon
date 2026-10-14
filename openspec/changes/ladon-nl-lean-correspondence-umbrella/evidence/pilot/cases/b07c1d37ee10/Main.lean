import Lean

theorem relaxedBound (x : Int) (hSmall : x ≤ 5) (hRule : x ≤ 5 → x ≤ 9) : x ≤ 9 := by
  exact hRule hSmall

theorem calibrationRecord (x : Int) (hCalibration : x = 4) : x = 4 := by
  exact hCalibration

theorem result (x : Int) (hSmall : x ≤ 5) (hRule : x ≤ 5 → x ≤ 9) (hCalibration : x = 4) : x = 4 := by
  have _hRelaxed := relaxedBound x hSmall hRule
  exact calibrationRecord x hCalibration
