import Lean

namespace Representation

theorem bridge (n : Nat) (h : n < 5) : n < 5 := h
theorem selected (n : Nat) (h : n < 5) : n < 5 := bridge n h

end Representation
