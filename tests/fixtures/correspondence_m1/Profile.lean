import Lean
namespace Profile
 theorem bridge {n : Nat} (h : 0 < n) : 0 < n := h
 theorem localValue (n : Nat) (h : 0 < n) : 0 < n := by
   let k := n
   exact bridge (n := k) h
end Profile
