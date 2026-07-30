import CapsuleFixture.Base
import CapsuleFixture.Large

namespace CapsuleFixture

section LocalContext

local notation "theBase" => base

/-- The selected theorem has a documentation range preceding its command. -/
theorem chosen : theBase = 1 ∧ chain70 = 0 ∧ Even 0 := by
  constructor
  · rfl
  · constructor
    · rfl
    · exact Even.zero

theorem later : True := by
  trivial

end LocalContext

end CapsuleFixture
