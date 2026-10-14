import Lean
namespace Correspondence
 theorem bridge (n : Nat) (h : 0 < n) : 0 < n := h
 theorem term (n : Nat) (h : 0 < n) : 0 < n := bridge n h
 theorem tactic (n : Nat) (h : 0 < n) : 0 < n := by
   exact bridge n h
end Correspondence
